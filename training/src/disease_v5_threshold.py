# %% [markdown]
# # KrishiRakshak PS1 - "Uncertain" threshold for the v5 disease model (Kaggle CPU)
#
# The application should not name a disease when the model is unsure; it should say "uncertain - take a clearer
# photo or consult your local KVK". This notebook chooses that confidence threshold for the v5 recommended model
# (six tomato classes) and reports what it costs:
# - **coverage**: share of photos that get an answer,
# - **accuracy when answered**: how often the answer is right,
# both on PlantVillage (lab) and PlantDoc (field) photos.
#
# Rules: the threshold is chosen on the **PlantDoc validation** images only (field photos are what matter; lab
# validation accuracy is close to 100% at any threshold). The test images only report.
# Rule used: the lowest threshold whose accuracy on answered PlantDoc validation photos reaches TARGET_ACCURACY
# (lowest = answer as many photos as possible).
#
# **Kaggle setup:** Accelerator = *None* (CPU), attach `abdallahalidev/plantvillage-dataset`,
# `yusufmurtaza01/plantdoc-object-detection-dataset`, `nirmalsankalana/plantdoc-dataset` and the output of the
# `ps1-tomato-disease-v5` notebook run.

# %%
import json, math, os, re, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch import nn
from torchvision import models

SMOKE = os.environ.get("KR_SMOKE") == "1"
INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "disease_threshold_v5"
WORK_DIR.mkdir(parents=True, exist_ok=True)

TARGET_ACCURACY = 0.85  # required accuracy on answered PlantDoc validation photos
THRESHOLDS = [round(t, 2) for t in np.arange(0.30, 0.951, 0.05)]
DECODE_MIN_SIDE = 336    # same decoding as training
BATCH = 64
PV_FOLDERS = {  # class name -> PlantVillage folder
    "healthy": "Tomato___healthy", "early_blight": "Tomato___Early_blight", "late_blight": "Tomato___Late_blight",
    "leaf_mold": "Tomato___Leaf_Mold", "septoria_leaf_spot": "Tomato___Septoria_leaf_spot",
    "bacterial_spot": "Tomato___Bacterial_spot", "yellow_leaf_curl_virus": "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
    "mosaic_virus": "Tomato___Tomato_mosaic_virus", "target_spot": "Tomato___Target_Spot",
    "spider_mites": "Tomato___Spider_mites Two-spotted_spider_mite",
}
torch.set_num_threads(os.cpu_count())
print("torch", torch.__version__, "| CPU cores", os.cpu_count())

# %% [markdown]
# ## Locate the v5 model, its split manifests and the datasets

# %%
def walk_dirs(root, max_depth=8):
    """os.walk below root up to max_depth, skipping PlantVillage class folders (keeps discovery fast)."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        p = Path(dirpath)
        if len(p.relative_to(root).parts) >= max_depth:
            dirnames[:] = []
        dirnames[:] = sorted(d for d in dirnames if "___" not in d)
        yield p, dirnames, filenames

PV_ROOT, V5_DIR, DATASET_DIRS = None, None, {}
for d, dirs, files in walk_dirs(INPUT_ROOT):
    if PV_ROOT is None and d.name.lower() == "color" and (d / "Tomato___Early_blight").is_dir():
        PV_ROOT = d
    if V5_DIR is None and d.name == "disease_outputs_v5" and "preprocess.json" in files:
        V5_DIR = d
    for name in ("plantdoc-object-detection-dataset", "plantdoc-dataset"):
        if name in dirs and name not in DATASET_DIRS:
            DATASET_DIRS[name] = d / name
assert PV_ROOT is not None, "attach abdallahalidev/plantvillage-dataset"
assert V5_DIR is not None, "attach the output of the ps1-tomato-disease-v5 notebook"
PREPROCESS = json.load(open(V5_DIR / "preprocess.json"))
CKPT_PATH = V5_DIR / PREPROCESS["recommended_checkpoint"]
print("PlantVillage:", PV_ROOT, "| v5 outputs:", V5_DIR, "| model:", CKPT_PATH.name)

def local_path(p):
    """Path of a manifest image on this machine (manifests were written on Kaggle)."""
    if os.path.exists(p):
        return p
    for name, root in DATASET_DIRS.items():
        if f"/{name}/" in p:
            return str(root / p.split(f"/{name}/", 1)[1])
    return p

def parse_box(s):
    """Crop box (x1, y1, x2, y2) from a manifest cell, or None (some values are numpy reprs like 'np.int64(150)')."""
    if not isinstance(s, str):
        return None
    nums = re.findall(r"-?\d+(?:\.\d+)?", re.sub(r"np\.\w+\(", "", s))
    assert len(nums) == 4, s
    return tuple(int(float(n)) for n in nums)

# %% [markdown]
# ## Model and data (the v5 manifests: labels are v5 class indices)

# %%
ckpt = torch.load(CKPT_PATH, map_location="cpu", weights_only=True)
CLASS_NAMES = ckpt["class_names"]
build, head = {"efficientnet_b0": (models.efficientnet_b0, 1), "mobilenet_v3_small": (models.mobilenet_v3_small, 3)}[ckpt["arch"]]
model = build(weights=None)
model.classifier[head] = nn.Linear(model.classifier[head].in_features, len(CLASS_NAMES))
model.load_state_dict(ckpt["model_state_dict"])
model.eval()
MEAN, STD = np.array(ckpt["mean"], np.float32), np.array(ckpt["std"], np.float32)
SIZE = ckpt["img_size"]

pv = pd.read_csv(V5_DIR / "plantvillage_split_manifest.csv")
pv["path"] = [str(PV_ROOT / PV_FOLDERS[CLASS_NAMES[l]] / f) for l, f in zip(pv.label, pv.file)]
pv["box"], pv["kind"] = None, "leaf"
pdm = pd.read_csv(V5_DIR / "plantdoc_split_manifest.csv")
pdm["path"] = pdm.path.map(local_path)
pdm["box"] = pd.Series([parse_box(b) for b in pdm.box], dtype=object)
SETS = {
    "plantdoc_val": pdm[pdm.split == "val"], "plantvillage_val": pv[pv.split == "val"],
    "plantvillage_test": pv[pv.split == "test"],
    "plantdoc_test_leaf_crops": pdm[(pdm.split == "test") & (pdm.kind == "crop")],
    "plantdoc_test_full_images": pdm[(pdm.split == "test") & (pdm.kind == "full")],
}
SETS = {k: v.reset_index(drop=True) for k, v in SETS.items() if len(v)}

def load_rgb(path, box=None):
    """Decode (large JPEGs at reduced scale, never below DECODE_MIN_SIDE for the region used) and crop - as in training."""
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

def preprocess(row):
    """One manifest row -> normalised CHW float32 array (direct resize, ImageNet mean/std)."""
    x = cv2.resize(load_rgb(row[0], row[1]), (SIZE, SIZE), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
    return ((x - MEAN) / STD).transpose(2, 0, 1)

@torch.no_grad()
def probabilities(df):
    """Softmax probabilities of the model for every row of a manifest."""
    out = []
    with ThreadPoolExecutor(8) as ex:
        for s in range(0, len(df), BATCH):
            x = np.stack(list(ex.map(preprocess, zip(df.path[s:s + BATCH], df.box[s:s + BATCH]))))
            out.append(torch.softmax(model(torch.from_numpy(x)), 1).numpy())
    return np.concatenate(out)

t0 = time.time()
PROBS = {k: probabilities(v) for k, v in SETS.items()}
print(f"predicted {sum(len(v) for v in SETS.values())} images in {time.time() - t0:.0f}s")

# %% [markdown]
# ## Coverage vs accuracy, threshold chosen on PlantDoc validation

# %%
def at_threshold(prob, y, t):
    """Coverage and accuracy on answered photos when the top probability must reach t (t=0: always answer)."""
    conf, pred = prob.max(1), prob.argmax(1)
    answered = conf >= t
    diseased = y > 0
    return dict(threshold=t, n=len(y), coverage=float(answered.mean()),
                accuracy_answered=float((pred[answered] == y[answered]).mean()) if answered.any() else np.nan,
                accuracy_all_photos=float((pred == y).mean()),
                # a diseased leaf answered as "healthy" is the worst mistake for a farmer
                missed_disease_answered=float(((pred == 0) & answered & diseased).sum() / max(1, (answered & diseased).sum())))

rows = [dict(eval_set=k, **at_threshold(PROBS[k], SETS[k].label.to_numpy(), t)) for k in SETS for t in [0.0] + THRESHOLDS]
curve = pd.DataFrame(rows)
curve.to_csv(WORK_DIR / "coverage_accuracy_curve.csv", index=False)

val = curve[(curve.eval_set == "plantdoc_val") & (curve.threshold > 0)]
ok = val[val.accuracy_answered >= TARGET_ACCURACY]
THRESHOLD = float(ok.threshold.min()) if len(ok) else float(val.loc[val.accuracy_answered.idxmax(), "threshold"])
print(f"chosen threshold (PlantDoc validation, accuracy when answered >= {TARGET_ACCURACY}): {THRESHOLD}"
      + ("" if len(ok) else "  <-- target not reached; using the most accurate threshold"))
pd.set_option("display.width", 200)
print(val.round(3).to_string(index=False))

report = curve[curve.threshold.isin([0.0, THRESHOLD])].copy()
report["setting"] = np.where(report.threshold == 0, "always answer", "with uncertain threshold")
print(report[["eval_set", "setting", "n", "coverage", "accuracy_answered", "missed_disease_answered"]].round(3).to_string(index=False))

# Per class on the field test: how often each disease gets an answer, and how often that answer is right
per_class = []
for k in ("plantdoc_test_leaf_crops", "plantdoc_test_full_images", "plantvillage_test"):
    if k not in SETS:
        continue
    y, p = SETS[k].label.to_numpy(), PROBS[k]
    answered, pred = p.max(1) >= THRESHOLD, p.argmax(1)
    for i, c in enumerate(CLASS_NAMES):
        m = y == i
        if m.any():
            per_class.append(dict(eval_set=k, cls=c, n=int(m.sum()), recall_always_answer=float((pred[m] == i).mean()),
                                  coverage=float(answered[m].mean()),
                                  accuracy_answered=float((pred[m & answered] == i).mean()) if (m & answered).any() else np.nan))
per_class = pd.DataFrame(per_class)
per_class.to_csv(WORK_DIR / "per_class_at_threshold.csv", index=False)
print(per_class.round(3).to_string(index=False))

json.dump({"model": CKPT_PATH.name, "classes": CLASS_NAMES, "threshold": THRESHOLD, "target_accuracy": TARGET_ACCURACY,
           "chosen_on": "plantdoc_val", "rule": "answer only if the top softmax probability >= threshold, otherwise "
           "report 'uncertain - take a clearer photo or consult your local KVK'",
           "summary": report.drop(columns=["setting"]).to_dict(orient="records")},
          open(WORK_DIR / "threshold.json", "w"), indent=2)
print(sorted(p.name for p in WORK_DIR.iterdir()))
