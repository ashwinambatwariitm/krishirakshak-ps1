# PS1 Dataset and Research Reference Library

## Purpose

This document collects the research papers, datasets, implementation documentation, and important links identified for the Bharat AI-SoC Challenge PS1 project:

> Offline crop-disease/pest detection and advisory for farmers

The project target is a Raspberry Pi 5 with 8 GB RAM, using a lightweight vision model for crop diagnosis and a Llama-family model deployed through ExecuTorch for offline advisory generation.

## How to use this document

Use the resources in this order:

1. Understand the datasets and their limitations.
2. Select a lightweight vision model.
3. Study edge and Raspberry Pi deployment.
4. Study Llama and ExecuTorch deployment.
5. Use the review papers to expand the literature review.

For every paper that becomes part of the final report, record:

```text
Title
Authors
Year
Dataset
Crop(s)
Model
Metrics
Hardware
Offline capability
Quantisation
Limitations
Licence or access status
```

The official challenge page remains the source of truth for challenge requirements and deadlines:

- [Bharat AI-SoC Challenge 2026-27](https://arm-education.github.io/Arm-Developer-Labs/Bharat_AI_SoC_2026_27.html)
- Local project plan: [plan_phase1.md](./plan_phase1.md)
- Dataset analysis workbook: [crop_datasets_analysis.xlsx](./crop_datasets_analysis.xlsx)

---

# A. Core dataset and project papers

## 1. PlantVillage dataset

**Title:** [An open access repository of images on plant health to enable the development of mobile disease diagnostics](https://arxiv.org/abs/1511.08060)

- **Authors:** David P. Hughes and Marcel Salathe
- **Year:** 2015
- **Paper page:** <https://arxiv.org/abs/1511.08060>
- **Download PDF:** <https://arxiv.org/pdf/1511.08060.pdf>
- **DOI/arXiv identifier:** <https://doi.org/10.48550/arXiv.1511.08060>
- **Dataset repository:** <https://github.com/spMohanty/PlantVillage-Dataset>
- **Dataset reference:** <https://www.quantitative-plant.org/dataset/plantvillage-dataset>

### Why it matters

This is the foundational paper for the PlantVillage image repository and mobile plant-disease diagnosis. It explains the motivation for image-based crop-health systems and controlled leaf-image datasets.

### Use in the PS1 project

Use PlantVillage for the initial tomato disease classifier:

- Healthy
- Early blight
- Late blight
- Leaf mold
- Septoria leaf spot

### Important limitation

Most PlantVillage images are single-leaf, laboratory-style images with relatively uniform backgrounds. Do not use PlantVillage alone as evidence of field performance. Use PlantDoc for external field-style testing.

---

## 2. PlantDoc dataset

**Title:** [PlantDoc: A Dataset for Visual Plant Disease Detection](https://arxiv.org/abs/1911.10317)

- **Authors:** Davinder Singh, Naman Jain, Pranjali Jain, Pratik Kayal, Sudhakar Kumawat, and Nipun Batra
- **Conference:** ACM CoDS-COMAD, 2020
- **Paper page:** <https://arxiv.org/abs/1911.10317>
- **Download PDF:** <https://arxiv.org/pdf/1911.10317.pdf>
- **HTML version:** <https://ar5iv.labs.arxiv.org/html/1911.10317>
- **DOI:** <https://doi.org/10.1145/3371158.3371196>
- **Dataset repository:** <https://github.com/pratikkayal/PlantDoc-Dataset>

### Why it matters

PlantDoc contains more natural, field-like images than PlantVillage, with cluttered backgrounds, varied lighting, and variable image quality.

### Use in the PS1 project

Use PlantDoc as an external test set:

```text
Train: PlantVillage
Internal test: held-out PlantVillage
External test: PlantDoc
```

Report PlantVillage and PlantDoc results separately. The difference demonstrates the domain gap between laboratory images and farmer photographs.

---

## 3. IP102 pest dataset

**Title:** [IP102: A Large-Scale Benchmark Dataset for Insect Pest Recognition](https://openaccess.thecvf.com/content_CVPR_2019/html/Wu_IP102_A_Large-Scale_Benchmark_Dataset_for_Insect_Pest_Recognition_CVPR_2019_paper.html)

- **Authors:** Xiaoping Wu, Chi Zhan, Yu-Kun Lai, Ming-Ming Cheng, and Jufeng Yang
- **Conference:** CVPR, 2019
- **Paper page:** <https://openaccess.thecvf.com/content_CVPR_2019/html/Wu_IP102_A_Large-Scale_Benchmark_Dataset_for_Insect_Pest_Recognition_CVPR_2019_paper.html>
- **Download PDF:** <https://openaccess.thecvf.com/content_CVPR_2019/papers/Wu_IP102_A_Large-Scale_Benchmark_Dataset_for_Insect_Pest_Recognition_CVPR_2019_paper.pdf>
- **DOI:** <https://doi.org/10.1109/CVPR.2019.00899>
- **Dataset repository:** <https://github.com/xpwu95/IP102>

### Why it matters

IP102 is a large insect-pest benchmark with 102 pest categories and classification data, plus a detection subset.

### Use in the PS1 project

Keep IP102 for a future, separate pest-detection module. Do not mix it into the first tomato disease classifier because it represents a different task and crop/pest taxonomy.

---

## 4. Mobile-friendly plant disease detection benchmark

**Title:** [Mobile-Friendly Deep Learning for Plant Disease Detection: A Lightweight CNN Benchmark Across 101 Classes of 33 Crops](https://arxiv.org/abs/2508.10817)

- **Authors:** Anand Kumar, Harminder Pal Monga, Tapasi Brahma, Satyam Kalra, and Navas Sherif
- **Year:** 2025
- **Paper page:** <https://arxiv.org/abs/2508.10817>
- **Download PDF:** <https://arxiv.org/pdf/2508.10817.pdf>

### Why it matters

This paper compares lightweight networks such as:

- MobileNetV2
- MobileNetV3
- EfficientNet-B0
- EfficientNet-B1

It focuses on mobile and edge efficiency, quantisation, and deployment trade-offs.

### Use in the PS1 project

Use it when selecting between MobileNetV3 and EfficientNet-Lite for Raspberry Pi inference. Compare accuracy, model size, RAM use, and latency rather than accuracy alone.

---

## 5. Plant disease detection for edge computing devices

**Title:** [Plant Disease Detection Model for Edge Computing Devices](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2023.1308528/full)

- **Authors:** Ameer Tamoor Khan, Signe Marie Jensen, Abdul Rehman Khan, and Shuai Li
- **Year:** 2023
- **Full article:** <https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2023.1308528/full>
- **Download PDF:** <https://www.frontiersin.org/articles/10.3389/fpls.2023.1308528/pdf>
- **DOI:** <https://doi.org/10.3389/fpls.2023.1308528>

### Why it matters

The paper discusses plant-disease models designed for edge-computing deployment, including lightweight models and model optimisation.

### Use in the PS1 project

Study its treatment of:

- Model efficiency
- Quantisation
- Accuracy-versus-latency trade-offs
- Offline or low-connectivity deployment

---

## 6. AI and IoT-powered edge device for crop pest and disease detection

**Title:** [AI and IoT-Powered Edge Device Optimized for Crop Pest and Disease Detection](https://www.nature.com/articles/s41598-024-55850-4)

- **Journal:** Scientific Reports
- **Year:** 2024
- **Full article:** <https://www.nature.com/articles/s41598-024-55850-4>
- **Download PDF:** <https://www.nature.com/articles/s41598-024-55850-4.pdf>
- **DOI:** <https://doi.org/10.1038/s41598-024-55850-4>

### Why it matters

This paper presents a low-power edge system for crop pest and disease detection and discusses device integration, model efficiency, and field operation.

### Use in the PS1 project

Compare its:

- System architecture
- Hardware assumptions
- Inference measurements
- Power considerations
- User-interface approach

with the Raspberry Pi 5 system.

---

## 7. AI-based crop disease detection using deep learning and Raspberry Pi

**Title:** [AI-Based Crop Disease Detection Using Deep Learning and Raspberry Pi](https://www.ijisrt.com/assets/upload/files/IJISRT25OCT1526.pdf)

- **Authors:** Pawankumar Bari, Om Kulkarni, Prathamesh Kudale, Shrushti Hadole, and Sujata Mali
- **Year:** 2025
- **Download PDF:** <https://www.ijisrt.com/assets/upload/files/IJISRT25OCT1526.pdf>
- **DOI:** <https://doi.org/10.38124/ijisrt/25oct1526>

### Why it matters

This paper describes a Raspberry Pi-oriented crop-disease system using a lightweight CNN and an offline deployment approach.

### Use in the PS1 project

Compare its:

- Raspberry Pi setup
- Model conversion
- Inference workflow
- Performance metrics
- Farmer-facing interface

with your own measurements.

---

## 8. Crop disease and pest identification based on deep learning and Raspberry Pi

**Title:** [Crop Disease and Pest Identification Based on Deep Learning and Raspberry Pi](https://dl.acm.org/doi/10.1145/3772673.3772703)

- **Authors:** Keke Wei and Yuanyuan Gao
- **Year:** 2025
- **ACM article:** <https://dl.acm.org/doi/10.1145/3772673.3772703>
- **ACM PDF:** <https://dl.acm.org/doi/pdf/10.1145/3772673.3772703>
- **DOI:** <https://doi.org/10.1145/3772673.3772703>

### Why it matters

This work studies lightweight models, including MobileNetV3, for Raspberry Pi crop analysis.

### Use in the PS1 project

Use it to compare:

- Model accuracy
- Inference latency
- Energy considerations
- Real-time operation
- Raspberry Pi deployment patterns

---

# B. Model architecture papers

## 9. MobileNetV2

**Title:** [Inverted Residuals and Linear Bottlenecks: Mobile Networks for Classification, Detection and Segmentation](https://arxiv.org/abs/1801.04381)

- **Authors:** Mark Sandler et al.
- **Year:** 2018
- **Paper page:** <https://arxiv.org/abs/1801.04381>
- **Download PDF:** <https://arxiv.org/pdf/1801.04381.pdf>
- **CVPR version:** <https://openaccess.thecvf.com/content_cvpr_2018/html/Sandler_MobileNetV2_Inverted_Residuals_CVPR_2018_paper.html>

### Why it matters

This paper explains inverted residuals and linear bottlenecks, which make MobileNetV2 suitable for mobile and embedded inference.

### Use in the PS1 project

Use MobileNetV2 as a baseline for comparison with MobileNetV3 or EfficientNet-Lite.

---

## 10. MobileNetV3

**Title:** [Searching for MobileNetV3](https://arxiv.org/abs/1905.02244)

- **Authors:** Andrew Howard et al.
- **Year:** 2019
- **Paper page:** <https://arxiv.org/abs/1905.02244>
- **Download PDF:** <https://arxiv.org/pdf/1905.02244.pdf>
- **ICCV version:** <https://openaccess.thecvf.com/content_ICCV_2019/html/Howard_Searching_for_MobileNetV3_ICCV_2019_paper.html>

### Why it matters

MobileNetV3 is designed for efficient mobile inference and is a strong candidate for the Raspberry Pi vision model.

### Use in the PS1 project

Use MobileNetV3 as the first practical vision baseline. Measure:

- Accuracy
- Model size
- RAM usage
- CPU latency
- Accuracy after quantisation

---

## 11. EfficientNet

**Title:** [EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks](https://arxiv.org/abs/1905.11946)

- **Authors:** Mingxing Tan and Quoc V. Le
- **Year:** 2019
- **Paper page:** <https://arxiv.org/abs/1905.11946>
- **Download PDF:** <https://arxiv.org/pdf/1905.11946.pdf>
- **ICML version:** <https://proceedings.mlr.press/v97/tan19a.html>

### Why it matters

EfficientNet introduces compound scaling for balancing network depth, width, and image resolution.

### Use in the PS1 project

Compare EfficientNet-Lite or EfficientNet-B0 with MobileNetV3. Select the model based on the complete Raspberry Pi trade-off, not only validation accuracy.

---

## 12. Deep learning for tiny devices

**Title:** [A Survey on Deep Learning for Tiny Devices](https://arxiv.org/abs/2002.11205)

- **Year:** 2020
- **Paper page:** <https://arxiv.org/abs/2002.11205>
- **Download PDF:** <https://arxiv.org/pdf/2002.11205.pdf>

### Why it matters

This survey covers neural-network deployment under memory, compute, and power constraints.

### Use in the PS1 project

Use it for the technical report section explaining:

- Edge-AI constraints
- Model compression
- Quantisation
- Runtime and hardware trade-offs

---

# C. Plant-disease detection and agricultural AI

## 13. Deep learning for image-based plant disease detection

**Title:** [Using Deep Learning for Image-Based Plant Disease Detection](https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2016.01419/full)

- **Author:** Konstantinos P. Ferentinos
- **Year:** 2018
- **Full article:** <https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2016.01419/full>
- **Download PDF:** <https://www.frontiersin.org/articles/10.3389/fpls.2016.01419/pdf>
- **DOI:** <https://doi.org/10.3389/fpls.2017.01419>

### Why it matters

This is a widely cited study on deep-learning-based plant disease recognition from leaf images.

### Use in the PS1 project

Study its:

- Class definitions
- Image-classification approach
- Evaluation methodology
- Dataset limitations

---

## 14. Plant disease recognition using deep learning and mobile applications

**Title:** [Plant Disease Recognition Using Deep Learning and Mobile Applications](https://www.mdpi.com/2077-0472/10/4/137)

- **Year:** 2020
- **Full article:** <https://www.mdpi.com/2077-0472/10/4/137>
- **Download PDF:** <https://www.mdpi.com/2077-0472/10/4/137/pdf>
- **DOI:** <https://doi.org/10.3390/agriculture10040137>

### Why it matters

This paper discusses disease-recognition models and their use in mobile applications.

### Use in the PS1 project

Use it for the camera-based farmer interface, mobile deployment, and discussion of practical diagnostic workflows.

---

## 15. Review of AI-based plant disease diagnosis

**Title:** [Artificial Intelligence in Plant Disease Detection: A Comprehensive Review](https://www.mdpi.com/2077-0472/13/4/857)

- **Year:** 2023
- **Full article:** <https://www.mdpi.com/2077-0472/13/4/857>
- **Download PDF:** <https://www.mdpi.com/2077-0472/13/4/857/pdf>
- **DOI:** <https://doi.org/10.3390/agriculture13040857>

### Why it matters

This review covers image-based disease detection, datasets, model families, and deployment issues.

### Use in the PS1 project

Use it to discover additional references and build the literature-review section of the technical report.

---

## 16. Deep learning-based plant disease detection review

**Title:** [Deep Learning-Based Plant Disease Detection: A Comprehensive Review](https://www.sciencedirect.com/science/article/pii/S2667305323000214)

- **Year:** 2023
- **Publisher page:** <https://www.sciencedirect.com/science/article/pii/S2667305323000214>

### Why it matters

This review discusses classification, detection, segmentation, datasets, and practical limitations.

### Use in the PS1 project

Use it to compare:

- Image classification
- Object detection
- Segmentation
- Field deployment
- Dataset bias

---

# D. Tomato-specific research

## 17. Tomato disease classification using PlantVillage

**Research search:** [Google Scholar: tomato disease classification with PlantVillage](https://scholar.google.com/scholar?q=tomato+plant+disease+classification+PlantVillage+deep+learning)

### Search focus

Look for papers covering:

- Early blight
- Late blight
- Leaf mold
- Septoria leaf spot
- Target spot
- Tomato mosaic virus
- Tomato yellow leaf curl virus

### Selection criteria

Prefer papers that report:

- Dataset details
- Exact class distribution
- Train/validation/test split
- Confusion matrix
- Per-class recall
- External validation
- Model size
- Inference latency

Avoid relying on papers that report only very high accuracy on random PlantVillage splits without field validation.

---

## 18. Tomato disease detection using field images

**Research search:** [Google Scholar: tomato disease detection using field images](https://scholar.google.com/scholar?q=tomato+leaf+disease+detection+field+images+deep+learning)

### Why it matters

Field-image research addresses the gap between:

```text
Clean laboratory leaf images
versus
Real farm photographs
```

### Use in the PS1 project

Prioritise papers that evaluate:

- Natural backgrounds
- Different lighting
- Partial leaves
- Multiple leaves
- Different cameras
- Disease stages
- Uncertain or out-of-distribution images

---

# E. Pest detection research

## 19. AgriPest dataset research

**Research search:** [Google Scholar: AgriPest crop pest detection dataset](https://scholar.google.com/scholar?q=AgriPest+dataset+crop+pest+detection)

### Use in the PS1 project

Keep this for a future object-detection pipeline. The workbook identifies it as a field pest dataset with bounding boxes, covering wheat, rice, corn, and rape.

It is not a direct fit for the first tomato disease-classification MVP.

---

## 20. Pest24 dataset research

**Research search:** [Google Scholar: Pest24 insect pest detection dataset](https://scholar.google.com/scholar?q=Pest24+dataset+insect+pest+detection)

### Use in the PS1 project

Pest24 is associated with automated pest-trap imagery. It may be useful for later pest monitoring, but trap-camera images are different from ordinary farmer crop-leaf photographs.

---

## 21. Insect pest recognition review research

**Research search:** [Google Scholar: deep-learning insect-pest recognition in agriculture](https://scholar.google.com/scholar?q=deep+learning+insect+pest+recognition+agriculture+review)

### Search focus

Use this search to find research on:

- Pest classification
- Pest object detection
- Tiny-object recognition
- Field-background robustness
- Pest monitoring
- Edge deployment

### Use in the PS1 project

Use this material when adding a separate pest-detection stage. Keep disease classification and pest detection as separate models unless there is a strong reason to unify them.

---

# F. Other crop datasets

## 22. Cassava disease classification

**Dataset competition:** [Cassava Leaf Disease Classification](https://www.kaggle.com/competitions/cassava-leaf-disease-classification)

**Research search:** [Google Scholar: cassava leaf disease classification](https://scholar.google.com/scholar?q=cassava+leaf+disease+classification+deep+learning+paper)

### Dataset classes

The workbook identifies:

- Cassava bacterial blight
- Cassava brown streak disease
- Cassava green mottle
- Cassava mosaic disease
- Healthy

### Use in the PS1 project

Use this dataset only if the project changes from tomato to cassava. It is a good alternative for a focused five-class crop-disease assistant.

---

## 23. Paddy Doctor and rice disease classification

**Dataset competition:** [Paddy Disease Classification](https://www.kaggle.com/competitions/paddy-disease-classification)

**Research search:** [Google Scholar: Paddy Doctor rice disease dataset](https://scholar.google.com/scholar?q=Paddy+Doctor+rice+disease+dataset+paper)

### Use in the PS1 project

Use this for a separate rice-focused system. The dataset includes rice diseases and pests and is geographically relevant to Indian agriculture, but it does not match the current tomato plan.

---

# G. Llama and ExecuTorch

## 24. Llama 3 technical report

**Title:** [The Llama 3 Herd of Models](https://arxiv.org/abs/2407.21783)

- **Year:** 2024
- **Paper page:** <https://arxiv.org/abs/2407.21783>
- **Download PDF:** <https://arxiv.org/pdf/2407.21783.pdf>

### Why it matters

This report describes the Llama 3 model family, training, evaluation, and capabilities.

### Use in the PS1 project

Use it as the model-family reference for the local advisory/reasoning component. Your report should identify the exact Llama model, version, quantisation, licence, and deployment configuration used.

---

## ExecuTorch implementation resources

ExecuTorch is primarily documented through its official documentation and repository rather than one single foundational paper:

- [ExecuTorch documentation](https://pytorch.org/executorch/)
- [ExecuTorch stable documentation](https://pytorch.org/executorch/stable/)
- [ExecuTorch GitHub repository](https://github.com/pytorch/executorch)
- [Arm ExecuTorch course](https://learn.arm.com/courses/executorch-on-arm/)

### Use in the PS1 project

Study:

- Model export
- Quantisation
- Backend selection
- Runtime execution
- ARM deployment
- Memory and latency measurement

The technical report must make clear that the Llama advisory component runs locally through ExecuTorch on the Raspberry Pi Arm CPU.

---

# H. Edge AI, quantisation, and hardware references

## 25. TensorFlow Lite quantisation

**Technical documentation:** [TensorFlow Lite post-training quantisation](https://www.tensorflow.org/lite/performance/post_training_quantization)

**Model optimisation guide:** [TensorFlow Model Optimization](https://www.tensorflow.org/model_optimization/guide)

### Why it matters

These resources explain post-training quantisation, including INT8 conversion and the accuracy/latency/model-size trade-off.

### Use in the PS1 project

Use them if the vision model is deployed with TensorFlow Lite. Keep this vision-model pipeline documented separately from the required ExecuTorch Llama pipeline.

---

## 26. ONNX Runtime quantisation

**Technical documentation:** [ONNX Runtime quantisation](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html)

### Why it matters

ONNX Runtime provides another deployment and quantisation option for the vision model.

### Use in the PS1 project

Use it only if you compare ONNX Runtime with another vision runtime. The Llama advisory requirement should still use ExecuTorch.

---

## 27. Raspberry Pi AI and edge deployment

- [Raspberry Pi AI documentation](https://www.raspberrypi.com/documentation/computers/ai.html)
- [Raspberry Pi computer documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [Arm AI developer resources](https://developer.arm.com/AI)

### Use in the PS1 project

Use these resources for:

- Raspberry Pi 5 setup
- Camera integration
- Cooling and power
- AI accelerator options
- Hailo-related deployment
- ARM software and hardware guidance

If a Hailo accelerator is used later, document the pipelines separately:

```text
Vision model -> HailoRT -> Hailo NPU
Llama model  -> ExecuTorch -> Raspberry Pi Arm CPU
```

---

## 28. Practical reference project

**Repository:** [Crop_Disease_Detection](https://github.com/PoulamiSarkar24/Crop_Disease_Detection)

### Repository contents

- [README.md](https://github.com/PoulamiSarkar24/Crop_Disease_Detection/blob/main/README.md)
- [Crop_disease.py](https://github.com/PoulamiSarkar24/Crop_Disease_Detection/blob/main/Crop_disease.py)
- [Model artifact](https://github.com/PoulamiSarkar24/Crop_Disease_Detection/blob/main/crop_disease_mobilenet.h5)
- [Workflow image](https://github.com/PoulamiSarkar24/Crop_Disease_Detection/blob/main/flowchart.png)
- [Web interface](https://github.com/PoulamiSarkar24/Crop_Disease_Detection/blob/main/index.html)
- [Frontend logic](https://github.com/PoulamiSarkar24/Crop_Disease_Detection/blob/main/script.js)

### Observed approach

```text
Image upload
    v
MobileNet-style classifier
    v
Class label and confidence
    v
Hard-coded treatment text
    v
Web interface
```

### Useful ideas

- Lightweight model
- Raspberry Pi-oriented deployment
- Simple image-upload interface
- Local-language interface
- Confidence display
- Farmer-facing workflow

### Important limitations

The repository does not visibly provide:

- Formal accuracy, precision, recall, or F1 results
- Confusion matrix
- Raspberry Pi latency and RAM measurements
- Llama
- ExecuTorch
- A documented local knowledge base
- Severity classification
- Field validation
- Reproducible training scripts

Use it as an architectural reference, not as evidence of a complete PS1 implementation.

---

# Dataset strategy for Phase 1

## Recommended immediate path

```text
PlantVillage tomato training
        +
PlantDoc tomato external testing
        +
Optional verified CCMT field-diversity data later
        +
MobileNetV3 or EfficientNet-Lite
        +
Raspberry Pi CPU inference
        +
Local verified agricultural knowledge base
        +
Llama through ExecuTorch
```

## Recommended initial classes

1. Healthy
2. Early blight
3. Late blight
4. Leaf mold
5. Septoria leaf spot

## Datasets to defer

- IP102: separate insect-pest task
- AgriPest: separate object-detection task
- Pest24: trap-camera pest task
- Cassava Leaf Disease: alternative cassava project
- Paddy Doctor: alternative rice project
- PlantWild: later in-the-wild robustness research
- PlantSeg: later segmentation and severity research

## Important dataset controls

- Profile downloaded files instead of trusting approximate online counts.
- Record licences and access dates.
- Split by original image before augmentation.
- Keep augmented copies in the same split as their source.
- Prevent duplicate or near-duplicate images across splits.
- Keep PlantDoc external test images separate from training.
- Report internal and external results separately.
- Do not merge broad labels with specific diseases without manual review.

## Severity limitation

The listed datasets generally do not contain validated severity labels. Therefore:

- Do not claim that the model learned severity from these datasets.
- Initially report severity as an estimated category.
- Base estimates on confidence, affected-area analysis if available, and expert-reviewed rules.
- Consider segmentation masks or a separate expert-labelled severity dataset during the PoC phase.

---

# Recommended reading order

## Stage 1: Datasets

1. PlantVillage paper
2. PlantDoc paper
3. IP102 paper
4. [crop_datasets_analysis.xlsx](./crop_datasets_analysis.xlsx)

## Stage 2: Vision model

5. MobileNetV2
6. MobileNetV3
7. EfficientNet
8. Mobile-friendly plant disease benchmark
9. Edge computing plant disease paper

## Stage 3: Deployment

10. Scientific Reports edge-device paper
11. Raspberry Pi crop-disease paper
12. Mobile plant-disease paper
13. Plant disease review papers
14. Raspberry Pi documentation

## Stage 4: Advisory pipeline

15. Llama 3 technical report
16. ExecuTorch documentation
17. Arm ExecuTorch course
18. Quantisation documentation

---

# Research notes template

Copy this template for every paper you study:

```text
Title:
Authors:
Year:
URL:
PDF:
Dataset:
Crop(s):
Task:
Model:
Training setup:
Metrics:
Hardware:
Runtime:
Offline capability:
Quantisation:
Main result:
Limitations:
How it helps the PS1 project:
Licence/access notes:
```

# Final research caution

Many plant-disease papers report excellent accuracy on controlled PlantVillage images. That does not automatically mean the model will work reliably on real farm photographs.

The most important research gap for this project is:

> Demonstrating reliable field-aware image classification, safe offline advisory generation, Llama deployment through ExecuTorch, and measurable Raspberry Pi 5 performance in one reproducible system.

