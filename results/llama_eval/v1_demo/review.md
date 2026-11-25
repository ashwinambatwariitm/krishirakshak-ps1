# Distortion review - v1_demo

prompt=prompts/advisor_v1_per_sentence.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## healthy - ACCEPTED, 5 kept
- K: Rotate with non-host crops such as cereals and legumes.
  S (5/5): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.
- K: Stake plants and use drip irrigation to reduce leaf wetness.
  S (6/6): Stake plants and use drip irrigation to reduce leaf wetness.
- K: Collect and destroy infected leaves, shoots and fruits.
  S (6/6): Collect and destroy infected leaves, shoots and fruits.
- K: Use only necessary, label-claimed pesticides.
  S (4/5): Spray only need-based, label-claim pesticides.
- K: Avoid growing tomato in the same field season after season.
  S (6/6): Avoid growing tomato in the same field season after season;

## early_blight - ACCEPTED, 12 kept
- K: Brown spots with concentric rings in a bull's eye pattern with yellow margin
  S (7/7): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Fruit gets infected through calyx or stem attachment
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: Brown concentric rings on fruits
  S (3/3): brown concentric rings on fruits.
- K: Irregular leaf spots mostly appear from marginal portion of leaves
  S (7/7): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: In many tomato cultivars, symptoms are V shaped and progress towards midrib
  S (7/7): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen
  S (11/11): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Mostly disease appears in vegetative phase of plant growth before flowering
  S (7/7): Mostly disease appears in vegetative phase of plant growth before flowering.
- K: This is a common disease of tomato occurring on the foliage at any stage of the growth
  S (5/5): This is a common disease of tomato occurring on the foliage at any stage of the growth.
- K: The fungus attacks the foliage causing characteristic leaf spots and blight
  S (7/7): The fungus attacks the foliage causing characteristic leaf spots and blight.
- K: Early blight is first observed on the plants as small, black lesions mostly on the older foliage
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Remove and destroy crop debris
  S (4/4): Remove and destroy crop debris.
- K: Follow crop rotation
  S (3/3): Follow crop rotation.

## late_blight - ACCEPTED, 7 kept
- K: Water-soaked black lesions on leaves and stems.
  S (6/6): Water-soaked black lesions on leaves and stems.
- K: Lesions expand rapidly and the entire leaf becomes necrotic.
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

## septoria_leaf_spot - ACCEPTED, 7 kept
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
- K: Spots start on lower leaves and gradually advance upwards.
  S (7/7): Spots usually starts on lower leaves and gradually advance upwards.
- K: Spots coalesce and leaves are blighted.
  S (4/4): Spots coalesce and leaves are blighted.
- K: Complete defoliation of affected leaves.
  S (4/4): Complete defoliation of affected leaves.
- K: Stems and flowers are sometimes attacked.
  S (4/4): Stems and flowers are sometimes attacked.
- K: Fruits are rarely attacked.
  S (3/3): Fruits are rarely attacked.

## bacterial_spot - ACCEPTED, 9 kept
- K: Small, brown, water-soaked, circular spots with yellow halo on leaves.
  S (9/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: Small water-soaked spots on green fruit.
  S (6/6): Small water-soaked spots on green fruit;
- K: The centre of the spots becomes irregular, light brown, sunken and scabby.
  S (8/8): the centre of the spots becomes irregular, light brown, sunken and scabby.
- K: Small, dark spots appear on leaflets and stems of seedlings.
  S (7/7): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: Numerous spots coalesce and cause severe burning of the leaves.
  S (7/7): Numerous spots coalesce and cause severe burning of the leaves.
- K: Prominent yellow halo is observed around the spot.
  S (6/6): Prominent yellow halo is observed around the spot.
- K: Infected leaves show small, brown, water-soaked, circular spots surrounded with yellowish halo.
  S (12/12): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.
- K: On older plants the leaflet infection is mostly on older leaves and may cause serious defoliation.
  S (7/7): On older plants the leaflet infection is mostly on older leaves and may cause serious defoliation.
- K: Use disease-free seed.
  S (2/2): Use disease-free seed.

## yellow_leaf_curl_virus - ACCEPTED, 2 kept
- K: The tomato leaf is curled and the leaves are rolled downwards.
  S (4/4): Leaves show downward rolling, curling, twisting and chlorosis.
- K: The leaves are curled and the leaves are rolled downwards.
  S (4/4): Leaves show downward rolling, curling, twisting and chlorosis.

