# Distortion review - lora_v10_all

prompt=prompts/aman_v10_no_diagnosis.txt options=--llama-pte models/llama3_2_1b_krishirakshak_lora_8da4w.pte

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## bacterial_canker - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## bacterial_speck - ACCEPTED, 2 kept
- K: Small black spots appear on leaf, petiole, pedicel, and peduncle.
  S (8/8): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Irregular, elongated lesions appear on stem.
  S (5/5): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.

## bacterial_spot - ACCEPTED, 4 kept
- K: Small, brown, water-soaked, circular spots with yellow halo on leaves;
  S (9/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: older leaves fall.
  S (3/3): older leaves fall.
- K: Small water-soaked spots on green fruit;
  S (6/6): Small water-soaked spots on green fruit;
- K: the centre of the spots becomes irregular, light brown, sunken and scabby.
  S (8/8): the centre of the spots becomes irregular, light brown, sunken and scabby.

## bacterial_wilt - ACCEPTED, 2 kept
- K: Lower leaves drop before wilting.
  S (5/5): Lower leaves drop before wilting.
- K: White bacterial ooze comes out from cut ends.
  S (4/5): White bacterial ooze from cut ends.

## collar_rot - ACCEPTED, 5 kept
- K: Mustard-like sclerotium appears later.
  S (4/5): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: Plants collapse soon after infection.
  S (4/4): Sometime plants collapse soon after infection.
- K: Use crop rotation with cereals, corn, sorghum, and millets.
  S (6/6): Use crop rotation with cereals, corn, sorghum and millets.
- K: Remove all weeds from field.
  S (3/3): Remove all the weeds from field.
- K: Avoid using infested farmyard manure, soil crop debris, and compost.
  S (8/9): Avoid use of infested farmyard manure, soil crop debris and compost in the field.

## damping_off - ACCEPTED, 2 kept
- K: Seedlings rot completely.
  S (2/2): Pre-emergence phase: Complete rotting of seedlings.
- K: Seedlings fall over or collapse.
  S (3/4): Seedlings topple over or collapse.

## early_blight - ACCEPTED, 8 kept
- K: Black spots with concentric rings in a bull's eye pattern with a yellow margin.
  S (6/7): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Fruit gets infected through the calyx or stem attachment;
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: black concentric rings on fruits.
  S (2/3): brown concentric rings on fruits.
- K: Irregular leaf spots mostly appear from the marginal portion of leaves.
  S (7/7): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: In many tomato cultivars, the symptoms are V-shaped and progress towards the midrib.
  S (7/7): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: These lesions are having prominent yellowing on their outer margin due to a host-specific toxin produced by the pathogen.
  S (11/11): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Mostly disease appears in the vegetative phase of the plant growth before flowering.
  S (7/7): Mostly disease appears in vegetative phase of plant growth before flowering.
- K: Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.

## fruit_rots - ACCEPTED, 6 kept
- K: Rhizoctonia fruit rot is the most serious disease of kharif tomato.
  S (4/4): Rhizoctonia fruit rot is most serious disease of kharif tomato.
- K: Symptoms appear as rhythmic rotting of fruits coming with the soil contact.
  S (8/8): Symptoms appear as rhythmic rotting of fruits coming with the soil contact.
- K: Rotting is followed by cracking and fungal growth over it.
  S (6/6): Rotting is immediately followed by cracking and fungal growth over it.
- K: Lower portion of fruits are usually infected which come into contact with the soil.
  S (6/8): Generally lower portion of fruits are infected which are coming in soil contact.
- K: To prevent the disease, keep the fruits off the soil by staking the plants.
  S (3/4): Avoid the contact of fruit from soil by staking of plant.
- K: Ensure proper drainage in the field.
  S (3/4): Provide proper drainage in the field.

## fusarium_wilt - ACCEPTED, 4 kept
- K: Younger leaves die in succession.
  S (3/3): Younger leaves die in succession.
- K: Petiole and leaves droop and wilt.
  S (4/4): Petiole and leaves droop and wilt.
- K: Browning of vascular system.
  S (3/3): Browning of vascular system.
- K: Entire plant wilt and die.
  S (2/2): Entire plant wilt and die.

## grey_leaf_spot - ACCEPTED, 4 kept
- K: Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
  S (14/14): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: Sometimes clear narrow yellow halo is visible around the spots.
  S (8/8): Sometimes clear narrow yellow halo is visible around the spots.
- K: Usually these spots are isolated but in later stage they coalesce to each other.
  S (8/8): Usually these spots are isolated but in later stage they coalesce to each other.
- K: Severely infected older leaves blight and fall down.
  S (7/7): Severely infected older leaves blight and fall down.

## healthy - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## helicoverpa_fruit_borer - ACCEPTED, 5 kept
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

## late_blight - ACCEPTED, 4 kept
- K: Black lesions on leaves and stems, expand rapidly, and the entire leaf becomes necrotic.
  S (7/9): Lesions expand rapidly and the entire leaf becomes necrotic.
- K: White sporulation on leaves.
  S (3/3): White sporulation on leaves.
- K: Dark brown lesions on fruit;
  S (4/4): Dark brown lesions on fruit;
- K: soft rot and disintegration of fruits.
  S (3/3): soft rot and disintegration of fruits.

## mites - ACCEPTED, 3 kept
- K: Affected leaves turn reddish-brown and bronzy.
  S (5/6): Affected leaves become reddish brown and bronzy.
- K: Severe infestation leaves silken webbing on the leaves, wither, and dry.
  S (6/6): Severe infestation larvae silken webbing on the leaves, wither and dry.
- K: Flower and fruit formation are affected.
  S (4/4): Flower and fruit formation affected.

## powdery_mildew - ACCEPTED, 4 kept
- K: Yellow blotches with a yellow halo appear on leaves.
  S (5/5): Irregular, bright yellow blotches with yellow halo appear on leaves.
- K: White spores are abundant in the infected area.
  S (5/5): Abundant white sporulation in the infected area of leaves.
- K: Plant leaves early and use sprinkler irrigation.
  S (3/4): Adopt early planting, sprinkler irrigation.
- K: Remove and destroy infected plants to prevent the disease.
  S (3/4): Immediately remove and destroy them to help prevent the disease from spreading.

## pseudocercospora_leaf_blight - ACCEPTED, 2 kept
- K: Leaves will soon fall off after infection.
  S (4/5): Leaf defoliate soon after infection.
- K: Burn the infected leaves.
  S (3/3): Collect and burn the infected leaves.

## root_knot_nematode - ACCEPTED, 9 kept
- K: Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
  S (12/12): Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
- K: This affects the uptake of nutrition and water and the plants show wilting during warmer part of the day.
  S (9/9): This affects the uptake of nutrition and water and the plants show wilting during warmer part of the day.
- K: This causes stunted plants with yellow foliage resulting in yield reduction.
  S (7/7): This causes stunted plants with yellow foliage resulting in yield reduction.
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

## septoria_leaf_spot - ACCEPTED, 4 kept
- K: Small, round to irregular spots with grey centre and dark margin on leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
- K: Stems and flowers are also affected.
  S (3/3): Stems and flowers are also affected.

## serpentine_leaf_miner - ACCEPTED, 2 kept
- K: Leaves with serpentine mines.
  S (3/3): Leaves with serpentine mines.
- K: Drying and dropping of leaves.
  S (3/3): Drying and dropping of leaves.

## spodoptera_tobacco_caterpillar - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## thrips - ACCEPTED, 3 kept
- K: Pre-mature dropping of flowers occurs.
  S (3/4): Pre-mature dropping of flowers.
- K: Thrips are the pests.
  S (2/2): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.
- K: Thrips suck the sap from tomato plants.
  S (2/2): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.

## tomato_mosaic - ACCEPTED, 2 kept
- K: Mottling on leaves with wilting of young leaves in sunny days.
  S (6/6): The disease is characterized by light and dark green mottling on the leaves often accompanied by wilting of young leaves in sunny days when plants first become infected.
- K: Wilting of young leaves in sunny days.
  S (5/5): The disease is characterized by light and dark green mottling on the leaves often accompanied by wilting of young leaves in sunny days when plants first become infected.

## tomato_spotted_wilt - ACCEPTED, 2 kept
- K: Growing tips may die-back and terminal branches may be streaked.
  S (6/6): Growing tips may die-back and terminal branches may be streaked.
- K: Use of healthy seedlings for transplanting.
  S (3/3): Use of healthy seedlings for transplanting.

## tuta_absoluta_pinworm - ACCEPTED, 2 kept
- K: Destroy the pinworm-infected plants and fruits.
  S (3/4): Collect and destroy the pinworm affected plants and fruits.
- K: Use healthy seedlings for transplanting.
  S (3/3): Use healthy seedlings for transplanting.

## whitefly - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## yellow_leaf_curl_virus - ACCEPTED, 6 kept
- K: Downward rolling and crinkling of the leaves;
  S (4/4): Downward rolling and crinkling of the leaves;
- K: older leaves become leathery and brittle.
  S (5/5): older leaves become leathery and brittle.
- K: Shortened internodes and more side branches give a bushy appearance.
  S (7/7): Shortened internodes and more side branches give a bushy appearance.
- K: The virus is spread by whiteflies (Bemisia tabaci).
  S (5/5): The virus is spread by whiteflies (Bemisia tabaci).
- K: Leaves show downward rolling, curling, twisting, and chlorosis.
  S (7/7): Leaves show downward rolling, curling, twisting and chlorosis.
- K: Plants show stunting, shortening of internodes, bushy appearance, no flowering, and fruiting later.
  S (9/9): Plants show stunting, shortening of internodes, bushy appearance, no flowering and fruiting at later stage of virus infection.

