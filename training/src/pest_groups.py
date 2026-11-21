# %% [markdown]
# # KrishiRakshak PS1 - pest detector by advice group (Kaggle GPU)
#
# The IP102 detector finds insects well (80-100% per pest) but names the exact species of look-alike pests poorly
# (black / large / yellow cutworm 19-58%, thrips species 25-67%). The farmer's advice does not depend on the exact
# species: the knowledge base has one topic per group (aphids, thrips, mites, caterpillars, whitefly). This notebook
# trains YOLOv8n directly on those **advice groups** plus "other insect":
#
# | class | IP102 species (0-based ids) | red chilli field photos |
# |---|---|---|
# | aphid | 24 aphids, 27 english grain aphid, 28 green bug, 29 bird cherry-oat aphid, 52 spotted alfalfa aphid, 89-91 citrus aphids | kutu daun |
# | whitefly | 71 greenhouse whitefly (Trialeurodes vaporariorum) | kutu kebul (Bemisia tabaci) |
# | thrips | 12, 33, 53, 54, 92 | thrips |
# | mite | 21 red spider, 32 long-legged spider mite, 74 citrus red mite | - |
# | caterpillar | 18-20 cutworms, 23 army worm, 38 cabbage army worm, 39 beet army worm, 86 Prodenia (Spodoptera) litura | ulat |
# | other_insect | all other IP102 species | - |
#
# New data: **Red Chili Pepper Pests Dataset** (indraagustian, Apache 2.0): field photos with boxes from Indonesian
# chilli plants (same plant family as tomato), four pests. Its own train/test split is kept; images that are
# augmented copies of one original photo stay in one split.
#
# Evaluation on identical held-out images, for this model and for the current app model (its IP102 species mapped to
# the same groups): insect found, **group named correctly when found**, group precision, false alarms on insect-free
# tomato leaves. The confidence threshold is chosen on validation negatives only (<= 5% false alarms).
#
# **Kaggle setup:** Accelerator = *GPU T4*, Internet = on, attach `parserpixy/ip102-dataset`,
# `indraagustian/red-chili-pepper-pests-dataset`, `abdallahalidev/plantvillage-dataset`,
# `nirmalsankalana/plantdoc-dataset` and the private dataset with the current app model
# (`pest_yolov8n_ip102_negatives.onnx`). Trained IP102 weights (`*.pt`) are used as the starting point if attached,
# otherwise training starts from COCO-pretrained YOLOv8n.

# %%
import os, sys, subprocess

ON_KAGGLE = os.path.exists("/kaggle/input")
SMOKE = os.environ.get("KR_SMOKE") == "1"
os.environ.setdefault("WANDB_MODE", "disabled")
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "ultralytics==8.4.7", "onnx==1.19.1",
                    "onnxruntime==1.23.2"], check=True)

# %%
import hashlib, json, random, re, shutil, time
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import onnx
import pandas as pd
import torch
import yaml
from PIL import Image
import ultralytics
from ultralytics import YOLO, settings as yolo_settings
from ultralytics.data.augment import LetterBox
from onnxruntime.quantization import CalibrationDataReader, CalibrationMethod, QuantFormat, QuantType, quantize_static
from onnxruntime.quantization.shape_inference import quant_pre_process

for key in ("wandb", "mlflow", "comet", "clearml", "dvc", "neptune", "raytune", "tensorboard"):
    try:
        yolo_settings.update({key: False})
    except Exception:
        pass
print("torch", torch.__version__, "| ultralytics", ultralytics.__version__)
T_START = time.time()

# %% [markdown]
# ## Configuration

# %%
SEED = 42
INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "pest_groups"
WORK_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = Path("/tmp/pest_groups") if ON_KAGGLE else WORK_DIR / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)
MODEL_NAME = "pest_yolov8n_groups"

GROUPS = ["aphid", "whitefly", "thrips", "mite", "caterpillar", "other_insect"]
OTHER = GROUPS.index("other_insect")
# Knowledge-base topic for each class (app/kb/tomato_kb.json)
TOPIC_OF_GROUP = {"aphid": "aphids", "whitefly": "whitefly", "thrips": "thrips", "mite": "mites",
                  "caterpillar": "caterpillars", "other_insect": "insect_other"}
GROUP_SPECIES = {
    "aphid": [24, 27, 28, 29, 52, 89, 90, 91],
    "whitefly": [71],
    "thrips": [12, 33, 53, 54, 92],
    "mite": [21, 32, 74],
    "caterpillar": [18, 19, 20, 23, 38, 39, 86],
}
GROUP_OF_SPECIES = defaultdict(lambda: OTHER)
for g, ids in GROUP_SPECIES.items():
    for s in ids:
        GROUP_OF_SPECIES[s] = GROUPS.index(g)
# Red chilli dataset: file-name prefix (Indonesian) -> group; used to check which label id is which pest
CHILI_PREFIX_GROUP = {"kutu-daun": "aphid", "kutu-kebul": "whitefly", "thrips": "thrips", "thrips-baru": "thrips",
                      "ulat": "caterpillar"}

IMG_SIZE = 128 if SMOKE else 640
EPOCHS_FROM_COCO = int(os.environ.get("KR_EPOCHS", 1 if SMOKE else 70))
EPOCHS_FROM_IP102 = int(os.environ.get("KR_EPOCHS", 1 if SMOKE else 40))
MAX_TRAIN_HOURS = float(os.environ.get("KR_MAX_TRAIN_HOURS", 7.5))   # Kaggle stops a run after 12 h
PATIENCE = 15
BATCH = 8 if SMOKE else 32
WORKERS = 0 if SMOKE else 4
GROUP_REPEAT = 2               # images with an advice-group insect appear this many times in training
VAL_FRACTION = 0.10
CHILI_VAL_PERCENT = 15
NEG_PV_TRAIN_MAX = 40 if SMOKE else 3500
NEG_EVAL_MAX = 30 if SMOKE else 1000
NEG_TOMATO_FOLDERS = ["Tomato___healthy", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Leaf_Mold",
                      "Tomato___Septoria_leaf_spot", "Tomato___Bacterial_spot",
                      "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___Tomato_mosaic_virus",
                      "Tomato___Target_Spot"]  # spider-mite images show mites -> excluded
CONF_GRID = [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]
MAX_FALSE_ALARM_RATE = 0.05
OLD_MODEL_THRESHOLD = 0.2      # the app's current threshold (results/int8_ptq/pest_yolov8n_ip102_negatives.json)
RELIABLE_MIN_TEST_BOXES, RELIABLE_MIN_GROUP_ACC, RELIABLE_MIN_PRECISION = 30, 0.80, 0.80
CALIB_IMAGES, CALIB_NEG, CALIB_CHUNK = (8, 8, 8) if SMOKE else (304, 96, 16)
MAX_EVAL_IMAGES = 40 if SMOKE else None

AUG = dict(degrees=30.0, flipud=0.5, fliplr=0.5, hsv_h=0.015, hsv_s=0.6, hsv_v=0.4, translate=0.1, scale=0.5,
           shear=2.0, perspective=0.0005, mosaic=1.0, mixup=0.1)

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
NC_IP102 = len(IP102_NAMES)

random.seed(SEED); np.random.seed(SEED)
DEVICE = 0 if torch.cuda.is_available() else "cpu"
print("device:", torch.cuda.get_device_name(0) if DEVICE == 0 else "cpu")

def save_json(obj, name):
    """Write obj as indented JSON into WORK_DIR (numpy values are converted to plain Python)."""
    with open(WORK_DIR / name, "w") as f:
        json.dump(obj, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))

def link(src, dst):
    """Symlink src to dst (copy if the file system does not allow links)."""
    try:
        os.symlink(src, dst)
    except OSError:
        shutil.copy(src, dst)

# %% [markdown]
# ## Locate datasets

# %%
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def walk_dirs(root, max_depth=6):
    """os.walk below root up to max_depth, skipping large image folders that never need searching."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        p = Path(dirpath)
        if len(p.relative_to(root).parts) >= max_depth or p.name in ("Annotations", "JPEGImages", "images", "labels"):
            dirnames[:] = []
        dirnames[:] = sorted(d for d in dirnames if "___" not in d)
        yield p, dirnames, filenames

def find_ip102():
    """IP102 VOC root (Annotations/ + JPEGImages/) and its trainval/test split files."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT):
        if "Annotations" in dirs and "JPEGImages" in dirs:
            split_files = {}
            for sd, _, sfiles in walk_dirs(d, max_depth=3):
                for name in ("trainval.txt", "test.txt"):
                    if name in sfiles and name not in split_files:
                        split_files[name] = sd / name
            return d, split_files
    raise FileNotFoundError("IP102 VOC folders not found - attach parserpixy/ip102-dataset")

def find_chili():
    """Folder of the red chilli dataset: contains train/images and test/images with 'kutu' / 'ulat' file names."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT, max_depth=5):
        if "train" in dirs and "test" in dirs and (d / "train" / "images").is_dir():
            names = os.listdir(d / "train" / "images")[:500]
            if any(n.startswith(("kutu", "ulat", "thrips")) for n in names):
                return d
    raise FileNotFoundError("red chilli pest dataset not found - attach indraagustian/red-chili-pepper-pests-dataset")

def find_plantvillage_color():
    for d, _, _ in walk_dirs(INPUT_ROOT):
        if d.name.lower() == "color" and (d / "Tomato___Early_blight").is_dir():
            return d
    return None

def find_plantdoc_classification():
    for d, dirs, _ in walk_dirs(INPUT_ROOT):
        if "test" in dirs and "train" in dirs:
            try:
                if any(re.sub(r"[\s_]+", " ", c).strip().lower() == "tomato early blight leaf"
                       for c in os.listdir(d / "test")):
                    return d
            except OSError:
                pass
    return None

def find_file(names):
    """First file under the inputs whose name is in names (searched deep), else None."""
    for d, _, files in walk_dirs(INPUT_ROOT, max_depth=8):
        for n in names:
            if n in files:
                return d / n
    return None

IP_ROOT, IP_SPLITS = find_ip102()
CHILI_ROOT = find_chili()
PV_ROOT = find_plantvillage_color()
PD_CLS_ROOT = find_plantdoc_classification()
OLD_ONNX = find_file(["pest_yolov8n_ip102_negatives.onnx"])
START_WEIGHTS = os.environ.get("KR_PEST_WEIGHTS") or find_file(
    ["pest_yolov8n_ip102_negatives.pt", "ip102_yolov8n_negft_best.pt", "ip102_yolov8n_best.pt"])
print("IP102:", IP_ROOT, "| chilli:", CHILI_ROOT, "| PlantVillage:", PV_ROOT, "| PlantDoc:", PD_CLS_ROOT)
print("current app model (for comparison):", OLD_ONNX)
print("start weights:", START_WEIGHTS or "yolov8n.pt (COCO)")

# %% [markdown]
# ## IP102 annotations (species id kept for the comparison, group id used for training)

# %%
def read_ids(path):
    return [l.strip() for l in open(path) if l.strip()] if path else []

def find_image(img_id):
    for ext in (".jpg", ".jpeg", ".png", ".JPG"):
        p = IP_ROOT / "JPEGImages" / f"{img_id}{ext}"
        if p.exists():
            return p
    return None

def read_xml_objects(xml_path):
    """<object> elements; files with extra text or a second <annotation> block are wrapped in one root."""
    text = xml_path.read_text(errors="ignore")
    try:
        return list(ET.fromstring(text).iter("object"))
    except ET.ParseError:
        body = re.sub(r"<\?xml[^>]*\?>", "", text)
        try:
            return list(ET.fromstring(f"<root>{body}</root>").iter("object"))
        except ET.ParseError:
            return None

def parse_ip102(img_id):
    """Image path, size and boxes (species id, x1, y1, x2, y2) of one IP102 image; never raises."""
    rec = dict(id=img_id, image=None, width=0, height=0, boxes=[], source="ip102")
    try:
        xml_path, img_path = IP_ROOT / "Annotations" / f"{img_id}.xml", find_image(img_id)
        if img_path is None or not xml_path.exists():
            return rec
        with Image.open(img_path) as im:
            W, H = im.size
        rec.update(image=str(img_path), width=W, height=H)
        for obj in read_xml_objects(xml_path) or []:
            try:
                c = int(obj.findtext("name").strip())
                bb = obj.find("bndbox")
                x1, y1, x2, y2 = (float(bb.findtext(k)) for k in ("xmin", "ymin", "xmax", "ymax"))
            except Exception:
                continue
            if not 0 <= c < NC_IP102:
                continue
            x1, x2 = sorted((min(max(x1, 0), W), min(max(x2, 0), W)))
            y1, y2 = sorted((min(max(y1, 0), H), min(max(y2, 0), H)))
            if x2 - x1 >= 2 and y2 - y1 >= 2 and (c, x1, y1, x2, y2) not in rec["boxes"]:
                rec["boxes"].append((c, x1, y1, x2, y2))
    except Exception as e:
        print("skipped", img_id, e)
    return rec

trainval_ids, test_ids = read_ids(IP_SPLITS.get("trainval.txt")), read_ids(IP_SPLITS.get("test.txt"))
t0 = time.time()
with ThreadPoolExecutor(16) as ex:
    recs = {r["id"]: r for r in ex.map(parse_ip102, sorted(set(trainval_ids) | set(test_ids)))}
usable = {k: r for k, r in recs.items() if r["image"] and r["boxes"]}
print(f"IP102: {len(usable)} usable of {len(recs)} images ({time.time() - t0:.0f}s)")
for r in usable.values():
    r["gboxes"] = [(GROUP_OF_SPECIES[c], x1, y1, x2, y2) for c, x1, y1, x2, y2 in r["boxes"]]

rng = random.Random(SEED)
tv = [i for i in trainval_ids if i in usable]
by_class = defaultdict(list)
for i in tv:
    by_class[Counter(c for c, *_ in usable[i]["boxes"]).most_common(1)[0][0]].append(i)
IP_SPLIT = {"train": [], "val": [], "test": sorted(i for i in test_ids if i in usable)}
for c, ids in sorted(by_class.items()):
    ids = sorted(ids); rng.shuffle(ids)
    n_val = min(int(round(len(ids) * VAL_FRACTION)) if len(ids) >= 2 else 0, len(ids) - 1)
    IP_SPLIT["val"] += ids[:n_val]; IP_SPLIT["train"] += ids[n_val:]
print({s: len(v) for s, v in IP_SPLIT.items()})

# %% [markdown]
# ## Red chilli field photos (YOLO labels). Which label id is which pest is checked against the file names.

# %%
def chili_original(stem):
    """Name of the original photo before Roboflow augmentation ('ulat--12-_jpg.rf.<hash>' -> 'ulat--12-')."""
    return re.sub(r"_(jpe?g|png|JPE?G|PNG)\.rf\.[0-9a-fA-F]+$", "", stem)

def chili_prefix(stem):
    return re.sub(r"[-_ ]*\(?-?\d.*$", "", chili_original(stem)).lower()

def read_chili(split):
    """Records of one chilli split folder; boxes as (label id, x1, y1, x2, y2) in pixels."""
    out = []
    img_dir, lab_dir = CHILI_ROOT / split / "images", CHILI_ROOT / split / "labels"
    if not img_dir.is_dir():
        return out
    for p in sorted(img_dir.iterdir()):
        if p.suffix.lower() not in IMG_EXT:
            continue
        lab = lab_dir / f"{p.stem}.txt"
        if not lab.exists():
            continue
        try:
            with Image.open(p) as im:
                W, H = im.size
        except Exception:
            continue
        boxes = []
        for line in lab.read_text().split("\n"):
            v = line.split()
            if len(v) != 5:
                continue  # polygon or empty lines are skipped
            c, cx, cy, w, h = int(float(v[0])), *map(float, v[1:])
            x1, y1, x2, y2 = (cx - w / 2) * W, (cy - h / 2) * H, (cx + w / 2) * W, (cy + h / 2) * H
            x1, x2 = max(0, x1), min(W, x2); y1, y2 = max(0, y1), min(H, y2)
            if x2 - x1 >= 2 and y2 - y1 >= 2:
                boxes.append((c, x1, y1, x2, y2))
        out.append(dict(id=f"chili_{split}_{p.stem}", image=str(p), width=W, height=H, boxes=boxes,
                        original=chili_original(p.stem), prefix=chili_prefix(p.stem), source="chili"))
    return out

chili = {s: read_chili(s) for s in ("train", "valid", "val", "test")}
chili_test = chili["test"]
chili_trainval = chili["train"] + chili["valid"] + chili["val"]
print("chilli images with labels:", {s: len(v) for s, v in chili.items()})
assert SMOKE or (len(chili_trainval) > 500 and len(chili_test) > 100), "chilli labels missing - check the folders"
# Label id -> group from the file names of the images that contain that id
votes = defaultdict(Counter)
for r in chili_trainval + chili_test:
    g = CHILI_PREFIX_GROUP.get(r["prefix"])
    for c, *_ in r["boxes"]:
        votes[c][g] += 1
CHILI_GROUP = {}
for c, cnt in sorted(votes.items()):
    named = Counter({k: v for k, v in cnt.items() if k})
    assert named, f"chilli label id {c} appears only in images without a known file-name prefix"
    g, n = named.most_common(1)[0]
    purity = n / sum(named.values())
    CHILI_GROUP[c] = GROUPS.index(g)
    print(f"chilli label id {c}: {g} (file names agree for {purity:.0%} of {sum(named.values())} boxes) {dict(cnt)}")
    assert purity >= 0.8, "chilli label ids do not match the file names - check the class mapping"
for r in chili_trainval + chili_test:
    r["gboxes"] = [(CHILI_GROUP[c], x1, y1, x2, y2) for c, x1, y1, x2, y2 in r["boxes"]]
# A photo named after one pest with boxes of another (e.g. caterpillar boxes in 'thrips' photos) is either
# mislabelled or mixed; it is left out so it cannot teach the look-alike confusion this model is meant to remove
def disagrees(r):
    g = CHILI_PREFIX_GROUP.get(r["prefix"])
    return g is not None and any(GROUPS[b[0]] != g for b in r["gboxes"])
test_ids_chili = {r["id"] for r in chili_test}
chili_disagree = Counter(("test" if r["id"] in test_ids_chili else "trainval", r["prefix"]) for r in chili_trainval + chili_test
                         if disagrees(r))
print("chilli photos left out (labels disagree with the file name):", dict(chili_disagree))
chili_trainval = [r for r in chili_trainval if not disagrees(r)]
chili_test = [r for r in chili_test if not disagrees(r)]

# Augmented copies of one photo stay in one split: drop training copies of photos that are in the test split
test_originals = {r["original"] for r in chili_test}
leak = [r for r in chili_trainval if r["original"] in test_originals]
chili_trainval = [r for r in chili_trainval if r["original"] not in test_originals]
def bucket(key):
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % 100
CHILI_SPLIT = {"train": [r for r in chili_trainval if bucket(r["original"]) >= CHILI_VAL_PERCENT],
               "val": [r for r in chili_trainval if bucket(r["original"]) < CHILI_VAL_PERCENT],
               "test": chili_test}
print(f"chilli: removed {len(leak)} training images that are copies of test photos;",
      {s: len(v) for s, v in CHILI_SPLIT.items()})

# %% [markdown]
# ## Insect-free tomato leaves (negatives), split by leaf / photo group

# %%
def pv_group(path):
    stem = Path(path).stem.split("___", 1)[-1].strip()
    m = re.match(r"^(.*?)\s+day\s*\d+.*$", stem, re.I)
    if m:
        return re.sub(r"[.]\d+$", "", m.group(1).strip().lower())
    m = re.match(r"^(.*?)(\d+)(?:\.\d+)?$", stem)
    return f"{m.group(1).strip().lower()}|{int(m.group(2)) // 20}" if m else stem.lower()

NEG = {"train": [], "val_pv": [], "test_pv": [], "val_pd": [], "test_pd": []}
if PV_ROOT is not None:
    for folder in NEG_TOMATO_FOLDERS:
        if (PV_ROOT / folder).is_dir():
            for p in sorted((PV_ROOT / folder).iterdir()):
                if p.suffix.lower() in IMG_EXT:
                    b = bucket(folder + "|" + pv_group(p.name))
                    NEG["train" if b < 70 else "val_pv" if b < 80 else "test_pv"].append(str(p))
    NEG["train"] = random.Random(SEED).sample(NEG["train"], min(NEG_PV_TRAIN_MAX, len(NEG["train"])))
if PD_CLS_ROOT is not None:
    for split_dir in ("train", "test"):
        for cdir in sorted((PD_CLS_ROOT / split_dir).iterdir()):
            name = re.sub(r"[\s_]+", " ", cdir.name).strip().lower()
            if cdir.is_dir() and name.startswith("tomato") and "mite" not in name:
                for p in sorted(cdir.iterdir()):
                    if p.suffix.lower() in IMG_EXT:
                        if split_dir == "test":
                            NEG["test_pd"].append(str(p))
                        else:
                            NEG["val_pd" if bucket(p.name) < 15 else "train"].append(str(p))
rng = random.Random(SEED + 1)
for k in ("val_pv", "test_pv", "val_pd", "test_pd"):
    NEG[k] = rng.sample(NEG[k], min(NEG_EVAL_MAX, len(NEG[k])))
print({k: len(v) for k, v in NEG.items()})

# %% [markdown]
# ## Build the YOLO dataset (group labels; images linked, not copied)

# %%
SPLITS = {s: [usable[i] for i in IP_SPLIT[s]] + CHILI_SPLIT[s] for s in ("train", "val", "test")}
YOLO_DIR = TMP_DIR / "yolo"
if YOLO_DIR.exists():
    shutil.rmtree(YOLO_DIR)

# Training reads small copies: decoding the large original photos made one epoch take ~19 min on Kaggle's 4 CPUs
# (data-loader bound). Labels are relative to the image size, so they stay valid. Evaluation uses the originals.
SMALL_DIR = TMP_DIR / "small"
SMALL_DIR.mkdir(parents=True, exist_ok=True)
MAX_SIDE = max(IMG_SIZE, 640)

def shrink(job):
    """Write a JPEG copy with the longer side at most MAX_SIDE (link the original if it is already small)."""
    src, dst = job
    if dst.exists():
        return
    im = cv2.imread(src)
    if im is None or max(im.shape[:2]) <= MAX_SIDE:
        link(src, dst); return
    f = MAX_SIDE / max(im.shape[:2])
    cv2.imwrite(str(dst), cv2.resize(im, (round(im.shape[1] * f), round(im.shape[0] * f)), interpolation=cv2.INTER_AREA),
                [cv2.IMWRITE_JPEG_QUALITY, 95])

def small_path(r):
    return SMALL_DIR / (r["id"].replace("/", "_") + ".jpg")

t0 = time.time()
with ThreadPoolExecutor(8) as ex:
    list(ex.map(shrink, [(r["image"], small_path(r)) for split in ("train", "val") for r in SPLITS[split]]))
print(f"small training copies written in {(time.time() - t0) / 60:.1f} min")

def write_item(split, r, name):
    src = small_path(r) if split in ("train", "val") else Path(r["image"])
    link(src, YOLO_DIR / "images" / split / f"{name}{src.suffix.lower()}")
    W, H = r["width"], r["height"]
    (YOLO_DIR / "labels" / split / f"{name}.txt").write_text("".join(
        f"{g} {(x1 + x2) / 2 / W:.6f} {(y1 + y2) / 2 / H:.6f} {(x2 - x1) / W:.6f} {(y2 - y1) / H:.6f}\n"
        for g, x1, y1, x2, y2 in r["gboxes"]))

profile = Counter()
for split, items in SPLITS.items():
    (YOLO_DIR / "images" / split).mkdir(parents=True); (YOLO_DIR / "labels" / split).mkdir(parents=True)
    for k, r in enumerate(items):
        repeat = GROUP_REPEAT if split == "train" and any(g != OTHER for g, *_ in r["gboxes"]) else 1
        for rep in range(repeat):
            write_item(split, r, f"{r['source']}_{k:05d}_{rep}")
        for g, *_ in r["gboxes"]:
            profile[(split, r["source"], GROUPS[g])] += 1
for k, src in enumerate(NEG["train"]):
    link(src, YOLO_DIR / "images" / "train" / f"neg_{k:05d}{Path(src).suffix.lower()}")
    (YOLO_DIR / "labels" / "train" / f"neg_{k:05d}.txt").write_text("")
prof = pd.Series(profile).unstack([0, 1]).fillna(0).astype(int)
prof.to_csv(WORK_DIR / "boxes_per_group.csv")
print("boxes per group (before training repeats):\n", prof.to_string())
DATA_YAML = YOLO_DIR / "data.yaml"
yaml.safe_dump({"path": str(YOLO_DIR), "train": "images/train", "val": "images/val", "test": "images/test",
                "names": dict(enumerate(GROUPS))}, open(DATA_YAML, "w"), sort_keys=False)

# %% [markdown]
# ## Train (time-limited so evaluation and export always finish inside Kaggle's 12 h)

# %%
start = str(START_WEIGHTS) if START_WEIGHTS else "yolov8n.pt"
epochs = EPOCHS_FROM_IP102 if START_WEIGHTS else EPOCHS_FROM_COCO
model = YOLO(start)
t_train = time.time()
def stop_on_time(trainer):
    if time.time() - t_train > MAX_TRAIN_HOURS * 3600:
        print(f"time limit reached after epoch {trainer.epoch + 1}: stopping")
        trainer.stop = True
model.add_callback("on_fit_epoch_end", stop_on_time)
model.train(data=str(DATA_YAML), epochs=epochs, imgsz=IMG_SIZE, batch=BATCH, patience=PATIENCE, workers=WORKERS,
            device=DEVICE, seed=SEED, project=str(WORK_DIR / "runs"), name=MODEL_NAME, exist_ok=True, plots=True,
            verbose=False, close_mosaic=10, **AUG)
BEST = Path(model.trainer.save_dir) / "weights" / "best.pt"
shutil.copy(BEST, WORK_DIR / f"{MODEL_NAME}.pt")   # saved before any later step can fail
print(f"training took {(time.time() - t_train) / 3600:.2f} h -> {BEST}")

# %% [markdown]
# ## Evaluation helpers
# A ground-truth insect is **found** when a kept box overlaps it with IoU >= 0.5; the group is **correct** when that
# box's group matches. **Precision** of a group: of the kept boxes of that group that overlap an insect, the share
# whose insect really is that group.

# %%
def iou_matrix(a, b):
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    x1 = np.maximum(a[:, None, 0], b[None, :, 0]); y1 = np.maximum(a[:, None, 1], b[None, :, 1])
    x2 = np.minimum(a[:, None, 2], b[None, :, 2]); y2 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area = lambda z: (z[:, 2] - z[:, 0]) * (z[:, 3] - z[:, 1])
    return inter / (area(a)[:, None] + area(b)[None, :] - inter + 1e-9)

def predict(m, paths, device, imgsz=IMG_SIZE):
    """{image path: (boxes xyxy, scores, classes)}, one image per call (exported models have batch 1)."""
    out = {}
    for p in map(str, paths):
        r = m.predict(source=p, conf=min(CONF_GRID), imgsz=imgsz, device=device, verbose=False)[0]
        out[p] = (r.boxes.xyxy.cpu().numpy(), r.boxes.conf.cpu().numpy(), r.boxes.cls.cpu().numpy().astype(int))
    return out

def subset(items):
    return items[:MAX_EVAL_IMAGES] if MAX_EVAL_IMAGES else items

def group_scores(preds, items, to_group, t):
    """Found rate, group accuracy when found and precision per group at threshold t, plus the confusion matrix."""
    gt_n, found_n, ok_n, pred_match, pred_ok = Counter(), Counter(), Counter(), Counter(), Counter()
    confusion = np.zeros((len(GROUPS), len(GROUPS)), int)
    species_found = species_ok = 0
    for r in items:
        gt = np.array([b[1:] for b in r["gboxes"]], float).reshape(-1, 4)
        gt_g = np.array([b[0] for b in r["gboxes"]], int)
        pb, pc, pk = preds[r["image"]]
        keep = pc >= t; pb, pk = pb[keep], pk[keep]
        pg = np.array([to_group(k) for k in pk], int)
        iou = iou_matrix(gt, pb)
        for j, g in enumerate(gt_g):
            gt_n[g] += 1
            if len(pb) and iou[j].max() >= 0.5:
                found_n[g] += 1
                guess = pg[iou[j].argmax()]
                confusion[g, guess] += 1
                ok_n[g] += int(guess == g)
                if r["source"] == "ip102" and to_group is old_group:  # exact species of the current model
                    species_found += 1; species_ok += int(pk[iou[j].argmax()] == r["boxes"][j][0])
        if len(pb) and len(gt):
            for i in range(len(pb)):
                if iou[:, i].max() >= 0.5:
                    pred_match[pg[i]] += 1; pred_ok[pg[i]] += int(gt_g[iou[:, i].argmax()] == pg[i])
    rows = []
    for g in range(len(GROUPS)):
        rows.append(dict(group=GROUPS[g], test_boxes=gt_n[g], found=found_n[g] / gt_n[g] if gt_n[g] else np.nan,
                         group_correct_when_found=ok_n[g] / found_n[g] if found_n[g] else np.nan,
                         precision=pred_ok[g] / pred_match[g] if pred_match[g] else np.nan))
    tot = sum(gt_n.values())
    rows.append(dict(group="all", test_boxes=tot, found=sum(found_n.values()) / max(tot, 1),
                     group_correct_when_found=sum(ok_n.values()) / max(sum(found_n.values()), 1),
                     precision=sum(pred_ok.values()) / max(sum(pred_match.values()), 1)))
    extra = dict(species_correct_when_found=species_ok / species_found) if species_found else {}
    return pd.DataFrame(rows), confusion, extra

def false_alarm_rates(m, keys, device, imgsz):
    out = {}
    for k in keys:
        if NEG[k]:
            preds = predict(m, subset(NEG[k]), device, imgsz)
            mx = np.array([v[1].max() if len(v[1]) else 0.0 for v in preds.values()])
            out[k] = {t: float((mx >= t).mean()) for t in CONF_GRID}
    return out

def new_group(k):
    return int(k)

def old_group(k):
    return GROUP_OF_SPECIES[int(k)]

def evaluate(m, to_group, device, threshold=None, tag="", imgsz=IMG_SIZE):
    """Threshold from validation negatives (unless given), then group scores on the IP102 and chilli test sets."""
    t0 = time.time()
    fa = false_alarm_rates(m, ["val_pv", "val_pd", "test_pv", "test_pd"], device, imgsz)
    if threshold is None:
        ok = [t for t in CONF_GRID if all(fa[k][t] <= MAX_FALSE_ALARM_RATE for k in ("val_pv", "val_pd") if k in fa)]
        threshold = min(ok) if ok else max(CONF_GRID)
    res = dict(threshold=threshold, false_alarms={k: v[threshold] for k, v in fa.items()}, sets={})
    for name, items in (("ip102_test", subset([usable[i] for i in IP_SPLIT["test"]])),
                        ("chili_test", subset(CHILI_SPLIT["test"]))):
        preds = predict(m, [r["image"] for r in items], device, imgsz)
        table, conf, extra = group_scores(preds, items, to_group, threshold)
        res["sets"][name] = dict(table=table, confusion=conf, **extra)
    print(f"[{tag}] threshold {threshold}, false alarms {res['false_alarms']} ({(time.time() - t0) / 60:.0f} min)")
    for name, s in res["sets"].items():
        print(f"  {name}:", {k: v for k, v in s.items() if k not in ("table", "confusion")})
        print(s["table"].round(3).to_string(index=False))
    return res

# %% [markdown]
# ## New group model vs the current app model, on identical test images

# %%
EVAL = {"groups_fp32": evaluate(YOLO(str(BEST)), new_group, DEVICE, tag="new group model")}
if OLD_ONNX:
    EVAL["current_app_fp32"] = evaluate(YOLO(str(OLD_ONNX), task="detect"), old_group, "cpu",
                                        threshold=OLD_MODEL_THRESHOLD, tag="current app model", imgsz=640)

# %% [markdown]
# ## Export FP32 ONNX and INT8 (static, QDQ, per-channel; box decoding kept in FP32)

# %%
pt_copy = TMP_DIR / f"{MODEL_NAME}.pt"
shutil.copy(BEST, pt_copy)
FP32 = WORK_DIR / f"{MODEL_NAME}.onnx"
shutil.move(str(YOLO(str(pt_copy)).export(format="onnx", imgsz=IMG_SIZE, opset=17, dynamic=False, simplify=False)), FP32)

class ArrayReader(CalibrationDataReader):
    def __init__(self, name, items):
        self.name, self.items = name, items
        self.set_range(0, len(items))
    def __len__(self):
        return len(self.items)
    def set_range(self, start_index, end_index):
        self.pos, self.end = start_index, end_index
    def get_next(self):
        if self.pos >= self.end:
            return None
        self.pos += 1
        return {self.name: self.items[self.pos - 1].astype(np.float32) / 255.0}

def letterbox_u8(path):
    padded = LetterBox(new_shape=(IMG_SIZE, IMG_SIZE), auto=False)(image=cv2.imread(str(path)))
    return np.ascontiguousarray(padded[..., ::-1].transpose(2, 0, 1)[None])

pre = TMP_DIR / f"{MODEL_NAME}_pre.onnx"
quant_pre_process(str(FP32), str(pre), skip_symbolic_shape=True)
m_pre = onnx.load(str(pre))
for i, n in enumerate(m_pre.graph.node):
    if not n.name:
        n.name = f"unnamed_{n.op_type}_{i}"
onnx.save(m_pre, str(pre))
detect = max({n.name.split("/")[1] for n in m_pre.graph.node if n.name.startswith("/model.")},
             key=lambda s: int(s.split(".")[1]))
exclude = [n.name for n in m_pre.graph.node
           if n.name.startswith(f"/{detect}/") and "/cv2." not in n.name and "/cv3." not in n.name]
rng = random.Random(SEED)
calib = [r["image"] for r in rng.sample(SPLITS["train"], CALIB_IMAGES)] + rng.sample(NEG["train"], CALIB_NEG)
calib_u8 = [letterbox_u8(p) for p in calib]
INT8 = WORK_DIR / f"{MODEL_NAME}_int8.onnx"
quantize_static(str(pre), str(INT8), ArrayReader(m_pre.graph.input[0].name, calib_u8),
                quant_format=QuantFormat.QDQ, activation_type=QuantType.QInt8, weight_type=QuantType.QInt8,
                per_channel=True, calibrate_method=CalibrationMethod.Percentile, nodes_to_exclude=exclude,
                extra_options={"CalibStridedMinMax": CALIB_CHUNK})
m_src, m_q = onnx.load(str(FP32)), onnx.load(str(INT8))
del m_q.metadata_props[:]
m_q.metadata_props.extend(m_src.metadata_props)
onnx.save(m_q, str(INT8))
del calib_u8
print(f"FP32 {FP32.stat().st_size / 1e6:.1f} MB, INT8 {INT8.stat().st_size / 1e6:.1f} MB")
EVAL["groups_int8"] = evaluate(YOLO(str(INT8), task="detect"), new_group, "cpu", tag="new group model INT8")

# %% [markdown]
# ## Reliable groups, app files and the summary

# %%
def combined(res):
    """Group scores over both test sets together (box counts added)."""
    rows = {}
    for s in res["sets"].values():
        for _, r in s["table"].iterrows():
            a = rows.setdefault(r.group, dict(n=0, found=0.0, ok=0.0, prec=[]))
            if r.test_boxes:
                a["n"] += r.test_boxes; a["found"] += r.found * r.test_boxes
                if not np.isnan(r.group_correct_when_found):
                    a["ok"] += r.group_correct_when_found * r.found * r.test_boxes
                if not np.isnan(r.precision):
                    a["prec"].append(r.precision)
    return {g: dict(test_boxes=int(a["n"]), found=a["found"] / a["n"] if a["n"] else np.nan,
                    group_correct_when_found=a["ok"] / a["found"] if a["found"] else np.nan,
                    precision=float(np.mean(a["prec"])) if a["prec"] else np.nan) for g, a in rows.items()}

final = EVAL["groups_int8"]          # the app runs the INT8 model
comb = combined(final)
reliable = [GROUPS.index(g) for g in GROUPS[:OTHER]
            if comb[g]["test_boxes"] >= RELIABLE_MIN_TEST_BOXES
            and comb[g]["group_correct_when_found"] >= RELIABLE_MIN_GROUP_ACC
            and comb[g]["precision"] >= RELIABLE_MIN_PRECISION]
print("reliable groups:", [GROUPS[i] for i in reliable])

summary = []
for tag, res in EVAL.items():
    for name, s in res["sets"].items():
        for _, r in s["table"].iterrows():
            summary.append(dict(model=tag, test_set=name, threshold=res["threshold"], **r.to_dict()))
summary = pd.DataFrame(summary)
summary.to_csv(WORK_DIR / "group_scores.csv", index=False)
for tag, res in EVAL.items():
    for name, s in res["sets"].items():
        pd.DataFrame(s["confusion"], index=[f"true {g}" for g in GROUPS], columns=GROUPS).to_csv(
            WORK_DIR / f"confusion_{tag}_{name}.csv")

save_json({"names": GROUPS}, "pest_labels.json")
save_json({"onnx_file": INT8.name, "fp32_onnx_file": FP32.name, "img_size": IMG_SIZE,
           "letterbox": "square 640 x 640, grey (114) padding", "color_order": "RGB", "scale": "pixel / 255",
           "layout": "NCHW float32 (the INT8 model quantizes its input internally)",
           "output": f"(1, {4 + len(GROUPS)}, 8400): 4 box values (cx, cy, w, h) + {len(GROUPS)} group scores; NMS by the app",
           "conf_threshold": final["threshold"], "nms_iou": 0.7,
           "conf_threshold_note": "chosen for the INT8 model on validation negatives (<= 5% false alarms)"},
          f"{MODEL_NAME}.json")
save_json({"weights": f"{MODEL_NAME}.pt", "img_size": IMG_SIZE, "conf_threshold": final["threshold"], "nms_iou": 0.7,
           "classes": GROUPS, "topic_by_class": {str(i): TOPIC_OF_GROUP[g] for i, g in enumerate(GROUPS)},
           "reliable_species_ids": reliable, "reliable_species_names": [GROUPS[i] for i in reliable],
           "rule": "box conf >= conf_threshold -> 'pest present'; give the group's advice topic only if the class id "
                   "is in reliable_species_ids, otherwise 'insect pest - species uncertain'"}, "pest_config.json")
save_json({"start_weights": start, "epochs_run": int(model.trainer.epoch + 1), "data": {
               "ip102": {s: len(v) for s, v in IP_SPLIT.items()}, "chili": {s: len(v) for s, v in CHILI_SPLIT.items()},
               "chili_removed_copies_of_test_photos": len(leak), "chili_label_groups": {str(k): GROUPS[v] for k, v in CHILI_GROUP.items()},
               "chili_left_out_label_disagrees_with_file_name": {f"{k[0]}:{k[1]}": v for k, v in chili_disagree.items()},
               "negatives": {k: len(v) for k, v in NEG.items()}},
           "group_species": GROUP_SPECIES, "reliable_groups": [GROUPS[i] for i in reliable], "combined_int8": comb,
           "models": {tag: {"threshold": r["threshold"], "false_alarms": r["false_alarms"],
                            **{f"{n}_species_correct_when_found": s["species_correct_when_found"]
                               for n, s in r["sets"].items() if "species_correct_when_found" in s}}
                      for tag, r in EVAL.items()},
           "config": dict(img_size=IMG_SIZE, batch=BATCH, aug=AUG, group_repeat=GROUP_REPEAT, seed=SEED,
                          ultralytics=ultralytics.__version__, torch=torch.__version__),
           "total_hours": (time.time() - T_START) / 3600}, "results.json")
pd.set_option("display.width", 250)
print(summary.round(3).to_string(index=False))
print(sorted(p.name for p in WORK_DIR.iterdir()))
