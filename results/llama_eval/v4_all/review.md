# Distortion review - v4_all

prompt=prompts/advisor_v4_no_example.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## bacterial_canker - ACCEPTED, 12 kept
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
- K: Spots on leaves and stems
  S (3/3): Spots on leaves, stems and fruits.
- K: Spots on fruits and leaves
  S (3/3): Spots on leaves, stems and fruits.
- K: Spots on fruits and stems
  S (3/3): Spots on leaves, stems and fruits.
- K: Spots on fruits and leaves and stems
  S (4/4): Spots on leaves, stems and fruits.
- K: Spots on fruits and leaves and stems and shoots
  S (5/5): Disease appears as spots on leaves, stems and fruits and as wilting of leaves and shoots.

## bacterial_speck - ACCEPTED, 5 kept
- K: The spots are necrotic, circular to roughly circular.
  S (4/4): The spots are necrotic, circular to roughly circular.
- K: The tissue around the spot retains its green colour longer than normal.
  S (8/8): As the fruit approaches the pink stage, the tissue around the spot retains its green colour longer than normal.
- K: Small black spots appear on leaf, petiole, pedicel, and peduncle.
  S (8/8): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Irregular, elongated lesions appear on stem.
  S (5/5): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Summer ploughing to desiccate the bacteria and host.
  S (5/5): Summer ploughing to desiccate the bacteria and host.

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

## bacterial_wilt - ACCEPTED, 6 kept
- K: Rapid wilting of the plant
  S (2/2): Rapid and complete wilting of plant.
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

## collar_rot - ACCEPTED, 3 kept
- K: White, cottony, silvery mycelial growth on affected portion
  S (7/7): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: White to light brown mustard like sclerotium on affected portion
  S (7/8): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: Soft tissue necrosis of stem bark near soil line
  S (8/8): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.

## damping_off - ACCEPTED, 3 kept
- K: Complete rotting of seedlings
  S (3/3): Pre-emergence phase: Complete rotting of seedlings.
- K: Seedlings topple over or collapse
  S (4/4): Seedlings topple over or collapse.
- K: Infected tissues become soft and water soaked
  S (6/6): Post-emergence phase: Infected tissues become soft and water soaked.

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

## fruit_rots - ACCEPTED, 4 kept
- K: Fruit rot appears as rhythmic rotting of fruits coming with the soil contact.
  S (7/7): Symptoms appear as rhythmic rotting of fruits coming with the soil contact.
- K: Fruit rot is immediately followed by cracking and fungal growth over it.
  S (6/7): Rotting is immediately followed by cracking and fungal growth over it.
- K: Fruit rot is generally lower portion of fruits that are coming in soil contact.
  S (7/7): Generally lower portion of fruits are infected which are coming in soil contact.
- K: Fruit rot is most serious disease of kharif tomato.
  S (3/3): Rhizoctonia fruit rot is most serious disease of kharif tomato.

## fusarium_wilt - ACCEPTED, 4 kept
- K: Younger leaves die in succession
  S (3/3): Younger leaves die in succession.
- K: Petiole and leaves droop and wilt
  S (4/4): Petiole and leaves droop and wilt.
- K: Browning of vascular system
  S (3/3): Browning of vascular system.
- K: Clearing of veinlets
  S (2/2): Clearing of the veinlets and yellowing of the lower leaves.

## grey_leaf_spot - ACCEPTED, 8 kept
- K: Small circular dark brown necrotic
  S (5/5): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Numerous spots appear all over the leaf lamina
  S (6/6): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Uniformly distributed on entire foliage
  S (4/4): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Clear narrow yellow halo is visible around the spots
  S (7/7): Sometimes clear narrow yellow halo is visible around the spots.
- K: Isolated spots are usually
  S (3/3): Usually these spots are isolated but in later stage they coalesce to each other.
- K: Severely infected older leaves
  S (4/4): Severely infected older leaves blight and fall down.
- K: Fall down severely
  S (3/3): Severely infected older leaves blight and fall down.
- K: Crop debris removal
  S (3/3): Removal and burning of all crop debris after senescence of the crop.

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
- K: Bore into the fruits with the posterior end outside the hole
  S (5/5): The larvae bore into the fruits with the posterior end outside the hole.
- K: Caterpillar feeds on the leaves for some time
  S (3/4): Young larva feeds on the leaves for some time and then attacks fruits.
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

## mites - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## powdery_mildew - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## pseudocercospora_leaf_blight - ACCEPTED, 5 kept
- K: Olivacious black sooty growth of fungus on lower surface of the leaves
  S (8/8): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: Symptoms are only observed on the leaves
  S (4/4): Symptoms are only observed on the leaves.
- K: No discoloration was observed on the corresponding upper side of the leaves
  S (6/6): No discoloration was observed on the corresponding upper side of the leaves.
- K: Collect and burn the infected leaves
  S (4/4): Collect and burn the infected leaves.
- K: Be careful for selecting exotic hybrids and varieties
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
- K: Plants wilt during the hot part of day especially under dry conditions and are often stunted.
  S (8/8): Plants wilt during the hot part of day, especially under dry conditions and are often stunted.
- K: Follow crop rotation with marigold wherever possible.
  S (6/6): Follow crop rotation with marigold, wherever possible.

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

## serpentine_leaf_miner - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## spodoptera_tobacco_caterpillar - ACCEPTED, 15 kept
- K: Young larva scrap leaves on ventral surface
  S (6/6): Young larva scrap leaves on ventral surface.
- K: Grownups defoliate crops
  S (3/3): Grownups defoliate crops.
- K: This is a minor pest under open conditions
  S (5/5): This is a minor pest under open conditions and assumes severe form under protected cultivation particularly in ill managed playhouses.
- K: Assumes severe form under protected cultivation
  S (6/6): This is a minor pest under open conditions and assumes severe form under protected cultivation particularly in ill managed playhouses.
- K: Eggs are laid in clusters on foliage
  S (4/4): Eggs are laid in clusters on foliage.
- K: Young larvae feed gregariously on leaves
  S (5/5): Young larvae feed gregariously on leaves.
- K: Mature larvae, migrate and cause damage
  S (5/5): Mature larvae, migrate and cause extensive damage to leaves and fruits.
- K: They hide in soil and crop debris
  S (4/4): They hide in soil and crop debris during the day time.
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
- K: Collect and destroy egg masses
  S (3/3): Collect and destroy egg masses and early instar larvae.

## thrips - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## tomato_mosaic - ACCEPTED, 3 kept
- K: Mottling on leaves
  S (2/2): Light and dark green mottling on leaves.
- K: Light and dark green mottling on leaves
  S (5/5): Light and dark green mottling on leaves.
- K: Wilting of young leaves
  S (3/3): Wilting of young leaves.

## tomato_spotted_wilt - ACCEPTED, 9 kept
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

## tuta_absoluta_pinworm - ACCEPTED, 2 kept
- K: The leaf is infested with the South American tomato pinworm.
  S (4/5): Installation of specific lures in pheromone traps for South American tomato pinworm, fruit borer and tobacco/leaf eating caterpillar @ 10-12 traps/ ha (replace the lures with fresh ones after every 2-3 weeks).
- K: The pinworm is found on the affected fruit.
  S (3/4): Collect and destroy the pinworm affected plants and fruits.

## whitefly - ACCEPTED, 20 kept
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
- K: It has piercing and sucking mouthpart
  S (3/3): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: And both nymphs and adults feed
  S (4/4): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: On lower surface of the leaves
  S (3/3): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Causing deformation of young leaves
  S (4/4): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Whiteflies also excrete
  S (2/2): Whiteflies also excrete honeydew, causing sooty mold.
- K: Honeydew
  S (1/1): Whiteflies also excrete honeydew, causing sooty mold.
- K: Causing sooty mold
  S (3/3): Whiteflies also excrete honeydew, causing sooty mold.
- K: Remove alternate weed host
  S (4/4): Remove alternate weed host Abutilon indicum.
- K: Abutilon indicum
  S (2/2): Remove alternate weed host Abutilon indicum.
- K: Uproot and destroy the diseased
  S (3/3): Uproot and destroy the diseased leaf curl plants.
- K: Leaf curl plants
  S (2/2): Downward curling and drying of leaves.
- K: Use nitrogen and irrigation
  S (2/2): Use nitrogen and irrigation judiciously.
- K: Judiciously
  S (1/1): Use nitrogen and irrigation judiciously.
- K: Nurseries in seedling trays
  S (3/3): Raise nurseries in seedling trays under nylon nets or polyhouses.
- K: Under nylon nets or polyhouses
  S (4/4): Raise nurseries in seedling trays under nylon nets or polyhouses.

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

