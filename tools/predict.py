"""Quick check of the PyTorch training checkpoints: tomato disease classifier and insect pest detector on photos.

This is a development tool for the first released checkpoints (v4 10-class disease model, IP102 species pest model).
The application on the Pi runs the deployed ONNX models in the C++ program (cpp/), see models/README.md.

Usage:
    python tools/predict.py leaf.jpg
    python tools/predict.py photos_folder/ --json predictions.json
    python tools/predict.py leaf.jpg --no-pest

By default the models are read from models/ (download them first, see models/README.md). The two models are
independent: the pest detector runs on every photo, even when the leaf looks healthy.

Preprocessing matches training exactly (RGB, direct resize to the model's input size with bilinear interpolation,
ImageNet mean/std), so results here should equal the evaluation results in results/.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from torch import nn
from torchvision import models

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DISEASE_MODEL = REPO / "models" / "tomato_disease_v4_effb0_10class.pt"
DEFAULT_PEST_MODEL = REPO / "models" / "pest_yolov8n_ip102_negatives.pt"
DEFAULT_PEST_CONFIG = REPO / "results" / "pest_yolov8n_with_negatives" / "pest_config.json"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# torchvision constructor and name of the final layer for each supported architecture
ARCHITECTURES = {
    "efficientnet_b0": (models.efficientnet_b0, 1),
    "mobilenet_v3_small": (models.mobilenet_v3_small, 3),
    "mobilenet_v3_large": (models.mobilenet_v3_large, 3),
}


def load_disease_model(path, device):
    """Load a disease checkpoint saved by the training scripts; returns (model, checkpoint info)."""
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    build, head_index = ARCHITECTURES[ckpt["arch"]]
    model = build(weights=None)
    head = model.classifier[head_index]
    model.classifier[head_index] = nn.Linear(head.in_features, len(ckpt["class_names"]))
    model.load_state_dict(ckpt["model_state_dict"])
    return model.eval().to(device), ckpt


def preprocess(image_rgb, ckpt):
    """RGB uint8 array -> normalised NCHW float tensor, exactly as in evaluation during training."""
    size = ckpt["img_size"]
    x = cv2.resize(image_rgb, (size, size), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
    x = (x - np.array(ckpt["mean"], np.float32)) / np.array(ckpt["std"], np.float32)
    return torch.from_numpy(x.transpose(2, 0, 1)).unsqueeze(0)


def classify_disease(model, ckpt, image_rgb, device, top_k):
    """Return the top_k (class name, probability) pairs for one image."""
    with torch.no_grad():
        probs = torch.softmax(model(preprocess(image_rgb, ckpt).to(device)), dim=1)[0].cpu().numpy()
    order = np.argsort(-probs)[:top_k]
    return [(ckpt["class_names"][i], float(probs[i])) for i in order]


def detect_pests(detector, image_path, conf, reliable_ids, device):
    """Run the pest detector; species are named only for ids that were reliable on the test set."""
    result = detector.predict(str(image_path), imgsz=640, conf=conf, device=device, verbose=False)[0]
    pests = []
    for box, score, cls in zip(result.boxes.xyxy.tolist(), result.boxes.conf.tolist(), result.boxes.cls.tolist()):
        cls = int(cls)
        pests.append({"species": result.names[cls], "species_reliable": cls in reliable_ids,
                      "confidence": round(float(score), 3), "box_xyxy": [round(v, 1) for v in box]})
    return pests


def list_images(inputs):
    """Expand the command-line inputs (files or folders) into a sorted list of image paths."""
    paths = []
    for item in map(Path, inputs):
        if item.is_dir():
            paths += sorted(p for p in item.rglob("*") if p.suffix.lower() in IMAGE_EXT)
        else:
            paths.append(item)
    return paths


def main():
    """Parse arguments, load the models once, and print a report for every image."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("images", nargs="+", help="image files or folders")
    parser.add_argument("--disease-model", default=str(DEFAULT_DISEASE_MODEL))
    parser.add_argument("--pest-model", default=str(DEFAULT_PEST_MODEL))
    parser.add_argument("--pest-config", default=str(DEFAULT_PEST_CONFIG),
                        help="pest_config.json with the list of reliably named species")
    parser.add_argument("--pest-conf", type=float, default=0.25, help="pest detection confidence (0.2 to 0.3)")
    parser.add_argument("--min-confidence", type=float, default=0.5,
                        help="below this disease probability the answer is reported as uncertain "
                             "(the application uses 0.85, chosen on validation data for the v5 model)")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--no-pest", action="store_true", help="run only the disease classifier")
    parser.add_argument("--json", help="also write all predictions to this JSON file")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, ckpt = load_disease_model(args.disease_model, device)
    detector, reliable_ids = None, set()
    if not args.no_pest:
        from ultralytics import YOLO  # imported here so the disease-only mode does not need ultralytics
        detector = YOLO(args.pest_model)
        if Path(args.pest_config).exists():
            reliable_ids = set(json.loads(Path(args.pest_config).read_text())["reliable_species_ids"])

    report = []
    for path in list_images(args.images):
        with Image.open(path) as im:
            image_rgb = np.array(im.convert("RGB"))
        top = classify_disease(model, ckpt, image_rgb, device, args.top_k)
        entry = {"image": str(path), "disease": top[0][0], "disease_probability": round(top[0][1], 3),
                 "disease_uncertain": top[0][1] < args.min_confidence,
                 "disease_top_k": [{"class": c, "probability": round(p, 3)} for c, p in top]}
        if detector is not None:
            entry["pests"] = detect_pests(detector, path, args.pest_conf, reliable_ids, device)
        report.append(entry)

        print(f"\n{path}")
        verdict = "UNCERTAIN - retake the photo or ask an expert" if entry["disease_uncertain"] else entry["disease"]
        print(f"  Disease : {verdict} ({top[0][1]:.0%})   others: "
              + ", ".join(f"{c} {p:.0%}" for c, p in top[1:]))
        if detector is not None:
            if not entry["pests"]:
                print("  Pests   : none detected")
            for pest in entry["pests"]:
                name = pest["species"] if pest["species_reliable"] else f"insect pest (possibly {pest['species']})"
                print(f"  Pest    : {name}, confidence {pest['confidence']:.2f}, box {pest['box_xyxy']}")

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
