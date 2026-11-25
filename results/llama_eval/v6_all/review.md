# Distortion review - v6_all

prompt=prompts/advisor_v6_full_stop.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## bacterial_canker - ACCEPTED, 2 kept
- K: The affected parts are seedlings, leaves, stem and fruits.
  S (5/6): Seedlings, leaves, stem and fruits are affected.
- K: The affected parts are leaves, stems and fruits.
  S (4/5): Seedlings, leaves, stem and fruits are affected.

## bacterial_speck - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## bacterial_spot - ACCEPTED, 8 kept
- K: Small, brown, water-soaked, circular spots with yellow halo on leaves;
  S (9/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: older leaves fall.
  S (3/3): older leaves fall.
- K: Small water-soaked spots on green fruit.
  S (6/6): Small water-soaked spots on green fruit;
- K: Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
  S (9/9): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: Moist weather and splattering rains are conducive to disease development.
  S (6/6): Moist weather and splattering rains are conducive to disease development.
- K: Most outbreaks of the disease can be traced back to heavy rainstorms that occur in the area.
  S (7/7): Most outbreaks of the disease can be traced back to heavy rainstorms that occur in the area.
- K: Infected leaves show small, brown, water-soaked, circular spots surrounded with yellowish halo.
  S (12/12): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.
- K: On older plants the leaflet infection is mostly on older leaves and may cause serious defoliation.
  S (7/7): On older plants the leaflet infection is mostly on older leaves and may cause serious defoliation.

## bacterial_wilt - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## collar_rot - ACCEPTED, 12 kept
- K: Soft tissue necrosis of bark of the stem near soil line
  S (8/8): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.
- K: White, cottony and silvery mycelial growth on the affected portion
  S (7/7): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: White to light brown mustard like sclerotium on the same portion
  S (8/8): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: Progressive dropping and yellowing followed by wilting of the entire plant
  S (6/6): Progressive dropping and yellowing followed by wilting of the entire plant is observed.
- K: Sometime plants collapse soon after infection
  S (5/5): Sometime plants collapse soon after infection.
- K: Use crop rotation with cereals, corn, sorghum and millets
  S (6/6): Use crop rotation with cereals, corn, sorghum and millets.
- K: Remove all the weeds from field
  S (3/3): Remove all the weeds from field.
- K: Avoid use of infested farmyard manure, soil crop debris and compost in the field
  S (9/9): Avoid use of infested farmyard manure, soil crop debris and compost in the field.
- K: Irrigate the soil in summer
  S (3/3): Irrigate the soil in summer and plough the field to destroy germinating sclerotia.
- K: Plough the field to destroy germinating sclerotia
  S (5/5): Irrigate the soil in summer and plough the field to destroy germinating sclerotia.
- K: Avoid dense planting and maintain proper aeration near collar region
  S (9/9): Avoid dense planting and maintain proper aeration near collar region.
- K: Use Ammonium Nitrate as a fertilizer for nitrogen source
  S (5/5): Use Ammonium Nitrate as a fertilizer for nitrogen source.

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
- K: Early blight is first observed on the plants as small black lesions mostly on the older foliage.
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Remove and destroy crop debris.
  S (4/4): Remove and destroy crop debris.
- K: Follow crop rotation.
  S (3/3): Follow crop rotation.

## fruit_rots - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

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

## grey_leaf_spot - ACCEPTED, 2 kept
- K: The symptoms are small circular dark brown necrotic spots on the leaf lamina, all over the leaf, and the spots are numerous.
  S (10/11): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Severely infected older leaves are severely blighted and fall down.
  S (7/7): Severely infected older leaves blight and fall down.

## healthy - ACCEPTED, 7 kept
- K: Avoid growing tomato in the same field season after season.
  S (6/6): Avoid growing tomato in the same field season after season;
- K: Rotate with non-host crops such as cereals and legumes.
  S (5/5): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.
- K: Stake plants.
  S (1/1): Stake plants and use drip irrigation to reduce leaf wetness.
- K: Use drip irrigation.
  S (2/2): Stake plants and use drip irrigation to reduce leaf wetness.
- K: Collect and destroy infected leaves, shoots and fruits.
  S (6/6): Collect and destroy infected leaves, shoots and fruits.
- K: Spray only need-based, label-claim pesticides.
  S (7/7): Spray only need-based, label-claim pesticides.
- K: Conduct agro-ecosystem analysis weekly.
  S (5/5): Conduct agro-ecosystem analysis (AESA) weekly in the morning, preferably before 9 a.m.

## helicoverpa_fruit_borer - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## late_blight - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## mites - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## powdery_mildew - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## pseudocercospora_leaf_blight - ACCEPTED, 2 kept
- K: The fungus growth is black sooty.
  S (4/4): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: Burn the infected leaves.
  S (3/3): Collect and burn the infected leaves.

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
- K: Plants wilt during the hot part of day especially under dry conditions and are often stunted.
  S (8/8): Plants wilt during the hot part of day, especially under dry conditions and are often stunted.
- K: Follow crop rotation with marigold wherever possible.
  S (6/6): Follow crop rotation with marigold, wherever possible.

## septoria_leaf_spot - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## serpentine_leaf_miner - ACCEPTED, 3 kept
- K: The leaf has a serpentine shape.
  S (3/3): Typical serpentine shaped tunnels are formed in the leaf lamina indicating the path of feeding by the maggots.
- K: The tiny fly punctures the leaf.
  S (3/3): The tiny, metallic fly punctures the leaf lamina and feeds on the oozing sap.
- K: The fly feeds on the sap.
  S (1/1): The tiny, metallic fly punctures the leaf lamina and feeds on the oozing sap.

## spodoptera_tobacco_caterpillar - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## thrips - ACCEPTED, 15 kept
- K: Thrips are sucking pests of tomato.
  S (3/3): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.
- K: Silvery streaks on leaf surface.
  S (4/4): Silvery streaks on leaf surface.
- K: Pre-mature dropping of flowers.
  S (3/3): Pre-mature dropping of flowers.
- K: Bud necrosis.
  S (1/1): Bud necrosis.
- K: Vector of tomato spotted wilt virus.
  S (4/4): Vector of tomato spotted wilt virus.
- K: Install blue sticky traps.
  S (4/4): Install blue sticky traps @ 10 traps/ha against thrips;
- K: Against thrips.
  S (2/2): Install blue sticky traps @ 10 traps/ha against thrips;
- K: Locally available.
  S (2/2): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: Empty tins painted blue.
  S (4/4): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: Coated with grease.
  S (2/2): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: Vaseline.
  S (1/1): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: Castor oil.
  S (1/1): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: Grow 5-6 rows of sorghum.
  S (3/3): Grow 5-6 rows of sorghum or maize around the field as a barrier crop.
- K: Or maize.
  S (1/1): Grow 5-6 rows of sorghum or maize around the field as a barrier crop.
- K: Around the field.
  S (2/2): Grow 5-6 rows of sorghum or maize around the field as a barrier crop.

## tomato_mosaic - ACCEPTED, 4 kept
- K: The affected leaves are usually distorted and puckered.
  S (5/5): The leaflets of affected leaves are usually distorted, puckered and smaller than normal.
- K: The affected plant is usually stunted, pale green, and spindly.
  S (5/6): The affected plant appears stunted, pale green and spindly.
- K: The disease is characterized by the presence of light and dark green mottling on the leaves.
  S (6/7): The disease is characterized by light and dark green mottling on the leaves often accompanied by wilting of young leaves in sunny days when plants first become infected.
- K: The mottling is often accompanied by wilting of young leaves.
  S (6/6): The disease is characterized by light and dark green mottling on the leaves often accompanied by wilting of young leaves in sunny days when plants first become infected.

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

## tuta_absoluta_pinworm - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## whitefly - ACCEPTED, 3 kept
- K: Yellowing
  S (1/1): Yellowing.
- K: Downward curling and drying of leaves
  S (4/4): Downward curling and drying of leaves.
- K: Vector of tomato leaf curl disease
  S (3/3): Vector of tomato leaf curl disease.

## yellow_leaf_curl_virus - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

