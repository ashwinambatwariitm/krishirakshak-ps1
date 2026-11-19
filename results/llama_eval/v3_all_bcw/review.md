# Distortion review - v3_all_bcw

prompt=prompts/aman_v3_no_keyword_list.txt options=--block-cause-words

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## bacterial_canker - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## bacterial_speck - ACCEPTED, 2 kept
- K: The spots on the tomato leaf are necrotic, circular, and roughly circular.
  S (4/5): The spots are necrotic, circular to roughly circular.
- K: The tissue around the spot is still green.
  S (4/5): As the fruit approaches the pink stage, the tissue around the spot retains its green colour longer than normal.

## bacterial_spot - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## bacterial_wilt - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## collar_rot - ACCEPTED, 11 kept
- K: Soft tissue necrosis of bark of the stem near soil line
  S (8/8): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.
- K: White, cottony and silvery mycelial growth is clearly visible on the affected portion
  S (9/9): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: Progressive dropping and yellowing followed by wilting of the entire plant
  S (6/6): Progressive dropping and yellowing followed by wilting of the entire plant is observed.
- K: Sometime plants collapse soon after infection
  S (5/5): Sometime plants collapse soon after infection.
- K: The disease is soil borne where pathogen survives in the form of sclerotia
  S (7/7): The disease is soil borne where pathogen survives in the form of sclerotia.
- K: Use crop rotation with cereals, corn, sorghum and millets
  S (6/6): Use crop rotation with cereals, corn, sorghum and millets.
- K: Remove all the weeds from field
  S (3/3): Remove all the weeds from field.
- K: Avoid use of infested farmyard manure, soil crop debris and compost in the field
  S (9/9): Avoid use of infested farmyard manure, soil crop debris and compost in the field.
- K: Irrigate the soil in summer and plough the field to destroy germinating sclerotia
  S (8/8): Irrigate the soil in summer and plough the field to destroy germinating sclerotia.
- K: Avoid dense planting and maintain proper aeration near collar region
  S (9/9): Avoid dense planting and maintain proper aeration near collar region.
- K: Use Ammonium Nitrate as a fertilizer for nitrogen source
  S (5/5): Use Ammonium Nitrate as a fertilizer for nitrogen source.

## damping_off - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## early_blight - ACCEPTED, 12 kept
- K: Brown spots with concentric rings in a bull's eye pattern with yellow margin
  S (7/7): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Fruit gets infected through calyx or stem attachment
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: Brown concentric rings on fruits
  S (3/3): brown concentric rings on fruits.
- K: Irregular leaf spots mostly appear from marginal portion of leaves
  S (7/7): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: In many tomato cultivars, symptoms are V shaped and progress towards midrib
  S (7/7): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen
  S (11/11): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Mostly disease appears in vegetative phase of plant growth before flowering
  S (7/7): Mostly disease appears in vegetative phase of plant growth before flowering.
- K: This is a common disease of tomato occurring on the foliage at any stage of the growth
  S (5/5): This is a common disease of tomato occurring on the foliage at any stage of the growth.
- K: The fungus attacks the foliage causing characteristic leaf spots and blight
  S (7/7): The fungus attacks the foliage causing characteristic leaf spots and blight.
- K: Early blight is first observed on the plants as small, black lesions mostly on the older foliage
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Remove and destroy crop debris
  S (4/4): Remove and destroy crop debris.
- K: Follow crop rotation
  S (3/3): Follow crop rotation.

## fruit_rots - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## fusarium_wilt - ACCEPTED, 4 kept
- K: Clearing of veinlets
  S (2/2): Clearing of the veinlets and yellowing of the lower leaves.
- K: Petiole and leaves droop and wilt
  S (4/4): Petiole and leaves droop and wilt.
- K: Browning of vascular system
  S (3/3): Browning of vascular system.
- K: Younger leaves die in succession
  S (3/3): Younger leaves die in succession.

## grey_leaf_spot - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## healthy - ACCEPTED, 2 kept
- K: Collect and destroy any infected leaves, shoots, or fruits.
  S (6/6): Collect and destroy infected leaves, shoots and fruits.
- K: Conduct an agro-ecosystem analysis (AESA) every week, preferably before 9 a.m.
  S (7/9): Conduct agro-ecosystem analysis (AESA) weekly in the morning, preferably before 9 a.m.

## helicoverpa_fruit_borer - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## late_blight - ACCEPTED, 10 kept
- K: Black spots on the leaves and stems.
  S (4/4): Water-soaked black lesions on leaves and stems.
- K: The blight appears on the leaves as a light-pale green water-soaked dead area.
  S (10/10): Blight appears on foliage as light-pale green water soaked dead area.
- K: The spots are wet in the morning and dry in the sun.
  S (2/2): The lesions are wet in morning and dried, shriveled in daylight.
- K: A white fungus grows near the edge of the blight on the underside of the leaves.
  S (6/8): In moist and cloudy weather a downy white fungus develops near the outer margin of lesion on underside of the leaves.
- K: The fungus grows in moist and cloudy weather.
  S (4/5): In moist and cloudy weather a downy white fungus develops near the outer margin of lesion on underside of the leaves.
- K: Avoid planting tomatoes in the same field every year.
  S (7/7): Avoid planting tomatoes in the same field every year.
- K: Remove infected plant parts.
  S (3/3): Remove infected plant parts.
- K: Ensure enough space between plants and stake them.
  S (5/5): Ensure enough space between plants and stake them.
- K: Use black polythene mulch to keep the soil dry.
  S (3/4): Use black polythene mulch (30 micron).
- K: Improve field drainage and avoid overhead irrigation.
  S (6/6): Improve field drainage and avoid overhead irrigation.

## mites - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## powdery_mildew - rejected, 1 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:1

## pseudocercospora_leaf_blight - ACCEPTED, 2 kept
- K: Black sooty growth on the lower surface of the leaves.
  S (6/6): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: Collect and burn the infected leaves.
  S (4/4): Collect and burn the infected leaves.

## root_knot_nematode - ACCEPTED, 2 kept
- K: Use resistant varieties of tomatoes.
  S (3/3): Tolerant/resistant varieties for root knot nematode: Pusa-120, Pusa Hybrid-2, Pusa Hybrid-4, Arka Vardan, Hisar Lalit, TNAU Tomato Hybrid Co3.
- K: Use crop rotation with marigold to control nematodes.
  S (4/5): Crop rotation: Marigold, Chrysanthemum spp., Sesbania spp., Crotalaria spp., Gaillardia sp, castor bean and Desmodium spp., (parasitic nematodes).

## septoria_leaf_spot - ACCEPTED, 6 kept
- K: Small, round to irregular spots with grey centre and dark margin on leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Small spots with a grey centre and dark margins on leaves.
  S (7/7): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
- K: Spots coalesce and leaves are blighted.
  S (4/4): Spots coalesce and leaves are blighted.
- K: Removal and destruction of the affected plant parts.
  S (4/4): Removal and destruction of the affected plant parts.

## serpentine_leaf_miner - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## spodoptera_tobacco_caterpillar - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## thrips - ACCEPTED, 2 kept
- K: Silvery streaks on the leaf surface.
  S (4/4): Silvery streaks on leaf surface.
- K: Thrips sucking pests of tomatoes.
  S (4/4): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.

## tomato_mosaic - ACCEPTED, 2 kept
- K: The spots are often accompanied by wilting of young leaves.
  S (5/6): The disease is characterized by light and dark green mottling on the leaves often accompanied by wilting of young leaves in sunny days when plants first become infected.
- K: The affected plant looks stunted, pale, and spindly.
  S (4/5): The affected plant appears stunted, pale green and spindly.

## tomato_spotted_wilt - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## tuta_absoluta_pinworm - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## whitefly - ACCEPTED, 20 kept
- K: Whitefly is a well-known
  S (3/3): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: Vector of tomato leaf curl disease.
  S (3/3): Vector of tomato leaf curl disease.
- K: It has piercing and
  S (1/1): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Sucking mouthpart.
  S (2/2): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Both nymphs and
  S (2/2): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Adults feed on lower surface.
  S (4/4): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Causing deformation of
  S (2/2): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Young leaves.
  S (2/2): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Whiteflies also
  S (1/1): Whiteflies also excrete honeydew, causing sooty mold.
- K: Excrete honeydew.
  S (2/2): Whiteflies also excrete honeydew, causing sooty mold.
- K: Causing sooty
  S (2/2): Whiteflies also excrete honeydew, causing sooty mold.
- K: Mold.
  S (1/1): Whiteflies also excrete honeydew, causing sooty mold.
- K: Remove alternate
  S (2/2): Remove alternate weed host Abutilon indicum.
- K: Weed host Abutilon indicum.
  S (4/4): Remove alternate weed host Abutilon indicum.
- K: Uproot and destroy
  S (2/2): Uproot and destroy the diseased leaf curl plants.
- K: Diseased leaf curl plants.
  S (3/3): Uproot and destroy the diseased leaf curl plants.
- K: Use nitrogen
  S (1/1): Use nitrogen and irrigation judiciously.
- K: And irrigation judiciously.
  S (2/2): Use nitrogen and irrigation judiciously.
- K: Raise nurseries
  S (2/2): Raise nurseries in seedling trays under nylon nets or polyhouses.
- K: In seedling trays under nylon nets or polyhouses.
  S (6/6): Raise nurseries in seedling trays under nylon nets or polyhouses.

## yellow_leaf_curl_virus - ACCEPTED, 2 kept
- K: The tomato leaf is curled and the leaves are rolled down.
  S (3/4): Leaves show downward rolling, curling, twisting and chlorosis.
- K: The leaves are curled and the leaves are rolled down.
  S (3/4): Leaves show downward rolling, curling, twisting and chlorosis.

