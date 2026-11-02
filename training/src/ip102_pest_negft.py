# %% [markdown]
# # KrishiRakshak PS1 - IP102 pest detector: fine-tune with insect-free leaf images (Kaggle GPU)
#
# The 100-epoch YOLOv8n detector reached mAP50 0.569 on the IP102 test split, but flagged **49% of plain tomato
# leaves** (no insects) as pests at confidence 0.25, because IP102 contains only insect photos. This notebook starts
# from those trained weights and fine-tunes with **insect-free leaf images (empty labels = background)** added to the
# training split, then compares before vs after on identical held-out images.
#
# Negative leaf images are split by leaf/photo group, never shared across parts:
# - **PlantVillage tomato leaves** (all classes except spider mites): 70% train / 10% validation / 20% test (by
#   camera-sequence group).
# - **PlantDoc tomato photos** (field): training folder -> 85% train / 15% validation; the separate test folder -> test.
# The confidence threshold is picked on the **validation** negatives only; false-alarm numbers are reported on the
# **test** negatives. IP102 detection metrics use the official IP102 test split, as before.
#
# **Kaggle setup:** Accelerator = *GPU T4*, Internet = on, attach `parserpixy/ip102-dataset`,
# `abdallahalidev/plantvillage-dataset`, `nirmalsankalana/plantdoc-dataset`, and the output of your
# `ps1-ip102-pest` notebook run (the trained weights).

# %%
import os, sys, subprocess

ON_KAGGLE = os.path.exists("/kaggle/input")
SMOKE = os.environ.get("KR_SMOKE") == "1"
os.environ.setdefault("WANDB_MODE", "disabled")
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "ultralytics==8.4.7"], check=True)

# %%
import hashlib, json, random, re, shutil, time
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml
from PIL import Image
import ultralytics
from ultralytics import YOLO, settings as yolo_settings

for key in ("wandb", "mlflow", "comet", "clearml", "dvc", "neptune", "raytune", "tensorboard"):
    try:
        yolo_settings.update({key: False})
    except Exception:
        pass
print("torch", torch.__version__, "| ultralytics", ultralytics.__version__)

# %% [markdown]
# ## Configuration

# %%
SEED = 42
INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "pest_outputs_negft"
WORK_DIR.mkdir(parents=True, exist_ok=True)

MODEL_WEIGHTS = "yolov8n.pt"          # COCO-pretrained starting point
REUSE_WEIGHTS = os.environ.get("KR_PEST_WEIGHTS")  # path to an already-trained best.pt -> skip training
REQUIRE_TRAINED_WEIGHTS = True  # this notebook always starts from the trained detector
FT_EPOCHS = int(os.environ.get("KR_EPOCHS", 1 if SMOKE else 30))
FT_LR0 = 0.002                  # low fixed learning rate for fine-tuning (SGD; "auto" would override it)
NEG_PV_TRAIN_MAX = 40 if SMOKE else 3500   # PlantVillage negatives added to training
NEG_EVAL_MAX = 30 if SMOKE else 1000       # cap per validation / test negative set
NEG_TOMATO_FOLDERS = ["Tomato___healthy", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Leaf_Mold",
                      "Tomato___Septoria_leaf_spot", "Tomato___Bacterial_spot",
                      "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___Tomato_mosaic_virus",
                      "Tomato___Target_Spot"]  # spider-mite images show mites -> excluded
IMG_SIZE = 128 if SMOKE else 640
EPOCHS = int(os.environ.get("KR_EPOCHS", 1 if SMOKE else 100))
PATIENCE = 25
BATCH = 8 if SMOKE else 32
WORKERS = 0 if SMOKE else 4
VAL_FRACTION = 0.10                   # carved from the official trainval split; official test split stays untouched
CONF_GRID = [0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7]
MAX_FALSE_ALARM_RATE = 0.05           # recommended threshold: lowest confidence with <=5% false alarms on clean leaves
RELIABLE_MIN_TEST_BOXES, RELIABLE_MIN_SPECIES_ACC, RELIABLE_MIN_AP50 = 10, 0.70, 0.50

# Online augmentation (YOLO defaults + vertical flip and rotation for insects at any angle)
AUG = dict(degrees=30.0, flipud=0.5, fliplr=0.5, hsv_h=0.015, hsv_s=0.6, hsv_v=0.4, translate=0.1, scale=0.5,
           shear=2.0, perspective=0.0005, mosaic=1.0, mixup=0.1, close_mosaic=10)

# IP102 class names, 0-based (from the official classes.txt; annotation <name> values are 0-based ids)
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

random.seed(SEED); np.random.seed(SEED)
DEVICE = 0 if torch.cuda.is_available() else "cpu"
print("device:", torch.cuda.get_device_name(0) if DEVICE == 0 else "cpu")
def assert_gpu_usable():
    """Fail fast if the assigned GPU is not supported by this PyTorch build (e.g. P100 on new CUDA wheels)."""
    if not torch.cuda.is_available():
        print("WARNING: no GPU - enable Accelerator = GPU T4 in the notebook settings."); return
    try:
        x = torch.randn(1, 3, 32, 32, device="cuda")
        torch.nn.functional.conv2d(x, torch.randn(4, 3, 3, 3, device="cuda")).sum().item()
    except RuntimeError as e:
        raise RuntimeError(f"GPU {torch.cuda.get_device_name(0)} is not usable with torch {torch.__version__}: {e}\n"
                           "Open the notebook settings, choose Accelerator = 'GPU T4 x2', and run again.") from e

assert_gpu_usable()

def save_json(obj, name):
    """Write obj as indented JSON into WORK_DIR (numpy values are converted to plain Python)."""
    with open(WORK_DIR / name, "w") as f:
        json.dump(obj, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))

# %% [markdown]
# ## Locate datasets

# %%
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

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
    """Return the IP102 VOC root (Annotations/ + JPEGImages/) and the paths of its trainval/test split files."""
    for d, dirs, files in walk_dirs(INPUT_ROOT):
        if "Annotations" in dirs and "JPEGImages" in dirs:
            split_files = {}
            for sd, _, sfiles in walk_dirs(d, max_depth=3):
                for name in ("trainval.txt", "test.txt"):
                    if name in sfiles and name not in split_files:
                        split_files[name] = sd / name
            return d, split_files
    raise FileNotFoundError("IP102 VOC folders (Annotations/, JPEGImages/) not found - attach parserpixy/ip102-dataset")

def find_plantvillage_color():
    """Return the PlantVillage 'color' folder (the variant that contains the tomato class folders)."""
    for d, _, _ in walk_dirs(INPUT_ROOT):
        if d.name.lower() == "color" and (d / "Tomato___Early_blight").is_dir():
            return d
    return None

def find_trained_weights():
    """best.pt from a previous run of this notebook attached as input (e.g. kernel output), else None."""
    for d, _, files in walk_dirs(INPUT_ROOT, max_depth=8):
        if "best.pt" in files and d.name == "weights" and d.parent.name == "ip102_yolov8n":
            return str(d / "best.pt")
        if "ip102_yolov8n_best.pt" in files:
            return str(d / "ip102_yolov8n_best.pt")
    return None

def find_plantdoc_classification():
    """Return the PlantDoc copy that is organised as train/ and test/ class folders."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT):
        if "test" in dirs and "train" in dirs:
            if any(re.sub(r"[\s_]+", " ", c).strip().lower() == "tomato early blight leaf" for c in os.listdir(d / "test")):
                return d
    return None

IP_ROOT, IP_SPLITS = find_ip102()
PD_CLS_ROOT = find_plantdoc_classification()
print("PlantDoc classification copy:", PD_CLS_ROOT)
PV_ROOT = find_plantvillage_color()
REUSE_WEIGHTS = REUSE_WEIGHTS or find_trained_weights()
print("trained weights found in inputs (training will be skipped):", REUSE_WEIGHTS)
if REQUIRE_TRAINED_WEIGHTS and not REUSE_WEIGHTS:
    raise FileNotFoundError("evaluation-only run, but no trained ip102_yolov8n weights were found in the inputs")
print("IP102 root:", IP_ROOT, "| split files:", {k: str(v) for k, v in IP_SPLITS.items()})
print("PlantVillage color:", PV_ROOT)

# %% [markdown]
# ## Parse annotations and profile the data
# Class ids are read from the XML annotations (not from file names, which turned out not to match the labels for
# every class). Image sizes are read from the actual image files.

# %%
def read_ids(path):
    """Read one image id per line from a split file (empty list if the file is missing)."""
    return [l.strip() for l in open(path) if l.strip()] if path else []

def find_image(img_id):
    """Return the JPEGImages path of an IP102 image id, trying the common extensions."""
    for ext in (".jpg", ".jpeg", ".png", ".JPG"):
        p = IP_ROOT / "JPEGImages" / f"{img_id}{ext}"
        if p.exists():
            return p
    return None

def read_xml_objects(xml_path):
    """Return (<object> elements, note). Some IP102 files contain extra text or a second <annotation> block after
    the first one; those are repaired by wrapping everything in one root and keeping all objects."""
    text = xml_path.read_text(errors="ignore")
    try:
        return list(ET.fromstring(text).iter("object")), None
    except ET.ParseError:
        body = re.sub(r"<\?xml[^>]*\?>", "", text)
        try:
            return list(ET.fromstring(f"<root>{body}</root>").iter("object")), "repaired xml"
        except ET.ParseError:
            return None, "unparseable xml"

def parse_one(img_id):
    """Parse one IP102 annotation; never raises (problems are recorded in the result instead)."""
    try:
        return _parse_one(img_id)
    except Exception as e:  # never let one bad file stop the run
        return dict(id=img_id, image=None, width=0, height=0, boxes=[], problems=[f"parse failure: {e}"])

def _parse_one(img_id):
    """Read the image size and all valid boxes (class id, x1, y1, x2, y2) for one IP102 image id."""
    rec = dict(id=img_id, image=None, width=0, height=0, boxes=[], problems=[])
    xml_path, img_path = IP_ROOT / "Annotations" / f"{img_id}.xml", find_image(img_id)
    if img_path is None or not xml_path.exists():
        rec["problems"].append("missing image or annotation"); return rec
    try:
        with Image.open(img_path) as im:
            W, H = im.size
    except Exception as e:
        rec["problems"].append(f"unreadable image: {e}"); return rec
    rec.update(image=str(img_path), width=W, height=H)
    objects, note = read_xml_objects(xml_path)
    if note:
        rec["problems"].append(note)
    if objects is None:
        return rec
    for obj in objects:
        try:
            c = int(obj.findtext("name").strip())
            bb = obj.find("bndbox")
            x1, y1, x2, y2 = (float(bb.findtext(k)) for k in ("xmin", "ymin", "xmax", "ymax"))
        except Exception:
            rec["problems"].append("bad object"); continue
        if not 0 <= c < NC:
            rec["problems"].append(f"class id {c} out of range"); continue
        x1, x2 = sorted((min(max(x1, 0), W), min(max(x2, 0), W)))
        y1, y2 = sorted((min(max(y1, 0), H), min(max(y2, 0), H)))
        if x2 - x1 < 2 or y2 - y1 < 2:
            rec["problems"].append("degenerate box"); continue
        if (c, x1, y1, x2, y2) not in rec["boxes"]:  # repaired files can repeat the same box
            rec["boxes"].append((c, x1, y1, x2, y2))
    return rec

trainval_ids, test_ids = read_ids(IP_SPLITS.get("trainval.txt")), read_ids(IP_SPLITS.get("test.txt"))
if not trainval_ids:  # fall back to every annotation if the split files are absent
    trainval_ids = sorted(p.stem for p in (IP_ROOT / "Annotations").glob("*.xml"))
    print("WARNING: no trainval.txt - using all annotations; test split will be carved randomly")
t0 = time.time()
with ThreadPoolExecutor(16) as ex:
    recs = {r["id"]: r for r in ex.map(parse_one, sorted(set(trainval_ids) | set(test_ids)))}
print(f"parsed {len(recs)} annotations in {time.time() - t0:.0f}s")

problems = Counter(p.split(":")[0] for r in recs.values() for p in r["problems"])
print("annotation problems:", dict(problems) or "none")
usable = {k: r for k, r in recs.items() if r["image"] and r["boxes"]}
print("usable images:", len(usable), "of", len(recs))

# File-name code vs annotated class (informational only)
name_mismatch = sum(1 for k, r in usable.items() if re.match(r"^IP\d{3}", k) and int(k[2:5]) != r["boxes"][0][0])
print(f"images whose file-name class code differs from the annotated class: {name_mismatch}")

# %% [markdown]
# ## Splits: official test untouched; validation carved from trainval per class

# %%
def primary_class(r):
    """Most frequent class among the boxes of one annotated image."""
    return Counter(c for c, *_ in r["boxes"]).most_common(1)[0][0]

rng = random.Random(SEED)
tv = [i for i in trainval_ids if i in usable]
te = [i for i in test_ids if i in usable]
if not te:  # fallback only
    rng.shuffle(tv); cut = int(len(tv) * 0.2); te, tv = tv[:cut], tv[cut:]
by_class = {}
for i in tv:
    by_class.setdefault(primary_class(usable[i]), []).append(i)
train_ids, val_ids = [], []
for c, ids in sorted(by_class.items()):
    ids = sorted(ids); rng.shuffle(ids)
    n_val = int(round(len(ids) * VAL_FRACTION)) if len(ids) >= 2 else 0
    n_val = min(n_val, len(ids) - 1)
    val_ids += ids[:n_val]; train_ids += ids[n_val:]
SPLITS = {"train": sorted(train_ids), "val": sorted(val_ids), "test": sorted(te)}
assert not (set(SPLITS["train"]) & set(SPLITS["test"])) and not (set(SPLITS["val"]) & set(SPLITS["test"]))

prof = []
for split, ids in SPLITS.items():
    imgs, boxes = Counter(), Counter()
    for i in ids:
        cls = [c for c, *_ in usable[i]["boxes"]]
        boxes.update(cls); imgs.update(set(cls))
    for c in range(NC):
        prof.append(dict(class_id=c, name=IP102_NAMES[c], split=split, images=imgs[c], boxes=boxes[c]))
prof = pd.DataFrame(prof)
class_table = prof.pivot_table(index=["class_id", "name"], columns="split", values="boxes").reset_index()
class_table.columns.name = None
class_table.to_csv(WORK_DIR / "ip102_class_profile.csv", index=False)
print({s: len(v) for s, v in SPLITS.items()})
print("classes with ZERO training boxes:", class_table.loc[class_table.train == 0, "name"].tolist())
bins = pd.cut(class_table.train, [-1, 0, 19, 49, 99, 299, 10**9], labels=["0", "1-19", "20-49", "50-99", "100-299", "300+"])
print("training boxes per class (number of classes):", bins.value_counts().sort_index().to_dict())

# %% [markdown]
# ## Insect-free leaf images (negatives), split by leaf / photo group

# %%
def bucket(key):
    """Stable 0-99 bucket for a key, so the same leaf or photo always lands in the same split."""
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % 100

def pv_group(path):
    """Leaf group of a PlantVillage file name (camera-sequence block or leaf id)."""
    stem = Path(path).stem.split("___", 1)[-1].strip()
    m = re.match(r"^(.*?)\s+day\s*\d+.*$", stem, re.I)
    if m:
        return re.sub(r"[.]\d+$", "", m.group(1).strip().lower())
    m = re.match(r"^(.*?)(\d+)(?:\.\d+)?$", stem)
    return f"{m.group(1).strip().lower()}|{int(m.group(2)) // 20}" if m else stem.lower()

NEG = {"train": [], "val_pv": [], "test_pv": [], "val_pd": [], "test_pd": []}
if PV_ROOT is not None:
    for folder in NEG_TOMATO_FOLDERS:
        if not (PV_ROOT / folder).is_dir():
            continue
        for p in sorted((PV_ROOT / folder).iterdir()):
            if p.suffix.lower() in IMG_EXT:
                b = bucket(folder + "|" + pv_group(p.name))
                NEG["train" if b < 70 else "val_pv" if b < 80 else "test_pv"].append(str(p))
    rng = random.Random(SEED)
    NEG["train"] = rng.sample(NEG["train"], min(NEG_PV_TRAIN_MAX, len(NEG["train"])))
if PD_CLS_ROOT is not None:
    for split_dir in ("train", "test"):
        for cdir in sorted((PD_CLS_ROOT / split_dir).iterdir()):
            name = re.sub(r"[\s_]+", " ", cdir.name).strip().lower()
            if not cdir.is_dir() or not name.startswith("tomato") or "mite" in name:
                continue
            for p in sorted(cdir.iterdir()):
                if p.suffix.lower() in IMG_EXT:
                    if split_dir == "test":
                        NEG["test_pd"].append(str(p))
                    else:
                        NEG["val_pd" if bucket(str(p.name)) < 15 else "train"].append(str(p))
rng = random.Random(SEED + 1)
for k in ("val_pv", "test_pv", "val_pd", "test_pd"):
    NEG[k] = rng.sample(NEG[k], min(NEG_EVAL_MAX, len(NEG[k])))
assert not set(NEG["train"]) & set(sum((NEG[k] for k in NEG if k != "train"), []))
print({k: len(v) for k, v in NEG.items()})

# %% [markdown]
# ## Build the YOLO-format dataset (labels written, images symlinked - no image copies)

# %%
# Kept OUTSIDE the Kaggle output folder: Kaggle saves only ~500 output files per run, and 19k label files would
# crowd out the trained weights (this happened in an earlier run).
YOLO_DIR = (Path("/tmp") if ON_KAGGLE else WORK_DIR) / "ip102_yolo"
if YOLO_DIR.exists():
    shutil.rmtree(YOLO_DIR)
for split, ids in SPLITS.items():
    (YOLO_DIR / "images" / split).mkdir(parents=True); (YOLO_DIR / "labels" / split).mkdir(parents=True)
    for i in ids:
        r = usable[i]; src = Path(r["image"])
        dst = YOLO_DIR / "images" / split / src.name
        try:
            os.symlink(src, dst)
        except OSError:
            shutil.copy(src, dst)
        W, H = r["width"], r["height"]
        lines = [f"{c} {(x1 + x2) / 2 / W:.6f} {(y1 + y2) / 2 / H:.6f} {(x2 - x1) / W:.6f} {(y2 - y1) / H:.6f}"
                 for c, x1, y1, x2, y2 in r["boxes"]]
        (YOLO_DIR / "labels" / split / f"{src.stem}.txt").write_text("\n".join(lines) + "\n")
for k, src in enumerate(NEG["train"]):  # negatives: image with an EMPTY label file = background
    dst = YOLO_DIR / "images" / "train" / f"neg_{k:05d}{Path(src).suffix.lower()}"
    try:
        os.symlink(src, dst)
    except OSError:
        shutil.copy(src, dst)
    (YOLO_DIR / "labels" / "train" / f"neg_{k:05d}.txt").write_text("")
print("negative (insect-free) images added to training:", len(NEG["train"]))
DATA_YAML = YOLO_DIR / "data.yaml"
yaml.safe_dump({"path": str(YOLO_DIR), "train": "images/train", "val": "images/val", "test": "images/test",
                "names": dict(enumerate(IP102_NAMES))}, open(DATA_YAML, "w"), sort_keys=False)
shutil.copy(DATA_YAML, WORK_DIR / "ip102_data.yaml")
print(DATA_YAML.read_text()[:300])

# %% [markdown]
# ## Fine-tune the trained detector (IP102 + insect-free leaves)

# %%
BASE = Path(REUSE_WEIGHTS)
t0 = time.time()
model = YOLO(str(BASE))
model.train(data=str(DATA_YAML), epochs=FT_EPOCHS, imgsz=IMG_SIZE, batch=BATCH, patience=PATIENCE, workers=WORKERS,
            device=DEVICE, seed=SEED, project=str(WORK_DIR / "runs"), name="ip102_yolov8n_negft", exist_ok=True,
            plots=True, verbose=False, optimizer="SGD", lr0=FT_LR0, warmup_epochs=1, **dict(AUG, close_mosaic=5))
BEST = Path(model.trainer.save_dir) / "weights" / "best.pt"
shutil.copy(BEST, WORK_DIR / "ip102_yolov8n_negft_best.pt")  # save the weights before any evaluation can fail
print(f"fine-tuning took {(time.time() - t0) / 60:.1f} min -> {BEST}")

# %% [markdown]
# ## Evaluate before (base) and after (fine-tuned) on identical images
# - IP102 official test split: mAP, and the two-level "pest found" / "species correct" rates per confidence threshold.
# - False alarms: fraction of insect-free leaf images with any detection at or above the threshold.
# - Each model's threshold is chosen on the **validation** negatives (<= 5% false alarms); test negatives only report.

# %%
def iou_matrix(a, b):
    """Pairwise intersection-over-union between box arrays a (n, 4) and b (m, 4) in x1y1x2y2 format."""
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    x1 = np.maximum(a[:, None, 0], b[None, :, 0]); y1 = np.maximum(a[:, None, 1], b[None, :, 1])
    x2 = np.minimum(a[:, None, 2], b[None, :, 2]); y2 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area = lambda z: (z[:, 2] - z[:, 0]) * (z[:, 3] - z[:, 1])
    return inter / (area(a)[:, None] + area(b)[None, :] - inter + 1e-9)

def run_predictions(m, paths, conf=0.05, chunk=int(os.environ.get("KR_PRED_CHUNK", 32))):
    """Predict in chunks: a list source is loaded as ONE batch by Ultralytics (3,798 images -> 17 GB)."""
    out, paths = {}, [str(p) for p in paths]
    for s in range(0, len(paths), chunk):
        for r in m.predict(source=paths[s:s + chunk], conf=conf, imgsz=IMG_SIZE, device=DEVICE,
                           stream=True, verbose=False):
            b = r.boxes
            out[r.path] = (b.xyxy.cpu().numpy(), b.conf.cpu().numpy(), b.cls.cpu().numpy().astype(int))
    return out

def two_level(preds):
    """Per threshold: share of insects found (any species), species accuracy when found, and box precision."""
    preds = {Path(k).stem: v for k, v in preds.items()}  # IP102 image ids are unique
    rows, by_class = [], {}
    for t in CONF_GRID:
        gt_total = gt_found = species_ok = pred_total = pred_tp = 0
        cls_found, cls_total, cls_ok = Counter(), Counter(), Counter()
        for i in SPLITS["test"]:
            r = usable[i]
            gt = np.array([b[1:] for b in r["boxes"]], float); gt_cls = np.array([b[0] for b in r["boxes"]])
            pb, pc, pk = preds.get(Path(r["image"]).stem, (np.zeros((0, 4)), np.zeros(0), np.zeros(0, int)))
            keep = pc >= t; pb, pk = pb[keep], pk[keep]
            iou = iou_matrix(gt, pb)
            found = iou.max(1) >= 0.5 if len(pb) else np.zeros(len(gt), bool)
            gt_total += len(gt); gt_found += found.sum(); cls_total.update(gt_cls.tolist())
            if found.any():
                ok = found & (pk[iou.argmax(1)] == gt_cls)
                species_ok += ok.sum(); cls_found.update(gt_cls[found].tolist()); cls_ok.update(gt_cls[ok].tolist())
            pred_total += len(pb); pred_tp += (iou.max(0) >= 0.5).sum() if len(gt) and len(pb) else 0
        rows.append(dict(conf=t, pest_found_rate=gt_found / max(gt_total, 1),
                         species_correct_when_found=species_ok / max(gt_found, 1),
                         species_correct_overall=species_ok / max(gt_total, 1),
                         box_precision_any_species=pred_tp / max(pred_total, 1)))
        by_class[t] = (cls_total, cls_found, cls_ok)
    return pd.DataFrame(rows), by_class

def evaluate(weights, tag):
    """Evaluate one detector: IP102 test mAP, two-level rates, false alarms on negatives, and its chosen threshold."""
    m = YOLO(str(weights))
    tm = m.val(data=str(DATA_YAML), split="test", imgsz=IMG_SIZE, batch=BATCH, device=DEVICE, plots=(tag == "negft"),
               project=str(WORK_DIR / "runs"), name=f"test_eval_{tag}", exist_ok=True, verbose=False)
    per_class = class_table.merge(pd.DataFrame({"class_id": [int(c) for c in tm.box.ap_class_index],
                                                "ap50": tm.box.ap50, "ap50_95": tm.box.ap}), on="class_id", how="left")
    levels, by_class = two_level(run_predictions(m, [usable[i]["image"] for i in SPLITS["test"]]))
    for k in ("val_pv", "val_pd", "test_pv", "test_pd"):
        if NEG[k]:
            preds = run_predictions(m, NEG[k])
            max_conf = np.array([v[1].max() if len(v[1]) else 0.0 for v in preds.values()])
            levels[f"false_alarm_{k}"] = [float((max_conf >= t).mean()) for t in CONF_GRID]
    val_cols = [c for c in levels if c.startswith("false_alarm_val")]
    ok = levels[(levels[val_cols] <= MAX_FALSE_ALARM_RATE).all(axis=1)].conf if val_cols else levels.conf[levels.conf == 0.25]
    thr = float(ok.min()) if len(ok) else float(max(CONF_GRID))
    print(f"[{tag}] TEST mAP50={tm.box.map50:.4f} mAP50-95={tm.box.map:.4f} | threshold (validation negatives) = {thr}")
    print(levels.round(4).to_string(index=False))
    return dict(tm=tm, per_class=per_class, levels=levels, by_class=by_class, threshold=thr)

EVAL = {"base": evaluate(BASE, "base"), "negft": evaluate(BEST, "negft")}

compare = []
for tag, r in EVAL.items():
    for label, t in (("at its chosen threshold", r["threshold"]), ("at 0.25", 0.25), ("at 0.5", 0.5)):
        row = r["levels"][r["levels"].conf == t].iloc[0].to_dict()
        compare.append(dict(model=tag, setting=label, test_map50=float(r["tm"].box.map50), **row))
compare = pd.DataFrame(compare)
compare.to_csv(WORK_DIR / "before_after.csv", index=False)
pd.set_option("display.width", 250)
print(compare.round(4).to_string(index=False))

# %% [markdown]
# ## Per-species reliability of the fine-tuned detector at its threshold

# %%
FT = EVAL["negft"]; CONF_THRESHOLD = FT["threshold"]
per_class = FT["per_class"]
cls_total, cls_found, cls_ok = FT["by_class"][CONF_THRESHOLD]
per_class["test_gt_boxes"] = per_class.class_id.map(lambda c: cls_total[c])
per_class["found_rate"] = per_class.class_id.map(lambda c: cls_found[c] / cls_total[c] if cls_total[c] else np.nan)
per_class["species_acc_when_found"] = per_class.class_id.map(lambda c: cls_ok[c] / cls_found[c] if cls_found[c] else np.nan)
per_class["reliable_species"] = ((per_class.test_gt_boxes >= RELIABLE_MIN_TEST_BOXES)
                                 & (per_class.species_acc_when_found >= RELIABLE_MIN_SPECIES_ACC)
                                 & (per_class.ap50 >= RELIABLE_MIN_AP50))
per_class.to_csv(WORK_DIR / "per_species_results.csv", index=False)
reliable = per_class[per_class.reliable_species]
print(f"reliable species: {len(reliable)} of {NC}")

# %% [markdown]
# ## Save artefacts for the later ONNX / Raspberry Pi step

# %%
save_json({"names": IP102_NAMES}, "pest_labels.json")
save_json({"weights": "ip102_yolov8n_negft_best.pt", "img_size": IMG_SIZE, "letterbox": True, "color_order": "RGB",
           "scale": "pixel / 255", "conf_threshold": CONF_THRESHOLD, "nms_iou": 0.7,
           "reliable_species_ids": reliable.class_id.astype(int).tolist(),
           "reliable_species_names": reliable.name.tolist(),
           "rule": "box conf >= conf_threshold -> 'pest present'; name the species only if its id is in "
                   "reliable_species_ids, otherwise report 'insect pest - species uncertain'"}, "pest_config.json")
save_json({"base_weights": str(BASE), "negatives": {k: len(v) for k, v in NEG.items()},
           "models": {tag: {"test_map50": float(r["tm"].box.map50), "test_map50_95": float(r["tm"].box.map),
                            "threshold": r["threshold"], "levels": r["levels"].to_dict(orient="records")}
                      for tag, r in EVAL.items()},
           "config": dict(ft_epochs=FT_EPOCHS, ft_lr0=FT_LR0, optimizer="SGD", img_size=IMG_SIZE, batch=BATCH,
                          aug=dict(AUG, close_mosaic=5), seed=SEED, ultralytics=ultralytics.__version__,
                          torch=torch.__version__)}, "results.json")
n_files = sum(1 for _ in WORK_DIR.rglob("*") if _.is_file())
print(f"{n_files} output files (Kaggle keeps ~500):", sorted(p.name for p in WORK_DIR.iterdir()))
