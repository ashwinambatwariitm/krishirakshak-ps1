# Distortion review - v5_all

prompt=prompts/advisor_v5_keywords_no_example.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## bacterial_canker - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## bacterial_speck - ACCEPTED, 2 kept
- K: The tissue around the spot retains its green colour longer than normal.
  S (8/8): As the fruit approaches the pink stage, the tissue around the spot retains its green colour longer than normal.
- K: The spots are necrotic, circular to roughly circular.
  S (4/4): The spots are necrotic, circular to roughly circular.

## bacterial_spot - ACCEPTED, 4 kept
- K: Small, brown, water-soaked, circular spots with yellow halo on leaves
  S (9/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: Small, dark spots on leaflets and stems of seedlings
  S (6/6): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: Moist weather and splattering rains are conducive to disease
  S (5/5): Moist weather and splattering rains are conducive to disease development.
- K: Infected leaves show small, brown, water-soaked, circular spots
  S (9/9): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.

## bacterial_wilt - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## collar_rot - ACCEPTED, 5 kept
- K: Soft tissue necrosis of bark of the stem near soil line
  S (8/8): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.
- K: White, cottony and silvery mycelial growth
  S (5/5): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: Mustard like sclerotium
  S (3/3): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: White to light brown mustard like sclerotium
  S (6/6): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: Soft tissue necrosis of stem
  S (4/4): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.

## damping_off - ACCEPTED, 3 kept
- K: Complete rotting of seedlings
  S (3/3): Pre-emergence phase: Complete rotting of seedlings.
- K: Seedlings topple over or collapse
  S (4/4): Seedlings topple over or collapse.
- K: Infected tissues become soft and water soaked
  S (6/6): Post-emergence phase: Infected tissues become soft and water soaked.

## early_blight - ACCEPTED, 10 kept
- K: Brown spots with concentric rings in a bull's eye pattern with yellow margin on tomato leaves
  S (7/8): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Early blight on a tomato leaf
  S (3/3): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Fruit gets infected through calyx or stem attachment
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: Brown concentric rings on fruits
  S (3/3): brown concentric rings on fruits.
- K: Irregular leaf spots mostly appear from marginal portion of leaves
  S (7/7): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: V-shaped lesions with prominent yellowing on outer margin
  S (5/6): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Disease appears in vegetative phase of plant growth before flowering
  S (6/6): Mostly disease appears in vegetative phase of plant growth before flowering.
- K: This is a common disease of tomato occurring on the foliage at any stage of the growth
  S (5/5): This is a common disease of tomato occurring on the foliage at any stage of the growth.
- K: The fungus attacks the foliage causing characteristic leaf spots and blight
  S (7/7): The fungus attacks the foliage causing characteristic leaf spots and blight.
- K: Early blight is first observed on the plants as small black lesions mostly on the older foliage
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.

## fruit_rots - ACCEPTED, 6 kept
- K: Rhizoctonia fruit rot is most serious disease of kharif tomato.
  S (4/4): Rhizoctonia fruit rot is most serious disease of kharif tomato.
- K: Symptoms appear as rhythmic rotting of fruits coming with the soil contact.
  S (8/8): Symptoms appear as rhythmic rotting of fruits coming with the soil contact.
- K: Rotting is immediately followed by cracking and fungal growth over it.
  S (7/7): Rotting is immediately followed by cracking and fungal growth over it.
- K: Generally lower portion of fruits are infected which are coming in soil contact.
  S (8/8): Generally lower portion of fruits are infected which are coming in soil contact.
- K: Avoid the contact of fruit from soil by staking of plant.
  S (5/5): Avoid the contact of fruit from soil by staking of plant.
- K: Provide proper drainage in the field.
  S (4/4): Provide proper drainage in the field.

## fusarium_wilt - ACCEPTED, 6 kept
- K: Younger leaves die in succession
  S (3/3): Younger leaves die in succession.
- K: Petiole and leaves droop and wilt
  S (4/4): Petiole and leaves droop and wilt.
- K: Browning of vascular system
  S (3/3): Browning of vascular system.
- K: Entire plant wilt and die
  S (2/2): Entire plant wilt and die.
- K: First symptom
  S (1/1): The first symptom of the disease is clearing of the veinlets and chlorosis of the leaves.
- K: Clearing of veinlets
  S (2/2): Clearing of the veinlets and yellowing of the lower leaves.

## grey_leaf_spot - ACCEPTED, 17 kept
- K: Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
  S (14/14): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Necrotic.
  S (1/1): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Circular.
  S (1/1): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Dark brown.
  S (2/2): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Brown.
  S (1/1): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Clear.
  S (1/1): Sometimes clear narrow yellow halo is visible around the spots.
- K: Narrow.
  S (1/1): Sometimes clear narrow yellow halo is visible around the spots.
- K: Yellow.
  S (1/1): Sometimes clear narrow yellow halo is visible around the spots.
- K: Severely.
  S (1/1): Severely infected older leaves blight and fall down.
- K: Infected.
  S (1/1): Severely infected older leaves blight and fall down.
- K: Older.
  S (1/1): Severely infected older leaves blight and fall down.
- K: Blight.
  S (1/1): Severely infected older leaves blight and fall down.
- K: Fall.
  S (1/1): Severely infected older leaves blight and fall down.
- K: Debris.
  S (1/1): Removal and burning of all crop debris after senescence of the crop.
- K: After.
  S (1/1): Removal and burning of all crop debris after senescence of the crop.
- K: Senescence.
  S (1/1): Removal and burning of all crop debris after senescence of the crop.
- K: Crop.
  S (1/1): Removal and burning of all crop debris after senescence of the crop.

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
- K: Conduct agro-ecosystem analysis weekly in the morning
  S (6/6): Conduct agro-ecosystem analysis (AESA) weekly in the morning, preferably before 9 a.m.

## helicoverpa_fruit_borer - ACCEPTED, 14 kept
- K: Young larvae feed on tender foliage
  S (5/5): Young larvae feed on tender foliage.
- K: Mature larvae bore circular holes
  S (5/5): Mature larvae bore circular holes.
- K: Thrust only a part of its body into fruit
  S (5/5): Thrust only a part of its body into fruit and eat the inner content.
- K: Eat the inner content
  S (2/2): Thrust only a part of its body into fruit and eat the inner content.
- K: Eggs hatch in about 3-4 days
  S (3/3): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: First instars larvae initially feed on the leaves
  S (5/5): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: Migrate to the developing green fruit later
  S (5/5): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: Larvae bore into the fruits with the posterior end outside the hole
  S (6/6): The larvae bore into the fruits with the posterior end outside the hole.
- K: Young larva feeds on the leaves for some time
  S (5/5): Young larva feeds on the leaves for some time and then attacks fruits.
- K: Attacks fruits
  S (2/2): Young larva feeds on the leaves for some time and then attacks fruits.
- K: Internal tissues are eaten severely
  S (4/4): Internal tissues are eaten severely and completely hollowed out.
- K: Completely hollowed out
  S (2/2): Internal tissues are eaten severely and completely hollowed out.
- K: While feeding the caterpillar thrust its head inside
  S (5/5): While feeding the caterpillar thrust its head inside leaving the rest of the body outside.
- K: Leaving the rest of the body outside
  S (4/4): While feeding the caterpillar thrust its head inside leaving the rest of the body outside.

## late_blight - ACCEPTED, 14 kept
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
- K: Blight appears on foliage as light-pale green water soaked dead area
  S (10/10): Blight appears on foliage as light-pale green water soaked dead area.
- K: The lesions are wet in morning and dried, shriveled in daylight
  S (5/5): The lesions are wet in morning and dried, shriveled in daylight.
- K: It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection
  S (9/9): It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.
- K: Downy white fungus develops near the outer margin of lesion on underside of the leaves
  S (10/10): In moist and cloudy weather a downy white fungus develops near the outer margin of lesion on underside of the leaves.
- K: Green and ripe fruit affected by the blight appear as greenish brown
  S (8/8): Green and ripe fruit affected by the blight appear as greenish brown and internal tissues become spongy with bad odour.
- K: Internal tissues become spongy with bad odour
  S (5/5): Green and ripe fruit affected by the blight appear as greenish brown and internal tissues become spongy with bad odour.
- K: Grow resistant variety/hybrid Arka Abhed F1
  S (6/6): Grow resistant variety/hybrid Arka Abhed F1.
- K: Avoid planting tomatoes in the same field every year
  S (7/7): Avoid planting tomatoes in the same field every year.
- K: Remove infected plant parts
  S (3/3): Remove infected plant parts.

## mites - ACCEPTED, 2 kept
- K: Red spider mites thrive under high temperature
  S (6/6): Red spider mites thrive under high temperature, dry weather and are more serious under protected conditions.
- K: Red spider mites are more serious under protected
  S (5/5): Red spider mites thrive under high temperature, dry weather and are more serious under protected conditions.

## powdery_mildew - ACCEPTED, 3 kept
- K: * The blisters are bright yellow and have a yellow halo.
  S (3/4): Irregular, bright yellow blotches with yellow halo appear on leaves.
- K: * The blisters are on the infected areas of the leaves.
  S (3/4): Abundant white sporulation in the infected area of leaves.
- K: * The blisters are on the infected areas of the leaves and are surrounded by white sporulation in the infected area.
  S (5/7): Abundant white sporulation in the infected area of leaves.

## pseudocercospora_leaf_blight - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## root_knot_nematode - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

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

## serpentine_leaf_miner - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## spodoptera_tobacco_caterpillar - ACCEPTED, 13 kept
- K: Young larva scrap leaves on ventral surface
  S (6/6): Young larva scrap leaves on ventral surface.
- K: Defoliate crops
  S (2/2): Grownups defoliate crops.
- K: This is a minor pest under open conditions
  S (5/5): This is a minor pest under open conditions and assumes severe form under protected cultivation particularly in ill managed playhouses.
- K: Assumes severe form under protected cultivation
  S (6/6): This is a minor pest under open conditions and assumes severe form under protected cultivation particularly in ill managed playhouses.
- K: Mature larvae, migrate and cause extensive damage
  S (6/6): Mature larvae, migrate and cause extensive damage to leaves and fruits.
- K: Hide in soil and crop debris during the day
  S (5/5): They hide in soil and crop debris during the day time.
- K: In early stages, the caterpillars are gregarious
  S (4/4): In early stages, the caterpillars are gregarious and scrape the chlorophyll content of leaf lamina giving it a papery white appearance.
- K: Scrape the chlorophyll content of leaf lamina
  S (5/5): In early stages, the caterpillars are gregarious and scrape the chlorophyll content of leaf lamina giving it a papery white appearance.
- K: Gives it a papery white appearance
  S (3/4): In early stages, the caterpillars are gregarious and scrape the chlorophyll content of leaf lamina giving it a papery white appearance.
- K: Later they become voracious feeders
  S (4/4): Later they become voracious feeders making irregular holes on the leaves.
- K: Making irregular holes on the leaves
  S (4/4): Later they become voracious feeders making irregular holes on the leaves.
- K: Grow castor as trap crop
  S (4/4): Grow castor as trap crop.
- K: Collect and destroy egg masses and early instar larvae
  S (6/6): Collect and destroy egg masses and early instar larvae.

## thrips - ACCEPTED, 10 kept
- K: Thrips sucking pests of tomato
  S (3/3): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.
- K: Silvery streaks on leaf surface
  S (4/4): Silvery streaks on leaf surface.
- K: Pre-mature dropping of flowers
  S (3/3): Pre-mature dropping of flowers.
- K: Bud necrosis
  S (1/1): Bud necrosis.
- K: Vector of tomato spotted wilt virus
  S (4/4): Vector of tomato spotted wilt virus.
- K: Install blue sticky traps
  S (4/4): Install blue sticky traps @ 10 traps/ha against thrips;
- K: Locally available empty tins painted blue
  S (6/6): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: Coated with grease, vaseline or castor oil
  S (4/4): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: Grow 5-6 rows of sorghum or maize
  S (4/4): Grow 5-6 rows of sorghum or maize around the field as a barrier crop.
- K: Around the field as a barrier crop
  S (4/4): Grow 5-6 rows of sorghum or maize around the field as a barrier crop.

## tomato_mosaic - ACCEPTED, 7 kept
- K: Mottling on tomato leaves
  S (2/2): Light and dark green mottling on leaves.
- K: * Light and dark green mottling
  S (4/4): Light and dark green mottling on leaves.
- K: * Wilting of young leaves
  S (3/3): Wilting of young leaves.
- K: * Leaflets distorted and puckered
  S (3/3): Leaflets distorted and puckered.
- K: * Fern leaf symptoms
  S (3/3): Fern leaf symptoms.
- K: * Stunted growth
  S (2/2): Stunted growth.
- K: * Crop rotation
  S (2/2): Crop rotation.

## tomato_spotted_wilt - ACCEPTED, 13 kept
- K: Severe Stunting
  S (2/2): Severe stunting.
- K: Chlorotic or Necrotic Rings
  S (3/3): Chlorotic or necrotic rings on leaves.
- K: Thickening of Veins
  S (2/2): Thickening of veins and bronzing of young leaves.
- K: Bronzing of Young Leaves
  S (3/3): Thickening of veins and bronzing of young leaves.
- K: Growing Tips Die-Back
  S (3/3): Growing tips die-back and wilt.
- K: Wilt
  S (1/1): Growing tips die-back and wilt.
- K: Yellow Areas
  S (2/2): Yellow areas with concentric circular markings in fruit.
- K: Concentric Circular Markings
  S (2/2): Yellow areas with concentric circular markings in fruit.
- K: Discoloration of Seed
  S (2/2): Discoloration of seed.
- K: Symptoms Vary
  S (2/2): Symptoms vary among hosts and in a single host species.
- K: Stunting is Common
  S (2/2): Stunting is a common symptom of TSWV infection.
- K: Among Hosts
  S (2/2): Symptoms vary among hosts and in a single host species.
- K: In Single Host Species
  S (3/3): Symptoms vary among hosts and in a single host species.

## tuta_absoluta_pinworm - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## whitefly - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## yellow_leaf_curl_virus - ACCEPTED, 13 kept
- K: Severe stunting of plants
  S (2/2): Severe stunting of plants.
- K: Downward rolling and crinkling of the leaves
  S (4/4): Downward rolling and crinkling of the leaves;
- K: Older leaves become leathery and brittle
  S (5/5): older leaves become leathery and brittle.
- K: Shortened internodes and more side branches give a bushy appearance
  S (7/7): Shortened internodes and more side branches give a bushy appearance.
- K: The virus is spread by whiteflies
  S (3/3): The virus is spread by whiteflies (Bemisia tabaci).
- K: Bemisia tabaci
  S (2/2): The virus is spread by whiteflies (Bemisia tabaci).
- K: Disease appear in severe forms during the month of September to November
  S (7/7): Disease appear in severe forms during the month of September to November.
- K: Downward rolling, curling, twisting and chlorosis
  S (5/5): Leaves show downward rolling, curling, twisting and chlorosis.
- K: Leaves show downward rolling, curling, twisting and chlorosis
  S (7/7): Leaves show downward rolling, curling, twisting and chlorosis.
- K: Plants show stunting, shortening of internodes, bushy appearance, no flowering and fruiting at later stage of virus infection
  S (12/12): Plants show stunting, shortening of internodes, bushy appearance, no flowering and fruiting at later stage of virus infection.
- K: Sometimes leaves show light and dark mottle symptoms
  S (7/7): Sometimes leaves show light and dark mottle symptoms.
- K: Leaf curl disease is characterized by severe stunting of the plants with downward rolling and crinkling of the leaves
  S (8/8): Leaf curl disease is characterized by severe stunting of the plants with downward rolling and crinkling of the leaves.
- K: Newly emerging
  S (2/2): The newly emerging leaves exhibit slight yellow colouration and later they also show curling symptoms.

