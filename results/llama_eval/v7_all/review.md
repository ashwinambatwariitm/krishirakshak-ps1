# Distortion review - v7_all

prompt=prompts/aman_v7_task_in_user.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - ACCEPTED, 3 kept
- K: Install yellow sticky traps @ 4-5/acre.
  S (5/5): Install yellow sticky traps @ 4-5/acre.
- K: Use nitrogen fertilizer judiciously.
  S (3/3): Use nitrogen fertilizer judiciously.
- K: Aphids are sucking pests of tomato.
  S (3/3): Aphids (Myzus persicae, Aphis gossypii) are sucking pests of tomato.

## bacterial_canker - ACCEPTED, 14 kept
- K: Seedlings affected
  S (2/2): Seedlings, leaves, stem and fruits are affected.
- K: Leaves affected
  S (2/2): Seedlings, leaves, stem and fruits are affected.
- K: Stem affected
  S (2/2): Seedlings, leaves, stem and fruits are affected.
- K: Fruits affected
  S (2/2): Seedlings, leaves, stem and fruits are affected.
- K: Spots on leaves
  S (2/2): Spots on leaves, stems and fruits.
- K: Spots on stems
  S (2/2): Spots on leaves, stems and fruits.
- K: Spots on fruits
  S (2/2): Spots on leaves, stems and fruits.
- K: Spots become brown
  S (3/3): Spots become brown with age and coalesce, but leaves do not fall off.
- K: Spots become rough
  S (3/3): Centre of spots become slightly raised, tan coloured and rough.
- K: Spots become tan
  S (2/2): Centre of spots become slightly raised, tan coloured and rough.
- K: Spots become slightly raised
  S (4/4): Centre of spots become slightly raised, tan coloured and rough.
- K: Spots become slightly wrinkled
  S (3/4): Centre of spots become slightly raised, tan coloured and rough.
- K: Spots become slightly discolored
  S (3/4): Centre of spots become slightly raised, tan coloured and rough.
- K: Spots become slightly discolored and rough
  S (4/5): Centre of spots become slightly raised, tan coloured and rough.

## bacterial_speck - ACCEPTED, 4 kept
- K: The tissue around the spot retains its green colour longer than normal.
  S (8/8): As the fruit approaches the pink stage, the tissue around the spot retains its green colour longer than normal.
- K: Small black spots appear on the leaf, petiole, pedicel, and peduncle.
  S (8/8): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Irregular, elongated lesions appear on the stem.
  S (5/5): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: The spots on the tomato leaves are necrotic, circular to roughly circular.
  S (4/5): The spots are necrotic, circular to roughly circular.

## bacterial_spot - ACCEPTED, 4 kept
- K: Small, brown, water-soaked, circular spots with yellow halo on leaves
  S (9/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: Small, dark spots on leaflets and stems of seedlings
  S (6/6): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: Moist weather and splattering rains are disease development
  S (5/5): Moist weather and splattering rains are conducive to disease development.
- K: Infected leaves show small, brown, water-soaked, circular spots
  S (9/9): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.

## bacterial_wilt - ACCEPTED, 3 kept
- K: * The wilting is happening on the lower leaves.
  S (3/4): Lower leaves drop before wilting.
- K: **Symptoms**
  S (1/1): Characteristic symptoms of bacterial wilt are the rapid and complete wilting of normal grown up plants.
- K: * The plant is wilting rapidly.
  S (2/2): Rapid and complete wilting of plant.

## collar_rot - ACCEPTED, 3 kept
- K: White, cottony, and silvery mycelial growth
  S (5/5): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: White to light brown mustard-like sclerotium
  S (6/6): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: Soft tissue necrosis of bark near soil line
  S (7/7): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.

## damping_off - ACCEPTED, 6 kept
- K: **Pre-emergence phase**
  S (2/2): Pre-emergence phase: Complete rotting of seedlings.
- K: - Complete rotting of seedlings is the first phase.
  S (4/4): Pre-emergence phase: Complete rotting of seedlings.
- K: - Infected tissues become soft and water soaked.
  S (6/6): Post-emergence phase: Infected tissues become soft and water soaked.
- K: - Seedlings topple over or collapse.
  S (4/4): Seedlings topple over or collapse.
- K: **Damping off of tomato**
  S (1/1): Damping off of tomato occurs in two stages, i.e.
- K: - In the pre-emergence phase, seedlings are killed just before reaching the soil surface.
  S (9/9): In the pre-emergence the phase the seedlings are killed just before they reach the soil surface.

## early_blight - ACCEPTED, 10 kept
- K: Brown Spots with Concentric Rings
  S (3/3): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Fruit gets infected through calyx or stem attachment;
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: brown concentric rings on fruits.
  S (3/3): brown concentric rings on fruits.
- K: Irregular Leaf Spots
  S (3/3): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: Symptoms are V-shaped and progress towards midrib.
  S (5/5): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
  S (11/11): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Early Blight
  S (2/2): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: This is a common disease of tomato occurring on the foliage at any stage of the growth.
  S (5/5): This is a common disease of tomato occurring on the foliage at any stage of the growth.
- K: The fungus attacks the foliage causing characteristic leaf spots and blight.
  S (7/7): The fungus attacks the foliage causing characteristic leaf spots and blight.
- K: Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.

## fruit_rots - ACCEPTED, 8 kept
- K: Symptoms appear as rhythmic rotting
  S (4/4): Symptoms appear as rhythmic rotting of fruits coming with the soil contact.
- K: Rotting is immediately followed by cracking
  S (4/4): Rotting is immediately followed by cracking and fungal growth over it.
- K: Fungal growth over it
  S (3/3): Rotting is immediately followed by cracking and fungal growth over it.
- K: Lower portion of fruits are infected
  S (4/4): Generally lower portion of fruits are infected which are coming in soil contact.
- K: Contact of fruit from soil
  S (3/3): Symptoms appear as rhythmic rotting of fruits coming with the soil contact.
- K: Staking of plant
  S (1/1): Avoid the contact of fruit from soil by staking of plant.
- K: Proper drainage in the field
  S (3/3): Provide proper drainage in the field.
- K: Rhizoctonia fruit rot is most serious disease
  S (3/3): Rhizoctonia fruit rot is most serious disease of kharif tomato.

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
- K: Grey leaf spot on a tomato leaf
  S (2/3): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: * Small circular dark brown necrotic
  S (5/5): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: * Numerous spots appear all over the leaf lamina
  S (6/6): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: * Uniformly distributed on entire foliage
  S (4/4): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: * Clear narrow yellow halo is visible around the spots
  S (7/7): Sometimes clear narrow yellow halo is visible around the spots.
- K: * Usually isolated but coalesce in later stages
  S (4/5): Usually these spots are isolated but in later stage they coalesce to each other.
- K: * Severely infected older leaves blight and fall down
  S (7/7): Severely infected older leaves blight and fall down.

## healthy - ACCEPTED, 6 kept
- K: Avoid growing tomato in the same field season after season
  S (6/6): Avoid growing tomato in the same field season after season;
- K: Rotate with non-host crops such as cereals and legumes
  S (5/5): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.
- K: Stake plants and use drip irrigation
  S (3/3): Stake plants and use drip irrigation to reduce leaf wetness.
- K: Collect and destroy infected leaves, shoots and fruits
  S (6/6): Collect and destroy infected leaves, shoots and fruits.
- K: Spray only need-based, label-claim pesticides
  S (7/7): Spray only need-based, label-claim pesticides.
- K: Conduct agro-ecosystem analysis weekly
  S (5/5): Conduct agro-ecosystem analysis (AESA) weekly in the morning, preferably before 9 a.m.

## helicoverpa_fruit_borer - ACCEPTED, 9 kept
- K: Young larvae feed on tender foliage.
  S (5/5): Young larvae feed on tender foliage.
- K: Mature larvae bore circular holes.
  S (5/5): Mature larvae bore circular holes.
- K: Thrust only a part of its body into fruit and eat the inner content.
  S (7/7): Thrust only a part of its body into fruit and eat the inner content.
- K: Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
  S (13/13): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: The larvae bore into the fruits with the posterior end outside the hole.
  S (6/6): The larvae bore into the fruits with the posterior end outside the hole.
- K: Young larva feeds on the leaves for some time and then attacks fruits.
  S (7/7): Young larva feeds on the leaves for some time and then attacks fruits.
- K: Internal tissues are eaten severely and completely hollowed out.
  S (6/6): Internal tissues are eaten severely and completely hollowed out.
- K: While feeding the caterpillar thrust its head inside leaving the rest of the body outside.
  S (9/9): While feeding the caterpillar thrust its head inside leaving the rest of the body outside.
- K: Grow simultaneously 40 days old American tall marigold and 25 days old tomato seedling at 1:16 rows.
  S (8/8): Grow simultaneously 40 days old American tall marigold and 25 days old tomato seedling at 1:16 rows.

## late_blight - ACCEPTED, 7 kept
- K: * Lesions expand rapidly
  S (3/3): Lesions expand rapidly and the entire leaf becomes necrotic.
- K: * Entire leaf becomes necrotic
  S (4/4): Lesions expand rapidly and the entire leaf becomes necrotic.
- K: * White sporulation on leaves
  S (3/3): White sporulation on leaves.
- K: * Dark brown lesions on fruit
  S (4/4): Dark brown lesions on fruit;
- K: * Soft rot and disintegration of fruits
  S (3/3): soft rot and disintegration of fruits.
- K: **Symptoms**
  S (1/1): Farmers should check their tomato plants regularly and look for these warning signs and symptoms.
- K: * Water-soaked black lesions on leaves and stems
  S (6/6): Water-soaked black lesions on leaves and stems.

## mites - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## powdery_mildew - ACCEPTED, 2 kept
- K: * Irregular, bright yellow blotches with yellow halo appear on leaves
  S (7/7): Irregular, bright yellow blotches with yellow halo appear on leaves.
- K: * Abundant white sporulation in the infected area of leaves
  S (6/6): Abundant white sporulation in the infected area of leaves.

## pseudocercospora_leaf_blight - ACCEPTED, 8 kept
- K: The symptoms of the disease are:
  S (1/1): Symptoms are only observed on the leaves.
- K: * Black sooty growth on the lower surface of the leaves
  S (6/6): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: * The leaves
  S (1/1): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: * The lower surface of the leaves
  S (3/3): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: * The fungus
  S (1/1): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: * The sooty growth
  S (2/2): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: * Collect and burn the infected leaves
  S (4/4): Collect and burn the infected leaves.
- K: * Be careful when selecting exotic hybrids and varieties
  S (5/5): Be careful for selecting exotic hybrids and varieties.

## root_knot_nematode - ACCEPTED, 9 kept
- K: Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system.
  S (10/10): Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
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

## septoria_leaf_spot - ACCEPTED, 4 kept
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
- K: Stems and flowers are also affected.
  S (3/3): Stems and flowers are also affected.
- K: Small, round to irregular spots with grey centre and dark margin on leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.

## serpentine_leaf_miner - ACCEPTED, 4 kept
- K: **Serpentine Leaf Miner**
  S (3/3): Flowering plants for serpentine leaf miner - Attractant plants: Carrot family, sunflower family, buck wheat, French bean (predatory thrips).
- K: * The tiny, metallic fly punctures the leaf lamina and feeds on the oozing sap.
  S (7/7): The tiny, metallic fly punctures the leaf lamina and feeds on the oozing sap.
- K: * Typical serpentine shaped tunnels are formed in the leaf lamina indicating the path of feeding by the maggots.
  S (11/11): Typical serpentine shaped tunnels are formed in the leaf lamina indicating the path of feeding by the maggots.
- K: * Leaves with serpentine mines are a sign of the disease.
  S (3/4): Leaves with serpentine mines.

## spodoptera_tobacco_caterpillar - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## thrips - ACCEPTED, 2 kept
- K: **Thrips on Tomato Leaves**
  S (2/2): For thrips: Count and record the number of nymphs and adults of thrips present on five terminal leaves per plant (tapping method also can be used to count thrips).
- K: Thrips are sucking pests of tomato leaves.
  S (3/4): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.

## tomato_mosaic - ACCEPTED, 5 kept
- K: Wilting of young leaves
  S (3/3): Wilting of young leaves.
- K: Leaflets distorted and puckered
  S (3/3): Leaflets distorted and puckered.
- K: Fern leaf symptoms
  S (3/3): Fern leaf symptoms.
- K: Stunted growth
  S (2/2): Stunted growth.
- K: Light and dark green mottling
  S (4/4): Light and dark green mottling on leaves.

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
- K: Yellow Areas with Concentric Circular Markings
  S (4/4): Yellow areas with concentric circular markings in fruit.
- K: Discoloration of Seed
  S (2/2): Discoloration of seed.
- K: Symptoms Vary
  S (2/2): Symptoms vary among hosts and in a single host species.
- K: Stunting is a Common Symptom
  S (3/3): Stunting is a common symptom of TSWV infection.
- K: Chlorotic or Necrotic Rings Form
  S (4/4): Chlorotic or necrotic rings form on the leaves of many infected hosts.
- K: Thickening of Veins and Bronzing of Young Leaves
  S (5/5): Thickening of veins and bronzing of young leaves.
- K: Growing Tips May Die-Back
  S (3/3): Growing tips die-back and wilt.

## tuta_absoluta_pinworm - ACCEPTED, 4 kept
- K: * Tomato leaves
  S (1/1): Mining of leaves, stem and pinholes on fruits.
- K: * Tomato stems
  S (1/1): Mining of leaves, stem and pinholes on fruits.
- K: * Tomato pinholes
  S (1/1): Mining of leaves, stem and pinholes on fruits.
- K: **Pests**
  S (1/1): In case of pests which are active during night like Spodoptera spray recommended biocides/ chemicals at the time of their appearance in the night.

## whitefly - ACCEPTED, 12 kept
- K: * Yellowing
  S (1/1): Yellowing.
- K: * Downward curling and drying of leaves
  S (4/4): Downward curling and drying of leaves.
- K: * Vector of tomato leaf curl disease
  S (3/3): Vector of tomato leaf curl disease.
- K: Whitefly is a well-known vector
  S (4/4): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: * Transmits tomato leaf curl virus
  S (4/4): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: * Feeds on lower surface of leaves
  S (4/4): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: * Causes deformation of young leaves
  S (4/4): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: * Causes sooty mold
  S (3/3): Whiteflies also excrete honeydew, causing sooty mold.
- K: Remove alternate weed host Abutilon indicum
  S (6/6): Remove alternate weed host Abutilon indicum.
- K: * Uproot and destroy the diseased leaf curl plants
  S (5/5): Uproot and destroy the diseased leaf curl plants.
- K: * Use nitrogen and irrigation judiciously
  S (3/3): Use nitrogen and irrigation judiciously.
- K: Raise nurseries in seedling trays under nylon nets or polyhouses
  S (8/8): Raise nurseries in seedling trays under nylon nets or polyhouses.

## yellow_leaf_curl_virus - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

