# Distortion review - lora_v8_all

prompt=prompts/aman_v8_no_numbering.txt options=--llama-pte models/llama3_2_1b_krishirakshak_lora_8da4w.pte

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - ACCEPTED, 2 kept
- K: Aphids are sucking pests of tomatoes.
  S (4/4): Aphids (Myzus persicae, Aphis gossypii) are sucking pests of tomato.
- K: Use nitrogen fertilizer judiciously.
  S (3/3): Use nitrogen fertilizer judiciously.

## bacterial_canker - ACCEPTED, 5 kept
- K: Small, water soaked spots with white halo on fruits.
  S (7/7): Small, water soaked spots with white halo on fruits.
- K: Centre of spots become slightly raised, tan coloured and rough.
  S (7/7): Centre of spots become slightly raised, tan coloured and rough.
- K: Cankers develop and form cracks;
  S (4/4): Cankers develop and form cracks;
- K: slimy bacterial ooze through cracks.
  S (5/5): slimy bacterial ooze through cracks.
- K: Vascular discolouration.
  S (2/2): Vascular discolouration.

## bacterial_speck - ACCEPTED, 2 kept
- K: Small black spots appear on leaf, stem, and parts that hold the leaf to the plant.
  S (6/8): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: Irregular, elongated lesions appear on stem.
  S (5/5): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.

## bacterial_spot - ACCEPTED, 4 kept
- K: Small, brown, water-soaked, circular spots with a yellow halo appear on leaves.
  S (9/10): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: Older leaves fall off.
  S (3/3): older leaves fall.
- K: Small water-soaked spots appear on green fruit.
  S (6/7): Small water-soaked spots on green fruit;
- K: The centre of the spots becomes irregular, light brown, sunken, and scabby.
  S (8/8): the centre of the spots becomes irregular, light brown, sunken and scabby.

## bacterial_wilt - ACCEPTED, 2 kept
- K: White bacterial ooze comes from cut ends.
  S (4/5): White bacterial ooze from cut ends.
- K: Lower leaves may drop before wilting.
  S (5/5): Lower leaves drop before wilting.

## collar_rot - ACCEPTED, 4 kept
- K: Soft tissue necrosis of the stem bark near the soil line is the first sign of the disease.
  S (8/9): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.
- K: A white, cottony, and silvery mycelial growth is visible on the affected area.
  S (7/8): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: Later, a white to light brown mustard-like sclerotium appears on the same area.
  S (8/10): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: The disease is soil-borne and the pathogen survives in the form of sclerotia.
  S (6/6): The disease is soil borne where pathogen survives in the form of sclerotia.

## damping_off - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## early_blight - ACCEPTED, 5 kept
- K: Brown spots with concentric rings in a bull's eye pattern with a yellow margin.
  S (7/7): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Fruit gets infected through the calyx or stem attachment.
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: Lesions are V-shaped and progress towards the midrib.
  S (4/5): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: These lesions have prominent yellowing on their outer margin due to a host-specific toxin produced by the pathogen.
  S (10/10): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Disease appears in the vegetative phase of the plant before flowering.
  S (5/5): Mostly disease appears in vegetative phase of plant growth before flowering.

## fruit_rots - ACCEPTED, 6 kept
- K: Rhizoctonia fruit rot is the most serious disease of kharif tomatoes.
  S (5/5): Rhizoctonia fruit rot is most serious disease of kharif tomato.
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

## fusarium_wilt - ACCEPTED, 3 kept
- K: Younger leaves die one by one.
  S (2/2): Younger leaves die in succession.
- K: Petiole and leaves droop and wilt.
  S (4/4): Petiole and leaves droop and wilt.
- K: Browning of vascular system.
  S (3/3): Browning of vascular system.

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
- K: Rotate with non-host crops like cereals and legumes.
  S (5/6): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.
- K: Do not plant tomato with chilli or brinjal.
  S (2/2): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.

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

## late_blight - ACCEPTED, 5 kept
- K: Water-soaked black lesions appear on leaves and stems.
  S (6/7): Water-soaked black lesions on leaves and stems.
- K: Lesions expand rapidly, and the entire leaf becomes necrotic.
  S (7/7): Lesions expand rapidly and the entire leaf becomes necrotic.
- K: White sporulation appears on leaves.
  S (3/4): White sporulation on leaves.
- K: Dark brown lesions appear on fruit.
  S (4/5): Dark brown lesions on fruit;
- K: Soft rot and disintegration of fruits occur.
  S (3/4): soft rot and disintegration of fruits.

## mites - ACCEPTED, 6 kept
- K: Severe infestation leaves silken webbing on the leaves, wither and dry.
  S (6/6): Severe infestation larvae silken webbing on the leaves, wither and dry.
- K: Flower and fruit formation are affected.
  S (4/4): Flower and fruit formation affected.
- K: Red spider mites thrive in high temperatures, dry weather, and protected conditions.
  S (7/8): Red spider mites thrive under high temperature, dry weather and are more serious under protected conditions.
- K: They are found on the lower surface of older leaves.
  S (5/5): They are generally found on the lower surface of older leaves.
- K: When infestation is severe, they attack all parts of the plant.
  S (3/4): However, when the infestation is very high they attack all parts of the plant and are observed in colonies covered by white-silky webs.
- K: Affected leaves turn reddish brown and bronzy.
  S (5/6): Affected leaves become reddish brown and bronzy.

## powdery_mildew - ACCEPTED, 5 kept
- K: Yellow blotches with a yellow halo appear on leaves.
  S (5/5): Irregular, bright yellow blotches with yellow halo appear on leaves.
- K: White spores are abundant in the infected area.
  S (5/5): Abundant white sporulation in the infected area of leaves.
- K: Plant tomatoes early and use sprinkler irrigation.
  S (3/4): Adopt early planting, sprinkler irrigation.
- K: Leave lower leaves clipped and mulched.
  S (4/5): Periodic clipping of lower leaves and mulching.
- K: Use organic mulch around the plants.
  S (3/3): Organic mulch added around the plants will protect roots while preventing fungal spores from splashing onto the plant.

## pseudocercospora_leaf_blight - ACCEPTED, 4 kept
- K: Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
  S (9/9): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: Symptoms are only observed on the leaves.
  S (4/4): Symptoms are only observed on the leaves.
- K: Leaf will soon fall off after infection.
  S (4/5): Leaf defoliate soon after infection.
- K: No discoloration was observed on the corresponding upper side of the leaves.
  S (6/6): No discoloration was observed on the corresponding upper side of the leaves.

## root_knot_nematode - ACCEPTED, 9 kept
- K: Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
  S (12/12): Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
- K: This affects the uptake of nutrition and water and the plants show wilting during the warmer part of the day.
  S (9/9): This affects the uptake of nutrition and water and the plants show wilting during warmer part of the day.
- K: This causes stunted plants with yellow foliage resulting in yield reduction.
  S (7/7): This causes stunted plants with yellow foliage resulting in yield reduction.
- K: Infected plants in patches in the field.
  S (3/3): Infected plants in patches in the field.
- K: Formation of galls on the host root system is the primary symptom.
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
- K: Small, round to irregular spots with a grey centre and dark margin on leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
- K: Stems and flowers are also affected.
  S (3/3): Stems and flowers are also affected.

## serpentine_leaf_miner - ACCEPTED, 2 kept
- K: Leaves with serpentine mines dry and drop off.
  S (3/4): Leaves with serpentine mines.
- K: The tiny, metallic fly punctures the leaf and feeds on the sap.
  S (5/5): The tiny, metallic fly punctures the leaf lamina and feeds on the oozing sap.

## spodoptera_tobacco_caterpillar - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## thrips - ACCEPTED, 3 kept
- K: Silvery streaks appear on the leaf surface.
  S (4/5): Silvery streaks on leaf surface.
- K: Pre-mature dropping of flowers occurs.
  S (3/4): Pre-mature dropping of flowers.
- K: Thrips are the pests.
  S (2/2): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.

## tomato_mosaic - ACCEPTED, 2 kept
- K: Mottling on leaves with wilting of young leaves in sunny days.
  S (6/6): The disease is characterized by light and dark green mottling on the leaves often accompanied by wilting of young leaves in sunny days when plants first become infected.
- K: Wilting of young leaves in sunny days.
  S (5/5): The disease is characterized by light and dark green mottling on the leaves often accompanied by wilting of young leaves in sunny days when plants first become infected.

## tomato_spotted_wilt - ACCEPTED, 5 kept
- K: Severe stunting.
  S (2/2): Severe stunting.
- K: Chlorotic or necrotic rings on leaves.
  S (4/4): Chlorotic or necrotic rings on leaves.
- K: Thickening of veins and bronzing of young leaves.
  S (5/5): Thickening of veins and bronzing of young leaves.
- K: Growing tips may die-back and terminal branches may be streaked.
  S (6/6): Growing tips may die-back and terminal branches may be streaked.
- K: Use of healthy seedlings for transplanting.
  S (3/3): Use of healthy seedlings for transplanting.

## tuta_absoluta_pinworm - ACCEPTED, 2 kept
- K: Destroy the plants and fruits that are infested with the pinworm.
  S (3/4): Collect and destroy the pinworm affected plants and fruits.
- K: Use healthy seedlings when transplanting tomatoes.
  S (3/4): Use healthy seedlings for transplanting.

## whitefly - ACCEPTED, 8 kept
- K: Downward curling and drying of leaves happen on tomato leaves.
  S (4/5): Downward curling and drying of leaves.
- K: Whitefly is a well-known vector that transmits tomato leaf curl virus.
  S (8/8): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: Whiteflies have piercing and sucking mouthparts and both nymphs and adults feed on the lower surface of the leaves, causing deformation of young leaves.
  S (13/14): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Whiteflies also excrete honeydew, which causes sooty mold.
  S (6/6): Whiteflies also excrete honeydew, causing sooty mold.
- K: Remove Abutilon indicum from the area.
  S (3/4): Remove alternate weed host Abutilon indicum.
- K: Uproot and destroy the diseased leaf curl plants.
  S (5/5): Uproot and destroy the diseased leaf curl plants.
- K: Use nitrogen and irrigation judiciously.
  S (3/3): Use nitrogen and irrigation judiciously.
- K: Raise nurseries in seedling trays under nylon nets or polyhouses.
  S (8/8): Raise nurseries in seedling trays under nylon nets or polyhouses.

## yellow_leaf_curl_virus - ACCEPTED, 5 kept
- K: Severe stunting of plants.
  S (2/2): Severe stunting of plants.
- K: Downward rolling and crinkling of the leaves;
  S (4/4): Downward rolling and crinkling of the leaves;
- K: older leaves become leathery and brittle.
  S (5/5): older leaves become leathery and brittle.
- K: Shortened internodes and more side branches give a bushy appearance.
  S (7/7): Shortened internodes and more side branches give a bushy appearance.
- K: The virus is spread by whiteflies (Bemisia tabaci).
  S (5/5): The virus is spread by whiteflies (Bemisia tabaci).

