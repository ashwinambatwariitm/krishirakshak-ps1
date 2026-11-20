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

### v5 - six classes for the Phase 1 demo (`results/disease_v5_six_classes/`)

The organisers asked for about 4-6 disease classes, including healthy, for one crop. v5 uses the v4 recipe on six
classes: healthy, early blight, late blight, septoria leaf spot, bacterial spot and yellow leaf curl virus (leaf mold is
mostly a polyhouse disease and was the weakest v4 field class). The splits are the v4 split manifests filtered to these
classes, so every test image was also a v4 test image (PlantVillage 2,111; PlantDoc 587 leaf crops and 188 full photos).

| System | PlantVillage test acc / F1 | PlantDoc crops acc / F1 | PlantDoc full photos acc / F1 |
|---|---|---|---|
| EfficientNet-B0, seed 7 (recommended on validation) | 98.7% / 0.980 | 76.0% / 0.693 | 73.4% / 0.683 |
| EfficientNet-B0, seed 42 | 99.0% / 0.985 | 75.5% / 0.692 | 75.0% / 0.689 |
| MobileNetV3-Small, seed 42 | 98.5% / 0.977 | 74.5% / 0.674 | 70.2% / 0.637 |
| v4 EfficientNet-B0, outputs restricted to the same six classes | 98.5% / 0.979 | 77.0% / 0.715 | 72.9% / 0.670 |

Training on six classes is no better than the v4 model restricted to the same six classes; the gain over the v4
10-class field result (F1 0.63) comes from choosing among fewer classes. Field recall per class (leaf crops): yellow
leaf curl virus 0.92, healthy 0.82, septoria 0.73, late blight 0.69, early blight 0.58, bacterial spot 0.43. Field
macro F1 stays between 0.65 and 0.71 under blur, shadow, rotation, low light and JPEG compression.

### "Uncertain" threshold for v5 (`results/disease_v5_threshold/`)

The application names a disease only when the top probability is at least 0.85; otherwise it answers "uncertain - take
a clearer photo or consult your local KVK". The threshold is the lowest one reaching 85% accuracy on answered PlantDoc
validation photos; the test sets only report.

| Test set | Accuracy, always answering | Photos answered at 0.85 | Accuracy on answered photos |
|---|---|---|---|
| PlantVillage (2,111) | 98.7% | 97% | 99.6% |
| PlantDoc leaf crops (587) | 76.3% | 70% | 88.3% |
| PlantDoc full photos (188) | 73.4% | 65% | 86.2% |

Diseased leaves answered as "healthy" fall from 5.3% to 4.0% on the field crops. Bacterial spot stays unreliable
(answered for 33% of its photos, 55% correct when answered), so the application presents it as "possible bacterial
spot - confirm with an expert".

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

### Accuracy per advice group (`results/pest_groups_ip102/`, `training/src/ip102_pest_groups.py`)

The advice the farmer sees is per knowledge-base topic, and several topics are groups of IP102 species
(`caterpillars` = 3 cutworms + 3 armyworms, `thrips` = 5 species). The application names a topic only when the
*species* is reliable (`pest_config.json`), which among tomato pests is only aphids; a found cutworm whose exact
species is uncertain gets the generic `insect_other` advice. This evaluation scores the deployed ONNX models (FP32 and
the INT8 model of the Pi) with the application's own pre/post-processing (`pest_detector.cpp`) on the IP102 test split;
its per-species numbers reproduce `per_species_results.csv` exactly. "Group right" = the best class of the matched box
is in the right group; "precision" = of all boxes the app would label with the group, the share that overlaps a
ground-truth insect of that group.

INT8, threshold 0.2, knowledge-base mapping of today:

| Advice group | Test boxes | Insect found | Exact species right (top-2) | **Group right** | Group precision |
|---|---|---|---|---|---|
| caterpillars (6 species) | 330 | 95% | 38% (62%) | **75%** | 75% |
| thrips (5 species) | 63 | 94% | 56% (73%) | **81%** | 73% |
| mites (2 species) | 52 | 83% | 53% (91%) | 58% | 73% |
| aphids (3 species) | 370 | 85% | 88% (92%) | 94% | 58% |

- Caterpillars and thrips meet the same bar as species (at least 10 test boxes, 70% right when found) plus 70% group
  precision: giving their topic's advice when the group is reliable would change the advice for a found caterpillar
  from generic to correct in about 3 of 4 cases. Mites pass with the extended mapping on FP32 only (76-77% right when
  found); aphid precision is low partly because colony photos label only some of the insects (extra correct boxes
  count as wrong).
- Most group errors go to species outside the tomato groups ("other": 43 of 314 found caterpillars) or between
  caterpillars and Spodoptera litura ("Prodenia litura", class 86; 35 + 21 boxes). With class 86 merged into
  caterpillars (mapping `kb_with_86`) the group is 86% right when found with 81% precision (INT8; FP32 85% / 82%).
- **Applied in the application** (20 Nov): `pest_config.json` lists `reliable_groups` = caterpillars, thrips; the
  knowledge base maps class 86 to caterpillars; `KnowledgeBase::pestTopic` (C++) and `pest_topic` (Python) give a
  reliable group's topic even when the species is uncertain, and the "species uncertain" message is still shown.
  Mites stay generic (58%). Tests: `pest_severity_test` and `tools/check_pest_severity.py`.
- An extended mapping (more aphid and mite species, Spodoptera litura, greenhouse whitefly, leafhoppers, mealybugs,
  fruit flies) is scored in `group_results.csv`; leafhoppers (98%) and fruit flies (100%) are reliable groups,
  whitefly is not (73% right, 42% precision). The KB advice for these topics would have to fit those species first.
- IP102 photos are mostly close-ups from the web; these are not field numbers for insects on tomato leaves.

### Independent test set: 8 tomato pests from other sources (`results/pest_independent_huang/`, `training/src/pest_independent_test.py`)

Data: the 609 original images of "A database of eight common tomato pest images" (Mei-Ling Huang, Tzu Chin Chuang,
Mendeley Data V1, 2020, doi:10.17632/s62zm6djd2.1, CC BY 4.0), collected from IPMImages, NBAIR (India) and Google
search: insects on plants (often cotton, maize or cabbage, not only tomato), 299 x 299 pixels. This is an
out-of-source check, not a tomato field test. 31 images are near-copies of IP102 images (perceptual hash, Hamming
distance <= 8 of 64; 19 identical) and are left out below (578 images). Deployed INT8 model, threshold 0.2; "advice"
is the set of topics of all boxes, as in the application. Rules: today = topic only for reliable species; group =
also for species of the reliable advice groups (caterpillars, thrips), KB mapping of today; extended = the extended
mapping (with Spodoptera litura, whitefly, fruit flies, ...) and its reliable groups.

| Pest (images) | Expected advice | Insect found | Right advice today | Right advice, group rule | Right advice, extended |
|---|---|---|---|---|---|
| Tetranychus urticae, spider mite (70) | mites | 67% | 0% | 0% | 1% |
| Myzus persicae, aphid (125) | aphids | 66% | 58% | 58% | 58% |
| Thrips palmi (24) | thrips | 75% | 0% | **50%** | 50% |
| Spodoptera exigua, beet armyworm (68) | caterpillars | 56% | 0% | **44%** | 44% |
| Spodoptera litura (84) | spodoptera | 80% | 0% | 0% (32% get caterpillar advice) | 0% (32% caterpillar) |
| Helicoverpa armigera (107) | helicoverpa | 63% | 0% | 0% (20% get caterpillar advice) | 0% (21% caterpillar) |
| Bemisia whitefly (59) | whitefly | 49% | 0% | 0% | 0% (32% get other advice) |
| Zeugodacus cucurbitae, melon fly (41) | fruit fly | 95% | 0% | 0% | **88%** |

| All 578 images | Right advice | Caterpillar advice for S. litura / Helicoverpa | Advice for a wrong kind of pest | Generic advice only | No insect found |
|---|---|---|---|---|---|
| today | 12.6% | 0% | 1.2% | 53.1% | 33.0% |
| group rule (KB mapping) | 19.9% | 8.3% | 1.7% | 37.0% | 33.0% |
| extended mapping | 26.3% | 8.3% | 6.2% | 26.1% | 33.0% |

- Outside IP102 the detector finds fewer insects (67% of photos, IP102 test 85-95%) and names the exact species far
  less often (spider mites 16%, thrips 46%, beet armyworm 32%): the IP102 numbers are optimistic for new photos.
- The group rule is safe: right advice rises from 12.6% to 19.9% of photos (thrips 0 -> 50%, beet armyworm
  0 -> 44%) and S. litura / Helicoverpa get the general caterpillar advice instead of generic advice, while advice for
  a wrong kind of pest stays below 2%.
- The extended mapping is not safe as it is: fruit flies become 88% right, but the silverleaf whitefly (Bemisia, not
  in IP102) is detected as leafhoppers and gets their advice in 32% of its photos.
- Spider mites are found (67%) but named as citrus mites (Panonychus citri), which are outside the mites topic of the
  knowledge base; Helicoverpa and Bemisia are not IP102 classes, so they need training data of their own.

## INT8 post-training quantization (`results/int8_ptq/`)

ONNX Runtime static quantization: QDQ format, INT8 weights per output channel, INT8 activations (S8S8, the format ONNX
Runtime recommends for Arm). Calibration images come from the training split, the calibration method and the
FP32/INT8 layout are chosen on validation, and the test sets only report. The FP32 ONNX models reproduce the published
PyTorch test accuracy (within 1-2 images, from FP16 evaluation during training).

Fully INT8 classifiers lost too much accuracy (v5 EfficientNet-B0 validation score 0.84 -> 0.77; MobileNetV3-Small
collapsed to 0.24). A per-block sensitivity test on PlantDoc training photos traced the loss to a few early blocks
(EfficientNet-B0 blocks 0-3; MobileNetV3-Small blocks 1 and 4 and its hard-swish activations). These blocks stay in
FP32 (mixed precision); they hold few weights, so the files are still about 3x smaller.

| Model | Test set | FP32 acc / F1 | INT8 acc / F1 | Same answer as FP32 | Size FP32 -> INT8 |
|---|---|---|---|---|---|
| v5 EfficientNet-B0 (blocks 0-3 FP32, Percentile) | PlantVillage | 98.7% / 0.980 | 98.9% / 0.983 | 99.6% | 16.1 -> 5.0 MB |
| | PlantDoc leaf crops | 76.3% / 0.696 | 75.6% / 0.685 | 93.7% | |
| | PlantDoc full photos | 73.4% / 0.681 | 73.9% / 0.678 | 94.7% | |
| v5 MobileNetV3-Small (blocks 0, 1, 4 + hard-swish FP32, MinMax) | PlantVillage | 98.5% / 0.976 | 98.3% / 0.974 | 99.3% | 6.1 -> 1.9 MB |
| | PlantDoc leaf crops | 74.6% / 0.675 | 75.3% / 0.686 | 90.6% | |
| | PlantDoc full photos | 69.7% / 0.630 | 67.6% / 0.608 | 89.4% | |
| v4 EfficientNet-B0, 10 classes (blocks 0-3 FP32) | PlantVillage | 98.4% / 0.980 | 98.4% / 0.979 | 99.6% | 16.1 -> 5.0 MB |
| | PlantDoc leaf crops | 68.5% / 0.629 | 67.1% / 0.617 | 92.5% | |

Per-class recall changes by at most 4.5 points on the field crops (bacterial spot 0.43 -> 0.39); the full per-class table
is `disease_per_class_recall.csv`.

Pest detector: the box decoding at the end of the YOLO head stays in FP32 (it joins pixel coordinates and 0-1 class
scores in one tensor). Percentile calibration was chosen on validation (validation mAP50 0.612 vs 0.608 FP32).

| Pest detector, threshold 0.20 | IP102 test mAP50 | Insects found | Species correct when found | False alarms, PlantVillage / PlantDoc | Size |
|---|---|---|---|---|---|
| FP32 ONNX | 0.571 | 92.2% | 76.5% | 0.3% / 5.1% | 13.6 MB |
| INT8 | 0.560 | 92.0% | 76.5% | 0.5% / 3.8% | 3.9 MB |

The ONNX model uses a square 640 x 640 input (PyTorch evaluation used a tighter rectangle), so its FP32 mAP differs
slightly from the PyTorch value; the 0.20 threshold is confirmed on validation for both FP32 and INT8. Mean per-species
AP50 change -0.011; the largest drops are rare species with fewer than 25 test boxes.

### Size, RAM and latency (`results/int8_ptq/bench_pc_x86.csv`, `tools/bench_onnx.py`)

Measured on a development PC (Intel i5-12500H, ONNX Runtime 1.23, batch 1, 4 threads). These numbers are only a
reference: the deployment numbers must be measured on the Raspberry Pi 5 with the same tool.

| Model | Size | Extra RAM (session / peak) | Latency median |
|---|---|---|---|
| v5 EfficientNet-B0 FP32 | 16.1 MB | 59 / 77 MB | 5.1 ms |
| v5 EfficientNet-B0 INT8 | 5.0 MB | 20 / 48 MB | 9.4 ms |
| v5 MobileNetV3-Small FP32 | 6.1 MB | 25 / 33 MB | 1.3 ms |
| v5 MobileNetV3-Small INT8 | 1.9 MB | 13 / 24 MB | 2.6 ms |
| Pest YOLOv8n FP32 | 13.6 MB | 46 / 100 MB | 124 ms |
| Pest YOLOv8n INT8 | 3.9 MB | 17 / 89 MB | 175 ms |

INT8 cuts model size by 3.2-3.5x and RAM by up to 3x, but is slower than FP32 on this x86 CPU: S8S8 activations are
not ONNX Runtime's fast path on Intel (a UINT8-activation prototype was faster there), and the mixed-precision
boundaries add conversion steps. S8S8 is the recommended path on Arm, so the speed comparison is decided on the Pi 5.

## Recommended models

| Task | Model | Notes |
|---|---|---|
| Tomato disease, Phase 1 demo (6 classes) | v5 EfficientNet-B0, seed 7 | Field accuracy 76% (crops); 88% on answered photos with the 0.85 "uncertain" threshold; INT8 5.0 MB with no meaningful accuracy loss |
| Tomato disease, small fallback (6 classes) | v5 MobileNetV3-Small, seed 42 | Field accuracy 75% (crops); INT8 1.9 MB |
| Tomato disease, all 10 classes (extended coverage) | v4 EfficientNet-B0, seed 7 | Field macro F1 about 0.62 |
| Tomato disease, 5 classes (earlier alternative) | v3 EfficientNet-B0, seed 42 | Field macro F1 about 0.78 on a different class set and test split |
| Insect pests | YOLOv8n fine-tuned with negatives | Confidence threshold 0.2 (FP32 and INT8) |

Download links and input specifications are in `models/README.md`.
