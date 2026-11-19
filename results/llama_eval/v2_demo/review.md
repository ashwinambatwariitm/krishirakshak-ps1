# Distortion review - v2_demo

prompt=prompts/aman_v2_explain.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## healthy - rejected, 0 kept (refused first, retry answer)
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## early_blight - rejected, 1 kept (refused first, retry answer)
Reasons: too_few_grounded_sentences:1

## late_blight - rejected, 0 kept (refused first, retry answer)
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## septoria_leaf_spot - ACCEPTED, 3 kept (refused first, retry answer)
- K: The tomato plant is affected by spots on the leaves with a grey center and dark margin.
  S (6/7): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: The spots start on the lower leaves and spread up.
  S (4/5): Spots usually starts on lower leaves and gradually advance upwards.
- K: The affected leaves are completely defoliated.
  S (3/4): Complete defoliation of affected leaves.

## bacterial_spot - ACCEPTED, 10 kept
- K: Small, brown, water-soaked, circular spots with yellow halo on leaves;
  S (9/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: older leaves fall.
  S (3/3): older leaves fall.
- K: Small spots on leaves with yellow halo.
  S (5/5): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
  S (9/9): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: Small dark spots on seedlings.
  S (4/4): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: Moist weather and splattering rains are conducive to disease development.
  S (6/6): Moist weather and splattering rains are conducive to disease development.
- K: Moist weather makes disease.
  S (2/3): Moist weather and splattering rains are conducive to disease development.
- K: Most outbreaks of the disease can be traced back to heavy rainstorms that occur in the area.
  S (7/7): Most outbreaks of the disease can be traced back to heavy rainstorms that occur in the area.
- K: Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.
  S (12/12): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.
- K: Infected leaves with spots.
  S (3/3): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.

## yellow_leaf_curl_virus - rejected, 0 kept (refused first, retry answer)
Reasons: empty_or_too_short, too_few_grounded_sentences:0

