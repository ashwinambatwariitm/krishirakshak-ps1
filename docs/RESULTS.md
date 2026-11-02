# Training results

All runs used a Kaggle Tesla T4 GPU. Every number below is measured on held-out test images that were never used for
training, checkpoint selection or threshold tuning. Raw outputs for each run are in `results/<run>/`.

## Test data rules

- PlantVillage photos of the same physical leaf (consecutive camera shots, or one leaf photographed over several
  days) are grouped, and a whole group goes to train, validation or test. Rotated or re-saved copies of a photo are
  found with a rotation/flip-invariant perceptual hash (pHash) and merged into the same group.
- The two PlantDoc copies on Kaggle contain the same photos: 1,000 tomato images were only 582 unique photos (452
  duplicate pairs). Copies are merged by pHash before splitting, so one photo cannot be in training through one copy
  and in test through the other.
- PlantDoc photos that are near-copies of a PlantVillage photo are removed.
- Augmentation is applied only to training images, in memory, at load time. No augmented image is stored.

## Tomato disease classifier

### v1 - PlantVillage only (`results/disease_v1_plantvillage_only/`)

| System | PlantVillage test acc / F1 | PlantDoc leaf crops acc / F1 | PlantDoc full photos acc / F1 |
|---|---|---|---|
| Direct MobileNetV3-Small | 97.4% / 0.958 | 31% / 0.27 | 39% / 0.31 |
| Direct EfficientNet-B0 | 97.7% / 0.962 | 33% / 0.30 | 40% / 0.38 |
| Two-stage, MobileNetV3 gate | 97.3% / 0.959 | 34% / 0.32 | 42% / 0.40 |
| Two-stage, custom CNN gate from the IEEE Access 2025 paper | 97.3% / 0.961 | 33% / 0.31 | 37% / 0.29 |

A model trained on lab photos only does not transfer to field photos (consistent with the PlantDoc paper). The
MobileNetV3 gate is better than the paper's CNN gate on field photos (40% vs 6% of healthy field leaves recognised)
and in dark images.

### v2 - PlantVillage plus the PlantDoc training share (`results/disease_v2_with_plantdoc/`)

PlantDoc split per class: 65% train, 10% validation, 25% test. Training batches are about half PlantVillage and half
PlantDoc, with classes balanced within each source.

| System | PlantVillage test F1 | PlantDoc crops F1 | PlantDoc full photos F1 |
|---|---|---|---|
| Baseline, PlantVillage only (same test images) | 0.971 | 0.35 | 0.29 |
| Direct MobileNetV3-Small | 0.981 | 0.73 | 0.71 |
| Direct MobileNetV3-Large | 0.944 | 0.72 | 0.62 |
| Direct EfficientNet-B0 | 0.959 | 0.77 | 0.78 |
| Two-stage MobileNetV3-Small | 0.974 | 0.72 | 0.71 |

Field macro F1 more than doubled. With field data, the two-stage design no longer beats a single model.

### v3 - same split as v2, EMA weights and a matched cosine schedule (`results/disease_v3_ema_two_seeds/`)

| System | PlantVillage test acc / F1 | PlantDoc crops acc / F1 | PlantDoc full photos acc / F1 |
|---|---|---|---|
| EfficientNet-B0, seed 42 | 97.2% / 0.970 | 81.3% / 0.783 | 80.0% / 0.777 |
| EfficientNet-B0, seed 7 | 98.2% / 0.982 | 78.0% / 0.751 | 77.9% / 0.753 |
| MobileNetV3-Small, seed 42 | 97.4% / 0.973 | 77.7% / 0.742 | 75.2% / 0.731 |
| MobileNetV3-Small, seed 7 | 96.8% / 0.966 | 76.2% / 0.730 | 74.5% / 0.722 |

Clean accuracy is close to v2 (within the seed-to-seed spread), but robustness improved clearly, for example heavy
blur 0.63 -> 0.69 and half shadow 0.68 -> 0.73 macro F1 on PlantDoc crops. EfficientNet-B0 beats MobileNetV3-Small on
field photos with both seeds.

### v4 - all 10 tomato classes (`results/disease_v4_all_10_classes/`)

PlantDoc has field photos for 8 of the 10 classes. Target spot has none and spider mites only 2 (left out), so those
two classes are tested on lab photos only. Field macro F1 is averaged over the 8 classes present.

| System | PlantVillage test (10 classes) acc / F1 | PlantDoc crops (8) acc / F1 | PlantDoc full photos (8) acc / F1 |
|---|---|---|---|
| EfficientNet-B0, seed 7 | 98.4% / 0.980 | 68.5% / 0.629 | 68.3% / 0.617 |
| EfficientNet-B0, seed 42 | 98.8% / 0.984 | 67.7% / 0.606 | 67.4% / 0.592 |
| MobileNetV3-Small, seed 42 | 98.4% / 0.979 | 62.7% / 0.557 | 60.0% / 0.497 |

Per-class recall, EfficientNet-B0 seed 7:

| Class | PlantVillage (lab) | PlantDoc crops (field) | PlantDoc full photos (field) |
|---|---|---|---|
| healthy | 1.00 | 0.76 | 0.71 |
| early blight | 0.89 | 0.56 | 0.59 |
| late blight | 0.98 | 0.73 | 0.78 |
| leaf mold | 1.00 | 0.45 | 0.45 |
| septoria leaf spot | 0.97 | 0.70 | 0.73 |
| bacterial spot | 0.97 | 0.49 | 0.33 |
| yellow leaf curl virus | 1.00 | 0.86 | 0.93 |
| mosaic virus | 1.00 | 0.48 | 0.54 |
| target spot | 1.00 | no field data | no field data |
| spider mites | 1.00 | no field data | no field data |

Adding five classes lowers field accuracy on the original five (macro F1 about 0.68 vs 0.78 in v3). The main new
confusion is bacterial spot vs septoria, which look alike. More field photos of bacterial spot, leaf mold and mosaic
virus are the most useful next step.

### Deployment footprint (`results/disease_v4_all_10_classes/footprint*.csv`)

Measured with PyTorch on a Kaggle x86 CPU (4 threads). Raspberry Pi 5 numbers must be measured after ONNX export.

| | EfficientNet-B0 | MobileNetV3-Small |
|---|---|---|
| Parameters | 4.02 M | 1.53 M |
| Weights FP32 / FP16 / INT8 (estimate) | 16.1 / 8.0 / about 4.0 MB | 6.1 / 3.1 / about 1.5 MB |
| Compute per 224x224 image | 0.77 GFLOPs | 0.11 GFLOPs |
| CPU latency, batch 1 | 31 ms | 12 ms |
| Extra RAM: model loaded and running | about 53 MB | about 30 MB |
| Cost of each additional disease class | 5 KB | 4 KB |

Scaling to more crops (EfficientNet-B0): one model for all 14 PlantVillage crops (38 classes) is about 16.2 MB with
the same latency and RAM; one model per crop (14 crops) is about 225 MB FP32 / 56 MB INT8 on disk with one model in RAM
at a time. The Python/PyTorch runtime itself used about 630 MB; the Pi application will use ONNX Runtime from C++.

## IP102 pest detector (YOLOv8n, all classes)

Data: 18,976 annotated images (13,662 train, 1,516 validation, official 3,798 test). One malformed annotation file was
repaired and one degenerate box dropped. The class code in IP102 file names disagrees with the annotated class for
12,948 images, so classes are always read from the XML annotations. Five species have no training boxes.

### Base detector, 100 epochs (`results/pest_yolov8n_ip102/`)

Test mAP50 0.569, mAP50-95 0.358. On 1,000 insect-free PlantVillage tomato leaves it reported pests on 49% of leaves at
confidence 0.25, because IP102 contains only insect photos.

### Fine-tuned with insect-free leaf images (`results/pest_yolov8n_with_negatives/`)

The base detector was fine-tuned for 30 epochs with 4,197 insect-free tomato leaf images (PlantVillage and PlantDoc)
added as background images. Negative images are split by leaf/photo group into train, validation and test; the
confidence threshold is chosen on the validation negatives.

| Model, threshold | IP102 test mAP50 | Insects found | Species correct when found | False alarms, PlantVillage leaves | False alarms, PlantDoc photos |
|---|---|---|---|---|---|
| Base, 0.25 | 0.569 | 88% | 78% | 57% | 48% |
| Base, 0.70 | 0.569 | 38% | 94% | 8.1% | 6.3% |
| Fine-tuned, 0.20 | 0.567 | 92% | 77% | 0.3% | 5.1% |
| Fine-tuned, 0.30 | 0.567 | 85% | 79% | 0.2% | 2.5% |
| Fine-tuned, 0.50 | 0.567 | 65% | 86% | 0.1% | 1.3% |

The false-alarm problem is solved without losing detection accuracy. 34 species meet the "reliable to name" bar
(at least 10 test boxes, 70% species accuracy when found, AP50 of 0.5). For tomato-relevant pests the insect is found
89-100% of the time; species naming is reliable for aphids (94%) and about 60% for whitefly, red spider mite,
Spodoptera litura, black cutworm and thrips, so the application should present those species as a suggestion.

## Recommended models

| Task | Model | Notes |
|---|---|---|
| Tomato disease, all 10 classes | v4 EfficientNet-B0, seed 7 | Full tomato coverage; field macro F1 about 0.62 |
| Tomato disease, 5 classes (alternative) | v3 EfficientNet-B0, seed 42 | Field macro F1 about 0.78 on 5 classes |
| Insect pests | YOLOv8n fine-tuned with negatives | Confidence threshold 0.2 to 0.3 |

Download links and input specifications are in `models/README.md`.
