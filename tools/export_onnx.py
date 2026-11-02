"""Export the trained models to ONNX and check that ONNX Runtime gives the same results as PyTorch.

Usage:
    python tools/export_onnx.py --disease-model models/tomato_disease_v4_effb0_10class.pt
    python tools/export_onnx.py --pest-model models/pest_yolov8n_ip102_negatives.pt --check-images samples/
    python tools/export_onnx.py --disease-model ... --pest-model ... --out-dir exported/

For the disease model this writes <name>.onnx and <name>.json (class names and the exact preprocessing the C++ code
must reproduce). The check compares PyTorch and ONNX Runtime outputs on random inputs and, if given, on real images.
For the pest detector the Ultralytics exporter is used (fixed 640 x 640 input, NMS done by the application).

Requires: torch, torchvision, onnx, onnxruntime (and ultralytics for the pest detector).
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from predict import load_disease_model, preprocess, list_images  # noqa: E402  (same preprocessing as predict.py)

MAX_ABS_DIFF = 1e-3  # allowed difference between PyTorch and ONNX logits


def export_disease(model_path, out_dir, check_images):
    """Export the disease classifier to ONNX, write its preprocessing description and verify the outputs."""
    import onnxruntime as ort
    from PIL import Image

    model, ckpt = load_disease_model(model_path, "cpu")
    size = ckpt["img_size"]
    onnx_path = out_dir / (Path(model_path).stem + ".onnx")
    dummy = torch.randn(1, 3, size, size)
    kwargs = dict(input_names=["image"], output_names=["logits"], opset_version=17,
                  dynamic_axes={"image": {0: "batch"}, "logits": {0: "batch"}})
    try:
        torch.onnx.export(model, dummy, str(onnx_path), dynamo=False, **kwargs)  # classic exporter, stable output
    except TypeError:  # older PyTorch without the "dynamo" argument
        torch.onnx.export(model, dummy, str(onnx_path), **kwargs)

    spec = {"onnx_file": onnx_path.name, "input": "image", "output": "logits", "classes": ckpt["class_names"],
            "img_size": size, "color_order": "RGB", "resize": "direct resize to img_size x img_size, bilinear",
            "scale": "pixel / 255", "mean": ckpt["mean"], "std": ckpt["std"], "layout": "NCHW float32",
            "output_meaning": "logits; apply softmax for probabilities"}
    (out_dir / (Path(model_path).stem + ".json")).write_text(json.dumps(spec, indent=2) + "\n")

    # Equivalence check: random batch plus real images (if given)
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    batches = [torch.randn(4, 3, size, size)]
    for path in list_images(check_images) if check_images else []:
        with Image.open(path) as im:
            batches.append(preprocess(np.array(im.convert("RGB")), ckpt))
    worst, agree, total = 0.0, 0, 0
    with torch.no_grad():
        for x in batches:
            ref = model(x).numpy()
            out = session.run(["logits"], {"image": x.numpy()})[0]
            worst = max(worst, float(np.abs(ref - out).max()))
            agree += int((ref.argmax(1) == out.argmax(1)).sum())
            total += len(x)
    status = "OK" if worst <= MAX_ABS_DIFF and agree == total else "MISMATCH"
    print(f"[disease] {onnx_path}  size {onnx_path.stat().st_size / 1e6:.1f} MB | max |logit diff| {worst:.2e} | "
          f"same top-1 on {agree}/{total} inputs -> {status}")
    return status == "OK"


def letterbox_640(image_bgr):
    """Square 640 x 640 letterbox (grey 114 padding), RGB, /255, NCHW float32 - the exported model's input."""
    from ultralytics.data.augment import LetterBox
    padded = LetterBox(new_shape=(640, 640), auto=False)(image=image_bgr)
    return np.ascontiguousarray(padded[..., ::-1].transpose(2, 0, 1)[None], dtype=np.float32) / 255.0


def export_pest(model_path, out_dir, check_images):
    """Export the YOLO pest detector to ONNX and compare raw outputs with PyTorch on identical inputs.

    The exported model has a fixed 640 x 640 input, so both models are fed the same square letterboxed image.
    (Ultralytics' PyTorch predictor pads to a tighter rectangle instead, which gives slightly different confidences
    on the same photo; thresholds should therefore be confirmed with the square input used on the device.)
    """
    import cv2
    import onnxruntime as ort
    from ultralytics import YOLO

    exported = Path(YOLO(model_path).export(format="onnx", imgsz=640, opset=17, dynamic=False, simplify=False))
    onnx_path = out_dir / exported.name
    if exported.resolve() != onnx_path.resolve():
        shutil.move(str(exported), onnx_path)
    print(f"[pest] {onnx_path}  size {onnx_path.stat().st_size / 1e6:.1f} MB")

    net = YOLO(model_path).model.float().eval()
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    inputs = [np.random.rand(1, 3, 640, 640).astype(np.float32)]
    inputs += [letterbox_640(cv2.imread(str(p))) for p in (list_images(check_images) if check_images else [])]
    worst = 0.0
    with torch.no_grad():
        for x in inputs:
            ref = net(torch.from_numpy(x))
            ref = (ref[0] if isinstance(ref, (list, tuple)) else ref).numpy()
            out = session.run(None, {input_name: x})[0]
            worst = max(worst, float(np.abs(ref - out).max()))
    status = "OK" if worst <= MAX_ABS_DIFF * 10 else "MISMATCH"  # raw box coordinates are in pixels
    print(f"[pest] raw output {out.shape}, max |diff| over {len(inputs)} inputs: {worst:.2e} -> {status}")
    print("[pest] device input: 640 x 640 letterbox, grey (114) padding, RGB, /255, NCHW float32; "
          "output: 4 box values (cx, cy, w, h) + one score per class for 8400 candidates, NMS done by the app")
    return status == "OK"


def main():
    """Export whichever models are given and exit with an error if any check fails."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--disease-model", help="disease checkpoint (.pt) to export")
    parser.add_argument("--pest-model", help="YOLO pest detector (.pt) to export")
    parser.add_argument("--out-dir", default="exported", help="output folder (default: exported/)")
    parser.add_argument("--check-images", nargs="*", help="image files or folders for the equivalence check")
    args = parser.parse_args()
    if not args.disease_model and not args.pest_model:
        parser.error("give --disease-model and/or --pest-model")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ok = True
    if args.disease_model:
        ok &= export_disease(args.disease_model, out_dir, args.check_images)
    if args.pest_model:
        ok &= export_pest(args.pest_model, out_dir, args.check_images)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
