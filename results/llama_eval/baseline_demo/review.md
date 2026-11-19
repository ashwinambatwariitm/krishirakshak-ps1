# Distortion review - baseline_demo

prompt=built-in options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## healthy - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## early_blight - ACCEPTED, 5 kept
- K: Brown spots with concentric rings in a bull's eye pattern with yellow margin on the photographed leaf.
  S (7/9): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: The fungus attacks the foliage, causing characteristic leaf spots and blight.
  S (7/7): The fungus attacks the foliage causing characteristic leaf spots and blight.
- K: Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Remove and destroy crop debris.
  S (4/4): Remove and destroy crop debris.
- K: Follow crop rotation.
  S (3/3): Follow crop rotation.

## late_blight - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## septoria_leaf_spot - ACCEPTED, 4 kept
- K: Small, round to irregular spots with grey centre and dark margin on tomato leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Spots coalesce and leaves are blighted.
  S (4/4): Spots coalesce and leaves are blighted.
- K: Complete defoliation of affected leaves.
  S (4/4): Complete defoliation of affected leaves.
- K: Removal and destruction of the affected plant parts.
  S (4/4): Removal and destruction of the affected plant parts.

## bacterial_spot - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## yellow_leaf_curl_virus - ACCEPTED, 7 kept
- K: Severe stunting of plants.
  S (2/2): Severe stunting of plants.
- K: Disease appears in severe forms during the month of September to November.
  S (7/7): Disease appear in severe forms during the month of September to November.
- K: Leaves show downward rolling, curling, twisting, and chlorosis.
  S (7/7): Leaves show downward rolling, curling, twisting and chlorosis.
- K: Plants show stunting, shortening of internodes, bushy appearance, no flowering, and fruiting at later stage of virus infection.
  S (12/12): Plants show stunting, shortening of internodes, bushy appearance, no flowering and fruiting at later stage of virus infection.
- K: Leaf curl disease is characterized by severe stunting of the plants with downward rolling and crinkling of the leaves.
  S (8/8): Leaf curl disease is characterized by severe stunting of the plants with downward rolling and crinkling of the leaves.
- K: Raise the nursery under a net of sufficient mesh size to keep out whiteflies.
  S (7/7): Raise the nursery under a net of sufficient mesh size to keep out whiteflies.
- K: Select seed from disease-free healthy plants.
  S (4/4): Select seed from disease-free healthy plants.

