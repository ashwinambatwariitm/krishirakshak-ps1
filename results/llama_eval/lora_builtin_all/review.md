# Distortion review - lora_builtin_all

prompt=built-in options=--llama-pte models/llama3_2_1b_krishirakshak_lora_8da4w.pte

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - ACCEPTED, 2 kept
- K: Aphids are sucking pests of tomatoes.
  S (4/4): Aphids (Myzus persicae, Aphis gossypii) are sucking pests of tomato.
- K: Use nitrogen fertilizer judiciously.
  S (3/3): Use nitrogen fertilizer judiciously.

## bacterial_canker - ACCEPTED, 8 kept
- K: Seedlings, leaves, stem, and fruits are affected.
  S (5/5): Seedlings, leaves, stem and fruits are affected.
- K: Spots appear on leaves, stems, and fruits.
  S (5/5): Disease appears as spots on leaves, stems and fruits and as wilting of leaves and shoots.
- K: White blisters form in the margins of leaves.
  S (4/5): White blister like spots in the margins of leaves and turn brown.
- K: Leaves and shoots wilt.
  S (3/3): Wilting of leaves and shoots, streaks on stems and petioles.
- K: Streaks appear on stems and petioles.
  S (3/4): Wilting of leaves and shoots, streaks on stems and petioles.
- K: Small, water-soaked spots with a white halo appear on fruits.
  S (7/8): Small, water soaked spots with white halo on fruits.
- K: The center of the spots becomes raised, tan, and rough.
  S (4/5): Centre of spots become slightly raised, tan coloured and rough.
- K: Cankers develop and form cracks.
  S (4/4): Cankers develop and form cracks;

## bacterial_speck - ACCEPTED, 2 kept
- K: Small black spots appear on the leaf, stem, and parts that hold the leaf to the plant.
  S (6/8): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Irregular, elongated lesions appear on the stem.
  S (5/5): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.

## bacterial_spot - ACCEPTED, 2 kept
- K: Small, brown, water-soaked, circular spots with a yellow halo appear on leaves.
  S (9/10): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: Use disease-free seed.
  S (2/2): Use disease-free seed.

## bacterial_wilt - ACCEPTED, 2 kept
- K: Wilting of the plant happens quickly and completely.
  S (3/4): Rapid and complete wilting of plant.
- K: Lower leaves drop off before wilting.
  S (5/5): Lower leaves drop before wilting.

## collar_rot - ACCEPTED, 9 kept
- K: Soft tissue necrosis appears on the stem near the soil line.
  S (7/8): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.
- K: White, cottony, and silvery mycelial growth is visible on the affected area.
  S (7/8): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: Later, a white to light brown mustard-like sclerotium appears.
  S (7/8): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: Plants may collapse soon after infection.
  S (4/4): Sometime plants collapse soon after infection.
- K: Use crop rotation with cereals, corn, sorghum, and millets.
  S (6/6): Use crop rotation with cereals, corn, sorghum and millets.
- K: Remove all weeds from the field.
  S (3/3): Remove all the weeds from field.
- K: Do not use infested farmyard manure, soil crop debris, or compost in the field.
  S (8/8): Avoid use of infested farmyard manure, soil crop debris and compost in the field.
- K: Irrigate the soil in summer and plough the field to destroy germinating sclerotia.
  S (8/8): Irrigate the soil in summer and plough the field to destroy germinating sclerotia.
- K: Use Ammonium Nitrate as a fertilizer.
  S (3/3): Use Ammonium Nitrate as a fertilizer for nitrogen source.

## damping_off - ACCEPTED, 2 kept
- K: Seedlings rot completely before reaching the soil.
  S (4/5): In the pre-emergence the phase the seedlings are killed just before they reach the soil surface.
- K: Use raised beds of 15 cm height.
  S (3/3): Use raised beds of 15 cm height.

## early_blight - ACCEPTED, 3 kept
- K: Brown spots with concentric rings in a bull's eye pattern with a yellow margin appear on the leaves.
  S (7/9): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Irregular leaf spots appear on the margins of the leaves.
  S (4/5): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: The disease appears in the vegetative phase of the plant growth before flowering.
  S (6/6): Mostly disease appears in vegetative phase of plant growth before flowering.

## fruit_rots - ACCEPTED, 3 kept
- K: Rhizoctonia fruit rot is the most serious disease of kharif tomatoes.
  S (5/5): Rhizoctonia fruit rot is most serious disease of kharif tomato.
- K: To prevent the disease, keep the fruits off the soil by staking the plants.
  S (3/4): Avoid the contact of fruit from soil by staking of plant.
- K: Ensure proper drainage in the field.
  S (3/4): Provide proper drainage in the field.

## fusarium_wilt - ACCEPTED, 2 kept
- K: Younger leaves die one by one.
  S (2/2): Younger leaves die in succession.
- K: Petiole and leaves droop and wilt.
  S (4/4): Petiole and leaves droop and wilt.

## grey_leaf_spot - ACCEPTED, 4 kept
- K: Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
  S (14/14): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Sometimes clear narrow yellow halo is visible around the spots.
  S (8/8): Sometimes clear narrow yellow halo is visible around the spots.
- K: Usually these spots are isolated but in later stage they coalesce to each other.
  S (8/8): Usually these spots are isolated but in later stage they coalesce to each other.
- K: Severely infected older leaves blight and fall down.
  S (7/7): Severely infected older leaves blight and fall down.

## healthy - ACCEPTED, 2 kept
- K: Rotate tomato plants with non-host crops like cereals and legumes.
  S (5/6): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.
- K: Do not plant tomatoes with chillies or brinjals.
  S (3/3): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.

## helicoverpa_fruit_borer - ACCEPTED, 3 kept
- K: Young larvae eat tender leaves.
  S (4/4): Young larvae feed on tender foliage.
- K: Mature larvae make circular holes in the leaves.
  S (4/5): Mature larvae bore circular holes.
- K: Eggs hatch in 3-4 days and the first larvae eat leaves and later move to the fruit.
  S (7/8): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.

## late_blight - ACCEPTED, 2 kept
- K: The lesions expand rapidly, and the leaf becomes completely dead.
  S (6/7): Lesions expand rapidly and the entire leaf becomes necrotic.
- K: White spores are seen on leaves.
  S (3/4): White sporulation on leaves.

## mites - ACCEPTED, 5 kept
- K: Affected leaves turn reddish brown and bronzy.
  S (5/6): Affected leaves become reddish brown and bronzy.
- K: Severe infestation leaves silken webbing on the leaves, wither and dry.
  S (6/6): Severe infestation larvae silken webbing on the leaves, wither and dry.
- K: Flower and fruit formation are affected.
  S (4/4): Flower and fruit formation affected.
- K: Plant tall border crops like maize or sorghum.
  S (5/6): Plant tall border crops such as maize or sorghum.
- K: Spray thoroughly on the underside of the leaves.
  S (4/4): Spray thoroughly on the underside of the leaves.

## powdery_mildew - ACCEPTED, 4 kept
- K: Yellow blotches with a yellow halo appear on leaves.
  S (5/5): Irregular, bright yellow blotches with yellow halo appear on leaves.
- K: Abundant white spores are found in the infected area.
  S (5/6): Abundant white sporulation in the infected area of leaves.
- K: Plant tomatoes 3 feet apart to allow for good air circulation.
  S (4/5): Proper plant spacing of about 3 feet apart to allow for proper air circulation, which helps the foliage dry faster.
- K: Mulch around the plants to protect the roots.
  S (4/4): Organic mulch added around the plants will protect roots while preventing fungal spores from splashing onto the plant.

## pseudocercospora_leaf_blight - ACCEPTED, 4 kept
- K: Symptoms only appear on the leaves.
  S (3/4): Symptoms are only observed on the leaves.
- K: The leaves will soon fall off after infection.
  S (4/5): Leaf defoliate soon after infection.
- K: No discoloration was seen on the upper side of the leaves.
  S (4/5): No discoloration was observed on the corresponding upper side of the leaves.
- K: Burn the infected leaves.
  S (3/3): Collect and burn the infected leaves.

## root_knot_nematode - ACCEPTED, 3 kept
- K: Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system, showing heavy galling.
  S (12/12): Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
- K: Infected plants appear in patches in the field.
  S (3/4): Infected plants in patches in the field.
- K: Roots branch profusely from the gall tissue, causing a 'beard root' symptom.
  S (9/9): Roots branch profusely starting from the gall tissue causing a 'beard root' symptom.

## septoria_leaf_spot - ACCEPTED, 4 kept
- K: Small, round to irregular spots with a grey centre and dark margin on leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
- K: Stems and flowers are also affected.
  S (3/3): Stems and flowers are also affected.

## serpentine_leaf_miner - ACCEPTED, 3 kept
- K: Leaves with serpentine mines drop off.
  S (3/4): Leaves with serpentine mines.
- K: The tiny, metallic fly punctures the leaf and feeds on the sap.
  S (5/5): The tiny, metallic fly punctures the leaf lamina and feeds on the oozing sap.
- K: Typical serpentine shaped tunnels are formed in the leaf.
  S (6/6): Typical serpentine shaped tunnels are formed in the leaf lamina indicating the path of feeding by the maggots.

## spodoptera_tobacco_caterpillar - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## thrips - ACCEPTED, 3 kept
- K: Thrips suck the sap from tomato plants.
  S (2/2): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.
- K: Use locally available empty tins painted blue and coated with grease, vaseline, or castor oil as an alternative trap.
  S (10/12): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: Plant 5-6 rows of sorghum or maize around the field as a barrier crop.
  S (7/7): Grow 5-6 rows of sorghum or maize around the field as a barrier crop.

## tomato_mosaic - ACCEPTED, 3 kept
- K: Mottling on leaves with wilting of young leaves in sunny days.
  S (6/6): The disease is characterized by light and dark green mottling on the leaves often accompanied by wilting of young leaves in sunny days when plants first become infected.
- K: The leaflets are distorted, puckered, and smaller than normal.
  S (5/5): The leaflets of affected leaves are usually distorted, puckered and smaller than normal.
- K: The affected plant is stunted, pale green, and spindly.
  S (5/5): The affected plant appears stunted, pale green and spindly.

## tomato_spotted_wilt - ACCEPTED, 5 kept
- K: Severe stunting.
  S (2/2): Severe stunting.
- K: Chlorotic or necrotic rings form on the leaves of many infected hosts.
  S (8/8): Chlorotic or necrotic rings form on the leaves of many infected hosts.
- K: Growing tips may die-back and terminal branches may be streaked.
  S (6/6): Growing tips may die-back and terminal branches may be streaked.
- K: Use healthy seedlings for transplanting.
  S (3/3): Use of healthy seedlings for transplanting.
- K: Plant sorghum, maize, or bajra as a barrier crop.
  S (5/5): Growing sorghum, maize or bajra as barrier crop.

## tuta_absoluta_pinworm - ACCEPTED, 2 kept
- K: Destroy the plants and fruits that are infested with the pinworm.
  S (3/4): Collect and destroy the pinworm affected plants and fruits.
- K: Use healthy seedlings when transplanting tomatoes.
  S (3/4): Use healthy seedlings for transplanting.

## whitefly - ACCEPTED, 2 kept
- K: Whitefly is a vector that spreads tomato leaf curl disease.
  S (4/5): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: Whitefly has a mouthpart that pierces and sucks the sap from leaves.
  S (4/5): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.

## yellow_leaf_curl_virus - ACCEPTED, 2 kept
- K: Whiteflies spread the virus.
  S (3/3): The virus is spread by whiteflies (Bemisia tabaci).
- K: Remove and destroy infected plants.
  S (3/3): Remove and destroy infected plants in the nursery;

