# KrishiRakshak - offline crop disease and pest advisor (Bharat AI-SoC Challenge 2026-27, PS1)

KrishiRakshak helps farmers identify crop diseases and insect pests from a photo and gives verified advice in English
and Hindi, fully offline on a Raspberry Pi 5 (8 GB).

```
Camera image
  -> image quality checks (OpenCV)
  -> tomato disease classifier (EfficientNet-B0)      \
  -> insect pest detector (YOLOv8n, IP102 species)    /  results combined by a coordinator
  -> local verified knowledge base (JSON / SQLite)
  -> Llama 3.2 1B through ExecuTorch (explanation in English / Hindi)
```

The disease and pest models are trained separately and combined only at inference time. The pest detector always
runs, even when the leaf looks healthy.

## Current status

| Part | Status |
|---|---|
| Tomato disease classifier, all 10 PlantVillage tomato classes | Trained and tested |
| Insect pest detector, 102 IP102 species | Trained, fine-tuned against false alarms, tested |
| ONNX export | Tool ready (`tools/export_onnx.py`); outputs verified against PyTorch |
| Raspberry Pi inference (C++), camera and quality checks | In progress |
| Knowledge base and Llama / ExecuTorch advisory | Next |

Key results (held-out test images; details in [docs/RESULTS.md](docs/RESULTS.md)):

| Model | Lab photos (PlantVillage) | Field photos (PlantDoc) |
|---|---|---|
| Disease, 10 classes, EfficientNet-B0 | 98.4% accuracy, macro F1 0.98 | 68% accuracy, macro F1 0.62 (8 classes with field data) |
| Disease, 5 classes, EfficientNet-B0 | 97.2% accuracy, macro F1 0.97 | 80% accuracy, macro F1 0.78 |
| Pests, YOLOv8n | IP102 test mAP50 0.567; finds 92% of insects | False alarms on insect-free leaves: 0.3% (lab), 5% (field) |

## Repository layout

```
README.md                  this file
CONTRIBUTING.md            setup, workflow, rules, how to run experiments and publish models
docs/                      problem statement, plan, design decisions, dataset research, results
  RESULTS.md               all training results and the recommended models
  ROADMAP.md               open tasks with "done when" criteria
  PROJECT_HANDOFF.md       design decisions and the reasons behind them
  plan_phase1.md           Phase 1 plan, milestones and evaluation checklist
tools/
  predict.py               run the disease and pest models on photos
  export_onnx.py           export to ONNX and check the outputs match PyTorch
  check_repo.py            repository rules (also run automatically on GitHub)
training/
  src/                     training scripts, one per experiment (cells separated by "# %%")
  build_notebooks.py       turns the scripts into Kaggle notebooks
  smoke_test/make_fake.py  tiny fake datasets for testing the scripts on a PC
  requirements.txt         Python packages for local testing
kaggle/                    generated notebooks, ready to upload to Kaggle
results/                   metrics, confusion matrices and split manifests of every run
models/README.md           how to download the trained models, input formats, checksums
```

Training scripts (newest last):

| Script | Purpose |
|---|---|
| `tomato_disease.py` | v1: PlantVillage only; direct model vs two-stage (Healthy/Diseased gate) |
| `tomato_disease_v2.py` | v2: adds the PlantDoc training share (field photos) |
| `tomato_disease_v3.py` | v3: EMA weights, matched learning-rate schedule, two seeds |
| `tomato_disease_v4.py` | v4: all 10 tomato classes, plus memory and latency measurements (current) |
| `ip102_pest.py` | YOLOv8n pest detector on IP102 (100 epochs) |
| `ip102_pest_negft.py` | Fine-tunes the detector with insect-free leaf images (current) |

## Quick start for team members

```
pip install -r training/requirements.txt onnx onnxruntime
gh release download models-v1 --repo ashwinambatwariitm/krishirakshak-ps1 --dir models
python tools/predict.py path/to/leaf_photo.jpg
```

Example output:

```
leaf_photo.jpg
  Disease : late_blight (97%)   others: healthy 0%, target_spot 0%
  Pests   : none detected
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) before making changes and pick a task from [docs/ROADMAP.md](docs/ROADMAP.md).

## Team tasks (Phase 1, until Friday 20 November 2026)

Each task has a work order with inputs, steps, deliverables and acceptance checks, and can be done without the
Raspberry Pi:

| Task | Work order | Start with |
|---|---|---|
| Farmer mobile app (web app served by the Pi, phone over the Pi's Wi-Fi hotspot) | [docs/handover/KrishiRakshak_App_Work_Order_Onkar.pdf](docs/handover/KrishiRakshak_App_Work_Order_Onkar.pdf) | [docs/APP_API.md](docs/APP_API.md), `python tools/mock_api_server.py` |
| Llama 3.2 1B advisor quality (on a laptop) | [docs/handover/LLAMA_1B_TASK_AMAN.md](docs/handover/LLAMA_1B_TASK_AMAN.md) (PDF next to it) | `gh release download llm-v1 --dir models`, `python -m llm.eval_advisor` |

Model files: vision models in release `models-v2`, Llama 3.2 1B (ExecuTorch, INT4) with its licence in release
`llm-v1`. Built with Llama.

## How to train on Kaggle

1. Create a Kaggle account with phone verification (needed for GPU and internet) and install the Kaggle command-line
   tool with an API token.
2. Build the notebooks with your username:
   ```
   python training/build_notebooks.py --kaggle-user YOUR_KAGGLE_NAME
   ```
3. Upload and start a notebook, for example the 10-class disease model:
   ```
   kaggle kernels push -p kaggle/ps1_tomato_disease_v4
   ```
4. Kaggle sometimes assigns an older P100 GPU that recent PyTorch does not support. The notebooks stop within seconds
   in that case; open the notebook on Kaggle, set Accelerator to "GPU T4 x2" and run it again.
5. Download the outputs when the run is complete:
   ```
   kaggle kernels output YOUR_KAGGLE_NAME/ps1-tomato-disease-v4 -p results/new_run
   ```

The datasets are attached automatically from Kaggle (listed in `training/build_notebooks.py`); nothing has to be
downloaded by hand. `ip102_pest_negft.py` needs the output of a finished `ps1-ip102-pest` run under the same account.

Kaggle keeps only about 500 output files per run, so the scripts write bulky intermediate data to `/tmp` and save the
trained weights before running any evaluation.

## Testing the scripts on a PC before using Kaggle GPU time

```
pip install -r training/requirements.txt
python training/smoke_test/make_fake.py /tmp/fake_data
KR_SMOKE=1 KR_INPUT=/tmp/fake_data KR_WORK=/tmp/fake_out python training/src/tomato_disease_v4.py
```

`KR_SMOKE=1` runs a tiny version (one epoch, small batches), `KR_INPUT` points to the input datasets and `KR_WORK` to
the output folder. The fake data reproduces every dataset layout and known data problem, so a script that passes
locally should not fail on Kaggle because of data handling. The accuracy numbers of a smoke run are meaningless.

## Rules that keep the test results honest

- Test images are never used for training, checkpoint selection or threshold tuning.
- Photos of the same leaf, and copies of the same photo across datasets, always stay in one split.
- Augmentation is done in memory during training only; augmented images are never saved.
- PlantVillage (lab) and PlantDoc (field) results are always reported separately.

## Datasets and licences

| Dataset | Kaggle copy used | Licence of the original |
|---|---|---|
| PlantVillage (color) | `abdallahalidev/plantvillage-dataset` | CC BY-SA 3.0; the authors state that models trained on it fall under the same licence |
| PlantDoc (boxes) | `yusufmurtaza01/plantdoc-object-detection-dataset` | CC BY 4.0 |
| PlantDoc (class folders) | `nirmalsankalana/plantdoc-dataset` | CC BY 4.0 (original repository) |
| IP102 (detection subset) | `parserpixy/ip102-dataset` | See the original IP102 repository terms |

Main libraries: PyTorch and torchvision (BSD), Albumentations 2.0.8 (MIT), Ultralytics YOLO (AGPL-3.0). The licence
of this repository must be compatible with these, in particular with AGPL-3.0 and CC BY-SA.

## Next steps

1. Export the chosen models to ONNX, check that ONNX outputs match PyTorch, and create INT8 versions.
2. Run both models from C++ (ONNX Runtime) on the Raspberry Pi 5 and measure latency, RAM, CPU load and temperature.
3. Build the verified knowledge base (English and Hindi) for the 10 tomato diseases and the main pests.
4. Run Llama 3.2 1B through ExecuTorch on the Pi and connect it to the knowledge base.
5. Collect more field photos of bacterial spot, leaf mold and mosaic virus (the weakest classes on field photos).

See [docs/plan_phase1.md](docs/plan_phase1.md) for the full plan and [docs/PROJECT_HANDOFF.md](docs/PROJECT_HANDOFF.md)
for the reasoning behind each design decision.
