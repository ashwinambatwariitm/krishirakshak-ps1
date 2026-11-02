# Theme: Agriculture & Food Security
# Offline crop-disease/pest detection and advisory for farmers
## Objective
Develop an AI-powered assistant that helps farmers identify crop diseases, detect pests and receive actionable recommendations, running entirely on-device without internet connectivity.

## Project Description
Teams will build an AI system capable of analysing crop images to:
- Detect diseases and pests
- Classify severity levels
- Recommend treatment and intervention strategies
- Provide region-specific advisory guidance
- Support multiple local languages
- Operate offline for rural communities with limited connectivity
## Example Application Areas
- Crop disease early warning
- Pest identification and management
- Fertiliser and irrigation advisory
- Post-harvest loss reduction
- Smallholder farmer decision support
- Agri-extension worker tools
## Hardware
Teams may use any Arm-based platform appropriate for their solution, including:
- Arm-based Android smartphones
- Raspberry Pi 5, CPU-only
- Raspberry Pi 5 with AI HAT+ / AI HAT+ 2
- Arm-based Linux devices

If a Hailo accelerator is used for vision workloads, vision models run through HailoRT on the Hailo NPU, while Llama runs through ExecuTorch on the Raspberry Pi Arm CPU. These are separate pipelines and should be clearly documented.

- Required Technologies
- Llama
- ExecuTorch
### Technical requirement: 
A model from the Llama family must be used for the advisory or reasoning component and deployed on-device using ExecuTorch as the reference runtime (for example, Llama 3.2 1B/3B-Instruct or a fine-tuned or distilled variant).

## Optional Technologies
- OpenCV
- Hailo SDK
- PlantVillage / Cassava / IP102 datasets
- Speech processing frameworks for voice-based advisory
- Multilingual NLP models
## Deliverables
- Source code
- Application
- Demonstration video
- Technical report