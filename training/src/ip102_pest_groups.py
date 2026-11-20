# %% [markdown]
# # KrishiRakshak PS1 - IP102 pest detector: accuracy per ADVICE GROUP (evaluation only, CPU)
#
# The application gives pest advice per knowledge-base topic, and several topics are groups of IP102 species:
# `caterpillars` = 3 cutworms + 3 armyworms, `thrips` = 5 thrips species, `mites`, `aphids`. Today the app gives a
# topic's advice only when the detected *species* is "reliable" (species accuracy >= 70% on the IP102 test split);
# among the tomato pests only aphids pass, so a cutworm whose exact species is uncertain gets generic advice even when
# the detector is sure it is a caterpillar. This notebook measures how often the detector gets the **advice group**
# right, which is what decides the advice the farmer sees.
#
# It runs the **deployed ONNX models** (FP32 and the INT8 model used on the Raspberry Pi) with the same pre- and
# post-processing as `cpp/src/pest_detector.cpp`: square 640 letterbox with grey (114) padding, best class per
# candidate, score > threshold, class-aware NMS (IoU 0.7, class offset 7680, at most 300 boxes). Ground truth and the
# matching rule (IoU >= 0.5 with the best-overlapping kept box) are the same as in `ip102_pest_negft.py`, so the
# species numbers here can be compared with `results/pest_yolov8n_with_negatives/per_species_results.csv`.
#
# Two species-to-topic mappings are scored:
# - **kb**: the mapping in `app/kb/tomato_kb.json` today.
# - **extended**: a proposal that adds the other IP102 species of the same kind (more aphids and mites), maps
#   "Prodenia litura" (Spodoptera litura) to the Spodoptera topic, and adds whiteflies, leafhoppers, mealybugs and
#   fruit flies. Whether those topics' advice fits these species is a knowledge-base decision; the numbers only show
#   how well the detector separates the groups.
#
# **Kaggle setup:** Accelerator = None (CPU), Internet = on, attach `parserpixy/ip102-dataset` and the private
# dataset `bangadbilla420/krishirakshak-pest-onnx` (the two ONNX files, pest_labels.json, pest_config.json from
# release models-v2 / results/pest_yolov8n_with_negatives).

# %%
import os, sys, subprocess

ON_KAGGLE = os.path.exists("/kaggle/input")
SMOKE = os.environ.get("KR_SMOKE") == "1"
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "onnxruntime==1.23.2"], check=True)

# %%
import json, re, time
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import pandas as pd

print("onnxruntime", ort.__version__, "| opencv", cv2.__version__)

# %% [markdown]
# ## Configuration

# %%
INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "pest_groups"
WORK_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE = 640                       # the exported model's fixed input
NMS_IOU, MAX_DET, MAX_WH = 0.7, 300, 7680.0   # as in cpp/src/pest_detector.cpp
CONF_MIN = 0.05                      # candidates kept for the threshold grid (filtering after NMS is equivalent)
CONF_GRID = [0.2, 0.3, 0.5]          # 0.2 = the application's threshold (pest_config.json)
APP_CONF = 0.2
MATCH_IOU = 0.5
# Same bar as for species in ip102_pest_negft.py, applied to the advice group; plus precision of the group name
RELIABLE_MIN_TEST_BOXES, RELIABLE_MIN_ACC, RELIABLE_MIN_PRECISION = 10, 0.70, 0.70
MAX_TEST_IMAGES = 40 if SMOKE else None

IP102_NAMES = ['rice leaf roller', 'rice leaf caterpillar', 'paddy stem maggot', 'asiatic rice borer', 'yellow rice borer',
    'rice gall midge', 'Rice Stemfly', 'brown plant hopper', 'white backed plant hopper', 'small brown plant hopper',
    'rice water weevil', 'rice leafhopper', 'grain spreader thrips', 'rice shell pest', 'grub', 'mole cricket', 'wireworm',
    'white margined moth', 'black cutworm', 'large cutworm', 'yellow cutworm', 'red spider', 'corn borer', 'army worm',
    'aphids', 'Potosiabre vitarsis', 'peach borer', 'english grain aphid', 'green bug', 'bird cherry-oataphid',
    'wheat blossom midge', 'penthaleus major', 'longlegged spider mite', 'wheat phloeothrips', 'wheat sawfly',
    'cerodonta denticornis', 'beet fly', 'flea beetle', 'cabbage army worm', 'beet army worm', 'Beet spot flies',
    'meadow moth', 'beet weevil', 'sericaorient alismots chulsky', 'alfalfa weevil', 'flax budworm', 'alfalfa plant bug',
    'tarnished plant bug', 'Locustoidea', 'lytta polita', 'legume blister beetle', 'blister beetle',
    'therioaphis maculata Buckton', 'odontothrips loti', 'Thrips', 'alfalfa seed chalcid', 'Pieris canidia',
    'Apolygus lucorum', 'Limacodidae', 'Viteus vitifoliae', 'Colomerus vitis', 'Brevipoalpus lewisi McGregor',
    'oides decempunctata', 'Polyphagotars onemus latus', 'Pseudococcus comstocki Kuwana', 'parathrene regalis',
    'Ampelophaga', 'Lycorma delicatula', 'Xylotrechus', 'Cicadella viridis', 'Miridae', 'Trialeurodes vaporariorum',
    'Erythroneura apicalis', 'Papilio xuthus', 'Panonchus citri McGregor', 'Phyllocoptes oleiverus ashmead',
    'Icerya purchasi Maskell', 'Unaspis yanonensis', 'Ceroplastes rubens', 'Chrysomphalus aonidum',
    'Parlatoria zizyphus Lucus', 'Nipaecoccus vastalor', 'Aleurocanthus spiniferus', 'Tetradacus c Bactrocera minax',
    'Dacus dorsalis(Hendel)', 'Bactrocera tsuneonis', 'Prodenia litura', 'Adristyrannus', 'Phyllocnistis citrella Stainton',
    'Toxoptera citricidus', 'Toxoptera aurantii', 'Aphis citricola Vander Goot', 'Scirtothrips dorsalis Hood', 'Dasineura sp',
    'Lawana imitata Melichar', 'Salurnis marginella Guerr', 'Deporaus marginatus Pascoe', 'Chlumetia transversa',
    'Mango flat beak leafhopper', 'Rhytidodera bowrinii white', 'Sternochetus frigidus', 'Cicadellidae']
assert len(IP102_NAMES) == 102
NC = len(IP102_NAMES)

# Species -> advice topic. "kb" = app/kb/tomato_kb.json species_ids today; "extended" = proposal (see top).
MAPPINGS = {
    "kb": {"aphids": [24, 27, 29], "thrips": [12, 33, 53, 54, 92], "mites": [21, 32],
           "caterpillars": [18, 19, 20, 23, 38, 39]},
    # knowledge base after the advice-group change: Spodoptera litura ("Prodenia litura", 86) merged into caterpillars
    "kb_with_86": {"aphids": [24, 27, 29], "thrips": [12, 33, 53, 54, 92], "mites": [21, 32],
                   "caterpillars": [18, 19, 20, 23, 38, 39, 86]},
    "extended": {"aphids": [24, 27, 28, 29, 52, 89, 90, 91], "thrips": [12, 33, 53, 54, 92],
                 "mites": [21, 31, 32, 60, 61, 63, 74, 75], "caterpillars": [18, 19, 20, 23, 38, 39],
                 "spodoptera_tobacco_caterpillar": [86], "whitefly": [71, 82],
                 "leafhoppers": [11, 69, 72, 98, 101], "mealybug": [64, 81], "fruit_fly": [83, 84, 85]},
}
for name, m in MAPPINGS.items():
    ids = [s for v in m.values() for s in v]
    assert len(ids) == len(set(ids)), f"{name}: a species is in two groups"
# Name check of the proposed groups (ids are easy to get wrong by one)
_KEYWORDS = {"aphids": r"aphi|green bug|toxoptera", "thrips": r"thrips", "mites": r"spider|mite|penthaleus|colomerus|brevip|polyphagotars|panonchus|phyllocoptes",
             "caterpillars": r"cutworm|army worm", "spodoptera_tobacco_caterpillar": r"prodenia", "whitefly": r"trialeurodes|aleurocanthus",
             "leafhoppers": r"leafhopper|cicadell|erythroneura", "mealybug": r"pseudococcus|nipaecoccus", "fruit_fly": r"bactrocera|dacus"}
for g, ids in MAPPINGS["extended"].items():
    for s in ids:
        assert re.search(_KEYWORDS[g], IP102_NAMES[s], re.I), f"extended {g}: id {s} is '{IP102_NAMES[s]}'"
TOMATO_SPECIES = sorted({s for m in MAPPINGS.values() for v in m.values() for s in v})

def save_json(obj, name):
    """Write obj as indented JSON into WORK_DIR (numpy values are converted to plain Python)."""
    with open(WORK_DIR / name, "w") as f:
        json.dump(obj, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))

# %% [markdown]
# ## Locate the IP102 dataset and the ONNX models

# %%
def walk_dirs(root, max_depth=6):
    """os.walk below root up to max_depth, skipping folders that never need searching (keeps discovery fast)."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        p = Path(dirpath)
        if len(p.relative_to(root).parts) >= max_depth or p.name in ("Annotations", "JPEGImages"):
            dirnames[:] = []
        dirnames[:] = sorted(d for d in dirnames if "___" not in d)
        yield p, dirnames, filenames

def find_ip102():
    """Return the IP102 VOC root (Annotations/ + JPEGImages/) and the path of its test split file."""
    for d, dirs, files in walk_dirs(INPUT_ROOT):
        if "Annotations" in dirs and "JPEGImages" in dirs:
            for sd, _, sfiles in walk_dirs(d, max_depth=3):
                if "test.txt" in sfiles:
                    return d, sd / "test.txt"
            raise FileNotFoundError(f"IP102 found at {d} but without test.txt")
    raise FileNotFoundError("IP102 VOC folders (Annotations/, JPEGImages/) not found - attach parserpixy/ip102-dataset")

def find_file(name):
    """First file with this exact name below INPUT_ROOT."""
    for d, _, files in walk_dirs(INPUT_ROOT, max_depth=8):
        if name in files:
            return d / name
    raise FileNotFoundError(f"{name} not found - attach bangadbilla420/krishirakshak-pest-onnx")

IP_ROOT, TEST_TXT = find_ip102()
MODELS = {"fp32": find_file("pest_yolov8n_ip102_negatives.onnx"),
          "int8": find_file("pest_yolov8n_ip102_negatives_int8.onnx")}
LABELS = json.loads(find_file("pest_labels.json").read_text())["names"]
assert [n.strip() for n in LABELS] == [n.strip() for n in IP102_NAMES], "pest_labels.json differs from IP102_NAMES"
APP_CONFIG = json.loads(find_file("pest_config.json").read_text())
assert abs(APP_CONFIG["conf_threshold"] - APP_CONF) < 1e-9 and abs(APP_CONFIG["nms_iou"] - NMS_IOU) < 1e-9
print("IP102:", IP_ROOT, "| models:", {k: str(v) for k, v in MODELS.items()})

# %% [markdown]
# ## Ground truth of the official IP102 test split (same parsing as ip102_pest_negft.py)

# %%
def find_image(img_id):
    """Return the JPEGImages path of an IP102 image id, trying the common extensions."""
    for ext in (".jpg", ".jpeg", ".png", ".JPG"):
        p = IP_ROOT / "JPEGImages" / f"{img_id}{ext}"
        if p.exists():
            return p
    return None

def read_xml_objects(xml_path):
    """Return the <object> elements; files with extra text or a second <annotation> block are wrapped in one root."""
    text = xml_path.read_text(errors="ignore")
    try:
        return list(ET.fromstring(text).iter("object"))
    except ET.ParseError:
        body = re.sub(r"<\?xml[^>]*\?>", "", text)
        try:
            return list(ET.fromstring(f"<root>{body}</root>").iter("object"))
        except ET.ParseError:
            return None

def parse_one(img_id):
    """Image path, size and valid boxes (class id, x1, y1, x2, y2) of one IP102 test image; never raises."""
    rec = dict(id=img_id, image=None, boxes=[])
    try:
        xml_path, img_path = IP_ROOT / "Annotations" / f"{img_id}.xml", find_image(img_id)
        if img_path is None or not xml_path.exists():
            return rec
        im = cv2.imread(str(img_path))
        if im is None:
            return rec
        H, W = im.shape[:2]
        objects = read_xml_objects(xml_path) or []
        rec["image"] = str(img_path)
        for obj in objects:
            try:
                c = int(obj.findtext("name").strip())
                bb = obj.find("bndbox")
                x1, y1, x2, y2 = (float(bb.findtext(k)) for k in ("xmin", "ymin", "xmax", "ymax"))
            except Exception:
                continue
            if not 0 <= c < NC:
                continue
            x1, x2 = sorted((min(max(x1, 0), W), min(max(x2, 0), W)))
            y1, y2 = sorted((min(max(y1, 0), H), min(max(y2, 0), H)))
            if x2 - x1 < 2 or y2 - y1 < 2:
                continue
            if (c, x1, y1, x2, y2) not in rec["boxes"]:
                rec["boxes"].append((c, x1, y1, x2, y2))
    except Exception as e:
        print("skip", img_id, e)
    return rec

test_ids = [l.strip() for l in open(TEST_TXT) if l.strip()]
with ThreadPoolExecutor(16) as ex:
    TEST = [r for r in ex.map(parse_one, test_ids) if r["image"] and r["boxes"]]
if MAX_TEST_IMAGES:
    TEST = TEST[:MAX_TEST_IMAGES]
gt_counts = Counter(b[0] for r in TEST for b in r["boxes"])
print(f"test images: {len(TEST)} | boxes: {sum(gt_counts.values())} | "
      f"tomato-relevant boxes: {sum(gt_counts[s] for s in TOMATO_SPECIES)}")

# %% [markdown]
# ## Inference exactly as the application does it (cpp/src/pest_detector.cpp)

# %%
def letterbox(rgb):
    """Square letterbox like the C++ code / Ultralytics LetterBox(auto=False): returns NCHW float input, ratio, pads."""
    h, w = rgb.shape[:2]
    r = min(IMG_SIZE / h, IMG_SIZE / w)
    new_w, new_h = round(w * r), round(h * r)          # Python round = half to even, as std::nearbyint
    dw, dh = (IMG_SIZE - new_w) / 2, (IMG_SIZE - new_h) / 2
    if (new_w, new_h) != (w, h):
        rgb = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    top, bottom, left, right = round(dh - 0.1), round(dh + 0.1), round(dw - 0.1), round(dw + 0.1)
    padded = cv2.copyMakeBorder(rgb, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
    x = np.ascontiguousarray(padded.transpose(2, 0, 1)[None], dtype=np.float32) / 255.0
    return x, r, left, top

def iou_xyxy(a, b):
    """IoU between one box a (4,) and boxes b (n, 4)."""
    x1 = np.maximum(a[0], b[:, 0]); y1 = np.maximum(a[1], b[:, 1])
    x2 = np.minimum(a[2], b[:, 2]); y2 = np.minimum(a[3], b[:, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area = lambda z: (z[..., 2] - z[..., 0]) * (z[..., 3] - z[..., 1])
    return inter / (area(a) + area(b) - inter + 1e-9)

def detect(session, path):
    """Boxes (n, 4) in photo pixels, best score (n,), best class (n,) and all class scores (n, 102) after NMS."""
    rgb = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)
    H, W = rgb.shape[:2]
    x, r, left, top = letterbox(rgb)
    out = session.run(None, {session.get_inputs()[0].name: x})[0][0]      # (4 + 102, candidates)
    scores_all = out[4:].T                                                 # (candidates, 102)
    best = scores_all.argmax(1)
    best_score = scores_all[np.arange(len(best)), best]
    keep = best_score > CONF_MIN
    cx, cy, w, h = out[:4, keep]
    boxes = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 1)
    best, best_score, scores_all = best[keep], best_score[keep], scores_all[keep]
    shifted = boxes + (best * MAX_WH)[:, None]                             # class-aware NMS
    order = np.argsort(-best_score, kind="stable")
    removed = np.zeros(len(order), bool)
    kept = []
    for i in range(len(order)):
        if removed[i]:
            continue
        kept.append(order[i])
        if len(kept) >= MAX_DET:
            break
        rest = np.arange(i + 1, len(order))
        rest = rest[~removed[rest]]
        if len(rest):
            removed[rest[iou_xyxy(shifted[order[i]], shifted[order[rest]]) > NMS_IOU]] = True
    kept = np.array(kept, int)
    b = boxes[kept]
    b = np.stack([np.clip((b[:, 0] - left) / r, 0, W), np.clip((b[:, 1] - top) / r, 0, H),
                  np.clip((b[:, 2] - left) / r, 0, W), np.clip((b[:, 3] - top) / r, 0, H)], 1)
    return b, best_score[kept], best[kept], scores_all[kept]

PRED = {}
for tag, path in MODELS.items():
    opts = ort.SessionOptions()
    session = ort.InferenceSession(str(path), opts, providers=["CPUExecutionProvider"])
    t0 = time.time()
    PRED[tag] = [detect(session, r["image"]) for r in TEST]
    print(f"[{tag}] {len(TEST)} images in {time.time() - t0:.0f}s")

if SMOKE:   # fake images give no detections: add one per ground-truth box (every third one with a wrong species)
    for tag in PRED:
        for n, r in enumerate(TEST):
            gt = np.array([b[1:] for b in r["boxes"]], float)
            cls = np.array([(b[0] + (n % 3 == 0)) % NC for b in r["boxes"]])
            scores = np.full((len(gt), NC), 0.01, np.float32); scores[np.arange(len(gt)), cls] = 0.9
            PRED[tag][n] = (gt, scores.max(1), cls, scores)

# %% [markdown]
# ## Scoring: species, advice group (best class), advice group (summed class scores)
# Every ground-truth box is matched to the kept box with the highest IoU (found if IoU >= 0.5), as in the fine-tuning
# notebook. "Group by sum" adds the class scores of each group for the matched box and picks the largest group (all
# other species together form "other"). Precision: of all kept boxes whose best class is in group G, the share that
# overlaps (IoU >= 0.5) a ground-truth box of group G - i.e. how often the app is right when it says "G".

# %%
def iou_matrix(a, b):
    """Pairwise IoU between box arrays a (n, 4) and b (m, 4) in x1y1x2y2 format."""
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    x1 = np.maximum(a[:, None, 0], b[None, :, 0]); y1 = np.maximum(a[:, None, 1], b[None, :, 1])
    x2 = np.minimum(a[:, None, 2], b[None, :, 2]); y2 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area = lambda z: (z[:, 2] - z[:, 0]) * (z[:, 3] - z[:, 1])
    return inter / (area(a)[:, None] + area(b)[None, :] - inter + 1e-9)

def score(preds, mapping, conf):
    """Per-box records for every ground-truth box, and per predicted box records, at one threshold."""
    group_of = {s: g for g, ids in mapping.items() for s in ids}
    groups = list(mapping)
    member = np.zeros((len(groups) + 1, NC), np.float32)                  # last row = "other"
    for gi, g in enumerate(groups):
        member[gi, mapping[g]] = 1
    member[-1] = 1 - member[:-1].sum(0)
    gt_rows, pred_rows = [], []
    for r, (pb, pc, pk, ps) in zip(TEST, preds):
        keep = pc > conf
        pb, pk, ps = pb[keep], pk[keep], ps[keep]
        gt = np.array([b[1:] for b in r["boxes"]], float)
        gt_cls = np.array([b[0] for b in r["boxes"]])
        iou = iou_matrix(gt, pb)
        for j, c in enumerate(gt_cls):
            row = dict(species=int(c), group=group_of.get(int(c), "other"), found=False)
            if len(pb) and iou[j].max() >= MATCH_IOU:
                k = int(iou[j].argmax())
                top2 = np.argsort(-ps[k])[:2]
                sums = member @ ps[k]
                row.update(found=True, pred_species=int(pk[k]), species_ok=int(pk[k]) == c,
                           species_top2_ok=c in top2.tolist(), pred_group=group_of.get(int(pk[k]), "other"),
                           pred_group_sum=(groups + ["other"])[int(sums.argmax())])
            gt_rows.append(row)
        for k in range(len(pb)):
            g = group_of.get(int(pk[k]), "other")
            hit = False
            if len(gt):
                same = np.array([group_of.get(int(c), "other") == g for c in gt_cls])
                hit = bool((iou[:, k][same] >= MATCH_IOU).any()) if same.any() else False
            pred_rows.append(dict(pred_group=g, correct=hit))
    gt_cols = ["species", "group", "found", "pred_species", "species_ok", "species_top2_ok", "pred_group", "pred_group_sum"]
    gt_df = pd.DataFrame(gt_rows).reindex(columns=gt_cols)
    # Boxes that were not found have no prediction: keep the flags real booleans and the species ids integers
    for col in ("found", "species_ok", "species_top2_ok"):
        gt_df[col] = gt_df[col].fillna(False).astype(bool)
    gt_df["pred_species"] = gt_df.pred_species.fillna(-1).astype(int)
    return gt_df, pd.DataFrame(pred_rows).reindex(columns=["pred_group", "correct"])

def group_table(gt, pr, mapping):
    """One row per group: boxes, found rate, species / group accuracy when found, precision of the group name."""
    rows = []
    for g in mapping:
        s = gt[gt.group == g]
        f = s[s.found]
        p = pr[pr.pred_group == g]
        rows.append(dict(group=g, species=len(mapping[g]), test_boxes=len(s),
                         found_rate=len(f) / max(len(s), 1),
                         species_acc_when_found=f.species_ok.mean() if len(f) else np.nan,
                         species_top2_acc_when_found=f.species_top2_ok.mean() if len(f) else np.nan,
                         group_acc_when_found=(f.pred_group == g).mean() if len(f) else np.nan,
                         group_sum_acc_when_found=(f.pred_group_sum == g).mean() if len(f) else np.nan,
                         group_correct_overall=(f.pred_group == g).sum() / max(len(s), 1),
                         predicted_boxes=len(p), group_precision=p.correct.mean() if len(p) else np.nan))
    t = pd.DataFrame(rows)
    t["reliable_group"] = ((t.test_boxes >= RELIABLE_MIN_TEST_BOXES) & (t.group_acc_when_found >= RELIABLE_MIN_ACC)
                           & (t.group_precision >= RELIABLE_MIN_PRECISION))
    return t

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
ALL_GROUPS, SPECIES_ROWS, CONFUSION = [], [], {}
for tag in MODELS:
    for mname, mapping in MAPPINGS.items():
        for conf in CONF_GRID:
            gt, pr = score(PRED[tag], mapping, conf)
            t = group_table(gt, pr, mapping)
            t.insert(0, "conf", conf); t.insert(0, "mapping", mname); t.insert(0, "model", tag)
            ALL_GROUPS.append(t)
            if conf == APP_CONF:
                f = gt[gt.found & (gt.group != "other")]
                CONFUSION[(tag, mname)] = pd.crosstab(f.group, f.pred_group)
                if mname == "extended":           # per-species view (all tomato-relevant species are in "extended")
                    for c in TOMATO_SPECIES:
                        s = gt[gt.species == c]; fs = s[s.found]
                        SPECIES_ROWS.append(dict(model=tag, class_id=c, name=IP102_NAMES[c], group=s.group.iloc[0] if len(s) else "",
                                                 test_boxes=len(s), found_rate=len(fs) / max(len(s), 1),
                                                 species_acc_when_found=fs.species_ok.mean() if len(fs) else np.nan,
                                                 species_top2_acc_when_found=fs.species_top2_ok.mean() if len(fs) else np.nan,
                                                 group_acc_when_found=(fs.pred_group == fs.group).mean() if len(fs) else np.nan,
                                                 most_confused_with=Counter(IP102_NAMES[p] for p in fs.pred_species[~fs.species_ok]).most_common(2)
                                                 if len(fs) else []))

groups_df = pd.concat(ALL_GROUPS, ignore_index=True)
species_df = pd.DataFrame(SPECIES_ROWS)
groups_df.to_csv(WORK_DIR / "group_results.csv", index=False)
species_df.to_csv(WORK_DIR / "species_results.csv", index=False)
for (tag, mname), cm in CONFUSION.items():
    cm.to_csv(WORK_DIR / f"group_confusion_{tag}_{mname}.csv")

for tag in MODELS:
    for mname in MAPPINGS:
        sel = groups_df[(groups_df.model == tag) & (groups_df.mapping == mname) & (groups_df.conf == APP_CONF)]
        print(f"\n=== {tag} | mapping {mname} | threshold {APP_CONF}")
        print(sel.drop(columns=["model", "mapping", "conf"]).round(3).to_string(index=False))
        print(CONFUSION[(tag, mname)].to_string())
print("\n=== per species (int8, threshold 0.2)")
print(species_df[species_df.model == "int8"].drop(columns="model").round(3).to_string(index=False))

# %% [markdown]
# ## Summary for the application

# %%
summary = {"test_images": len(TEST), "app_threshold": APP_CONF, "reliable_rule": dict(
               min_test_boxes=RELIABLE_MIN_TEST_BOXES, min_group_acc_when_found=RELIABLE_MIN_ACC,
               min_group_precision=RELIABLE_MIN_PRECISION),
           "mappings": MAPPINGS, "results": {}}
for tag in MODELS:
    for mname in MAPPINGS:
        sel = groups_df[(groups_df.model == tag) & (groups_df.mapping == mname) & (groups_df.conf == APP_CONF)]
        summary["results"][f"{tag}_{mname}"] = {
            "reliable_groups": sel[sel.reliable_group].group.tolist(),
            "groups": sel.drop(columns=["model", "mapping", "conf"]).round(4).to_dict(orient="records")}
save_json(summary, "results.json")
print(json.dumps({k: v["reliable_groups"] for k, v in summary["results"].items()}, indent=1))
print(sorted(p.name for p in WORK_DIR.iterdir()))
