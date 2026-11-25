# %% [markdown]
# # KrishiRakshak PS1 - Tomato disease training v2: lab + field images (Kaggle GPU)
#
# Version 1 trained on PlantVillage only: ~97% on PlantVillage test but only ~31-42% on PlantDoc field photos.
# Version 2 adds **PlantDoc's training share** so the model learns field conditions, while a held-out PlantDoc test
# share is never used for training, checkpoint selection or threshold tuning.
#
# | System | What it is |
# |---|---|
# | `baseline_pv_only` | MobileNetV3-Small trained on PlantVillage only (same recipe as v1, for a fair before/after) |
# | `direct_mnv3s` | MobileNetV3-Small, 5-class, PlantVillage + PlantDoc |
# | `direct_mnv3l` | MobileNetV3-Large, 5-class, PlantVillage + PlantDoc |
# | `direct_effb0` | EfficientNet-B0, 5-class, PlantVillage + PlantDoc |
# | `cascade_mnv3s` | Healthy/Diseased gate -> 4-disease model, both MobileNetV3-Small, PlantVillage + PlantDoc |
#
# Rules (see `docs/RESULTS.md, "Test data rules"`): online augmentation only (never saved); splits made before augmentation and grouped
# so the same leaf/photo never crosses splits; the two PlantDoc copies on Kaggle are merged by perceptual hash so a
# photo cannot be in train via one copy and in test via the other; PlantDoc images resembling PlantVillage are dropped.
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
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "disease_outputs_v2"
WORK_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE = 224
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
BATCH = 16 if SMOKE else 64
NUM_WORKERS = 2 if SMOKE else 4
EPOCHS = 1 if SMOKE else 25
EPOCH_SAMPLES = 160 if SMOKE else 8000   # images drawn per epoch by the balanced sampler
PATIENCE = 7
PD_SHARE = 0.5                  # fraction of each training batch drawn from PlantDoc (field) images
PV_TEST_FRAC, PV_VAL_FRAC = 0.15, 0.15
PD_TEST_FRAC, PD_VAL_FRAC = 0.25, 0.10
TARGET_DISEASED_RECALL = 0.98   # gate threshold tuned on validation to miss at most ~2% of diseased leaves
SEQ_BLOCK = 20                  # PlantVillage camera-sequence numbers grouped in blocks of 20 (4-7 shots per leaf)
HASH_MAX_DIST = 16              # pHash bits: same photo (rotation/flip invariant); real duplicates <= 6, different leaves >= 92
MAX_GROUP_SIZE = 60             # duplicate merging never grows a group beyond this
PLANTDOC_LEAK_DIST = 20         # PlantDoc images this close to any PlantVillage image are dropped entirely
MIN_CROP_SIDE = 32              # PlantDoc leaf boxes smaller than this (px) are skipped
DECODE_MIN_SIDE = 336           # large JPEGs are decoded at reduced scale but never below this many px for the region used

# Order matters: index 0 must be healthy (the gate and the cascade rely on it).
TOMATO_CLASSES = {
    "healthy": "Tomato___healthy",
    "early_blight": "Tomato___Early_blight",
    "late_blight": "Tomato___Late_blight",
    "leaf_mold": "Tomato___Leaf_Mold",
    "septoria_leaf_spot": "Tomato___Septoria_leaf_spot",
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
pdi["group"] = [f"pd{dsu.find(i)}" for i in range(len(pdi))]
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
# ## Models and training loop
# Balanced sampling: each epoch draws `EPOCH_SAMPLES` images, `PD_SHARE` of them from PlantDoc, classes balanced
# within each domain. Checkpoints are selected by the **mean of PlantVillage-val and PlantDoc-val macro F1**.

# %%
def build_model(arch, n_classes):
    """Create an ImageNet-pretrained backbone (or the paper CNN) with a new output layer of n_classes."""
    if arch == "mobilenet_v3_small":
        m = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
        m.classifier[3] = nn.Linear(m.classifier[3].in_features, n_classes)
    elif arch == "mobilenet_v3_large":
        m = models.mobilenet_v3_large(weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2)
        m.classifier[3] = nn.Linear(m.classifier[3].in_features, n_classes)
    elif arch == "efficientnet_b0":
        m = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, n_classes)
    else:
        raise ValueError(arch)
    return m

for arch in ("mobilenet_v3_small", "mobilenet_v3_large", "efficientnet_b0"):
    print(f"{arch:20s} {sum(p.numel() for p in build_model(arch, 5).parameters()) / 1e6:.2f}M parameters (5-class head)")

def task_frame(df, task):
    """Relabel a manifest for one task: 5-class direct, Healthy/Diseased gate, or 4-disease stage 2."""
    if task == "direct":
        return df.assign(y=df.label)
    if task == "gate":
        return df.assign(y=(df.label > 0).astype(int))
    if task == "stage2":
        d = df[df.label > 0]
        return d.assign(y=d.label - 1)
    raise ValueError(task)

def balanced_weights(df, pd_share):
    """Per-image sampling weights: PlantDoc gets pd_share of each epoch and classes are balanced within each source."""
    w = np.zeros(len(df))
    shares = {"pv": 1 - pd_share, "pd": pd_share}
    for dom, share in shares.items():
        m = (df.domain == dom).to_numpy()
        if share <= 0 or not m.any():
            continue
        counts = df.y[m].value_counts()
        w[m] = share / (len(counts) * df.y[m].map(counts).to_numpy())
    return w / w.sum()

@torch.no_grad()
def predict(model, loader):
    """Return softmax probabilities and true labels for every image in the loader."""
    model.eval(); probs, ys = [], []
    for x, y in loader:
        with torch.autocast(device_type=DEVICE.type, dtype=torch.float16, enabled=USE_AMP):
            logits = model(x.to(DEVICE, non_blocking=True))
        probs.append(torch.softmax(logits.float(), 1).cpu().numpy()); ys.append(y.numpy())
    return np.concatenate(probs), np.concatenate(ys)

def macro_f1(y, p, n):
    """Macro F1 score of the predictions."""
    return f1_score(y, p.argmax(1), average="macro", labels=range(n), zero_division=0)

def train_model(run, arch, task, train_df, val_frames, pd_share, epochs=EPOCHS, lr=1e-3):
    """Train one model and keep the checkpoint with the best validation score (stops early when it stops improving)."""
    names = {"direct": CLASS_NAMES, "gate": GATE_NAMES, "stage2": DISEASE_NAMES}[task]
    n = len(names)
    tr = task_frame(train_df, task)
    model = build_model(arch, n).to(DEVICE)
    sampler = WeightedRandomSampler(torch.as_tensor(balanced_weights(tr, pd_share), dtype=torch.double),
                                    num_samples=EPOCH_SAMPLES, replacement=True,
                                    generator=torch.Generator().manual_seed(SEED))
    train_dl = make_loader(frame_dataset(tr, train_tf), sampler)
    val_dls = {k: make_loader(frame_dataset(task_frame(v, task), eval_tf)) for k, v in val_frames.items()}
    loss_fn = nn.CrossEntropyLoss(label_smoothing=0.05)  # classes already balanced by the sampler
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=epochs * len(train_dl), pct_start=0.15)
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
            total += loss.item() * len(y); seen += len(y)
        row = dict(epoch=epoch, train_loss=total / max(seen, 1))
        for k, dl in val_dls.items():
            p, yv = predict(model, dl)
            row[f"val_{k}_macro_f1"] = macro_f1(yv, p, n)
        row["val_score"] = float(np.mean([row[f"val_{k}_macro_f1"] for k in val_dls]))
        row["seconds"] = round(time.time() - t0, 1)
        history.append(row)
        print(f"[{run}] " + " ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in row.items()))
        if row["val_score"] > best:
            best, bad = row["val_score"], 0
            torch.save({"model_state_dict": model.state_dict(), "arch": arch, "class_names": list(names),
                        "img_size": IMG_SIZE, "mean": list(MEAN), "std": list(STD), "epoch": epoch,
                        "val_score": best, "train_data": "plantvillage" + ("+plantdoc" if pd_share > 0 else "")}, ckpt)
        else:
            bad += 1
            if bad >= PATIENCE:
                print(f"[{run}] early stop at epoch {epoch}"); break
    pd.DataFrame(history).to_csv(WORK_DIR / f"{run}_history.csv", index=False)
    model.load_state_dict(torch.load(ckpt, map_location=DEVICE, weights_only=True)["model_state_dict"])
    print(f"[{run}] best val score = {best:.4f} -> {ckpt.name}")
    return model.eval()

# %% [markdown]
# ## Train all models

# %%
pv_tr, pv_va, pv_te = (pv[pv.split == s] for s in ("train", "val", "test"))
pd_tr, pd_va, pd_te = (pdr[pdr.split == s] for s in ("train", "val", "test"))
both_train = pd.concat([pv_tr, pd_tr], ignore_index=True)
VAL_BOTH = {"pv": pv_va, "pd": pd_va}

RUNS = [  # name, architecture, task, training frame, validation frames, PlantDoc share
    ("baseline_pv_only", "mobilenet_v3_small", "direct", pv_tr, {"pv": pv_va}, 0.0),
    ("direct_mnv3s", "mobilenet_v3_small", "direct", both_train, VAL_BOTH, PD_SHARE),
    ("direct_mnv3l", "mobilenet_v3_large", "direct", both_train, VAL_BOTH, PD_SHARE),
    ("direct_effb0", "efficientnet_b0", "direct", both_train, VAL_BOTH, PD_SHARE),
    ("gate_mnv3s", "mobilenet_v3_small", "gate", both_train, VAL_BOTH, PD_SHARE),
    ("stage2_mnv3s", "mobilenet_v3_small", "stage2", both_train, VAL_BOTH, PD_SHARE),
]
trained = {}
for run, arch, task, tr_df, va, share in RUNS:
    t0 = time.time()
    trained[run] = train_model(run, arch, task, tr_df, va, share)
    print(f"[{run}] trained in {(time.time() - t0) / 60:.1f} min\n")

# %% [markdown]
# ## Gate threshold (validation only) and system selection (validation only)

# %%
def predict_all(df):
    """Probabilities of every trained model on one evaluation set."""
    dl = make_loader(frame_dataset(df.assign(y=df.label), eval_tf))
    return {run: predict(m, dl)[0] for run, m in trained.items()}, df.label.to_numpy()

def cascade_pred(p_gate, p_stage2, thr):
    """Two-stage prediction: healthy if P(healthy) > thr, otherwise the stage-2 disease (class index + 1)."""
    return np.where(p_gate[:, 0] > thr, 0, 1 + p_stage2.argmax(1))

SYSTEMS = ["baseline_pv_only", "direct_mnv3s", "direct_mnv3l", "direct_effb0", "cascade_mnv3s"]

def system_preds(P, thr):
    """Predicted class per compared system (direct models and the two-stage cascade)."""
    out = {s: P[s].argmax(1) for s in SYSTEMS if not s.startswith("cascade")}
    out["cascade_mnv3s"] = cascade_pred(P["gate_mnv3s"], P["stage2_mnv3s"], thr)
    return out

VAL_PRED = {k: predict_all(v) for k, v in VAL_BOTH.items()}
p_h_dis = np.concatenate([P["gate_mnv3s"][y > 0, 0] for P, y in VAL_PRED.values()])
GATE_THRESHOLD = float(min(0.999, max(0.5, np.quantile(p_h_dis, TARGET_DISEASED_RECALL)))) if len(p_h_dis) else 0.5
print("gate healthy threshold:", GATE_THRESHOLD)

val_scores = {}
for s in SYSTEMS:
    f1s = {k: f1_score(y, system_preds(P, GATE_THRESHOLD)[s], average="macro", labels=range(5), zero_division=0)
           for k, (P, y) in VAL_PRED.items()}
    val_scores[s] = dict(pv_val_macro_f1=f1s["pv"], pd_val_macro_f1=f1s["pd"], val_score=float(np.mean(list(f1s.values()))))
val_scores = pd.DataFrame(val_scores).T
RECOMMENDED = val_scores.drop(index="baseline_pv_only").val_score.idxmax()
print(val_scores.round(4).to_string()); print("recommended system (by validation):", RECOMMENDED)

# %% [markdown]
# ## Test results (PlantVillage test + untouched PlantDoc test)

# %%
def multiclass_metrics(y, pred, names=CLASS_NAMES):
    """Accuracy, macro F1, balanced accuracy, missed-disease rate, per-class report and confusion matrix."""
    k = len(names)
    y, pred = np.asarray(y), np.asarray(pred)
    diseased = y > 0
    return dict(
        n=int(len(y)),
        accuracy=float(accuracy_score(y, pred)),
        macro_f1=float(f1_score(y, pred, average="macro", labels=range(k), zero_division=0)),
        balanced_accuracy=float(balanced_accuracy_score(y, pred)) if len(np.unique(y)) > 1 else float("nan"),
        missed_disease_rate=float(np.mean(pred[diseased] == 0)) if diseased.any() else float("nan"),
        per_class=classification_report(y, pred, labels=list(range(k)), target_names=names, output_dict=True, zero_division=0),
        confusion_matrix=confusion_matrix(y, pred, labels=list(range(k))).tolist(),
    )

def plot_cm(cm, title, path):
    """Save a confusion-matrix image with the count written in each cell."""
    cm = np.array(cm)
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.imshow(cm, cmap="Blues")
    ax.set_xticks(range(5), CLASS_NAMES, rotation=40, ha="right", fontsize=8); ax.set_yticks(range(5), CLASS_NAMES, fontsize=8)
    for (r, c), v in np.ndenumerate(cm):
        ax.text(c, r, v, ha="center", va="center", fontsize=8, color="white" if v > cm.max() / 2 else "black")
    ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(title, fontsize=9)
    plt.tight_layout(); plt.savefig(path, dpi=110); plt.close(fig)

TEST_SETS = {"plantvillage_test": pv_te, "plantdoc_test_leaf_crops": pd_te[pd_te.kind == "crop"],
             "plantdoc_test_full_images": pd_te[pd_te.kind == "full"]}
RESULTS = {"gate_threshold": GATE_THRESHOLD, "recommended_system": RECOMMENDED,
           "validation": val_scores.to_dict(orient="index"), "sets": {}}
for set_name, df in TEST_SETS.items():
    if len(df) == 0:
        continue
    P, y = predict_all(df)
    preds = system_preds(P, GATE_THRESHOLD)
    RESULTS["sets"][set_name] = {s: multiclass_metrics(y, p) for s, p in preds.items()}
    for s in ("baseline_pv_only", RECOMMENDED):
        plot_cm(RESULTS["sets"][set_name][s]["confusion_matrix"], f"{s} - {set_name}", WORK_DIR / f"cm_{set_name}_{s}.png")

summary = pd.DataFrame([dict(eval_set=s, system=k, n=v["n"], accuracy=v["accuracy"], macro_f1=v["macro_f1"],
                             balanced_accuracy=v["balanced_accuracy"], missed_disease_rate=v["missed_disease_rate"])
                        for s, r in RESULTS["sets"].items() for k, v in r.items()])
summary.to_csv(WORK_DIR / "results_summary.csv", index=False)
pd.set_option("display.width", 200)
print(summary.round(4).to_string(index=False))
for set_name, r in RESULTS["sets"].items():
    pc = r[RECOMMENDED]["per_class"]
    print(f"{RECOMMENDED} per-class recall on {set_name}:", {c: round(pc[c]["recall"], 3) for c in CLASS_NAMES})

# %% [markdown]
# ## Robustness - angle, lighting and camera quality (PlantVillage test and PlantDoc test leaf crops)

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
for set_name in ("plantvillage_test", "plantdoc_test_leaf_crops"):
    df = TEST_SETS[set_name]
    if len(df) == 0:
        continue
    for cond, fn in CONDITIONS.items():
        ds = LeafDataset(df.path, df.label, eval_tf, boxes=df.box.tolist(), corrupt=fn)
        dl = make_loader(ds)
        P = {run: predict(m, dl)[0] for run, m in trained.items()}
        for s, p in system_preds(P, GATE_THRESHOLD).items():
            m = multiclass_metrics(ds.labels, p)
            robust_rows.append(dict(eval_set=set_name, condition=cond, system=s, macro_f1=m["macro_f1"],
                                    accuracy=m["accuracy"], missed_disease_rate=m["missed_disease_rate"]))
robust = pd.DataFrame(robust_rows)
robust.to_csv(WORK_DIR / "robustness.csv", index=False)
for set_name, d in robust.groupby("eval_set"):
    print(f"\nmacro F1 - {set_name}")
    print(d.pivot(index="condition", columns="system", values="macro_f1").reindex(list(CONDITIONS)).round(4).to_string())

# %% [markdown]
# ## Save everything needed for the later ONNX / Raspberry Pi step

# %%
save_json({"classes": CLASS_NAMES, "disease_classes": DISEASE_NAMES, "gate_classes": GATE_NAMES}, "labels.json")
save_json({"img_size": IMG_SIZE, "resize": "direct resize to img_size x img_size (no aspect-ratio preservation)",
           "color_order": "RGB", "scale": "pixel / 255", "mean": MEAN, "std": STD, "layout": "NCHW float32",
           "recommended_system": RECOMMENDED,
           "recommended_checkpoints": (["gate_mnv3s_best.pt", "stage2_mnv3s_best.pt"] if RECOMMENDED == "cascade_mnv3s"
                                       else [f"{RECOMMENDED}_best.pt"]),
           "gate_healthy_threshold": GATE_THRESHOLD,
           "gate_rule": "healthy if softmax(gate)[0] > gate_healthy_threshold, else run stage2"}, "preprocess.json")
RESULTS["config"] = dict(seed=SEED, img_size=IMG_SIZE, epochs=EPOCHS, epoch_samples=EPOCH_SAMPLES, batch=BATCH,
                         patience=PATIENCE, pd_share=PD_SHARE, target_diseased_recall=TARGET_DISEASED_RECALL,
                         seq_block=SEQ_BLOCK, hash_max_dist=HASH_MAX_DIST, torch=torch.__version__,
                         albumentations=A.__version__, plantvillage_split=pv_table.to_dict(),
                         plantdoc_crop_split=split_table(pdr[pdr.kind == "crop"]).to_dict(),
                         plantdoc_full_split=split_table(pdr[pdr.kind == "full"]).to_dict(),
                         plantdoc_groups_dropped_as_plantvillage_lookalikes=len(leaked_groups),
                         plantdoc_folder_label_conflicts=label_conflicts)
save_json(RESULTS, "results.json")
print(sorted(p.name for p in WORK_DIR.iterdir()))
