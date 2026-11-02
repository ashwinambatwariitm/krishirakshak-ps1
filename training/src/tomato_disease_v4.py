# %% [markdown]
# # KrishiRakshak PS1 - Tomato disease training v4: all 10 tomato classes (Kaggle GPU)
#
# Extends the v3 recipe (PlantVillage + PlantDoc training share, EMA weights, cosine schedule) from 5 to **all 10
# PlantVillage tomato classes**, and measures the **deployment footprint** (model size, compute, CPU latency, RAM) plus
# what adding more crops later would cost.
#
# | Class | PlantDoc field images? |
# |---|---|
# | healthy, early blight, late blight, leaf mold, septoria leaf spot | yes |
# | bacterial spot, yellow leaf curl virus, mosaic virus | yes |
# | target spot | **no** - lab-validated only |
# | spider mites | only 2 photos - excluded from PlantDoc, lab-validated only |
#
# Test rules (unchanged): PlantVillage test (15%) and PlantDoc test (25%) are never used for training, checkpoint
# selection or any tuning; photos of one leaf and copies of one photo (across both PlantDoc copies) stay in one split;
# PlantDoc photos resembling PlantVillage are dropped. Field macro F1 is computed over the classes present in the field
# test set, so classes with no field data are not counted as field failures or successes.
#
# **Kaggle setup:** Accelerator = *GPU T4*, Internet = on, attach `abdallahalidev/plantvillage-dataset`,
# `yusufmurtaza01/plantdoc-object-detection-dataset`, `nirmalsankalana/plantdoc-dataset`.

# %%
import os, sys, subprocess

ON_KAGGLE = os.path.exists("/kaggle/input")
SMOKE = os.environ.get("KR_SMOKE") == "1"  # tiny local test run
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "albumentations==2.0.8"], check=True)

# %%
import json, math, random, re, time, warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import albumentations as A
import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import yaml
from albumentations.pytorch import ToTensorV2
from PIL import Image
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import models

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
print("torch", torch.__version__, "| albumentations", A.__version__, "| cv2", cv2.__version__)

# %% [markdown]
# ## Configuration

# %%
SEED = 42
INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "disease_outputs_v4"
WORK_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE = 224
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
BATCH = 16 if SMOKE else 64
NUM_WORKERS = 2 if SMOKE else 4
EPOCHS = 1 if SMOKE else 20
WARMUP_EPOCHS = 1
EMA_DECAY = 0.998                # per optimiser step (~125 steps per epoch)
SEEDS = [42, 7]
EPOCH_SAMPLES = 160 if SMOKE else 10000  # images drawn per epoch by the balanced sampler
PATIENCE = 10
PD_SHARE = 0.5                  # fraction of each training batch drawn from PlantDoc (field) images
PV_TEST_FRAC, PV_VAL_FRAC = 0.15, 0.15
PD_TEST_FRAC, PD_VAL_FRAC = 0.25, 0.10
TARGET_DISEASED_RECALL = 0.98   # gate threshold tuned on validation to miss at most ~2% of diseased leaves
SEQ_BLOCK = 20                  # PlantVillage camera-sequence numbers grouped in blocks of 20 (4-7 shots per leaf)
HASH_MAX_DIST = 16              # pHash bits: same photo (rotation/flip invariant); real duplicates <= 6, different leaves >= 92
MAX_GROUP_SIZE = 60             # duplicate merging never grows a group beyond this
PLANTDOC_LEAK_DIST = 20         # PlantDoc images this close to any PlantVillage image are dropped entirely
MIN_CROP_SIDE = 32              # PlantDoc leaf boxes smaller than this (px) are skipped
MIN_PD_CLASS_ROWS = 20          # PlantDoc classes with fewer samples are left out of PlantDoc entirely (too few to
                                # train or test on; the balanced sampler would otherwise repeat them hundreds of times)
DECODE_MIN_SIDE = 336           # large JPEGs are decoded at reduced scale but never below this many px for the region used

# Order matters: index 0 must be healthy (the gate and the cascade rely on it).
TOMATO_CLASSES = {  # the first five keep their v3 indices
    "healthy": "Tomato___healthy",
    "early_blight": "Tomato___Early_blight",
    "late_blight": "Tomato___Late_blight",
    "leaf_mold": "Tomato___Leaf_Mold",
    "septoria_leaf_spot": "Tomato___Septoria_leaf_spot",
    "bacterial_spot": "Tomato___Bacterial_spot",
    "yellow_leaf_curl_virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "mosaic_virus": "Tomato___Tomato_mosaic_virus",
    "target_spot": "Tomato___Target_Spot",
    "spider_mites": "Tomato___Spider_mites Two-spotted_spider_mite",
}
CLASS_NAMES = list(TOMATO_CLASSES)
DISEASE_NAMES = CLASS_NAMES[1:]
GATE_NAMES = ["healthy", "diseased"]

# PlantDoc label -> our label. "Tomato leaf" is PlantDoc's generic healthy-tomato class.
PLANTDOC_MAP = {
    "tomato leaf": "healthy",
    "tomato early blight leaf": "early_blight",
    "tomato leaf late blight": "late_blight",
    "tomato mold leaf": "leaf_mold",
    "tomato septoria leaf spot": "septoria_leaf_spot",
    "tomato leaf bacterial spot": "bacterial_spot",
    "tomato leaf yellow virus": "yellow_leaf_curl_virus",
    "tomato leaf mosaic virus": "mosaic_virus",
    "tomato two spotted spider mites leaf": "spider_mites",
}

random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
USE_AMP = DEVICE.type == "cuda"
print("device:", DEVICE, torch.cuda.get_device_name(0) if USE_AMP else "")

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

def norm_name(s):
    """Normalise a class or folder name: underscores to spaces, single spaces, lower case."""
    return re.sub(r"\s+", " ", s.replace("_", " ")).strip().lower()

def save_json(obj, name):
    """Write obj as indented JSON into WORK_DIR (numpy values are converted to plain Python)."""
    with open(WORK_DIR / name, "w") as f:
        json.dump(obj, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))

# %% [markdown]
# ## Locate the attached datasets

# %%
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def walk_dirs(root, max_depth=6):
    """os.walk below root up to max_depth, skipping folders that never need searching (keeps discovery fast)."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        p = Path(dirpath)
        if len(p.relative_to(root).parts) >= max_depth:
            dirnames[:] = []
        dirnames[:] = sorted(d for d in dirnames if "___" not in d)  # don't list PlantVillage class folders
        yield p, dirnames, filenames

def find_plantvillage_color():
    """Return the PlantVillage 'color' folder (the variant that contains the tomato class folders)."""
    for d, _, _ in walk_dirs(INPUT_ROOT):
        if d.name.lower() == "color" and (d / "Tomato___Early_blight").is_dir():
            return d
    raise FileNotFoundError("PlantVillage 'color' folder not found - attach abdallahalidev/plantvillage-dataset")

def find_plantdoc_detection():
    """Return (root, class names) of the PlantDoc copy that has YOLO boxes and a dataset yaml."""
    for d, _, files in walk_dirs(INPUT_ROOT):
        for f in files:
            if f.lower().endswith((".yaml", ".yml")) and (d / "images").is_dir():
                try:
                    cfg = yaml.safe_load(open(d / f))
                except Exception:
                    continue
                names = cfg.get("names") if isinstance(cfg, dict) else None
                if isinstance(names, list):
                    names = dict(enumerate(names))
                if isinstance(names, dict) and any(norm_name(str(n)) == "tomato septoria leaf spot" for n in names.values()):
                    return d, {int(k): str(v) for k, v in names.items()}
    return None, None

def find_plantdoc_classification():
    """Return the PlantDoc copy that is organised as train/ and test/ class folders."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT):
        if "test" in dirs and "train" in dirs:
            if any(norm_name(c) == "tomato early blight leaf" for c in os.listdir(d / "test")):
                return d
    return None

PV_ROOT = find_plantvillage_color()
PD_DET_ROOT, PD_DET_NAMES = find_plantdoc_detection()
PD_CLS_ROOT = find_plantdoc_classification()
print("PlantVillage color :", PV_ROOT)
print("PlantDoc detection :", PD_DET_ROOT)
print("PlantDoc full image:", PD_CLS_ROOT)
assert PD_DET_ROOT is not None or PD_CLS_ROOT is not None, "v2 needs at least one PlantDoc dataset attached"

# %% [markdown]
# ## Image profiling, perceptual hashing and grouping helpers

# %%
HASH_WORDS = 4  # 255-bit DCT pHash padded to 256 bits = 4 x uint64

def dihedral_phashes(img):
    """pHash of all 8 rotations/flips -> (8, HASH_WORDS). Real duplicates differ by <= 6 bits, different leaves >= 92."""
    g = img.convert("L").resize((64, 64), Image.BILINEAR)
    out = []
    for k in range(4):
        r = g.rotate(90 * k)
        for v in (r, r.transpose(Image.FLIP_LEFT_RIGHT)):
            d = cv2.dct(np.asarray(v, np.float32))[:16, :16].flatten()[1:]
            out.append(np.packbits(np.append(d > np.median(d), False)).view(">u8").astype(np.uint64))
    return np.stack(out)

def profile_one(path):
    """Open one image: record size and mode, flag unreadable files, and compute its rotation/flip pHashes."""
    try:
        with Image.open(path) as im:
            mode, (w, h) = im.mode, im.size
            im.draft("RGB", (256, 256))  # hashing only needs a small decode
            im.load()
            return dict(width=w, height=h, mode=mode, ok=True), dihedral_phashes(im)
    except Exception as e:
        return dict(width=0, height=0, mode="", ok=False, error=str(e)[:120]), np.zeros((8, HASH_WORDS), np.uint64)

def profile_paths(paths):
    """Profile many images in parallel; returns (DataFrame of sizes and status, array of hashes)."""
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(profile_one, paths))
    hashes = np.stack([r[1] for r in res]) if res else np.zeros((0, 8, HASH_WORDS), np.uint64)
    return pd.DataFrame([r[0] for r in res]), hashes

def popcount64(x):
    """Number of set bits in each uint64 value (Hamming weight), with a fallback for older numpy."""
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(x)
    return np.unpackbits(x.view(np.uint8).reshape(*x.shape, 8), axis=-1).sum(-1)

def near_duplicate_pairs(h_query, h_ref, max_dist, same=False, chunk=64):
    """Pairs (i, j) where query i's hash is within max_dist bits of any rotation/flip of reference j."""
    out = []
    for s in range(0, len(h_query), chunk):
        q = h_query[s:s + chunk, 0]
        d = popcount64(q[:, None, None, :] ^ h_ref[None, :, :, :]).sum(-1, dtype=np.int32).min(-1)
        ii, jj = np.nonzero(d <= max_dist)
        ii = ii + s
        if same:
            keep = ii < jj
            ii, jj = ii[keep], jj[keep]
        out.append(np.stack([ii, jj], 1))
    return np.concatenate(out) if out else np.zeros((0, 2), int)

class DSU:
    """Union-find structure used to merge duplicate photos into groups."""
    def __init__(self, n): self.p, self.size = list(range(n)), [1] * n
    def find(self, x):
        """Return the representative (root) of x's group, shortening the path on the way."""
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b, max_size=None):
        """Merge the groups of a and b; refuse if the merged group would exceed max_size."""
        a, b = self.find(a), self.find(b)
        if a == b:
            return True
        if max_size is not None and self.size[a] + self.size[b] > max_size:
            return False  # refuse to chain unrelated photos into one giant group
        self.p[b] = a; self.size[a] += self.size[b]
        return True

def per_class_group_split(df, test_frac, val_frac, seed=SEED):
    """Whole groups go to one split; per class, groups are shuffled and filled to the target image shares."""
    g = (df.groupby("group").agg(label=("label", lambda s: s.value_counts().idxmax()), size=("label", "size"))
         .reset_index())
    rng, assign = np.random.default_rng(seed), {}
    for _, d in g.groupby("label"):
        d = d.iloc[rng.permutation(len(d))]
        total, cum = d["size"].sum(), 0
        for grp, size in zip(d.group, d["size"]):
            assign[grp] = "test" if cum < test_frac * total else ("val" if cum < (test_frac + val_frac) * total else "train")
            cum += size
    return df.group.map(assign).to_numpy()

def split_table(df):
    """Images per class and split, as a table for printing and saving."""
    return (df.pivot_table(index="label", columns="split", values="path", aggfunc="count")
            .reindex(index=range(len(CLASS_NAMES)), columns=["train", "val", "test"]).fillna(0).astype(int)
            .rename(index=dict(enumerate(CLASS_NAMES))))

# %% [markdown]
# ## PlantVillage: profile, group by leaf, split 70 / 15 / 15 per class
# File names carry the camera sequence number (`RS_Erly.B 6330`, `6331`, ...) or a leaf id with day
# (`GHLB Leaf 1 Day 6`); consecutive shots of one leaf are grouped, and rotated/flipped copies are merged by pHash.

# %%
def leaf_group_key(cls, filename):
    """Group key for PlantVillage photos of the same leaf: camera-sequence block or leaf id from the file name."""
    stem = Path(filename).stem.split("___", 1)[-1].strip()
    m = re.match(r"^(.*?)\s+day\s*\d+.*$", stem, re.I)
    if m:  # time series of one leaf
        leaf = re.sub(r"[.]\d+$", "", m.group(1).strip().lower())
        return f"{cls}|{leaf}"
    m = re.match(r"^(.*?)(\d+)(?:\.\d+)?$", stem)
    if m:
        return f"{cls}|{m.group(1).strip().lower()}|{int(m.group(2)) // SEQ_BLOCK}"
    return f"{cls}|{stem.lower()}"

rows = []
for label, (cname, folder) in enumerate(TOMATO_CLASSES.items()):
    for f in sorted((PV_ROOT / folder).iterdir()):
        if f.suffix.lower() in IMG_EXT:
            rows.append(dict(path=str(f), file=f.name, label=label))
pv = pd.DataFrame(rows)
t0 = time.time()
prof, pv_hashes = profile_paths(pv.path.tolist())
pv = pd.concat([pv, prof], axis=1)
ok_mask = pv.ok.to_numpy(bool)
print(f"PlantVillage: profiled {len(pv)} images in {time.time() - t0:.0f}s; corrupt: {(~ok_mask).sum()}")
pv, pv_hashes = pv[ok_mask].reset_index(drop=True), pv_hashes[ok_mask]

dsu = DSU(len(pv))
first_of_key = {}
for i, k in enumerate(leaf_group_key(CLASS_NAMES[l], f) for l, f in zip(pv.label, pv.file)):
    dsu.union(first_of_key.setdefault(k, i), i)
pv_dups = near_duplicate_pairs(pv_hashes, pv_hashes, HASH_MAX_DIST, same=True)
pv_labels = pv.label.to_numpy()
for i, j in pv_dups:
    if pv_labels[i] == pv_labels[j]:
        dsu.union(int(i), int(j), MAX_GROUP_SIZE)
pv["group"] = [f"pv{dsu.find(i)}" for i in range(len(pv))]
pv["split"] = per_class_group_split(pv, PV_TEST_FRAC, PV_VAL_FRAC)
pv["box"], pv["domain"], pv["kind"] = None, "pv", "leaf"
assert (pv.groupby("group").split.nunique() == 1).all()
pv_table = split_table(pv)
print(f"groups: {pv.group.nunique()} | duplicate pairs: {len(pv_dups)}\n{pv_table.to_string()}")
assert (pv_table > 0).all().all(), "every class must appear in train, val and test"
pv[["file", "label", "group", "split"]].to_csv(WORK_DIR / "plantvillage_split_manifest.csv", index=False)

# %% [markdown]
# ## PlantDoc: merge both Kaggle copies, remove PlantVillage look-alikes, split 65 / 10 / 25 per class
# - **Leaf crops** come from the annotated boxes (detection copy).
# - **Full photos** come from the class folders (classification copy), or from a detection image whose tomato boxes
#   all share one label.
# - Copies of the same photo (across or within the two datasets) form one group and stay in one split.

# %%
pd_images = []
if PD_DET_ROOT is not None:
    id_to_label = {i: CLASS_NAMES.index(PLANTDOC_MAP[norm_name(n)]) for i, n in PD_DET_NAMES.items()
                   if norm_name(n) in PLANTDOC_MAP}
    for img_path in sorted((PD_DET_ROOT / "images").rglob("*")):
        if img_path.suffix.lower() not in IMG_EXT:
            continue
        lbl = Path(str(img_path).replace(f"{os.sep}images{os.sep}", f"{os.sep}labels{os.sep}")).with_suffix(".txt")
        if not lbl.exists():
            continue
        boxes = []
        for line in open(lbl).read().splitlines():
            p = line.split()
            if len(p) >= 5 and int(float(p[0])) in id_to_label:
                boxes.append((id_to_label[int(float(p[0]))], tuple(map(float, p[1:5]))))
        if boxes:
            pd_images.append(dict(path=str(img_path), source="det", folder_label=np.nan, yolo=boxes))
if PD_CLS_ROOT is not None:
    for split_dir in sorted(d for d in PD_CLS_ROOT.iterdir() if d.is_dir()):
        for cdir in sorted(split_dir.iterdir()):
            if cdir.is_dir() and norm_name(cdir.name) in PLANTDOC_MAP:
                lab = CLASS_NAMES.index(PLANTDOC_MAP[norm_name(cdir.name)])
                pd_images += [dict(path=str(f), source="cls", folder_label=lab, yolo=[])
                              for f in sorted(cdir.iterdir()) if f.suffix.lower() in IMG_EXT]
pdi = pd.DataFrame(pd_images)
prof, pd_hashes = profile_paths(pdi.path.tolist())
pdi = pd.concat([pdi, prof], axis=1)
ok_mask = pdi.ok.to_numpy(bool)
pdi, pd_hashes = pdi[ok_mask].reset_index(drop=True), pd_hashes[ok_mask]
print(f"PlantDoc tomato images: {len(pdi)} ({dict(Counter(pdi.source))}); unreadable: {(~ok_mask).sum()}")

dsu = DSU(len(pdi))
pd_dups = near_duplicate_pairs(pd_hashes, pd_hashes, HASH_MAX_DIST, same=True)
for i, j in pd_dups:
    dsu.union(int(i), int(j), MAX_GROUP_SIZE)
roots = [dsu.find(i) for i in range(len(pdi))]
first_path = pdi.groupby(pd.Series(roots)).path.min()  # name each photo group by its first file path
pdi["group"] = ["pd:" + first_path[r] for r in roots]
leak_hits = near_duplicate_pairs(pd_hashes, pv_hashes, PLANTDOC_LEAK_DIST)
leaked_groups = set(pdi.group.iloc[np.unique(leak_hits[:, 0])]) if len(leak_hits) else set()
pdi = pdi[~pdi.group.isin(leaked_groups)].reset_index(drop=True)
print(f"duplicate photo pairs across/within PlantDoc copies: {len(pd_dups)} | unique photos: {pdi.group.nunique()} "
      f"| groups dropped as PlantVillage look-alikes: {len(leaked_groups)}")

pd_rows, label_conflicts = [], 0
for g, d in pdi.groupby("group", sort=True):
    det = d[d.source == "det"]
    box_labels = set()
    if len(det):
        r0 = det.iloc[0]  # one detection copy per photo is enough
        W, H = r0.width, r0.height
        for lab, (cx, cy, w, h) in r0.yolo:
            box = (max(0, round((cx - w / 2) * W)), max(0, round((cy - h / 2) * H)),
                   min(W, round((cx + w / 2) * W)), min(H, round((cy + h / 2) * H)))
            box_labels.add(lab)
            if min(box[2] - box[0], box[3] - box[1]) >= MIN_CROP_SIDE:
                pd_rows.append(dict(path=r0.path, box=box, label=lab, kind="crop", group=g, width=W, height=H))
    folder_labels = set(int(x) for x in d.folder_label.dropna())
    if len(folder_labels) > 1:
        label_conflicts += 1; continue
    full_label = next(iter(folder_labels)) if folder_labels else (next(iter(box_labels)) if len(box_labels) == 1 else None)
    if full_label is not None:
        rep = d[d.source == "cls"].iloc[0] if (d.source == "cls").any() else det.iloc[0]
        pd_rows.append(dict(path=rep.path, box=None, label=full_label, kind="full", group=g,
                            width=rep.width, height=rep.height))
pdr = pd.DataFrame(pd_rows)
pd_class_rows = pdr.label.value_counts()
too_small = [CLASS_NAMES[c] for c, n in pd_class_rows.items() if n < MIN_PD_CLASS_ROWS]
pdr = pdr[pdr.label.map(pd_class_rows) >= MIN_PD_CLASS_ROWS].reset_index(drop=True)
print("PlantDoc classes left out (too few samples):", too_small or "none",
      "| PlantDoc has no images for:", [c for i, c in enumerate(CLASS_NAMES) if i not in pd_class_rows.index] or "none")
pdr["domain"] = "pd"
pdr["split"] = per_class_group_split(pdr, PD_TEST_FRAC, PD_VAL_FRAC)
assert (pdr.groupby("group").split.nunique() == 1).all()
print(f"photos with conflicting folder labels (dropped as full images): {label_conflicts}")
for kind in ("crop", "full"):
    print(f"PlantDoc {kind}s:\n{split_table(pdr[pdr.kind == kind]).to_string()}")
pdr.drop(columns=["box"]).assign(box=pdr.box.astype(str)).to_csv(WORK_DIR / "plantdoc_split_manifest.csv", index=False)

# %% [markdown]
# ## Augmentation (training only, generated in memory every step - never saved)
#
# | Real-world condition | Augmentation |
# |---|---|
# | Any angle / orientation | rotation 0-360 deg (reflect border), horizontal + vertical flip, perspective tilt, shear |
# | Distance & framing | random crop keeping 50-100% of the area, small shifts, hidden patches filled from surrounding leaf |
# | Lighting | brightness +/-35%, contrast +/-30%, gamma, soft uneven light (partial shade / sun patch), colour temperature 3500-10000 K |
# | Camera quality | motion / Gaussian / defocus blur, sensor noise, JPEG quality 30-90, downscale->upscale |
# | Colour (kept small) | hue +/-5 only - yellowing and lesion colour are disease symptoms |

# %%
train_tf = A.Compose([
    A.RandomResizedCrop(size=(IMG_SIZE, IMG_SIZE), scale=(0.5, 1.0), ratio=(0.75, 1.333), p=1.0),
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.5),
    A.Rotate(limit=180, border_mode=cv2.BORDER_REFLECT_101, p=0.8),
    A.Perspective(scale=(0.02, 0.08), p=0.3),
    A.Affine(shear=(-8, 8), translate_percent=(-0.05, 0.05), border_mode=cv2.BORDER_REFLECT_101, p=0.3),
    A.OneOf([
        A.RandomBrightnessContrast(brightness_limit=0.35, contrast_limit=0.30, p=1.0),
        A.RandomGamma(gamma_limit=(70, 150), p=1.0),
    ], p=0.8),
    A.OneOf([  # soft uneven light: partial shade / sun patch / light falloff
        A.Illumination(mode="linear", intensity_range=(0.05, 0.2), p=1.0),
        A.Illumination(mode="corner", intensity_range=(0.05, 0.2), p=1.0),
        A.Illumination(mode="gaussian", intensity_range=(0.05, 0.2), p=1.0),
    ], p=0.35),
    A.PlanckianJitter(mode="blackbody", temperature_limit=(3500, 10000), p=0.3),  # golden hour .. deep shade
    A.HueSaturationValue(hue_shift_limit=5, sat_shift_limit=25, val_shift_limit=15, p=0.4),
    A.OneOf([
        A.MotionBlur(blur_limit=(3, 9), p=1.0),
        A.GaussianBlur(blur_limit=(3, 7), p=1.0),
        A.Defocus(radius=(1, 3), p=1.0),
    ], p=0.3),
    A.OneOf([
        A.GaussNoise(std_range=(0.02, 0.08), p=1.0),
        A.ISONoise(p=1.0),
    ], p=0.3),
    A.Downscale(scale_range=(0.4, 0.8), p=0.2),
    A.ImageCompression(quality_range=(30, 90), p=0.4),
    # occlusion filled from surrounding leaf (black squares would look like lesions)
    A.CoarseDropout(num_holes_range=(1, 3), hole_height_range=(0.05, 0.15), hole_width_range=(0.05, 0.15),
                    fill="inpaint_telea", p=0.2),
    A.Normalize(mean=MEAN, std=STD),
    ToTensorV2(),
])
eval_tf = A.Compose([A.Resize(IMG_SIZE, IMG_SIZE), A.Normalize(mean=MEAN, std=STD), ToTensorV2()])

def load_rgb(path, box=None):
    """Decode (large JPEGs at reduced scale, never below DECODE_MIN_SIDE for the region used) and crop."""
    with Image.open(path) as im:
        W, H = im.size
        rw, rh = (box[2] - box[0], box[3] - box[1]) if box is not None else (W, H)
        s = min(1.0, DECODE_MIN_SIDE / max(1, min(rw, rh)))
        if s < 0.5:
            im.draft("RGB", (max(1, math.ceil(W * s)), max(1, math.ceil(H * s))))
        im = im.convert("RGB")
        if box is not None:
            fx, fy = im.size[0] / W, im.size[1] / H
            im = im.crop((box[0] * fx, box[1] * fy, box[2] * fx, box[3] * fy))
        return np.array(im)

class LeafDataset(Dataset):
    """Reads the original file on every access; optional per-item crop box and deterministic corruption."""
    def __init__(self, paths, labels, transform, boxes=None, corrupt=None):
        self.paths, self.labels = list(paths), np.asarray(labels, dtype=np.int64)
        self.boxes = list(boxes) if boxes is not None else [None] * len(self.paths)
        self.transform, self.corrupt = transform, corrupt
    def __len__(self):
        return len(self.paths)
    def load(self, i):
        """Read image i as an RGB array (cropped to its box and corrupted for robustness tests if configured)."""
        img = load_rgb(self.paths[i], self.boxes[i])
        return self.corrupt(img, i) if self.corrupt is not None else img
    def __getitem__(self, i):
        """Return (transformed image tensor, label) for image i."""
        return self.transform(image=self.load(i))["image"], self.labels[i]

def seed_worker(_):
    """DataLoader worker init: give every worker its own random seeds, including the albumentations RNG."""
    info = torch.utils.data.get_worker_info()
    seed = info.seed % 2**32
    random.seed(seed); np.random.seed(seed)
    if hasattr(info.dataset.transform, "set_random_seed"):
        info.dataset.transform.set_random_seed(seed)  # albumentations keeps its own RNG; give each worker its own

def make_loader(ds, sampler=None):
    """Build a DataLoader; training loaders shuffle or sample and drop the last incomplete batch."""
    train = sampler is not None
    return DataLoader(ds, batch_size=BATCH, sampler=sampler, shuffle=False, drop_last=train, num_workers=NUM_WORKERS,
                      pin_memory=USE_AMP, worker_init_fn=seed_worker, persistent_workers=train and NUM_WORKERS > 0)

def frame_dataset(df, transform, label_col="y"):
    """LeafDataset from a manifest DataFrame (path, optional crop box and a label column)."""
    return LeafDataset(df.path, df[label_col], transform, boxes=df.box.tolist())

# Preview grid: PlantVillage and PlantDoc training images with augmentation (for the report; not used for training)
prev_df = pd.concat([pv[pv.split == "train"].sample(3, random_state=SEED),
                     pdr[pdr.split == "train"].sample(min(3, (pdr.split == "train").sum()), random_state=SEED)])
preview = frame_dataset(prev_df.assign(y=prev_df.label), train_tf)
fig, axes = plt.subplots(len(preview), 7, figsize=(14, 2.1 * len(preview)))
for r in range(len(preview)):
    axes[r, 0].imshow(cv2.resize(preview.load(r), (IMG_SIZE, IMG_SIZE)))
    axes[r, 0].set_title(f"{prev_df.domain.iloc[r]}: {CLASS_NAMES[prev_df.label.iloc[r]]}", fontsize=7)
    for c in range(1, 7):
        x = preview[r][0].permute(1, 2, 0).numpy() * np.array(STD) + np.array(MEAN)
        axes[r, c].imshow(np.clip(x, 0, 1))
for a in axes.flat:
    a.axis("off")
plt.tight_layout(); plt.savefig(WORK_DIR / "augmentation_preview.png", dpi=110); plt.show()

# %% [markdown]
# ## Models and training loop (EMA weights, cosine schedule)
# Balanced sampling as in v2: each epoch draws `EPOCH_SAMPLES` images, `PD_SHARE` of them from PlantDoc, classes
# balanced within each domain. The EMA copy is validated every epoch; the best EMA checkpoint (mean of
# PlantVillage-val and PlantDoc-val macro F1) is kept.

# %%
def build_model(arch, n_classes):
    """Create an ImageNet-pretrained backbone (or the paper CNN) with a new output layer of n_classes."""
    if arch == "mobilenet_v3_small":
        m = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
        m.classifier[3] = nn.Linear(m.classifier[3].in_features, n_classes)
    elif arch == "efficientnet_b0":
        m = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, n_classes)
    else:
        raise ValueError(arch)
    return m

def balanced_weights(df, pd_share):
    """Per-image sampling weights: PlantDoc gets pd_share of each epoch and classes are balanced within each source."""
    w = np.zeros(len(df))
    for dom, share in {"pv": 1 - pd_share, "pd": pd_share}.items():
        m = (df.domain == dom).to_numpy()
        if share <= 0 or not m.any():
            continue
        counts = df.y[m].value_counts()
        w[m] = share / (len(counts) * df.y[m].map(counts).to_numpy())
    return w / w.sum()

@torch.no_grad()
def predict(model, loader, tta=False):
    """Return softmax probabilities and true labels for every image in the loader."""
    model.eval(); probs, ys = [], []
    for x, y in loader:
        x = x.to(DEVICE, non_blocking=True)
        with torch.autocast(device_type=DEVICE.type, dtype=torch.float16, enabled=USE_AMP):
            p = torch.softmax(model(x).float(), 1)
            if tta:
                p = (p + torch.softmax(model(torch.flip(x, dims=[3])).float(), 1)) / 2
        probs.append(p.float().cpu().numpy()); ys.append(y.numpy())
    return np.concatenate(probs), np.concatenate(ys)

def macro_f1(y, pred):
    """Macro F1 over the classes present in y (field sets have no target-spot / spider-mite images)."""
    return f1_score(y, pred, average="macro", labels=np.unique(y), zero_division=0)

def train_model(run, arch, train_df, val_frames, pd_share, seed, epochs=EPOCHS, lr=1e-3):
    """Train one model and keep the checkpoint with the best validation score (stops early when it stops improving)."""
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    tr = train_df.assign(y=train_df.label)
    model = build_model(arch, len(CLASS_NAMES)).to(DEVICE)
    ema = torch.optim.swa_utils.AveragedModel(
        model, multi_avg_fn=torch.optim.swa_utils.get_ema_multi_avg_fn(EMA_DECAY), use_buffers=True)
    sampler = WeightedRandomSampler(torch.as_tensor(balanced_weights(tr, pd_share), dtype=torch.double),
                                    num_samples=EPOCH_SAMPLES, replacement=True,
                                    generator=torch.Generator().manual_seed(seed))
    train_dl = make_loader(frame_dataset(tr, train_tf), sampler)
    val_dls = {k: make_loader(frame_dataset(v.assign(y=v.label), eval_tf)) for k, v in val_frames.items()}
    loss_fn = nn.CrossEntropyLoss(label_smoothing=0.05)  # classes already balanced by the sampler
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    total_steps, warm = epochs * len(train_dl), WARMUP_EPOCHS * len(train_dl)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / warm if s < warm else
                                              0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, total_steps - warm))))
    scaler = torch.amp.GradScaler("cuda", enabled=USE_AMP)
    ckpt, best, bad, history = WORK_DIR / f"{run}_best.pt", -1.0, 0, []
    for epoch in range(1, epochs + 1):
        t0 = time.time()
        model.train(); total, seen = 0.0, 0
        for x, y in train_dl:
            x, y = x.to(DEVICE, non_blocking=True), y.to(DEVICE, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=DEVICE.type, dtype=torch.float16, enabled=USE_AMP):
                loss = loss_fn(model(x), y)
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); sched.step()
            ema.update_parameters(model)
            total += loss.item() * len(y); seen += len(y)
        row = dict(epoch=epoch, train_loss=total / max(seen, 1), lr=sched.get_last_lr()[0])
        for k, dl in val_dls.items():
            p, yv = predict(ema.module, dl)
            row[f"val_{k}_macro_f1"] = macro_f1(yv, p.argmax(1))
        row["val_score"] = float(np.mean([row[f"val_{k}_macro_f1"] for k in val_dls]))
        row["seconds"] = round(time.time() - t0, 1)
        history.append(row)
        print(f"[{run}] " + " ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in row.items()))
        if row["val_score"] > best:
            best, bad = row["val_score"], 0
            torch.save({"model_state_dict": ema.module.state_dict(), "arch": arch, "class_names": CLASS_NAMES,
                        "img_size": IMG_SIZE, "mean": list(MEAN), "std": list(STD), "epoch": epoch, "seed": seed,
                        "val_score": best, "weights": "EMA", "train_data": "plantvillage+plantdoc"}, ckpt)
        else:
            bad += 1
            if bad >= PATIENCE:
                print(f"[{run}] early stop at epoch {epoch}"); break
    pd.DataFrame(history).to_csv(WORK_DIR / f"{run}_history.csv", index=False)
    final = build_model(arch, len(CLASS_NAMES)).to(DEVICE)
    final.load_state_dict(torch.load(ckpt, map_location=DEVICE, weights_only=True)["model_state_dict"])
    print(f"[{run}] best EMA val score = {best:.4f} -> {ckpt.name}")
    return final.eval()

# %% [markdown]
# ## Train: EfficientNet-B0 and MobileNetV3-Small, two seeds each

# %%
pv_tr, pv_va, pv_te = (pv[pv.split == s] for s in ("train", "val", "test"))
pd_tr, pd_va, pd_te = (pdr[pdr.split == s] for s in ("train", "val", "test"))
both_train = pd.concat([pv_tr, pd_tr], ignore_index=True)
VAL_BOTH = {"pv": pv_va, "pd": pd_va}

ARCHS = {"effb0": "efficientnet_b0", "mnv3s": "mobilenet_v3_small"}
SEEDS_PER_ARCH = {"effb0": SEEDS, "mnv3s": SEEDS[:1]}  # MobileNetV3-Small is the small fallback; one seed is enough
trained = {}
for short, arch in ARCHS.items():
    for seed in SEEDS_PER_ARCH[short]:
        run = f"{short}_seed{seed}"
        t0 = time.time()
        trained[run] = train_model(run, arch, both_train, VAL_BOTH, PD_SHARE, seed)
        print(f"[{run}] trained in {(time.time() - t0) / 60:.1f} min\n")

# %% [markdown]
# ## System selection on validation only
# Systems: each single model, and each architecture's two-seed average (an ensemble would double Pi inference time,
# so it is reported for information). The recommended deployable system is the **single model** with the best
# validation score.

# %%
def run_probs(df, tta=False):
    """Probabilities of every trained model on one manifest, optionally with horizontal-flip averaging."""
    dl = make_loader(frame_dataset(df.assign(y=df.label), eval_tf))
    return {run: predict(m, dl, tta=tta)[0] for run, m in trained.items()}, df.label.to_numpy()

def system_probs(P):
    """Add multi-seed ensembles (averaged probabilities) to the per-model probabilities."""
    out = dict(P)
    for short in ARCHS:
        runs = [r for r in P if r.startswith(short + "_")]
        if len(runs) > 1:
            out[f"{short}_{len(runs)}seed_ensemble"] = np.mean([P[r] for r in runs], axis=0)
    return out

VAL_PROBS = {k: run_probs(v) for k, v in VAL_BOTH.items()}
val_rows = {}
for s in system_probs(VAL_PROBS["pv"][0]):
    f1s = {k: macro_f1(y, system_probs(P)[s].argmax(1)) for k, (P, y) in VAL_PROBS.items()}
    val_rows[s] = dict(pv_val_macro_f1=f1s["pv"], pd_val_macro_f1=f1s["pd"], val_score=float(np.mean(list(f1s.values()))))
val_scores = pd.DataFrame(val_rows).T
RECOMMENDED = val_scores.loc[list(trained)].val_score.idxmax()
print(val_scores.round(4).to_string()); print("recommended single model (by validation):", RECOMMENDED)

# %% [markdown]
# ## Test results (PlantVillage test + untouched PlantDoc test - identical split to v2)

# %%
def multiclass_metrics(y, pred, names=CLASS_NAMES):
    """Accuracy, macro F1, balanced accuracy, missed-disease rate, per-class report and confusion matrix."""
    k = len(names)
    y, pred = np.asarray(y), np.asarray(pred)
    diseased = y > 0
    first5 = y < 5  # the original v3 classes: comparable subset (a prediction of a new class counts as wrong)
    return dict(
        n=int(len(y)),
        classes_present=[names[c] for c in np.unique(y)],
        accuracy=float(accuracy_score(y, pred)),
        macro_f1=float(macro_f1(y, pred)),
        accuracy_original5=float(accuracy_score(y[first5], pred[first5])) if first5.any() else float("nan"),
        macro_f1_original5=float(f1_score(y[first5], pred[first5], average="macro", labels=np.unique(y[first5]),
                                          zero_division=0)) if first5.any() else float("nan"),
        balanced_accuracy=float(balanced_accuracy_score(y, pred)) if len(np.unique(y)) > 1 else float("nan"),
        missed_disease_rate=float(np.mean(pred[diseased] == 0)) if diseased.any() else float("nan"),
        per_class=classification_report(y, pred, labels=list(range(k)), target_names=names, output_dict=True, zero_division=0),
        confusion_matrix=confusion_matrix(y, pred, labels=list(range(k))).tolist(),
    )

def plot_cm(cm, title, path):
    """Save a confusion-matrix image with the count written in each cell."""
    cm = np.array(cm)
    k = len(CLASS_NAMES)
    fig, ax = plt.subplots(figsize=(8, 6.5))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(k), CLASS_NAMES, rotation=45, ha="right", fontsize=7); ax.set_yticks(range(k), CLASS_NAMES, fontsize=7)
    for (r, c), v in np.ndenumerate(cm):
        ax.text(c, r, v, ha="center", va="center", fontsize=8, color="white" if v > cm.max() / 2 else "black")
    ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(title, fontsize=9)
    plt.tight_layout(); plt.savefig(path, dpi=110); plt.close(fig)

TEST_SETS = {"plantvillage_test": pv_te, "plantdoc_test_leaf_crops": pd_te[pd_te.kind == "crop"],
             "plantdoc_test_full_images": pd_te[pd_te.kind == "full"]}
RESULTS = {"recommended_system": RECOMMENDED, "validation": val_scores.to_dict(orient="index"), "sets": {}}
for set_name, df in TEST_SETS.items():
    if len(df) == 0:
        continue
    P, y = run_probs(df)
    res = {s: multiclass_metrics(y, p.argmax(1)) for s, p in system_probs(P).items()}
    P_tta, _ = run_probs(df, tta=True)
    res[f"{RECOMMENDED}+flipTTA"] = multiclass_metrics(y, P_tta[RECOMMENDED].argmax(1))
    RESULTS["sets"][set_name] = res
    plot_cm(res[RECOMMENDED]["confusion_matrix"], f"{RECOMMENDED} - {set_name}", WORK_DIR / f"cm_{set_name}_{RECOMMENDED}.png")

summary = pd.DataFrame([dict(eval_set=s, system=k, n=v["n"], accuracy=v["accuracy"], macro_f1=v["macro_f1"],
                             balanced_accuracy=v["balanced_accuracy"], missed_disease_rate=v["missed_disease_rate"],
                             accuracy_original5=v["accuracy_original5"], macro_f1_original5=v["macro_f1_original5"])
                        for s, r in RESULTS["sets"].items() for k, v in r.items()])
summary.to_csv(WORK_DIR / "results_summary.csv", index=False)
pd.set_option("display.width", 200)
print(summary.round(4).to_string(index=False))
for set_name, r in RESULTS["sets"].items():
    pc = r[RECOMMENDED]["per_class"]
    print(f"{RECOMMENDED} per-class recall on {set_name}:",
          {c: (round(pc[c]["recall"], 3), int(pc[c]["support"])) for c in CLASS_NAMES if pc[c]["support"] > 0})

# %% [markdown]
# ## Robustness of the recommended model - angle, lighting and camera quality

# %%
def _rotate_any(deg):
    """Robustness condition: rotate by deg degrees with reflected borders."""
    def f(img, i):
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D((w / 2, h / 2), deg, 1.0)
        return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT_101)
    return f

def _jpeg(q):
    """Robustness condition: re-encode as JPEG at quality q."""
    def f(img, i):
        ok, buf = cv2.imencode(".jpg", cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, q])
        return cv2.cvtColor(cv2.imdecode(buf, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    return f

def _half_shadow(img, i):
    """Robustness condition: darken the left half of the image to 45% (a hard shadow)."""
    out = img.astype(np.float32); out[:, : img.shape[1] // 2] *= 0.45
    return out.clip(0, 255).astype(np.uint8)

def _motion(k):
    """Robustness condition: horizontal motion blur with a k-pixel kernel."""
    kern = np.zeros((k, k), np.float32); kern[k // 2, :] = 1.0 / k
    return lambda img, i: cv2.filter2D(img, -1, kern)

def _noise(std):
    """Robustness condition: Gaussian noise (std as a fraction of 255), seeded per image."""
    return lambda img, i: (img + np.random.default_rng(i).normal(0, std * 255, img.shape)).clip(0, 255).astype(np.uint8)

def _downscale(f):
    """Robustness condition: shrink by factor f and scale back up (low-resolution camera)."""
    def g(img, i):
        h, w = img.shape[:2]
        small = cv2.resize(img, (max(1, int(w * f)), max(1, int(h * f))), interpolation=cv2.INTER_AREA)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    return g

CONDITIONS = {
    "clean": None,
    "rotate_90": lambda img, i: np.ascontiguousarray(np.rot90(img, 1)),
    "rotate_180": lambda img, i: np.ascontiguousarray(np.rot90(img, 2)),
    "rotate_45": _rotate_any(45),
    "brightness_x0.5": lambda img, i: (img * 0.5).astype(np.uint8),
    "brightness_x1.6": lambda img, i: (img * 1.6).clip(0, 255).astype(np.uint8),
    "half_shadow": _half_shadow,
    "gaussian_blur_s2": lambda img, i: cv2.GaussianBlur(img, (0, 0), 2),
    "motion_blur_9": _motion(9),
    "noise_std0.06": _noise(0.06),
    "jpeg_q30": _jpeg(30),
    "downscale_0.35": _downscale(0.35),
}

robust_rows = []
best_model = trained[RECOMMENDED]
for set_name in ("plantvillage_test", "plantdoc_test_leaf_crops", "plantdoc_test_full_images"):
    df = TEST_SETS[set_name]
    if len(df) == 0:
        continue
    for cond, fn in CONDITIONS.items():
        ds = LeafDataset(df.path, df.label, eval_tf, boxes=df.box.tolist(), corrupt=fn)
        p, y = predict(best_model, make_loader(ds))
        m = multiclass_metrics(y, p.argmax(1))
        robust_rows.append(dict(eval_set=set_name, condition=cond, macro_f1=m["macro_f1"], accuracy=m["accuracy"],
                                missed_disease_rate=m["missed_disease_rate"]))
robust = pd.DataFrame(robust_rows)
robust.to_csv(WORK_DIR / "robustness.csv", index=False)
print(robust.pivot(index="condition", columns="eval_set", values="macro_f1").reindex(list(CONDITIONS)).round(4).to_string())

# %% [markdown]
# ## Deployment footprint - size, compute, CPU latency, RAM, and the cost of adding classes / crops
# Measured with PyTorch on Kaggle's x86 CPU (4 threads) - an indication only; the Raspberry Pi 5 numbers must be
# measured on the Pi after ONNX export. RAM is measured in a fresh process (peak resident memory) so it is not mixed
# up with this notebook's training memory. INT8 size is an estimate (weights / 4) until real INT8 export.

# %%
import textwrap
from torch.utils.flop_counter import FlopCounterMode

HEAD_ATTR = {"efficientnet_b0": "classifier[1]", "mobilenet_v3_small": "classifier[3]"}
EXTRA_CROPS = 13  # PlantVillage covers 14 crops; tomato is done

def rss_probe(arch, ckpt, n_classes):
    """Current resident memory (VmRSS) after importing PyTorch, after loading the model, and the peak during
    inference (VmHWM after resetting the peak counter), in a fresh CPU-only process."""
    code = textwrap.dedent(f"""
        import torch
        from torch import nn
        from torchvision import models
        torch.set_num_threads(4)
        def status(key):
            for line in open("/proc/self/status"):
                if line.startswith(key):
                    return int(line.split()[1]) / 1024
        base = status("VmRSS:")
        m = models.{arch}(weights=None)
        m.{HEAD_ATTR[arch]} = nn.Linear(m.{HEAD_ATTR[arch]}.in_features, {n_classes})
        m.load_state_dict(torch.load(r"{ckpt}", map_location="cpu", weights_only=True)["model_state_dict"])
        m.eval(); loaded = status("VmRSS:")
        try:
            open("/proc/self/clear_refs", "w").write("5")  # reset the peak counter
            peak_key = "VmHWM:"
        except OSError:
            peak_key = "VmRSS:"
        with torch.no_grad():
            for _ in range(10):
                m(torch.randn(1, 3, {IMG_SIZE}, {IMG_SIZE}))
        print(base, loaded, max(status(peak_key), status("VmRSS:")))
    """)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=600, env=env)
    base, loaded, peak = map(float, out.stdout.split()[-3:])
    return base, loaded, peak

foot_rows = []
for short, arch in ARCHS.items():
    run = f"{short}_seed{SEEDS_PER_ARCH[short][0]}"
    ckpt = WORK_DIR / f"{run}_best.pt"
    m = build_model(arch, len(CLASS_NAMES)).eval().cpu()
    m.load_state_dict(torch.load(ckpt, map_location="cpu", weights_only=True)["model_state_dict"])
    params = sum(p.numel() for p in m.parameters())
    head = eval(f"m.{HEAD_ATTR[arch]}")
    x = torch.randn(1, 3, IMG_SIZE, IMG_SIZE)
    with torch.no_grad(), FlopCounterMode(display=False) as fc:
        m(x)
    torch.set_num_threads(4)
    with torch.no_grad():
        for _ in range(5):
            m(x)
        times = []
        for _ in range(3 if SMOKE else 30):
            t0 = time.perf_counter(); m(x); times.append(time.perf_counter() - t0)
    base, loaded, peak = rss_probe(arch, ckpt, len(CLASS_NAMES))
    foot_rows.append(dict(
        model=run, architecture=arch, classes=len(CLASS_NAMES), parameters_M=params / 1e6,
        gflops_per_image=fc.get_total_flops() / 1e9,
        weights_fp32_MB=params * 4 / 1e6, weights_fp16_MB=params * 2 / 1e6, weights_int8_MB_est=params / 1e6,
        checkpoint_file_MB=ckpt.stat().st_size / 1e6,
        cpu_latency_ms_median_kaggle=float(np.median(times) * 1000),
        ram_pytorch_runtime_MB=base, ram_after_model_load_MB=loaded, ram_peak_inference_MB=peak,
        ram_model_plus_inference_MB=peak - base,
        head_params_per_extra_class=head.in_features + 1,
        bytes_per_extra_class_fp32=(head.in_features + 1) * 4))
foot = pd.DataFrame(foot_rows)
foot.to_csv(WORK_DIR / "footprint.csv", index=False)
print(foot.round(3).T.to_string())

proj_rows = []
for r in foot_rows:
    per_class_MB = r["bytes_per_extra_class_fp32"] / 1e6
    proj_rows += [
        dict(model=r["model"], scenario="now: tomato only (10 classes)", models_on_disk=1,
             fp32_MB=r["weights_fp32_MB"], int8_MB_est=r["weights_int8_MB_est"],
             note="measured"),
        dict(model=r["model"], scenario="one model, all 14 PlantVillage crops (38 classes)", models_on_disk=1,
             fp32_MB=r["weights_fp32_MB"] + 28 * per_class_MB, int8_MB_est=r["weights_int8_MB_est"] + 28 * per_class_MB / 4,
             note="same latency and RAM; only the last layer grows"),
        dict(model=r["model"], scenario=f"one model per crop ({EXTRA_CROPS + 1} crops), loaded on demand",
             models_on_disk=EXTRA_CROPS + 1, fp32_MB=(EXTRA_CROPS + 1) * r["weights_fp32_MB"],
             int8_MB_est=(EXTRA_CROPS + 1) * r["weights_int8_MB_est"],
             note="RAM stays at one model if only the selected crop's model is loaded"),
    ]
proj = pd.DataFrame(proj_rows)
proj.to_csv(WORK_DIR / "footprint_projection.csv", index=False)
print(proj.round(2).to_string(index=False))
RESULTS["footprint"] = foot.to_dict(orient="records")
RESULTS["footprint_projection"] = proj.to_dict(orient="records")

# %% [markdown]
# ## Save everything needed for the later ONNX / Raspberry Pi step

# %%
save_json({"classes": CLASS_NAMES}, "labels.json")
save_json({"img_size": IMG_SIZE, "resize": "direct resize to img_size x img_size (no aspect-ratio preservation)",
           "color_order": "RGB", "scale": "pixel / 255", "mean": MEAN, "std": STD, "layout": "NCHW float32",
           "recommended_system": RECOMMENDED, "recommended_checkpoint": f"{RECOMMENDED}_best.pt",
           "weights": "EMA"}, "preprocess.json")
RESULTS["config"] = dict(seeds=SEEDS, img_size=IMG_SIZE, epochs=EPOCHS, warmup_epochs=WARMUP_EPOCHS, ema_decay=EMA_DECAY,
                         epoch_samples=EPOCH_SAMPLES, batch=BATCH, patience=PATIENCE, pd_share=PD_SHARE,
                         torch=torch.__version__, albumentations=A.__version__,
                         plantvillage_split=pv_table.to_dict(),
                         plantdoc_crop_split=split_table(pdr[pdr.kind == "crop"]).to_dict(),
                         plantdoc_full_split=split_table(pdr[pdr.kind == "full"]).to_dict(),
                         plantdoc_classes_left_out=too_small, classes=CLASS_NAMES)
save_json(RESULTS, "results.json")
print(sorted(p.name for p in WORK_DIR.iterdir()))
