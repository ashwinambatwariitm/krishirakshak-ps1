# Disease severity: validation of the colour rule on expert lesion masks

Script: `tools/eval_severity_plantseg.py`. Result per image and summary: `colour_rule_eval.json`.

## Data

PlantSeg test split (Wei et al. 2024, "PlantSeg: A Large-Scale In-the-wild Dataset for Plant Disease
Segmentation", arXiv 2409.04038), Hugging Face copy `Voxel51/PlantSeg-Test`: 181 tomato field photos with lesion
masks checked by plant pathologists (early blight 37, late blight 33, leaf mold 31, septoria 26, bacterial spot 22,
yellow leaf curl virus 19, mosaic virus 13).

Licence CC BY-NC-ND 4.0: used for evaluation only. The images and masks are not stored in this repository and are
not used for training.

PlantSeg has lesion masks but no leaf masks. The severity level is therefore compared on the same leaf area for
prediction and reference (the method's own leaf mask), which isolates the error of the lesion detection.
Images are split by a fixed hash of the file name; colour variants were tuned on one half, results are reported on
the other (held-out) half.

## Result (held-out half, 91 photos)

| Method | Lesion precision | Lesion recall | Lesion IoU | Level agrees with expert |
|---|---|---|---|---|
| M0 current rule (whole photo) | 0.24 | 0.38 | 0.17 | 30% |
| M1 lesions inside the main leaf only | 0.23 | 0.41 | 0.17 | 31% |
| M2 lesions inside all large leaves | 0.23 | 0.41 | 0.17 | 31% |
| best of 12 colour variants (tuned on the other half) | 0.23 | 0.40 | 0.17 | 32% |

With three levels, 33% is the agreement of a random guess. The rule reports "high" for 125 of 181 photos: every
non-green pixel counts as disease (yellowing, stems, shadows, soil, glare). It finds blight lesions (recall 0.72-0.79
for early and late blight) but cannot separate them from the rest (precision about 0.3), and it fails on the virus
diseases, whose symptoms are mottling and deformation rather than spots (recall about 0.2).

## Segmentation model (training/src/lesion_seg.py, run 2) - used in the application

Same held-out half, same protocol (`model_v2_eval.json`, method MODEL):

| Method | Lesion precision | Lesion recall | Lesion IoU | Level agrees with expert |
|---|---|---|---|---|
| colour rule (M0) | 0.24 | 0.38 | 0.17 | 30% |
| **lesion segmentation model** | **0.68** | **0.45** | **0.37** | **61%** (88 graded) |

Per disease (correct level / photos): bacterial spot 8/8, late blight 13/16, early blight 12/16, leaf mold 10/14,
septoria 7/14, yellow leaf curl virus 3/13, mosaic virus 1/7. Without the two virus diseases: 50/68 = 74%. The
application therefore reports no level for the virus diseases.

Run 1 of the model scored 19% here: the field lesion masks store lesions as pixel value 38 and were read with a
"> 127" threshold, so the field photos were trained as "no lesion". Run 2 reads any non-zero value as lesion and
stops if the field masks look empty.

## Consequence (colour rule)

- The colour rule was withdrawn and replaced by the lesion segmentation model above (61% on the same held-out
  photos), trained on data whose licences allow training and publishing the weights.
