# %% [markdown]
# # KrishiRakshak PS1 - Tomato leaf check v2: "is this a tomato leaf?" (Kaggle GPU)
#
# **v2 (21 Nov 2026):** chilli, brinjal and bell pepper leaves added as "other". v1 had none of the crops that grow
# next to tomato in India; on the Raspberry Pi test 3 of 5 chilli field photos passed as tomato (one diagnosed as
# tomato leaf curl virus). New data: Red Chili Pepper Pests Dataset (indraagustian, Apache 2.0; field photos, its
# own train / valid / test folders, near-copies across them removed), Eggplant Disease Recognition Dataset
# (sujaykapadnis, CC BY 4.0; original photos only, not its augmented copies) and Solanaceae Family Leaves Dataset
# (ziya07, CC0; brinjal and bell pepper folders, its tomato folder is not used).
#
# The disease model only knows tomato classes, so it gives a confident tomato disease for any photo: an IP102
# rice-leaf photo was called "bacterial spot, 73%". This notebook trains a small separate model that runs before the
# disease result is shown and answers one question: tomato leaf or not. The validated disease model (v5) is not
# changed.
#
# | Class | Training images |
# |---|---|
# | tomato | all 10 PlantVillage tomato classes + PlantDoc tomato field photos and leaf crops (the v4 split manifests, so every disease test image is also a test image here) |
# | other | PlantVillage leaves of the 13 other crops (potato and pepper are the hardest: same plant family), PlantDoc field photos of the other crops, IP102 insect photos (rice, wheat, maize, citrus, mango ... fields), Natural Images (people, animals, vehicles, flowers, fruit) |
#
# **Test rules (as v4/v5):** test images are never used for training, checkpoint selection or the threshold.
# Photos of one leaf and copies of one photo (rotation/flip-invariant pHash) stay in one split. PlantDoc photos that
# are near-copies of a PlantVillage photo are removed, and other-crop photos that are near-copies of a tomato photo
# are removed (they would teach the model that a tomato photo is "other").
#
# **Threshold:** a photo is rejected when P(other) is above a threshold chosen on validation so that at most
# `MAX_TOMATO_REJECT_VAL` of the tomato validation photos (field and lab, each) are rejected. Target from
# docs/ROADMAP.md (A1): at least 90% of non-tomato photos rejected, at most 5% of tomato field photos rejected.
#
# **Baseline:** the obvious alternative without a new model - reject when the v5 disease model's top probability is
# low - is evaluated on the same test images with a threshold chosen the same way.
#
# **Kaggle setup:** Accelerator = *GPU T4*, Internet = on, attach `abdallahalidev/plantvillage-dataset`,
# `yusufmurtaza01/plantdoc-object-detection-dataset`, `nirmalsankalana/plantdoc-dataset`, `parserpixy/ip102-dataset`,
# `prasunroy/natural-images`, `indraagustian/red-chili-pepper-pests-dataset`,
# `sujaykapadnis/eggplant-disease-recognition-dataset`, `ziya07/solanaceae-family-leaves-dataset`, and the outputs of
# `ps1-tomato-disease-v4` (split manifests) and `ps1-tomato-disease-v5` (baseline checkpoint).

# %%
import os, sys, subprocess

ON_KAGGLE = os.path.exists("/kaggle/input")
SMOKE = os.environ.get("KR_SMOKE") == "1"  # tiny local test run
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "albumentations==2.0.8", "onnx", "onnxruntime"],
                   check=True)

# %%
import hashlib, json, math, random, re, time, warnings
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import albumentations as A
import cv2
import numpy as np
import pandas as pd
import torch
import yaml
from albumentations.pytorch import ToTensorV2
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from torchvision import models

warnings.filterwarnings("ignore", category=UserWarning)
print("torch", torch.__version__, "| albumentations", A.__version__, "| cv2", cv2.__version__)

# %% [markdown]
# ## Configuration

# %%
SEED = 42
INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "leaf_check_outputs"
WORK_DIR.mkdir(parents=True, exist_ok=True)

CLASS_NAMES = ["tomato", "other"]   # index 0 = tomato leaf, 1 = anything else
IMG_SIZE = 224                       # same preprocessing as the disease model, so the device resizes once
MEAN, STD = (0.485, 0.456, 0.406), (0.229, 0.224, 0.225)
BATCH = 16 if SMOKE else 64
NUM_WORKERS = 2 if SMOKE else 4
EPOCHS = 1 if SMOKE else 12
WARMUP_EPOCHS = 1
EMA_DECAY = 0.998
EPOCH_SAMPLES = 160 if SMOKE else 12000
PATIENCE = 5
ARCHS = ["mobilenet_v3_small", "efficientnet_b0"]
DECODE_MIN_SIDE = 336

# Images per source (sampled, so profiling and training stay fast; the split is made after sampling)
PV_OTHER_PER_CLASS = 20 if SMOKE else 450   # 25 non-tomato PlantVillage classes -> about 11,000 images
IP102_MAX = 40 if SMOKE else 4000
NATURAL_MAX = 40 if SMOKE else 2400
EXTRA_MAX_PER_CROP = 20 if SMOKE else 1500   # chilli / brinjal / bell pepper photos (v2)

# Split shares (as v4): PlantVillage 70/15/15, PlantDoc 65/10/25; IP102 uses its official trainval/test split
PV_TEST_FRAC, PV_VAL_FRAC = 0.15, 0.15
PD_TEST_FRAC, PD_VAL_FRAC = 0.25, 0.10
OTHER_TEST_FRAC, OTHER_VAL_FRAC = 0.20, 0.15
SEQ_BLOCK = 20
HASH_MAX_DIST = 16          # pHash bits: same photo (rotation/flip invariant)
MAX_GROUP_SIZE = 60
PLANTDOC_LEAK_DIST = 20     # PlantDoc photos this close to a PlantVillage photo are dropped
MIN_CROP_SIDE = 32

# Share of each training batch per (class, source); within a source, its sub-classes (crops) are balanced
SAMPLE_SHARE = {("tomato", "pv"): 0.22, ("tomato", "pd"): 0.28,
                ("other", "pv"): 0.14, ("other", "pd"): 0.14, ("other", "ip102"): 0.07, ("other", "natural"): 0.05,
                ("other", "solanaceae"): 0.10}   # v2: chilli, brinjal, bell pepper (crops balanced inside)
MAX_TOMATO_REJECT_VAL = 0.03   # threshold rule on validation (margin below the 5% target: validation sets are small)

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

def crop_of(name):
    """Crop name of a PlantVillage folder or PlantDoc class ('Pepper,_bell___healthy' -> 'pepper')."""
    n = norm_name(name.split("___")[0]).replace(",", "")
    if "pepper" in n:
        return "pepper"
    if n.startswith("corn"):
        return "corn"
    if n.startswith("soy"):
        return "soybean"
    return n.split(" ")[0]

# %% [markdown]
# ## Locate the attached datasets and the v4 / v5 outputs

# %%
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def walk_dirs(root, max_depth=6):
    """os.walk below root up to max_depth, skipping folders that never need searching (keeps discovery fast)."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        p = Path(dirpath)
        if len(p.relative_to(root).parts) >= max_depth or p.name in ("Annotations", "JPEGImages"):
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
    """Return (root, {class id: name}) of the PlantDoc copy that has YOLO boxes and a dataset yaml."""
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

def find_ip102():
    """Return the IP102 VOC root (Annotations/ + JPEGImages/) and the paths of its trainval/test split files."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT):
        if "Annotations" in dirs and "JPEGImages" in dirs:
            split_files = {}
            for sd, _, sfiles in walk_dirs(d, max_depth=3):
                for name in ("trainval.txt", "test.txt"):
                    if name in sfiles and name not in split_files:
                        split_files[name] = sd / name
            return d, split_files
    return None, {}

def find_natural_images():
    """Return the Natural Images folder (class folders airplane/, car/, cat/, ...), or None if not attached."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT):
        if {"airplane", "car", "person"} <= set(dirs):
            return d
    return None

def find_chili():
    """Red chilli pest dataset: folder with train/images whose files start with kutu / ulat / thrips (v2)."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT, max_depth=5):
        if "train" in dirs and (d / "train" / "images").is_dir():
            names = os.listdir(d / "train" / "images")[:500]
            if any(n.startswith(("kutu", "ulat", "thrips")) for n in names):
                return d
    return None

def images_below(root, keep=lambda p: True):
    """All image files below root (recursive) whose path passes keep."""
    return sorted(str(p) for p in Path(root).rglob("*") if p.suffix.lower() in IMG_EXT and keep(str(p).lower()))

def find_dir(test):
    """First folder under the inputs for which test(folder, subfolder names) is true, or None."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT, max_depth=6):
        if test(d, dirs):
            return d
    return None

FILE_INDEX = {}  # small result files (manifests, checkpoints) found under the inputs
for d, _, files in walk_dirs(INPUT_ROOT, max_depth=8):
    for f in files:
        if f.endswith((".csv", ".pt")):
            FILE_INDEX.setdefault(f, []).append(d / f)

PV_ROOT = find_plantvillage_color()
PD_DET_ROOT, PD_DET_NAMES = find_plantdoc_detection()
PD_CLS_ROOT = find_plantdoc_classification()
IP_ROOT, IP_SPLITS = find_ip102()
NAT_ROOT = find_natural_images()
V4_PV_MANIFEST = next((p for p in FILE_INDEX.get("plantvillage_split_manifest.csv", []) if "v5" not in str(p)), None)
V4_PD_MANIFEST = next((p for p in FILE_INDEX.get("plantdoc_split_manifest.csv", []) if "v5" not in str(p)), None)
print("PlantVillage color :", PV_ROOT)
print("PlantDoc detection :", PD_DET_ROOT)
print("PlantDoc folders   :", PD_CLS_ROOT)
print("IP102              :", IP_ROOT, {k: str(v) for k, v in IP_SPLITS.items()})
print("Natural Images     :", NAT_ROOT)
CHILI_ROOT = find_chili()
EGGPLANT_ROOT = find_dir(lambda d, dirs: "eggplant disease recognition" in d.name.lower())
SOLANACEAE_ROOT = find_dir(lambda d, dirs: "Brinjal" in dirs and any(x.lower().startswith("pepper") for x in dirs))
print("chilli / eggplant / solanaceae:", CHILI_ROOT, "|", EGGPLANT_ROOT, "|", SOLANACEAE_ROOT)
print("v4 manifests       :", V4_PV_MANIFEST, V4_PD_MANIFEST)
assert V4_PV_MANIFEST and V4_PD_MANIFEST, "attach the output of the ps1-tomato-disease-v4 notebook (split manifests)"

# Manifest paths were written on Kaggle; re-root them if the datasets are mounted elsewhere (e.g. the smoke test)
DATASET_DIRS = {}
for d, dirs, _ in walk_dirs(INPUT_ROOT, max_depth=4):
    for name in ("plantdoc-object-detection-dataset", "plantdoc-dataset"):
        if name in dirs and name not in DATASET_DIRS:
            DATASET_DIRS[name] = d / name

def local_path(p):
    """Path of a manifest image on this machine."""
    if os.path.exists(p):
        return p
    for name, root in DATASET_DIRS.items():
        if f"/{name}/" in p:
            return str(root / p.split(f"/{name}/", 1)[1])
    return p

# %% [markdown]
# ## Perceptual hashing and grouping helpers (as v4)

# %%
HASH_WORDS = 4

def dihedral_phashes(img):
    """pHash of all 8 rotations/flips -> (8, HASH_WORDS)."""
    g = img.convert("L").resize((64, 64), Image.BILINEAR)
    out = []
    for k in range(4):
        r = g.rotate(90 * k)
        for v in (r, r.transpose(Image.FLIP_LEFT_RIGHT)):
            d = cv2.dct(np.asarray(v, np.float32))[:16, :16].flatten()[1:]
            out.append(np.packbits(np.append(d > np.median(d), False)).view(">u8").astype(np.uint64))
    return np.stack(out)

def profile_one(path):
    """Open one image: record its size, flag unreadable files, and compute its rotation/flip pHashes."""
    try:
        with Image.open(path) as im:
            w, h = im.size
            im.draft("RGB", (256, 256))
            im.load()
            return dict(width=w, height=h, ok=True), dihedral_phashes(im)
    except Exception:
        return dict(width=0, height=0, ok=False), np.zeros((8, HASH_WORDS), np.uint64)

def profile_paths(paths):
    """Profile many images in parallel; returns (DataFrame of sizes and status, array of hashes)."""
    with ThreadPoolExecutor(8) as ex:
        res = list(ex.map(profile_one, paths))
    hashes = np.stack([r[1] for r in res]) if res else np.zeros((0, 8, HASH_WORDS), np.uint64)
    return pd.DataFrame([r[0] for r in res]), hashes

def popcount64(x):
    """Number of set bits in each uint64 value."""
    if hasattr(np, "bitwise_count"):
        return np.bitwise_count(x)
    return np.unpackbits(x.view(np.uint8).reshape(*x.shape, 8), axis=-1).sum(-1)

def near_duplicate_pairs(h_query, h_ref, max_dist, same=False, chunk=64):
    """Pairs (i, j) where query i's hash is within max_dist bits of any rotation/flip of reference j."""
    out = []
    if len(h_query) == 0 or len(h_ref) == 0:
        return np.zeros((0, 2), int)
    for s in range(0, len(h_query), chunk):
        q = h_query[s:s + chunk, 0]
        d = popcount64(q[:, None, None, :] ^ h_ref[None, :, :, :]).sum(-1, dtype=np.int32).min(-1)
        ii, jj = np.nonzero(d <= max_dist)
        ii = ii + s
        if same:
            keep = ii < jj
            ii, jj = ii[keep], jj[keep]
        out.append(np.stack([ii, jj], 1))
    return np.concatenate(out)

class DSU:
    """Union-find structure used to merge duplicate photos into groups."""
    def __init__(self, n): self.p, self.size = list(range(n)), [1] * n
    def find(self, x):
        """Return the representative (root) of x's group."""
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]; x = self.p[x]
        return x
    def union(self, a, b, max_size=None):
        """Merge the groups of a and b; refuse if the merged group would exceed max_size."""
        a, b = self.find(a), self.find(b)
        if a == b:
            return True
        if max_size is not None and self.size[a] + self.size[b] > max_size:
            return False
        self.p[b] = a; self.size[a] += self.size[b]
        return True

def group_split(df, test_frac, val_frac, stratum="sub", seed=SEED):
    """Whole groups go to one split; per stratum (crop / class), groups are shuffled and filled to the shares."""
    g = df.groupby("group").agg(s=(stratum, "first"), size=(stratum, "size")).reset_index()
    rng, assign = np.random.default_rng(seed), {}
    for _, d in g.groupby("s"):
        d = d.iloc[rng.permutation(len(d))]
        total, cum = d["size"].sum(), 0
        for grp, size in zip(d.group, d["size"]):
            assign[grp] = "test" if cum < test_frac * total else ("val" if cum < (test_frac + val_frac) * total else "train")
            cum += size
    return df.group.map(assign).to_numpy()

def leaf_group_key(cls, filename):
    """Group key for PlantVillage photos of the same leaf: camera-sequence block or leaf id from the file name."""
    stem = Path(filename).stem.split("___", 1)[-1].strip()
    m = re.match(r"^(.*?)\s+day\s*\d+.*$", stem, re.I)
    if m:
        leaf = re.sub(r"[.]\d+$", "", m.group(1).strip().lower())
        return f"{cls}|{leaf}"
    m = re.match(r"^(.*?)(\d+)(?:\.\d+)?$", stem)
    if m:
        return f"{cls}|{m.group(1).strip().lower()}|{int(m.group(2)) // SEQ_BLOCK}"
    return f"{cls}|{stem.lower()}"

def parse_box(s):
    """Crop box (x1, y1, x2, y2) from a v4 manifest cell, or None."""
    if not isinstance(s, str):
        return None
    nums = re.findall(r"-?\d+(?:\.\d+)?", re.sub(r"np\.\w+\(", "", s))
    return tuple(int(float(n)) for n in nums) if len(nums) == 4 else None

# %% [markdown]
# ## Tomato: the v4 split manifests (all 10 tomato classes)
# Every image keeps its v4 split, so the tomato test images here are exactly the disease test images.

# %%
V4_TOMATO_FOLDERS = ["Tomato___healthy", "Tomato___Early_blight", "Tomato___Late_blight", "Tomato___Leaf_Mold",
                     "Tomato___Septoria_leaf_spot", "Tomato___Bacterial_spot",
                     "Tomato___Tomato_Yellow_Leaf_Curl_Virus", "Tomato___Tomato_mosaic_virus",
                     "Tomato___Target_Spot", "Tomato___Spider_mites Two-spotted_spider_mite"]
tpv = pd.read_csv(V4_PV_MANIFEST)
tpv["path"] = [str(PV_ROOT / V4_TOMATO_FOLDERS[l] / f) for l, f in zip(tpv.label, tpv.file)]
tpv = tpv.assign(box=None, y=0, source="pv", sub=[V4_TOMATO_FOLDERS[l] for l in tpv.label], kind="leaf")
tpd = pd.read_csv(V4_PD_MANIFEST)
tpd["path"] = tpd.path.map(local_path)
tpd["box"] = pd.Series([parse_box(b) for b in tpd.box], dtype=object)
tpd = tpd.assign(y=0, source="pd", sub="tomato")
tomato = pd.concat([tpv[["path", "box", "y", "source", "sub", "kind", "group", "split"]],
                    tpd[["path", "box", "y", "source", "sub", "kind", "group", "split"]]], ignore_index=True)
missing = [p for p in tomato.path.unique() if not os.path.exists(p)]
assert not missing, f"{len(missing)} tomato manifest images not found, e.g. {missing[:3]}"
print("tomato images per source and split:\n", tomato.pivot_table(index="source", columns="split", values="path",
                                                                   aggfunc="count").to_string())

# Hashes of the tomato field photos: other-crop photos that are copies of one of these are dropped below
tomato_pd_paths = sorted(tpd.path.unique())
_, tomato_pd_hashes = profile_paths(tomato_pd_paths)

# %% [markdown]
# ## Other crops in PlantVillage (lab photos), grouped by leaf and split 70 / 15 / 15 per class

# %%
rng = np.random.default_rng(SEED)
rows = []
for cdir in sorted(PV_ROOT.iterdir()):
    if not cdir.is_dir() or cdir.name.lower().startswith("tomato"):
        continue
    files = sorted(f for f in cdir.iterdir() if f.suffix.lower() in IMG_EXT)
    if len(files) > PV_OTHER_PER_CLASS:
        files = [files[i] for i in sorted(rng.choice(len(files), PV_OTHER_PER_CLASS, replace=False))]
    rows += [dict(path=str(f), file=f.name, cls=cdir.name) for f in files]
opv = pd.DataFrame(rows)
prof, opv_hashes = profile_paths(opv.path.tolist())
opv = pd.concat([opv, prof], axis=1)
ok = opv.ok.to_numpy(bool)
opv, opv_hashes = opv[ok].reset_index(drop=True), opv_hashes[ok]
dsu = DSU(len(opv))
first_of_key = {}
for i, k in enumerate(leaf_group_key(c, f) for c, f in zip(opv.cls, opv.file)):
    dsu.union(first_of_key.setdefault(k, i), i)
for i, j in near_duplicate_pairs(opv_hashes, opv_hashes, HASH_MAX_DIST, same=True):
    dsu.union(int(i), int(j), MAX_GROUP_SIZE)
opv = opv.assign(group=[f"opv{dsu.find(i)}" for i in range(len(opv))], box=None, y=1, source="pv", sub=opv.cls,
                 kind="leaf")
opv["split"] = group_split(opv, PV_TEST_FRAC, PV_VAL_FRAC)
print(f"PlantVillage other crops: {len(opv)} images, {opv['sub'].nunique()} classes, "
      f"crops: {sorted(set(map(crop_of, opv['sub'])))}")

# %% [markdown]
# ## Other crops in PlantDoc (field photos): both Kaggle copies, leaf crops from the boxes + full photos
# Photos with any tomato box or folder are left out; copies of a photo stay in one group; photos that are
# near-copies of a PlantVillage photo or of a tomato field photo are dropped.

# %%
pd_images = []
if PD_DET_ROOT is not None:
    other_ids = {i: n for i, n in PD_DET_NAMES.items() if not norm_name(n).startswith("tomato")}
    for img_path in sorted((PD_DET_ROOT / "images").rglob("*")):
        if img_path.suffix.lower() not in IMG_EXT:
            continue
        lbl = Path(str(img_path).replace(f"{os.sep}images{os.sep}", f"{os.sep}labels{os.sep}")).with_suffix(".txt")
        if not lbl.exists():
            continue
        boxes, has_tomato = [], False
        for line in open(lbl).read().splitlines():
            p = line.split()
            if len(p) < 5:
                continue
            cid = int(float(p[0]))
            if cid in other_ids:
                boxes.append((other_ids[cid], tuple(map(float, p[1:5]))))
            else:
                has_tomato = True
        if boxes:
            pd_images.append(dict(path=str(img_path), source_copy="det", folder=None, yolo=boxes, has_tomato=has_tomato))
if PD_CLS_ROOT is not None:
    for split_dir in sorted(d for d in PD_CLS_ROOT.iterdir() if d.is_dir()):
        for cdir in sorted(split_dir.iterdir()):
            if cdir.is_dir():
                is_tomato = norm_name(cdir.name).startswith("tomato")
                pd_images += [dict(path=str(f), source_copy="cls", folder=cdir.name, yolo=[], has_tomato=is_tomato)
                              for f in sorted(cdir.iterdir()) if f.suffix.lower() in IMG_EXT]
pdi = pd.DataFrame(pd_images)
prof, pd_hashes = profile_paths(pdi.path.tolist())
pdi = pd.concat([pdi, prof], axis=1)
ok = pdi.ok.to_numpy(bool)
pdi, pd_hashes = pdi[ok].reset_index(drop=True), pd_hashes[ok]
dsu = DSU(len(pdi))
for i, j in near_duplicate_pairs(pd_hashes, pd_hashes, HASH_MAX_DIST, same=True):
    dsu.union(int(i), int(j), MAX_GROUP_SIZE)
roots = [dsu.find(i) for i in range(len(pdi))]
first_path = pdi.groupby(pd.Series(roots)).path.min()
pdi["group"] = ["opd:" + first_path[r] for r in roots]
# a group is dropped if any copy shows tomato, or if it is a near-copy of a PlantVillage or tomato field photo
drop = set(pdi.group[pdi.has_tomato])
for ref, dist in ((opv_hashes, PLANTDOC_LEAK_DIST), (tomato_pd_hashes, HASH_MAX_DIST)):
    hits = near_duplicate_pairs(pd_hashes, ref, dist)
    drop |= set(pdi.group.iloc[np.unique(hits[:, 0])]) if len(hits) else set()
pdi = pdi[~pdi.group.isin(drop)].reset_index(drop=True)
print(f"PlantDoc other-crop photos: {pdi.group.nunique()} unique (dropped groups: {len(drop)})")

pd_rows = []
for g, d in pdi.groupby("group", sort=True):
    det = d[d.source_copy == "det"]
    if len(det):
        r0 = det.iloc[0]
        W, H = r0.width, r0.height
        for name, (cx, cy, w, h) in r0.yolo:
            box = (max(0, round((cx - w / 2) * W)), max(0, round((cy - h / 2) * H)),
                   min(W, round((cx + w / 2) * W)), min(H, round((cy + h / 2) * H)))
            if min(box[2] - box[0], box[3] - box[1]) >= MIN_CROP_SIDE:
                pd_rows.append(dict(path=r0.path, box=box, sub=crop_of(name), kind="crop", group=g))
    rep = d[d.source_copy == "cls"].iloc[0] if (d.source_copy == "cls").any() else det.iloc[0]
    name = rep.folder if isinstance(rep.folder, str) else rep.yolo[0][0]
    pd_rows.append(dict(path=rep.path, box=None, sub=crop_of(name), kind="full", group=g))
opd = pd.DataFrame(pd_rows).assign(y=1, source="pd")
opd["split"] = group_split(opd, PD_TEST_FRAC, PD_VAL_FRAC)
assert (opd.groupby("group").split.nunique() == 1).all()
print("PlantDoc other crops (rows per crop and split):\n",
      opd.pivot_table(index="sub", columns="split", values="path", aggfunc="count").fillna(0).astype(int).to_string())

# %% [markdown]
# ## IP102 insect photos (official trainval / test split) and Natural Images

# %%
parts = []
if IP_ROOT is not None:
    def ids_of(name):
        """Image ids listed in an IP102 split file."""
        return [l.strip() for l in open(IP_SPLITS[name])] if name in IP_SPLITS else []
    def jpg(i):
        """Path of an IP102 image id (the files use several extensions)."""
        for ext in (".jpg", ".jpeg", ".png", ".JPG"):
            p = IP_ROOT / "JPEGImages" / f"{i}{ext}"
            if p.exists():
                return str(p)
        return None
    tv, te = ids_of("trainval.txt"), ids_of("test.txt")
    n_te = min(len(te), int(IP102_MAX * 0.25))
    te = [te[i] for i in rng.choice(len(te), n_te, replace=False)] if te else []
    tv = [tv[i] for i in rng.choice(len(tv), min(len(tv), IP102_MAX - n_te), replace=False)] if tv else []
    ip_rows = [dict(path=jpg(i), split="test") for i in te]
    n_val = int(len(tv) * OTHER_VAL_FRAC / (1 - OTHER_TEST_FRAC))
    ip_rows += [dict(path=jpg(i), split="val" if k < n_val else "train") for k, i in enumerate(tv)]
    ip = pd.DataFrame([r for r in ip_rows if r["path"]])
    parts.append(ip.assign(box=None, y=1, source="ip102", sub="insect", kind="photo", group=ip.path))
if NAT_ROOT is not None:
    nat = pd.DataFrame([dict(path=str(f), sub=c.name) for c in sorted(NAT_ROOT.iterdir()) if c.is_dir()
                        for f in sorted(c.iterdir()) if f.suffix.lower() in IMG_EXT])
    nat = nat.iloc[rng.choice(len(nat), min(len(nat), NATURAL_MAX), replace=False)].reset_index(drop=True)
    nat = nat.assign(box=None, y=1, source="natural", kind="photo", group=nat.path)
    nat["split"] = group_split(nat, OTHER_TEST_FRAC, OTHER_VAL_FRAC)
    parts.append(nat)

# %% [markdown]
# ## v2: chilli, brinjal and bell pepper leaves ("solanaceae" source; crops balanced inside it)
# Chilli keeps the dataset's own test folder as test; its train / valid photos are split 85 / 15 by original photo
# name. Brinjal and bell pepper are split like the other sources. Copies of one photo (pHash, rotations included)
# form one group; a chilli training photo that is a near-copy of a chilli test photo is dropped (the dataset has the
# same photo under different names). Every image here is also checked against the tomato field photos.

# %%
def chili_original(stem):
    """Original photo name before Roboflow augmentation ('ulat--12-_jpg.rf.<hash>' -> 'ulat--12-')."""
    return re.sub(r"_(jpe?g|png|JPE?G|PNG)\.rf\.[0-9a-fA-F]+$", "", stem)

extra_rows = []
if CHILI_ROOT is not None:
    for folder, split in (("train", None), ("valid", None), ("val", None), ("test", "test")):
        for f in images_below(CHILI_ROOT / folder / "images") if (CHILI_ROOT / folder / "images").is_dir() else []:
            orig = chili_original(Path(f).stem)
            sp = split or ("val" if int(hashlib.md5(orig.encode()).hexdigest(), 16) % 100 < 15 else "train")
            extra_rows.append(dict(path=f, sub="chilli", split=sp, group="chili:" + orig))
if EGGPLANT_ROOT is not None:
    # original photos only: the dataset also ships augmented copies of the same photos
    for f in images_below(EGGPLANT_ROOT, lambda q: "augment" not in q):
        extra_rows.append(dict(path=f, sub="brinjal", split=None, group=None))
if SOLANACEAE_ROOT is not None:
    for sub_dir in sorted(SOLANACEAE_ROOT.iterdir()):
        name = sub_dir.name.lower()
        if not sub_dir.is_dir() or name.startswith("tomato"):
            continue   # the tomato folder of this dataset is not used
        crop = "brinjal" if "brinjal" in name else "pepper" if "pepper" in name else None
        if crop:
            extra_rows += [dict(path=f, sub=crop, split=None, group=None) for f in images_below(sub_dir)]
ext = pd.DataFrame(extra_rows, columns=["path", "sub", "split", "group"])
if len(ext):
    # cap per crop (chilli: training share first; its test folder is kept whole)
    keep = []
    for crop, d in ext.groupby("sub"):
        test_part = d[d.split == "test"]
        rest = d[d.split != "test"]
        n = max(0, EXTRA_MAX_PER_CROP - len(test_part)) if crop == "chilli" else EXTRA_MAX_PER_CROP
        keep.append(pd.concat([test_part, rest.iloc[rng.choice(len(rest), min(len(rest), n), replace=False)]]))
    ext = pd.concat(keep).reset_index(drop=True)
    prof, ext_hashes = profile_paths(ext.path.tolist())
    ok = prof.ok.to_numpy(bool)
    ext, ext_hashes = ext[ok].reset_index(drop=True), ext_hashes[ok]
    dsu = DSU(len(ext))
    subs = ext["sub"].to_numpy()
    for i, j in near_duplicate_pairs(ext_hashes, ext_hashes, HASH_MAX_DIST, same=True):
        if subs[i] == subs[j]:   # copies are merged within one crop only
            dsu.union(int(i), int(j), MAX_GROUP_SIZE)
    roots = [dsu.find(i) for i in range(len(ext))]
    ext["group"] = [f"ext{r}" for r in roots]
    is_chili = (ext["sub"] == "chilli").to_numpy()
    # chilli: one split per group of copies - test if any copy is in the dataset's test folder (this removes
    # near-copies of test photos from training), else val if any copy is val, else train
    rank = {"test": 2, "val": 1, "train": 0}
    chili_split = ext[is_chili].groupby("group").split.agg(lambda v: max(v, key=lambda x: rank[x]))
    ext.loc[is_chili, "split"] = ext.loc[is_chili, "group"].map(chili_split)
    # brinjal / bell pepper: group split per crop, like the other sources
    if (~is_chili).any():
        ext.loc[~is_chili, "split"] = group_split(ext[~is_chili], OTHER_TEST_FRAC, OTHER_VAL_FRAC)
    # never a copy of a tomato field photo
    hits = near_duplicate_pairs(ext_hashes, tomato_pd_hashes, HASH_MAX_DIST)
    if len(hits):
        ext = ext.drop(index=np.unique(hits[:, 0])).reset_index(drop=True)
    assert (ext.groupby("group").split.nunique() == 1).all()
    parts.append(ext.assign(box=None, y=1, source="solanaceae", kind="photo"))
    print("v2 chilli / brinjal / pepper:\n", ext.pivot_table(index="sub", columns="split", values="path",
                                                             aggfunc="count").fillna(0).astype(int).to_string())

cols = ["path", "box", "y", "source", "sub", "kind", "group", "split"]
data = pd.concat([tomato[cols], opv[cols], opd[cols]] + [p[cols] for p in parts], ignore_index=True)
data["box"] = pd.Series(list(data.box), dtype=object)
summary = data.pivot_table(index=["y", "source"], columns="split", values="path", aggfunc="count").fillna(0).astype(int)
print(summary.to_string())
data.drop(columns=["box"]).assign(box=data.box.astype(str)).to_csv(WORK_DIR / "leaf_check_split_manifest.csv",
                                                                   index=False)

# %% [markdown]
# ## Augmentation (training only, in memory) and data loading
# As the disease model, plus stronger colour changes: the question here is "which plant", not "which disease".

# %%
train_tf = A.Compose([
    A.RandomResizedCrop(size=(IMG_SIZE, IMG_SIZE), scale=(0.4, 1.0), ratio=(0.75, 1.333), p=1.0),
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.5),
    A.Rotate(limit=180, border_mode=cv2.BORDER_REFLECT_101, p=0.8),
    A.Perspective(scale=(0.02, 0.08), p=0.3),
    A.OneOf([
        A.RandomBrightnessContrast(brightness_limit=0.35, contrast_limit=0.30, p=1.0),
        A.RandomGamma(gamma_limit=(70, 150), p=1.0),
    ], p=0.8),
    A.PlanckianJitter(mode="blackbody", temperature_limit=(3500, 10000), p=0.3),
    A.HueSaturationValue(hue_shift_limit=8, sat_shift_limit=30, val_shift_limit=20, p=0.5),
    A.OneOf([A.MotionBlur(blur_limit=(3, 9), p=1.0), A.GaussianBlur(blur_limit=(3, 7), p=1.0)], p=0.3),
    A.GaussNoise(std_range=(0.02, 0.08), p=0.2),
    A.Downscale(scale_range=(0.4, 0.8), p=0.2),
    A.ImageCompression(quality_range=(30, 90), p=0.4),
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

class PhotoDataset(Dataset):
    """Reads the original file on every access (optional crop box)."""
    def __init__(self, df, transform):
        self.paths, self.boxes = df.path.tolist(), df.box.tolist()
        self.labels = df.y.to_numpy(np.int64)
        self.transform = transform
    def __len__(self):
        return len(self.paths)
    def __getitem__(self, i):
        """Return (transformed image tensor, label) for image i."""
        return self.transform(image=load_rgb(self.paths[i], self.boxes[i]))["image"], self.labels[i]

def seed_worker(_):
    """DataLoader worker init: own random seeds per worker, including the albumentations RNG."""
    info = torch.utils.data.get_worker_info()
    seed = info.seed % 2**32
    random.seed(seed); np.random.seed(seed)
    if hasattr(info.dataset.transform, "set_random_seed"):
        info.dataset.transform.set_random_seed(seed)

def make_loader(ds, sampler=None):
    """DataLoader; training loaders sample and drop the last incomplete batch."""
    train = sampler is not None
    return DataLoader(ds, batch_size=BATCH, sampler=sampler, shuffle=False, drop_last=train, num_workers=NUM_WORKERS,
                      pin_memory=USE_AMP, worker_init_fn=seed_worker, persistent_workers=train and NUM_WORKERS > 0)

def sample_weights(df):
    """Per-image sampling weights: each (class, source) gets its SAMPLE_SHARE; sub-classes balanced inside it."""
    w = np.zeros(len(df))
    shares = {k: v for k, v in SAMPLE_SHARE.items() if ((df.y == CLASS_NAMES.index(k[0])) & (df.source == k[1])).any()}
    norm = sum(shares.values())
    for (cls, src), share in shares.items():
        m = ((df.y == CLASS_NAMES.index(cls)) & (df.source == src)).to_numpy()
        counts = df["sub"][m].value_counts()
        w[m] = share / norm / (len(counts) * df["sub"][m].map(counts).to_numpy())
    return w / w.sum()

# %% [markdown]
# ## Training (EMA weights, cosine schedule); checkpoint chosen by validation balanced accuracy at 0.5

# %%
def build_model(arch):
    """ImageNet-pretrained backbone with a new 2-class output layer."""
    if arch == "mobilenet_v3_small":
        m = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
        m.classifier[3] = nn.Linear(m.classifier[3].in_features, len(CLASS_NAMES))
    elif arch == "efficientnet_b0":
        m = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, len(CLASS_NAMES))
    else:
        raise ValueError(arch)
    return m

@torch.no_grad()
def predict_other(model, df):
    """P(other) for every row of df."""
    model.eval(); out = []
    for x, _ in make_loader(PhotoDataset(df, eval_tf)):
        with torch.autocast(device_type=DEVICE.type, dtype=torch.float16, enabled=USE_AMP):
            out.append(torch.softmax(model(x.to(DEVICE)).float(), 1)[:, 1].cpu().numpy())
    return np.concatenate(out) if out else np.zeros(0)

def val_score(df, p):
    """Mean of: tomato accepted (field), tomato accepted (lab), other rejected - at threshold 0.5."""
    t = df.y.to_numpy() == 0
    parts = [((p < 0.5) & t & (df.source == "pd").to_numpy()).sum() / max(1, (t & (df.source == "pd")).sum()),
             ((p < 0.5) & t & (df.source == "pv").to_numpy()).sum() / max(1, (t & (df.source == "pv")).sum()),
             ((p >= 0.5) & ~t).sum() / max(1, (~t).sum())]
    return float(np.mean(parts))

train_df, val_df, test_df = (data[data.split == s].reset_index(drop=True) for s in ("train", "val", "test"))

def train_model(arch, seed=SEED):
    """Train one model; keep the EMA checkpoint with the best validation score."""
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    model = build_model(arch).to(DEVICE)
    ema = torch.optim.swa_utils.AveragedModel(
        model, multi_avg_fn=torch.optim.swa_utils.get_ema_multi_avg_fn(EMA_DECAY), use_buffers=True)
    sampler = WeightedRandomSampler(torch.as_tensor(sample_weights(train_df), dtype=torch.double),
                                    num_samples=EPOCH_SAMPLES, replacement=True,
                                    generator=torch.Generator().manual_seed(seed))
    train_dl = make_loader(PhotoDataset(train_df, train_tf), sampler)
    loss_fn = nn.CrossEntropyLoss(label_smoothing=0.05)
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    total, warm = EPOCHS * len(train_dl), WARMUP_EPOCHS * len(train_dl)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: (s + 1) / warm if s < warm else
                                              0.5 * (1 + math.cos(math.pi * (s - warm) / max(1, total - warm))))
    scaler = torch.amp.GradScaler("cuda", enabled=USE_AMP)
    ckpt, best, bad, history = WORK_DIR / f"{arch}_best.pt", -1.0, 0, []
    for epoch in range(1, EPOCHS + 1):
        t0 = time.time(); model.train(); loss_sum, seen = 0.0, 0
        for x, y in train_dl:
            x, y = x.to(DEVICE, non_blocking=True), y.to(DEVICE, non_blocking=True)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=DEVICE.type, dtype=torch.float16, enabled=USE_AMP):
                loss = loss_fn(model(x), y)
            scaler.scale(loss).backward(); scaler.step(opt); scaler.update(); sched.step()
            ema.update_parameters(model)
            loss_sum += loss.item() * len(y); seen += len(y)
        score = val_score(val_df, predict_other(ema.module, val_df))
        history.append(dict(epoch=epoch, train_loss=loss_sum / max(seen, 1), val_score=score,
                            seconds=round(time.time() - t0, 1)))
        print(f"[{arch}] epoch {epoch} loss {history[-1]['train_loss']:.4f} val {score:.4f} "
              f"({history[-1]['seconds']}s)")
        if score > best:
            best, bad = score, 0
            torch.save({"model_state_dict": ema.module.state_dict(), "arch": arch, "class_names": CLASS_NAMES,
                        "img_size": IMG_SIZE, "mean": list(MEAN), "std": list(STD), "epoch": epoch,
                        "val_score": best}, ckpt)
        else:
            bad += 1
            if bad >= PATIENCE:
                break
    pd.DataFrame(history).to_csv(WORK_DIR / f"{arch}_history.csv", index=False)
    model = build_model(arch).to(DEVICE)
    model.load_state_dict(torch.load(ckpt, map_location=DEVICE)["model_state_dict"])
    return model, best

trained = {arch: train_model(arch) for arch in ARCHS}
for arch, (_, s) in trained.items():
    print(f"{arch}: best validation score {s:.4f}")

# %% [markdown]
# ## Threshold on validation, then test results
# Rejection threshold t on P(other): the largest share of other photos rejected while at most
# `MAX_TOMATO_REJECT_VAL` of tomato validation photos are rejected, in the field (PlantDoc) and in the lab
# (PlantVillage) separately. The model is chosen on validation too (rejected-other share at its threshold;
# MobileNetV3-Small when within one point, because it is about 3x faster on the Pi).

# %%
def choose_threshold(df, p):
    """Lowest P(other) threshold that keeps tomato rejection <= MAX_TOMATO_REJECT_VAL in field and lab validation."""
    t_mask = df.y.to_numpy() == 0
    cands = np.unique(np.concatenate([np.linspace(0.05, 0.995, 190), p[t_mask]]))
    for t in cands:
        ok = all(((p >= t) & t_mask & (df.source == s).to_numpy()).sum() <= MAX_TOMATO_REJECT_VAL *
                 max(1, (t_mask & (df.source == s).to_numpy()).sum()) for s in ("pd", "pv"))
        if ok:
            return float(t)
    return 0.995

def rates(df, p, t):
    """Per test subset: share of photos rejected as 'not a tomato leaf'."""
    rows = []
    def add(name, m):
        if m.sum():
            rows.append(dict(subset=name, photos=int(m.sum()), rejected=float((p[m] >= t).mean())))
    tom = df.y.to_numpy() == 0
    for src, kind in (("pv", "leaf"), ("pd", "crop"), ("pd", "full")):
        add(f"tomato {src} {kind}", tom & (df.source == src).to_numpy() & (df.kind == kind).to_numpy())
    oth = ~tom
    add("other: all", oth)
    for src in ("pv", "pd", "ip102", "natural", "solanaceae"):
        add(f"other {src}", oth & (df.source == src).to_numpy())
    for crop in ("chilli", "brinjal", "pepper"):   # v2 sources, per crop
        add(f"other v2 {crop}", oth & (df.source == "solanaceae").to_numpy() & (df["sub"] == crop).to_numpy())
    for crop in sorted(set(df["sub"][oth & df.source.isin(["pv", "pd"]).to_numpy()].map(crop_of))):
        add(f"other crop: {crop} (lab + field)",
            oth & df.source.isin(["pv", "pd"]).to_numpy() & (df["sub"].map(crop_of) == crop).to_numpy())
    return pd.DataFrame(rows)

choice = {}
for arch, (model, _) in trained.items():
    pv_ = predict_other(model, val_df)
    t = choose_threshold(val_df, pv_)
    other_rej = float((pv_[val_df.y.to_numpy() == 1] >= t).mean())
    choice[arch] = dict(threshold=t, val_other_rejected=other_rej)
    print(f"{arch}: threshold {t:.3f}, validation other rejected {other_rej:.3f}")
best_arch = max(choice, key=lambda a: choice[a]["val_other_rejected"])
if choice["mobilenet_v3_small"]["val_other_rejected"] >= choice[best_arch]["val_other_rejected"] - 0.01:
    best_arch = "mobilenet_v3_small"
THRESHOLD = choice[best_arch]["threshold"]
model = trained[best_arch][0]
print("chosen:", best_arch, "threshold", THRESHOLD)

p_test = predict_other(model, test_df)
test_rates = rates(test_df, p_test, THRESHOLD)
print(test_rates.to_string(index=False))
test_rates.to_csv(WORK_DIR / "test_rejection_rates.csv", index=False)
test_df.assign(p_other=p_test).drop(columns=["box"]).to_csv(WORK_DIR / "test_predictions.csv", index=False)

# %% [markdown]
# ## Baseline: reject when the v5 disease model's top probability is low (same images, same threshold rule)

# %%
def find_v5_checkpoint():
    """The v5 disease checkpoint (6 classes; v4's has 10 and the same file name)."""
    for p in FILE_INDEX.get("effb0_seed7_best.pt", []) + FILE_INDEX.get("effb0_seed42_best.pt", []):
        ck = torch.load(p, map_location="cpu", weights_only=False)
        if len(ck.get("class_names", [])) == 6:
            return ck, p
    return None, None

baseline = None
ck, ck_path = find_v5_checkpoint()
if ck is not None:
    dm = models.efficientnet_b0()
    dm.classifier[1] = nn.Linear(dm.classifier[1].in_features, len(ck["class_names"]))
    dm.load_state_dict(ck["model_state_dict"]); dm = dm.to(DEVICE).eval()

    @torch.no_grad()
    def disease_low_conf(df):
        """1 - top softmax probability of the disease model (high = unsure = reject)."""
        out = []
        for x, _ in make_loader(PhotoDataset(df, eval_tf)):
            with torch.autocast(device_type=DEVICE.type, dtype=torch.float16, enabled=USE_AMP):
                out.append(1 - torch.softmax(dm(x.to(DEVICE)).float(), 1).max(1).values.cpu().numpy())
        return np.concatenate(out)
    b_t = choose_threshold(val_df, disease_low_conf(val_df))
    baseline = rates(test_df, disease_low_conf(test_df), b_t)
    print(f"baseline (v5 disease model {ck_path}), rejection threshold on 1 - top probability: {b_t:.3f}")
    print(baseline.to_string(index=False))
    baseline.to_csv(WORK_DIR / "baseline_v5_confidence_rates.csv", index=False)
else:
    print("v5 checkpoint not attached: baseline skipped")

# %% [markdown]
# ## ONNX export for the device (FP32) and the specification JSON read by the C++ pipeline

# %%
import onnx, onnxruntime as ort

model_cpu = build_model(best_arch)
model_cpu.load_state_dict(torch.load(WORK_DIR / f"{best_arch}_best.pt", map_location="cpu")["model_state_dict"])
model_cpu.eval()
ONNX_NAME = f"tomato_leaf_check_v2_{'mnv3s' if best_arch == 'mobilenet_v3_small' else 'effb0'}.onnx"
dummy = torch.randn(1, 3, IMG_SIZE, IMG_SIZE)
torch.onnx.export(model_cpu, dummy, WORK_DIR / ONNX_NAME, input_names=["input"], output_names=["logits"],
                  opset_version=17, dynamic_axes=None, dynamo=False)
onnx.checker.check_model(onnx.load(WORK_DIR / ONNX_NAME))
sess = ort.InferenceSession(str(WORK_DIR / ONNX_NAME), providers=["CPUExecutionProvider"])
diff = float(np.abs(sess.run(None, {"input": dummy.numpy()})[0] - model_cpu(dummy).detach().numpy()).max())
print("ONNX vs PyTorch max logit difference:", diff)
assert diff < 1e-3

# Same fields as the disease specification (classes, img_size, mean, std) plus the rejection rule
spec = dict(model=ONNX_NAME, arch=best_arch, classes=CLASS_NAMES, img_size=IMG_SIZE, mean=list(MEAN), std=list(STD),
            input="RGB, direct resize to img_size (bilinear), pixel / 255, (x - mean) / std, NCHW float32",
            reject_class="other", reject_threshold=THRESHOLD,
            rule=f"reject when softmax P(other) >= reject_threshold (chosen on validation: at most "
                 f"{MAX_TOMATO_REJECT_VAL:.0%} of tomato validation photos rejected in field and in lab)",
            test=test_rates.to_dict(orient="records"),
            baseline_v5_confidence=None if baseline is None else baseline.to_dict(orient="records"),
            validation=choice, onnx_vs_pytorch_max_diff=diff)
with open(WORK_DIR / ONNX_NAME.replace(".onnx", ".json"), "w") as f:
    json.dump(spec, f, indent=2)
save_json(dict(summary=summary.reset_index().astype(str).to_dict(orient="records"), chosen=best_arch,
               threshold=THRESHOLD), "results.json")
print("written:", sorted(p.name for p in WORK_DIR.iterdir()))
