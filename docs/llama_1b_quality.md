# Llama 3.2 1B answer quality (prompt work)

Task: `docs/handover/LLAMA_1B_TASK_AMAN.md`. Goal: more 1B answers pass the grounding check, without making them less
correct. The check, its 0.75 threshold and every safety check are unchanged; only the prompt changed.

**Result: `prompts/aman_v8_no_numbering.txt`**. On all 27 topics it is accepted for 24 (baseline 15), the six demo
topics 6/6 (baseline 3/6), 0 refusals (baseline 8), 7.2 grounded sentences per topic (baseline 2.9) and no distortion
found in a manual review of all 195 kept sentences. It also generates fewer tokens per answer (78 vs 106), so it should
not be slower on the Pi.

## Update 20 Nov: new grounding check (main) and the LoRA model (llm-v2)

The saved answers were re-checked with the grounding check merged into `main` (PR #6), without running Llama again:
`grounding_test . --replay` built from `main` (f883488). The LoRA-tuned 1B (`llama3_2_1b_krishirakshak_lora_8da4w.pte`,
release llm-v2, the app's new default) was run with `--llama-pte` on the same 27 topics and replayed the same way.

| Model + prompt | All 27 accepted | Demo | Grounded / topic | Distortions (manual review) | Generated tokens / answer |
|---|---|---|---|---|---|
| base 1B + built-in | 14 | 3/6 | 2.8 | - | 106 |
| **base 1B + v8** | **24** | **6/6** | **7.1** | 0 | 78 |
| base 1B + v10 | 24 | 6/6 | 7.9 | not re-reviewed | 82 |
| LoRA + built-in (app default) | 22 | 5/6 | 2.9 | 1 | 42 |
| **LoRA + v8** | **22** | **5/6** | **3.7** | 0 | 52 |
| LoRA + v10 | 21 | 5/6 | 3.1 | not reviewed | - |

- v8 keeps its result under the stricter check (24 -> 24; 7.2 -> 7.1 grounded per topic). Prompts that had
  distortions lost exactly those answers (v1 20 -> 17, v7 24 -> 22), so the new rules catch what the manual review found.
- On the LoRA model v8 gives the same acceptance as the built-in prompt with 28% more grounded sentences (3.7 vs 2.9)
  and removes the one distortion, for about 10 more tokens per answer. The LoRA model writes full, readable sentences
  (no fragment lists like the base 1B); it rejects `healthy` (provisional), `damping_off`, `spodoptera`,
  `bacterial_speck` and `serpentine_leaf_miner`/`whitefly`.
- Distortion still kept by the new check (LoRA + built-in, helicoverpa_fruit_borer): "Mature larvae make circular holes
  in the leaves." - source "Mature larvae bore circular holes." (they bore into the fruit; "leaves" added).
- Choice for the core team: base 1B + v8 gives the most accepted and grounded answers; LoRA + v8 is the better prompt
  for the LoRA model, with shorter (faster) answers. Speed on the Pi is not measured here.
- Results: `results/llama_eval/lora_builtin_all`, `lora_v8_all`, `lora_v10_all` (accepted columns in their
  summary.json are from the old check of this branch; the table above uses the new check).

## How it was measured

- C++ application, laptop (WSL Debian 12, x86), `krishirakshak --root . --eval-advisor <topics>`, same `.pte`
  (`llama3_2_1b_instruct_8da4w.pte`) and KB (`tomato_kb_v3`) as the app; prompt set with `KR_ADVISOR_PROMPT=<file>`.
  Greedy decoding, so a run is repeatable. Branch base: `llama-quality-speed` (ce31cb3).
- Every variant runs on **all 27 topics**; the demo result is read from the same run (the six demo topics are part of
  the 27), so no prompt is tuned to six cases.
- `python -m llm.summarize_eval results/llama_eval/<run>` turns the C++ output (`eval.jsonl`) into `answers.json` and
  `summary.json` (same keys as `llm/eval_advisor.py`) and `review.md`: every kept sentence of every accepted answer next
  to the source sentence that supports it best.
- **Manual review**: I read every kept sentence of the accepted answers against its source. A sentence that changes
  the meaning (wrong plant part, wrong disease name, symptom turned into an instruction, changed season or schedule,
  nonsense) is a distortion, also when the check kept it because of a known gap (short words such as "rot" are not
  checked, "plant" is a stop word). **Clean** = accepted with no distortion. Variants that were clearly behind on
  acceptance were not reviewed (marked -).
- `healthy` uses the spread line that is being fixed; its result is provisional.

## Log

All 27 topics unless the run name ends in `_demo`. bcw = `--block-cause-words`. Grounded = mean kept sentences per
topic. Runs are in `results/llama_eval/<run>/`.

| Variant (prompt file) | Change | Demo | All 27 accepted | Clean | Refused first | Grounded | Distortions (topics) |
|---|---|---|---|---|---|---|---|
| baseline (built-in) | - | 3/6 | 15 | 15 | 8 | 2.9 | 0 |
| baseline + bcw | - | 5/6 | 17 | 15 | 8 | 3.1 | 3 (collar_rot, late_blight x2) |
| v1 `aman_v1_per_sentence` | rewrite every fact sentence as its own short sentence; key-word list; one-shot example | 6/6 | 20 | 18 | 0 | 5.0 | 4 (damping_off x3, serpentine_leaf_miner) |
| v1 + bcw | | 6/6 | 20 | 17 | 0 | 6.3 | 6 (+ helicoverpa x2) |
| v1b `aman_v1b_full_stop` | v1 + "each ending with a full stop" | 3/6 (demo run) | - | - | 0 | 3.3 | - |
| v2 `aman_v2_explain` | "friendly extension worker", official advice + explanation | 2/6 (demo run) | - | - | 5 of 6 | 2.3 | - |
| v3 `aman_v3_no_keyword_list` | v1 without the key-word list | 5/6 | 13 | - | 0 | 3.1 | - |
| v4 `aman_v4_no_example` | v3 without the one-shot example | 6/6 | 22 | 22 | 0 | 6.4 | 0 |
| v4 + bcw | | 6/6 | 22 | 22 | 0 | 6.4 | 0 |
| v5 `aman_v5_keywords_no_example` | v1 without the example (key-word list kept) | 6/6 | 19 | - | 0 | 6.0 | - |
| v6 `aman_v6_full_stop` | v4 + full stop | 3/6 | 15 | - | 0 | 4.1 | - |
| v7 `aman_v7_task_in_user` | v4 instructions moved from the system to the user message | 5/6 | 24 | 21 | 0 | 5.7 | 3 (bacterial_canker, bacterial_wilt, tuta: headers only) |
| **v8 `aman_v8_no_numbering`** | **v4 + "Do not number the lines."** | **6/6** | **24** | **24** | **0** | **7.2** | **0** |
| v8 + bcw | (only fruit_rots changes) | 6/6 | 24 | 23 | 0 | 7.2 | 1 (fruit_rots) |
| v9 `aman_v9_all_sentences` | v4 + "Rewrite all the sentences of the FACTS, not only the first ones." | 6/6 | 21 | - | 0 | 6.1 | - |
| v10 `aman_v10_no_diagnosis` | v4 without the diagnosis line | 6/6 | 24 | 23 | 0 | 8.1 | 1 (early_blight, a demo topic) |
| v11 `aman_v11_no_numbering_no_diagnosis` | v8 without the diagnosis line | 6/6 | 23 | 22 | 0 | 7.8 | 1 (yellow_leaf_curl_virus, a demo topic) |
| v12 `aman_v12_no_repeat` | v8 + "Never write the same sentence twice." | 6/6 | 24 | 23 | 0 | 7.1 | 1 (helicoverpa) |
| v13 `aman_v13_capital` | v8 + "Start every line with a capital letter." | 4/6 | 22 | - | 0 | 4.7 | - |

v8 still rejects three topics: `bacterial_speck` (writes one sentence twice; the copy is dropped as a duplicate, so 1
grounded), `tuta_absoluta_pinworm` (numbers its lines anyway and loops on "The pinworm is found on the leaf") and
`whitefly` (one lowercase line without punctuation, so the check sees one long sentence). The app then shows the KB
text, which is the safe outcome. v12 and v13 targeted these failures: v12 fixes tuta but loses powdery_mildew, changes
the wording of 20 topics and brings a new distortion; v13 breaks the demo (4/6).

## What helped and why

1. **Ask for a rewrite of each fact sentence, not for advice** (baseline -> v1: 15 -> 20 accepted, 8 -> 0 refusals,
   2.9 -> 5.0 grounded). The check keeps a sentence only if 75% of its content words come from one source sentence.
   "Rewrite every sentence as its own short sentence, in the same order, never join two" makes the 1B produce exactly
   that shape. Asking it to advise or explain makes it merge facts and add its own words (dropped), and the 1B
   refuses advice-style prompts (v2: 5 of 6 refused). "Rewrite this text" is never refused.
2. **No one-shot example and no example key words** (v1 -> v4: 18 -> 22 clean, 4 -> 0 distortions). The 1B copies
   the example into the answer: the grain-storage example became "Use raised beds of 15 cm height to dry grain" for
   damping-off, and the example key-word list was copied as the aphids answer. The instructions alone are enough.
3. **"Do not number the lines."** (v4 -> v8: 22 -> 24 accepted, 6.4 -> 7.2 grounded, list markers dropped 21 -> 3).
   The 1B numbers its lines anyway ("1.", "I.", "1 Thrips ..."): a bare marker becomes a dropped "sentence", and a
   number glued to a sentence fails the number rule (the number is not in the source): with v4 all 8 thrips lines
   ("1 Thrips are sucking pests of tomato", ...) were dropped. Saying it twice in the prompt (once in the list of
   things not to write, once as its own sentence) stopped it for 25 of 27 topics.
4. **`--block-cause-words` does not help the rewrite prompt** (v4 + bcw gives the same answers as v4; v8 + bcw changes
   only fruit_rots, and adds a distortion there), so v8 should run without it. It helps
   the built-in prompt (3/6 -> 5/6 demo) but part of that gain is distortions the check misses (below), so I would not
   switch it on for this.

What did not work: asking for full stops (v1b, v6: fewer accepted, the 1B starts adding words), "explain" wording
(v2, refusals), moving the instructions into the user message (v7: markdown headers and new distortions), dropping the
diagnosis line (v10, v11: more kept sentences but each brought a new distortion on a demo topic), "rewrite all the
sentences" (v9), "never write the same sentence twice" (v12) and "start every line with a capital letter" (v13). **The 1B is very sensitive to wording**: a one-sentence change moves the result by up to 7 topics (v4 -> v6:
22 -> 15), so every change has to be run on all 27 topics and the kept sentences read again.

## Distortions found (all kept by the current check)

All are now "dropped" cases in `cpp/tests/grounding_test.cpp`. **The test fails on purpose (16 failures)** until the
grounding gaps are closed; the previously existing cases and the three new "kept" cases pass.

| Run | Topic | Kept sentence | Source | Problem |
|---|---|---|---|---|
| baseline + bcw | collar_rot | The disease is not spread through the use of infested farmyard manure, soil crop debris, and compost in the field. | Avoid use of infested farmyard manure, soil crop debris and compost in the field. | reversal (negation matched to "avoid") |
| baseline + bcw | late_blight | The disease is a black rot on tomato leaves. | Water-soaked black lesions on leaves and stems. | "rot" not checked (3 letters) |
| baseline + bcw | late_blight | The disease is killing the entire plant. | It enlarges rapidly until entire leaves are killed ... | "plant" is a stop word |
| v1 | damping_off | Prevent seedlings from rotting completely. | Pre-emergence phase: Complete rotting of seedlings. | symptom turned into an instruction |
| v1 | damping_off | Infect young, juvenile tissues of the collar. | ... infection of the young, juvenile tissues of the collar ... | reads as an instruction to infect |
| v1 | damping_off | Use raised beds of 15 cm height to dry grain. | Use raised beds of 15 cm height. | purpose copied from the prompt example |
| v1 | serpentine_leaf_miner | Apply neem cake to furrows (open)/beds (polyhouse) every 25 days. | ... @ 250 kg/ha at planting and repeat after 25 days. | schedule changed, dose left out |
| v1 + bcw | helicoverpa_fruit_borer | Larvae feed on the leaves while feeding the caterpillar. | Young larvae feed on tender foliage. | nonsense |
| v1 + bcw | helicoverpa_fruit_borer | Grow simultaneously 40 | Grow simultaneously 40 days old American tall marigold and 25 days old tomato seedling at 1:16 rows. | number without its meaning |
| v7 | bacterial_canker | Spots become slightly wrinkled | Centre of spots become slightly raised, tan coloured and rough. | symptom changed (3 of 4 words match) |
| v7 | bacterial_wilt | The wilting is happening on the lower leaves. | Lower leaves drop before wilting. | wrong plant part |
| v7 | tuta_absoluta_pinworm | `**Pests**` (and "* Tomato leaves", "* Tomato pinholes") | - | headers and fragments only, accepted as an answer |
| v8 + bcw | fruit_rots | The disease is most severe in the lower portion of the fruit. | Generally lower portion of fruits are infected which are coming in soil contact. | "infected" became "most severe" (3 of 4 words match) |
| v12 | helicoverpa_fruit_borer | Leave the rest of the body outside | While feeding the caterpillar thrust its head inside leaving the rest of the body outside. | description turned into an instruction |
| v10 | early_blight | Fruit blight observed on plants as small black lesions | Early blight is first observed on the plants as small, black lesions ... | wrong disease name (5 of 6 words match) |
| v11 | yellow_leaf_curl_virus | Disease appears in September | Disease appear in severe forms during the month of September to November. | season changed |

Grounding gaps these show (for the core team; the check was not changed in this task):
- 3-letter words are not checked ("rot"), and "plant" is a stop word.
- A negated rewrite can match a source that is negative for another reason ("avoid").
- With 4 content words, one changed or invented word still passes (3 of 4 = 0.75): "wrinkled", "fruit blight".
- **A one-word line passes (1 of 1) and counts towards the two grounded sentences**, so an answer of markdown headers
  and fragments can be accepted. Suggest a minimum of 2 content words per kept sentence.

## Known limits of v8

- **Fragments.** v8 keeps the facts but some answers are lists of short noun phrases rather than sentences. Worst case
  `bacterial_canker`: 19 kept items such as "Seedlings affected", "Wilting", "Cracks", "Petioles". Also
  "Mulch organic mulch" (powdery_mildew), "Bemisia tabaci" (yellow_leaf_curl_virus). Faithful, but poor to read.
- **Run-on text in the app.** v8 writes one sentence per line, often without a full stop. The app joins kept sentences
  with spaces, so the farmer sees "Install yellow sticky traps Use nitrogen fertilizer judiciously". Suggest: when
  joining, add a full stop to a kept sentence that does not end with one.
- **Retry prompt.** With v8 there are no refusals, so the retry prompt (hard-coded in `llama_advisor.cpp`) is not used.
  In the baseline runs its answers invented facts ("February or March", "Burn infected leaves", another disease name);
  most were dropped by the check. If the built-in prompt changes to v8, the retry could reuse the v8 wording.
- `healthy` is accepted with v8 but is provisional until the healthy evaluation fix.
- Measured on the laptop only. The Pi uses the same `.pte` and greedy decoding, so the text should be the same, but
  speed needs measuring there.

## Files

- `prompts/aman_v*.txt` - all variants (v8 is the one to use).
- `results/llama_eval/<run>/` - `eval.jsonl` (raw C++ output), `answers.json`, `summary.json`, `review.md`,
  `run_info.txt`, `stderr.txt`.
- `llm/summarize_eval.py` - table, review and JSON files from C++ runs.
- `cpp/tests/grounding_test.cpp` - 16 new "dropped" cases, 3 new "kept" cases.
