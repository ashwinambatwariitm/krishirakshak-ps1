"""Validate the colour-based disease severity rule against expert lesion masks (PlantSeg test split, tomato).

PlantSeg (Wei et al. 2024, CC BY-NC-ND 4.0) has lesion masks checked by plant pathologists for in-the-wild photos.
Its images and masks are NOT stored in this repository (licence: no redistribution, no derivatives); only the
metrics computed here are. Download: Hugging Face dataset Voxel51/PlantSeg-Test (samples.json + data/tomato_*.jpg).

PlantSeg has lesion masks but no leaf masks, so severity is checked in two parts:
  1. lesion detection: predicted lesion pixels vs the expert mask (precision, recall, IoU, Dice), per image and pooled;
  2. severity level: lesion share = lesion pixels / leaf pixels, where both the prediction and the reference use
     the same leaf mask (the method's own leaf estimate), so the comparison isolates the lesion detection error.
     Reference level = level of (expert lesion pixels inside the leaf / leaf pixels).
Images are split by a fixed hash of the file name into a tuning half and a held-out half; report the held-out half.

Methods (all on a 512 px copy, OpenCV HSV, hue 0-179; same constants as app/pipeline/severity.py):
  M0 whole photo   plant = S>=40 & V>=40 (7x7 close); lesion = plant & not green(H 35-85, S>=40)  [current rule]
  M1 main leaf     leaf = largest connected plant region, holes filled; lesion = leaf & not green
  M2 large leaves  leaf = all plant regions >= 5% of the image, holes filled; lesion = leaf & not green
  MODEL            the leaf + lesion segmentation model (--onnx, training/src/lesion_seg.py): leaf = leaf output,
                   lesion = lesion output inside the leaf (sigmoid > 0.5)

Usage: python tools/eval_severity_plantseg.py --root <PlantSeg_test folder> --out results/severity_plantseg/eval.json
       [--onnx severity_lraspp_mnv3.onnx --spec severity_spec.json]   (adds the MODEL method)
"""
import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

SIDE = 512
SAT_MIN, VAL_MIN = 40, 40
GREEN = (35, 85)
LEVELS = [(0.10, "low"), (0.25, "moderate"), (1.01, "high")]


def level(share):
    return next(name for bound, name in LEVELS if share < bound)


def fill_holes(mask):
    """Fill enclosed holes (dark lesion centres inside a leaf) by flood-filling the background from the border."""
    m = mask.astype(np.uint8) * 255
    h, w = m.shape
    padded = cv2.copyMakeBorder(m, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    flood = padded.copy()
    cv2.floodFill(flood, np.zeros((h + 4, w + 4), np.uint8), (0, 0), 255)
    holes = cv2.bitwise_not(flood)[1:-1, 1:-1]
    return (m | holes) > 0


class OnnxSeverity:
    """Leaf + lesion segmentation model exported by training/src/lesion_seg.py."""

    def __init__(self, onnx_path, spec_path):
        import onnxruntime as ort
        self.spec = json.loads(Path(spec_path).read_text())
        self.sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
        self.size = self.spec["input"]["size"]
        self.mean = np.array(self.spec["input"]["mean"], np.float32)
        self.std = np.array(self.spec["input"]["std"], np.float32)

    def __call__(self, rgb):
        h, w = rgb.shape[:2]
        x = cv2.resize(rgb, (self.size, self.size), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        x = ((x - self.mean) / self.std).transpose(2, 0, 1)[None]
        logits = self.sess.run(None, {self.spec["input"]["name"]: x})[0][0]
        leaf = cv2.resize(logits[0], (w, h)) > 0          # sigmoid > 0.5  <=>  logit > 0
        lesion = (cv2.resize(logits[1], (w, h)) > 0) & leaf
        return leaf, lesion


MODEL = None


def masks(rgb, method):
    if method == "MODEL":
        return MODEL(rgb)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    plant = (sat >= SAT_MIN) & (val >= VAL_MIN)
    plant = cv2.morphologyEx(plant.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)).astype(bool)
    green = (hue >= GREEN[0]) & (hue <= GREEN[1]) & (sat >= SAT_MIN)
    if method == "M0":
        leaf = plant
    else:
        n, lab, stats, _ = cv2.connectedComponentsWithStats(plant.astype(np.uint8), connectivity=8)
        if n <= 1:
            return plant & False, plant & False
        areas = stats[1:, cv2.CC_STAT_AREA]
        if method == "M1":
            keep = [1 + int(np.argmax(areas))]
        else:
            keep = [1 + i for i, a in enumerate(areas) if a >= 0.05 * plant.size] or [1 + int(np.argmax(areas))]
        leaf = fill_holes(np.isin(lab, keep))
    return leaf, leaf & ~green


def gt_mask(sample, shape):
    h, w = shape
    m = np.zeros((h, w), np.uint8)
    for poly in sample.get("segmentations", {}).get("polylines", []):
        for ring in poly["points"]:
            pts = np.array([[x * w, y * h] for x, y in ring], np.int32)
            if len(pts) >= 3:
                cv2.fillPoly(m, [pts], 1)
    return m.astype(bool)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--onnx", help="severity model (adds method MODEL)")
    ap.add_argument("--spec", help="its severity_spec.json")
    args = ap.parse_args()
    global MODEL
    methods = ["M0", "M1", "M2"]
    if args.onnx:
        MODEL = OnnxSeverity(args.onnx, args.spec)
        methods.append("MODEL")
    root = Path(args.root)
    samples = json.loads((root / "tomato_samples.json").read_text())

    rows = []
    for s in samples:
        img = cv2.imread(str(root / s["filepath"]))
        if img is None:
            continue
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        scale = SIDE / max(h, w)
        small = cv2.resize(rgb, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
        gt = gt_mask(s, small.shape[:2])
        name = Path(s["filepath"]).name
        split = "tune" if int(hashlib.sha1(name.encode()).hexdigest(), 16) % 2 == 0 else "test"
        row = {"image": name, "disease": s["disease"], "split": split, "gt_image_share": float(gt.mean())}
        for m in methods:
            leaf, les = masks(small, m)
            tp = int((les & gt).sum())
            row[m] = {"tp": tp, "pred": int(les.sum()), "gt": int(gt.sum()), "leaf": int(leaf.sum()),
                      "gt_in_leaf": int((gt & leaf).sum())}
            if leaf.sum() >= 0.05 * leaf.size:
                pred_share = les.sum() / leaf.sum()
                ref_share = (gt & leaf).sum() / leaf.sum()
                row[m].update(pred_share=float(pred_share), ref_share=float(ref_share),
                              pred_level=level(pred_share), ref_level=level(ref_share))
        rows.append(row)

    summary = {}
    for split in ("tune", "test", "all"):
        sel = [r for r in rows if split == "all" or r["split"] == split]
        summary[split] = {"images": len(sel)}
        for m in methods:
            tp = sum(r[m]["tp"] for r in sel)
            pred = sum(r[m]["pred"] for r in sel)
            gt = sum(r[m]["gt"] for r in sel)
            graded = [r[m] for r in sel if "pred_level" in r[m]]
            agree = sum(g["pred_level"] == g["ref_level"] for g in graded)
            share_err = [abs(g["pred_share"] - g["ref_share"]) for g in graded]
            coverage = sum(r[m]["gt_in_leaf"] for r in sel) / max(1, gt)
            summary[split][m] = {
                "lesion_precision": round(tp / max(1, pred), 3), "lesion_recall": round(tp / max(1, gt), 3),
                "lesion_iou": round(tp / max(1, pred + gt - tp), 3),
                "lesion_dice": round(2 * tp / max(1, pred + gt), 3),     # same pooled pixel counts as the IoU
                "expert_lesion_inside_leaf_mask": round(coverage, 3),
                "graded_images": len(graded), "level_agreement": round(agree / max(1, len(graded)), 3),
                "median_abs_share_error": round(float(np.median(share_err)), 3) if share_err else None,
                "confusion": {f"{a}->{b}": sum(1 for g in graded if g["ref_level"] == a and g["pred_level"] == b)
                              for a in ("low", "moderate", "high") for b in ("low", "moderate", "high")}}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps({"summary": summary, "images": rows}, indent=1))
    for split in ("tune", "test"):
        print(f"== {split} ({summary[split]['images']} images)")
        for m in methods:
            v = summary[split][m]
            print(f"  {m}: lesion P {v['lesion_precision']:.2f} R {v['lesion_recall']:.2f} IoU {v['lesion_iou']:.2f} | "
                  f"expert lesion inside leaf {v['expert_lesion_inside_leaf_mask']:.2f} | level agreement "
                  f"{v['level_agreement']:.2f} on {v['graded_images']} | median share error {v['median_abs_share_error']}")


if __name__ == "__main__":
    main()
