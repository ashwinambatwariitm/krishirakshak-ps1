# Distortion review - v13_all

prompt=prompts/aman_v13_capital.txt options=

For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).

## aphids - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## bacterial_canker - ACCEPTED, 7 kept
- K: SEEDLINGS, LEAFS, STEM AND FRUITS ARE AFFECTED.
  S (5/5): Seedlings, leaves, stem and fruits are affected.
- K: SPOTS ON LEAFS, STEMS, AND FRUITS.
  S (4/4): Spots on leaves, stems and fruits.
- K: WHITE BLISTER LIKE SPOTS IN THE MARGINS OF LEAFS.
  S (6/6): White blister like spots in the margins of leaves and turn brown.
- K: SPOTS BECOME BROWN WITH AGE AND COALESCE.
  S (4/4): Spots become brown with age and coalesce, but leaves do not fall off.
- K: LEAFLET ON ONE SIDE OF RACHIS SHOWS WITHERING.
  S (5/5): Leaflets on one side of rachis show withering initially.
- K: CROP ROTATION WITH NON HOST CROPS IS RECOMMENDED.
  S (3/4): Crop rotation with non host crops.
- K: DISINFECTION OF TOOLS AND IMPLEMENTS IS RECOMMENDED.
  S (3/4): Disinfection of tools and implements.

## bacterial_speck - ACCEPTED, 5 kept
- K: A SPOT IS NECROTIC AND CIRCULAR TO RUBBISHLY CIRCULAR.
  S (3/4): The spots are necrotic, circular to roughly circular.
- K: B THE SPOT IS CIRCULAR TO RUBBISHLY CIRCULAR.
  S (2/3): The spots are necrotic, circular to roughly circular.
- K: C AS THE FRUIT APPROACHES THE PINK STAGE, THE TISSUE AROUND THE SPOT RETAINS ITS GREEN COLOR LONGER THAN NORMAL.
  S (11/12): As the fruit approaches the pink stage, the tissue around the spot retains its green colour longer than normal.
- K: D SMALL BLACK SPOTS APPEAR ON LEAF, PETIOLE, PEDICEL, AND PEDUNCLE.
  S (8/8): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.
- K: E WHILE IRREGULAR, ELONGATED LESIONS APPEAR ON STEM.
  S (5/5): Small black spots appear on leaf, petiole, pedicel, and peduncle while irregular, elongated lesions appear on stem.

## bacterial_spot - ACCEPTED, 4 kept
- K: A SMALL, BROWN, WATER-SOAKED, CIRCULAR SPOT ON THE LEAF OF A TOMATO PLANT IS A SYMPTOM OF BACTERIAL LEAF SPOT.
  S (7/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: THE SPOTS ARE SMALL, BROWN, WATER-SOAKED, CIRCULAR, AND HAVE A YELLOW HALO AROUND THEM.
  S (8/9): Small, brown, water-soaked, circular spots with yellow halo on leaves;
- K: A SMALL, DARK SPOT APPEARS ON THE LEAFLET AND STEM OF A SEEDLING PLANT.
  S (6/7): Small, dark spots appear on leaflets and stems of seedlings transplanted crop.
- K: NUMEROOUS SPOTS COALESCE AND CAUSE SEVERE BURNING OF THE LEAFS.
  S (6/7): Numerous spots coalesce and cause severe burning of the leaves.

## bacterial_wilt - ACCEPTED, 6 kept
- K: A Rapid and complete wilting of the plant.
  S (3/3): Rapid and complete wilting of plant.
- K: B Lower leaves drop before wilting.
  S (5/5): Lower leaves drop before wilting.
- K: C Yellow brown discolouration of tissues.
  S (4/4): Yellow brown discolouration of tissues.
- K: D White bacterial ooze from cut ends.
  S (4/4): White bacterial ooze from cut ends.
- K: E Characteristic symptoms of bacterial wilt are the rapid and complete wilting of normal grown up plants.
  S (8/8): Characteristic symptoms of bacterial wilt are the rapid and complete wilting of normal grown up plants.
- K: F Lower leaves may drop before wilting.
  S (5/5): Lower leaves drop before wilting.

## collar_rot - ACCEPTED, 5 kept
- K: THE FIRST SYMPTOM OF DISEASE IS OBSERVED AS SOFT TISSUE NECROSIS OF BARK OF THE STEM NEAR SOIL LINE.
  S (10/10): The first symptom of disease is observed as soft tissue necrosis of bark of the stem near soil line.
- K: WHITE, COTTONY, AND SILVER MYCELIAL GROWTH IS CLEARLY VISABLE ON THE AFFECTED PORTION.
  S (7/9): White, cottony and silvery mycelial growth is clearly visible on the affected portion.
- K: LATER ON, WHITE TO LIGHT BROWN MUSTARD-LIKE SCLEROTIUM IS OBSERVED ON THE SAME PORTION.
  S (10/10): Later on white to light brown mustard like sclerotium is observed on the same portion.
- K: PROGRESSIVE DROPPING AND YELLOWING FOLLOWED BY WILTING OF THE ENTIRE PLANT IS OBSERVED.
  S (7/7): Progressive dropping and yellowing followed by wilting of the entire plant is observed.
- K: SOMETIME PLANTS COLLAPSE SOON AFTER INFECTION.
  S (5/5): Sometime plants collapse soon after infection.

## damping_off - ACCEPTED, 3 kept
- K: The post-emergence phase of damping off is the infection of young, juvenile tissues of the collar.
  S (8/9): The post-emergence phase is characterized by the infection of the young, juvenile tissues of the collar at the ground level.
- K: The seedlings topple over or collapse.
  S (4/4): Seedlings topple over or collapse.
- K: The infected tissues become soft and water soaked.
  S (6/6): Post-emergence phase: Infected tissues become soft and water soaked.

## early_blight - ACCEPTED, 9 kept
- K: BROWN SPOTS WITH CONCENTRIC RINGS IN A BULL'S EYE PATTERN WITH YELLOW MARGIN ON Fruits.
  S (7/8): Brown spots with concentric rings in a bull's eye pattern with yellow margin.
- K: Fruit gets infected through calyx or stem attachment;
  S (7/7): Fruit gets infected through calyx or stem attachment;
- K: brown concentric rings on fruits.
  S (3/3): brown concentric rings on fruits.
- K: Irregular leaf spots mostly appear from marginal portion of leaves.
  S (7/7): Irregular leaf spots mostly appear from marginal portion of leaves.
- K: In many tomato cultivars, symptoms are V shaped and progress towards midrib.
  S (7/7): In many tomato cultivars, symptoms are V shaped and progress towards midrib.
- K: These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
  S (11/11): These lesions are having prominent yellowing on their outer margin due to host specific toxin produced by the pathogen.
- K: Mostly disease appears in vegetative phase of plant growth before flowering.
  S (7/7): Mostly disease appears in vegetative phase of plant growth before flowering.
- K: This is a common disease of tomato occurring on the foliage at any stage of the growth.
  S (5/5): This is a common disease of tomato occurring on the foliage at any stage of the growth.
- K: The fungus attacks the foliage causing characteristic leaf spots and blight.
  S (7/7): The fungus attacks the foliage causing characteristic leaf spots and blight.

## fruit_rots - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## fusarium_wilt - ACCEPTED, 3 kept
- K: CLEARING OF VEINLETS AND YELLOWING OF THE LOWER LEAFS.
  S (5/5): Clearing of the veinlets and yellowing of the lower leaves.
- K: THE FIRST SYMPTOM OF THE DISEASE IS CLEARING OF VEINLETS AND CHLOROSIS OF THE LEAVES.
  S (5/5): The first symptom of the disease is clearing of the veinlets and chlorosis of the leaves.
- K: IN YOUNG PLANTS, THE SYMPTOM CONSISTS OF CLEARING OF VEINLETS AND Dropping OF PETIOLES.
  S (7/7): In young plants, symptom consists of clearing of veinlet and dropping of petioles.

## grey_leaf_spot - ACCEPTED, 4 kept
- K: SMALL CIRCULAR DARK BROWN NECROTIC SPOTS APPEAR ON THE LEAF LAMINA, ALL OVER THE FLESH, BUT ARE ISOLATED.
  S (10/12): Small circular dark brown necrotic, numerous spots appear all over the leaf lamina that is uniformly distributed on entire foliage.
- K: REMOVAL AND BURNING OF ALL CROP DEBRIS AFTER SENESCENCE OF THE CROP.
  S (6/6): Removal and burning of all crop debris after senescence of the crop.
- K: REMOVAL OF ALL CROP DEBRIS FROM THE FARM.
  S (3/4): Removal and burning of all crop debris after senescence of the crop.
- K: SEVERE INFECTED LEAFS BLIGHT AND FALL DOWN.
  S (5/6): Severely infected older leaves blight and fall down.

## healthy - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## helicoverpa_fruit_borer - ACCEPTED, 7 kept
- K: B Mature LARVA BORE CIRCULAR HOLES
  S (4/5): Mature larvae bore circular holes.
- K: C THRUST ONLY PART OF ITS BODY INTO FRUIT
  S (5/5): Thrust only a part of its body into fruit and eat the inner content.
- K: D EAT THE INNER CONTENT
  S (2/2): Thrust only a part of its body into fruit and eat the inner content.
- K: E THE LARVA BORE INTO THE FRUIT WITH THE POSTERIOR END OUTSIDE
  S (4/5): The larvae bore into the fruits with the posterior end outside the hole.
- K: F FEEDING THE CATERPILLAR THRUSTS ITS HEAD INSIDE
  S (5/5): While feeding the caterpillar thrust its head inside leaving the rest of the body outside.
- K: G LEAVING THE REST OF THE BODY OUTSIDE
  S (4/4): While feeding the caterpillar thrust its head inside leaving the rest of the body outside.
- K: H YOUNG LARVA FEEDS ON LEAF FLESH
  S (4/5): Young larva feeds on the leaves for some time and then attacks fruits.

## late_blight - rejected, 1 kept
Reasons: too_few_grounded_sentences:1

## mites - ACCEPTED, 5 kept
- K: AFFECTED LEAFS
  S (2/2): Affected leaves become reddish brown and bronzy.
- K: INFESTATION
  S (1/1): Severe infestation larvae silken webbing on the leaves, wither and dry.
- K: PEST
  S (1/1): In case of pests which are active during night like Spodoptera spray recommended biocides/ chemicals at the time of their appearance in the night.
- K: SANITATION
  S (1/1): Field sanitation;
- K: affected plants should be planted in tall border crops such as maize or sorghum.
  S (6/7): Plant tall border crops such as maize or sorghum.

## powdery_mildew - ACCEPTED, 8 kept
- K: Irregular, bright yellow blotches with yellow halo appear on leaves.
  S (7/7): Irregular, bright yellow blotches with yellow halo appear on leaves.
- K: Abundant white sporulation in the infected area of leaves.
  S (6/6): Abundant white sporulation in the infected area of leaves.
- K: Field sanitation.
  S (2/2): Field sanitation.
- K: Adopt early planting, sprinkler irrigation.
  S (5/5): Adopt early planting, sprinkler irrigation.
- K: Immediately remove and destroy them to help prevent the disease from spreading.
  S (5/5): Immediately remove and destroy them to help prevent the disease from spreading.
- K: Proper plant spacing of about 3 feet apart to allow for proper air circulation, which helps the foliage dry faster.
  S (9/9): Proper plant spacing of about 3 feet apart to allow for proper air circulation, which helps the foliage dry faster.
- K: Periodic clipping of lower leaves and mulching.
  S (5/5): Periodic clipping of lower leaves and mulching.
- K: Organic mulch added around the plants will protect roots while preventing fungal spores from splashing onto the plant.
  S (11/11): Organic mulch added around the plants will protect roots while preventing fungal spores from splashing onto the plant.

## pseudocercospora_leaf_blight - ACCEPTED, 3 kept
- K: OLIVACIOUS BLACK SOOTY GROWTH OF FUNGUS IS OBSERVED ON THE LOWER SURFACE OF THE LEAF.
  S (9/9): Olivacious black sooty growth of fungus was observed on the lower surface of the leaves.
- K: COLLECT AND BURN THE INFECTED LEAFS.
  S (4/4): Collect and burn the infected leaves.
- K: BE CAREFUL WHEN SELECTING EXOTIC HYBRIDS AND VARIETIES.
  S (5/5): Be careful for selecting exotic hybrids and varieties.

## root_knot_nematode - ACCEPTED, 5 kept
- K: ROOT-KNOT NEMATODES CAUSE ROOT GALLS ON THE FEEDER ROOTS AND OFTEN AFFECT THE ENTIRE ROOT SYSTEM SHOWING HEAVY GALLING.
  S (11/12): Root-knot nematodes cause root galls on the feeder roots and sometimes affect the entire root system showing heavy galling.
- K: INFECTED PLANTS IN PATCHES IN THE FIELD.
  S (3/3): Infected plants in patches in the field.
- K: FORMATION OF GALLS ON HOST ROOT SYSTEM IS THE PRIMARY SYMPTOM.
  S (7/7): Formation of galls on host root system is the primary symptom.
- K: IN SEVERELY INFECTED PLANTS THE ROOT SYSTEM IS REDUCED AND THE ROOTLETS ARE ALMOST COMPLETELY ABSENT.
  S (9/9): In severely infected plants the root system is reduced and the rootlets are almost completely absent.
- K: FOLLOW CROP ROTATION WITH MARIGOLD, WHEREVER POSSIBLE.
  S (6/6): Follow crop rotation with marigold, wherever possible.

## septoria_leaf_spot - ACCEPTED, 8 kept
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
- K: Removal and destruction of the affected plant parts.
  S (4/4): Removal and destruction of the affected plant parts.

## serpentine_leaf_miner - rejected, 0 kept
Reasons: empty_or_too_short, too_few_grounded_sentences:0

## spodoptera_tobacco_caterpillar - ACCEPTED, 4 kept
- K: THE YOUNG LARVA OF THE TOBACCO CATERPILLAR WILL SCRAP LEAFS ON THE VENTRAL SURFACE OF THE LEAF.
  S (6/8): Young larva scrap leaves on ventral surface.
- K: THIS IS A MINOR PEST UNDER OPEN CONDITIONS AND ASSUMES SEVERE FORM UNDER PROTECTED CULTIVATION.
  S (10/10): This is a minor pest under open conditions and assumes severe form under protected cultivation particularly in ill managed playhouses.
- K: THE EGGS WILL BE LAID IN CLUSTERS ON FLESH.
  S (3/4): Eggs are laid in clusters on foliage.
- K: THE MATURE LARVA WILL MIGRATE AND CAUSE EXTENSIVE DAMAGE TO LEAFS AND FRUITS.
  S (7/8): Mature larvae, migrate and cause extensive damage to leaves and fruits.

## thrips - ACCEPTED, 2 kept
- K: B THRIPS ARE SUCKING PESTS OF TOMATO.
  S (3/3): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.
- K: C THRIPS ARE SUCKING PESTS OF TOMATO.
  S (3/3): Thrips (Thrips tabaci, Frankliniella schultzei) are sucking pests of tomato.

## tomato_mosaic - ACCEPTED, 11 kept
- K: Light and dark green mottling on leaves
  S (5/5): Light and dark green mottling on leaves.
- K: Wilting of young leaves
  S (3/3): Wilting of young leaves.
- K: Leaflets distorted and puckered
  S (3/3): Leaflets distorted and puckered.
- K: Fern leaf symptoms
  S (3/3): Fern leaf symptoms.
- K: Stunted growth
  S (2/2): Stunted growth.
- K: Light and dark green mottling on leaves often accompanied by wilting of young leaves in sunny days when plants first become infected
  S (13/13): The disease is characterized by light and dark green mottling on the leaves often accompanied by wilting of young leaves in sunny days when plants first become infected.
- K: The leaflets of affected leaves are usually distorted, puckered and smaller than normal
  S (7/7): The leaflets of affected leaves are usually distorted, puckered and smaller than normal.
- K: Sometimes the leaflets become indented resulting in "fern leaf" symptoms
  S (7/7): Sometimes the leaflets become indented resulting in "fern leaf" symptoms.
- K: The affected plant appears stunted, pale green and spindly
  S (6/6): The affected plant appears stunted, pale green and spindly.
- K: Disease free seeds
  S (2/2): Disease free seeds.
- K: Removal of infected plants
  S (2/2): Removal of infected plants.

## tomato_spotted_wilt - ACCEPTED, 9 kept
- K: SEVERE STUNTING.
  S (2/2): Severe stunting.
- K: CHLOROCYTE OR NECROTIC RINGS ON LEAVES.
  S (3/4): Chlorotic or necrotic rings on leaves.
- K: THICKENING OF VEINS AND BRONZING OF YOUNG LEAVES.
  S (5/5): Thickening of veins and bronzing of young leaves.
- K: GROWING TIPS DIE-BACK AND WILT.
  S (4/4): Growing tips die-back and wilt.
- K: YELLOW AREAS WITH CONCENTRIC CIRCULAR MARKINGS IN FRUIT.
  S (5/5): Yellow areas with concentric circular markings in fruit.
- K: DISCOLORATION OF SEED.
  S (2/2): Discoloration of seed.
- K: SYMPTOMS VARY AMONG HOSTS AND IN A SINGLE HOST SPECIES.
  S (6/6): Symptoms vary among hosts and in a single host species.
- K: STUNTING IS A COMMON SYMPTOM OF TSWV INFECTION.
  S (5/5): Stunting is a common symptom of TSWV infection.
- K: CHLOROCYTE OR NECROTIC RINGS FORM ON THE LEAVES OF MANY INFECTED HOSTS.
  S (7/8): Chlorotic or necrotic rings form on the leaves of many infected hosts.

## tuta_absoluta_pinworm - ACCEPTED, 2 kept
- K: LEAF MINING
  S (2/2): Mining of leaves, stem and pinholes on fruits.
- K: HEALTHY SEEDLINGS
  S (2/2): Use healthy seedlings for transplanting.

## whitefly - ACCEPTED, 8 kept
- K: YELLOWING
  S (1/1): Yellowing.
- K: DOWNWARD CURLING AND DRYING OF LEAVES
  S (4/4): Downward curling and drying of leaves.
- K: VECTOR OF TOMATO LEAF CURL DISEASE
  S (3/3): Vector of tomato leaf curl disease.
- K: WHICH TRANSMITS TOMATO LEAF CURL VIRUS
  S (4/4): Whitefly is a well-known vector, which transmits tomato leaf curl virus.
- K: IT HAS PIERCING AND SUCKING MOUTHPART AND BOTH NYPMS AND ADULTS FEED ON LOWER SURFACE OF THE LEAVES CAUSING DEFORMATION OF YOUNG LEAVES
  S (12/13): It has piercing and sucking mouthpart and both nymphs and adults feed on lower surface of the leaves causing deformation of young leaves.
- K: WHITEFLIES ALSO EXCRETE HONEYDEW
  S (3/3): Whiteflies also excrete honeydew, causing sooty mold.
- K: CAUSING SOOTY MOLD
  S (3/3): Whiteflies also excrete honeydew, causing sooty mold.
- K: WHITEFLY IS A WELL-KNOWN VECTER
  S (3/4): Whitefly is a well-known vector, which transmits tomato leaf curl virus.

## yellow_leaf_curl_virus - ACCEPTED, 6 kept
- K: The virus is spread by whiteflies.
  S (3/3): The virus is spread by whiteflies (Bemisia tabaci).
- K: The disease appears in severe forms during the months of September and November.
  S (7/7): Disease appear in severe forms during the month of September to November.
- K: The leaves show downward rolling, curling, twisting, and chlorosis.
  S (7/7): Leaves show downward rolling, curling, twisting and chlorosis.
- K: The plants show stunting, shortening of internodes, bushy appearance, no flowering, and fruiting at later stages of the virus infection.
  S (11/12): Plants show stunting, shortening of internodes, bushy appearance, no flowering and fruiting at later stage of virus infection.
- K: The newly emerging leaves exhibit slight yellow colouration and later they also show curling symptoms.
  S (11/11): The newly emerging leaves exhibit slight yellow colouration and later they also show curling symptoms.
- K: The leaf curl disease is characterized by severe stunting of the plants with downward rolling and crinkling of the leaves.
  S (8/8): Leaf curl disease is characterized by severe stunting of the plants with downward rolling and crinkling of the leaves.

