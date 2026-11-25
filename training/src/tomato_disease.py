# %% [markdown]
# # KrishiRakshak PS1 - Tomato disease training (Kaggle GPU)
#
# Trains and compares tomato-leaf disease models on **PlantVillage (color only)** and evaluates them,
# untouched, on **PlantDoc** field/web images.
#
# | System | What it is |
# |---|---|
# | `direct_mnv3` | MobileNetV3-Small, one 5-class model (baseline) |
# | `direct_effb0` | EfficientNet-B0, one 5-class model (comparison) |
# | `cascade_mnv3` | Stage 1 MobileNetV3-Small Healthy/Diseased gate -> Stage 2 MobileNetV3-Small 4-disease model |
# | `cascade_paper_gate` | Stage 1 = custom 4-layer CNN from the IEEE Access 2025 paper -> same Stage 2 |
#
# Classes: `healthy`, `early_blight`, `late_blight`, `leaf_mold`, `septoria_leaf_spot`.
#
# Rules followed (see `docs/RESULTS.md, "Test data rules"`):
# - Augmentation is **online only** - generated in memory per training step, never written to disk.
# - Validation / test / PlantDoc images get resize + normalise only.
# - Splits are made **before** augmentation, and grouped so photos of the same physical leaf never cross splits.
# - PlantDoc is never used for training or threshold tuning.
# - Checkpoints are selected by validation macro F1. ONNX export is a separate later step.
#
# **Kaggle setup:** Accelerator = *GPU T4*, Internet = on, and attach these datasets:
# `abdallahalidev/plantvillage-dataset`, `yusufmurtaza01/plantdoc-object-detection-dataset`,
# `nirmalsankalana/plantdoc-dataset`.

# %%
import os, sys, subprocess

ON_KAGGLE = os.path.exists("/kaggle/input")
SMOKE = os.environ.get("KR_SMOKE") == "1"  # tiny local test run
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "albumentations==2.0.8"], check=True)

# %%
import json, random, re, time, warnings
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
from sklearn.model_selection import StratifiedGroupKFold
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import models

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")
print("torch", torch.__version__, "| albumentations", A.__version__, "| cv2", cv2.__version__)

# %% [markdown]
# ## Configuration

# %%
SEED = 42
INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "disease_outputs"
WORK_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE = 224
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
BATCH = 16 if SMOKE else 64
NUM_WORKERS = 2 if SMOKE else 4
EPOCHS = 1 if SMOKE else 30
PAPER_CNN_EPOCHS = 1 if SMOKE else 40
PATIENCE = 8
TRAIN_EFFICIENTNET = True
TARGET_DISEASED_RECALL = 0.98   # Stage-1 threshold is tuned on validation to miss at most ~2% of diseased leaves
SEQ_BLOCK = 20                  # PlantVillage camera-sequence numbers grouped in blocks of 20 (4-7 shots per leaf)
HASH_MAX_DIST = 16              # pHash bits: same photo (rotation/flip invariant); real duplicates <= 6, different leaves >= 92
MAX_GROUP_SIZE = 60             # duplicate merging never grows a group beyond this
PLANTDOC_LEAK_DIST = 20         # PlantDoc images this close to any PlantVillage image are dropped from evaluation
MIN_CROP_SIDE = 32              # PlantDoc leaf boxes smaller than this (px) are skipped

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

# PlantDoc label -> our label. "Tomato leaf" is PlantDoc's generic healthy-tomato class (needs manual review).
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
# Searched under the input folder so it works regardless of Kaggle's mount layout.

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

# %% [markdown]
# ## Build the PlantVillage tomato manifest and profile every image
# Each image is opened once to record size/mode, catch corrupt files, and compute 8 rotation/flip variants of a
# perceptual hash (pHash) used for duplicate detection.

# %%
HASH_WORDS = 4  # 255-bit DCT pHash padded to 256 bits = 4 x uint64

def dihedral_phashes(img):
    """pHash of all 8 rotations/flips -> array (8, HASH_WORDS).
    Calibrated on real PlantVillage photos: rotated/flipped/re-compressed copies differ by <= 6 bits,
    different leaves by >= 92 bits."""
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

rows = []
for label, (cname, folder) in enumerate(TOMATO_CLASSES.items()):
    for f in sorted((PV_ROOT / folder).iterdir()):
        if f.suffix.lower() in IMG_EXT:
            rows.append(dict(path=str(f), file=f.name, label=label, class_name=cname))
pv = pd.DataFrame(rows)

t0 = time.time()
prof, pv_hashes = profile_paths(pv.path.tolist())
pv = pd.concat([pv, prof], axis=1)
print(f"profiled {len(pv)} images in {time.time() - t0:.0f}s; corrupt: {(~pv.ok).sum()}")
print(pv.groupby("class_name").size().rename("images").to_string())
print("sizes:", Counter(zip(pv.width, pv.height)).most_common(3), "| modes:", dict(Counter(pv["mode"])))
pv.drop(columns=["path"]).to_csv(WORK_DIR / "plantvillage_tomato_profile.csv", index=False)

# %% [markdown]
# ## Leak-proof grouping before splitting
# PlantVillage photographed each leaf 4-7 times while rotating it, and file names carry the camera sequence number
# (e.g. `RS_Erly.B 6330`, `6331`, ...) or a leaf id with day (`GHLB Leaf 1 Day 6`). Images are grouped by
# source + sequence block / leaf id, then exact and rotated/flipped duplicates (pHash) are merged into the same group.
# Whole groups go to train, validation or test - never split across them.

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

def popcount64(x):
    """Number of set bits in each uint64 value (Hamming weight), with a fallback for older numpy."""
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(x)
    return np.unpackbits(x.view(np.uint8).reshape(*x.shape, 8), axis=-1).sum(-1)

def near_duplicate_pairs(h_query, h_ref, max_dist, same=False, chunk=64):
    """Pairs (i, j) where query i's hash is within max_dist bits of any rotation/flip of reference j."""
    out = []
    for s in range(0, len(h_query), chunk):
        q = h_query[s:s + chunk, 0]                                   # (q, words)
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

ok_mask = pv.ok.to_numpy(bool)
pv, pv_hashes = pv[ok_mask].reset_index(drop=True), pv_hashes[ok_mask]
pv["leaf_key"] = [leaf_group_key(c, f) for c, f in zip(pv.class_name, pv.file)]

dsu = DSU(len(pv))
first_of_key = {}
for i, k in enumerate(pv.leaf_key):
    dsu.union(first_of_key.setdefault(k, i), i)
dup_pairs = near_duplicate_pairs(pv_hashes, pv_hashes, HASH_MAX_DIST, same=True)
labels_arr = pv.label.to_numpy()
cross_class = [(pv.file[i], pv.class_name[i], pv.file[j], pv.class_name[j])
               for i, j in dup_pairs if labels_arr[i] != labels_arr[j]]
refused = sum(not dsu.union(int(i), int(j), MAX_GROUP_SIZE) for i, j in dup_pairs if labels_arr[i] == labels_arr[j])
pv["group"] = [dsu.find(i) for i in range(len(pv))]

gsize = pv.group.value_counts()
print(f"leaf keys: {pv.leaf_key.nunique()} | duplicate pairs (pHash<={HASH_MAX_DIST} bits): {len(dup_pairs)} "
      f"| merges refused by size cap: {refused} | final groups: {len(gsize)} | largest group: {gsize.max()} images")
print("same photo under DIFFERENT labels (label conflicts, check manually):", len(cross_class), cross_class[:5])
pd.DataFrame(cross_class, columns=["file_a", "class_a", "file_b", "class_b"]).to_csv(WORK_DIR / "label_conflicts.csv", index=False)

# %% [markdown]
# ## Stratified group split: ~70% train / 15% validation / 15% test

# %%
def group_split(df, seed=SEED):
    """Stratified group split: about 70% train, 15% validation, 15% test; groups never cross splits."""
    y, g = df.label.values, df.group.values
    trv, te = next(StratifiedGroupKFold(n_splits=7, shuffle=True, random_state=seed).split(df, y, g))
    sub = df.iloc[trv]
    tr, va = next(StratifiedGroupKFold(n_splits=6, shuffle=True, random_state=seed).split(sub, sub.label.values, sub.group.values))
    split = np.empty(len(df), dtype=object)
    split[te], split[trv[tr]], split[trv[va]] = "test", "train", "val"
    return split

pv["split"] = group_split(pv)
groups_per_split = pv.groupby("group").split.nunique()
assert (groups_per_split == 1).all(), "a leaf group crosses splits"
split_table = (pv.pivot_table(index="class_name", columns="split", values="file", aggfunc="count")
               .reindex(index=CLASS_NAMES, columns=["train", "val", "test"]).fillna(0).astype(int))
print(split_table.to_string())
assert (split_table > 0).all().all(), "every class must appear in train, val and test"
pv[["file", "class_name", "label", "leaf_key", "group", "split"]].to_csv(WORK_DIR / "plantvillage_split_manifest.csv", index=False)
train_df, val_df, test_df = (pv[pv.split == s].reset_index(drop=True) for s in ("train", "val", "test"))

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
#
# PlantVillage leaves were all rotated tip-up before being saved, so full rotation is essential.

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

class LeafDataset(Dataset):
    """Reads the original file on every access; optional crop box and deterministic corruption (for robustness tests)."""
    def __init__(self, paths, labels, transform, boxes=None, corrupt=None):
        self.paths, self.labels = list(paths), np.asarray(labels, dtype=np.int64)
        self.transform, self.boxes, self.corrupt = transform, boxes, corrupt
    def __len__(self):
        return len(self.paths)
    def load(self, i):
        """Read image i as an RGB array (cropped to its box and corrupted for robustness tests if configured)."""
        with Image.open(self.paths[i]) as im:
            im = im.convert("RGB")
            if self.boxes is not None:
                im = im.crop(tuple(self.boxes[i]))
            img = np.array(im)
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

def make_loader(ds, train):
    """Build a DataLoader; training loaders shuffle or sample and drop the last incomplete batch."""
    return DataLoader(ds, batch_size=BATCH, shuffle=train, drop_last=train, num_workers=NUM_WORKERS,
                      pin_memory=USE_AMP, worker_init_fn=seed_worker, persistent_workers=train and NUM_WORKERS > 0)

# Preview grid for visual checking / the report (the only augmented pixels ever written, and not used for training)
preview = LeafDataset(train_df.path, train_df.label, train_tf)
idx = np.random.default_rng(SEED).choice(len(preview), size=min(6, len(preview)), replace=False)
fig, axes = plt.subplots(len(idx), 7, figsize=(14, 2.1 * len(idx)))
for r, i in enumerate(idx):
    axes[r, 0].imshow(cv2.resize(preview.load(i), (IMG_SIZE, IMG_SIZE))); axes[r, 0].set_title(train_df.class_name[i], fontsize=7)
    for c in range(1, 7):
        x = preview[i][0].permute(1, 2, 0).numpy() * np.array(STD) + np.array(MEAN)
        axes[r, c].imshow(np.clip(x, 0, 1))
for a in axes.flat:
    a.axis("off")
plt.tight_layout(); plt.savefig(WORK_DIR / "augmentation_preview.png", dpi=110); plt.show()

# %% [markdown]
# ## Models
# MobileNetV3-Small and EfficientNet-B0 start from ImageNet weights. `PaperCNN` reproduces the paper's custom CNN
# (Conv 32-64-128-128, ReLU + max-pool, Dense 256, Dropout 0.5) trained from scratch, at 224x224 input so all
# models share one preprocessing pipeline.

# %%
class PaperCNN(nn.Module):
    """Custom 4-layer CNN from the IEEE Access 2025 paper, used as a baseline Healthy/Diseased gate."""
    def __init__(self, n_classes, img_size=IMG_SIZE):
        super().__init__()
        def block(i, o):
            return [nn.Conv2d(i, o, 3, padding=1), nn.ReLU(inplace=True), nn.MaxPool2d(2)]
        self.features = nn.Sequential(*block(3, 32), *block(32, 64), *block(64, 128), *block(128, 128))
        s = img_size // 16
        self.classifier = nn.Sequential(nn.Flatten(), nn.Linear(128 * s * s, 256), nn.ReLU(inplace=True),
                                        nn.Dropout(0.5), nn.Linear(256, n_classes))
    def forward(self, x):
        return self.classifier(self.features(x))

def build_model(arch, n_classes):
    """Create an ImageNet-pretrained backbone (or the paper CNN) with a new output layer of n_classes."""
    if arch == "mobilenet_v3_small":
        m = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
        m.classifier[3] = nn.Linear(m.classifier[3].in_features, n_classes)
    elif arch == "efficientnet_b0":
        m = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, n_classes)
    elif arch == "paper_cnn":
        m = PaperCNN(n_classes)
    else:
        raise ValueError(arch)
    return m

for arch in ("mobilenet_v3_small", "efficientnet_b0", "paper_cnn"):
    print(f"{arch:20s} {sum(p.numel() for p in build_model(arch, 2).parameters()) / 1e6:.2f}M parameters (2-class head)")

# %% [markdown]
# ## Training loop
# AdamW + one-cycle LR, mixed precision on GPU, class-weighted cross-entropy (classes are imbalanced),
# best checkpoint by validation macro F1, early stopping.

# %%
@torch.no_grad()
def predict(model, loader):
    """Return softmax probabilities and true labels for every image in the loader."""
    model.eval(); probs, ys = [], []
    for x, y in loader:
        with torch.autocast(device_type=DEVICE.type, dtype=torch.float16, enabled=USE_AMP):
            logits = model(x.to(DEVICE, non_blocking=True))
        probs.append(torch.softmax(logits.float(), 1).cpu().numpy()); ys.append(y.numpy())
    return np.concatenate(probs), np.concatenate(ys)

def train_model(run, arch, task_names, train_ds, val_ds, epochs, lr):
    """Train one model and keep the checkpoint with the best validation score (stops early when it stops improving)."""
    n = len(task_names)
    model = build_model(arch, n).to(DEVICE)
    counts = np.bincount(train_ds.labels, minlength=n)
    weights = torch.tensor(len(train_ds) / (n * np.maximum(counts, 1)), dtype=torch.float32, device=DEVICE)
    loss_fn = nn.CrossEntropyLoss(weight=weights, label_smoothing=0.05)
    train_dl, val_dl = make_loader(train_ds, True), make_loader(val_ds, False)
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
        p, yv = predict(model, val_dl)
        row = dict(epoch=epoch, train_loss=total / max(seen, 1), val_accuracy=accuracy_score(yv, p.argmax(1)),
                   val_macro_f1=f1_score(yv, p.argmax(1), average="macro", labels=range(n), zero_division=0),
                   seconds=round(time.time() - t0, 1))
        history.append(row)
        print(f"[{run}] " + " ".join(f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in row.items()))
        if row["val_macro_f1"] > best:
            best, bad = row["val_macro_f1"], 0
            torch.save({"model_state_dict": model.state_dict(), "arch": arch, "class_names": list(task_names),
                        "img_size": IMG_SIZE, "mean": list(MEAN), "std": list(STD), "epoch": epoch,
                        "val_macro_f1": best}, ckpt)
        else:
            bad += 1
            if bad >= PATIENCE:
                print(f"[{run}] early stop at epoch {epoch}"); break
    pd.DataFrame(history).to_csv(WORK_DIR / f"{run}_history.csv", index=False)
    model.load_state_dict(torch.load(ckpt, map_location=DEVICE, weights_only=True)["model_state_dict"])
    print(f"[{run}] best val macro F1 = {best:.4f} -> {ckpt.name}")
    return model.eval()

# %% [markdown]
# ## Train all models

# %%
def task_dataset(df, task, transform):
    """Dataset for one task: 5-class direct, Healthy/Diseased gate, or 4-disease stage 2."""
    if task == "direct":
        return LeafDataset(df.path, df.label, transform)
    if task == "gate":
        return LeafDataset(df.path, (df.label > 0).astype(int), transform)
    if task == "stage2":
        d = df[df.label > 0]
        return LeafDataset(d.path, d.label - 1, transform)
    raise ValueError(task)

RUNS = [  # name, architecture, task, epochs, max learning rate
    ("direct_mnv3", "mobilenet_v3_small", "direct", EPOCHS, 1e-3),
    ("gate_mnv3", "mobilenet_v3_small", "gate", EPOCHS, 1e-3),
    ("stage2_mnv3", "mobilenet_v3_small", "stage2", EPOCHS, 1e-3),
    ("gate_paper_cnn", "paper_cnn", "gate", PAPER_CNN_EPOCHS, 3e-4),
]
if TRAIN_EFFICIENTNET:
    RUNS.insert(1, ("direct_effb0", "efficientnet_b0", "direct", EPOCHS, 1e-3))
TASK_NAMES = {"direct": CLASS_NAMES, "gate": GATE_NAMES, "stage2": DISEASE_NAMES}

trained = {}
for run, arch, task, epochs, lr in RUNS:
    t0 = time.time()
    trained[run] = train_model(run, arch, TASK_NAMES[task], task_dataset(train_df, task, train_tf),
                               task_dataset(val_df, task, eval_tf), epochs, lr)
    print(f"[{run}] trained in {(time.time() - t0) / 60:.1f} min\n")

# %% [markdown]
# ## Evaluation sets
# - **PlantVillage test** - held-out leaf groups.
# - **PlantDoc leaf crops** - each annotated tomato leaf cut out of PlantDoc field/web photos (fair test for a single-leaf classifier).
# - **PlantDoc full images** - whole photos as a farmer would take them (hardest).
#
# PlantDoc images that are near-copies of any PlantVillage image are removed first.

# %%
def drop_plantvillage_lookalikes(paths):
    """Flag PlantDoc images that are near-copies of a PlantVillage image (removed to avoid leakage)."""
    _, h = profile_paths(paths)
    if len(paths) == 0:
        return np.zeros(0, bool)
    hits = near_duplicate_pairs(h, pv_hashes, PLANTDOC_LEAK_DIST)
    leaked = np.zeros(len(paths), bool); leaked[np.unique(hits[:, 0])] = True
    return leaked

EVAL_SETS = {"plantvillage_test": LeafDataset(test_df.path, test_df.label, eval_tf)}
external_notes = {}

if PD_DET_ROOT is not None:
    id_to_label = {i: CLASS_NAMES.index(PLANTDOC_MAP[norm_name(n)]) for i, n in PD_DET_NAMES.items() if norm_name(n) in PLANTDOC_MAP}
    print("PlantDoc detection classes used:", {PD_DET_NAMES[i]: CLASS_NAMES[l] for i, l in id_to_label.items()})
    crops = []
    for img_path in sorted((PD_DET_ROOT / "images").rglob("*")):
        if img_path.suffix.lower() not in IMG_EXT:
            continue
        lbl = Path(str(img_path).replace(f"{os.sep}images{os.sep}", f"{os.sep}labels{os.sep}")).with_suffix(".txt")
        if not lbl.exists():
            continue
        lines = [l.split() for l in open(lbl).read().splitlines() if l.strip()]
        lines = [l for l in lines if int(float(l[0])) in id_to_label]
        if not lines:
            continue
        with Image.open(img_path) as im:
            W, H = im.size
        for c, cx, cy, w, h in (map(float, l[:5]) for l in lines):
            box = (max(0, round((cx - w / 2) * W)), max(0, round((cy - h / 2) * H)),
                   min(W, round((cx + w / 2) * W)), min(H, round((cy + h / 2) * H)))
            if min(box[2] - box[0], box[3] - box[1]) >= MIN_CROP_SIDE:
                crops.append(dict(path=str(img_path), box=box, label=id_to_label[int(c)]))
    crops = pd.DataFrame(crops)
    if len(crops):
        uniq = crops.path.unique().tolist()
        leaked = dict(zip(uniq, drop_plantvillage_lookalikes(uniq)))
        n_before = len(crops); crops = crops[~crops.path.map(leaked)].reset_index(drop=True)
        external_notes["plantdoc_crops_removed_as_plantvillage_lookalikes"] = n_before - len(crops)
        EVAL_SETS["plantdoc_leaf_crops"] = LeafDataset(crops.path, crops.label, eval_tf, boxes=crops.box.tolist())
        print("PlantDoc leaf crops per class:", crops.label.map(dict(enumerate(CLASS_NAMES))).value_counts().to_dict())

if PD_CLS_ROOT is not None:
    full = []
    for split_dir in ("train", "test"):
        for cdir in sorted((PD_CLS_ROOT / split_dir).iterdir()):
            if cdir.is_dir() and norm_name(cdir.name) in PLANTDOC_MAP:
                lab = CLASS_NAMES.index(PLANTDOC_MAP[norm_name(cdir.name)])
                full += [dict(path=str(f), label=lab) for f in sorted(cdir.iterdir()) if f.suffix.lower() in IMG_EXT]
    full = pd.DataFrame(full)
    if len(full):
        leaked = drop_plantvillage_lookalikes(full.path.tolist())
        external_notes["plantdoc_full_removed_as_plantvillage_lookalikes"] = int(leaked.sum())
        full = full[~leaked].reset_index(drop=True)
        EVAL_SETS["plantdoc_full_images"] = LeafDataset(full.path, full.label, eval_tf)
        print("PlantDoc full images per class:", full.label.map(dict(enumerate(CLASS_NAMES))).value_counts().to_dict())

print({k: len(v) for k, v in EVAL_SETS.items()}, external_notes)

# %% [markdown]
# ## Tune the Stage-1 threshold on validation (PlantVillage only)
# A leaf is reported healthy only when P(healthy) is above the threshold. The threshold is the lowest value that keeps
# diseased recall >= `TARGET_DISEASED_RECALL` on validation. It is then frozen for test and PlantDoc.

# %%
def tune_gate_threshold(model):
    """Lowest healthy-probability threshold that keeps diseased recall at TARGET_DISEASED_RECALL on validation."""
    p, y = predict(model, make_loader(task_dataset(val_df, "gate", eval_tf), False))
    p_h_diseased = p[y == 1, 0]
    thr = float(max(0.5, np.quantile(p_h_diseased, TARGET_DISEASED_RECALL))) if len(p_h_diseased) else 0.5
    return min(thr, 0.999)

GATE_THRESHOLDS = {g: tune_gate_threshold(trained[g]) for g in ("gate_mnv3", "gate_paper_cnn")}
print("tuned healthy thresholds:", GATE_THRESHOLDS)

# %% [markdown]
# ## Evaluate every system on every set

# %%
def multiclass_metrics(y, pred, names):
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

def binary_gate_metrics(p_healthy, y5, thr):
    """Healthy/Diseased metrics of a gate at a given healthy-probability threshold."""
    y_dis = np.asarray(y5) > 0
    pred_dis = p_healthy <= thr
    return dict(threshold=thr, accuracy=float(np.mean(pred_dis == y_dis)),
                diseased_recall=float(pred_dis[y_dis].mean()) if y_dis.any() else float("nan"),
                healthy_recall=float((~pred_dis[~y_dis]).mean()) if (~y_dis).any() else float("nan"),
                macro_f1=float(f1_score(y_dis, pred_dis, average="macro", zero_division=0)))

def cascade_pred(p_gate, p_stage2, thr):
    """Two-stage prediction: healthy if P(healthy) > thr, otherwise the stage-2 disease (class index + 1)."""
    return np.where(p_gate[:, 0] > thr, 0, 1 + p_stage2.argmax(1))

def predict_all(ds):
    """Probabilities of every trained model on one evaluation set."""
    dl = make_loader(ds, False)
    return {run: predict(m, dl)[0] for run, m in trained.items()}, ds.labels

def systems_from_probs(P, y):
    """Metrics of every compared system (direct models and two-stage cascades) from model probabilities."""
    out = {"direct_mnv3": multiclass_metrics(y, P["direct_mnv3"].argmax(1), CLASS_NAMES)}
    if "direct_effb0" in P:
        out["direct_effb0"] = multiclass_metrics(y, P["direct_effb0"].argmax(1), CLASS_NAMES)
    for gate, name in (("gate_mnv3", "cascade_mnv3"), ("gate_paper_cnn", "cascade_paper_gate")):
        out[name] = multiclass_metrics(y, cascade_pred(P[gate], P["stage2_mnv3"], GATE_THRESHOLDS[gate]), CLASS_NAMES)
        out[name + "@0.5"] = multiclass_metrics(y, cascade_pred(P[gate], P["stage2_mnv3"], 0.5), CLASS_NAMES)
    return out

RESULTS = {"gate_thresholds": GATE_THRESHOLDS, "external_notes": external_notes, "sets": {}}
for set_name, ds in EVAL_SETS.items():
    P, y = predict_all(ds)
    systems = systems_from_probs(P, y)
    gates = {g: {"tuned": binary_gate_metrics(P[g][:, 0], y, GATE_THRESHOLDS[g]),
                 "at_0.5": binary_gate_metrics(P[g][:, 0], y, 0.5)} for g in ("gate_mnv3", "gate_paper_cnn")}
    dis = y > 0
    stage2 = multiclass_metrics(y[dis] - 1, P["stage2_mnv3"][dis].argmax(1), DISEASE_NAMES) if dis.any() else None
    RESULTS["sets"][set_name] = {"systems": systems, "gates": gates, "stage2_on_diseased_only": stage2}
    for sys_name in ("direct_mnv3", "cascade_mnv3"):
        cm = np.array(systems[sys_name]["confusion_matrix"])
        fig, ax = plt.subplots(figsize=(5.5, 4.5))
        ax.imshow(cm, cmap="Blues")
        ax.set_xticks(range(5), CLASS_NAMES, rotation=40, ha="right", fontsize=8); ax.set_yticks(range(5), CLASS_NAMES, fontsize=8)
        for (r, c), v in np.ndenumerate(cm):
            ax.text(c, r, v, ha="center", va="center", fontsize=8, color="white" if v > cm.max() / 2 else "black")
        ax.set_xlabel("predicted"); ax.set_ylabel("true"); ax.set_title(f"{sys_name} - {set_name}", fontsize=9)
        plt.tight_layout(); plt.savefig(WORK_DIR / f"cm_{set_name}_{sys_name}.png", dpi=110); plt.close(fig)

summary = pd.DataFrame([
    dict(eval_set=s, system=k, n=v["n"], accuracy=v["accuracy"], macro_f1=v["macro_f1"],
         balanced_accuracy=v["balanced_accuracy"], missed_disease_rate=v["missed_disease_rate"])
    for s, r in RESULTS["sets"].items() for k, v in r["systems"].items()])
gate_summary = pd.DataFrame([
    dict(eval_set=s, gate=g, setting=t, **v) for s, r in RESULTS["sets"].items()
    for g, d in r["gates"].items() for t, v in d.items()])
summary.to_csv(WORK_DIR / "results_summary.csv", index=False)
gate_summary.to_csv(WORK_DIR / "gate_summary.csv", index=False)
pd.set_option("display.width", 200)
print(summary.round(4).to_string(index=False)); print(); print(gate_summary.round(4).to_string(index=False))

# %% [markdown]
# ## Robustness test - angle, lighting and camera quality
# Fixed (non-random) changes applied to the PlantVillage test set; each model sees exactly the same images.

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
    "rotate_270": lambda img, i: np.ascontiguousarray(np.rot90(img, 3)),
    "rotate_45": _rotate_any(45),
    "brightness_x0.5": lambda img, i: (img * 0.5).astype(np.uint8),
    "brightness_x0.7": lambda img, i: (img * 0.7).astype(np.uint8),
    "brightness_x1.3": lambda img, i: (img * 1.3).clip(0, 255).astype(np.uint8),
    "brightness_x1.6": lambda img, i: (img * 1.6).clip(0, 255).astype(np.uint8),
    "half_shadow": _half_shadow,
    "gaussian_blur_s2": lambda img, i: cv2.GaussianBlur(img, (0, 0), 2),
    "motion_blur_9": _motion(9),
    "noise_std0.06": _noise(0.06),
    "jpeg_q30": _jpeg(30),
    "downscale_0.35": _downscale(0.35),
}

robust_rows = []
for cond, fn in CONDITIONS.items():
    ds = LeafDataset(test_df.path, test_df.label, eval_tf, corrupt=fn)
    P, y = predict_all(ds)
    for sys_name, m in systems_from_probs(P, y).items():
        if "@" not in sys_name:
            robust_rows.append(dict(condition=cond, system=sys_name, accuracy=m["accuracy"], macro_f1=m["macro_f1"],
                                    missed_disease_rate=m["missed_disease_rate"]))
robust = pd.DataFrame(robust_rows)
robust.to_csv(WORK_DIR / "robustness_plantvillage_test.csv", index=False)
print(robust.pivot(index="condition", columns="system", values="macro_f1").reindex(list(CONDITIONS)).round(4).to_string())
RESULTS["robustness_macro_f1"] = robust.pivot(index="condition", columns="system", values="macro_f1").to_dict()

# %% [markdown]
# ## Save everything needed for the later ONNX / Raspberry Pi step

# %%
save_json({"classes": CLASS_NAMES, "disease_classes": DISEASE_NAMES, "gate_classes": GATE_NAMES}, "labels.json")
save_json({"img_size": IMG_SIZE, "resize": "direct resize to img_size x img_size (no aspect-ratio preservation)",
           "color_order": "RGB", "scale": "pixel / 255", "mean": MEAN, "std": STD, "layout": "NCHW float32",
           "gate_healthy_threshold": GATE_THRESHOLDS["gate_mnv3"],
           "gate_rule": "healthy if softmax(gate)[0] > gate_healthy_threshold, else run stage2"}, "preprocess.json")
RESULTS["config"] = dict(seed=SEED, img_size=IMG_SIZE, epochs=EPOCHS, paper_cnn_epochs=PAPER_CNN_EPOCHS, batch=BATCH,
                         patience=PATIENCE, target_diseased_recall=TARGET_DISEASED_RECALL, seq_block=SEQ_BLOCK,
                         hash_max_dist=HASH_MAX_DIST, torch=torch.__version__, albumentations=A.__version__,
                         plantvillage_root=str(PV_ROOT), plantdoc_detection_root=str(PD_DET_ROOT),
                         plantdoc_full_root=str(PD_CLS_ROOT), split_counts=split_table.fillna(0).astype(int).to_dict())
save_json(RESULTS, "results.json")
print(sorted(p.name for p in WORK_DIR.iterdir()))
