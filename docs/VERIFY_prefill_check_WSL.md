# Prefill check on the WSL build machine (branch llama-prefix-cache)

- Branch verified: `llama-prefix-cache`, commit `a7c1377` ("Turn the prompt prefix cache off by default and add a
  tool that compares split and single prefill logits"), on top of `43f524a` and `26221a7`
- Machine: development PC with ExecuTorch 1.5.1, the Llama `.pte` (`models/llama3_2_1b_instruct_8da4w.pte`) and its
  tokenizer (Intel i5-12500H, WSL2, Ubuntu 22.04, 12 GB RAM for WSL)
- Date: 17 November 2026
- No code was changed and nothing was committed to `llama-prefix-cache`, `pi-perf-model` or `main`. This report is the
  only commit, on branch `verify/prefill-check-wsl`.

## Summary

| Step | Result |
|---|---|
| 1. Branch | `a7c1377` on top |
| 2. Build + tests | Configure and build exit 0, 0 compiler warnings, no CMake warnings; `prefill_check` built; `ctest` 1/1 passed |
| 3. Default (cache off) | `prefix_cache` = `off`, `accepted` = true, `raw_text` identical to the cache-off text of the previous report |
| 4. Prompt dumps | All three written (exit 0) |
| 5. Prefill check | Split prefill changes the final logits by 0.95 - 2.61 (max abs) on every split of the two diagnosis prompts; only two splits, both on the follow-up prompt, give exactly 0. `same_top1` is yes in every row |
| 6. Determinism | Two repeated runs byte-identical to each other and to the step 5 output |

Failures: none (all commands exit 0).

Main findings:

1. Every row has `max_abs_diff` above 0.01 except two rows of the follow-up (ask) prompt: k = 97 (the split the app
   uses for the ask prompt; rest 286) and k = 192 (rest 191), both exactly 0.000000.
2. No row has `same_top1` = NO: the first generated token is the same in all splits (margins 2.03 / 2.65 / 0.26).
3. The difference does not depend on `rest_tokens` being below 192: rows with rest below 192 and rows with rest of
   192 or more are both large on the diagnosis prompts, and the two exact matches have rest 286 and 191.
4. This explains the earlier observation: the app's diagnosis split (k = 123) gives a difference of 1.58 (late blight)
   and 1.55 (early blight) logit units, while the app's ask split (k = 97) gives 0. The differences are large (about
   1 - 2.6 logit units), not rounding-size (around 1e-3); by the criterion of the previous report this points to a
   systematic difference between split and single prefill rather than small numerical noise. Why some split points
   of the ask prompt are exact is not explained by this check.

## Step 2 - build and tests

```
cmake -S cpp -B build/x86-llm -G Ninja -DEXECUTORCH_ROOT=$HOME/x86_libs/executorch   -> exit 0, no CMake warnings
cmake --build build/x86-llm -j                                                       -> exit 0, 0 compiler warnings
targets present: krishirakshak, prefill_check, grounding_test, membw
(cd build/x86-llm && ctest --output-on-failure)
1/1 Test #1: grounding ........................   Passed    0.02 sec
100% tests passed, 0 tests failed out of 1
```

## Step 3 - default run (prefix cache off)

`build/x86-llm/krishirakshak --root . P1` with P1 = PlantDoc test `Tomato_leaf_late_blight/test_Tomato leaf late blight_1.jpg`,
exit 0.

- `llama_info`: `{"max_context":1024,"prefix_cache":false,"prefix_prefill_ms":0.0,"prefix_tokens":0}`
- `llama.stats.prefix_cache` = `off`, prompt_tokens 295, prefilled_tokens 295, time_to_first_token_s 7.96,
  tokens_per_s 12.37
- `llama.accepted` = true
- `raw_text` identical to the cache-off text of the previous report (pair 1, P1): yes
- diagnosis `late_blight` 0.950692 (unchanged)

## Step 4 - prompt dumps

| file | command | exit | size |
|---|---|---|---|
| `/tmp/prompt_late.txt` | `KR_DUMP_PROMPT=... krishirakshak --root . P1` | 0 | 1502 bytes, 295 tokens |
| `/tmp/prompt_early.txt` | `KR_DUMP_PROMPT=... krishirakshak --root . P2` (P2 = `Tomato_Early_blight_leaf/test_Tomato Early blight leaf_1.jpg`) | 0 | 1300 bytes, 243 tokens |
| `/tmp/prompt_ask.txt` | `KR_DUMP_PROMPT=... krishirakshak --root . --ask "when can I harvest after spraying" --topic late_blight` | 0 | 1675 bytes, 383 tokens |

`prompt_late.txt` (Python repr):

```
'<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\nYou rewrite agricultural extension text for tomato farmers in India. Rewrite each FACT in simple English as one short sentence. Keep the meaning of every fact exactly: do not add new advice, do not leave out an instruction and never turn an instruction into its opposite. Write each fact once, as plain sentences without a title, list markers or an introduction.\n\nExample.\nFACTS:\n1. Removal and destruction of crop debris.\n2. Avoid overhead irrigation.\nRewritten facts:\nRemove the old plant waste from the field and destroy it. Do not water the plants from above.<|eot_id|><|start_header_id|>user<|end_header_id|>\n\nDiagnosis: Late blight on a tomato leaf (model confidence 95%). Estimated spread on the photographed leaf: moderate. This disease is urgent: it spreads very fast.\n\nFACTS:\n1. Water-soaked black lesions on leaves and stems. Lesions expand rapidly and the entire leaf becomes necrotic. White sporulation on leaves. Dark brown lesions on fruit; soft rot and disintegration of fruits.\n2. Grow resistant variety/hybrid Arka Abhed F1. Avoid planting tomatoes in the same field every year. Remove infected plant parts. Ensure enough space between plants and stake them. Use black polythene mulch (30 micron). Improve field drainage and avoid overhead irrigation. Plant windbreaks and avoid late sowing in the monsoon season.\n3. Proper drainage. Crop rotation.\n\nRewritten facts:<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n'
```

`prompt_early.txt` has the same system part and example; the user part is the early blight diagnosis line and three
facts (TNAU symptoms, TNAU cultural, NIPHM cultural). `prompt_ask.txt` has the follow-up system prompt ("You are
KrishiRakshak, an assistant for tomato farmers in India. Answer the farmer's question using ONLY the FACTS ..."), the
question and four retrieved facts (NIPHM safety, streptocycline spray, Bt/NPV for caterpillars, ICAR general IPM).

## Step 5 - prefill check (full output tables, all exit 0)

Command form: `build/x86-llm/prefill_check models/llama3_2_1b_instruct_8da4w.pte models/llama3_2_tokenizer.model PROMPT [k ...]`

### prompt_late.txt, default split points

```
prompt tokens 295, single prefill top1 40 (margin 2.0284)
     k rest_tokens max_abs_diff top1_full top1_split margin_full same_top1
   255          40     0.953166        40         40      2.0284       yes
   195         100     1.207803        40         40      2.0284       yes
   145         150     1.378229        40         40      2.0284       yes
   123         172     1.578526        40         40      2.0284       yes
   104         191     2.095018        40         40      2.0284       yes
   103         192     1.478511        40         40      2.0284       yes
    95         200     1.696650        40         40      2.0284       yes
    45         250     1.650483        40         40      2.0284       yes
```

### prompt_late.txt, splits 123 103 50 10

```
prompt tokens 295, single prefill top1 40 (margin 2.0284)
     k rest_tokens max_abs_diff top1_full top1_split margin_full same_top1
   123         172     1.578526        40         40      2.0284       yes
   103         192     1.478511        40         40      2.0284       yes
    50         245     1.477001        40         40      2.0284       yes
    10         285     1.745469        40         40      2.0284       yes
```

### prompt_early.txt, default split points

```
prompt tokens 243, single prefill top1 40 (margin 2.6481)
     k rest_tokens max_abs_diff top1_full top1_split margin_full same_top1
   203          40     1.344894        40         40      2.6481       yes
   143         100     1.258501        40         40      2.6481       yes
    93         150     1.887733        40         40      2.6481       yes
    71         172     1.711092        40         40      2.6481       yes
    52         191     2.610542        40         40      2.6481       yes
    51         192     1.983968        40         40      2.6481       yes
    43         200     2.433090        40         40      2.6481       yes
```

### prompt_early.txt, splits 123 51 10

```
prompt tokens 243, single prefill top1 40 (margin 2.6481)
     k rest_tokens max_abs_diff top1_full top1_split margin_full same_top1
   123         120     1.550141        40         40      2.6481       yes
    51         192     1.983968        40         40      2.6481       yes
    10         233     1.453342        40         40      2.6481       yes
```

### prompt_ask.txt, default split points

```
prompt tokens 383, single prefill top1 8586 (margin 0.2578)
     k rest_tokens max_abs_diff top1_full top1_split margin_full same_top1
   343          40     1.376500      8586       8586      0.2578       yes
   283         100     1.271472      8586       8586      0.2578       yes
   233         150     1.171670      8586       8586      0.2578       yes
   211         172     1.743923      8586       8586      0.2578       yes
   192         191     0.000000      8586       8586      0.2578       yes
   191         192     1.210777      8586       8586      0.2578       yes
   183         200     1.198607      8586       8586      0.2578       yes
   133         250     1.326009      8586       8586      0.2578       yes
```

### prompt_ask.txt, splits 97 250 300

```
prompt tokens 383, single prefill top1 8586 (margin 0.2578)
     k rest_tokens max_abs_diff top1_full top1_split margin_full same_top1
    97         286     0.000000      8586       8586      0.2578       yes
   250         133     1.254998      8586       8586      0.2578       yes
   300          83     1.141149      8586       8586      0.2578       yes
```

### Rows to point out

`max_abs_diff` above 0.01: every row of `prompt_late.txt` and `prompt_early.txt` (0.95 - 2.61), and every row of
`prompt_ask.txt` except:

| prompt | k | rest_tokens | max_abs_diff |
|---|---|---|---|
| ask | 192 | 191 | 0.000000 |
| ask | 97 (split used by the app) | 286 | 0.000000 |

`same_top1` = NO: none.

Dependence on `rest_tokens` below 192: none visible.

| prompt | max_abs_diff, rest < 192 | max_abs_diff, rest >= 192 |
|---|---|---|
| late | 0.95 - 2.10 (rest 40, 100, 150, 172, 191) | 1.48 - 1.75 (rest 192, 200, 245, 250, 285) |
| early | 1.26 - 2.61 (rest 40, 100, 120, 150, 172, 191) | 1.45 - 2.43 (rest 192, 200, 233) |
| ask | 1.14 - 1.74 (rest 40, 83, 100, 133, 150, 172), and 0.000000 at rest 191 (k = 192) | 1.20 - 1.33 (rest 192, 200, 250), and 0.000000 at rest 286 (k = 97) |

## Step 6 - determinism

`build/x86-llm/prefill_check models/llama3_2_1b_instruct_8da4w.pte models/llama3_2_tokenizer.model /tmp/prompt_late.txt`
run twice more (exit 0 both): both outputs are byte-identical to each other (`cmp`) and to the step 5 output of the
same command. The numbers above are deterministic on this machine.
