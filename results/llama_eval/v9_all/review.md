# Distortion review - v9_all

prompt=prompts/advisor_v9_all_sentences.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - ACCEPTED, 3 kept
- K: Yellow sticky traps are effective at 4-5 acres.
  S (4/5): Install yellow sticky traps @ 4-5/acre.
- K: Use nitrogen fertilizer judiciously.
  S (3/3): Use nitrogen fertilizer judiciously.
- K: Aphids are sucking pests of tomatoes.
  S (4/4): Aphids (Myzus persicae, Aphis gossypii) are sucking pests of tomato.

## bacterial_canker - ACCEPTED, 21 kept
- K: Seedlings affected
  S (2/2): Seedlings, leaves, stem and fruits are affected.
- K: Leaves affected
  S (2/2): Seedlings, leaves, stem and fruits are affected.
- K: Stems affected
  S (2/2): Seedlings, leaves, stem and fruits are affected.
- K: Fruits affected
  S (2/2): Seedlings, leaves, stem and fruits are affected.
- K: Spots on leaves
  S (2/2): Spots on leaves, stems and fruits.
- K: Spots on stems
  S (2/2): Spots on leaves, stems and fruits.
- K: Spots on fruits
  S (2/2): Spots on leaves, stems and fruits.
- K: White blister like spots
  S (4/4): White blister like spots in the margins of leaves and turn brown.
- K: Wilting of leaves
  S (2/2): Wilting of leaves and shoots, streaks on stems and petioles.
- K: Streaks on stems
  S (2/2): Wilting of leaves and shoots, streaks on stems and petioles.
- K: Small water soaked spots
  S (4/4): Small, water soaked spots with white halo on fruits.
- K: Water soaked spots with white halo
  S (5/5): Small, water soaked spots with white halo on fruits.
- K: Centre of spots become slightly raised
  S (5/5): Centre of spots become slightly raised, tan coloured and rough.
- K: Tan coloured and rough
  S (2/2): Centre of spots become slightly raised, tan coloured and rough.
- K: Cankers develop
  S (2/2): Cankers develop and form cracks;
- K: Form cracks
  S (2/2): Cankers develop and form cracks;
- K: Slimy bacterial ooze through cracks
  S (5/5): slimy bacterial ooze through cracks.
- K: Vascular discolouration
  S (2/2): Vascular discolouration.
- K: Disease appears as spots
  S (2/2): Disease appears as spots on leaves, stems and fruits and as wilting of leaves and shoots.
- K: Wilting of leaves and shoots
  S (3/3): Wilting of leaves and shoots, streaks on stems and petioles.
- K: White blister like spots in margins
  S (5/5): White blister like spots in the margins of leaves and turn brown.

## bacterial_speck - ACCEPTED, 10 kept
- K: Circular to roughly circular in shape
  S (2/3): The spots are necrotic, circular to roughly circular.
- K: Necrotic
  S (1/1): The spots are necrotic, circular to roughly circular.
- K: Circular to roughly circular
  S (2/2): The spots are necrotic, circular to roughly circular.
- K: Pink stage
  S (2/2): As the fruit approaches the pink stage, the tissue around the spot retains its green colour longer than normal.
- K: Green colour retention longer than normal
  S (4/5): As the fruit approaches the pink stage, the tissue around the spot retains its green colour longer than normal.
- K: Small black spots on leaf
  S (4/4): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Petiole
  S (1/1): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Pedicel
  S (1/1): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Elongated lesions on stem
  S (3/3): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Summer ploughing to desiccate bacteria
  S (4/4): Summer ploughing to desiccate the bacteria and host.

## bacterial_spot - ACCEPTED, 4 kept
- K: Small, brown, water-soaked, circular spots with yellow halo on leaves
  S (9/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: Small, dark spots on leaflets and stems of seedlings
  S (6/6): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: Moist weather and splattering rains are conducive to disease
  S (5/5): Moist weather and splattering rains are conducive to disease development.
- K: Infected leaves show small, brown, water-soaked, circular spots
  S (9/9): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.

## bacterial_wilt - ACCEPTED, 5 kept
- K: Lower leaves drop before wilting
  S (5/5): Lower leaves drop before wilting.
- K: Yellow brown discolouration of tissues
  S (4/4): Yellow brown discolouration of tissues.
- K: White bacterial ooze from cut ends
  S (4/4): White bacterial ooze from cut ends.
- K: Characteristic symptoms of bacterial wilt
  S (4/4): Characteristic symptoms of bacterial wilt are the rapid and complete wilting of normal grown up plants.
- K: Lower leaves may drop before wilting
  S (5/5): Lower leaves drop before wilting.

## collar_rot - ACCEPTED, 10 kept
- K: Soft tissue necrosis of bark
  S (4/4): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.
- K: White, cottony and silvery mycelial growth
  S (5/5): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: White to light brown mustard like sclerotium
  S (6/6): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: Progressive dropping and yellowing
  S (3/3): Progressive dropping and yellowing followed by wilting of the entire plant is observed.
- K: Wilting of the entire plant
  S (2/2): Progressive dropping and yellowing followed by wilting of the entire plant is observed.
- K: Crop rotation with cereals
  S (3/3): Use crop rotation with cereals, corn, sorghum and millets.
- K: Remove weeds from field
  S (3/3): Remove all the weeds from field.
- K: Avoid infested farmyard manure
  S (4/4): Avoid use of infested farmyard manure, soil crop debris and compost in the field.
- K: Soil crop debris and compost
  S (4/4): Avoid use of infested farmyard manure, soil crop debris and compost in the field.
- K: Ammonium Nitrate as fertilizer
  S (3/3): Use Ammonium Nitrate as a fertilizer for nitrogen source.

## damping_off - ACCEPTED, 3 kept
- K: Complete rotting of seedlings
  S (3/3): Pre-emergence phase: Complete rotting of seedlings.
- K: Seedlings topple over or collapse
  S (4/4): Seedlings topple over or collapse.
- K: Infected tissues become soft and water soaked
  S (6/6): Post-emergence phase: Infected tissues become soft and water soaked.

## early_blight - ACCEPTED, 12 kept
- K: Brown spots with concentric rings in a bull's eye pattern with yellow margin on tomato leaves.
  S (7/8): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Fruit gets infected through calyx or stem attachment.
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: Brown concentric rings on fruits.
  S (3/3): brown concentric rings on fruits.
- K: Irregular leaf spots mostly appear from marginal portion of leaves.
  S (7/7): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: V shaped and progress towards midrib.
  S (4/4): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: Prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
  S (9/9): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Mostly disease appears in vegetative phase of plant growth before flowering.
  S (7/7): Mostly disease appears in vegetative phase of plant growth before flowering.
- K: This is a common disease of tomato occurring on the foliage at any stage of the growth.
  S (5/5): This is a common disease of tomato occurring on the foliage at any stage of the growth.
- K: The fungus attacks the foliage causing characteristic leaf spots and blight.
  S (7/7): The fungus attacks the foliage causing characteristic leaf spots and blight.
- K: Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Remove and destroy crop debris.
  S (4/4): Remove and destroy crop debris.
- K: Follow crop rotation.
  S (3/3): Follow crop rotation.

## fruit_rots - ACCEPTED, 2 kept
- K: The most serious disease of kharif tomatoes is fruit rot, which appears as a rhythmic rotting of fruits coming into contact with the soil.
  S (7/10): Symptoms appear as rhythmic rotting of fruits coming with the soil contact.
- K: Fruit rot is most serious in the kharif season.
  S (3/4): Rhizoctonia fruit rot is most serious disease of kharif tomato.

## fusarium_wilt - ACCEPTED, 6 kept
- K: Younger leaves die in succession
  S (3/3): Younger leaves die in succession.
- K: Petiole and leaves droop and wilt
  S (4/4): Petiole and leaves droop and wilt.
- K: Browning of vascular system
  S (3/3): Browning of vascular system.
- K: Entire plant wilt and die
  S (2/2): Entire plant wilt and die.
- K: First symptom of the disease
  S (1/1): The first symptom of the disease is clearing of the veinlets and chlorosis of the leaves.
- K: Clearing of the veinlets
  S (2/2): Clearing of the veinlets and yellowing of the lower leaves.

## grey_leaf_spot - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

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

## helicoverpa_fruit_borer - ACCEPTED, 11 kept
- K: Young larvae feed on tender foliage
  S (5/5): Young larvae feed on tender foliage.
- K: Mature larvae bore circular holes
  S (5/5): Mature larvae bore circular holes.
- K: Thrust only a part of its body into fruit and eat the inner content
  S (7/7): Thrust only a part of its body into fruit and eat the inner content.
- K: Eggs hatch in about 3-4 days
  S (3/3): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: First instars larvae initially feed on the leaves
  S (5/5): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: Larvae bore into the fruits with the posterior end outside the hole
  S (6/6): The larvae bore into the fruits with the posterior end outside the hole.
- K: Young larva feeds on the leaves for some time
  S (5/5): Young larva feeds on the leaves for some time and then attacks fruits.
- K: Caterpillar thrusts head inside leaving the rest of the body outside
  S (8/8): While feeding the caterpillar thrust its head inside leaving the rest of the body outside.
- K: Grow simultaneously 40 days old American tall marigold
  S (6/6): Grow simultaneously 40 days old American tall marigold and 25 days old tomato seedling at 1:16 rows.
- K: 40 days old tomato seedling
  S (2/2): Grow simultaneously 40 days old American tall marigold and 25 days old tomato seedling at 1:16 rows.
- K: 1:16 rows
  S (1/1): Grow simultaneously 40 days old American tall marigold and 25 days old tomato seedling at 1:16 rows.

## late_blight - ACCEPTED, 15 kept
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
- K: Avoid planting tomatoes in the same field every year
  S (7/7): Avoid planting tomatoes in the same field every year.
- K: Remove infected plant parts
  S (3/3): Remove infected plant parts.
- K: Ensure enough space between plants and stake them
  S (5/5): Ensure enough space between plants and stake them.

## mites - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## powdery_mildew - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## pseudocercospora_leaf_blight - ACCEPTED, 5 kept
- K: Olivacious black sooty growth of fungus on lower surface of the leaves
  S (8/8): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: Symptoms are only observed on the leaves
  S (4/4): Symptoms are only observed on the leaves.
- K: No discoloration on the upper side of the leaves
  S (4/4): No discoloration was observed on the corresponding upper side of the leaves.
- K: Collect and burn the infected leaves
  S (4/4): Collect and burn the infected leaves.
- K: Be careful for selecting exotic hybrids and varieties
  S (5/5): Be careful for selecting exotic hybrids and varieties.

## root_knot_nematode - ACCEPTED, 2 kept
- K: The root-knot nematode causes root galls on the feeder roots and sometimes affects the entire root system, showing heavy galling.
  S (10/12): Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
- K: Plants wilt during the hot part of the day, especially under dry conditions, and are often stunted.
  S (8/8): Plants wilt during the hot part of day, especially under dry conditions and are often stunted.

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

## spodoptera_tobacco_caterpillar - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## thrips - ACCEPTED, 2 kept
- K: Thrips are sucking pests of tomatoes.
  S (4/4): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.
- K: Thrips are a vector of tomato spotted wilt virus.
  S (4/5): Vector of tomato spotted wilt virus.

## tomato_mosaic - ACCEPTED, 3 kept
- K: Mottling on leaves
  S (2/2): Light and dark green mottling on leaves.
- K: Light and dark green mottling on leaves
  S (5/5): Light and dark green mottling on leaves.
- K: Wilting of young leaves
  S (3/3): Wilting of young leaves.

## tomato_spotted_wilt - ACCEPTED, 17 kept
- K: Severe stunting
  S (2/2): Severe stunting.
- K: Chlorotic or necrotic rings on leaves
  S (4/4): Chlorotic or necrotic rings on leaves.
- K: Thickening of veins
  S (2/2): Thickening of veins and bronzing of young leaves.
- K: Bronzing of young leaves
  S (3/3): Thickening of veins and bronzing of young leaves.
- K: Growing tips die-back
  S (3/3): Growing tips die-back and wilt.
- K: Wilt
  S (1/1): Growing tips die-back and wilt.
- K: Yellow areas with concentric circular markings in fruit
  S (5/5): Yellow areas with concentric circular markings in fruit.
- K: Discoloration of seed
  S (2/2): Discoloration of seed.
- K: Symptoms vary among hosts
  S (4/4): Symptoms vary among hosts and in a single host species.
- K: In a single host species
  S (3/3): Symptoms vary among hosts and in a single host species.
- K: Stunting is a common symptom of TSWV infection
  S (5/5): Stunting is a common symptom of TSWV infection.
- K: Chlorotic or necrotic rings form on the leaves of many infected hosts
  S (8/8): Chlorotic or necrotic rings form on the leaves of many infected hosts.
- K: Thickening of veins and bronzing of young leaves
  S (5/5): Thickening of veins and bronzing of young leaves.
- K: Growing tips may die-back and terminal branches may be streaked
  S (6/6): Growing tips may die-back and terminal branches may be streaked.
- K: Affected plants may have a one sided growth habit
  S (4/4): Affected plants may have a one sided growth habit or may be entirely stunted and have drooping leaves, suggesting a wilt.
- K: Or may be entirely stunted and have drooping leaves
  S (4/4): Affected plants may have a one sided growth habit or may be entirely stunted and have drooping leaves, suggesting a wilt.
- K: Pale red or yellow areas with concentric circular marking in the normal red skin of ripe tomato
  S (8/8): Pale red or yellow areas with concentric circular marking in the normal red skin of ripe tomato are formed.

## tuta_absoluta_pinworm - ACCEPTED, 3 kept
- K: The pinworm affected plants and fruits need to be collected and destroyed.
  S (5/6): Collect and destroy the pinworm affected plants and fruits.
- K: The pinworm affected plants and fruits should be avoided.
  S (3/4): Collect and destroy the pinworm affected plants and fruits.
- K: Healthy seedlings should be used for transplanting.
  S (3/4): Use healthy seedlings for transplanting.

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
- K: Yellow colouration on newly emerging leaves
  S (5/5): The newly emerging leaves exhibit slight yellow colouration and later they also show curling symptoms.
- K: Curling symptoms on newly emerging leaves
  S (5/5): The newly emerging leaves exhibit slight yellow colouration and later they also show curling symptoms.

