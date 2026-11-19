# Distortion review - baseline_all_bcw

prompt=built-in options=--block-cause-words

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - ACCEPTED, 3 kept
- K: Aphids are sucking pests of tomato.
  S (3/3): Aphids (Myzus persicae, Aphis gossypii) are sucking pests of tomato.
- K: Install yellow sticky traps @ 4-5/acre.
  S (5/5): Install yellow sticky traps @ 4-5/acre.
- K: Use nitrogen fertilizer judiciously.
  S (3/3): Use nitrogen fertilizer judiciously.

## bacterial_canker - rejected, 0 kept (refused first, retry answer)
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## bacterial_speck - ACCEPTED, 4 kept (refused first, retry answer)
- K: The spots are necrotic, circular to roughly circular.
  S (4/4): The spots are necrotic, circular to roughly circular.
- K: Summer ploughing to desicitate the bacteria and host.
  S (4/5): Summer ploughing to desiccate the bacteria and host.
- K: Seed should be collected from disease free plants.
  S (3/3): Seed should be collected from disease free plants.
- K: The seeds should be collected from healthy plants that are free from the disease.
  S (3/4): Seed should be collected from disease free plants.

## bacterial_spot - ACCEPTED, 2 kept
- K: The symptoms of the disease are small, brown, water-soaked, circular spots with a yellow halo on the leaves.
  S (9/10): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: The disease is characterized by small, brown, water-soaked, circular spots with a yellow halo on the leaves.
  S (9/10): Small, brown, water-soaked, circular spots with yellow halo on leaves;

## bacterial_wilt - rejected, 0 kept (refused first, retry answer)
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## collar_rot - ACCEPTED, 3 kept
- K: The first symptom of the disease is soft tissue necrosis of the stem bark near the soil line.
  S (9/9): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.
- K: The disease is characterized by the presence of white, cottony, and silvery mycelial growth on the affected portion.
  S (7/9): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: The disease is not spread through the use of infested farmyard manure, soil crop debris, and compost in the field.
  S (8/10): Avoid use of infested farmyard manure, soil crop debris and compost in the field.

## damping_off - ACCEPTED, 2 kept
- K: Damping off occurs when the seedlings are killed before they reach the soil surface.
  S (6/8): In the pre-emergence the phase the seedlings are killed just before they reach the soil surface.
- K: Damping off occurs when the infected tissues become soft and water soaked.
  S (6/8): Post-emergence phase: Infected tissues become soft and water soaked.

## early_blight - ACCEPTED, 5 kept
- K: Brown spots with concentric rings in a bull's eye pattern with yellow margin on the photographed leaf.
  S (7/9): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: The fungus attacks the foliage, causing characteristic leaf spots and blight.
  S (7/7): The fungus attacks the foliage causing characteristic leaf spots and blight.
- K: Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
  S (9/9): Early blight is first observed on the plants as small, black lesions mostly on the older foliage.
- K: Remove and destroy crop debris.
  S (4/4): Remove and destroy crop debris.
- K: Follow crop rotation.
  S (3/3): Follow crop rotation.

## fruit_rots - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## fusarium_wilt - ACCEPTED, 3 kept
- K: Clearing of the veinlets on the photographed leaf is the first symptom of the disease.
  S (4/5): The first symptom of the disease is clearing of the veinlets and chlorosis of the leaves.
- K: The first symptom of the disease is clearing of the veinlets and chlorosis of the leaves.
  S (5/5): The first symptom of the disease is clearing of the veinlets and chlorosis of the leaves.
- K: The first symptom of the disease is clearing of the veinlets and dropping of petioles.
  S (5/5): In young plants, symptom consists of clearing of veinlet and dropping of petioles.

## grey_leaf_spot - rejected, 1 kept (refused first, retry answer)
Reasons: too_few_grounded_sentences:1

## healthy - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## helicoverpa_fruit_borer - ACCEPTED, 9 kept
- K: Young larvae feed on tender foliage.
  S (5/5): Young larvae feed on tender foliage.
- K: Mature larvae bore circular holes.
  S (5/5): Mature larvae bore circular holes.
- K: Thrust only a part of its body into fruit and eat the inner content.
  S (7/7): Thrust only a part of its body into fruit and eat the inner content.
- K: Eggs hatch in about 3-4 days.
  S (3/3): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: First instars larvae initially feed on the leaves and migrate to the developing green fruit later.
  S (10/10): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: The larvae bore into the fruits with the posterior end outside the hole.
  S (6/6): The larvae bore into the fruits with the posterior end outside the hole.
- K: Young larva feeds on the leaves for some time and then attacks fruits.
  S (7/7): Young larva feeds on the leaves for some time and then attacks fruits.
- K: Internal tissues are eaten severely and completely hollowed out.
  S (6/6): Internal tissues are eaten severely and completely hollowed out.
- K: While feeding the caterpillar thrust its head inside leaving the rest of the body outside.
  S (9/9): While feeding the caterpillar thrust its head inside leaving the rest of the body outside.

## late_blight - ACCEPTED, 4 kept
- K: The disease is a black rot on tomato leaves.
  S (2/2): Water-soaked black lesions on leaves and stems.
- K: The disease is killing the entire leaf.
  S (3/3): It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.
- K: The disease is spreading through the air.
  S (2/2): Spreads through tiny air-borne spores and thrives in wet, humid conditions (15-18 degree C, humidity above 90%).
- K: The disease is killing the entire plant.
  S (2/2): It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.

## mites - ACCEPTED, 2 kept
- K: Severe infestation larvae silken webbing on the leaves, wither and dry.
  S (7/7): Severe infestation larvae silken webbing on the leaves, wither and dry.
- K: Affected leaves become reddish brown and bronzy.
  S (6/6): Affected leaves become reddish brown and bronzy.

## powdery_mildew - rejected, 0 kept (refused first, retry answer)
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## pseudocercospora_leaf_blight - rejected, 1 kept (refused first, retry answer)
Reasons: too_few_grounded_sentences:1

## root_knot_nematode - ACCEPTED, 3 kept
- K: Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
  S (12/12): Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
- K: Infected plants in patches in the field.
  S (3/3): Infected plants in patches in the field.
- K: Infected roots become knobby and knotty.
  S (5/5): Infected roots become knobby and knotty.

## septoria_leaf_spot - ACCEPTED, 4 kept
- K: Small, round to irregular spots with grey centre and dark margin on tomato leaves.
  S (9/9): Small, round to irregular spots with grey centre and dark margin on leaves.
- K: Spots coalesce and leaves are blighted.
  S (4/4): Spots coalesce and leaves are blighted.
- K: Complete defoliation of affected leaves.
  S (4/4): Complete defoliation of affected leaves.
- K: Removal and destruction of the affected plant parts.
  S (4/4): Removal and destruction of the affected plant parts.

## serpentine_leaf_miner - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## spodoptera_tobacco_caterpillar - ACCEPTED, 10 kept
- K: Young larva scrap leaves on ventral surface.
  S (6/6): Young larva scrap leaves on ventral surface.
- K: Grownups defoliate crops.
  S (3/3): Grownups defoliate crops.
- K: This is a minor pest under open conditions.
  S (5/5): This is a minor pest under open conditions and assumes severe form under protected cultivation particularly in ill managed playhouses.
- K: Assumes severe form under protected cultivation.
  S (6/6): This is a minor pest under open conditions and assumes severe form under protected cultivation particularly in ill managed playhouses.
- K: Eggs are laid in clusters on foliage.
  S (4/4): Eggs are laid in clusters on foliage.
- K: Young larvae feed gregariously on leaves.
  S (5/5): Young larvae feed gregariously on leaves.
- K: Mature larvae, migrate and cause extensive damage to leaves and fruits.
  S (8/8): Mature larvae, migrate and cause extensive damage to leaves and fruits.
- K: They hide in soil and crop debris during the day time.
  S (6/6): They hide in soil and crop debris during the day time.
- K: In early stages, the caterpillars are gregarious and scrape the chlorophyll content of leaf lamina.
  S (9/9): In early stages, the caterpillars are gregarious and scrape the chlorophyll content of leaf lamina giving it a papery white appearance.
- K: Later they become voracious feeders making irregular holes on the leaves.
  S (8/8): Later they become voracious feeders making irregular holes on the leaves.

## thrips - ACCEPTED, 5 kept
- K: Silvery streaks on leaf surface.
  S (4/4): Silvery streaks on leaf surface.
- K: Pre-mature dropping of flowers.
  S (3/3): Pre-mature dropping of flowers.
- K: Bud necrosis.
  S (1/1): Bud necrosis.
- K: Vector of tomato spotted wilt virus.
  S (4/4): Vector of tomato spotted wilt virus.
- K: Thrips are sucking pests of tomato.
  S (3/3): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.

## tomato_mosaic - rejected, 0 kept (refused first, retry answer)
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## tomato_spotted_wilt - ACCEPTED, 3 kept
- K: Symptoms vary among hosts and in a single host species.
  S (6/6): Symptoms vary among hosts and in a single host species.
- K: Affected plants may have a one sided growth habit or may be entirely stunted and have drooping leaves.
  S (8/8): Affected plants may have a one sided growth habit or may be entirely stunted and have drooping leaves, suggesting a wilt.
- K: Severe stunting.
  S (2/2): Severe stunting.

## tuta_absoluta_pinworm - rejected, 0 kept (refused first, retry answer)
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## whitefly - ACCEPTED, 13 kept
- K: - Chlorotic spots
  S (2/2): Chlorotic spots.
- K: - Yellowing
  S (1/1): Yellowing.
- K: - Downward curling and drying of leaves
  S (4/4): Downward curling and drying of leaves.
- K: - Vector of tomato leaf curl disease
  S (3/3): Vector of tomato leaf curl disease.
- K: The whitefly is a well-known vector that transmits:
  S (5/5): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: - Tomato leaf curl virus
  S (3/3): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: - Both nymphs and adults feed on lower surface of the leaves
  S (7/7): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: - Deformation of young leaves
  S (3/3): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: - Whiteflies also excrete honeydew, causing:
  S (4/4): Whiteflies also excrete honeydew, causing sooty mold.
- K: - Sooty mold
  S (2/2): Whiteflies also excrete honeydew, causing sooty mold.
- K: - Remove alternate weed host Abutilon indicum
  S (6/6): Remove alternate weed host Abutilon indicum.
- K: - Uproot and destroy the diseased leaf curl plants
  S (5/5): Uproot and destroy the diseased leaf curl plants.
- K: - Use nitrogen and irrigation judiciously
  S (3/3): Use nitrogen and irrigation judiciously.

## yellow_leaf_curl_virus - ACCEPTED, 7 kept
- K: Severe stunting of plants.
  S (2/2): Severe stunting of plants.
- K: Disease appears in severe forms during the month of September to November.
  S (7/7): Disease appear in severe forms during the month of September to November.
- K: Leaves show downward rolling, curling, twisting, and chlorosis.
  S (7/7): Leaves show downward rolling, curling, twisting and chlorosis.
- K: Plants show stunting, shortening of internodes, bushy appearance, no flowering, and fruiting at later stage of virus infection.
  S (12/12): Plants show stunting, shortening of internodes, bushy appearance, no flowering and fruiting at later stage of virus infection.
- K: Leaf curl disease is characterized by severe stunting of the plants with downward rolling and crinkling of the leaves.
  S (8/8): Leaf curl disease is characterized by severe stunting of the plants with downward rolling and crinkling of the leaves.
- K: Raise the nursery under a net of sufficient mesh size to keep out whiteflies.
  S (7/7): Raise the nursery under a net of sufficient mesh size to keep out whiteflies.
- K: Select seed from disease-free healthy plants.
  S (4/4): Select seed from disease-free healthy plants.

