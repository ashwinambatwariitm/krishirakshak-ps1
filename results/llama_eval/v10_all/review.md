# Distortion review - v10_all

prompt=prompts/aman_v10_no_diagnosis.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## bacterial_canker - ACCEPTED, 30 kept
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
- K: White blister like spots
  S (4/4): White blister like spots in the margins of leaves and turn brown.
- K: Margins of leaves
  S (2/2): White blister like spots in the margins of leaves and turn brown.
- K: Wilting of leaves
  S (2/2): Wilting of leaves and shoots, streaks on stems and petioles.
- K: Fruits
  S (1/1): Seedlings, leaves, stem and fruits are affected.
- K: Small water soaked spots
  S (4/4): Small, water soaked spots with white halo on fruits.
- K: White halo
  S (2/2): Small, water soaked spots with white halo on fruits.
- K: Centre of spots
  S (2/2): Centre of spots become slightly raised, tan coloured and rough.
- K: Become slightly raised
  S (3/3): Centre of spots become slightly raised, tan coloured and rough.
- K: Tan coloured
  S (1/1): Centre of spots become slightly raised, tan coloured and rough.
- K: Rough
  S (1/1): Centre of spots become slightly raised, tan coloured and rough.
- K: Cankers
  S (1/1): Cankers develop and form cracks;
- K: Develop
  S (1/1): Cankers develop and form cracks;
- K: Form cracks
  S (2/2): Cankers develop and form cracks;
- K: Slimy bacterial ooze
  S (3/3): slimy bacterial ooze through cracks.
- K: Through cracks
  S (2/2): slimy bacterial ooze through cracks.
- K: Vascular discolouration
  S (2/2): Vascular discolouration.
- K: Disease appears
  S (1/1): Disease appears as spots on leaves, stems and fruits and as wilting of leaves and shoots.
- K: As spots on leaves
  S (2/2): Spots on leaves, stems and fruits.
- K: Stems
  S (1/1): Seedlings, leaves, stem and fruits are affected.
- K: And fruits
  S (1/1): Seedlings, leaves, stem and fruits are affected.
- K: Spots become brown
  S (3/3): Spots become brown with age and coalesce, but leaves do not fall off.
- K: Coalesce
  S (1/1): Spots become brown with age and coalesce, but leaves do not fall off.
- K: But leaves do not fall off
  S (2/2): Spots become brown with age and coalesce, but leaves do not fall off.
- K: Leaflets on one side of rachis
  S (3/3): Leaflets on one side of rachis show withering initially.
- K: Show withering initially
  S (3/3): Leaflets on one side of rachis show withering initially.

## bacterial_speck - ACCEPTED, 6 kept
- K: Small black spots appear on leaf
  S (5/5): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Small black spots appear on petiole
  S (5/5): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Small black spots appear on pedicel
  S (5/5): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Small black spots appear on stem
  S (5/5): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Summer ploughing to desiccate bacteria
  S (4/4): Summer ploughing to desiccate the bacteria and host.
- K: Summer ploughing to desiccate host
  S (4/4): Summer ploughing to desiccate the bacteria and host.

## bacterial_spot - ACCEPTED, 7 kept
- K: small, brown, water-soaked, circular spots with yellow halo on leaves
  S (9/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: small, dark spots appear on leaflets and stems of seedlings
  S (7/7): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: numerous spots coalesce and cause severe burning of the leaves
  S (7/7): Numerous spots coalesce and cause severe burning of the leaves.
- K: prominent yellow halo is observed around the spot
  S (6/6): Prominent yellow halo is observed around the spot.
- K: moist weather and splattering rains are conducive to disease development
  S (6/6): Moist weather and splattering rains are conducive to disease development.
- K: infected leaves show small, brown, water-soaked, circular spots surrounded with yellowish halo
  S (12/12): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.
- K: use disease-free seed
  S (2/2): Use disease-free seed.

## bacterial_wilt - ACCEPTED, 6 kept
- K: Rapid wilting of plants
  S (2/2): Rapid and complete wilting of plant.
- K: Lower leaves drop before wilting
  S (5/5): Lower leaves drop before wilting.
- K: Yellow-brown discoloration of tissues
  S (3/4): Yellow brown discolouration of tissues.
- K: White bacterial ooze from cut ends
  S (4/4): White bacterial ooze from cut ends.
- K: Characteristic symptoms of bacterial wilt
  S (4/4): Characteristic symptoms of bacterial wilt are the rapid and complete wilting of normal grown up plants.
- K: Lower leaves may drop before wilting
  S (5/5): Lower leaves drop before wilting.

## collar_rot - ACCEPTED, 10 kept
- K: Soft tissue necrosis of bark
  S (4/4): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.
- K: White cottony mycelial growth
  S (4/4): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: Silvery mycelial growth
  S (3/3): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: White to light brown sclerotium
  S (4/4): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: Progressive dropping and yellowing
  S (3/3): Progressive dropping and yellowing followed by wilting of the entire plant is observed.
- K: Wilting of the entire plant
  S (2/2): Progressive dropping and yellowing followed by wilting of the entire plant is observed.
- K: Collapse of plants
  S (1/1): Sometime plants collapse soon after infection.
- K: Crop rotation with cereals
  S (3/3): Use crop rotation with cereals, corn, sorghum and millets.
- K: Avoid infested farmyard manure
  S (4/4): Avoid use of infested farmyard manure, soil crop debris and compost in the field.
- K: Remove weeds from field
  S (3/3): Remove all the weeds from field.

## damping_off - ACCEPTED, 4 kept
- K: Complete rotting of seedlings
  S (3/3): Pre-emergence phase: Complete rotting of seedlings.
- K: Seedlings topple over or collapse
  S (4/4): Seedlings topple over or collapse.
- K: Young, juvenile tissues of the collar at the ground level
  S (6/6): The post-emergence phase is characterized by the infection of the young, juvenile tissues of the collar at the ground level.
- K: Infected tissues become soft and water soaked
  S (6/6): Post-emergence phase: Infected tissues become soft and water soaked.

## early_blight - ACCEPTED, 10 kept
- K: Brown spots with concentric rings in a bull's eye pattern with yellow margin
  S (7/7): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Fruit gets infected through calyx or stem attachment
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: Brown concentric rings on fruits
  S (3/3): brown concentric rings on fruits.
- K: Irregular leaf spots mostly appear from marginal portion of leaves
  S (7/7): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: V shaped symptoms progress towards midrib
  S (5/5): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: Prominent yellowing on outer margin due to host specific toxin
  S (7/7): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Early blight observed on plants as small black lesions
  S (6/6): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Fruit blight observed on plants as small black lesions
  S (5/6): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Remove and destroy crop debris
  S (4/4): Remove and destroy crop debris.
- K: Follow crop rotation
  S (3/3): Follow crop rotation.

## fruit_rots - ACCEPTED, 2 kept
- K: Rhizoctonia fruit rot is the most serious disease of kharif tomato.
  S (4/4): Rhizoctonia fruit rot is most serious disease of kharif tomato.
- K: Avoid the contact of fruit from soil by staking of plant.
  S (5/5): Avoid the contact of fruit from soil by staking of plant.

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

## grey_leaf_spot - ACCEPTED, 7 kept
- K: Small circular dark brown necrotic
  S (5/5): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Numerous spots appear all over the leaf lamina
  S (6/6): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Uniformly distributed on entire foliage
  S (4/4): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Clear narrow yellow halo is visible around the spots
  S (7/7): Sometimes clear narrow yellow halo is visible around the spots.
- K: Isolated spots are usually found
  S (3/4): Usually these spots are isolated but in later stage they coalesce to each other.
- K: Severely infected older leaves blight and fall down
  S (7/7): Severely infected older leaves blight and fall down.
- K: Remove and burn all crop debris
  S (3/4): Removal and burning of all crop debris after senescence of the crop.

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

## helicoverpa_fruit_borer - ACCEPTED, 10 kept
- K: Young larvae feed on tender foliage.
  S (5/5): Young larvae feed on tender foliage.
- K: Mature larvae bore circular holes.
  S (5/5): Mature larvae bore circular holes.
- K: Thrust only a part of its body into fruit and eat the inner content.
  S (7/7): Thrust only a part of its body into fruit and eat the inner content.
- K: Eggs hatch in about 3-4 days.
  S (3/3): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: First instars larvae initially feed on the leaves.
  S (5/5): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: Larvae bore into the fruits with the posterior end outside the hole.
  S (6/6): The larvae bore into the fruits with the posterior end outside the hole.
- K: Young larva feeds on the leaves for some time.
  S (5/5): Young larva feeds on the leaves for some time and then attacks fruits.
- K: Internal tissues are eaten severely.
  S (4/4): Internal tissues are eaten severely and completely hollowed out.
- K: Internal tissues are eaten completely.
  S (4/4): Internal tissues are eaten severely and completely hollowed out.
- K: Larvae feed on the leaves for some time.
  S (3/4): Young larvae feed on tender foliage.

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
- K: Blight appears on foliage as light-pale green water soaked dead area
  S (10/10): Blight appears on foliage as light-pale green water soaked dead area.
- K: The lesions are wet in morning and dried, shriveled in daylight
  S (5/5): The lesions are wet in morning and dried, shriveled in daylight.
- K: It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection
  S (9/9): It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.
- K: In moist and cloudy weather a downy white fungus develops near the outer margin of lesion on underside of the leaves
  S (13/13): In moist and cloudy weather a downy white fungus develops near the outer margin of lesion on underside of the leaves.
- K: Green and ripe fruit affected by the blight appear as greenish brown and internal tissues become spongy with bad odour
  S (13/13): Green and ripe fruit affected by the blight appear as greenish brown and internal tissues become spongy with bad odour.
- K: Grow resistant variety/hybrid Arka Abhed F1
  S (6/6): Grow resistant variety/hybrid Arka Abhed F1.
- K: Avoid planting tomatoes in the same field every year
  S (7/7): Avoid planting tomatoes in the same field every year.

## mites - ACCEPTED, 4 kept
- K: Reddish brown and bronzy affected leaves
  S (5/5): Affected leaves become reddish brown and bronzy.
- K: Severe infestation larvae silken webbing on the leaves
  S (6/6): Severe infestation larvae silken webbing on the leaves, wither and dry.
- K: Wither and dry
  S (1/1): Severe infestation larvae silken webbing on the leaves, wither and dry.
- K: Affected leaves become reddish brown and bronzy
  S (6/6): Affected leaves become reddish brown and bronzy.

## powdery_mildew - ACCEPTED, 3 kept
- K: Yellow blotches with a yellow halo on the leaves are a sign of the disease.
  S (4/5): Irregular, bright yellow blotches with yellow halo appear on leaves.
- K: Make sure the plants are spaced far enough apart to allow for good air circulation.
  S (4/5): Proper plant spacing of about 3 feet apart to allow for proper air circulation, which helps the foliage dry faster.
- K: Use organic mulch to protect the roots and prevent fungal spores from spreading.
  S (7/8): Organic mulch added around the plants will protect roots while preventing fungal spores from splashing onto the plant.

## pseudocercospora_leaf_blight - ACCEPTED, 3 kept
- K: Olivacious black sooty growth of fungus on lower surface of leaves
  S (8/8): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: Collect and burn infected leaves
  S (4/4): Collect and burn the infected leaves.
- K: Be careful when selecting exotic hybrids and varieties
  S (5/5): Be careful for selecting exotic hybrids and varieties.

## root_knot_nematode - ACCEPTED, 9 kept
- K: Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
  S (12/12): Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
- K: Infected plants in patches in the field.
  S (3/3): Infected plants in patches in the field.
- K: Formation of galls on host root system is the primary symptom.
  S (7/7): Formation of galls on host root system is the primary symptom.
- K: Roots branch profusely starting from the gall tissue causing a 'beard root' symptom.
  S (10/10): Roots branch profusely starting from the gall tissue causing a 'beard root' symptom.
- K: Infected roots become knobby and knotty.
  S (5/5): Infected roots become knobby and knotty.
- K: In severely infected plants the root system is reduced and the rootlets are almost completely absent.
  S (9/9): In severely infected plants the root system is reduced and the rootlets are almost completely absent.
- K: The roots are seriously hampered in their function of uptake and transport of water and nutrients.
  S (8/8): The roots are seriously hampered in their function of uptake and transport of water and nutrients.
- K: Plants wilt during the hot part of day, especially under dry conditions and are often stunted.
  S (8/8): Plants wilt during the hot part of day, especially under dry conditions and are often stunted.
- K: Follow crop rotation with marigold, wherever possible.
  S (6/6): Follow crop rotation with marigold, wherever possible.

## septoria_leaf_spot - ACCEPTED, 9 kept
- K: Small, round to irregular spots with grey centre and dark margin on leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
- K: Less vigorous plant are usually affected.
  S (4/4): Less vigorous plant are usually affected.
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

## serpentine_leaf_miner - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## spodoptera_tobacco_caterpillar - ACCEPTED, 17 kept
- K: Young larva scrap leaves on ventral surface
  S (6/6): Young larva scrap leaves on ventral surface.
- K: Grownups defoliate crops
  S (3/3): Grownups defoliate crops.
- K: This is a minor pest under open conditions
  S (5/5): This is a minor pest under open conditions and assumes severe form under protected cultivation particularly in ill managed playhouses.
- K: Assumes severe form under protected cultivation
  S (6/6): This is a minor pest under open conditions and assumes severe form under protected cultivation particularly in ill managed playhouses.
- K: Under protected cultivation particularly in ill managed playhouses
  S (6/6): This is a minor pest under open conditions and assumes severe form under protected cultivation particularly in ill managed playhouses.
- K: Eggs are laid in clusters on foliage
  S (4/4): Eggs are laid in clusters on foliage.
- K: Young larvae feed gregariously on leaves
  S (5/5): Young larvae feed gregariously on leaves.
- K: Mature larvae, migrate and cause extensive damage
  S (6/6): Mature larvae, migrate and cause extensive damage to leaves and fruits.
- K: To leaves and fruits
  S (2/2): Mature larvae, migrate and cause extensive damage to leaves and fruits.
- K: They hide in soil and crop debris during the day
  S (5/5): They hide in soil and crop debris during the day time.
- K: In early stages, the caterpillars are gregarious
  S (4/4): In early stages, the caterpillars are gregarious and scrape the chlorophyll content of leaf lamina giving it a papery white appearance.
- K: Scrape the chlorophyll content of leaf lamina
  S (5/5): In early stages, the caterpillars are gregarious and scrape the chlorophyll content of leaf lamina giving it a papery white appearance.
- K: Giving it a papery white appearance
  S (4/4): In early stages, the caterpillars are gregarious and scrape the chlorophyll content of leaf lamina giving it a papery white appearance.
- K: Later they become voracious feeders
  S (4/4): Later they become voracious feeders making irregular holes on the leaves.
- K: Making irregular holes on the leaves
  S (4/4): Later they become voracious feeders making irregular holes on the leaves.
- K: Grow castor as trap crop
  S (4/4): Grow castor as trap crop.
- K: Collect and destroy egg masses and early instar larvae
  S (6/6): Collect and destroy egg masses and early instar larvae.

## thrips - ACCEPTED, 6 kept
- K: Thrips are sucking pests of tomato
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

## tomato_mosaic - ACCEPTED, 7 kept
- K: Light and dark green mottling on leaves
  S (5/5): Light and dark green mottling on leaves.
- K: Wilting of young leaves
  S (3/3): Wilting of young leaves.
- K: Leaflets distorted and puckered
  S (3/3): Leaflets distorted and puckered.
- K: Fern leaf symptoms
  S (3/3): Fern leaf symptoms.
- K: Stunted growth
  S (2/2): Stunted growth.
- K: Disease free seeds
  S (2/2): Disease free seeds.
- K: Crop rotation
  S (2/2): Crop rotation.

## tomato_spotted_wilt - ACCEPTED, 9 kept
- K: Severe stunting
  S (2/2): Severe stunting.
- K: Chlorotic or necrotic rings on leaves
  S (4/4): Chlorotic or necrotic rings on leaves.
- K: Growing tips die-back and wilt
  S (4/4): Growing tips die-back and wilt.
- K: Yellow areas with concentric circular markings in fruit
  S (5/5): Yellow areas with concentric circular markings in fruit.
- K: Discoloration of seed
  S (2/2): Discoloration of seed.
- K: Symptoms vary among hosts and in a single host species
  S (6/6): Symptoms vary among hosts and in a single host species.
- K: Stunting is a common symptom of TSWV infection
  S (5/5): Stunting is a common symptom of TSWV infection.
- K: Chlorotic or necrotic rings form on the leaves of many infected hosts
  S (8/8): Chlorotic or necrotic rings form on the leaves of many infected hosts.
- K: Thickening of veins and bronzing of young leaves
  S (5/5): Thickening of veins and bronzing of young leaves.

## tuta_absoluta_pinworm - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## whitefly - ACCEPTED, 18 kept
- K: Chlorotic spots
  S (2/2): Chlorotic spots.
- K: Yellowing
  S (1/1): Yellowing.
- K: Downward curling and drying of leaves
  S (4/4): Downward curling and drying of leaves.
- K: Vector of tomato leaf curl disease
  S (3/3): Vector of tomato leaf curl disease.
- K: Whitefly is a well-known vector
  S (4/4): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: Transmits tomato leaf curl virus
  S (4/4): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: Piercing and sucking mouthpart
  S (3/3): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Both nymphs and adults feed
  S (4/4): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: On lower surface of the leaves
  S (3/3): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Causing deformation of young leaves
  S (4/4): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Whiteflies also excrete
  S (2/2): Whiteflies also excrete honeydew, causing sooty mold.
- K: Honeydew, causing sooty mold
  S (4/4): Whiteflies also excrete honeydew, causing sooty mold.
- K: Remove alternate weed host
  S (4/4): Remove alternate weed host Abutilon indicum.
- K: Abutilon indicum
  S (2/2): Remove alternate weed host Abutilon indicum.
- K: Uproot and destroy diseased leaf curl plants
  S (5/5): Uproot and destroy the diseased leaf curl plants.
- K: Use nitrogen and irrigation judiciously
  S (3/3): Use nitrogen and irrigation judiciously.
- K: Raise nurseries in seedling trays
  S (4/4): Raise nurseries in seedling trays under nylon nets or polyhouses.
- K: Under nylon nets or polyhouses
  S (4/4): Raise nurseries in seedling trays under nylon nets or polyhouses.

## yellow_leaf_curl_virus - ACCEPTED, 16 kept
- K: Downward rolling leaves
  S (3/3): Downward rolling and crinkling of the leaves;
- K: Older leaves become brittle
  S (4/4): older leaves become leathery and brittle.
- K: Leaves show curling and twisting
  S (4/4): Leaves show downward rolling, curling, twisting and chlorosis.
- K: Plants show stunting and bushy
  S (3/3): Plants show stunting, shortening of internodes, bushy appearance, no flowering and fruiting at later stage of virus infection.
- K: No flowering or fruiting
  S (2/2): Plants show stunting, shortening of internodes, bushy appearance, no flowering and fruiting at later stage of virus infection.
- K: Light and dark mottle symptoms
  S (4/4): Sometimes leaves show light and dark mottle symptoms.
- K: Yellow colouration
  S (2/2): The newly emerging leaves exhibit slight yellow colouration and later they also show curling symptoms.
- K: Newly emerging leaves
  S (3/3): The newly emerging leaves exhibit slight yellow colouration and later they also show curling symptoms.
- K: Nursery under net
  S (2/2): Raise the nursery under a net of sufficient mesh size to keep out whiteflies.
- K: Seed from disease-free plants
  S (2/2): Select seed from disease-free healthy plants.
- K: Remove and destroy infected
  S (3/3): Remove and destroy infected plants in the nursery;
- K: Transplant infected seedlings
  S (3/3): do not transplant infected seedlings.
- K: Field sanitation
  S (2/2): In the field: field sanitation, rogue out affected plants, grow maize or sorghum as a barrier crop around the field, use yellow sticky traps @ 10/acre.
- K: Rogue out affected plants
  S (2/2): In the field: field sanitation, rogue out affected plants, grow maize or sorghum as a barrier crop around the field, use yellow sticky traps @ 10/acre.
- K: Grow maize or sorghum
  S (3/3): In the field: field sanitation, rogue out affected plants, grow maize or sorghum as a barrier crop around the field, use yellow sticky traps @ 10/acre.
- K: Yellow sticky traps
  S (3/3): In the field: field sanitation, rogue out affected plants, grow maize or sorghum as a barrier crop around the field, use yellow sticky traps @ 10/acre.

