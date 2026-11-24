# End-to-end tests on the Raspberry Pi 5

Every test photo was sent in every one of the 10 languages to the application running on the Raspberry Pi 5 (8 GB,
official 27 W supply, active cooler, indoors), once through the HTTP API and once through the farmer app in a
phone-size browser. Llama, the grounding check and IndicTrans2 translation were on, as in normal use.

| Run | Build | Photos | API runs | App runs | Result |
|---|---|---|---|---|---|
| [2026-11-23_360runs](2026-11-23_360runs) (final) | main + the "recent scans" fix, as packaged by `cpp/package_pi.sh` | 36 | 360 | 360 | no failures |
| [2026-11-21_370runs](2026-11-21_370runs) | build of 21 Nov (before the "Not a tomato plant" wording and the pest-box merge rule) | 37 (one photo twice) | 370 | 370 | no failures |

This is a software test of the whole chain, not an accuracy test: only 9 photos are tomato leaves. Accuracy is measured
on the held-out test sets (docs/RESULTS.md).

## Final run (23-24 Nov 2026)

API run (`api/`, one JSON answer per photo and language, the program's own reply plus `_seconds` at the client):

| | Median | Range | Runs |
|---|---|---|---|
| Whole answer, translated | 8.36 s | 4.72-20.13 s | 171 |
| Llama 3.2 1B LoRA INT4 | 7.28 s | 3.72-14.78 s | 200 |
| Translation (IndicTrans2 CT2 INT8) | 1.09 s | 0.70-5.49 s | 171 |
| Vision (leaf check, disease, pests in parallel) | 114 ms | 112-136 ms | 330 |
| "Not a tomato plant" answer | 118 ms | 114-131 ms | 110 |
| Llama first token | 2.4 s | 1.8-3.7 s | 190 |
| Llama decode | 14.0 tokens/s | 13.3-14.8 | 190 |

- Statuses: 220 answered, 110 "not a tomato plant", 30 "retake photo" (photo too small or too bright).
- Every accepted Llama answer was translated in all nine languages (67 sentences per language), with the same
  diagnosis and the same Llama text in every language.
- Peak memory of the service during the run: 1.74 GB of 8 GB (`api/device_samples.log`, VmHWM). Service start with
  the file cache cleared: 13.5 s to the first answer (models loaded in 12.9 s). CPU 56-65 C, 2400 MHz, no throttling.
- Compared with 21 Nov: the same diagnoses and advice. Two insect counts on chilli photos changed (aphids 5 to 4,
  thrips 2 to 1): a box lying almost inside a kept box of the same group now counts as the same insect.

App run (`app/results.jsonl`): the right screen in all 360 runs, the Llama card shown exactly when Llama's text was
accepted (190 of 190), spray lists complete (220 of 220), no JavaScript error, nothing wider than the screen, the app
font loaded for every script. Median 6.9 s per run. One run (Gujarati, late blight) stalled on the test computer for 47
minutes with no error on the Pi; it was run again and passed.

## Test photos

The photos are not stored here; they come from public datasets whose licences are listed in the main README.

| Group | Photos | Source | Expected result |
|---|---|---|---|
| 1_tomato_disease | Tomato_Early_blight_leaf, Tomato_Septoria_leaf_spot, Tomato_leaf (healthy), Tomato_leaf_late_blight, Tomato_leaf_yellow_virus | PlantDoc. Late blight is in the test split of the disease model, the other four were in its training split | the named disease (healthy: verified tips) |
| 2_tomato_field | tomato_field_1 to 4 | PlantDoc test split (labels: septoria, septoria, early blight, late blight) | the PlantDoc label |
| 3_insects | 12 IP102 test photos (black cutworm, red spider mite, army worm, aphids, cabbage army worm, thrips, two each) | IP102 test split | the insect group; mites get general advice |
| 4_not_tomato | potato, pepper, corn, grape, apple, squash, strawberry, person, car, flower, fruit | leaf-check test photos (PlantVillage other crops, Natural Images) | "not a tomato plant" or "retake photo" |
| 5_chilli_field_pests | chilli_aphids_1, chilli_field_1 to 3 | Red Chili Pepper Pests Dataset, test folder | "not a tomato plant", insects still shown |

The 21 Nov run also had `chilli_aphids_2`, which turned out to be the same photo as `chilli_aphids_1`; it was removed
for the final run.

Against the PlantDoc labels the diagnosis is right on 7 of the 9 tomato photos, and on 3 of the 5 held-out ones:
`tomato_field_3` (early blight) is rejected as "not a tomato plant" (leaf check 0.52, threshold 0.425) and
`tomato_field_4` (late blight) is diagnosed as early blight. Other known results: `05_apple` shows a false aphid, the
healthy leaf gets the verified tips but no Llama text, and the red spider mite photos get general insect advice.

## Repeat the test

```
# on the Pi, next to the running service
python3 tools/e2e/full_test.py <photos> <out>
# on a PC on the Pi's network (needs the playwright package)
python3 tools/e2e/ui_full.py <out_app> <photos> http://<pi-address>:8080/
# checks and the numbers above
python3 tools/e2e/analyse_full.py <out>
python3 tools/e2e/ui_analyse.py <out_app>/results.jsonl <out>
python3 tools/e2e/e2e_stats.py <out>
```
