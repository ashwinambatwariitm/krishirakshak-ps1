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
- Limitation: the pest detector (YOLOv8n, IP102) identifies aphids reliably; other insects on tomato are reported as
  "insect, species uncertain". Counts are those of the detector (missed or merged insects change the count).
- Result JSON: `pest_severity` (topic, group, count, box_share, level, basis, scouting, threshold). The web page shows
  it in "Insects in this photo"; the Llama prompt includes the count and level of the main pest.

## Disease severity (open)

The first method, a colour rule (share of non-green pixels, `cpp/src/severity.cpp`), was validated on 181 tomato
field photos with expert lesion masks (PlantSeg): its level agrees with the expert level in only 31% of the photos,
the same as a random guess, and isolating the leaf or tuning the colours does not help
(`results/severity_plantseg/README.md`). It is therefore no longer shown to the farmer or given to Llama; it remains
in the result as `"validated": false`.

Planned: a small segmentation model for lesions and leaf area (severity = lesion area / leaf area, levels below 10%,
10-25%, above 25%), trained on data whose licence allows training and shipping the weights, and evaluated on the
same held-out PlantSeg photos. For the virus diseases (leaf curl, mosaic) an area-based level may not be meaningful;
their advice does not depend on a level (remove infected plants, control the vector).
