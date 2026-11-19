# Distortion review - v12_all

prompt=prompts/aman_v12_no_repeat.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - ACCEPTED, 2 kept
- K: Install yellow sticky traps
  S (4/4): Install yellow sticky traps @ 4-5/acre.
- K: Use nitrogen fertilizer judiciously
  S (3/3): Use nitrogen fertilizer judiciously.

## bacterial_canker - ACCEPTED, 23 kept
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
- K: White blisters
  S (2/2): White blister like spots in the margins of leaves and turn brown.
- K: Wilting
  S (1/1): Wilting of leaves and shoots, streaks on stems and petioles.
- K: Streaks
  S (1/1): Wilting of leaves and shoots, streaks on stems and petioles.
- K: Petioles
  S (1/1): Wilting of leaves and shoots, streaks on stems and petioles.
- K: Water-soaked spots
  S (3/3): Small, water soaked spots with white halo on fruits.
- K: White halo
  S (2/2): Small, water soaked spots with white halo on fruits.
- K: Spots become slightly raised
  S (4/4): Centre of spots become slightly raised, tan coloured and rough.
- K: Spots become tan coloured
  S (3/3): Centre of spots become slightly raised, tan coloured and rough.
- K: Spots become rough
  S (3/3): Centre of spots become slightly raised, tan coloured and rough.
- K: Cankers develop
  S (2/2): Cankers develop and form cracks;
- K: Cracks form
  S (2/2): Cankers develop and form cracks;
- K: Slimy bacterial ooze
  S (3/3): slimy bacterial ooze through cracks.
- K: Vascular discolouration
  S (2/2): Vascular discolouration.
- K: Spots coalesce
  S (2/2): Spots become brown with age and coalesce, but leaves do not fall off.
- K: Leaves do not fall off
  S (2/2): Spots become brown with age and coalesce, but leaves do not fall off.
- K: Leaflets withering
  S (2/2): Leaflets on one side of rachis show withering initially.

## bacterial_speck - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## bacterial_spot - ACCEPTED, 5 kept
- K: Yellowish halo surrounds small brown water spots on tomato leaves
  S (8/8): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.
- K: Small water spots on tomato fruit
  S (4/4): Small water-soaked spots on green fruit;
- K: Small dark spots on seedling leaves
  S (4/5): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: Moist weather promotes disease development
  S (3/4): Moist weather and splattering rains are conducive to disease development.
- K: Small brown water spots on tomato leaves
  S (5/5): Small, brown, water-soaked, circular spots with yellow halo on leaves;

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

## early_blight - ACCEPTED, 10 kept
- K: Brown spots with concentric rings in a bull's eye pattern with yellow margin on tomato leaves
  S (7/8): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Fruit gets infected through calyx or stem attachment
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: Brown concentric rings on fruits
  S (3/3): brown concentric rings on fruits.
- K: Irregular leaf spots mostly appear from marginal portion of leaves
  S (7/7): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: V shaped and progress towards midrib
  S (4/4): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: Prominent yellowing on outer margin due to host specific toxin
  S (7/7): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Disease appears in vegetative phase of plant growth before flowering
  S (6/6): Mostly disease appears in vegetative phase of plant growth before flowering.
- K: Early blight is first observed on the plants as small black lesions mostly on older foliage
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Remove and destroy crop debris
  S (4/4): Remove and destroy crop debris.
- K: Follow crop rotation
  S (3/3): Follow crop rotation.

## fruit_rots - ACCEPTED, 3 kept
- K: Rhizoctonia fruit rot is most serious disease of kharif tomato.
  S (4/4): Rhizoctonia fruit rot is most serious disease of kharif tomato.
- K: Avoid the contact of fruit from soil by staking of plant.
  S (5/5): Avoid the contact of fruit from soil by staking of plant.
- K: Provide proper drainage in the field.
  S (4/4): Provide proper drainage in the field.

## fusarium_wilt - ACCEPTED, 4 kept
- K: Younger leaves die in succession
  S (3/3): Younger leaves die in succession.
- K: Petiole and leaves droop and wilt
  S (4/4): Petiole and leaves droop and wilt.
- K: Browning of vascular system
  S (3/3): Browning of vascular system.
- K: Clearing of the veinlets
  S (2/2): Clearing of the veinlets and yellowing of the lower leaves.

## grey_leaf_spot - ACCEPTED, 5 kept
- K: Small circular dark brown necrotic spots on the leaf lamina
  S (8/8): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Clear narrow yellow halo around the spots
  S (6/6): Sometimes clear narrow yellow halo is visible around the spots.
- K: Isolated spots coalesce to each other
  S (5/5): Usually these spots are isolated but in later stage they coalesce to each other.
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

## helicoverpa_fruit_borer - ACCEPTED, 8 kept
- K: Young larvae feed on tender foliage
  S (5/5): Young larvae feed on tender foliage.
- K: Mature larvae bore circular holes
  S (5/5): Mature larvae bore circular holes.
- K: Thrust only a part of its body into fruit
  S (5/5): Thrust only a part of its body into fruit and eat the inner content.
- K: Eat the inner content
  S (2/2): Thrust only a part of its body into fruit and eat the inner content.
- K: Internal tissues are eaten severely
  S (4/4): Internal tissues are eaten severely and completely hollowed out.
- K: Hollowed out
  S (1/1): Internal tissues are eaten severely and completely hollowed out.
- K: While feeding the caterpillar thrusts head inside
  S (5/5): While feeding the caterpillar thrust its head inside leaving the rest of the body outside.
- K: Leave the rest of the body outside
  S (3/4): While feeding the caterpillar thrust its head inside leaving the rest of the body outside.

## late_blight - ACCEPTED, 16 kept
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
- K: Enlarges rapidly until entire leaves are killed
  S (6/6): It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.
- K: Exposing all the fruits for infection
  S (3/3): It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.
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
- K: Ensure enough space between plants and stake
  S (5/5): Ensure enough space between plants and stake them.

## mites - ACCEPTED, 2 kept
- K: Red spider mites thrive under high temperature
  S (6/6): Red spider mites thrive under high temperature, dry weather and are more serious under protected conditions.
- K: Red spider mites are more serious under protected
  S (5/5): Red spider mites thrive under high temperature, dry weather and are more serious under protected conditions.

## powdery_mildew - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## pseudocercospora_leaf_blight - ACCEPTED, 4 kept
- K: Olivaceous black sooty growth of fungus on lower surface of the leaves
  S (7/8): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: No discoloration on upper side of the leaves
  S (4/4): No discoloration was observed on the corresponding upper side of the leaves.
- K: Collect and burn infected leaves
  S (4/4): Collect and burn the infected leaves.
- K: Be careful when selecting hybrid and variety
  S (3/4): Be careful for selecting exotic hybrids and varieties.

## root_knot_nematode - ACCEPTED, 8 kept
- K: Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
  S (12/12): Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
- K: Infected plants in patches in the field.
  S (3/3): Infected plants in patches in the field.
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

## septoria_leaf_spot - ACCEPTED, 10 kept
- K: Small, round to irregular spots with grey centre and dark margin on leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
- K: Stems and flowers are also affected.
  S (3/3): Stems and flowers are also affected.
- K: Less vigorous plant are usually affected.
  S (4/4): Less vigorous plant are usually affected.
- K: Spots usually starts on lower leaves and gradually advance upwards.
  S (8/8): Spots usually starts on lower leaves and gradually advance upwards.
- K: Spots coalesce and leaves are blighted.
  S (4/4): Spots coalesce and leaves are blighted.
- K: Complete defoliation of affected leaves.
  S (4/4): Complete defoliation of affected leaves.
- K: Stems and flowers are sometimes attacked.
  S (4/4): Stems and flowers are sometimes attacked.
- K: Fruits are rarely attacked.
  S (3/3): Fruits are rarely attacked.

## serpentine_leaf_miner - ACCEPTED, 3 kept
- K: the tiny metallic fly punctures the leaf lamina and feeds on the oozing sap
  S (7/7): The tiny, metallic fly punctures the leaf lamina and feeds on the oozing sap.
- K: typical serpentine shaped tunnels are formed in the leaf lamina indicating the path of feeding by the maggots
  S (11/11): Typical serpentine shaped tunnels are formed in the leaf lamina indicating the path of feeding by the maggots.
- K: leaves with serpentine mines are present on the tomato leaf
  S (3/4): Leaves with serpentine mines.

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
- K: Mature larvae, migrate and cause extensive damage
  S (6/6): Mature larvae, migrate and cause extensive damage to leaves and fruits.
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

## thrips - ACCEPTED, 9 kept
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
- K: Blue sticky traps
  S (3/3): Install blue sticky traps @ 10 traps/ha against thrips;
- K: Install traps
  S (2/2): Install blue sticky traps @ 10 traps/ha against thrips;
- K: Use blue sticky traps
  S (3/3): Install blue sticky traps @ 10 traps/ha against thrips;
- K: Use sorghum or maize
  S (2/2): Grow 5-6 rows of sorghum or maize around the field as a barrier crop.

## tomato_mosaic - ACCEPTED, 3 kept
- K: Mottling on leaves
  S (2/2): Light and dark green mottling on leaves.
- K: Light and dark green mottling on leaves
  S (5/5): Light and dark green mottling on leaves.
- K: Wilting of young leaves
  S (3/3): Wilting of young leaves.

## tomato_spotted_wilt - ACCEPTED, 18 kept
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
- K: Among Hosts
  S (2/2): Symptoms vary among hosts and in a single host species.
- K: In Single Host Species
  S (3/3): Symptoms vary among hosts and in a single host species.
- K: TSWV Infection
  S (2/2): Stunting is a common symptom of TSWV infection.
- K: Stunting is a Common Symptom
  S (3/3): Stunting is a common symptom of TSWV infection.
- K: Chlorotic or Necrotic Rings Form
  S (4/4): Chlorotic or necrotic rings form on the leaves of many infected hosts.
- K: On the Leaves of Many Infected Hosts
  S (4/4): Chlorotic or necrotic rings form on the leaves of many infected hosts.
- K: Thickening of Veins and Bronzing of Young Leaves
  S (5/5): Thickening of veins and bronzing of young leaves.
- K: Growing Tips May Die-Back
  S (3/3): Growing tips die-back and wilt.

## tuta_absoluta_pinworm - ACCEPTED, 3 kept
- K: Destroy the pinworm affected plants and fruits.
  S (4/4): Collect and destroy the pinworm affected plants and fruits.
- K: Avoid solanaceous crops after tomato.
  S (4/4): Avoid solanaceous crops after tomato.
- K: Use healthy seedlings for transplanting.
  S (3/3): Use healthy seedlings for transplanting.

## whitefly - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

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

