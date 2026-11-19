# Distortion review - v1b_demo

prompt=prompts/aman_v1b_full_stop.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## healthy - ACCEPTED, 6 kept
- K: Avoid growing tomato in the same field season after season.
  S (6/6): Avoid growing tomato in the same field season after season;
- K: Rotate with non-host crops such as cereals and legumes.
  S (5/5): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.
- K: Stake plants and use drip irrigation to reduce leaf wetness.
  S (6/6): Stake plants and use drip irrigation to reduce leaf wetness.
- K: Collect and destroy infected leaves, shoots and fruits.
  S (6/6): Collect and destroy infected leaves, shoots and fruits.
- K: Spray only need-based, label-claim pesticides.
  S (7/7): Spray only need-based, label-claim pesticides.
- K: Conduct agro-ecosystem analysis weekly in the morning.
  S (6/6): Conduct agro-ecosystem analysis (AESA) weekly in the morning, preferably before 9 a.m.

## early_blight - ACCEPTED, 6 kept
- K: Fruit gets infected through calyx or stem attachment.
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: Irregular leaf spots mostly appear from marginal portion of leaves.
  S (7/7): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: In many tomato cultivars, symptoms are V shaped and progress towards midrib.
  S (7/7): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
  S (11/11): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Mostly disease appears in vegetative phase of plant growth before flowering.
  S (7/7): Mostly disease appears in vegetative phase of plant growth before flowering.
- K: Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.

## late_blight - ACCEPTED, 7 kept
- K: Water-soaked black lesions on leaves and stems.
  S (6/6): Water-soaked black lesions on leaves and stems.
- K: Lesions expand rapidly, and the entire leaf becomes necrotic.
  S (7/7): Lesions expand rapidly and the entire leaf becomes necrotic.
- K: White sporulation on leaves.
  S (3/3): White sporulation on leaves.
- K: Blight appears on foliage as light-pale green water soaked dead area.
  S (10/10): Blight appears on foliage as light-pale green water soaked dead area.
- K: The lesions are wet in morning and dried, shriveled in daylight.
  S (5/5): The lesions are wet in morning and dried, shriveled in daylight.
- K: It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.
  S (9/9): It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.
- K: In moist and cloudy weather a downy white fungus develops near the outer margin of lesion on underside of the leaves.
  S (13/13): In moist and cloudy weather a downy white fungus develops near the outer margin of lesion on underside of the leaves.

## septoria_leaf_spot - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## bacterial_spot - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## yellow_leaf_curl_virus - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

