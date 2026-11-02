"""Create tiny synthetic copies of the Kaggle dataset layouts, for testing the notebooks on a PC.

The fake data mimics every layout and quirk the notebooks must handle: PlantVillage colour/grayscale
variants and camera-sequence file names, a corrupt file, rotated duplicates, PlantDoc in both Kaggle copies
(with the same photo in both), a very large field photo, and IP102 VOC annotations whose file-name class code
does not match the label.

Usage: python training/smoke_test/make_fake.py OUTPUT_FOLDER
"""
import random
import shutil
import sys
import uuid
from pathlib import Path
import numpy as np
import cv2

root = Path(sys.argv[1])
rng = np.random.default_rng(0)
random.seed(0)

def leaf(spot_color, n_spots, size=256, bg=(128, 128, 128)):
    """Synthetic leaf image: a green ellipse with coloured spots on a plain background."""
    img = np.full((size, size, 3), bg, np.uint8)
    cv2.ellipse(img, (size // 2, size // 2), (size // 3, size // 2 - 20), 0, 0, 360, (40, 150, 40), -1)
    for _ in range(n_spots):
        c = tuple(int(v) for v in rng.integers(size // 3, 2 * size // 3, 2))
        cv2.circle(img, c, int(rng.integers(4, 12)), spot_color, -1)
    return (img.astype(np.int16) + rng.integers(-15, 15, img.shape)).clip(0, 255).astype(np.uint8)

STYLE = {"Tomato___healthy": ((40, 150, 40), 0), "Tomato___Early_blight": ((30, 60, 90), 8),
         "Tomato___Late_blight": ((20, 20, 20), 5), "Tomato___Leaf_Mold": ((60, 200, 220), 10),
         "Tomato___Septoria_leaf_spot": ((200, 200, 200), 15)}
PREFIX = {"Tomato___healthy": "RS_HL", "Tomato___Early_blight": "RS_Erly.B", "Tomato___Late_blight": "RS_Late.B",
          "Tomato___Leaf_Mold": "Crnl_L.Mold", "Tomato___Septoria_leaf_spot": "Matt.S_CG"}

# PlantVillage: color + a decoy grayscale variant + a non-tomato class
pv = root / "plantvillage-dataset" / "plantvillage dataset"
for cls, (col, n) in STYLE.items():
    d = pv / "color" / cls; d.mkdir(parents=True)
    for k in range(70):
        name = f"{uuid.uuid4()}___{PREFIX[cls]} {6300 + 7 * k}.JPG"
        cv2.imwrite(str(d / name), cv2.cvtColor(leaf(col, n), cv2.COLOR_RGB2BGR))
    if cls == "Tomato___Late_blight":
        for leaf_id in range(3):
            for day in (1, 6, 12):
                cv2.imwrite(str(d / f"{uuid.uuid4()}___GHLB Leaf {leaf_id} Day {day}.JPG"), cv2.cvtColor(leaf(col, n), cv2.COLOR_RGB2BGR))
    # an exact rotated duplicate under a different sequence number (must be merged into one group)
    src = sorted(d.iterdir())[0]
    cv2.imwrite(str(d / f"{uuid.uuid4()}___{PREFIX[cls]} 9999.JPG"), cv2.rotate(cv2.imread(str(src)), cv2.ROTATE_90_CLOCKWISE))
(pv / "color" / "Apple___Apple_scab").mkdir(parents=True)
cv2.imwrite(str(pv / "color" / "Apple___Apple_scab" / "a.JPG"), leaf((0, 0, 0), 3))
(pv / "grayscale" / "Tomato___Early_blight").mkdir(parents=True)
(pv / "color" / "Tomato___Early_blight" / "corrupt___RS_Erly.B 7000.JPG").write_bytes(b"not an image")

# PlantDoc object-detection layout (YOLO txt)
NAMES = ["Cherry leaf", "Peach leaf", "Corn leaf blight", "Apple rust leaf", "Potato leaf late blight", "Strawberry leaf",
         "Corn rust leaf", "Tomato leaf late blight", "Tomato mold leaf", "Potato leaf early blight", "Apple leaf",
         "Tomato leaf yellow virus", "Blueberry leaf", "Tomato leaf mosaic virus", "Raspberry leaf",
         "Tomato leaf bacterial spot", "Squash Powdery mildew leaf", "grape leaf", "Corn Gray leaf spot",
         "Tomato Early blight leaf", "Apple Scab Leaf", "Tomato Septoria leaf spot", "Tomato leaf", "Soyabean leaf",
         "Bell_pepper leaf spot", "Bell_pepper leaf", "grape leaf black rot", "Potato leaf",
         "Tomato two spotted spider mites leaf"]
od = root / "plantdoc-object-detection-dataset"
od_ids = {22: "Tomato___healthy", 19: "Tomato___Early_blight", 7: "Tomato___Late_blight", 8: "Tomato___Leaf_Mold",
          21: "Tomato___Septoria_leaf_spot", 0: None}
for split, n in (("train", 12), ("val", 4)):
    (od / "images" / split).mkdir(parents=True); (od / "labels" / split).mkdir(parents=True)
    for k in range(n):
        cid = list(od_ids)[k % len(od_ids)]
        cls = od_ids[cid] or "Tomato___healthy"
        img = cv2.resize(leaf(*STYLE[cls], bg=(90, 120, 60)), (480, 360))
        cv2.imwrite(str(od / "images" / split / f"{split}_{k:05d}.jpg"), img)
        lines = [f"{cid} 0.5 0.5 0.6 0.8", f"{cid} 0.1 0.1 0.02 0.02"]  # second box is too small -> skipped
        (od / "labels" / split / f"{split}_{k:05d}.txt").write_text("\n".join(lines) + "\n")
(od / "dataset.yaml").write_text("path: /kaggle/input/plantdoc-object-detection-dataset\ntrain: images/train\nval: images/val\nnc: 29\nnames:\n"
                                 + "".join(f"  {i}: {n}\n" for i, n in enumerate(NAMES)))

# PlantDoc classification layout (full images), incl. one copy of a PlantVillage image (must be dropped as leakage)
pc = root / "plantdoc-dataset"
cls_dirs = {"Tomato_leaf": "Tomato___healthy", "Tomato_Early_blight_leaf": "Tomato___Early_blight",
            "Tomato_leaf_late_blight": "Tomato___Late_blight", "Tomato_mold_leaf": "Tomato___Leaf_Mold",
            "Tomato_Septoria_leaf_spot": "Tomato___Septoria_leaf_spot", "Apple_Scab_Leaf": None}
for split in ("train", "test"):
    for dname, cls in cls_dirs.items():
        d = pc / split / dname; d.mkdir(parents=True)
        for k in range(4):
            cv2.imwrite(str(d / f"{split}_{dname}_{k}.jpg"), cv2.resize(leaf(*STYLE[cls or "Tomato___healthy"], bg=(70, 110, 50)), (500, 400)))
leak_src = sorted((pv / "color" / "Tomato___Early_blight").glob("*6300.JPG"))[0]
cv2.imwrite(str(pc / "test" / "Tomato_Early_blight_leaf" / "leak.jpg"), cv2.imread(str(leak_src)))

# IP102 VOC layout
ip = root / "ip102-dataset"
(ip / "Annotations").mkdir(parents=True); (ip / "JPEGImages").mkdir(parents=True)
ids = []
for cls in (0, 5, 24, 71, 101):
    code = 102 if cls == 101 else cls  # mimic the real file-name quirk
    for k in range(14):
        img_id = f"IP{code:03d}{k:06d}"; ids.append(img_id)
        W, H = 520, 400
        img = np.full((H, W, 3), rng.integers(60, 200, 3), np.uint8)
        x1, y1 = int(rng.integers(20, 300)), int(rng.integers(20, 200)); x2, y2 = x1 + 120, y1 + 90
        cv2.ellipse(img, ((x1 + x2) // 2, (y1 + y2) // 2), (60, 45), 0, 0, 360, tuple(int(v) for v in rng.integers(0, 255, 3)), -1)
        cv2.imwrite(str(ip / "JPEGImages" / f"{img_id}.jpg"), img)
        (ip / "Annotations" / f"{img_id}.xml").write_text(
            f"<annotation><filename>{img_id}.jpg</filename><size><width>{W}</width><height>{H}</height><depth>3</depth></size>"
            f"<object><name>{cls}</name><bndbox><xmin>{x1}</xmin><ymin>{y1}</ymin><xmax>{x2}</xmax><ymax>{y2}</ymax></bndbox></object>"
            "</annotation>")
random.shuffle(ids)
(ip / "trainval.txt").write_text("\n".join(sorted(ids[:52])) + "\n")
(ip / "test.txt").write_text("\n".join(sorted(ids[52:])) + "\n")
print("fake datasets written to", root)

# v2 extras: the same photo in both PlantDoc copies (must become one group), and a very large field photo
for k in (0, 6):  # train_00000 / train_00006 have class id 22 ("Tomato leaf") -> copy into the classification copy
    shutil.copy(od / "images" / "train" / f"train_{k:05d}.jpg", pc / "train" / "Tomato_leaf" / f"dup_of_det_{k}.jpg")
big = cv2.resize(leaf(*STYLE["Tomato___Late_blight"], bg=(60, 100, 40)), (2400, 1800))
cv2.imwrite(str(pc / "train" / "Tomato_leaf_late_blight" / "big_field_photo.jpg"), big)
print("v2 extras written")

# v4 extras: the five other PlantVillage tomato classes, plus PlantDoc field images for three of them
NEW = {"Tomato___Bacterial_spot": (((90, 40, 40), 12), "GCREC_Bact.Sp", 15, "Tomato_leaf_bacterial_spot"),
       "Tomato___Tomato_Yellow_Leaf_Curl_Virus": (((200, 200, 40), 6), "UF.GRC_YLCV_Lab", 11, "Tomato_leaf_yellow_virus"),
       "Tomato___Tomato_mosaic_virus": (((120, 160, 60), 9), "PSU_CG", 13, "Tomato_leaf_mosaic_virus"),
       "Tomato___Target_Spot": (((60, 30, 30), 7), "Com.G_TgS_FL", None, None),
       "Tomato___Spider_mites Two-spotted_spider_mite": (((230, 230, 230), 20), "Com.G_SpM_FL", None, None)}
for cls, ((col, n), prefix, det_id, cls_dir) in NEW.items():
    d = pv / "color" / cls; d.mkdir(parents=True)
    for k in range(60):
        cv2.imwrite(str(d / f"{uuid.uuid4()}___{prefix} {7000 + 7 * k}.JPG"), cv2.cvtColor(leaf(col, n), cv2.COLOR_RGB2BGR))
    if det_id is not None:
        for k in range(10):
            img = cv2.resize(leaf(col, n, bg=(90, 120, 60)), (480, 360))
            name = f"new_{det_id}_{k:03d}.jpg"
            cv2.imwrite(str(od / "images" / "train" / name), img)
            (od / "labels" / "train" / f"new_{det_id}_{k:03d}.txt").write_text(f"{det_id} 0.5 0.5 0.6 0.8\n")
        for split in ("train", "test"):
            dd = pc / split / cls_dir; dd.mkdir(parents=True, exist_ok=True)
            for k in range(8):
                cv2.imwrite(str(dd / f"{split}_{k}.jpg"), cv2.resize(leaf(col, n, bg=(70, 110, 50)), (500, 400)))
# PlantDoc spider-mite class with only 2 images (must be left out of PlantDoc)
dd = pc / "train" / "Tomato_two_spotted_spider_mites_leaf"; dd.mkdir(parents=True)
for k in range(2):
    cv2.imwrite(str(dd / f"sm_{k}.jpg"), cv2.resize(leaf((230, 230, 230), 20, bg=(70, 110, 50)), (500, 400)))
print("v4 extras written")
