# Verification of branch llama-prefix-cache on the WSL build machine

- Branch verified: `llama-prefix-cache`, commit `43f524a` ("Reuse the KV cache of the fixed Llama prompt prefix
  between requests, with a no-prefix-cache option for comparison"), on top of `26221a7` and `fe9104b`
- Machine: development PC with ExecuTorch 1.5.1 (x86 and aarch64 installs), the Llama `.pte` and the ARM toolchain
  (Intel i5-12500H, WSL2, Ubuntu 22.04, 12 GB RAM for WSL). CPU idle before the measurements.
- Date: 17 November 2026
- No code was changed and nothing was committed to `llama-prefix-cache`, `pi-perf-model` or `main`. This report is the
  only commit, on branch `verify/llama-prefix-cache-wsl`.

## Summary

| Step | Result |
|---|---|
| 1. Branch | `43f524a` on top as expected |
| 2. x86 build with ExecuTorch + tests | Configure, compile and link succeeded: no warnings, no errors, no undefined references. `ctest` 1/1 passed |
| 3. Correctness and speed, 3 photos in one process | **FAIL (correctness).** With the prefix cache on, Llama's `raw_text` differs from cache off for every request, and every cached answer is rejected by the output check (0/6 accepted vs 6/6 with the cache off). Time to first token is lower with the cache (2.8 - 5.7 s vs 5.5 - 7.7 s) |
| 4. Follow-up switching | Answers; `prefix_cache` = `miss` as expected; `raw_text` identical to `--no-prefix-cache` |
| 5. Thread scaling | Done; table below |
| 6. Pi build | Configure and build exit 0, aarch64 binaries; **0 compiler warnings** (confirmed with a full clean rebuild); OpenCV header warnings are gone |

Failures:

1. Step 3: the diagnosis (advise) output with the prefix cache on is wrong (different text, ignores the facts,
   repetition loop or refusal), in both cache-hit and cache-miss cases. Details and a suggested experiment below.

## Step 2 - build and tests (x86, ExecuTorch 1.5.1)

```
cmake -S cpp -B build/x86-llm -G Ninja -DEXECUTORCH_ROOT=$HOME/x86_libs/executorch   -> exit 0, no CMake warnings
cmake --build build/x86-llm -j                                                       -> exit 0, 0 compiler warnings
(cd build/x86-llm && ctest --output-on-failure)
1/1 Test #1: grounding ........................   Passed    0.04 sec
100% tests passed, 0 tests failed out of 1
```

No link errors: Module, TextDecoderRunner, TextPrefiller, TextTokenGenerator, Sampler, IOManager and
get_llm_metadata all resolved against the installed ExecuTorch 1.5.1 libraries. (The CMake CMP0144 developer
warning seen on `pi-perf-model@fe9104b` no longer appears.)

## Step 3 - correctness and speed (three photos in one process)

Photos (PlantDoc test split):
- P1 = `Tomato_leaf_late_blight/test_Tomato leaf late blight_1.jpg`
- P2 = `Tomato_Early_blight_leaf/test_Tomato Early blight leaf_1.jpg`

Commands, run as a pair twice (on 1, off 1, on 2, off 2), all exit 0:

```
build/x86-llm/krishirakshak --root . P1 P2 P1 > /tmp/pc_on.json 2> /tmp/pc_on.log
build/x86-llm/krishirakshak --root . --no-prefix-cache P1 P2 P1 > /tmp/pc_off.json 2> /tmp/pc_off.log
```

### "loaded:" line, Llama part

| run | prefix_cache | prefix_tokens | prefix_prefill_ms | load_ms |
|---|---|---|---|---|
| on 1 | true | 123 | 3615.3 | 8122.8 |
| off 1 | false | 0 | 0.0 | 3583.7 |
| on 2 | true | 123 | 2097.3 | 5356.1 |
| off 2 | false | 0 | 0.0 | 3179.2 |

### Per request

| mode | pair | request | prompt_tokens | prefilled_tokens | prefix_cache | time_to_first_token_s | tokens_per_s | llama.accepted | diagnosis |
|---|---|---|---|---|---|---|---|---|---|
| on | 1 | P1 late blight | 295 | 172 | hit | 5.65 | 10.33 | False | late_blight 0.950692 |
| on | 1 | P2 early blight | 243 | 120 | hit | 2.79 | 17.31 | False | early_blight 0.946727 |
| on | 1 | P1 late blight (again) | 295 | 172 | hit | 3.94 | 15.29 | False | late_blight 0.950692 |
| off | 1 | P1 late blight | 295 | 295 | off | 6.70 | 13.79 | True | late_blight 0.950692 |
| off | 1 | P2 early blight | 243 | 243 | off | 6.42 | 11.73 | True | early_blight 0.946727 |
| off | 1 | P1 late blight (again) | 295 | 295 | off | 7.72 | 15.37 | True | late_blight 0.950692 |
| on | 2 | P1 late blight | 295 | 172 | hit | 4.67 | 12.74 | False | late_blight 0.950692 |
| on | 2 | P2 early blight | 243 | 120 | hit | 2.77 | 16.55 | False | early_blight 0.946727 |
| on | 2 | P1 late blight (again) | 295 | 172 | hit | 4.10 | 15.88 | False | late_blight 0.950692 |
| off | 2 | P1 late blight | 295 | 295 | off | 6.54 | 17.68 | True | late_blight 0.950692 |
| off | 2 | P2 early blight | 243 | 243 | off | 5.45 | 13.12 | True | early_blight 0.946727 |
| off | 2 | P1 late blight (again) | 295 | 295 | off | 7.03 | 16.71 | True | late_blight 0.950692 |

- Vision diagnosis identical in all 12 requests.
- 123 (prefix) + 172 (request) = 295 and 123 + 120 = 243: the token split matches the full prompt.

### raw_text comparison, cache on vs off

| pair | request | identical |
|---|---|---|
| 1 | P1 late blight | **No** |
| 1 | P2 early blight | **No** |
| 1 | P1 late blight (again) | **No** |
| 2 | P1 late blight | **No** |
| 2 | P2 early blight | **No** |
| 2 | P1 late blight (again) | **No** |

Each mode is deterministic: the texts of pair 1 and pair 2 are identical within a mode (on: 3/3, off: 3/3).

Example, pair 1, P1 late blight:

Cache ON (rejected: `empty_or_too_short`, `too_few_grounded_sentences:0`; 159 generated tokens):

```
I. The disease is caused by a black sooty fungus.
II. The disease is spreading rapidly.
III. The disease is highly contagious.
IV. The disease is spreading very quickly.
V. The disease is spreading rapidly and has already affected many plants.
VI. The disease is spreading rapidly and has already affected many plants.
VII. The disease is spreading rapidly and has already affected many plants.
VIII. The disease is spreading rapidly and has already affected many plants.
IX. The disease is spreading rapidly and has already affected many plants.
X. The disease is spreading rapidly and has already affected many plants.
XI. The disease is spreading rapidly and has already affected many plants.
XII. The disease is spreading rapidly and has already affected many plants.
XIII.
```

Cache OFF (accepted; 86 generated tokens):

```
I. Remove the old plant debris from the field.
II. Do not water the plants from the ground.
III. Remove infected plant parts.
IV. Ensure enough space between plants.
V. Stake the plants.
VI. Use black polythene mulch.
VII. Improve field drainage.
VIII. Avoid overhead irrigation.
IX. Plant windbreaks.
X. Avoid late sowing in the monsoon season.
```

Example, pair 1, P2 early blight: cache ON = `I can't fulfill this request.` (7 tokens, rejected); cache OFF = a 145-token answer
whose grounded sentences were accepted (it starts with a refusal sentence that the grounding check drops, then
"Remove and destroy crop debris. Use resistant or tolerant cultivars. ...").

### Additional check (no code change): diagnosis cache miss inside a request

Through the web server in one process: first `POST /api/ask` (switches the cache to the follow-up prefix), then
`POST /api/analyse` with P1 twice.

```
A ask      : miss | 'You can harvest tomatoes 28 days after transplanting, but only after the first t'
B analyse 1: miss | accepted False | 'I. The disease is caused by a black sooty fungus.\nII. The disease is spreading rapidly.\nII'
B analyse 2: hit  | accepted False | 'I. The disease is caused by a black sooty fungus.\nII. The disease is spreading rapidly.\nII'
```

So the wrong diagnosis output does not depend on a stale cache (it also happens on a miss, where the prefix is
prefilled inside the same request), while the follow-up prompt gives the same text split or not (step 4).

### Observations for the investigation

- Both prompt types go through the same code path (`ensurePrefix(prefix)` at position 0, then
  `prefill(tail, pos = prefixTokens_)`), and the split check (`head + tail == all`) passed for both.
- Follow-up prompt: split 97 + 286 tokens -> text identical to a single 383-token prefill.
- Diagnosis prompt: split 123 + 172 tokens -> different text from a single 295-token prefill, already from the
  second generated sentence on.
- `TextPrefiller::prefill_chunk` in ExecuTorch 1.5.1 passes `start_pos` to `TextDecoderRunner::step` and advances it
  by the chunk length, which looks correct for a non-zero start position.
- Possible explanations, not verified: (a) chunked prefill is not numerically identical to a single prefill
  (for example attention or dynamic activation quantization computed per chunk), and the diagnosis prompt is fragile
  enough for greedy decoding to flip early; (b) a position or mask problem that only shows for some prompt lengths.
- Suggested experiment: for the diagnosis prompt, compare the logits after the last prompt token for
  (i) one 295-token prefill and (ii) 123 + 172 tokens prefilled in two calls, without any reuse across requests
  (max absolute difference, and the top-5 tokens with their margins). A difference around 1e-3 with a small top-1
  margin points to (a); a large difference points to (b). Until this is settled, the prefix cache should stay off by
  default.

## Step 4 - follow-up switching

```
build/x86-llm/krishirakshak --root . --ask "when can I harvest after spraying" --topic late_blight      -> exit 0
```

- `stats`: `prefix_cache` = `miss`, prompt_tokens 383, prefilled_tokens 286, time_to_first_token_s 4.516,
  tokens_per_s 12.63, generated_tokens 30, total_s 6.89
- `raw_text`: `You can harvest tomatoes 28 days after transplanting, but only after the first true leaves appear.`
- `accepted`: False (`empty_or_too_short`, `no_grounded_sentence`): the grounding check correctly blocks this stitched
  answer; `answer` is null and the retrieved facts are returned (general/safety, bacterial_spot/chemical,
  caterpillars/biological, healthy/cultural).
- Same command with `--no-prefix-cache`: `prefix_cache` = `off`, prefilled_tokens 383, time_to_first_token_s 9.587,
  tokens_per_s 14.90, **identical `raw_text`**.

## Step 5 - thread scaling (cache on, one late blight photo, one process per N)

| --llama-threads | prefix_prefill_ms at load | time_to_first_token_s | tokens_per_s | generated_tokens | prefilled_tokens | prefix_cache |
|---|---|---|---|---|---|---|
| 1 | 3413 | 6.04 | 8.27 | 159 | 172 | hit |
| 2 | 4163 | 5.70 | 12.59 | 159 | 172 | hit |
| 3 | 2898 | 4.75 | 14.62 | 159 | 172 | hit |
| 4 | 2344 | 3.97 | 13.59 | 159 | 172 | hit |

(These runs use the cache-on path, so the generated text is the faulty one from step 3; the timings are still
comparable between N. WSL timings are only indicative for the Pi.)

## Step 6 - Pi build

```
cmake -S cpp -B build/arm -G Ninja -DCMAKE_TOOLCHAIN_FILE=cpp/arm-toolchain.cmake -DEXECUTORCH_ROOT=$HOME/arm_libs/executorch
  -> exit 0, no CMake warnings or errors
cmake --build build/arm -j
  -> exit 0, 0 compiler warnings
cmake --build build/arm --clean-first -j      (to count warnings over a full rebuild: 12 compile steps)
  -> exit 0, 0 compiler warnings
file build/arm/krishirakshak  -> ELF 64-bit LSB pie executable, ARM aarch64, dynamically linked
file build/arm/membw          -> ELF 64-bit LSB pie executable, ARM aarch64, dynamically linked
```

The 166 OpenCV header warnings reported for `pi-perf-model@fe9104b` are gone.
