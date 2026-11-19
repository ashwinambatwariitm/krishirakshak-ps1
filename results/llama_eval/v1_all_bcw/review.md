# Distortion review - v1_all_bcw

prompt=prompts/aman_v1_per_sentence.txt options=--block-cause-words

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## bacterial_canker - ACCEPTED, 18 kept
- K: Seedlings, leaves, stem and fruits
  S (4/4): Seedlings, leaves, stem and fruits are affected.
- K: Spots on leaves, stems and fruits
  S (4/4): Spots on leaves, stems and fruits.
- K: are affected.
  S (1/1): Seedlings, leaves, stem and fruits are affected.
- K: Small, water soaked spots
  S (4/4): Small, water soaked spots with white halo on fruits.
- K: with white halo on fruits.
  S (3/3): Small, water soaked spots with white halo on fruits.
- K: Centre of spots become slightly
  S (4/4): Centre of spots become slightly raised, tan coloured and rough.
- K: raised, tan coloured and rough.
  S (3/3): Centre of spots become slightly raised, tan coloured and rough.
- K: Cankers develop and form
  S (3/3): Cankers develop and form cracks;
- K: cracks;
  S (1/1): Cankers develop and form cracks;
- K: slimy bacterial ooze
  S (3/3): slimy bacterial ooze through cracks.
- K: through cracks.
  S (2/2): slimy bacterial ooze through cracks.
- K: Vascular discolouration.
  S (2/2): Vascular discolouration.
- K: Disease appears as
  S (1/1): Disease appears as spots on leaves, stems and fruits and as wilting of leaves and shoots.
- K: spots on leaves, stems and
  S (3/3): Spots on leaves, stems and fruits.
- K: fruits and as wilting of
  S (2/2): Disease appears as spots on leaves, stems and fruits and as wilting of leaves and shoots.
- K: leaves and shoots.
  S (2/2): Wilting of leaves and shoots, streaks on stems and petioles.
- K: White blister like spots
  S (4/4): White blister like spots in the margins of leaves and turn brown.
- K: in the margins of leaves.
  S (2/2): White blister like spots in the margins of leaves and turn brown.

## bacterial_speck - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## bacterial_spot - ACCEPTED, 9 kept
- K: Small, brown, water-soaked, circular spots with yellow halo on leaves.
  S (9/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: Small water-soaked spots on green fruit.
  S (6/6): Small water-soaked spots on green fruit;
- K: The centre of the spots becomes irregular, light brown, sunken and scabby.
  S (8/8): the centre of the spots becomes irregular, light brown, sunken and scabby.
- K: Small, dark spots appear on leaflets and stems of seedlings.
  S (7/7): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: Numerous spots coalesce and cause severe burning of the leaves.
  S (7/7): Numerous spots coalesce and cause severe burning of the leaves.
- K: Prominent yellow halo is observed around the spot.
  S (6/6): Prominent yellow halo is observed around the spot.
- K: Infected leaves show small, brown, water-soaked, circular spots surrounded with yellowish halo.
  S (12/12): Infected leaves show small, brown, water soaked, circular spots surrounded with yellowish halo.
- K: On older plants the leaflet infection is mostly on older leaves and may cause serious defoliation.
  S (7/7): On older plants the leaflet infection is mostly on older leaves and may cause serious defoliation.
- K: Use disease-free seed.
  S (2/2): Use disease-free seed.

## bacterial_wilt - ACCEPTED, 6 kept
- K: Lower leaves drop before wilting.
  S (5/5): Lower leaves drop before wilting.
- K: Characteristic symptoms of bacterial wilt are the rapid and complete wilting of normal grown up plants.
  S (8/8): Characteristic symptoms of bacterial wilt are the rapid and complete wilting of normal grown up plants.
- K: Infected plant parts when cut and immersed in clear water, a white streak of bacterial ooze is seen coming out from cut ends.
  S (12/12): Infected plant parts when cut and immersed in clear water, a white streak of bacterial ooze is seen coming out from cut ends.
- K: Crop rotation.
  S (2/2): Crop rotation.
- K: Disease free seedlings.
  S (2/2): Disease free seedlings.
- K: Restriction of irrigation.
  S (2/2): Restriction of irrigation.

## collar_rot - ACCEPTED, 11 kept
- K: Soft tissue necrosis of bark
  S (4/4): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.
- K: White, cottony, and silvery mycelial growth
  S (5/5): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: White to light brown mustard like sclerotium
  S (6/6): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: Progressive dropping and yellowing
  S (3/3): Progressive dropping and yellowing followed by wilting of the entire plant is observed.
- K: Wilting of the entire plant
  S (2/2): Progressive dropping and yellowing followed by wilting of the entire plant is observed.
- K: Use crop rotation
  S (2/2): Use crop rotation with cereals, corn, sorghum and millets.
- K: Remove all weeds
  S (2/2): Remove all the weeds from field.
- K: Avoid use of infested farmyard manure
  S (4/4): Avoid use of infested farmyard manure, soil crop debris and compost in the field.
- K: Avoid dense planting
  S (3/3): Avoid dense planting and maintain proper aeration near collar region.
- K: Maintain proper aeration near collar region
  S (6/6): Avoid dense planting and maintain proper aeration near collar region.
- K: Use Ammonium Nitrate as a fertilizer
  S (3/3): Use Ammonium Nitrate as a fertilizer for nitrogen source.

## damping_off - ACCEPTED, 3 kept
- K: Prevent seedlings from rotting completely.
  S (3/4): Pre-emergence phase: Complete rotting of seedlings.
- K: Infect young, juvenile tissues of the collar.
  S (5/5): The post-emergence phase is characterized by the infection of the young, juvenile tissues of the collar at the ground level.
- K: Use raised beds of 15 cm height to dry grain.
  S (3/4): Use raised beds of 15 cm height.

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

## fruit_rots - ACCEPTED, 5 kept
- K: Fruit rot is most serious disease of kharif tomato.
  S (3/3): Rhizoctonia fruit rot is most serious disease of kharif tomato.
- K: Symptoms appear as rhythmic rotting of fruits coming with the soil contact.
  S (8/8): Symptoms appear as rhythmic rotting of fruits coming with the soil contact.
- K: Rotting is immediately followed by cracking and fungal growth over it.
  S (7/7): Rotting is immediately followed by cracking and fungal growth over it.
- K: Generally lower portion of fruits are infected which are coming in soil contact.
  S (8/8): Generally lower portion of fruits are infected which are coming in soil contact.
- K: Staking of plant to avoid fruit contact.
  S (4/4): Avoid the contact of fruit from soil by staking of plant.

## fusarium_wilt - ACCEPTED, 4 kept
- K: Clearing of veinlets
  S (2/2): Clearing of the veinlets and yellowing of the lower leaves.
- K: Petiole and leaves droop and wilt
  S (4/4): Petiole and leaves droop and wilt.
- K: Browning of vascular system
  S (3/3): Browning of vascular system.
- K: Younger leaves die in succession
  S (3/3): Younger leaves die in succession.

## grey_leaf_spot - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## healthy - ACCEPTED, 4 kept
- K: Conduct an agro-ecosystem analysis weekly.
  S (5/5): Conduct agro-ecosystem analysis (AESA) weekly in the morning, preferably before 9 a.m.
- K: Rotate with non-host crops such as cereals and legumes.
  S (5/5): rotate with non-host crops such as cereals and legumes, and do not follow tomato with chilli or brinjal.
- K: Use drip irrigation to reduce leaf wetness.
  S (5/5): Stake plants and use drip irrigation to reduce leaf wetness.
- K: Collect and destroy infected leaves, shoots, and fruits.
  S (6/6): Collect and destroy infected leaves, shoots and fruits.

## helicoverpa_fruit_borer - ACCEPTED, 13 kept
- K: Young larvae feed on tender foliage
  S (5/5): Young larvae feed on tender foliage.
- K: Mature larvae bore circular holes
  S (5/5): Mature larvae bore circular holes.
- K: Thrust only a part of its body into fruit
  S (5/5): Thrust only a part of its body into fruit and eat the inner content.
- K: Eggs hatch in about 3-4 days
  S (3/3): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: First instars larvae initially feed on the leaves
  S (5/5): Eggs hatch in about 3-4 days and the first instars larvae initially feed on the leaves and migrate to the developing green fruit later.
- K: Mature larvae bore into the fruits
  S (3/4): Mature larvae bore circular holes.
- K: Young larva feeds on the leaves
  S (4/4): Young larva feeds on the leaves for some time and then attacks fruits.
- K: Larvae bore into the fruits with the posterior end outside
  S (5/5): The larvae bore into the fruits with the posterior end outside the hole.
- K: Internal tissues are eaten severely
  S (4/4): Internal tissues are eaten severely and completely hollowed out.
- K: Internal tissues are eaten completely
  S (4/4): Internal tissues are eaten severely and completely hollowed out.
- K: Larvae feed on the leaves for some time
  S (3/4): Young larvae feed on tender foliage.
- K: Larvae feed on the leaves while feeding the caterpillar
  S (3/4): Young larvae feed on tender foliage.
- K: Grow simultaneously 40
  S (2/2): Grow simultaneously 40 days old American tall marigold and 25 days old tomato seedling at 1:16 rows.

## late_blight - ACCEPTED, 8 kept
- K: Water-soaked black lesions on leaves and stems.
  S (6/6): Water-soaked black lesions on leaves and stems.
- K: Lesions expand rapidly and the entire leaf becomes necrotic.
  S (7/7): Lesions expand rapidly and the entire leaf becomes necrotic.
- K: White sporulation on leaves.
  S (3/3): White sporulation on leaves.
- K: Dark brown lesions on fruit;
  S (4/4): Dark brown lesions on fruit;
- K: soft rot and disintegration of fruits.
  S (3/3): soft rot and disintegration of fruits.
- K: Blight appears on foliage as light-pale green water soaked dead area.
  S (10/10): Blight appears on foliage as light-pale green water soaked dead area.
- K: The lesions are wet in morning and dried, shriveled in daylight.
  S (5/5): The lesions are wet in morning and dried, shriveled in daylight.
- K: It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.
  S (9/9): It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection.

## mites - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## powdery_mildew - ACCEPTED, 10 kept
- K: Yellow blotches with yellow halo
  S (3/3): Irregular, bright yellow blotches with yellow halo appear on leaves.
- K: Abundant white sporulation
  S (3/3): Abundant white sporulation in the infected area of leaves.
- K: Field sanitation
  S (2/2): Field sanitation.
- K: Early planting
  S (2/2): Adopt early planting, sprinkler irrigation.
- K: Sprinkler irrigation
  S (2/2): Adopt early planting, sprinkler irrigation.
- K: Remove and destroy
  S (2/2): Immediately remove and destroy them to help prevent the disease from spreading.
- K: Proper plant spacing
  S (2/2): Proper plant spacing of about 3 feet apart to allow for proper air circulation, which helps the foliage dry faster.
- K: Lower leaves clipping
  S (3/3): Periodic clipping of lower leaves and mulching.
- K: Mulching
  S (1/1): Periodic clipping of lower leaves and mulching.
- K: Organic mulch
  S (2/2): Organic mulch added around the plants will protect roots while preventing fungal spores from splashing onto the plant.

## pseudocercospora_leaf_blight - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## root_knot_nematode - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## septoria_leaf_spot - ACCEPTED, 7 kept
- K: Spots join and leaves are blighted;
  S (4/4): Spots join and leaves are blighted;
- K: complete defoliation.
  S (2/2): complete defoliation.
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

## serpentine_leaf_miner - ACCEPTED, 2 kept
- K: Drying and dropping of leaves.
  S (3/3): Drying and dropping of leaves.
- K: Apply neem cake to furrows (open)/beds (polyhouse) every 25 days.
  S (8/9): Apply neem cake to furrows (open)/beds (polyhouse) @ 250 kg/ha at planting and repeat after 25 days.

## spodoptera_tobacco_caterpillar - ACCEPTED, 2 kept
- K: Young larva scrap leaves on ventral surface
  S (6/6): Young larva scrap leaves on ventral surface.
- K: Young caterpillars eat leaves on the surface of the leaf
  S (3/4): Young larva scrap leaves on ventral surface.

## thrips - ACCEPTED, 19 kept
- K: Thrips (Thrips tabaci, Frankliniella schultzei)
  S (4/4): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.
- K: are sucking pests of tomato.
  S (2/2): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.
- K: Silvery streaks on leaf
  S (3/3): Silvery streaks on leaf surface.
- K: surface.
  S (1/1): Silvery streaks on leaf surface.
- K: Pre-mature dropping
  S (2/2): Pre-mature dropping of flowers.
- K: of flowers.
  S (1/1): Pre-mature dropping of flowers.
- K: Bud necrosis.
  S (1/1): Bud necrosis.
- K: Vector of tomato spotted
  S (2/2): Vector of tomato spotted wilt virus.
- K: wilts virus.
  S (2/2): Vector of tomato spotted wilt virus.
- K: Install blue sticky
  S (3/3): Install blue sticky traps @ 10 traps/ha against thrips;
- K: traps @ 10 traps/ha
  S (1/1): Install blue sticky traps @ 10 traps/ha against thrips;
- K: against thrips;
  S (2/2): Install blue sticky traps @ 10 traps/ha against thrips;
- K: locally available
  S (2/2): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: empty tins painted
  S (3/3): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: blue and coated
  S (2/2): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: with grease,
  S (1/1): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: vaseline or
  S (1/1): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: castor oil
  S (1/1): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.
- K: used.
  S (1/1): locally available empty tins painted blue and coated with grease, vaseline or castor oil can also be used.

## tomato_mosaic - ACCEPTED, 6 kept
- K: Light and dark green mottling on leaves
  S (5/5): Light and dark green mottling on leaves.
- K: Leaflets distorted and puckered
  S (3/3): Leaflets distorted and puckered.
- K: Fern leaf symptoms
  S (3/3): Fern leaf symptoms.
- K: Stunted growth
  S (2/2): Stunted growth.
- K: Disease symptoms
  S (1/1): Fern leaf symptoms.
- K: Wilting of young leaves
  S (3/3): Wilting of young leaves.

## tomato_spotted_wilt - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## tuta_absoluta_pinworm - ACCEPTED, 2 kept
- K: leaves, stem, and pinholes on fruits
  S (4/4): Mining of leaves, stem and pinholes on fruits.
- K: mining of leaves, stem, and pinholes on fruits
  S (5/5): Mining of leaves, stem and pinholes on fruits.

## whitefly - ACCEPTED, 25 kept
- K: Chlorotic spots
  S (2/2): Chlorotic spots.
- K: Yellowing.
  S (1/1): Yellowing.
- K: Downward
  S (1/1): Downward curling and drying of leaves.
- K: Curling and drying of leaves.
  S (3/3): Downward curling and drying of leaves.
- K: Vector of tomato
  S (1/1): Vector of tomato leaf curl disease.
- K: Leaf curl disease.
  S (2/2): Downward curling and drying of leaves.
- K: Whitefly is
  S (1/1): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: A well-known vector.
  S (3/3): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: Which transmits
  S (1/1): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: Tomato leaf curl virus.
  S (3/3): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: Piercing and sucking
  S (2/2): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Mouthpart and
  S (1/1): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Both nymphs and adults
  S (3/3): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Feed on lower
  S (2/2): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Surface of the leaves
  S (2/2): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Causing deformation
  S (2/2): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Of young leaves.
  S (2/2): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: Whiteflies also
  S (1/1): Whiteflies also excrete honeydew, causing sooty mold.
- K: Excrete honeydew.
  S (2/2): Whiteflies also excrete honeydew, causing sooty mold.
- K: Causing sooty
  S (2/2): Whiteflies also excrete honeydew, causing sooty mold.
- K: Mold.
  S (1/1): Whiteflies also excrete honeydew, causing sooty mold.
- K: Remove
  S (1/1): Remove alternate weed host Abutilon indicum.
- K: Alternate weed
  S (2/2): Remove alternate weed host Abutilon indicum.
- K: Host Abutilon
  S (2/2): Remove alternate weed host Abutilon indicum.
- K: Indicum.
  S (1/1): Remove alternate weed host Abutilon indicum.

## yellow_leaf_curl_virus - ACCEPTED, 2 kept
- K: The tomato leaf is curled and the leaves are rolled downwards.
  S (4/4): Leaves show downward rolling, curling, twisting and chlorosis.
- K: The leaves are curled and the leaves are rolled downwards.
  S (4/4): Leaves show downward rolling, curling, twisting and chlorosis.

