# Trained models

Model weights are not stored in git. They are published as GitHub Release assets of this repository:

- `models-v3`: the disease severity model and the IndicTrans2 translation model (CTranslate2 INT8).
- `llm-v2`: the LoRA-tuned Llama 3.2 1B `.pte` (default advisor model); `llm-v1`: the base Llama 3.2 1B `.pte` and the
  tokenizer (needed by both).
- `models-v2`: the v5 six-class tomato disease models (PyTorch) and all ONNX files (FP32 and INT8) for the
  Raspberry Pi application.
- `models-v1`: the earlier PyTorch checkpoints (v3, v4 and the pest detector).

Download into this folder and check each file against its SHA-256 checksum:

```
gh release download models-v3 --repo ashwinambatwariitm/krishirakshak-ps1 --dir models
gh release download llm-v2 --repo ashwinambatwariitm/krishirakshak-ps1 --dir models
gh release download llm-v1 --repo ashwinambatwariitm/krishirakshak-ps1 --dir models
gh release download models-v2 --repo ashwinambatwariitm/krishirakshak-ps1 --dir models
gh release download models-v1 --repo ashwinambatwariitm/krishirakshak-ps1 --dir models
tar -xzf models/indictrans2_en_indic_200M_ct2_int8.tar.gz -C models
sha256sum models/*.pt models/*.onnx models/*.pte
```

Then try them on a photo: `python tools/predict.py leaf.jpg`. To export a checkpoint to ONNX:
`python tools/export_onnx.py --disease-model models/tomato_disease_v4_effb0_10class.pt --pest-model models/pest_yolov8n_ip102_negatives.pt --check-images some_photos/`
To measure size, RAM and latency of ONNX files: `python tools/bench_onnx.py models/*.onnx --threads 4`.

## Release models-v3

| File | What it is | SHA-256 |
|---|---|---|
| `severity_lraspp_mnv3.onnx` | Disease severity: leaf + lesion segmentation, input 448 (docs/SEVERITY.md) | `1a9ca939cfc3890cbf095317578c457793ffe2fe6b3db92651a022a1b29c1642` |
| `indictrans2_en_indic_200M_ct2_int8.tar.gz` | IndicTrans2 en-indic 200M, CTranslate2 INT8 (extract into models/) | `e2bd68362cb1b127e8f180b1982a2000fd2834245c0df7d7b7c3615762058f9a` |
| `indictrans2_model.SRC` | SentencePiece source model of IndicTrans2 | `3cedc5cbcc740369b76201942a0f096fec7287fee039b55bdb956f301235b914` |

The severity model was trained on Roboflow Universe "tomato" by A Tomato segment (v7, CC BY 4.0), the Kaggle "Leaf
disease segmentation dataset" (masks CC0, PlantDoc images CC BY 4.0) and PlantDoc backgrounds (CC BY 4.0).
IndicTrans2 is by AI4Bharat, MIT licence (`INDICTRANS2_LICENSE.txt` in the release).

## Release llm-v2

`llama3_2_1b_krishirakshak_lora_8da4w.pte` (SHA-256 `236a022621730a1387aec86b3e6209c4be110eb84e9e6bb2f8504234999c58e8`):
LoRA-tuned Llama 3.2 1B Instruct, ExecuTorch 8da4w, default advisor model (training/src/llama_lora_distill.py). Uses
the tokenizer of llm-v1. Llama 3.2 is licensed under the Llama 3.2 Community License, Copyright (c) Meta Platforms,
Inc. All Rights Reserved; licence, use policy and notice are in the release. Built with Llama.

## Release models-v2

Recommended for the Phase 1 demo: `tomato_disease_v5_effb0_6class` (disease, "uncertain" below a top probability of
0.85, see `results/disease_v5_threshold/threshold.json`) and `pest_yolov8n_ip102_negatives` (confidence threshold
0.20). Accuracy of every file is in `docs/RESULTS.md`. Input and output specifications of each ONNX file (classes, input
size, normalisation, thresholds) are in the JSON files in `results/int8_ptq/`.

| File | What it is | SHA-256 |
|---|---|---|
| `tomato_disease_v5_effb0_6class.pt` | Tomato disease classifier, 6 classes, EfficientNet-B0 seed 7 (recommended) | `2a9847989b983c604e6089f77430bff8139ea390fa0e9c6adb978c1cdf97d495` |
| `tomato_disease_v5_mnv3s_6class.pt` | Smaller fallback, 6 classes, MobileNetV3-Small seed 42 | `4b207fa16c6bfbd365a5459503e27675b1b7573e72ea3df3e9ac17571b0f716f` |
| `tomato_disease_v5_effb0_6class.onnx` | ONNX FP32 of the recommended v5 model (16.1 MB) | `1a54987e167855fdd98e6a8d4ce88199144206c8156ac8368b3e08a6569a1590` |
| `tomato_disease_v5_effb0_6class_int8.onnx` | ONNX INT8, mixed precision (5.0 MB) | `ad00021f5c2423ec5b8885fc4981698b7fec4ee8d3e3177a789044fd5d5b8ff6` |
| `tomato_disease_v5_mnv3s_6class.onnx` | ONNX FP32 of the small fallback (6.1 MB) | `4a791a8c02f20cd49b96a83ee16a6426f8e637bf84d6fe395f7504a09569bdb7` |
| `tomato_disease_v5_mnv3s_6class_int8.onnx` | ONNX INT8, mixed precision (1.9 MB) | `48fc57c2d987591599fa2a926bd3709d3708acce9780c5a78e2048b4a96d8b11` |
| `tomato_disease_v4_effb0_10class.onnx` | ONNX FP32 of the v4 10-class model (16.1 MB) | `77d40c8c5b8556160c63acb155e9b3524af24b0e8e505407bdad2bd18c64f140` |
| `tomato_disease_v4_effb0_10class_int8.onnx` | ONNX INT8 of the v4 10-class model (5.0 MB) | `ac0eb60df6d6a070e96c3074a508e76b2611080942279ca848364a1abd4dcd01` |
| `pest_yolov8n_ip102_negatives.onnx` | ONNX FP32 of the pest detector, 640 x 640 input (13.6 MB) | `dfbdb150843c3f714fc2cd82b3d0138f55e70ef4812920774dd542d06b2d7e23` |
| `pest_yolov8n_ip102_negatives_int8.onnx` | ONNX INT8 of the pest detector (3.9 MB) | `cbf9844d5b6e3be1c16dcdc13c57bb913771c9072474f3cb838ec3f38fd24873` |

## Release models-v1

| File | What it is | SHA-256 |
|---|---|---|
| `tomato_disease_v4_effb0_10class.pt` | Tomato disease classifier, all 10 classes (extended coverage) | `ecb0abfe188bb658605e777bbf03bdef47bda57fef8db8918e58eeef7854a106` |
| `tomato_disease_v4_mnv3s_10class.pt` | Smaller fallback (MobileNetV3-Small, 6 MB, about 2.5x faster), all 10 classes; field macro F1 about 0.50-0.56 | `a2ebb0eeddca12279e12a0802d568f471f4a790add4e1b4e700e244d005fa3e8` |
| `tomato_disease_v3_effb0_5class.pt` | Tomato disease classifier, 5 classes (earlier alternative) | `12e61130ca17e707c85a056937d08ff61854f395732d1b69ab26bbd67ac1dabe` |
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

ckpt = torch.load("models/tomato_disease_v5_effb0_6class.pt", map_location="cpu", weights_only=True)
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

6-class order (v5): healthy, early_blight, late_blight, septoria_leaf_spot, bacterial_spot, yellow_leaf_curl_virus.

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
"insect pest detected, species uncertain". A species whose knowledge-base topic is in `reliable_groups` (caterpillars,
thrips) still gets that topic's advice (`results/pest_groups_ip102`).
