# %% [markdown]
# # KrishiRakshak PS1 - INT8 post-training quantization (PTQ) of the vision models (Kaggle CPU)
#
# Converts the trained FP32 models to INT8 with ONNX Runtime static quantization and measures what is lost:
# - **Tomato disease classifiers**: v5 six-class EfficientNet-B0 (the Phase 1 demo model) and MobileNetV3-Small (the
#   small fallback), and the v4 ten-class EfficientNet-B0 (extended coverage): accuracy, macro F1, per-class recall
#   and missed-disease rate on PlantVillage test (lab photos) and on PlantDoc test leaf crops and full photos (field).
# - **IP102 pest detector** (YOLOv8n fine-tuned with insect-free leaves): mAP50, pest-found rate, species accuracy and
#   false alarms on insect-free tomato leaves.
#
# Same rules as training: calibration images come from the **training** split, the calibration method is chosen on
# the **validation** split, and the **test** split only reports. The splits are the ones used for training: the
# disease split manifests saved by the v4 notebook (v5 used the same manifests filtered to its six classes, so
# filtering by each model's class names reproduces its splits), and the pest splits re-created with the identical
# code and seed of the fine-tuning notebook. The FP32 test numbers here must therefore equal the published ones (checked below).
#
# Quantization settings: QDQ format, INT8 weights (per output channel) and INT8 activations (S8S8, the ONNX Runtime
# default and the recommended choice for Arm CPUs). Calibration methods compared: MinMax and Percentile (99.999).
#
# Mixed precision for the classifiers: fully INT8 EfficientNet-B0 lost ~9 points of accuracy and fully INT8
# MobileNetV3-Small collapsed (agreement with FP32 ~12%). A per-block sensitivity test (quantize one block at a time,
# measured on PlantDoc *training* photos) showed the damage comes from a few early blocks: EfficientNet-B0 blocks 0-3,
# MobileNetV3-Small blocks 1 and 4 and its hard-swish activations. Keeping those in FP32 restored FP32 accuracy on
# that diagnostic set while the file stays ~3x smaller (most weights sit in the later blocks). The candidate block
# sets below come from that test; the final choice among them is made on validation, as always.
# In the pest detector the box decoding at the end of the head always stays in FP32:
# it joins box coordinates (0-640 px) and class scores (0-1) into one tensor, and a single INT8 scale for both would
# erase the scores.
#
# Size, RAM and latency are measured separately with `tools/bench_onnx.py` (on the Raspberry Pi 5 for the
# deployment numbers); this notebook measures accuracy.
#
# **Kaggle setup:** Accelerator = *None* (CPU), Internet = on, attach `abdallahalidev/plantvillage-dataset`,
# `yusufmurtaza01/plantdoc-object-detection-dataset`, `nirmalsankalana/plantdoc-dataset`, `parserpixy/ip102-dataset`,
# and the outputs of the `ps1-tomato-disease-v4`, `ps1-tomato-disease-v5` and `ps1-ip102-pest-negft` notebook runs
# (weights and split files).

# %%
import os, sys, subprocess

ON_KAGGLE = os.path.exists("/kaggle/input")
SMOKE = os.environ.get("KR_SMOKE") == "1"  # tiny local test run
os.environ.setdefault("WANDB_MODE", "disabled")
if ON_KAGGLE:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "ultralytics==8.4.7", "onnx==1.20.1",
                    "onnxruntime==1.23.2"], check=True)

# %%
import hashlib, json, math, random, re, shutil, time
import xml.etree.ElementTree as ET
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import onnx
import onnxruntime as ort
import pandas as pd
import torch
import yaml
from onnxruntime.quantization import CalibrationDataReader, CalibrationMethod, QuantFormat, QuantType, quantize_static
from onnxruntime.quantization.shape_inference import quant_pre_process
from PIL import Image
from sklearn.metrics import f1_score
from torch import nn
from torchvision import models
import ultralytics
from ultralytics import YOLO, settings as yolo_settings
from ultralytics.data.augment import LetterBox

for key in ("wandb", "mlflow", "comet", "clearml", "dvc", "neptune", "raytune", "tensorboard"):
    try:
        yolo_settings.update({key: False})
    except Exception:
        pass
print("torch", torch.__version__, "| onnx", onnx.__version__, "| onnxruntime", ort.__version__,
      "| ultralytics", ultralytics.__version__, "| CPU cores", os.cpu_count())

# %% [markdown]
# ## Configuration

# %%
SEED = 42
INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "int8_outputs"
TMP_DIR = (Path("/tmp") if ON_KAGGLE else WORK_DIR) / "int8_tmp"  # candidate models; not kept as output
WORK_DIR.mkdir(parents=True, exist_ok=True); TMP_DIR.mkdir(parents=True, exist_ok=True)

# Calibration: counts must be multiples of CALIB_CHUNK (activations are collected chunk by chunk to bound RAM)
CALIB_CHUNK = 8 if SMOKE else 16
CALIB_DISEASE_PER_DOMAIN = 8 if SMOKE else 192  # per model: PlantVillage + PlantDoc training images (lab and field)
CALIB_POOL_PER_DOMAIN = 24 if SMOKE else 400     # training images loaded once; each model takes those of its classes
CALIB_PEST_IP102 = 8 if SMOKE else 304           # IP102 training images ...
CALIB_PEST_NEG = 8 if SMOKE else 96              # ... plus insect-free training leaves (the device sees both)
DISEASE_METHODS = ["minmax", "percentile"]
# Blocks kept in FP32 per architecture (node-name prefixes; "unnamed_" = the hard-swish nodes that ONNX Runtime's
# pre-processing creates without names). An empty list = fully INT8, kept as the reference.
FP32_BLOCK_SETS = {
    "efficientnet_b0": [[], ["features.0", "features.1"], ["features.0", "features.1", "features.3"],
                        ["features.0", "features.1", "features.2", "features.3"]],
    "mobilenet_v3_small": [[], ["features.0", "features.1", "features.4", "unnamed_"],
                           ["features.0", "features.1", "features.2", "features.4", "unnamed_"]],
}
PEST_METHODS = ["minmax", "percentile"]          # entropy search over YOLO's large activation maps is very slow
METHODS = {"minmax": CalibrationMethod.MinMax, "percentile": CalibrationMethod.Percentile}
EVAL_BATCH = 64

# Disease (same values as the v4 training notebook)
IMG_SIZE = 224
DECODE_MIN_SIDE = 336
TOMATO_CLASSES = {  # label index of the v4 manifests -> PlantVillage folder
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
# output name -> (training notebook output folder, checkpoint file names; "recommended" = the one named in the
# folder's preprocess.json). The class list of each model is read from its checkpoint.
DISEASE_MODELS = {
    "tomato_disease_v5_effb0_6class": ("disease_outputs_v5", "recommended"),
    "tomato_disease_v5_mnv3s_6class": ("disease_outputs_v5", ["mnv3s_seed42_best.pt"]),
    "tomato_disease_v4_effb0_10class": ("disease_outputs_v4", ["effb0_seed7_best.pt"]),
}

# Pest (same values as the fine-tuning notebook ip102_pest_negft.py)
PEST_NAME = "pest_yolov8n_ip102_negatives"
PEST_WEIGHT_FILES = ["pest_yolov8n_ip102_negatives.pt", "ip102_yolov8n_negft_best.pt"]
PEST_IMG = 640
VAL_FRACTION = 0.10
NEG_EVAL_MAX = 30 if SMOKE else 1000
NEG_PV_TRAIN_MAX = 40 if SMOKE else 3500
NEG_TOMATO_FOLDERS = [f for c, f in TOMATO_CLASSES.items() if c != "spider_mites"]  # mite photos show mites
CONF_GRID = [0.1, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7]
MAX_FALSE_ALARM_RATE = 0.05

# IP102 class names, 0-based (identical to the training notebooks)
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

random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
ORT_OPTS = ort.SessionOptions()
ORT_OPTS.intra_op_num_threads = os.cpu_count()

def save_json(obj, name):
    """Write obj as indented JSON into WORK_DIR (numpy values are converted to plain Python)."""
    with open(WORK_DIR / name, "w") as f:
        json.dump(obj, f, indent=2, default=lambda o: o.item() if hasattr(o, "item") else str(o))

# %% [markdown]
# ## Locate datasets, trained weights and split files

# %%
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def walk_dirs(root, max_depth=8):
    """os.walk below root up to max_depth, skipping the large image folders that never need searching."""
    root = Path(root)
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        p = Path(dirpath)
        if len(p.relative_to(root).parts) >= max_depth or p.name in ("Annotations", "JPEGImages"):
            dirnames[:] = []
        dirnames[:] = sorted(d for d in dirnames if "___" not in d)  # don't list PlantVillage class folders
        yield p, dirnames, filenames

ALL_FILES = [d / f for d, _, files in walk_dirs(INPUT_ROOT) for f in files if f.endswith((".csv", ".pt", ".json"))]

def find_file(names, folder=None):
    """First file under INPUT_ROOT named one of names (in the order given), optionally only inside a folder of that
    name (the v4 and v5 outputs use the same file names), or None."""
    for n in names:
        for p in ALL_FILES:
            if p.name == n and (folder is None or p.parent.name == folder):
                return p
    return None

def disease_checkpoint(folder, names):
    """Checkpoint of one disease model; "recommended" reads the file name from the folder's preprocess.json."""
    if names == "recommended":
        pre = find_file(["preprocess.json"], folder)
        names = [json.load(open(pre))["recommended_checkpoint"]] if pre else []
    return find_file(names, folder)

def find_plantvillage_color():
    """Return the PlantVillage 'color' folder (the variant that contains the tomato class folders)."""
    for d, _, _ in walk_dirs(INPUT_ROOT):
        if d.name.lower() == "color" and (d / "Tomato___Early_blight").is_dir():
            return d
    raise FileNotFoundError("PlantVillage 'color' folder not found - attach abdallahalidev/plantvillage-dataset")

def find_plantdoc_classification():
    """Return the PlantDoc copy that is organised as train/ and test/ class folders."""
    for d, dirs, _ in walk_dirs(INPUT_ROOT):
        if "test" in dirs and "train" in dirs:
            if any(re.sub(r"[\s_]+", " ", c).strip().lower() == "tomato early blight leaf" for c in os.listdir(d / "test")):
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
    raise FileNotFoundError("IP102 VOC folders (Annotations/, JPEGImages/) not found - attach parserpixy/ip102-dataset")

PV_ROOT = find_plantvillage_color()
PD_CLS_ROOT = find_plantdoc_classification()
IP_ROOT, IP_SPLITS = find_ip102()
PV_MANIFEST = find_file(["plantvillage_split_manifest.csv"], "disease_outputs_v4")
PD_MANIFEST = find_file(["plantdoc_split_manifest.csv"], "disease_outputs_v4")
DISEASE_WEIGHTS = {k: disease_checkpoint(folder, names) for k, (folder, names) in DISEASE_MODELS.items()}
PEST_WEIGHTS = find_file(PEST_WEIGHT_FILES)
for name, value in [("PlantVillage color", PV_ROOT), ("PlantDoc folders", PD_CLS_ROOT), ("IP102", IP_ROOT),
                    ("v4 PlantVillage manifest", PV_MANIFEST), ("v4 PlantDoc manifest", PD_MANIFEST),
                    ("pest weights", PEST_WEIGHTS)] + list(DISEASE_WEIGHTS.items()):
    print(f"{name:34s}: {value}")
missing = [n for n, v in [("plantvillage_split_manifest.csv", PV_MANIFEST), ("plantdoc_split_manifest.csv", PD_MANIFEST),
                          ("pest weights", PEST_WEIGHTS)] + list(DISEASE_WEIGHTS.items()) if v is None]
if missing:
    raise FileNotFoundError(f"missing inputs: {missing} - attach the ps1-tomato-disease-v4, ps1-tomato-disease-v5 "
                            "and ps1-ip102-pest-negft outputs")

# %% [markdown]
# ## Shared quantization helpers

# %%
class ArrayReader(CalibrationDataReader):
    """Feeds calibration images one at a time. ONNX Runtime asks for one chunk at a time (set_range), so only one
    chunk of intermediate activations is held in memory (all at once needs ~90 MB per image for EfficientNet-B0 and
    ~280 MB per image for YOLOv8n at 640 x 640)."""
    def __init__(self, input_name, items, to_input):
        self.name, self.items, self.to_input = input_name, items, to_input
        self.set_range(0, len(items))
    def __len__(self):
        return len(self.items)
    def set_range(self, start_index, end_index):
        """Restrict the reader to items[start_index:end_index] (called by quantize_static for each chunk)."""
        self.pos, self.end = start_index, end_index
    def get_next(self):
        """Next calibration input as {input name: NCHW float32 array}, or None when the chunk is finished."""
        if self.pos >= self.end:
            return None
        self.pos += 1
        return {self.name: self.to_input(self.items[self.pos - 1])}

def preprocessed(fp32_path):
    """ONNX Runtime's recommended pre-processing before quantization (graph optimisation), cached per model.
    Nodes the pre-processing creates without a name (e.g. the HardSigmoid/Mul pair of hard-swish) get one, so they
    can be kept in FP32 by name."""
    pre = TMP_DIR / (Path(fp32_path).stem + "_pre.onnx")
    if not pre.exists():
        quant_pre_process(str(fp32_path), str(pre), skip_symbolic_shape=True)
        m = onnx.load(str(pre))
        for i, n in enumerate(m.graph.node):
            if not n.name:
                n.name = f"unnamed_{n.op_type}_{i}"
        onnx.save(m, str(pre))
    return pre

def quantize(fp32_path, out_path, items, to_input, method, exclude=()):
    """Static INT8 quantization (QDQ, S8S8, per-channel weights) calibrated on items; returns seconds taken."""
    pre = preprocessed(fp32_path)
    assert len(items) % CALIB_CHUNK == 0, "calibration count must be a multiple of CALIB_CHUNK"
    t0 = time.time()
    quantize_static(str(pre), str(out_path), ArrayReader(onnx.load(str(pre)).graph.input[0].name, items, to_input),
                    quant_format=QuantFormat.QDQ, activation_type=QuantType.QInt8, weight_type=QuantType.QInt8,
                    per_channel=True, calibrate_method=METHODS[method], nodes_to_exclude=list(exclude),
                    extra_options={"CalibStridedMinMax": CALIB_CHUNK})
    return time.time() - t0

def copy_metadata(src, dst):
    """Copy ONNX metadata (Ultralytics stores class names, stride and image size there) onto the quantized model."""
    m_src, m = onnx.load(str(src)), onnx.load(str(dst))
    del m.metadata_props[:]
    m.metadata_props.extend(m_src.metadata_props)
    onnx.save(m, str(dst))

def size_mb(path):
    """File size in MB."""
    return round(Path(path).stat().st_size / 1e6, 2)

# %% [markdown]
# ## Disease classifiers: data (v4 split manifests; each model uses the rows of its own classes)
# Images are loaded once for all ten v4 classes. Calibration: PlantVillage and PlantDoc **training** images in equal
# numbers (lab and field photos look different). Method selection: the training notebooks' validation score = mean of
# PlantVillage and PlantDoc validation macro F1.

# %%
def load_rgb(path, box=None):
    """Decode (large JPEGs at reduced scale, never below DECODE_MIN_SIDE for the region used) and crop - as in v4."""
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

def load_set(df):
    """All images of a manifest resized to IMG_SIZE x IMG_SIZE (uint8 RGB, kept in RAM: 150 KB per image)."""
    def one(row):
        return cv2.resize(load_rgb(row[0], row[1]), (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_LINEAR)
    with ThreadPoolExecutor(8) as ex:
        return np.stack(list(ex.map(one, zip(df.path, df.box))))

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

def parse_box(s):
    """Crop box (x1, y1, x2, y2) from a manifest cell, or None. v4 wrote some values as numpy reprs such as
    'np.int64(150)', so the numbers are extracted rather than evaluated."""
    if not isinstance(s, str):
        return None
    nums = re.findall(r"-?\d+(?:\.\d+)?", re.sub(r"np\.\w+\(", "", s))
    assert len(nums) == 4, s
    return tuple(int(float(n)) for n in nums)

pv = pd.read_csv(PV_MANIFEST)
pv["path"] = [str(PV_ROOT / TOMATO_CLASSES[CLASS_NAMES[l]] / f) for l, f in zip(pv.label, pv.file)]
pv["box"], pv["kind"] = None, "leaf"
pdm = pd.read_csv(PD_MANIFEST)
pdm["path"] = pdm.path.map(local_path)
pdm["box"] = [parse_box(b) for b in pdm.box]
assert all(os.path.exists(p) for p in pd.concat([pv.path, pdm.path])), "manifest images not found"

DISEASE_SETS = {  # name -> manifest rows; the names match the v4 results_summary.csv
    "plantvillage_val": pv[pv.split == "val"], "plantdoc_val": pdm[pdm.split == "val"],
    "plantvillage_test": pv[pv.split == "test"],
    "plantdoc_test_leaf_crops": pdm[(pdm.split == "test") & (pdm.kind == "crop")],
    "plantdoc_test_full_images": pdm[(pdm.split == "test") & (pdm.kind == "full")],
}
if SMOKE:  # the smoke-test manifests may have no full PlantDoc photos in some splits
    DISEASE_SETS = {k: v for k, v in DISEASE_SETS.items() if len(v)}
calib_pool = pd.concat([d[d.split == "train"].sample(min(CALIB_POOL_PER_DOMAIN, (d.split == "train").sum()),
                                                     random_state=SEED).assign(domain=dom)
                        for dom, d in (("pv", pv), ("pd", pdm))])
t0 = time.time()
X = {k: load_set(v) for k, v in DISEASE_SETS.items()}
Y4 = {k: v.label.to_numpy() for k, v in DISEASE_SETS.items()}  # v4 label indices
X_POOL, Y4_POOL, DOMAIN_POOL = load_set(calib_pool), calib_pool.label.to_numpy(), calib_pool.domain.to_numpy()
print(f"loaded in {time.time() - t0:.0f}s:", {k: len(v) for k, v in X.items()}, "| calibration pool:", len(X_POOL))

def model_data(class_names):
    """Image sets, labels (in the model's own class order) and calibration images for a model's classes."""
    keep = [CLASS_NAMES.index(c) for c in class_names]
    remap = np.full(len(CLASS_NAMES), -1); remap[keep] = np.arange(len(keep))
    xs, ys = {}, {}
    for k in X:
        m = np.isin(Y4[k], keep)
        xs[k], ys[k] = X[k][m], remap[Y4[k][m]]
    calib = []
    for dom in ("pv", "pd"):
        idx = np.flatnonzero(np.isin(Y4_POOL, keep) & (DOMAIN_POOL == dom))[:CALIB_DISEASE_PER_DOMAIN]
        assert len(idx) == CALIB_DISEASE_PER_DOMAIN, f"calibration pool too small for {class_names} ({dom})"
        calib += list(X_POOL[idx])
    return xs, ys, calib

# %% [markdown]
# ## Disease classifiers: export FP32 ONNX, quantize with each method, choose on validation

# %%
ARCHITECTURES = {"efficientnet_b0": (models.efficientnet_b0, 1), "mobilenet_v3_small": (models.mobilenet_v3_small, 3)}

def load_disease_model(path):
    """Load a v4 checkpoint (same as tools/predict.py); returns (model, checkpoint dict)."""
    ckpt = torch.load(path, map_location="cpu", weights_only=True)
    build, head_index = ARCHITECTURES[ckpt["arch"]]
    model = build(weights=None)
    model.classifier[head_index] = nn.Linear(model.classifier[head_index].in_features, len(ckpt["class_names"]))
    model.load_state_dict(ckpt["model_state_dict"])
    return model.eval(), ckpt

def to_input(u8, mean, std):
    """uint8 NHWC (or HWC) RGB -> normalised NCHW float32, exactly as in training evaluation."""
    x = (u8.astype(np.float32) / 255.0 - mean) / std
    return np.ascontiguousarray((x[None] if x.ndim == 3 else x).transpose(0, 3, 1, 2))

def onnx_probs(path, u8, mean, std):
    """Softmax probabilities of an ONNX classifier on a uint8 image stack."""
    session = ort.InferenceSession(str(path), ORT_OPTS, providers=["CPUExecutionProvider"])
    out = []
    for i in range(0, len(u8), EVAL_BATCH):
        logits = session.run(None, {"image": to_input(u8[i:i + EVAL_BATCH], mean, std)})[0]
        e = np.exp(logits - logits.max(1, keepdims=True))
        out.append(e / e.sum(1, keepdims=True))
    return np.concatenate(out)

def cls_metrics(y, prob, names):
    """Accuracy, macro F1 (over classes present, as in training), missed-disease rate and recall of every class."""
    pred = prob.argmax(1)
    diseased = y > 0  # index 0 is healthy in every model
    recall = {c: (float((pred[y == i] == i).mean()) if (y == i).any() else np.nan) for i, c in enumerate(names)}
    return dict(n=len(y), accuracy=float((pred == y).mean()),
                macro_f1=float(f1_score(y, pred, average="macro", labels=np.unique(y), zero_division=0)),
                missed_disease_rate=float((pred[diseased] == 0).mean()) if diseased.any() else np.nan,
                recall=recall)

def disease_variants(pre_path, arch):
    """Candidate settings: (variant name, method, nodes kept in FP32, number of FP32 blocks) for every calibration
    method and every FP32 block set of the architecture."""
    node_names = [n.name for n in onnx.load(str(pre_path)).graph.node]
    out = []
    for blocks in FP32_BLOCK_SETS[arch]:
        prefixes = [b if b == "unnamed_" else f"/features/{b}/" for b in blocks]
        exclude = tuple(n for n in node_names if any(n.startswith(p) for p in prefixes))
        label = "int8" if not blocks else "fp32:" + ",".join(b.replace("features.", "f").replace("unnamed_", "hswish") for b in blocks)
        out += [(f"{m}+{label}", m, exclude, len(blocks)) for m in DISEASE_METHODS]
    return out

DISEASE_RESULTS = {}
for name, weights in DISEASE_WEIGHTS.items():
    model, ckpt = load_disease_model(weights)
    names = ckpt["class_names"]
    assert names[0] == "healthy" and set(names) <= set(CLASS_NAMES), names
    Xm, Ym, calib = model_data(names)
    mean, std = np.array(ckpt["mean"], np.float32), np.array(ckpt["std"], np.float32)
    fp32_path = WORK_DIR / f"{name}.onnx"
    torch.onnx.export(model, torch.randn(1, 3, IMG_SIZE, IMG_SIZE), str(fp32_path), input_names=["image"],
                      output_names=["logits"], opset_version=17, dynamo=False,
                      dynamic_axes={"image": {0: "batch"}, "logits": {0: "batch"}})
    with torch.no_grad():  # FP32 ONNX must match PyTorch before anything is compared with it
        x = to_input(Xm["plantdoc_val"][:16], mean, std)
        diff = np.abs(model(torch.from_numpy(x)).numpy()
                      - ort.InferenceSession(str(fp32_path), providers=["CPUExecutionProvider"]).run(None, {"image": x})[0]).max()
    assert diff < 1e-3, f"FP32 ONNX differs from PyTorch by {diff}"
    spec = {"onnx_file": f"{name}_int8.onnx", "fp32_onnx_file": fp32_path.name, "input": "image", "output": "logits",
            "classes": ckpt["class_names"], "img_size": IMG_SIZE, "color_order": "RGB",
            "resize": "direct resize to img_size x img_size, bilinear", "scale": "pixel / 255", "mean": ckpt["mean"],
            "std": ckpt["std"], "layout": "NCHW float32 (the INT8 model quantizes its input internally)",
            "output_meaning": "logits; apply softmax for probabilities"}
    save_json(spec, f"{name}.json")

    fp32 = {k: onnx_probs(fp32_path, v, mean, std) for k, v in Xm.items()}
    rows = []
    for tag, method, exclude, n_fp32 in disease_variants(preprocessed(fp32_path), ckpt["arch"]):
        q_path = TMP_DIR / f"{name}_{tag}.onnx"
        secs = quantize(fp32_path, q_path, calib, lambda u: to_input(u, mean, std), method, exclude)
        val = {k: cls_metrics(Ym[k], onnx_probs(q_path, Xm[k], mean, std), names) for k in Xm if k.endswith("_val")}
        rows.append(dict(model=name, variant=tag, fp32_blocks=n_fp32, size_mb=size_mb(q_path), calib_seconds=round(secs),
                         **{f"{k}_macro_f1": v["macro_f1"] for k, v in val.items()},
                         val_score=float(np.mean([v["macro_f1"] for v in val.values()]))))
        print(f"[{name}] {tag:40s} val score {rows[-1]['val_score']:.4f}  ({secs:.0f}s)")
    fp32_val = float(np.mean([cls_metrics(Ym[k], fp32[k], names)["macro_f1"] for k in Xm if k.endswith("_val")]))
    variants = pd.DataFrame(rows)
    # best validation score; on a tie prefer fewer FP32 blocks (faster on the device)
    best = variants.sort_values(["val_score", "fp32_blocks"], ascending=[False, True]).iloc[0]
    int8_path = WORK_DIR / f"{name}_int8.onnx"
    shutil.copy(TMP_DIR / f"{name}_{best.variant}.onnx", int8_path)
    print(f"[{name}] FP32 val score {fp32_val:.4f} | chosen INT8 variant: {best.variant} ({best.val_score:.4f})")

    int8 = {k: onnx_probs(int8_path, v, mean, std) for k, v in Xm.items()}
    DISEASE_RESULTS[name] = dict(fp32=fp32, int8=int8, y=Ym, names=names, variants=variants, chosen=best.variant,
                                 fp32_val_score=fp32_val, sizes=(size_mb(fp32_path), size_mb(int8_path)),
                                 run=weights.stem.replace("_best", ""), folder=DISEASE_MODELS[name][0])

# %% [markdown]
# ## Disease classifiers: FP32 vs INT8 on the test sets
# Test sets are reported only; nothing above was chosen with them.

# %%
test_rows, recall_rows = [], []
for name, r in DISEASE_RESULTS.items():
    summary_file = find_file(["results_summary.csv"], r["folder"])
    published = pd.read_csv(summary_file) if summary_file is not None else None
    for k in [k for k in r["y"] if not k.endswith("_val")]:
        y = r["y"][k]
        m = {p: cls_metrics(y, r[p][k], r["names"]) for p in ("fp32", "int8")}
        agree = float((r["fp32"][k].argmax(1) == r["int8"][k].argmax(1)).mean())
        for p in ("fp32", "int8"):
            test_rows.append(dict(model=name, eval_set=k, precision=p, variant="fp32" if p == "fp32" else r["chosen"],
                                  size_mb=r["sizes"][p == "int8"], n=m[p]["n"], accuracy=m[p]["accuracy"],
                                  macro_f1=m[p]["macro_f1"], missed_disease_rate=m[p]["missed_disease_rate"],
                                  top1_agreement_with_fp32=agree if p == "int8" else 1.0))
        for i, c in enumerate(r["names"]):
            recall_rows.append(dict(model=name, eval_set=k, cls=c, n=int((y == i).sum()),
                                    recall_fp32=m["fp32"]["recall"][c], recall_int8=m["int8"]["recall"][c],
                                    change=m["int8"]["recall"][c] - m["fp32"]["recall"][c]))
        if published is not None and not SMOKE:  # FP32 ONNX must reproduce the published PyTorch test numbers
            pub = published[(published.eval_set == k) & (published.system == r["run"])]
            if len(pub):
                gap = abs(pub.accuracy.iloc[0] - m["fp32"]["accuracy"])
                # training evaluated with FP16 autocast on the GPU, which flips the odd borderline image
                print(f"{name} {k}: FP32 ONNX accuracy {m['fp32']['accuracy']:.4f} vs published "
                      f"{pub.accuracy.iloc[0]:.4f}" + ("" if gap < 0.01 else "  <-- CHECK: differs"))
disease_test = pd.DataFrame(test_rows)
disease_recall = pd.DataFrame(recall_rows).dropna(subset=["recall_fp32"])
disease_variants_all = pd.concat([r["variants"] for r in DISEASE_RESULTS.values()])
disease_test.to_csv(WORK_DIR / "disease_fp32_vs_int8_test.csv", index=False)
disease_recall.to_csv(WORK_DIR / "disease_per_class_recall.csv", index=False)
disease_variants_all.to_csv(WORK_DIR / "disease_int8_variants_val.csv", index=False)
pd.set_option("display.width", 250)
print(disease_variants_all.round(4).to_string(index=False))
print(disease_test.round(4).to_string(index=False))
print(disease_recall.round(3).to_string(index=False))
del X, X_POOL  # free RAM before the pest detector

# %% [markdown]
# ## Pest detector: re-create the IP102 splits and insect-free leaf sets (identical code and seed to fine-tuning)

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
    """Return (<object> elements, note); repairs files with extra text or a second <annotation> block."""
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
    """Read the image size and all valid boxes (class id, x1, y1, x2, y2) for one IP102 image id; never raises."""
    rec = dict(id=img_id, image=None, width=0, height=0, boxes=[], problems=[])
    try:
        xml_path, img_path = IP_ROOT / "Annotations" / f"{img_id}.xml", find_image(img_id)
        if img_path is None or not xml_path.exists():
            return rec
        with Image.open(img_path) as im:
            W, H = im.size
        rec.update(image=str(img_path), width=W, height=H)
        objects, _ = read_xml_objects(xml_path)
        for obj in objects or []:
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
            if x2 - x1 >= 2 and y2 - y1 >= 2 and (c, x1, y1, x2, y2) not in rec["boxes"]:
                rec["boxes"].append((c, x1, y1, x2, y2))
    except Exception as e:
        rec["problems"].append(str(e))
    return rec

trainval_ids, test_ids = read_ids(IP_SPLITS.get("trainval.txt")), read_ids(IP_SPLITS.get("test.txt"))
with ThreadPoolExecutor(16) as ex:
    recs = {r["id"]: r for r in ex.map(parse_one, sorted(set(trainval_ids) | set(test_ids)))}
usable = {k: r for k, r in recs.items() if r["image"] and r["boxes"]}

def primary_class(r):
    """Most frequent class among the boxes of one annotated image."""
    return Counter(c for c, *_ in r["boxes"]).most_common(1)[0][0]

rng = random.Random(SEED)
tv = [i for i in trainval_ids if i in usable]
te = [i for i in test_ids if i in usable]
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
print({s: len(v) for s, v in SPLITS.items()}, {k: len(v) for k, v in NEG.items()})

# YOLO-format labels for validation and test only (evaluation needs no training set); images are symlinked
YOLO_DIR = TMP_DIR / "ip102_yolo"
shutil.rmtree(YOLO_DIR, ignore_errors=True)
for split in ("val", "test"):
    (YOLO_DIR / "images" / split).mkdir(parents=True); (YOLO_DIR / "labels" / split).mkdir(parents=True)
    for i in SPLITS[split]:
        r = usable[i]; src = Path(r["image"])
        os.symlink(src, YOLO_DIR / "images" / split / src.name)
        W, H = r["width"], r["height"]
        (YOLO_DIR / "labels" / split / f"{src.stem}.txt").write_text("\n".join(
            f"{c} {(x1 + x2) / 2 / W:.6f} {(y1 + y2) / 2 / H:.6f} {(x2 - x1) / W:.6f} {(y2 - y1) / H:.6f}"
            for c, x1, y1, x2, y2 in r["boxes"]) + "\n")
DATA_YAML = YOLO_DIR / "data.yaml"
yaml.safe_dump({"path": str(YOLO_DIR), "train": "images/val", "val": "images/val", "test": "images/test",
                "names": dict(enumerate(IP102_NAMES))}, open(DATA_YAML, "w"), sort_keys=False)

# %% [markdown]
# ## Pest detector: export FP32 ONNX and quantize (box decoding kept in FP32)

# %%
def letterbox_640(path):
    """Square 640 x 640 letterbox (grey 114 padding), RGB, /255, NCHW float32 - the exported model's input."""
    padded = LetterBox(new_shape=(PEST_IMG, PEST_IMG), auto=False)(image=cv2.imread(str(path)))
    return np.ascontiguousarray(padded[..., ::-1].transpose(2, 0, 1)[None], dtype=np.float32) / 255.0

# The exporter writes next to the weights, and attached inputs are read-only on Kaggle: export from a copy
pest_pt = TMP_DIR / f"{PEST_NAME}.pt"
shutil.copy(PEST_WEIGHTS, pest_pt)
exported = Path(YOLO(str(pest_pt)).export(format="onnx", imgsz=PEST_IMG, opset=17, dynamic=False, simplify=False))
PEST_FP32 = WORK_DIR / f"{PEST_NAME}.onnx"
shutil.move(str(exported), PEST_FP32)

# Head decoding: every node of the Detect layer except its convolution branches (cv2 = boxes, cv3 = classes)
pre_graph = onnx.load(str(preprocessed(PEST_FP32))).graph
detect = max({n.name.split("/")[1] for n in pre_graph.node if n.name.startswith("/model.")}, key=lambda s: int(s.split(".")[1]))
PEST_EXCLUDE = [n.name for n in pre_graph.node
                if n.name.startswith(f"/{detect}/") and "/cv2." not in n.name and "/cv3." not in n.name]
print(f"Detect layer {detect}: {len(PEST_EXCLUDE)} decoding nodes kept in FP32")

rng = random.Random(SEED)
pest_calib = rng.sample([usable[i]["image"] for i in SPLITS["train"]], CALIB_PEST_IP102) + rng.sample(NEG["train"], CALIB_PEST_NEG)
pest_calib_u8 = [np.round(letterbox_640(p) * 255).astype(np.uint8) for p in pest_calib]  # 1.2 MB each instead of 4.9
PEST_CANDIDATES = {}
for method in PEST_METHODS:
    q_path = TMP_DIR / f"{PEST_NAME}_{method}.onnx"
    secs = quantize(PEST_FP32, q_path, pest_calib_u8, lambda u: u.astype(np.float32) / 255.0, method, PEST_EXCLUDE)
    copy_metadata(PEST_FP32, q_path)
    PEST_CANDIDATES[method] = q_path
    print(f"[pest] {method}: {size_mb(q_path)} MB, calibrated in {secs:.0f}s")
del pest_calib_u8

# %% [markdown]
# ## Pest detector: evaluation helpers (same definitions as the fine-tuning notebook)

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

def run_predictions(m, paths, conf=0.05):
    """Predictions {image path: (boxes xyxy, scores, classes)}. One image per call: the exported model has a fixed
    batch of 1, and Ultralytics sends a list source as one batch (its batch argument does not change that)."""
    out = {}
    for path in map(str, paths):
        r = m.predict(source=path, conf=conf, imgsz=PEST_IMG, device="cpu", verbose=False)[0]
        b = r.boxes
        out[r.path] = (b.xyxy.cpu().numpy(), b.conf.cpu().numpy(), b.cls.cpu().numpy().astype(int))
    return out

def two_level(preds, split):
    """Per threshold: share of insects found (any species), species accuracy when found, and box precision."""
    preds = {Path(k).stem: v for k, v in preds.items()}  # IP102 image ids are unique
    rows, by_cls = [], {}
    for t in CONF_GRID:
        gt_total = gt_found = species_ok = pred_total = pred_tp = 0
        cls_found, cls_total, cls_ok = Counter(), Counter(), Counter()
        for i in SPLITS[split]:
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
        by_cls[t] = (cls_total, cls_found, cls_ok)
    return pd.DataFrame(rows), by_cls

def false_alarms(m, keys):
    """Per negative set: fraction of insect-free leaf images with any detection at or above each threshold."""
    out = {}
    for k in keys:
        if NEG[k]:
            preds = run_predictions(m, NEG[k])
            max_conf = np.array([v[1].max() if len(v[1]) else 0.0 for v in preds.values()])
            out[f"false_alarm_{k}"] = [float((max_conf >= t).mean()) for t in CONF_GRID]
    return out

def choose_threshold(levels):
    """Lowest confidence with at most MAX_FALSE_ALARM_RATE false alarms on every validation negative set."""
    val_cols = [c for c in levels if c.startswith("false_alarm_val")]
    ok = levels[(levels[val_cols] <= MAX_FALSE_ALARM_RATE).all(axis=1)].conf
    return float(ok.min()) if len(ok) else float(max(CONF_GRID))

def evaluate_pest(path, split):
    """mAP on an IP102 split plus false alarms on that split's negatives; on test also the two-level rates."""
    m = YOLO(str(path), task="detect")
    tm = m.val(data=str(DATA_YAML), split=split, imgsz=PEST_IMG, batch=1, device="cpu", plots=False,
               project=str(TMP_DIR / "runs"), name=f"{Path(path).stem}_{split}", exist_ok=True, verbose=False)
    if split == "test":
        levels, by_cls = two_level(run_predictions(m, [usable[i]["image"] for i in SPLITS["test"]]), "test")
    else:
        levels, by_cls = pd.DataFrame({"conf": CONF_GRID}), None
    for k, v in false_alarms(m, [k for k in NEG if k != "train" and (k.startswith("val") or split == "test")]).items():
        levels[k] = v
    ap50 = dict(zip([int(c) for c in tm.box.ap_class_index], tm.box.ap50))
    return dict(map50=float(tm.box.map50), map50_95=float(tm.box.map), levels=levels, by_cls=by_cls,
                threshold=choose_threshold(levels), ap50=ap50)

# %% [markdown]
# ## Pest detector: choose the calibration method on validation, then compare FP32 and INT8 on test

# %%
t0 = time.time()
pest_val = {"fp32": evaluate_pest(PEST_FP32, "val")}
for method, path in PEST_CANDIDATES.items():
    pest_val[method] = evaluate_pest(path, "val")
pest_val_rows = [dict(variant=k, size_mb=size_mb(PEST_FP32 if k == "fp32" else PEST_CANDIDATES[k]), val_map50=r["map50"],
                      val_map50_95=r["map50_95"], threshold_from_val_negatives=r["threshold"]) for k, r in pest_val.items()]
pest_val_df = pd.DataFrame(pest_val_rows)
pest_val_df.to_csv(WORK_DIR / "pest_int8_variants_val.csv", index=False)
print(pest_val_df.round(4).to_string(index=False), f"\n({(time.time() - t0) / 60:.0f} min)")
PEST_CHOSEN = max(PEST_CANDIDATES, key=lambda k: pest_val[k]["map50"])
PEST_INT8 = WORK_DIR / f"{PEST_NAME}_int8.onnx"
shutil.copy(PEST_CANDIDATES[PEST_CHOSEN], PEST_INT8)
print("chosen INT8 calibration method:", PEST_CHOSEN)

t0 = time.time()
pest_test = {"fp32": evaluate_pest(PEST_FP32, "test"), "int8": evaluate_pest(PEST_INT8, "test")}
print(f"test evaluation took {(time.time() - t0) / 60:.0f} min")
pest_rows = []
for p, r in pest_test.items():
    for label, t in (("at its chosen threshold", r["threshold"]), ("at 0.25", 0.25), ("at 0.5", 0.5)):
        row = r["levels"][r["levels"].conf == t].iloc[0].to_dict()
        pest_rows.append(dict(precision=p, variant="fp32" if p == "fp32" else PEST_CHOSEN,
                              size_mb=size_mb(PEST_FP32 if p == "fp32" else PEST_INT8), setting=label,
                              test_map50=r["map50"], test_map50_95=r["map50_95"], **row))
pest_compare = pd.DataFrame(pest_rows)
pest_compare.to_csv(WORK_DIR / "pest_fp32_vs_int8_test.csv", index=False)
print(pest_compare.round(4).to_string(index=False))

species = []
for c in range(NC):
    row = dict(class_id=c, name=IP102_NAMES[c])
    for p, r in pest_test.items():
        total, found, ok = r["by_cls"][r["threshold"]]
        row.update({f"ap50_{p}": r["ap50"].get(c, np.nan), f"test_boxes": total[c],
                    f"found_rate_{p}": found[c] / total[c] if total[c] else np.nan,
                    f"species_acc_when_found_{p}": ok[c] / found[c] if found[c] else np.nan})
    row["ap50_change"] = row["ap50_int8"] - row["ap50_fp32"]
    species.append(row)
pest_species = pd.DataFrame(species)
pest_species.to_csv(WORK_DIR / "pest_per_species_fp32_vs_int8.csv", index=False)
print("species with the largest AP50 drop:")
print(pest_species.sort_values("ap50_change").head(10).round(3).to_string(index=False))

# %% [markdown]
# ## Save the summary and the device configuration of the INT8 pest detector

# %%
save_json({"onnx_file": PEST_INT8.name, "fp32_onnx_file": PEST_FP32.name, "img_size": PEST_IMG,
           "letterbox": "square 640 x 640, grey (114) padding", "color_order": "RGB", "scale": "pixel / 255",
           "layout": "NCHW float32 (the INT8 model quantizes its input internally)",
           "output": "(1, 106, 8400): 4 box values (cx, cy, w, h) + 102 class scores per candidate; NMS by the app",
           "conf_threshold": pest_test["int8"]["threshold"], "nms_iou": 0.7,
           "conf_threshold_note": "chosen for the INT8 model on validation negatives (<= 5% false alarms)"},
          f"{PEST_NAME}.json")
summary = {
    "settings": dict(format="QDQ", activations="int8", weights="int8 per-channel", calib_chunk=CALIB_CHUNK,
                     calib_disease=2 * CALIB_DISEASE_PER_DOMAIN, calib_pest=CALIB_PEST_IP102 + CALIB_PEST_NEG,
                     onnxruntime=ort.__version__, onnx=onnx.__version__, torch=torch.__version__,
                     ultralytics=ultralytics.__version__, cpu_cores=os.cpu_count()),
    "disease": {name: dict(chosen_variant=r["chosen"], fp32_val_score=r["fp32_val_score"], size_mb_fp32=r["sizes"][0],
                           size_mb_int8=r["sizes"][1])
                for name, r in DISEASE_RESULTS.items()},
    "disease_test": disease_test.to_dict(orient="records"),
    "pest": dict(chosen_method=PEST_CHOSEN, size_mb_fp32=size_mb(PEST_FP32), size_mb_int8=size_mb(PEST_INT8),
                 excluded_decode_nodes=len(PEST_EXCLUDE),
                 test={p: dict(map50=r["map50"], map50_95=r["map50_95"], threshold=r["threshold"],
                               levels=r["levels"].to_dict(orient="records")) for p, r in pest_test.items()}),
}
save_json(summary, "results.json")
print(sorted(p.name for p in WORK_DIR.iterdir()))
