# Distortion review - v3_demo_bcw

prompt=prompts/advisor_v3_no_keyword_list.txt options=--block-cause-words

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## healthy - ACCEPTED, 2 kept
- K: Collect and destroy any infected leaves, shoots, or fruits.
  S (6/6): Collect and destroy infected leaves, shoots and fruits.
- K: Conduct an agro-ecosystem analysis (AESA) every week, preferably before 9 a.m.
  S (7/9): Conduct agro-ecosystem analysis (AESA) weekly in the morning, preferably before 9 a.m.

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

## late_blight - ACCEPTED, 10 kept
- K: Black spots on the leaves and stems.
  S (4/4): Water-soaked black lesions on leaves and stems.
- K: The blight appears on the leaves as a light-pale green water-soaked dead area.
  S (10/10): Blight appears on foliage as light-pale green water soaked dead area.
- K: The spots are wet in the morning and dry in the sun.
  S (2/2): The lesions are wet in morning and dried, shriveled in daylight.
- K: A white fungus grows near the edge of the blight on the underside of the leaves.
  S (6/8): In moist and cloudy weather a downy white fungus develops near the outer margin of lesion on underside of the leaves.
- K: The fungus grows in moist and cloudy weather.
  S (4/5): In moist and cloudy weather a downy white fungus develops near the outer margin of lesion on underside of the leaves.
- K: Avoid planting tomatoes in the same field every year.
  S (7/7): Avoid planting tomatoes in the same field every year.
- K: Remove infected plant parts.
  S (3/3): Remove infected plant parts.
- K: Ensure enough space between plants and stake them.
  S (5/5): Ensure enough space between plants and stake them.
- K: Use black polythene mulch to keep the soil dry.
  S (3/4): Use black polythene mulch (30 micron).
- K: Improve field drainage and avoid overhead irrigation.
  S (6/6): Improve field drainage and avoid overhead irrigation.

## septoria_leaf_spot - ACCEPTED, 6 kept
- K: Small, round to irregular spots with grey centre and dark margin on leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Small spots with a grey centre and dark margins on leaves.
  S (7/7): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
- K: Spots coalesce and leaves are blighted.
  S (4/4): Spots coalesce and leaves are blighted.
- K: Removal and destruction of the affected plant parts.
  S (4/4): Removal and destruction of the affected plant parts.

## bacterial_spot - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## yellow_leaf_curl_virus - ACCEPTED, 2 kept
- K: The tomato leaf is curled and the leaves are rolled down.
  S (3/4): Leaves show downward rolling, curling, twisting and chlorosis.
- K: The leaves are curled and the leaves are rolled down.
  S (3/4): Leaves show downward rolling, curling, twisting and chlorosis.

