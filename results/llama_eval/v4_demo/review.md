# Distortion review - v4_demo

prompt=prompts/advisor_v4_no_example.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## healthy - ACCEPTED, 7 kept
- K: Avoid growing tomato in the same field season after season
  S (6/6): Avoid growing tomato in the same field season after season;
- K: Rotate with non-host crops such as cereals and legumes
  S (5/5): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.
- K: Do not follow tomato with chilli or brinjal
  S (3/3): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.
- K: Stake plants and use drip irrigation to reduce leaf wetness
  S (6/6): Stake plants and use drip irrigation to reduce leaf wetness.
- K: Collect and destroy infected leaves, shoots and fruits
  S (6/6): Collect and destroy infected leaves, shoots and fruits.
- K: Spray only need-based, label-claim pesticides
  S (7/7): Spray only need-based, label-claim pesticides.
- K: Conduct agro-ecosystem analysis weekly
  S (5/5): Conduct agro-ecosystem analysis (AESA) weekly in the morning, preferably before 9 a.m.

## early_blight - ACCEPTED, 10 kept
- K: Brown spots with concentric rings in a bull's eye pattern with yellow margin on the photographed leaf.
  S (7/9): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Early blight on a tomato leaf.
  S (3/3): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Fruit gets infected through calyx or stem attachment.
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: Irregular leaf spots mostly appear from marginal portion of leaves.
  S (7/7): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: Symptoms are V shaped and progress towards midrib.
  S (5/5): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
  S (11/11): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Mostly disease appears in vegetative phase of plant growth before flowering.
  S (7/7): Mostly disease appears in vegetative phase of plant growth before flowering.
- K: This is a common disease of tomato occurring on the foliage at any stage of the growth.
  S (5/5): This is a common disease of tomato occurring on the foliage at any stage of the growth.
- K: The fungus attacks the foliage causing characteristic leaf spots and blight.
  S (7/7): The fungus attacks the foliage causing characteristic leaf spots and blight.
- K: Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.

## late_blight - ACCEPTED, 12 kept
- K: Water-soaked black lesions on leaves and stems
  S (6/6): Water-soaked black lesions on leaves and stems.
- K: Lesions expand rapidly and the entire leaf becomes necrotic
  S (7/7): Lesions expand rapidly and the entire leaf becomes necrotic.
- K: White sporulation on leaves
  S (3/3): White sporulation on leaves.
- K: Dark brown lesions on fruit
  S (4/4): Dark brown lesions on fruit;
- K: Soft rot and disintegration of fruits
  S (3/3): soft rot and disintegration of fruits.
- K: Light-pale green water soaked dead area
  S (7/7): Blight appears on foliage as light-pale green water soaked dead area.
- K: Wet in morning and dried, shriveled in daylight
  S (4/4): The lesions are wet in morning and dried, shriveled in daylight.
- K: Enlarges rapidly until entire leaves are killed and exposing all the fruits for infection
  S (9/9): It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.
- K: Downy white fungus develops near the outer margin of lesion on underside of the leaves
  S (10/10): In moist and cloudy weather a downy white fungus develops near the outer margin of lesion on underside of the leaves.
- K: Green and ripe fruit affected by the blight appear as greenish brown
  S (8/8): Green and ripe fruit affected by the blight appear as greenish brown and internal tissues become spongy with bad odour.
- K: Internal tissues become spongy with bad odour
  S (5/5): Green and ripe fruit affected by the blight appear as greenish brown and internal tissues become spongy with bad odour.
- K: Grow resistant variety/hybrid Arka Abhed F1
  S (6/6): Grow resistant variety/hybrid Arka Abhed F1.

## septoria_leaf_spot - ACCEPTED, 7 kept
- K: Small, round to irregular spots with grey centre and dark margin on leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
- K: Stems and flowers are also affected.
  S (3/3): Stems and flowers are also affected.
- K: Complete defoliation of affected leaves.
  S (4/4): Complete defoliation of affected leaves.
- K: Stems and flowers are sometimes attacked.
  S (4/4): Stems and flowers are sometimes attacked.
- K: Fruits are rarely attacked.
  S (3/3): Fruits are rarely attacked.

## bacterial_spot - ACCEPTED, 5 kept
- K: Small, brown, water-soaked, circular spots with yellow halo on leaves
  S (9/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: Small, dark spots appear on leaflets and stems of seedlings transplanted crop
  S (9/9): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: Moist weather and splattering rains are conducive to disease development
  S (6/6): Moist weather and splattering rains are conducive to disease development.
- K: Most outbreaks of the disease can be traced back to heavy rainstorms that occur in the area
  S (7/7): Most outbreaks of the disease can be traced back to heavy rainstorms that occur in the area.
- K: Infected leaves show small, brown, water-soaked, circular spots surrounded with yellowish halo
  S (12/12): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.

## yellow_leaf_curl_virus - ACCEPTED, 6 kept
- K: Severe stunting of plants
  S (2/2): Severe stunting of plants.
- K: Older leaves become leathery and brittle
  S (5/5): older leaves become leathery and brittle.
- K: Shortened internodes and more side branches give a bushy appearance
  S (7/7): Shortened internodes and more side branches give a bushy appearance.
- K: The virus is spread by whiteflies
  S (3/3): The virus is spread by whiteflies (Bemisia tabaci).
- K: Bemisia tabaci
  S (2/2): The virus is spread by whiteflies (Bemisia tabaci).
- K: Downward rolling and crinkling of the leaves
  S (4/4): Downward rolling and crinkling of the leaves;

