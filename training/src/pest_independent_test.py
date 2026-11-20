# %% [markdown]
# # KrishiRakshak PS1 - pest detector on an independent test set (8 tomato pests, CPU)
#
# The IP102 test split comes from the same web collection as the training data. This notebook scores the deployed
# pest detector on photos from **other sources**: the 609 original images of "A database of eight common tomato pest
# images" (Mei-Ling Huang, Tzu Chin Chuang, Mendeley Data V1, 2020, doi:10.17632/s62zm6djd2.1, **CC BY 4.0**),
# collected from IPMImages, NBAIR (India) and Google search. Insects are photographed on plants (leaves, fruit, cotton,
# maize, ...), not only on tomato, and images are 299 x 299, so this is an out-of-source check, not a tomato field test.
#
# - **Leakage check:** IP102 was also collected from the web, so every image is compared with all IP102 images by a
#   perceptual hash (full image and centre square). Results are reported with and without near-duplicates.
# - **Detector:** the deployed ONNX models (FP32, INT8) with the application's own pre/post-processing
#   (`cpp/src/pest_detector.cpp`), threshold 0.2.
# - **Advice the farmer would see**, per image (all boxes above the threshold), under three rules:
#   `today` - a topic only for species in `reliable_species_ids` (pest_config.json), otherwise `insect_other`;
#   `group_kb` - also the topic of a species whose advice group is reliable (caterpillars, thrips; results of
#   ip102_pest_groups.py), knowledge-base mapping of today; `group_extended` - the same with the extended mapping
#   (Spodoptera litura, whitefly, fruit flies, more aphids and mites) and its reliable groups.
#
# **Kaggle setup:** Accelerator = None (CPU), Internet = on, attach `parserpixy/ip102-dataset`,
# `bangadbilla420/krishirakshak-pest-onnx` and `bangadbilla420/tomato-pest-8-originals-huang`.

# %%
import os, sys, subprocess

ON_KAGGLE = os.path.exists("/kaggle/input")
SMOKE = os.environ.get("KR_SMOKE") == "1"
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "onnxruntime==1.23.2"], check=True)

# %%
import json, re, time, zipfile
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
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "pest_independent"
WORK_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE, NMS_IOU, MAX_DET, MAX_WH, CONF_MIN = 640, 0.7, 300, 7680.0, 0.05   # as cpp/src/pest_detector.cpp
APP_CONF = 0.2
HASH_MAX_DIST = 8                     # Hamming distance (of 64 bits) for a near-duplicate
MAX_IP102_IMAGES = 300 if SMOKE else None

# Huang & Chuang folders -> species, expected knowledge-base topic, IP102 ids of the same insect (if any)
CLASSES = {
    "TU": ("Tetranychus urticae (two-spotted spider mite)", "mites", [21, 32]),
    "MP": ("Myzus persicae (green peach aphid)", "aphids", [24]),
    "TP": ("Thrips palmi (melon thrips)", "thrips", [12, 33, 53, 54, 92]),
    "SE": ("Spodoptera exigua (beet armyworm)", "caterpillars", [39]),
    "SL": ("Spodoptera litura (tobacco caterpillar)", "spodoptera_tobacco_caterpillar", [86]),
    "HA": ("Helicoverpa armigera (fruit borer)", "helicoverpa_fruit_borer", []),
    "BA": ("Bemisia argentifolii (silverleaf whitefly)", "whitefly", []),
    "ZC": ("Zeugodacus cucurbitae (melon fly)", "fruit_fly", []),
}
CATERPILLAR_TOPICS = {"caterpillars", "spodoptera_tobacco_caterpillar", "helicoverpa_fruit_borer", "cutworm"}

KB_MAP = {"aphids": [24, 27, 29], "thrips": [12, 33, 53, 54, 92], "mites": [21, 32],
          "caterpillars": [18, 19, 20, 23, 38, 39]}
EXT_MAP = {"aphids": [24, 27, 28, 29, 52, 89, 90, 91], "thrips": [12, 33, 53, 54, 92],
           "mites": [21, 31, 32, 60, 61, 63, 74, 75], "caterpillars": [18, 19, 20, 23, 38, 39],
           "spodoptera_tobacco_caterpillar": [86], "whitefly": [71, 82], "leafhoppers": [11, 69, 72, 98, 101],
           "mealybug": [64, 81], "fruit_fly": [83, 84, 85]}
# Reliable advice groups at threshold 0.2, INT8 (results/pest_groups_ip102/results.json)
RELIABLE_GROUPS = {"group_kb": {"caterpillars", "thrips"},
                   "group_extended": {"caterpillars", "thrips", "leafhoppers", "fruit_fly"}}

def save_json(obj, name):
    """Write obj as indented JSON into WORK_DIR (numpy values are converted to plain Python)."""
    with open(WORK_DIR / name, "w") as f:
        json.dump(obj, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))

# %% [markdown]
# ## Locate inputs

# %%
def walk_dirs(root, max_depth=7):
    """os.walk below root up to max_depth, not descending into the large IP102 image folders."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        p = Path(dirpath)
        if len(p.relative_to(root).parts) >= max_depth or p.name in ("Annotations", "JPEGImages"):
            dirnames[:] = []
        yield p, dirnames, filenames

def find_file(name):
    """First file with this exact name below INPUT_ROOT."""
    for d, _, files in walk_dirs(INPUT_ROOT):
        if name in files:
            return d / name
    raise FileNotFoundError(f"{name} not found - attach bangadbilla420/krishirakshak-pest-onnx")

def find_huang():
    """Folder that holds the eight class folders (extracts originals.zip first if the upload was not unpacked)."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT):
        if set(CLASSES) <= set(dirs):
            return d
    for d, _, files in walk_dirs(INPUT_ROOT):
        if "originals.zip" in files:
            out = WORK_DIR.parent / "huang_unzipped"
            zipfile.ZipFile(d / "originals.zip").extractall(out)
            for d2, dirs2, _ in walk_dirs(out):
                if set(CLASSES) <= set(dirs2):
                    return d2
    raise FileNotFoundError("Huang class folders not found - attach bangadbilla420/tomato-pest-8-originals-huang")

def find_ip102_images():
    """All IP102 JPEGImages files and the ids of the official test split."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT):
        if "Annotations" in dirs and "JPEGImages" in dirs:
            test = set()
            for sd, _, sfiles in walk_dirs(d, max_depth=3):
                if "test.txt" in sfiles:
                    test = {l.strip() for l in open(sd / "test.txt") if l.strip()}
                    break
            imgs = sorted(p for p in (d / "JPEGImages").iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
            return imgs, test
    raise FileNotFoundError("IP102 not found - attach parserpixy/ip102-dataset")

HUANG = find_huang()
MODELS = {"fp32": find_file("pest_yolov8n_ip102_negatives.onnx"), "int8": find_file("pest_yolov8n_ip102_negatives_int8.onnx")}
NAMES = [n.strip() for n in json.loads(find_file("pest_labels.json").read_text())["names"]]
APP_CONFIG = json.loads(find_file("pest_config.json").read_text())
RELIABLE_SPECIES = set(APP_CONFIG["reliable_species_ids"])
assert abs(APP_CONFIG["conf_threshold"] - APP_CONF) < 1e-9
IP_IMAGES, IP_TEST = find_ip102_images()
if MAX_IP102_IMAGES:
    IP_IMAGES = IP_IMAGES[:MAX_IP102_IMAGES]
IMAGES = [(cls, p) for cls in CLASSES for p in sorted((HUANG / cls).iterdir()) if p.suffix.lower() == ".jpg"]
print("Huang images:", len(IMAGES), dict(Counter(c for c, _ in IMAGES)), "| IP102 images:", len(IP_IMAGES))

# %% [markdown]
# ## Leakage check: perceptual hash against every IP102 image

# %%
def phash(gray):
    """64-bit DCT perceptual hash of a grayscale image."""
    small = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    low = cv2.dct(small)[:8, :8].flatten()
    return np.packbits(low > np.median(low[1:]))

def hashes(path):
    """Hashes of the full image and of its centre square (the Huang images are square crops)."""
    g = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if g is None:
        return None
    h, w = g.shape
    s = min(h, w)
    sq = g[(h - s) // 2:(h - s) // 2 + s, (w - s) // 2:(w - s) // 2 + s]
    return phash(g), phash(sq)

t0 = time.time()
with ThreadPoolExecutor(8) as ex:
    ip_hashes = list(ex.map(hashes, IP_IMAGES))
ok = [i for i, h in enumerate(ip_hashes) if h is not None]
IP_H = np.stack([np.concatenate(ip_hashes[i]) for i in ok])          # (n, 16 bytes): full | centre square
IP_IDS = [IP_IMAGES[i].stem for i in ok]
print(f"hashed {len(ok)} IP102 images in {time.time() - t0:.0f}s")

def nearest_ip102(path):
    """Smallest Hamming distance to any IP102 image (full or centre-square hash) and that image's id."""
    g = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    q = phash(g)
    d_full = np.unpackbits(IP_H[:, :8] ^ q, axis=1).sum(1)
    d_sq = np.unpackbits(IP_H[:, 8:] ^ q, axis=1).sum(1)
    d = np.minimum(d_full, d_sq)
    k = int(d.argmin())
    return int(d[k]), IP_IDS[k]

dup = [nearest_ip102(p) for _, p in IMAGES]
dist_counts = Counter(min(d, 20) for d, _ in dup)
print("nearest-IP102 Hamming distance (count):", dict(sorted(dist_counts.items())))

# %% [markdown]
# ## Detector (same code as ip102_pest_groups.py / pest_detector.cpp)

# %%
def letterbox(rgb):
    """Square letterbox like the C++ code / Ultralytics LetterBox(auto=False): NCHW float input, ratio, pads."""
    h, w = rgb.shape[:2]
    r = min(IMG_SIZE / h, IMG_SIZE / w)
    new_w, new_h = round(w * r), round(h * r)
    dw, dh = (IMG_SIZE - new_w) / 2, (IMG_SIZE - new_h) / 2
    if (new_w, new_h) != (w, h):
        rgb = cv2.resize(rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    top, bottom, left, right = round(dh - 0.1), round(dh + 0.1), round(dw - 0.1), round(dw + 0.1)
    padded = cv2.copyMakeBorder(rgb, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
    return np.ascontiguousarray(padded.transpose(2, 0, 1)[None], dtype=np.float32) / 255.0, r, left, top

def iou_xyxy(a, b):
    """IoU between one box a (4,) and boxes b (n, 4)."""
    x1 = np.maximum(a[0], b[:, 0]); y1 = np.maximum(a[1], b[:, 1])
    x2 = np.minimum(a[2], b[:, 2]); y2 = np.minimum(a[3], b[:, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area = lambda z: (z[..., 2] - z[..., 0]) * (z[..., 3] - z[..., 1])
    return inter / (area(a) + area(b) - inter + 1e-9)

def detect(session, path):
    """Best score and best class of every box kept after class-aware NMS (box geometry is not needed here)."""
    rgb = cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)
    x, _, _, _ = letterbox(rgb)
    out = session.run(None, {session.get_inputs()[0].name: x})[0][0]
    scores_all = out[4:].T
    best = scores_all.argmax(1)
    best_score = scores_all[np.arange(len(best)), best]
    keep = best_score > CONF_MIN
    cx, cy, w, h = out[:4, keep]
    boxes = np.stack([cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2], 1)
    best, best_score = best[keep], best_score[keep]
    shifted = boxes + (best * MAX_WH)[:, None]
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
    return best_score[kept], best[kept]

PRED = {}
for tag, path in MODELS.items():
    session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
    t0 = time.time()
    PRED[tag] = [detect(session, p) for _, p in IMAGES]
    print(f"[{tag}] {len(IMAGES)} images in {time.time() - t0:.0f}s")

# %% [markdown]
# ## Advice per image under the three rules

# %%
def topic_of(species, rule):
    """Knowledge-base topic the application would show for one detected species under a rule."""
    # Same as KnowledgeBase::pestTopic: a mapped species gets its topic when it is reliable; the group rules also give
    # it when its advice group is reliable
    mapping = EXT_MAP if rule == "group_extended" else KB_MAP
    group = next((g for g, ids in mapping.items() if species in ids), None)
    if group is None:
        return "insect_other"
    if species in RELIABLE_SPECIES or (rule != "today" and group in RELIABLE_GROUPS[rule]):
        return group
    return "insect_other"

RULES = ["today", "group_kb", "group_extended"]
rows = []
for tag in MODELS:
    for (cls, path), (dist, near_id), (sc, sp) in zip(IMAGES, dup, PRED[tag]):
        keep = sc > APP_CONF
        sc, sp = sc[keep], sp[keep]
        expected, ip_ids = CLASSES[cls][1], CLASSES[cls][2]
        row = dict(model=tag, cls=cls, image=path.name, ip102_dist=dist, ip102_nearest=near_id,
                   ip102_nearest_in_test=near_id in IP_TEST, near_duplicate=dist <= HASH_MAX_DIST,
                   found=bool(len(sp)), top_species=NAMES[int(sp[sc.argmax()])] if len(sp) else "",
                   top_species_ok=bool(len(sp)) and int(sp[sc.argmax()]) in ip_ids)
        for rule in RULES:
            topics = {topic_of(int(s), rule) for s in sp}
            specific = topics - {"insect_other"}
            row[f"{rule}_right"] = expected in topics
            row[f"{rule}_caterpillar_family"] = bool(specific & CATERPILLAR_TOPICS) if expected in CATERPILLAR_TOPICS else np.nan
            row[f"{rule}_wrong"] = bool(specific - {expected})
            row[f"{rule}_generic_only"] = bool(len(sp)) and not specific
        rows.append(row)
df = pd.DataFrame(rows)
df.to_csv(WORK_DIR / "per_image.csv", index=False)

def summary_table(d):
    """Per class: images, found, top-species right, and per rule right / wrong / generic-only advice."""
    agg = {"images": ("image", "size"), "near_duplicates": ("near_duplicate", "sum"), "insect_found": ("found", "mean"),
           "top_species_right": ("top_species_ok", "mean")}
    for rule in RULES:
        agg[f"{rule}_right"] = (f"{rule}_right", "mean")
        agg[f"{rule}_wrong"] = (f"{rule}_wrong", "mean")
        agg[f"{rule}_generic_only"] = (f"{rule}_generic_only", "mean")
    agg["group_kb_caterpillar_family"] = ("group_kb_caterpillar_family", "mean")
    t = d.groupby("cls").agg(**agg).reindex(list(CLASSES))
    t.insert(0, "expected_topic", [CLASSES[c][1] for c in t.index])
    return t

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
SUMMARY = {}
for tag in MODELS:
    for subset, d in (("all", df[df.model == tag]), ("no_near_duplicates", df[(df.model == tag) & ~df.near_duplicate])):
        t = summary_table(d)
        t.to_csv(WORK_DIR / f"summary_{tag}_{subset}.csv")
        SUMMARY[f"{tag}_{subset}"] = t.round(4).reset_index().to_dict(orient="records")
        print(f"\n=== {tag} | {subset}")
        print(t.round(2).to_string())
print("\nnear-duplicates of IP102 images:", int(df[df.model == "int8"].near_duplicate.sum()), "of", len(IMAGES),
      "| of those, nearest IP102 image in its test split:", int(df[(df.model == "int8") & df.near_duplicate].ip102_nearest_in_test.sum()))
save_json({"source": "Huang & Chuang 2020, Mendeley Data V1, doi:10.17632/s62zm6djd2.1, CC BY 4.0 (609 originals)",
           "app_threshold": APP_CONF, "hash_max_dist": HASH_MAX_DIST, "classes": CLASSES,
           "reliable_groups": {k: sorted(v) for k, v in RELIABLE_GROUPS.items()},
           "reliable_species": sorted(RELIABLE_SPECIES), "summary": SUMMARY}, "results.json")
print(sorted(p.name for p in WORK_DIR.iterdir()))
