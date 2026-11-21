"""Compare the IP102 species pest model and the advice-group pest model on the independent 8-tomato-pest set.

Data: "A database of eight common tomato pest images" (Mei-Ling Huang, Tzu Chin Chuang, Mendeley Data V1, 2020,
doi:10.17632/s62zm6djd2.1, CC BY 4.0), file "Original image of tomato pest.7z" (609 photos, one folder per pest).
The 31 photos that are near-copies of IP102 images (results/pest_independent_huang/per_image.csv, column
near_duplicate) are left out, so both models are scored on the same 578 photos as in that evaluation.

Detection copies cpp/src/pest_detector.cpp (letterbox 640 with grey 114 padding, best class per candidate,
class-aware greedy NMS); the advice of a photo is the set of knowledge-base topics of all its boxes, as in the app.
Small enough for a laptop CPU (about 3 minutes for both INT8 models).

Usage:
    python tools/eval_pest_independent.py --huang "DIR/Original image of tomato pest" \
        --species-onnx models/pest_yolov8n_ip102_negatives_int8.onnx \
        --groups-onnx models/pest_yolov8n_groups_int8.onnx --out results/pest_groups/independent_huang
    add --fp32 to also score the FP32 ONNX files (results/pest_groups/independent_huang_fp32)
"""
import argparse
import glob
import json
import os

import cv2
import numpy as np
import onnxruntime as ort
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Expected knowledge-base topic per folder of the Huang set
EXPECT = {"TU": "mites", "MP": "aphids", "TP": "thrips", "SE": "caterpillars", "SL": "spodoptera_tobacco_caterpillar",
          "HA": "helicoverpa_fruit_borer", "BA": "whitefly", "ZC": "fruit_fly"}
CATERPILLAR_FAMILY = {"SL", "HA"}   # general caterpillar advice for these two is counted separately, not as right


def letterbox(img, size=640):
    """Square letterbox as in pest_detector.cpp (numpy rounds half to even, like roundHalfEven there)."""
    h, w = img.shape[:2]
    r = min(size / h, size / w)
    nw, nh = int(np.round(w * r)), int(np.round(h * r))
    dw, dh = (size - nw) / 2, (size - nh) / 2
    if (nw, nh) != (w, h):
        img = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    top, bottom = int(np.round(dh - 0.1)), int(np.round(dh + 0.1))
    left, right = int(np.round(dw - 0.1)), int(np.round(dw + 0.1))
    return cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))


def iou(a, b):
    """Intersection over union of two (x1, y1, x2, y2) boxes."""
    x1, y1, x2, y2 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    return inter / ((a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter + 1e-9)


def detect(sess, rgb, conf, nms=0.7, max_det=300):
    """(score, class) of the boxes the app keeps for one RGB photo."""
    x = letterbox(rgb).astype(np.float32).transpose(2, 0, 1)[None] / 255.0
    out = sess.run(None, {sess.get_inputs()[0].name: x})[0][0]      # (4 + classes, candidates)
    best, score = out[4:].argmax(0), out[4:].max(0)
    cand = []
    for i in np.nonzero(score > conf)[0]:
        cx, cy, w, h = out[:4, i]
        off = best[i] * 7680.0                                      # class offset: classes do not suppress each other
        cand.append((float(score[i]), int(best[i]), (cx - w / 2 + off, cy - h / 2 + off, cx + w / 2 + off, cy + h / 2 + off)))
    cand.sort(key=lambda c: -c[0])
    kept = []
    for c in cand:
        if len(kept) < max_det and all(iou(c[2], k[2]) <= nms for k in kept):
            kept.append(c)
    return [(s, k) for s, k, _ in kept]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--huang", required=True, help="folder with the eight pest folders (TU, MP, TP, ...)")
    ap.add_argument("--species-onnx", default=f"{REPO}/models/pest_yolov8n_ip102_negatives_int8.onnx")
    ap.add_argument("--groups-onnx", default=f"{REPO}/models/pest_yolov8n_groups_int8.onnx")
    ap.add_argument("--out", default=f"{REPO}/results/pest_groups/independent_huang")
    ap.add_argument("--fp32", action="store_true", help="also score the FP32 ONNX files (same names without _int8)")
    args = ap.parse_args()

    kb = json.load(open(f"{REPO}/app/kb/tomato_kb.json"))
    topic_of_species = {s: t for t, v in kb["topics"].items() for s in v.get("species_ids", [])}
    sp_cfg = json.load(open(f"{REPO}/results/pest_yolov8n_with_negatives/pest_config.json"))
    sp_reliable = set(sp_cfg["reliable_species_ids"])
    sp_groups = set(sp_cfg.get("reliable_groups", ["caterpillars", "thrips"]))   # rule of PR #8
    gr_cfg = json.load(open(f"{REPO}/results/pest_groups/pest_config.json"))
    gr_topic = {int(k): v for k, v in gr_cfg["topic_by_class"].items()}
    gr_reliable = set(gr_cfg["reliable_species_ids"])

    # Advice rules (knowledge-base topic of one box)
    rules = {
        "species model, species rule": (args.species_onnx, sp_cfg["conf_threshold"],
            lambda k: topic_of_species.get(k, "insect_other") if k in sp_reliable else "insect_other"),
        "species model, group rule (PR #8)": (args.species_onnx, sp_cfg["conf_threshold"],
            lambda k: topic_of_species.get(k, "insect_other")
            if k in sp_reliable or topic_of_species.get(k) in sp_groups else "insect_other"),
        "group model, reliable groups": (args.groups_onnx, gr_cfg["conf_threshold"],
            lambda k: gr_topic[k] if k in gr_reliable else "insect_other"),
        "group model, all groups": (args.groups_onnx, gr_cfg["conf_threshold"], lambda k: gr_topic[k]),
    }
    # FP32 versions of both models (same thresholds as the INT8 app files) for the precision comparison
    if args.fp32:
        rules["species model FP32, group rule (PR #8)"] = (args.species_onnx.replace("_int8", ""), sp_cfg["conf_threshold"],
            rules["species model, group rule (PR #8)"][2])
        rules["group model FP32, reliable groups"] = (args.groups_onnx.replace("_int8", ""), gr_cfg["conf_threshold"],
            rules["group model, reliable groups"][2])
    near = pd.read_csv(f"{REPO}/results/pest_independent_huang/per_image.csv")
    skip = set(near[near.near_duplicate.astype(bool)].image)

    sessions, detections, rows = {}, {}, []
    for rule, (path, conf, topic_of) in rules.items():
        if path not in sessions:
            so = ort.SessionOptions(); so.intra_op_num_threads = 4
            sessions[path] = ort.InferenceSession(path, so, providers=["CPUExecutionProvider"])
        for cls, expected in EXPECT.items():
            for f in sorted(glob.glob(os.path.join(args.huang, cls, "*"))):
                name = os.path.basename(f)
                if name in skip or not name.lower().endswith((".jpg", ".jpeg", ".png")):
                    continue
                key = (path, f)
                if key not in detections:
                    bgr = cv2.imread(f)
                    detections[key] = None if bgr is None else detect(sessions[path], cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), conf)
                dets = detections[key]
                if dets is None:
                    continue
                topics = {topic_of(k) for _, k in dets}
                wrong = topics - {expected, "insect_other"} - ({"caterpillars"} if cls in CATERPILLAR_FAMILY else set())
                rows.append(dict(rule=rule, pest=cls, image=name, insect_found=bool(dets), right_advice=expected in topics,
                                 caterpillar_advice_for_spodoptera_helicoverpa=cls in CATERPILLAR_FAMILY and "caterpillars" in topics,
                                 wrong_pest_advice=bool(wrong), generic_only=topics == {"insect_other"}))
    df = pd.DataFrame(rows)
    os.makedirs(args.out, exist_ok=True)
    df.to_csv(os.path.join(args.out, "per_image.csv"), index=False)
    cols = ["insect_found", "right_advice", "caterpillar_advice_for_spodoptera_helicoverpa", "wrong_pest_advice", "generic_only"]
    summary = (df.groupby("rule", sort=False)[cols].mean() * 100).round(1)
    summary.insert(0, "photos", df.groupby("rule", sort=False).size())
    summary.to_csv(os.path.join(args.out, "summary.csv"))
    per_pest = (df.pivot_table(index="pest", columns="rule", values="right_advice", aggfunc="mean", sort=False) * 100).round(0)
    per_pest.to_csv(os.path.join(args.out, "right_advice_per_pest.csv"))
    pd.set_option("display.width", 200)
    print(summary.to_string()); print("\nright advice per pest (%):"); print(per_pest.to_string())


if __name__ == "__main__":
    main()
