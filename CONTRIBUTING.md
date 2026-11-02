# Working on KrishiRakshak

This guide explains how to set up, how to run an experiment, and the rules every change must follow. Open tasks are
listed in [docs/ROADMAP.md](docs/ROADMAP.md).

## Setup

```
git clone git@github.com:ashwinambatwariitm/krishirakshak-ps1.git
cd krishirakshak-ps1
python -m venv .venv && source .venv/bin/activate
pip install -r training/requirements.txt onnx onnxruntime
gh release download models-v1 --dir models        # or download the files from the Releases page
sha256sum models/*.pt                              # compare with models/README.md
python tools/predict.py path/to/leaf_photo.jpg      # quick check that everything works
```

## Day-to-day workflow

1. Pick a task from [docs/ROADMAP.md](docs/ROADMAP.md) and put your name next to it in a pull request, so two people
   do not work on the same thing.
2. Create a branch: `git checkout -b short-task-name`.
3. Make the change, run `python tools/check_repo.py`, commit, push the branch and open a pull request.
4. Ask one teammate to review before merging into `main`. GitHub runs the same repository check automatically.

## Running a new training experiment

1. Copy the latest script in `training/src/` to a new version, for example `tomato_disease_v5.py`, and describe at the
   top what changes and why. Keep the earlier versions unchanged; they document how the results were obtained.
2. Register the script in the `NOTEBOOKS` list in `training/build_notebooks.py`.
3. Test it on fake data first; this catches path and data problems without using Kaggle GPU time:
   ```
   python training/smoke_test/make_fake.py /tmp/fake_data
   KR_SMOKE=1 KR_INPUT=/tmp/fake_data KR_WORK=/tmp/fake_out python training/src/tomato_disease_v5.py
   ```
4. Build and upload with your own Kaggle account:
   ```
   python training/build_notebooks.py --kaggle-user YOUR_KAGGLE_NAME
   kaggle kernels push -p kaggle/ps1_tomato_disease_v5
   ```
5. Download the outputs, copy only the small files (JSON, CSV, PNG; no weights, no `runs/` folders with thousands of
   files) into `results/<descriptive_run_name>/`, and add a section to `docs/RESULTS.md`.
6. If the new model is better on the test sets, publish it as a new release (see "Publishing models" below).

## Rules

These rules keep the results trustworthy and the repository clean.

**Evaluation**
- Test images are never used for training, checkpoint selection or threshold tuning. Use the validation split for
  every decision.
- Keep photos of the same leaf, and copies of the same photo, in one split. Reuse the grouping functions in the
  training scripts when adding data.
- Report lab (PlantVillage) and field (PlantDoc or own photos) results separately. Field results are what matter.
- Augment only in memory during training; never save augmented images.
- Compare against the current best model on the same test images before claiming an improvement.

**Repository**
- Plain ASCII in all files and file names; no spaces in file names (`tools/check_repo.py` enforces this).
- Model weights, ONNX files and datasets never go into git. Weights are published as GitHub Release assets.
- Never commit credentials: `kaggle.json`, Kaggle API tokens, GitHub tokens, private keys.
- Comment the reason behind non-obvious code, and give every non-trivial function a docstring.

**Kaggle**
- Each person uses their own Kaggle account and GPU quota (30 GPU hours per week).
- Kaggle keeps only about 500 output files per run: write bulky data to `/tmp` and save weights right after training.
- If Kaggle assigns a P100 GPU, the notebook stops within seconds; switch the accelerator to "GPU T4 x2".
- `kaggle kernels output` downloads file by file and can take a while; let it finish.

## Publishing models

1. Give the file a descriptive name, for example `tomato_disease_v5_effb0_10class.pt`.
2. Create a release with a new tag:
   ```
   gh release create models-v2 models/tomato_disease_v5_effb0_10class.pt --title "Models v2" --notes "What changed and the test results"
   ```
3. Add the file, its purpose and its SHA-256 checksum (`sha256sum file.pt`) to `models/README.md`, and update the
   "Recommended models" table in `docs/RESULTS.md`.

## Tools

| Command | What it does |
|---|---|
| `python tools/predict.py IMAGE_OR_FOLDER` | Runs the disease classifier and the pest detector on photos |
| `python tools/export_onnx.py --disease-model M --pest-model P --check-images DIR` | Exports to ONNX and checks the outputs match PyTorch |
| `python tools/check_repo.py` | Checks the repository rules before committing |
| `python training/build_notebooks.py --kaggle-user NAME` | Builds the Kaggle notebooks from `training/src/` |
| `python training/smoke_test/make_fake.py DIR` | Creates fake datasets for testing the training scripts |
