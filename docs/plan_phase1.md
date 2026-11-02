# Phase 1 Plan - Offline Crop Disease/Pest Detection and Advisory

## Project

**Working name:** KrishiRakshak  
**Challenge:** Bharat AI-SoC Challenge 2026-27  
**Problem statement:** PS1 - Offline crop-disease/pest detection and advisory for farmers  
**Target hardware:** Raspberry Pi 5 with 8 GB RAM  
**Primary deployment target:** Raspberry Pi 5 CPU  
**Optional future accelerator:** Raspberry Pi AI HAT+ / AI HAT+ 2 with Hailo NPU  
**Phase 1 submission deadline:** 23 November 2026

This document is the working plan for the Phase 1 Open Qualifying submission. It is intended to be a practical implementation guide and a checklist for the source code, application, demonstration video, and technical report.

## Official references

- **Official challenge page:** <https://arm-education.github.io/Arm-Developer-Labs/Bharat_AI_SoC_2026_27.html>
- **Local challenge reference:** [info.md](./info.md)
- **Local PS1 requirements:** [PS1_Agriculture_Food_Security.md](./PS1_Agriculture_Food_Security.md)
- **ExecuTorch course:** <https://learn.arm.com/courses/executorch-on-arm/>
- **Arm learning resources:** <https://arm-education.github.io/online-resources-arm/>

Before submitting, check the official challenge page for changes to dates, technical requirements, submission instructions, and terms.

---

## 1. Phase 1 objective

Build and demonstrate a working offline AI assistant that can:

1. Capture or receive a crop-leaf image.
2. Detect a selected crop disease or pest condition.
3. Report a confidence score.
4. Estimate or classify severity.
5. Retrieve verified agricultural guidance from a local knowledge base.
6. Use a Llama-family model for explanation or advisory reasoning.
7. Run the Llama advisory component on-device through ExecuTorch.
8. Present the result in English and at least one local language, preferably Hindi for the first release.
9. Continue working with internet connectivity disabled.
10. Handle uncertain, blurry, dark, or unsupported images safely.

The Phase 1 release should be a focused, reliable vertical slice rather than a broad system supporting many crops and diseases.

## 2. Recommended Phase 1 scope

### Crop

Start with **tomato**. It is a practical first choice because public datasets and examples are available and several common leaf conditions are visually distinguishable.

### Initial classes

Use a small set of classes:

1. Healthy
2. Early blight
3. Late blight
4. Leaf mould
5. Unknown or poor-quality image

If the available data or validation quality is insufficient, reduce the scope to fewer conditions. Do not add a class merely to make the feature list larger.

### Languages

Implement:

- English
- Hindi

The first release should prioritise correct and understandable advice over the number of supported languages.

### User experience

The first application should provide:

- Camera capture or image selection
- Image-quality validation
- Disease or pest prediction
- Confidence score
- Severity level
- Symptoms and explanation
- Immediate actions
- Prevention guidance
- Expert-help recommendation for uncertain or severe cases
- English/Hindi language selection
- Offline result history if time permits

Voice input and text-to-speech are optional enhancements and should not delay the core offline workflow.

---

## 3. System architecture

```text
Camera or image upload
          |
          v
Image-quality checks and OpenCV preprocessing
          |
          v
Lightweight crop-disease vision model
          |
          v
Condition, confidence, and severity result
          |
          v
Local verified agricultural knowledge base
          |
          v
Llama-family model through ExecuTorch
          |
          v
English or Hindi farmer-friendly advisory
```

### Component responsibilities

| Component | Responsibility | Phase 1 runtime |
|---|---|---|
| Camera or USB camera | Capture crop images | Raspberry Pi 5 |
| OpenCV | Image capture, resizing, quality checks, preprocessing | Raspberry Pi CPU |
| Vision model | Identify crop condition | Raspberry Pi CPU initially |
| Severity logic | Estimate severity from model output or affected area | Raspberry Pi CPU |
| Local knowledge base | Store verified symptoms and interventions | JSON or SQLite |
| Llama model | Explain and format advisory using supplied context | ExecuTorch on Raspberry Pi CPU |
| User interface | Display results and language selection | Local web UI, desktop UI, or attached display |
| Optional Hailo pipeline | Accelerate compatible vision inference | HailoRT on Hailo NPU |

### Important pipeline rule

If a Hailo accelerator is added later:

```text
Vision model -> HailoRT -> Hailo NPU
Llama model  -> ExecuTorch -> Raspberry Pi Arm CPU
```

These are separate pipelines and must be documented separately. Hailo is optional for Phase 1; CPU-only operation is a valid starting point and provides a useful baseline.

---

## 4. Raspberry Pi 5 deployment plan

### Hardware

Recommended equipment:

- Raspberry Pi 5 with 8 GB RAM
- Official or reliable USB-C power supply
- Active cooling
- 64 GB or larger high-quality microSD card, preferably a USB 3 SSD
- Raspberry Pi camera module or USB camera
- Stable lighting for image capture
- Optional display, microphone, and speaker

Use an SSD if possible. Datasets, model files, Python packages, logs, and test images can consume substantial storage.

### Operating system and environment

Use:

- 64-bit Raspberry Pi OS
- Python 3
- A deployment virtual environment
- Git
- OpenCV
- NumPy
- Pillow
- ExecuTorch runtime
- JSON or SQLite for local advisory data

Keep training dependencies separate from deployment dependencies.

#### Training environment

- PyTorch
- torchvision
- Dataset tooling
- Evaluation and visualisation tools
- Export and conversion tools

#### Raspberry Pi deployment environment

- OpenCV
- NumPy
- Pillow
- ExecuTorch runtime
- Application code
- Local knowledge-base files

Training should normally be performed on a more powerful computer. The Raspberry Pi should perform camera capture, preprocessing, inference, advisory generation, and user interaction.

### Initial device checks

Record the following before development:

```bash
uname -m
cat /etc/os-release
free -h
vcgencmd get_throttled
```

Confirm that:

- The system is using a 64-bit ARM environment.
- Cooling is installed and working.
- The power supply is adequate.
- The device is not throttling.
- Sufficient disk space is available.

Record the operating-system version, kernel version, Python version, ExecuTorch version, and model versions in the technical report.

---

## 5. Vision model plan

### Model choice

Start with a lightweight image-classification model:

- MobileNetV3
- EfficientNet-Lite
- A compact custom CNN
- A small YOLO variant only if object localisation is necessary

Classification is recommended for the first version because it is simpler to train, export, deploy, and measure on the Raspberry Pi CPU.

### Vision model input and output

Example:

```text
Input: crop-leaf image

Output:
- Selected crop: tomato
- Predicted condition: early blight
- Confidence: 0.87
- Optional affected-area estimate
- Severity: medium
```

### Image-quality checks

Before inference, check for:

- Excessive darkness
- Excessive brightness
- Blur
- Very small or absent leaf region
- Unsupported crop
- Empty or invalid image

If the image is poor, do not produce a confident diagnosis. Ask the user to capture another image.

### Confidence policy

Use thresholds only after validating them on a held-out test set. An initial engineering policy can be:

```text
Confidence >= 0.80:
    Show likely diagnosis.

Confidence from 0.55 to 0.80:
    Show possible diagnosis and request another image.

Confidence < 0.55:
    Do not diagnose; ask for a clearer image or expert review.
```

These values are starting points, not agricultural standards. Document the selected thresholds and the validation results.

### Severity estimation

If a segmentation or detection model estimates affected leaf area, an initial rule may be:

```text
Low:    less than 10% affected
Medium: 10-30% affected
High:   more than 30% affected
```

If the system uses classification only, describe severity as an estimated category rather than an exact measurement. Validate thresholds using labelled examples or expert feedback.

### Model evaluation

Measure:

- Accuracy
- Precision
- Recall
- F1 score
- Confusion matrix
- Per-class performance
- Unknown/uncertain rejection rate
- Inference latency
- Model size
- RAM usage

Test on images that were not used during training. Where possible, split data by plant, field, or source rather than randomly duplicating similar images across training and test sets.

---

## 6. Dataset plan

Possible sources named by the challenge include:

- PlantVillage
- Cassava datasets
- IP102

For the tomato-first plan, select the dataset that best matches the chosen classes and expected field conditions.

For every dataset, record:

- Name and URL
- Version or access date
- Licence
- Number of images
- Classes used
- Preprocessing
- Train/validation/test split
- Known limitations

Avoid claiming real-world performance from clean laboratory images alone. Add a separate field-style test set containing different lighting, backgrounds, cameras, leaf angles, and disease stages.

Do not commit large datasets or model weights to GitHub unless the licence and repository limits allow it. Provide download and preparation instructions instead.

### Dataset decisions from the workbook analysis

The workbook [crop_datasets_analysis.xlsx](./crop_datasets_analysis.xlsx) was reviewed across its `Master`, `Classes`, and `Preprocessing plan` worksheets. The recommended Phase 1 dataset strategy is:

| Purpose | Dataset | Decision |
|---|---|---|
| Initial tomato disease training | PlantVillage | **Use now** |
| Real-world tomato validation | PlantDoc | **Use now** |
| Additional field diversity | CCMT (Ghana) | **Use later, after verification** |
| Tomato pest support | IP102 | **Defer; separate future task** |
| Wheat, rice, maize, and rape pest detection | AgriPest | **Defer; separate object-detection task** |
| Trap-based pest detection | Pest24 | **Defer; different capture environment** |
| Cassava disease assistant | Cassava Leaf Disease | **Alternative crop, not the current tomato plan** |
| Rice disease assistant | Paddy Doctor | **Alternative crop, not the current tomato plan** |
| General in-the-wild robustness | PlantWild | **Future research** |
| Segmentation and severity research | PlantSeg | **Future research** |

Do not combine all datasets into one classifier. They represent different crops, label types, capture environments, and tasks.

### Phase 1 tomato classes

Use the following initial five-class classifier:

1. Healthy
2. Early blight
3. Late blight
4. Leaf mold
5. Septoria leaf spot

PlantVillage contains substantial tomato data for these classes, including approximately 1,000 early-blight images, 1,909 late-blight images, 952 leaf-mold images, 1,771 Septoria leaf-spot images, and 1,591 healthy images. Verify final counts from downloaded files rather than relying only on workbook estimates.

PlantVillage also contains tomato bacterial spot, spider mites, target spot, tomato yellow leaf curl virus, and tomato mosaic virus. Keep these as possible later classes unless the first five-class system is already reliable.

### Recommended dataset split

Use the datasets in separate roles:

```text
Training:
    PlantVillage tomato classes

Internal validation/test:
    Held-out PlantVillage tomato images

External field-style test:
    PlantDoc tomato images
```

Report PlantVillage and PlantDoc results separately. Do not combine their scores into one accuracy value. This makes the domain gap visible:

- PlantVillage is mostly single-leaf, laboratory-style imagery with uniform backgrounds.
- PlantDoc contains field or web-sourced images with clutter, varied lighting, and variable resolutions.

This external test is important because a model that performs well on PlantVillage may fail on real farmer photographs.

### Optional CCMT use

CCMT contains tomato, cassava, maize, and cashew classes with mixed backgrounds and lighting. Its tomato classes include leaf blight, leaf curl, Septoria leaf spot, Verticillium wilt, and healthy.

Use CCMT first as an additional external test set. Only use it for fine-tuning after:

- Downloaded files are profiled.
- The licence is recorded.
- Actual class counts are confirmed.
- Augmented or duplicate images are identified.
- Class definitions are manually compared with PlantVillage and PlantDoc.

Do not automatically merge the broad CCMT label `Tomato - leaf blight` with PlantVillage `early blight` or `late blight`. The label may not represent the same condition. Septoria leaf spot is a more likely match, but it still requires manual review.

### Datasets to defer

- **IP102:** Use later for a separate insect-pest model. It contains many pest classes and does not directly match the current tomato disease MVP.
- **AgriPest:** Use later for object detection with bounding boxes. It covers wheat, rice, corn, and rape rather than the current tomato disease scope.
- **Pest24:** Use later for trap-camera pest detection; its imagery does not represent normal crop-leaf photographs.
- **Cassava Leaf Disease:** Use only if the project changes from tomato to cassava.
- **Paddy Doctor:** Use only if the project changes to rice.
- **PlantWild:** Consider later for complex in-the-wild robustness testing.
- **PlantSeg:** Consider later for segmentation-based affected-area estimation and severity research.

### Dataset profiling requirements

Before training, profile each downloaded dataset and record:

- Image count
- Per-class distribution
- Width and height
- File formats
- Corrupt files
- Duplicate or near-duplicate images
- Label names
- Bounding-box or mask availability
- Existing train/validation/test split
- Augmentation history
- Licence and source URL

The workbook correctly recommends profiling files rather than trusting unverified counts. Treat values marked as memory-based or requiring verification as provisional.

Create a manifest with at least:

```text
image_path
dataset
original_class
unified_class
crop
split
width
height
licence
```

Example:

```csv
image_path,dataset,original_class,unified_class,crop,split
plantvillage/Tomato___Early_blight/a.jpg,PlantVillage,Tomato___Early_blight,early_blight,tomato,train
plantdoc/Tomato Early blight leaf/b.jpg,PlantDoc,Tomato Early blight leaf,early_blight,tomato,external_test
```

### Label normalisation

Different datasets use different names for similar or broad conditions:

| Unified label | PlantVillage example | PlantDoc example | CCMT example | Recommendation |
|---|---|---|---|---|
| `healthy` | `Tomato___healthy` | `Tomato leaf` may require review | `Tomato - healthy` | Manually verify generic leaf images |
| `early_blight` | `Tomato___Early_blight` | `Tomato Early blight leaf` | No clearly equivalent class | PlantVillage and PlantDoc may be compatible |
| `late_blight` | `Tomato___Late_blight` | `Tomato leaf late blight` | No clearly equivalent class | PlantVillage and PlantDoc may be compatible |
| `leaf_mold` | `Tomato___Leaf_Mold` | `Tomato mold leaf` | No clearly equivalent class | Review before merging |
| `septoria_leaf_spot` | `Tomato___Septoria_leaf_spot` | `Tomato Septoria leaf spot` | `Tomato - septoria leaf spot` | Likely compatible after review |
| `bacterial_spot` | `Tomato___Bacterial_spot` | `Tomato leaf bacterial spot` | Not listed as a CCMT tomato class | PlantVillage and PlantDoc may be compatible |

Do not automatically merge broad labels with specific diseases. Every mapping must be reviewed and recorded in the manifest.

### Data leakage controls

- Split by original image before augmentation.
- Keep augmented copies in the same partition as their source image.
- Do not allow near-duplicate images in both training and test sets.
- Keep PlantDoc and the final field test set completely separate from training.
- If CCMT is used for fine-tuning, retain an untouched CCMT test subset.

### Training and evaluation sequence

1. Train a baseline on PlantVillage tomato classes.
2. Evaluate on a held-out PlantVillage test set.
3. Evaluate the same model on PlantDoc.
4. Inspect errors and document the domain gap.
5. Optionally add verified, compatible field images.
6. Re-test on untouched PlantDoc and CCMT subsets.
7. Compare the updated model against the baseline.

This sequence demonstrates measurable improvement rather than simply combining data and reporting a single inflated score.

### Severity limitation

The listed datasets generally do not contain validated severity labels. Therefore:

- Do not claim that the classifier learned severity from these datasets.
- Initially report severity as an estimated category.
- Base the estimate on confidence, visible affected area if available, and expert-reviewed rules.
- Consider segmentation masks or a separately expert-labelled severity dataset in the PoC phase.

If affected-area estimation is added, document the thresholds as engineering estimates rather than agricultural standards.

---

## 7. Local agricultural knowledge base

The knowledge base is the source of truth for agricultural guidance. Llama should explain and localise verified information, not invent treatment advice.

Store the information in JSON or SQLite. Example JSON structure:

```json
{
  "tomato_early_blight": {
    "crop": "tomato",
    "condition": "early blight",
    "symptoms": [
      "brown circular spots",
      "yellowing around lesions"
    ],
    "severity": {
      "low": [
        "remove affected leaves",
        "avoid wetting foliage while watering"
      ],
      "medium": [
        "remove heavily affected leaves",
        "improve spacing and airflow",
        "consult a local agricultural expert"
      ],
      "high": [
        "seek advice from a local agricultural officer",
        "follow locally approved crop-protection guidance"
      ]
    },
    "prevention": [
      "use disease-free seed",
      "rotate crops",
      "remove plant debris"
    ],
    "sources": [
      "Add verified agricultural source here"
    ]
  }
}
```

For every advisory entry:

- Record the source.
- Record the region where the advice applies.
- Distinguish prevention from treatment.
- Avoid unsupported pesticide names or dosages.
- Include a recommendation to consult an agricultural expert for serious or uncertain cases.
- Prepare an English version and a reviewed Hindi version.

---

## 8. Llama and ExecuTorch plan

### Model selection

Start with:

- Llama 3.2 1B Instruct, quantised if supported by the selected ExecuTorch workflow.

Consider Llama 3.2 3B Instruct only after the 1B model works and memory and latency measurements are acceptable. Do not begin with a large 7B or 8B model on the Raspberry Pi.

### Llama responsibilities

Llama should:

- Explain the detected condition in simple language.
- Convert structured results into a farmer-friendly response.
- Answer follow-up questions using only the local knowledge base.
- Present advice in English or Hindi.
- Clearly communicate uncertainty.

Llama should not:

- Invent a diagnosis.
- Invent pesticide names, dosages, or application schedules.
- Override the confidence policy.
- Pretend that an uncertain image is a confirmed diagnosis.
- Depend on an online API.

### Prompt structure

Example:

```text
You are an offline agricultural advisory assistant.

Detected crop: tomato
Detected condition: early blight
Confidence: 0.87
Severity: medium

Verified local guidance:
- Remove heavily infected leaves.
- Avoid overhead irrigation.
- Improve airflow.
- Consult a local agricultural expert before using pesticides.

Respond in Hindi using simple language.
Use only the verified guidance provided above.
Do not invent pesticide names, dosages, or unsupported treatments.
If confidence is low, recommend taking another photo or consulting an expert.
```

### ExecuTorch evidence to capture

Document and measure:

- Llama model name and version
- Model licence
- Quantisation method
- Export or conversion process
- ExecuTorch version
- Backend used
- Model file size
- RAM usage
- Model loading time
- First-token latency
- Full-response latency
- Device temperature and throttling state
- Behaviour with network connectivity disabled

The technical report and demonstration must make clear that the Llama advisory component runs locally through ExecuTorch on the Raspberry Pi Arm CPU.

---

## 9. Application workflow

The target workflow is:

1. Farmer opens the application.
2. Farmer takes a crop-leaf photograph or selects an existing image.
3. The application checks image quality.
4. OpenCV preprocesses the image.
5. The vision model predicts the likely condition.
6. The application calculates or estimates severity.
7. The local knowledge base retrieves matching verified guidance.
8. Llama receives the structured result and verified context.
9. ExecuTorch generates an offline explanation.
10. The application displays the result in the selected language.
11. The farmer can ask a follow-up question using the same local context.
12. The application recommends expert help when confidence is low or severity is high.

Example output:

```text
Likely condition: Tomato early blight
Confidence: 87%
Estimated severity: Medium

Immediate actions:
- Remove heavily affected leaves.
- Avoid overhead watering.
- Improve airflow around plants.

Important:
This is an offline AI-assisted estimate. For severe or uncertain cases,
consult a local agricultural officer.
```

---

## 10. Suggested repository structure

```text
ARM_AgriTech/
|-- app/
|   |-- android/
|   |-- pi_ui/
|   `-- web_demo/
|-- models/
|   |-- vision/
|   `-- llama/
|-- data/
|   |-- raw/
|   |-- processed/
|   `-- advisory/
|-- training/
|   |-- train.py
|   |-- evaluate.py
|   `-- export.py
|-- executorch/
|   |-- convert_model.py
|   `-- run_inference.py
|-- docs/
|   |-- architecture.md
|   |-- evaluation.md
|   `-- deployment.md
|-- demo/
|-- requirements.txt
|-- README.md
|-- info.md
|-- PS1_Agriculture_Food_ Security.md
`-- plan_phase1.md
```

Keep the final repository understandable to someone who did not build the project.

---

## 11. Milestones

### Milestone 1 - Hardware and camera

- Install 64-bit Raspberry Pi OS.
- Configure power and active cooling.
- Connect the camera.
- Capture and save test images.
- Verify that the camera works without internet access.
- Record hardware and software versions.

### Milestone 2 - Vision baseline

- Select one crop and initial disease classes.
- Prepare the dataset.
- Train or obtain a compact vision model.
- Export the model for Raspberry Pi inference.
- Run inference on the Pi.
- Measure accuracy, confidence behaviour, latency, model size, and memory.

### Milestone 3 - Image-quality and safety handling

- Add blur and brightness checks.
- Add unsupported-image handling.
- Add low-confidence rejection.
- Test healthy, diseased, poor-quality, and unrelated images.

### Milestone 4 - Advisory knowledge base

- Collect trusted agricultural guidance.
- Store structured entries in JSON or SQLite.
- Add severity-specific advice.
- Add sources and licence notes.
- Review English and Hindi content.

### Milestone 5 - ExecuTorch Llama

- Select a supported small Llama model.
- Convert and quantise it according to the ExecuTorch workflow.
- Run a simple offline prompt on the Pi.
- Connect Llama to structured vision results and verified context.
- Measure loading time, response latency, RAM use, and temperature.

### Milestone 6 - Complete application

Connect:

```text
camera -> image checks -> vision -> severity -> knowledge base -> Llama -> interface
```

Add language selection, result display, error messages, and an offline indicator.

### Milestone 7 - Evaluation

- Test different lighting conditions.
- Test different cameras.
- Test clean and damaged leaves.
- Test partial leaves and varied backgrounds.
- Test similar-looking conditions.
- Test images not present in the training dataset.
- Disable Wi-Fi and mobile data.
- Measure end-to-end latency and resource usage.
- Collect feedback from an agricultural expert or representative users if possible.

### Milestone 8 - Submission preparation

- Freeze the Phase 1 feature set.
- Clean the source repository.
- Add setup instructions.
- Verify licences.
- Record the demonstration video.
- Complete the technical report.
- Run the final offline test.
- Submit before 23 November 2026.

---

## 12. Evaluation plan

### Vision metrics

Report:

- Accuracy
- Precision
- Recall
- F1 score
- Per-class results
- Confusion matrix
- Unknown-image rejection rate
- False-positive examples
- False-negative examples

### System metrics

Report:

- Raspberry Pi model and RAM
- Operating-system version
- Python version
- Vision model size
- Llama model size
- RAM usage
- CPU utilisation where practical
- Model loading time
- Vision inference latency
- Llama first-token latency
- Complete advisory latency
- Total end-to-end latency
- Temperature and throttling observations
- Offline success rate

### User and language evaluation

Check:

- Is the advice understandable to a non-expert?
- Are disease names preserved accurately?
- Is Hindi reviewed by a fluent speaker?
- Does the response clearly state uncertainty?
- Does the response avoid unsupported treatment claims?
- Can a user recover from a poor image?

---

## 13. Demonstration video plan

The demonstration should show a complete and reproducible offline workflow:

1. Introduce the problem and target users.
2. Show the Raspberry Pi 5 and camera.
3. Show the system architecture briefly.
4. Disable Wi-Fi and mobile data.
5. Capture a real crop image.
6. Show image-quality validation.
7. Show the disease or pest prediction.
8. Show confidence and severity.
9. Show retrieved verified guidance.
10. Show the Llama-generated advisory through ExecuTorch.
11. Switch from English to Hindi.
12. Ask an offline follow-up question.
13. Demonstrate a poor-quality or uncertain image.
14. Show the safe fallback message.
15. Display latency, memory, model, and device information.
16. Explain limitations and future improvements.

The video should visibly prove that the system continues to function without internet connectivity.

---

## 14. Technical report outline

1. Abstract
2. Problem and target users
3. Motivation for offline edge AI
4. Proposed solution
5. System architecture
6. Raspberry Pi 5 hardware and software environment
7. Dataset sources, licences, and preparation
8. Vision model architecture and training
9. Vision evaluation and limitations
10. Severity estimation method
11. Agricultural knowledge base and source verification
12. Llama model selection
13. Prompt design and safety controls
14. ExecuTorch conversion and deployment
15. Offline operation and privacy
16. English and Hindi support
17. End-to-end performance measurements
18. Demonstration procedure
19. Known limitations
20. Future work
21. Installation and usage instructions
22. References

The report should explicitly explain the separation between:

- Vision inference
- Local agricultural knowledge retrieval
- Llama advisory generation
- ExecuTorch runtime
- Optional Hailo acceleration

---

## 15. Safety, privacy, and reliability

The application must:

- Show confidence and uncertainty.
- Never present an image-based estimate as certain.
- Avoid unsupported pesticide dosage recommendations.
- Recommend a local agricultural officer for serious or uncertain cases.
- Use only verified local guidance.
- Keep user images locally unless explicit consent is provided.
- Avoid uploading images or prompts to cloud services.
- Clearly state that the system is an advisory tool.
- Explain that expert confirmation may be required.

For pesticide-related advice, use verified regional agricultural sources and include label-compliance warnings. Treatment varies by crop, region, pest, product, and local regulation.

---

## 16. Phase 1 acceptance checklist

### Challenge compliance

- [ ] PS1 is the selected problem statement.
- [ ] The solution runs on an Arm-based device.
- [ ] A Llama-family model is used for advisory or reasoning.
- [ ] Llama is deployed on-device using ExecuTorch.
- [ ] The application works without internet connectivity.
- [ ] Source code is ready.
- [ ] Application is ready.
- [ ] Demonstration video is ready.
- [ ] Technical report is ready.

### Product functionality

- [ ] Camera or image input works.
- [ ] Image-quality validation works.
- [ ] Selected crop is documented.
- [ ] Initial disease/pest classes are documented.
- [ ] Vision prediction works on the Raspberry Pi.
- [ ] Confidence score is displayed.
- [ ] Severity is displayed with an explanation.
- [ ] Local knowledge base is available offline.
- [ ] Llama uses the verified context.
- [ ] ExecuTorch execution is demonstrated.
- [ ] English output works.
- [ ] Hindi output works.
- [ ] Poor or uncertain images produce a safe fallback.
- [ ] Offline follow-up questions work.

### Evaluation and documentation

- [ ] Dataset sources and licences are recorded.
- [ ] Model licences are recorded.
- [ ] Vision metrics are reported.
- [ ] Latency is measured.
- [ ] RAM usage is measured.
- [ ] Temperature and throttling are checked.
- [ ] End-to-end offline testing is recorded.
- [ ] Known limitations are documented.
- [ ] Installation instructions are tested on a clean environment.
- [ ] The GitHub repository is organised and reproducible.

---

## 17. Recommended priority order

Implement in this order:

1. Select one crop and a small set of conditions.
2. Capture and organise representative data.
3. Build and evaluate the vision model.
4. Add image-quality and low-confidence handling.
5. Create a verified local agricultural knowledge base.
6. Integrate a small Llama model with ExecuTorch.
7. Build the offline application flow.
8. Add Hindi output.
9. Measure latency, memory, temperature, and offline behaviour.
10. Record the demonstration.
11. Write and review the technical report.
12. Freeze and submit the Phase 1 release.

Avoid starting with:

- Many crops
- Many languages
- Voice interaction
- Complex cloud dashboards
- Large Llama models
- Full pest detection across every crop
- Unsupported treatment recommendations
- Hailo acceleration before the CPU baseline works

---

## 18. First vertical slice

The first end-to-end target is:

```text
Tomato leaf photo
    v
Image-quality check
    v
Early-blight prediction
    v
Confidence score
    v
Medium severity estimate
    v
Verified agricultural context
    v
Hindi advisory from Llama through ExecuTorch
    v
Works with internet disabled
```

Do not expand the feature set until this flow is reliable, measurable, and reproducible on the Raspberry Pi 5.

## 19. Future work after Phase 1

Potential PoC Development improvements include:

- Additional crops and diseases
- Pest detection and localisation
- Segmentation-based severity estimation
- Hailo NPU acceleration for vision
- Additional Indian languages
- Offline speech input and text-to-speech
- Better field-condition datasets
- Agri-extension worker workflows
- Local result history and export
- Expert feedback and continual evaluation
- Improved model compression and latency

These are secondary to delivering a dependable Phase 1 system.
