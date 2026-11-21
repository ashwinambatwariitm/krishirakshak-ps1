# %% [markdown]
# # KrishiRakshak PS1 - Tomato disease severity model (leaf + lesion segmentation, Kaggle GPU)
#
# Problem statement PS1 asks to "classify severity levels". A colour rule was tried first and failed validation on
# expert-annotated field photos (31% level agreement, results/severity_plantseg/README.md). This notebook trains a
# small segmentation network with two outputs per pixel:
# - **leaf**: the photographed leaf,
# - **lesion**: diseased area on that leaf,
# and severity = lesion area / leaf area, levels low (< 10%), moderate (10-25%), high (> 25%).
#
# Data (licences allow training and publishing the weights):
# - Roboflow Universe "tomato" by A Tomato segment, version 7: 537 tomato leaves with leaf and disease-area
#   polygons, CC BY 4.0 (private Kaggle copy `ashwinambatwar/tomato-leaf-lesion-seg-rf`). Its own train / valid /
#   test split is kept: train for training, valid for model selection, test only for the final report.
# - "Leaf disease segmentation dataset" (Kaggle `fakhrealam9537/leaf-disease-segmentation-dataset`): field photos
#   (from PlantDoc, CC BY 4.0) with lesion masks (CC0), several crops. Lesion masks only: these images train the
#   lesion output; the leaf output is masked out of the loss for them. The pre-augmented copies are not used.
# - PlantDoc (`nirmalsankalana/plantdoc-dataset`, CC BY 4.0): field photos used only as blurred backgrounds behind
#   the Roboflow leaves (copy-paste), because Roboflow photographs leaves on a plain grey background.
# The field test set (PlantSeg, CC BY-NC-ND) is not used here; the exported ONNX model is evaluated on it offline
# (tools/eval_severity_plantseg.py), on the same held-out photos as the colour rule.
#
# Model: torchvision LR-ASPP MobileNetV3-Large (ImageNet backbone), 2 output channels, input 448 x 448.
# Output: severity_lraspp_mnv3.pt, severity_lraspp_mnv3.onnx (logits 1x2x448x448), spec + metrics JSON.
#
# **Kaggle setup:** Accelerator = GPU T4, internet on, attach the three datasets above.

# %%
import json, math, os, random, time
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torchvision.models import MobileNet_V3_Large_Weights
from torchvision.models.segmentation import lraspp_mobilenet_v3_large

SMOKE = os.environ.get("KR_SMOKE") == "1"
INPUT_ROOT = Path(os.environ.get("KR_INPUT", "/kaggle/input"))
WORK_DIR = Path(os.environ.get("KR_WORK", "/kaggle/working")) / "lesion_seg"
WORK_DIR.mkdir(parents=True, exist_ok=True)
SIZE = 448                 # network input side
EPOCHS = 2 if SMOKE else 60
BATCH = 4 if SMOKE else 16
LR = 1e-3
PASTE_PROB = 0.5           # share of Roboflow training leaves pasted onto a field background
LEVELS = [(0.10, "low"), (0.25, "moderate"), (1.01, "high")]
MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)
SEED = 7
random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("torch", torch.__version__, "| device", DEVICE, torch.cuda.get_device_name(0) if DEVICE == "cuda" else "")


def level(share):
    return next(name for bound, name in LEVELS if share < bound)

# %% [markdown]
# ## Find the datasets

# %%
def find_files(root, name, max_depth=7):
    out = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        if Path(dirpath).relative_to(root).parts.__len__() >= max_depth:
            dirnames[:] = []
        if name in filenames:
            out.append(Path(dirpath) / name)
    return out


coco_files = {p.parent.name: p for p in find_files(INPUT_ROOT, "_annotations.coco.json")}
assert {"train", "valid", "test"} <= set(coco_files), f"Roboflow splits not found: {coco_files}"
print("Roboflow:", {k: str(v.parent) for k, v in coco_files.items()})

# Kaggle lesion-mask set: an images/ folder with a sibling masks folder, outside the "aug_data" copy
alam_pairs = []
for dirpath, dirnames, filenames in os.walk(INPUT_ROOT, followlinks=True):
    p = Path(dirpath)
    if p.name == "images" and "aug" not in str(p).lower():
        masks = next((p.parent / m for m in ("masks", "mask", "labels") if (p.parent / m).is_dir()), None)
        if masks is None:
            continue
        mask_by_stem = {m.stem: m for m in masks.iterdir()}
        for img in sorted(p.iterdir()):
            if img.suffix.lower() in (".jpg", ".jpeg", ".png") and img.stem in mask_by_stem:
                alam_pairs.append((img, mask_by_stem[img.stem]))
print("field lesion pairs:", len(alam_pairs))

backgrounds = []
for dirpath, dirnames, filenames in os.walk(INPUT_ROOT, followlinks=True):
    if "plantdoc" in dirpath.lower():
        backgrounds += [Path(dirpath) / f for f in filenames if f.lower().endswith((".jpg", ".jpeg", ".png"))]
backgrounds = sorted(backgrounds)[: (50 if SMOKE else 2000)]
print("background photos:", len(backgrounds))

# %% [markdown]
# ## Load the Roboflow polygons as leaf / lesion masks

# %%
def load_coco(path):
    d = json.loads(path.read_text())
    cats = {c["id"]: c["name"].lower() for c in d["categories"]}
    by_img = {}
    for a in d["annotations"]:
        by_img.setdefault(a["image_id"], []).append(a)
    items = []
    for im in d["images"]:
        h, w = im["height"], im["width"]
        leaf = np.zeros((h, w), np.uint8)
        lesion = np.zeros((h, w), np.uint8)
        for a in by_img.get(im["id"], []):
            target = leaf if cats[a["category_id"]] == "leaf" else (lesion if "disease" in cats[a["category_id"]] else None)
            if target is None:
                continue
            for poly in a["segmentation"]:
                pts = np.array(poly, np.float32).reshape(-1, 2).round().astype(np.int32)
                if len(pts) >= 3:
                    cv2.fillPoly(target, [pts], 1)
        lesion &= leaf          # disease area counts only on the leaf
        items.append({"image": path.parent / im["file_name"], "leaf": leaf, "lesion": lesion, "has_leaf": True})
    return items


rf = {split: load_coco(p) for split, p in coco_files.items()}
if SMOKE:
    rf = {k: v[:8] for k, v in rf.items()}
print({k: len(v) for k, v in rf.items()})

# Field lesion pairs: 90% training, 10% held out (lesion IoU on field photos), fixed split
random.Random(SEED).shuffle(alam_pairs)
alam_pairs = alam_pairs[: (8 if SMOKE else len(alam_pairs))]
n_val = max(1, len(alam_pairs) // 10) if alam_pairs else 0
alam_val, alam_train = alam_pairs[:n_val], alam_pairs[n_val:]
if alam_pairs and not SMOKE:
    # Guard against a wrong mask encoding: the field masks must contain lesion pixels
    shares = [cv2.imread(str(m), cv2.IMREAD_GRAYSCALE) for _, m in alam_pairs[:50]]
    lesion_share = float(np.mean([(m > 0).mean() for m in shares]))
    print(f"field masks: mean lesion share {lesion_share:.3f} (first 50)")
    assert lesion_share > 0.02, "field lesion masks look empty: check the mask encoding"


def load_alam(pair):
    img, msk = pair
    m = cv2.imread(str(msk), cv2.IMREAD_GRAYSCALE)
    # Lesion pixels are stored as a palette value (38 in this dataset), not 255: any non-zero value is lesion.
    # (A first run used "> 127" and so trained the field photos as "no lesion"; checked below.)
    return {"image": img, "leaf": np.zeros_like(m), "lesion": (m > 0).astype(np.uint8), "has_leaf": False}

# %% [markdown]
# ## Training data: augmentation and copy-paste onto field backgrounds

# %%
def read_rgb(path):
    return cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB)


def paste_on_background(img, leaf):
    """Put the leaf (with its own pixels) on a blurred field photo; masks stay the same."""
    bg = read_rgb(random.choice(backgrounds))
    bg = cv2.resize(bg, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_AREA)
    bg = cv2.GaussianBlur(bg, (0, 0), random.uniform(1.5, 6.0))
    alpha = cv2.GaussianBlur(leaf.astype(np.float32), (0, 0), 1.0)[..., None]   # soft edge
    return (img * alpha + bg * (1 - alpha)).astype(np.uint8)


def augment(img, leaf, lesion):
    h, w = img.shape[:2]
    # random scale / crop (keeps at least half of the side)
    s = random.uniform(0.5, 1.0)
    ch, cw = int(h * s), int(w * s)
    y, x = random.randint(0, h - ch), random.randint(0, w - cw)
    img, leaf, lesion = img[y:y + ch, x:x + cw], leaf[y:y + ch, x:x + cw], lesion[y:y + ch, x:x + cw]
    if random.random() < 0.5:
        img, leaf, lesion = img[:, ::-1], leaf[:, ::-1], lesion[:, ::-1]
    if random.random() < 0.5:
        img, leaf, lesion = img[::-1], leaf[::-1], lesion[::-1]
    k = random.randint(0, 3)
    img, leaf, lesion = np.rot90(img, k), np.rot90(leaf, k), np.rot90(lesion, k)
    img = np.ascontiguousarray(img).astype(np.float32)
    # colour: brightness, contrast, saturation (lesion colours must stay recognisable: small hue change only)
    img = img * random.uniform(0.7, 1.3) + random.uniform(-20, 20)
    gray = img.mean(axis=2, keepdims=True)
    img = gray + (img - gray) * random.uniform(0.7, 1.3)
    img = np.clip(img, 0, 255).astype(np.uint8)
    if random.random() < 0.3:
        img = cv2.GaussianBlur(img, (0, 0), random.uniform(0.5, 1.5))
    return img, np.ascontiguousarray(leaf), np.ascontiguousarray(lesion)


def to_tensor(img, leaf, lesion):
    img = cv2.resize(img, (SIZE, SIZE), interpolation=cv2.INTER_AREA)
    leaf = cv2.resize(leaf, (SIZE, SIZE), interpolation=cv2.INTER_NEAREST)
    lesion = cv2.resize(lesion, (SIZE, SIZE), interpolation=cv2.INTER_NEAREST)
    x = ((img.astype(np.float32) / 255.0 - MEAN) / STD).transpose(2, 0, 1)
    return torch.from_numpy(x), torch.from_numpy(np.stack([leaf, lesion]).astype(np.float32))


class SegData(torch.utils.data.Dataset):
    def __init__(self, items, train):
        self.items, self.train = items, train

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        it = self.items[i]
        if isinstance(it, tuple):           # field lesion pair, loaded lazily
            it = load_alam(it)
        img = read_rgb(it["image"])
        leaf, lesion = it["leaf"], it["lesion"]
        if lesion.shape != img.shape[:2]:
            lesion = cv2.resize(lesion, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
            leaf = cv2.resize(leaf, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
        if self.train:
            if it["has_leaf"] and backgrounds and random.random() < PASTE_PROB:
                img = paste_on_background(img, leaf)
            img, leaf, lesion = augment(img, leaf, lesion)
        x, y = to_tensor(img, leaf, lesion)
        # loss weight per output channel: no leaf supervision for lesion-only images
        wmask = torch.tensor([1.0 if it["has_leaf"] else 0.0, 1.0])
        return x, y, wmask


train_items = rf["train"] + alam_train
loader = torch.utils.data.DataLoader(SegData(train_items, True), batch_size=BATCH, shuffle=True,
                                     num_workers=0 if SMOKE else 4, drop_last=True)
print("training images:", len(train_items), "(Roboflow", len(rf["train"]), "+ field", len(alam_train), ")")

# %% [markdown]
# ## Model and training

# %%
model = lraspp_mobilenet_v3_large(weights=None, weights_backbone=MobileNet_V3_Large_Weights.IMAGENET1K_V2,
                                  num_classes=2)
model = model.to(DEVICE)
opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
steps = EPOCHS * max(1, len(loader))
sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=LR, total_steps=steps, pct_start=0.1)
scaler = torch.amp.GradScaler(enabled=DEVICE == "cuda")


def seg_loss(logits, y, wmask):
    """BCE + soft Dice per output channel, weighted per image and channel."""
    w = wmask[:, :, None, None]
    bce = F.binary_cross_entropy_with_logits(logits, y, reduction="none")
    bce = (bce * w).sum() / (w.sum() * logits.shape[2] * logits.shape[3] + 1e-6)
    p = torch.sigmoid(logits)
    inter = (p * y).sum(dim=(2, 3))
    dice = 1 - (2 * inter + 1) / (p.sum(dim=(2, 3)) + y.sum(dim=(2, 3)) + 1)
    dice = (dice * wmask).sum() / (wmask.sum() + 1e-6)
    return bce + dice


@torch.no_grad()
def predict(img_rgb):
    """RGB uint8 photo -> (leaf mask, lesion mask) at the photo size, thresholds 0.5."""
    model.eval()
    x = ((cv2.resize(img_rgb, (SIZE, SIZE), interpolation=cv2.INTER_AREA).astype(np.float32) / 255 - MEAN) / STD)
    x = torch.from_numpy(x.transpose(2, 0, 1))[None].to(DEVICE)
    p = torch.sigmoid(model(x)["out"])[0].cpu().numpy()
    p = np.stack([cv2.resize(c, (img_rgb.shape[1], img_rgb.shape[0])) for c in p])
    leaf = p[0] > 0.5
    return leaf, (p[1] > 0.5) & leaf


def evaluate(items, with_leaf=True):
    """Leaf / lesion IoU, severity share error and level agreement (reference = annotated masks)."""
    li = lu = si = su = 0
    errs, agree, n = [], 0, 0
    conf = {}
    for it in items:
        if isinstance(it, tuple):
            it = load_alam(it)
        img = read_rgb(it["image"])
        leaf, lesion = it["leaf"].astype(bool), it["lesion"].astype(bool)
        if lesion.shape != img.shape[:2]:
            lesion = cv2.resize(lesion.astype(np.uint8), (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST) > 0
        pl, ples = predict(img)
        if not with_leaf:                    # field lesion set: no leaf reference, lesion IoU only
            si += (ples & lesion).sum(); su += (ples | lesion).sum()
            continue
        li += (pl & leaf).sum(); lu += (pl | leaf).sum()
        si += (ples & lesion).sum(); su += (ples | lesion).sum()
        if leaf.sum() > 0 and pl.sum() > 0:
            ref, pred = lesion.sum() / leaf.sum(), ples.sum() / pl.sum()
            errs.append(abs(ref - pred)); n += 1
            a, b = level(ref), level(pred)
            agree += a == b
            conf[f"{a}->{b}"] = conf.get(f"{a}->{b}", 0) + 1
    # Dice from the same pooled pixel counts: 2 |A and B| / (|A| + |B|) = 2 I / (I + U)
    out = {"lesion_iou": round(float(si / max(1, su)), 3), "lesion_dice": round(float(2 * si / max(1, si + su)), 3)}
    if with_leaf:
        out.update(leaf_iou=round(float(li / max(1, lu)), 3), leaf_dice=round(float(2 * li / max(1, li + lu)), 3), level_agreement=round(agree / max(1, n), 3),
                   median_share_error=round(float(np.median(errs)), 3) if errs else None, confusion=conf, images=n)
    return out


history, best, best_score = [], None, -1.0
t0 = time.time()
for epoch in range(EPOCHS):
    model.train()
    total = 0.0
    for x, y, wmask in loader:
        x, y, wmask = x.to(DEVICE), y.to(DEVICE), wmask.to(DEVICE)
        with torch.autocast(device_type="cuda", enabled=DEVICE == "cuda"):
            logits = model(x)["out"]
        loss = seg_loss(logits.float(), y, wmask)
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.step(opt); scaler.update(); sched.step()
        total += loss.item()
    val = evaluate(rf["valid"])
    score = val["level_agreement"] + val["lesion_iou"]       # model selection on the Roboflow valid split only
    history.append({"epoch": epoch + 1, "loss": round(total / max(1, len(loader)), 4), **val})
    print(f"epoch {epoch + 1:3d} loss {history[-1]['loss']:.4f} | valid leaf IoU {val['leaf_iou']:.3f} "
          f"lesion IoU {val['lesion_iou']:.3f} level {val['level_agreement']:.3f} | {time.time() - t0:.0f} s")
    if score > best_score:
        best_score, best = score, {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
        torch.save(best, WORK_DIR / "severity_lraspp_mnv3.pt")   # saved right away (Kaggle output quota)

# %% [markdown]
# ## Final evaluation of the selected model (test splits are used only here)

# %%
model.load_state_dict(best)
metrics = {"valid": evaluate(rf["valid"]), "test": evaluate(rf["test"]),
           "field_lesion_heldout": evaluate(alam_val, with_leaf=False) if alam_val else None,
           "history": history, "train_images": {"roboflow": len(rf["train"]), "field_lesion": len(alam_train)}}
print(json.dumps({k: v for k, v in metrics.items() if k != "history"}, indent=1))

# %% [markdown]
# ## Export to ONNX (input 1x3x448x448 normalised RGB, output 1x2x448x448 logits: leaf, lesion)

# %%
class Export(nn.Module):
    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, x):
        return self.m(x)["out"]


# The wrapper must be in eval mode itself: torch.onnx.export restores the wrapper's mode afterwards, which would
# switch the whole model (BatchNorm) back to training mode for the check below
wrapper = Export(model.cpu()).eval()
dummy = torch.randn(1, 3, SIZE, SIZE)
onnx_path = WORK_DIR / "severity_lraspp_mnv3.onnx"
torch.onnx.export(wrapper, dummy, str(onnx_path), input_names=["image"], output_names=["logits"],
                  opset_version=17, dynamo=False)
wrapper.eval()
spec = {"model": "severity_lraspp_mnv3", "input": {"name": "image", "size": SIZE, "color_order": "RGB",
        "scale": "pixel / 255", "mean": MEAN.tolist(), "std": STD.tolist(), "resize": "INTER_AREA, no letterbox"},
        "output": {"name": "logits", "channels": ["leaf", "lesion"], "activation": "sigmoid", "threshold": 0.5},
        "severity": {"share": "lesion pixels inside the leaf / leaf pixels",
                     "levels": {"low": "< 0.10", "moderate": "0.10 - 0.25", "high": ">= 0.25"}},
        "data": ["Roboflow Universe 'tomato' by A Tomato segment, v7, CC BY 4.0",
                 "Kaggle fakhrealam9537/leaf-disease-segmentation-dataset (masks CC0, images from PlantDoc CC BY 4.0)",
                 "PlantDoc backgrounds (CC BY 4.0)"]}
(WORK_DIR / "severity_spec.json").write_text(json.dumps(spec, indent=1))
(WORK_DIR / "severity_metrics.json").write_text(json.dumps(metrics, indent=1))
try:   # check the ONNX file gives the same output as PyTorch
    import onnxruntime as ort
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    with torch.no_grad():
        ref = wrapper(dummy).numpy()
    diff = float(np.abs(sess.run(None, {"image": dummy.numpy()})[0] - ref).max())
    print("ONNX vs PyTorch max |difference|:", diff)
except ImportError:
    print("onnxruntime not installed; ONNX check skipped")
print("saved:", sorted(p.name for p in WORK_DIR.iterdir()))
