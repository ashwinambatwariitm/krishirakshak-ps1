# KrishiRakshak PS1 - Complete Project Handoff

**Handoff date:** 1 November 2026  
**Project:** KrishiRakshak (this repository)  
**Purpose:** Give any team member enough context to continue the Bharat AI-SoC PS1 project without repeating the earlier analysis or making incompatible architectural decisions.

> This document records the design decisions made at the start of the project (1 November 2026). Sections 10, 11 and 13 describe the state at that time. Current training results are in [RESULTS.md](RESULTS.md).

---

## 1. User objective

This project is a solution for **PS1 of the Bharat AI-SoC Challenge 2026-27**:

> An offline crop-disease/pest detection and advisory system for farmers.

The intended product should:

1. Accept a crop image from a camera or file.
2. Detect disease and/or pests.
3. Estimate confidence and severity.
4. Retrieve verified agricultural guidance from a local knowledge base.
5. Use a Llama-family model to produce a useful explanation/advisory.
6. Run offline on Arm hardware, especially a **Raspberry Pi 5 with 8 GB RAM**.
7. Use **ExecuTorch** for the Llama advisory/reasoning component.
8. Support English and preferably Hindi.
9. Be implemented with a C/C++-compatible inference path for deployment.
10. Include reproducible evaluation, model-size/latency measurements, and a technical report/demo.

The team has prior experience training a road-anomaly model, exporting it to ONNX, and running C/C++ inference on a Raspberry Pi. The goal is therefore a practical export/deployment workflow rather than only a Python research prototype.

---

## 2. Authoritative challenge references

- Official challenge page: <https://arm-education.github.io/Arm-Developer-Labs/Bharat_AI_SoC_2026_27.html>
- Local detailed challenge reference: [info.md](./info.md)
- Local PS1 problem statement: [PS1_Agriculture_Food_Security.md](./PS1_Agriculture_Food_Security.md)
- Arm ExecuTorch course: <https://learn.arm.com/courses/executorch-on-arm/>
- Arm online resources: <https://arm-education.github.io/online-resources-arm/>

The official webpage remains authoritative if dates, requirements, or submission instructions change. The working Phase 1 deadline recorded earlier is **23 November 2026**, but it must be rechecked before submission.

PS1 requires the Llama and ExecuTorch components. ONNX is optional for the vision models; it is not a replacement for the required ExecuTorch Llama deployment.

---

## 3. Agreed high-level architecture

The recommended product pipeline is:

```text
Camera/image
  -> image-quality checks and OpenCV preprocessing
  -> disease classifier
  -> independent pest detector
  -> estimated severity
  -> local verified agricultural knowledge base
  -> structured prompt/context
  -> Llama-family advisory model through ExecuTorch
  -> English/Hindi user interface
```

Recommended C++ deployment split:

```text
Disease model: ONNX Runtime C++ (or another measured Arm runtime)
Pest model: ONNX Runtime C++ or HailoRT if an AI HAT is later used
Image processing: OpenCV
Knowledge base: JSON or SQLite
Advisory model: Llama through ExecuTorch C++
Coordinator: C++
```

Do **not** initially merge disease and pest weights into one ordinary classifier:

- Disease is primarily an image-level classification problem.
- Pest detection generally needs object detection and bounding boxes.
- Different datasets have different label spaces and annotation formats.
- Separate models allow independent evaluation and safer future expansion.
- An inference coordinator can combine their structured outputs.

The pest model should remain independent even when the disease gate predicts "healthy"; a plant can look healthy while insects are present.

---

## 4. Scope decisions

### 4.1 Initial disease scope

The first practical MVP is a tomato disease system. The proposed initial classes are:

1. Healthy
2. Early blight
3. Late blight
4. Leaf mold
5. Septoria leaf spot

The earlier plan also mentions an "unknown/poor-quality" route. This should preferably be implemented as an image-quality/uncertainty rejection path rather than pretending that an ordinary disease classifier has learned every possible unknown condition.

PlantVillage contains additional tomato classes, including bacterial spot, spider mites, target spot, tomato yellow leaf curl virus, and tomato mosaic virus. These are possible later additions, but the first release should not expand the class list before the five-class baseline is reliable.

### 4.2 Pest scope

Pest detection is a separate workstream and is not yet trained. IP102, AgriPest, and Pest24 were discussed as possible sources, but the current notebook is disease-only.

Important label distinction:

- **Disease dataset:** leaf/image-level classes.
- **Pest dataset:** often insect categories plus bounding boxes or detection annotations.
- IP102 is a pest dataset, not a plant-disease dataset.

Tomato remains the safest first disease scope. Maize/corn was identified as a stronger future crop-overlap candidate between disease and pest datasets, but it should not displace the tomato MVP without a deliberate scope decision.

### 4.3 Languages

Initial target:

- English
- Hindi

The advisory model must be grounded in verified local content. It should explain and localise known guidance, not invent pesticide dosages or treatment instructions.

---

## 5. Dataset strategy

### PlantVillage - training baseline

Use the **color** configuration only for the first experiment:

```python
load_dataset("mohanty/PlantVillage", "color")
```

PlantVillage is large, consistently labelled, and useful for establishing a reproducible baseline. However, most images are controlled, single-leaf, and have relatively uniform backgrounds.

Known metadata discrepancy:

- Official repository: approximately 54,306 images, 38 classes, 14 crops, 26 diseases.
- TensorFlow Datasets: approximately 54,303 examples.
- Kaggle copies: approximately 54,303-54,305.

The exact downloaded copy must be profiled locally. Record:

- Source and version/date.
- Total count.
- Class distribution.
- Image dimensions and channels.
- Corrupt files.
- Exact duplicate or near-duplicate images.
- Train/validation/test counts.

Do not accidentally combine color, grayscale, and segmented PlantVillage variants.

### PlantDoc - external field-domain evaluation

PlantDoc is smaller and noisier but more representative of real field/web imagery. It should first be used as an **untouched external evaluation set**, not automatically merged into training.

Report PlantVillage and PlantDoc results separately. Never combine them into one accuracy number because the domain gap is important evidence.

Compatible labels require manual review. For example, PlantDoc "Tomato Early blight leaf" may match PlantVillage early blight, but label names alone are not sufficient proof.

Optional later procedure:

1. Train on PlantVillage.
2. Evaluate on held-out PlantVillage.
3. Evaluate the same model on PlantDoc.
4. Only then consider carefully selected PlantDoc fine-tuning.
5. Preserve an untouched PlantDoc test subset.

### CCMT - deferred

CCMT includes tomato, cassava, maize, and cashew classes with mixed backgrounds and lighting. It may be used later for external testing or carefully controlled fine-tuning.

Do not automatically map broad labels such as `Tomato - leaf blight` to PlantVillage `early_blight` or `late_blight`. The definitions may not match. Septoria may be more compatible but still requires manual inspection.

### Pest datasets - deferred

- **IP102:** broad insect-pest classification/detection resource; use later for a separate pest model.
- **AgriPest:** object-detection task involving crops such as wheat, rice, corn, and rape; use later.
- **Pest24:** trap-camera pest imagery; different from ordinary leaf photographs; defer.

### Dataset workbook

[crop_datasets_analysis.xlsx](./crop_datasets_analysis.xlsx) contains the team's dataset analysis:

- `Master`
- `Classes`
- `Preprocessing plan`

It is a central reference for class lists, counts, crop overlap, and preprocessing decisions.

---

## 6. Augmentation decisions

A specific requirement is that PlantVillage images be made more field-like, similar to PlantDoc, without storing a huge set of augmented files.

Agreed approach: **online/dynamic augmentation during training**.

Recommended training-only transformations:

- Resize and random crop.
- Horizontal flip.
- Mild rotation.
- Scale and translation.
- Brightness/contrast variation.
- Mild saturation/hue variation.
- Mild blur.
- Mild noise or JPEG-compression simulation.

Do not save augmented images. Generate them in memory and discard each tensor after the training step.

Do **not** apply random augmentation to:

- Validation data.
- Test data.
- PlantDoc external test data.
- Final Raspberry Pi camera evaluation images.

Split original images before augmentation. Every augmented version of an image must remain in the same split as its source. Check duplicate and near-duplicate leakage.

Background replacement/compositing was discussed but deferred because it is more complex and can create unrealistic artefacts. Establish a clean baseline first.

---

## 7. Model decisions

### Disease model

Primary recommendation:

- **MobileNetV3-Small**, ImageNet initialisation.

Comparison candidate:

- EfficientNet-B0 or EfficientNet-Lite.

The final choice must be based on:

- PlantVillage macro F1.
- PlantDoc macro F1.
- Diseased recall.
- Confusion matrix.
- Export equivalence.
- Raspberry Pi latency.
- RAM usage.
- Thermal behaviour.

Training accuracy alone is not a sufficient selection criterion.

### Two-stage disease design

The team proposed copying the approach from the paper **Deep Learning Based Mobile Application for Automated Plant Disease Detection**:

1. Stage 1: Healthy vs Diseased.
2. Stage 2: classify the disease.

This is a valid experiment and is included in the notebook. Important failure mode:

- If Stage 1 falsely predicts Healthy, Stage 2 will not run and the disease is missed.

Therefore:

- Prioritise diseased recall in Stage 1.
- Use a confidence/uncertainty threshold.
- Route uncertain predictions to Stage 2 or return "uncertain, retake image".
- Train a direct multiclass baseline as a comparison.

The two-stage cascade must not be assumed better until measured against a single multiclass model.

### Pest model

Recommended future starting point:

- YOLOv8n or another lightweight YOLO detector.
- Compare against a lightweight YOLOv5/IP102 approach where appropriate.

The pest model requires detection annotations and should be benchmarked separately from disease classification.

### Advisory model

Start with:

- Llama 3.2 1B Instruct or the smallest supported Llama-family model.

Consider Llama 3.2 3B only after measuring the 1B system. Do not begin with a 7B/8B model on the Pi without a measured memory plan.

The advisory model receives structured data such as:

```json
{
  "crop": "tomato",
  "disease": "late_blight",
  "confidence": 0.91,
  "severity": "estimated_moderate",
  "pests": [],
  "image_quality": "acceptable",
  "verified_context_id": "tomato_late_blight_v1"
}
```

The local knowledge base should be the source of truth for symptoms, prevention, and treatment guidance. Llama should:

- Explain the prediction.
- Summarise verified guidance.
- Translate/localise the answer.
- State uncertainty and recommend expert confirmation when appropriate.

It should not independently invent facts, diagnoses, pesticide dosages, or unsafe treatment instructions.

---

## 8. Training, checkpoints, export, and quantisation

The expected workflow is:

```text
Train in FP32
  -> select best validation checkpoint
  -> validate checkpoint
  -> export FP32 ONNX
  -> compare PyTorch and ONNX outputs
  -> create FP16/INT8 candidates
  -> evaluate accuracy and field-domain performance
  -> benchmark on Raspberry Pi
  -> select final format
```

A common question is whether training creates `best.pt`. It may create `best.pt`, `best_checkpoint.pt`, or another framework-specific name. It is a training checkpoint, not automatically a deployment model.

For classification, select checkpoints using validation macro F1 or balanced accuracy, especially because class imbalance is likely. Record:

- Epoch.
- Training loss.
- Validation loss.
- Accuracy.
- Macro F1.
- Per-class precision/recall/F1.
- Confusion matrix.
- Checkpoint path.

Expected precision candidates:

- FP32: reference and accuracy baseline.
- FP16: possible memory/performance option depending on runtime.
- INT8: likely candidate for lightweight vision models, but must be measured.

INT8 calibration must use representative images and must be validated on both held-out PlantVillage and PlantDoc. Do not decide based solely on model file size.

Measure on Pi:

- Accuracy/macro F1.
- Inference latency, including preprocessing.
- Peak RAM.
- CPU utilisation.
- Temperature.
- Throttling.
- Startup time.
- Sustained repeated-inference behaviour.

Llama memory is separate from vision memory and includes model weights, runtime buffers, tokenizer, prompt, generated tokens, and KV cache.

---

## 9. Paper reviewed: mobile application approach

Local paper:

Deep_Learning_Based_Mobile_Application_for_Automated_Plant_Disease_Detection.pdf (see [papers.md](papers.md))

The paper uses a custom PyTorch CNN rather than MobileNet, EfficientNet, or YOLO:

- Conv layer: 32 filters.
- Conv layer: 64 filters.
- Conv layer: 128 filters.
- Conv layer: 128 filters.
- ReLU and max pooling.
- Dense layer with 256 units.
- Dropout 0.5.
- Softmax output.

Main experiment:

- Healthy vs Diseased binary classification on PlantVillage.

Reported results:

- Training accuracy: 95.35%.
- Validation accuracy: 92.37%.
- Test accuracy: 92.06%.
- Approximate precision/recall/F1: around 90%.

Severity uses OpenCV grayscale, blur, thresholding, morphology, and infected-pixel ratio.

The paper is useful as a baseline/reference for the two-stage idea, but it is not sufficient as the final PS1 architecture because:

- It is mainly binary.
- It uses a Flask backend/mobile application rather than a fully offline ExecuTorch system.
- It does not provide the required Llama/ExecuTorch integration.
- It has internal reporting inconsistencies, including references to both binary and 39-class results.

Severity from PlantVillage/PlantDoc should initially be called **estimated severity**, not ground-truth severity, unless expert-labelled severity data is obtained.

---

## 10. Current Kaggle notebook

Local notebook:

`ps1_two_stage_plantvillage.ipynb` (first prototype, replaced by `training/src/`)

Kaggle notebook:

<https://www.kaggle.com/code/ashvinambatwar/ps1-two-stage-plantvillage>

The notebook:

- Loads `mohanty/PlantVillage` `color`.
- Profiles labels.
- Creates reproducible train/validation/test splits.
- Applies online training augmentation only.
- Builds a Healthy/Diseased gate.
- Builds a full PlantVillage disease classifier.
- Uses MobileNetV3-Small with ImageNet initialisation.
- Selects checkpoints by validation macro F1.
- Saves `health_gate_best.pt`.
- Saves `disease_classifier_best.pt`.
- Exports FP32 ONNX models.
- Includes notes for later ONNX equivalence validation and INT8 work.

Expected training calls:

- Health gate: 12 epochs.
- Disease classifier: 15 epochs.

Notebook JSON was validated locally with:

```bash
python3 -m json.tool ps1_two_stage_plantvillage.ipynb
```

### Kaggle execution state at handoff

- Kaggle CLI is installed and authenticated locally.
- The notebook was successfully uploaded as a private Kaggle notebook.
- Internet was enabled.
- The initial GPU upload was rejected because the account had reached the maximum batch GPU session count.
- It was re-uploaded successfully with CPU execution:
  `ashvinambatwar/ps1-two-stage-plantvillage`
- At handoff, the notebook had been uploaded/queued, but no completed training metrics, checkpoints, ONNX files, or benchmark results had yet been retrieved.
- The Kaggle output directory exists locally but contains no confirmed final artifacts yet.

Useful local checks:

```bash
kaggle kernels list --mine --search ps1-two-stage-plantvillage --page-size 5
kaggle kernels output ashvinambatwar/ps1-two-stage-plantvillage -p /path/to/output
```

If GPU capacity becomes available, re-upload with `"enable_gpu": true` in the temporary metadata used for `kaggle kernels push`. Do not expose or inspect Kaggle credentials in project documentation.

The temporary upload folder `.kaggle_ps1_upload/` is operational state, not a final project deliverable. It can be removed later if no longer needed, but do not delete the notebook or outputs.

---

## 11. Current repository/workspace files

- [info.md](./info.md): detailed challenge reference and official URL.
- [plan_phase1.md](./plan_phase1.md): detailed Phase 1 architecture, milestones, dataset plan, deployment plan, evaluation checklist, and safety requirements.
- [dataset_research.md](./dataset_research.md): 28 research papers, datasets, implementation links, Edge AI resources, Llama/ExecuTorch resources, and notes.
- [crop_datasets_analysis.xlsx](./crop_datasets_analysis.xlsx): team's dataset analysis workbook.
- [PS1_Agriculture_Food_Security.md](./PS1_Agriculture_Food_Security.md): local PS1 problem statement.
- `ps1_two_stage_plantvillage.ipynb` (first prototype, replaced by `training/src/`): Kaggle-ready training notebook.
- 1511.08060v2.pdf (see [papers.md](papers.md)): PlantVillage reference.
- PlantDoc_dataset.pdf (see [papers.md](papers.md)): PlantDoc reference.
- Deep_Learning_Based_Mobile_Application_for_Automated_Plant_Disease_Detection.pdf (see [papers.md](papers.md)): reviewed custom-CNN paper.
- RP_9788743814399C9.pdf (see [papers.md](papers.md)): local research paper requiring context-specific review if used.


---

## 12. Design questions and how they were resolved

### "Can disease and pest models be combined?"

Yes, at the application/coordinator level, not by blindly merging weights. Keep disease classification and pest detection separate, then combine structured outputs before advisory generation.

### "Can the same plant disease appear in the pest dataset?"

The correct overlap is the **crop**, not the disease label. A crop can have both disease and pest models. The same disease should not be treated as an insect-pest class.

### "Can we use the same crop in both datasets?"

Yes. Maize/corn was identified as a promising future overlap. Tomato is still the safer first disease-only MVP because the available pest data does not yet provide a verified, compatible tomato-pest subset.

### "PlantDoc is better than PlantVillage, so should it replace PlantVillage?"

No. PlantDoc is more field-realistic but smaller/noisier. PlantVillage is larger and cleaner for baseline training. Use PlantVillage for training and PlantDoc for external domain evaluation, then optionally fine-tune with a carefully held-out PlantDoc subset.

### "Is ONNX required?"

No. ONNX is optional for the vision models but is a practical choice for C++ inference on the Pi. ExecuTorch is required for the Llama advisory component.

### "Should we train separate weights and combine them later?"

Yes for disease and pest, because they are different tasks. Export each model separately, then write an inference coordinator. Do not combine incompatible label spaces into one classifier.

### "Should we check FP32, FP16, and INT8 during training?"

Train a stable FP32 model first, then export and benchmark precision variants. Final choice must be based on accuracy, field-domain robustness, latency, RAM, and thermal measurements.

### "Should we use a Healthy/Diseased gate first?"

Yes, as an experiment. Also train a direct multiclass baseline. The cascade is only preferable if it improves the required metrics without unacceptable false-Healthy failures.

### "Can augmentation make PlantVillage look like PlantDoc?"

Online realistic augmentation can reduce the domain gap but cannot make PlantVillage equivalent to PlantDoc. Keep PlantDoc untouched for honest external testing.

### "Should augmented images be stored?"

No. Generate them dynamically during training only.

### "Can the paper's custom CNN be the final model?"

It can be a baseline, but MobileNetV3-Small is currently the preferred lightweight disease model because it is more suitable for edge deployment and comparison.

---

## 13. Immediate next steps (as of 1 November 2026)

Perform these in order:

1. Check the Kaggle notebook status and retrieve outputs:
   ```bash
   kaggle kernels output ashvinambatwar/ps1-two-stage-plantvillage -p /tmp/ps1_output
   ```
2. If the run failed, inspect the actual error before changing code.
3. If CPU training is too slow, retry with GPU after the account's active GPU sessions finish.
4. Verify the actual PlantVillage count and class distribution from the downloaded copy.
5. Confirm that the selected five tomato classes exist and are mapped correctly.
6. Inspect health-gate and disease-classifier validation metrics and confusion matrices.
7. Add PyTorch-vs-ONNX output-equivalence validation.
8. Add ONNX INT8 calibration/export and compare FP32 versus INT8.
9. Add a direct five-class/multiclass tomato baseline and compare it with the cascade.
10. Download/profile PlantDoc separately and run external evaluation without leakage.
11. Record actual metrics in a results file or in the relevant project documentation.
12. Choose MobileNetV3-Small versus EfficientNet-B0/Lite based on PlantDoc performance and Pi benchmarks.
13. Implement the C++ image-quality, preprocessing, ONNX inference, and coordinator path.
14. Define a local JSON/SQLite agricultural knowledge base with citations/versioning.
15. Convert and run a small Llama model with ExecuTorch on the Pi.
16. Measure Llama memory, first-token latency, generation latency, and total advisory latency.
17. Add the separate pest-detection workstream only after the disease vertical slice is working.
18. Build the offline end-to-end demo and technical report.

---

## 14. Definition of done for the first vertical slice

The first usable milestone is complete when:

- A tomato image can be processed offline.
- Image quality failures are rejected safely.
- A disease prediction and confidence are returned.
- The two-stage and direct multiclass baselines have been compared.
- PlantVillage test results and PlantDoc external results are reported separately.
- The selected model exports successfully.
- C++ inference reproduces the Python/ONNX result within a documented tolerance.
- A local knowledge-base entry is retrieved.
- Llama generates an advisory through ExecuTorch on the Pi.
- The advisory states uncertainty and does not invent unsupported treatment claims.
- English and Hindi output are demonstrated.
- RAM, latency, CPU, temperature, and throttling measurements are recorded.
- The system works with internet disabled.

---

## 15. Important cautions

1. Do not claim PlantVillage accuracy as field performance.
2. Do not leak PlantDoc or augmented images into training.
3. Do not call heuristic pixel-ratio severity "ground truth".
4. Do not let a false Healthy gate silently suppress all disease analysis; implement uncertainty handling.
5. Do not run pest detection only when the disease model says diseased.
6. Do not merge disease and pest labels just because the crop is the same.
7. Do not treat `best.pt` as a deployment artifact without export and equivalence testing.
8. Do not claim INT8 is better without field-domain and Pi measurements.
9. Do not use Llama as the agricultural source of truth; ground it in local verified content.
10. Do not expose Kaggle credentials or put them in the repository.
11. Recheck the official challenge page before submission.

