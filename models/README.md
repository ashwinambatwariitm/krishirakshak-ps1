# Trained models

Model weights are not stored in git. Download them from the GitHub Release of this repository (tag `models-v1`) into
this folder and check each file against its SHA-256 checksum:

```
gh release download models-v1 --repo ashwinambatwariitm/krishirakshak-ps1 --dir models
sha256sum models/*.pt
```

Then try them on a photo: `python tools/predict.py leaf.jpg`. To export them to ONNX for the Raspberry Pi:
`python tools/export_onnx.py --disease-model models/tomato_disease_v4_effb0_10class.pt --pest-model models/pest_yolov8n_ip102_negatives.pt --check-images some_photos/`

| File | What it is | SHA-256 |
|---|---|---|
| `tomato_disease_v4_effb0_10class.pt` | Tomato disease classifier, all 10 classes (recommended) | `ecb0abfe188bb658605e777bbf03bdef47bda57fef8db8918e58eeef7854a106` |
| `tomato_disease_v4_mnv3s_10class.pt` | Smaller fallback (MobileNetV3-Small, 6 MB, about 2.5x faster), all 10 classes; field macro F1 about 0.50-0.56 | `a2ebb0eeddca12279e12a0802d568f471f4a790add4e1b4e700e244d005fa3e8` |
| `tomato_disease_v3_effb0_5class.pt` | Tomato disease classifier, 5 classes (alternative) | `12e61130ca17e707c85a056937d08ff61854f395732d1b69ab26bbd67ac1dabe` |
| `pest_yolov8n_ip102_negatives.pt` | IP102 insect pest detector, fine-tuned with insect-free leaves | `1a6d9aebf217d4437190a2901c7dfa5f9ff84b08f5e13fc098b4c9418b7ca260` |

## Disease classifiers (PyTorch checkpoints)

Each file is a dictionary saved with `torch.save`:

| Key | Meaning |
|---|---|
| `model_state_dict` | Weights (EMA-averaged) |
| `arch` | `efficientnet_b0` or `mobilenet_v3_small` (torchvision) |
| `class_names` | Output order of the classes |
| `img_size`, `mean`, `std` | Input size and normalisation |

Loading example:

```python
import torch
from torch import nn
from torchvision import models

ckpt = torch.load("models/tomato_disease_v4_effb0_10class.pt", map_location="cpu", weights_only=True)
model = models.efficientnet_b0(weights=None)
model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(ckpt["class_names"]))
model.load_state_dict(ckpt["model_state_dict"])
model.eval()
```

Input: RGB image, resized directly to 224 x 224 (no aspect-ratio preservation), pixel values divided by 255, then
normalised with mean (0.485, 0.456, 0.406) and std (0.229, 0.224, 0.225), layout NCHW float32. Output: logits in the
order of `class_names`.

10-class order (v4): healthy, early_blight, late_blight, leaf_mold, septoria_leaf_spot, bacterial_spot,
yellow_leaf_curl_virus, mosaic_virus, target_spot, spider_mites.

5-class order (v3): healthy, early_blight, late_blight, leaf_mold, septoria_leaf_spot.

## Pest detector (Ultralytics YOLOv8n)

```python
from ultralytics import YOLO

detector = YOLO("models/pest_yolov8n_ip102_negatives.pt")
result = detector.predict("leaf.jpg", imgsz=640, conf=0.25)[0]
```

Input 640 x 640 (letterbox). 102 IP102 classes; names are stored in the model and in
`results/pest_yolov8n_with_negatives/pest_labels.json`. Recommended confidence threshold 0.2 to 0.3. Name the species
only for the ids in `reliable_species_ids` of `results/pest_yolov8n_with_negatives/pest_config.json`; otherwise report
"insect pest detected, species uncertain".
