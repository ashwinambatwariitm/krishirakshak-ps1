# Roadmap and open tasks

Phase 1 submission deadline: 23 November 2026 (check the official challenge page for changes). Each task has a clear
"done when" so it can be picked up and finished independently. Put your name next to a task in your pull request.

## Track A - Vision models (accuracy)

| # | Task | Done when |
|---|---|---|
| A1 | "Is this a tomato leaf?" check. The disease model currently gives a confident tomato disease even for other plants or insect close-ups (an IP102 rice-leaf photo was called "bacterial spot, 73%"). Options: a small tomato-leaf / not-tomato-leaf classifier, or an out-of-distribution score on the disease model's features. | Non-tomato photos (PlantDoc other crops, IP102 images) are rejected at least 90% of the time on a held-out set, while at most 5% of tomato field photos are rejected. |
| A2 | Tune the "uncertain" threshold of the disease model on the validation split (currently a fixed 0.5 in `tools/predict.py`). Report accuracy on answered photos and the share of photos answered (coverage). | A coverage-vs-accuracy table on PlantDoc validation, the chosen threshold, then test-set numbers at that threshold. |
| A3 | More field photos for the weakest classes: bacterial spot (33-49% field recall), leaf mold (45%), mosaic virus (48-54%). Sources: own photos from farms or local markets, other licensed datasets. Record source and licence for every image. | At least 100 new field photos per class, added with the same grouping and split rules; v5 field macro F1 compared with v4 on the same test images. |
| A4 | Check INT8 quantisation of the disease model and the pest detector (ONNX Runtime static quantisation with validation images for calibration). | FP32 vs INT8 table: size, PlantVillage and PlantDoc macro F1 (disease) and IP102 mAP50 / false alarms (pest). |
| A5 | Pest species naming: for the commonly confused tomato pests (whitefly, red spider mite, Spodoptera litura, black cutworm, thrips), test a second-stage classifier on detected crops trained on the 75,000-image IP102 classification set. | Species accuracy when found improves on the IP102 test split versus the current detector. |
| A6 | Re-check pest confidence thresholds with the exported ONNX model and its 640 x 640 square input (Ultralytics' PyTorch predictor pads to a tighter rectangle, which changes confidences slightly). | Threshold table (insects found and false alarms) computed with the exported model. |

## Track B - Raspberry Pi 5 deployment (hardware)

| # | Task | Done when |
|---|---|---|
| B1 | Run both ONNX models from C++ with ONNX Runtime on the Pi, using the input specifications in `models/README.md` and the JSON written by `tools/export_onnx.py`. | Same top-1 class / detections as `tools/predict.py` on 20 test photos. |
| B2 | Measure on the Pi: latency including preprocessing, peak RAM, CPU load, temperature and throttling, for FP32 and INT8. | Table in `docs/RESULTS.md`. |
| B3 | Camera capture and image quality checks (blur, too dark, too bright, leaf too small) with OpenCV. | Poor photos are rejected with a clear message; thresholds documented. |
| B4 | Coordinator: combine disease, pest and quality results into one structured result for the advisory step. | JSON output matching the format in `docs/PROJECT_HANDOFF.md` section 7. |

## Track C - Advisory (Llama through ExecuTorch)

| # | Task | Done when |
|---|---|---|
| C1 | Verified knowledge base (JSON or SQLite) for the 10 tomato classes and the main pests: symptoms, prevention, safe first actions, when to call an expert, source for every statement; English and reviewed Hindi. | Every entry has a source; a fluent Hindi speaker has reviewed the Hindi text. |
| C2 | Run Llama 3.2 1B Instruct through ExecuTorch on the Pi (4-bit, XNNPACK backend). | Model loads offline; first-token latency, tokens per second and RAM recorded. |
| C3 | Prompt that uses only the knowledge-base entry and the model results, states uncertainty, and never invents pesticide names or doses. | 20 test cases (including uncertain and pest-only cases) reviewed by the team. |

## Track D - Submission

| # | Task | Done when |
|---|---|---|
| D1 | Technical report following the outline in `docs/plan_phase1.md` section 14. | Draft reviewed by every team member. |
| D2 | Demonstration video with internet disabled (see `docs/plan_phase1.md` section 13). | Video shows the full offline flow in English and Hindi. |
| D3 | Choose a licence compatible with PlantVillage (CC BY-SA) and Ultralytics (AGPL-3.0), add LICENSE, make the repository public before submitting. | LICENSE file added; repository public. |
