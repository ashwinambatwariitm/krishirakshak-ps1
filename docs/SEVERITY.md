# Severity levels

Problem statement PS1 asks the system to "classify severity levels" of diseases and pests. This page describes what
the application reports today, how it was checked, and what is still open.

## Pest severity (in the application)

Code: `cpp/src/pest_severity.cpp` (application), `app/pipeline/pest_severity.py` (Python reference, same rule).
Tests: `cpp/tests/pest_severity_test.cpp`, `python -m tools.check_pest_severity`.

One level per pest topic found in the photo, from the number of insects the pest detector found:

| Group | Topics | low | moderate | high |
|---|---|---|---|---|
| Colony insects | aphids, whitefly, mites, thrips, leafhoppers, mealybug | 1-4 | 5-19 | 20+ |
| Chewing larvae | caterpillars, fruit borer, Spodoptera, cutworm, Tuta, leaf miner | - | 1-2 | 3+ |
| Species uncertain | insect_other | 1-4 | 5-19 | 20+ |

- The level describes **this photo only**; a photo cannot measure infestation of a field. These count bands are a
  project rule, not an agronomic standard. A single caterpillar is never "low" because a single larva per plant is
  already the published economic threshold for fruit borer (TNAU IPM).
- Every level quotes the published way to check the field before spraying, from the knowledge base: the NIPHM
  AESA-based IPM package for tomato (count insects on five leaves per plant; larvae per plant; five random spots),
  and the economic threshold where one exists (fruit borer, TNAU). No threshold is invented where the sources give
  none.
- Limitation: the pest detector (YOLOv8n, IP102) names the species of aphids reliably; caterpillars and thrips are
  reliable as advice groups (pest_config.json `reliable_groups`, results/pest_groups_ip102) and get their topic even
  when the species is uncertain; other insects on tomato are reported as "insect, species uncertain". Counts are those
  of the detector (missed or merged insects change the count).
- Result JSON: `pest_severity` (topic, group, count, box_share, level, basis, scouting, threshold). The web page shows
  it in "Insects in this photo". The count is not given to Llama: with it, the 1B model echoed the count instead of
  advising (Pi test, 21 Nov 2026).

## Disease severity (in the application)

Code: `cpp/src/severity.cpp` (application), `app/pipeline/severity.py` (Python reference, same method; C++ and
Python give identical levels on 185/185 test photos). Training: `training/src/lesion_seg.py` (Kaggle notebook
`ps1-lesion-seg`); model `models/severity_lraspp_mnv3.onnx` (12.9 MB, release asset); specification and training
metrics in `results/severity/`.

- Method: a small segmentation network (LR-ASPP MobileNetV3-Large, input 448 x 448) marks the leaf and the diseased
  area on it; severity = lesion area / leaf area; low < 10%, moderate 10-25%, high >= 25%. About 130 ms on the
  Raspberry Pi 5 (4 threads).
- Training data, licences allow training and publishing the weights: Roboflow Universe "tomato" by A Tomato
  segment, version 7 (537 leaves with leaf and disease-area polygons, CC BY 4.0); Kaggle "Leaf disease segmentation
  dataset" (field photos from PlantDoc, CC BY 4.0, with lesion masks, CC0; lesion output only); PlantDoc field
  photos as blurred backgrounds behind the Roboflow leaves.
- Validation on 91 held-out tomato field photos with lesion masks checked by plant pathologists (PlantSeg test
  split, evaluation only; `results/severity_plantseg/README.md`): level agrees with the expert level on **61%** of
  the photos (colour rule used before: 31%), **74%** without the virus diseases; lesion IoU 0.37, Dice 0.54 (colour
  rule 0.17 / 0.29; mean Dice per photo 0.48 vs 0.28). On the Roboflow test split (same photo style as training) 94%.
- Segmentation scores (pooled over all pixels; Dice = 2 x overlap / (predicted + reference area), from the same pixel
  counts as the IoU, `results/severity_plantseg/model_v2_eval.json` and `results/severity/severity_metrics.json`):

  | Test set | Lesion IoU | Lesion Dice | Leaf IoU | Leaf Dice |
  |---|---|---|---|---|
  | Roboflow test split (54 leaves, same style as training) | 0.868 | 0.929 | 0.968 | 0.984 |
  | Field lesion photos, held out (Kaggle leaf disease segmentation) | 0.812 | 0.896 | - | - |
  | PlantSeg expert masks, held-out half (91 field photos) | 0.373 | 0.543 | - | - |
- Virus diseases (leaf curl, mosaic) get no level (`"not_applicable"`): their symptoms are curling and mottling, not
  lesion areas, and the model's level agreed with the expert only 4 of 20 times.
- The level is called an estimate for the photographed leaf. It is shown in the app ("Estimated spread on leaf",
  `"validated": true`) and given to Llama in the diagnosis line.

History: the first method, a colour rule (share of non-green pixels), agreed with the expert level on only 31% of
the held-out photos (a random guess: 33%) and was withdrawn.
