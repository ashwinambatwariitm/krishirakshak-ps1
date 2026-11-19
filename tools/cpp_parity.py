"""Parity test: the C++ pipeline must give the same answers as the Python reference (app/pipeline).

Runs both on the same photos and compares, per photo: top-1 disease class, all class probabilities (max absolute
difference), quality decision, estimated severity, and pest detections (species and box). Also reports the
accuracy of the C++ answers on the labelled PlantDoc full-photo test split.

Usage:
    python tools/cpp_parity.py --binary build/x86/krishirakshak --data-root /path/to/data [--int8]
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from app.pipeline.coordinator import DEFAULT_CONFIG
from app.pipeline.quality import check_quality, decode_image
from app.pipeline.severity import SeverityModel
from app.pipeline.vision import DiseaseClassifier, PestDetector

REPO = Path(__file__).resolve().parent.parent


def test_photos(data_root):
    """PlantDoc full-photo test split of the v5 manifest, with local paths and labels."""
    m = pd.read_csv(REPO / "results/disease_v5_six_classes/plantdoc_split_manifest.csv")
    t = m[(m.split == "test") & (m.kind == "full")].copy()
    t["local"] = (t.path.str.replace("/kaggle/input/datasets/nirmalsankalana/plantdoc-dataset/",
                                     f"{data_root}/plantdoc_cls/", regex=False)
                  .str.replace("/kaggle/input/datasets/yusufmurtaza01/plantdoc-object-detection-dataset/",
                               f"{data_root}/plantdoc_det/", regex=False))
    return t


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", default=str(REPO / "build/x86/krishirakshak"))
    parser.add_argument("--data-root", required=True)
    parser.add_argument("--int8", action="store_true")
    args = parser.parse_args()

    photos = test_photos(args.data_root)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(photos.local) + "\n")
        list_file = f.name
    cmd = [args.binary, "--root", str(REPO), "--no-llama", "--brief", "--list", list_file] + (["--int8"] if args.int8 else [])
    cpp = {}
    for line in subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.splitlines():
        r = json.loads(line)
        cpp[r["image"]] = r

    suffix = "_int8" if args.int8 else ""
    disease = DiseaseClassifier(str(DEFAULT_CONFIG["disease_onnx"]).replace(".onnx", f"{suffix}.onnx"),
                                DEFAULT_CONFIG["disease_spec"])
    severity = SeverityModel(DEFAULT_CONFIG["severity_onnx"], DEFAULT_CONFIG["severity_spec"])
    pest = PestDetector(str(DEFAULT_CONFIG["pest_onnx"]).replace(".onnx", f"{suffix}.onnx"), DEFAULT_CONFIG["pest_spec"],
                        DEFAULT_CONFIG["pest_labels"], DEFAULT_CONFIG["pest_config"])

    top1_same = quality_same = sev_same = pest_same = 0
    max_prob_diff = max_share_diff = 0.0
    cpp_correct = n = rejected = 0
    for path, label in zip(photos.local, photos.label):
        img = decode_image(Path(path).read_bytes())
        c = cpp[path]
        n += 1
        q = check_quality(img)
        quality_same += q["ok"] == c["quality"]["ok"]
        if not c["quality"]["ok"]:
            rejected += 1
            continue
        py_rank = disease.predict(img)
        py_probs = {r["class"]: r["probability"] for r in py_rank}
        cpp_probs = {r["class"]: r["probability"] for r in c["disease"]}
        top1_same += py_rank[0]["class"] == c["disease"][0]["class"]
        max_prob_diff = max(max_prob_diff, max(abs(py_probs[k] - v) for k, v in cpp_probs.items()))
        cpp_correct += disease.classes.index(c["disease"][0]["class"]) == label

        if "severity" in c:
            s = severity.estimate(img, c["disease"][0]["class"])   # severity is computed for the top class
            sev_same += s["level"] == c["severity"]["level"]
            if s["lesion_share"] is not None and c["severity"]["lesion_share"] is not None:
                max_share_diff = max(max_share_diff, abs(s["lesion_share"] - c["severity"]["lesion_share"]))
        else:
            sev_same += 1

        py_pests = [(p["species_id"], np.round(p["box_xyxy"], 0).tolist()) for p in pest.predict(img)]
        cpp_pests = [(p["species_id"], np.round(p["box_xyxy"], 0).tolist()) for p in c["pests"]]
        pest_same += py_pests == cpp_pests
        if py_pests != cpp_pests:
            print(f"pest difference on {Path(path).name}: python {py_pests} c++ {cpp_pests}")

    a = n - rejected
    print(f"photos: {n}   model: {'INT8' if args.int8 else 'FP32'}")
    print(f"quality decision identical:   {quality_same}/{n}   (rejected by the quality gate in both: {rejected})")
    print(f"top-1 disease identical:      {top1_same}/{a}   max |prob difference| {max_prob_diff:.2e}")
    print(f"severity level identical:     {sev_same}/{a}   max |lesion share difference| {max_share_diff:.2e}")
    print(f"pest detections identical:    {pest_same}/{a}")
    print(f"C++ top-1 accuracy: {cpp_correct / n:.3f} of all {n} test photos "
          f"(quality-rejected photos counted as wrong); {cpp_correct / a:.3f} of the {a} accepted photos")


if __name__ == "__main__":
    main()
