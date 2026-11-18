# WSL verification report - branch llama-quality-speed

| | |
|---|---|
| Branch / commit | `llama-quality-speed` at `ce31cb3` (no changes made to it) |
| Date | 18 November 2026 |
| Machine | WSL2 Ubuntu 22.04, Intel Core i5-12500H (16 threads), about 9 GB RAM for WSL, GCC 11.4.0 |
| Power | **on battery ("Not charging") during steps 3-6**: absolute times are 3-8x slower than earlier measurements on this machine the same day; compare times only within this report |
| Status | All steps done (step 7: export on Kaggle, evaluation on this PC) |

## Summary

| Step | Result |
|---|---|
| 1. Checkout | `ce31cb3` on top, as expected |
| 2. Build + tests | **The given configure command fails with the system CMake 3.22.1** (ExecuTorch requires 3.24). With CMake 3.31.10 from `~/.venvs/et/bin` (the one the existing build folder was configured with): configure exit 0, no CMake warnings; full rebuild 0 warnings, 0 errors, 0 undefined references; `ctest` 1/1 passed |
| 3. Regression vs `app-handover-llama-3b` | early blight: `raw_text` identical. late blight: identical for the first 552 characters, then the new binary stops (`stopped_on_repeat: true`); the old binary continues with a repeated part. Both accepted |
| 4. Decoding options, 1B | best: `--block-cause-words`, **5/6 accepted** (default 3/6, every fact-bias setting 4/6). **But 2 of the 4 kept late-blight sentences pass only through gaps in the grounding check** (see 4.3) |
| 5. Llama 3B | 5/6 accepted with and without `--block-cause-words`; identical answers (the option did not change any token) |
| 6. Streaming | result event after 2.7 s, first token after 19.4 s, final after 37.9 s, 117 token events; `final.data` equals `/api/analyse` except timings |
| 7. FP32 baseline | **FP32 6/6 accepted vs INT4 3/6** with the same prompts and options: the INT4 quantization is a main cause of the rejected answers. FP32: 21 grounded / 46 dropped sentences, Llama 412 s vs 163 s, peak RSS 6.2 GB |
| 8. Pi bundle | ARM configure + build exit 0, 0 warnings, 0 errors; aarch64 binary; bundle 2.9 GB (both Llama models included); not copied |

## Step 1 - checkout

```
$ git log -3 --oneline
ce31cb3 Llama on the runner building blocks: token streaming endpoint, optional fact steering, near-duplicate repeat stop, advisor evaluation mode
887cdf0 Performance status page and raw Raspberry Pi 5 benchmark results; LoRA notebook: dynamic shapes for KV-cache generation
bb00834 Questions for the mentor: project status and ten questions on judging priorities (Markdown and PDF)
```

## Step 2 - build and tests

Command as given (`cmake` on the default PATH is `/usr/bin/cmake` 3.22.1):

```
$ cmake -S cpp -B build/x86-llm -G Ninja -DEXECUTORCH_ROOT=$HOME/x86_libs/executorch
-- Native build (development machine)
CMake Error at /home/studinstru/x86_libs/executorch/lib/cmake/ExecuTorch/executorch-config.cmake:26 (cmake_minimum_required):
  CMake 3.24 or higher is required.  You are running version 3.22.1
Call Stack (most recent call first):
  CMakeLists.txt:98 (find_package)
-- Configuring incomplete, errors occurred!
```

The following `cmake --build` still succeeded because the existing build folder had been configured earlier with
`CMAKE_COMMAND=/home/studinstru/.venvs/et/lib/python3.10/site-packages/cmake/data/bin/cmake` (3.31.10). Repeated with
`PATH=$HOME/.venvs/et/bin:$PATH` and all sources touched (full rebuild of the changed code):

| Check | Result |
|---|---|
| configure | exit 0, 0 CMake warnings |
| build | exit 0, 12/12 steps, **0 compiler warnings, 0 errors, 0 undefined references** |
| `ctest --output-on-failure` | `1/1 Test #1: grounding ... Passed` |

Suggestion: `cpp/README.md` could state that the build needs CMake >= 3.24 (e.g. `pip install cmake` in the venv).

## Step 3 - same output as before (regression)

Old binary: `git worktree add /tmp/kr_old origin/app-handover-llama-3b` (887cdf0), built to `/tmp/kr_old/build` (configure
and build exit 0). Both binaries run with default options, `--root .` of this checkout, photos from
`dist/krishirakshak-pi/photos/`. Worktree removed afterwards (`git worktree list` shows only the main checkout).

| Photo | raw_text identical | accepted old / new | time to first token old / new | tokens/s old / new | generated tokens old / new | stopped_on_repeat (new) |
|---|---|---|---|---|---|---|
| Tomato_leaf_late_blight | **no** (identical up to char 552) | true / true | 26.59 s / 20.99 s | 6.55 / 3.43 | 159 / 116 | **true** |
| Tomato_Early_blight_leaf | yes | true / true | 29.16 s / 24.94 s | 6.19 / 5.97 | 108 / 108 | false |

Late blight, where the texts part (old text continues, new text ends at the near-duplicate stop):

```
old: ... as a light-pale green water soaked dead area on the foliage.\n\nV. The lesions are wet in morning and dried, shriveled in daylight.\nThe diseas...   (724 characters)
new: ... as a light-pale green water soaked dead area on the foliage.                                                                                         (552 characters)
```

The difference is the new near-duplicate repeat stop, not a change in the generated tokens before it. Timing note:
both binaries ran under the same (battery) conditions; the lower tokens/s of the new binary on late blight (3.43 vs
6.55) did not show on early blight (5.97 vs 6.19) and should be re-measured on mains power or on the Pi.

## Step 4 - decoding options, Llama 1B, six demo diseases

`B=build/x86-llm/krishirakshak; $B --root . --eval-advisor demo [options]` - every run exit 0.

| Config | Accepted (of 6) | Grounded sentences | Dropped sentences | Llama seconds | Per topic (accepted, grounded) |
|---|---|---|---|---|---|
| default | 3 | 18 | 56 | 163 | healthy n0, early_blight Y5, late_blight n1, septoria Y4, bacterial_spot n1, yellow_leaf_curl Y7 |
| `--block-cause-words` | **5** | 22 | 60 | 161 | healthy n0, early_blight Y5, late_blight Y4, septoria Y4, bacterial_spot Y2, yellow_leaf_curl Y7 |
| `--fact-bias 1` | 4 | 19 | 35 | 179 | healthy Y5, early_blight Y3, late_blight n1, septoria Y5, bacterial_spot Y4, yellow_leaf_curl n1 |
| `--fact-bias 2` | 4 | 20 | 34 | 143 | healthy Y6, early_blight Y3, late_blight n1, septoria Y5, bacterial_spot Y4, yellow_leaf_curl n1 |
| `--fact-bias 3` | 4 | 26 | 34 | 189 | healthy Y6, early_blight Y5, late_blight n1, septoria Y9, bacterial_spot Y4, yellow_leaf_curl n1 |
| `--fact-bias 2 --block-cause-words` | 4 | 20 | 32 | 150 | same per-topic result as `--fact-bias 2` |

Observations:
- Fact bias reduces dropped sentences by about 40% (56 -> 32-35) and fixes healthy and bacterial spot, but loses
  yellow leaf curl virus (7 grounded sentences at default -> 1).
- The output files contain 2-4 empty lines besides the JSON lines (one JSON line per topic + one summary line);
  a reader should skip non-JSON lines.

### 4.1 Raw text, default

early_blight (accepted, 5 grounded):
```
I. Brown spots with concentric rings in a bull's eye pattern with yellow margin on the photographed leaf.

II. The fungus attacks the foliage, causing characteristic leaf spots and blight.

III. Early blight is first observed on the plants as small, black lesions mostly on the older foliage.

IV. Remove and destroy crop debris. Follow crop rotation.

Note: I've kept the original meaning and details of the facts, but rewritten them in simple English as short sentences, without adding new information, changing the meaning, or altering the instructions.
```

late_blight (rejected: too_few_grounded_sentences:1):
```
I. The disease is caused by a fungus that infects the leaves and stems of the tomato plant.

II. The fungus causes black, water-soaked lesions on the leaves and stems.

III. The lesions expand rapidly, and the entire leaf becomes necrotic.

IV. The disease is caused by a fungus that infects the fruit, causing it to become soft, rot, and disintegrate.

V. The disease is caused by a fungus that causes the fruit to become greenish-brown and has a bad odor.

VI. The disease is caused by a fungus that infects the leaves and stems, and the fruit.

VII. The disease is caused by a fungus that infects the leaves and stems, and the fruit.
```

### 4.2 Raw text, `--block-cause-words` (best by acceptance)

early_blight: identical to the default text above (accepted, 5 grounded).

late_blight (accepted, 4 grounded):
```
I. The disease is a black rot on tomato leaves.
II. The disease is spreading rapidly.
III. The disease is killing the entire leaf.
IV. The disease is causing soft rot and fruit decay.
V. The disease is spreading through the air.
VI. The disease is killing the entire plant.
VII. The disease is spreading through the soil.
VIII. The disease is killing the entire plant.
```
Kept by the check: "The disease is a black rot on tomato leaves. The disease is killing the entire leaf. The disease is
spreading through the air. The disease is killing the entire plant."

### 4.3 Grounding check gaps exposed by `--block-cause-words`

The supporting source sentence of each kept late-blight sentence (computed with the same rule, `llm/grounding.py`):

| Kept sentence | Content words compared | Best source sentence | Correct? |
|---|---|---|---|
| The disease is a black rot on tomato leaves. | black, leaf (2/2) | "Water-soaked black lesions on leaves and stems." | **No** - "rot" (3 letters) is below the 4-letter minimum and is not compared; the source says lesions, not rot |
| The disease is killing the entire leaf. | kill, entire, leaf (3/3) | "It enlarges rapidly until entire leaves are killed and exposing all the fruits for infection." | yes |
| The disease is spreading through the air. | spread, through (2/2) | "Spreads through tiny air-borne spores ..." | yes ("air" is 3 letters and not compared, but the meaning holds) |
| The disease is killing the entire plant. | kill, entire (2/2) | same "entire leaves are killed" sentence | **No** - "plant" is a stop word, so leaf -> plant is not detected |

So the higher acceptance of `--block-cause-words` on late blight comes partly from short generic sentences with two
content words that pass through these gaps. The gaps are older than this branch.

## Step 5 - Llama 3B (`--llama-pte models/llama3_2_3b_instruct_8da4w.pte`)

| Config | Accepted (of 6) | Grounded | Dropped | Llama seconds | Per topic |
|---|---|---|---|---|---|
| default | 5 | 25 | 45 | 510 | healthy Y5, early_blight Y2, late_blight Y4, septoria n0, bacterial_spot Y10, yellow_leaf_curl Y4 |
| `--block-cause-words` | 5 | 25 | 45 | 744 | identical texts and decisions (the option never changed a token) |

Kept text, 3B default:
- early_blight: "Spots with rings in a circle pattern, yellow around the edge, and brown in the middle. It starts as small, black spots on old leaves."
- late_blight: "White spores can be seen on the leaves. This can spread quickly and kill the entire leaf, exposing the fruit to infection. A white fungus grows near the edge of a lesion on the underside of the leaves in damp and cloudy weather. Use a resistant tomato variety ..."

## Step 6 - streaming (`POST /api/analyse_stream`)

Server `--serve 8080 --bind 127.0.0.1`, photo P1 = `dist/krishirakshak-pi/photos/Tomato_leaf_late_blight.jpg`, timing loop
as given (times relative to the start of curl):

| Event | Time | Count |
|---|---|---|
| `result` (diagnosis + extracts, no Llama text) | 2.67 s | 1 |
| first `token` | 19.38 s | 117 token events |
| `final` | 37.90 s | 1 |

`final.data` compared with `POST /api/analyse` for the same photo, with `timings_ms` and the timing fields of
`llama.stats` removed: **identical**. Events are newline-delimited JSON objects `{"data": ..., "event": "result"}`,
`{"event": "token", "text": ...}`, `{"data": ..., "event": "final"}`. Server stopped afterwards.

## Step 7 - FP32 baseline

Export: not run on this PC - the FP32 export loads the full model in PyTorch, more memory than this laptop (about 9 GB for
WSL) can give without heavy swapping (an earlier Llama export on this machine stopped WSL). It was run in a Kaggle CPU
session (about 30 GB RAM) with the exact arguments of `llm/export_llama.sh fp32` (torch 2.14.1, torchao 0.18.0,
executorch 1.5.1, the same original Llama 3.2 1B Instruct checkpoint):

| Attempt | Result |
|---|---|
| 1 | failed after 12 s: `mismatched input 'get_bos_id' expecting <EOF>` (Hydra) - a quoting error in the run script (the metadata argument lost its `\"` escapes), not in the repository |
| 2 | **export succeeded** in about 12.5 minutes: `Saved exported program to llama3_2_1b_instruct_fp32.pte` (5,994,769,024 bytes) |

Evaluation on this PC: `$B --root . --eval-advisor demo --llama-pte <fp32 .pte> > /tmp/e_fp32.jsonl`, exit 0, peak RSS
6.17 GB, wall time 9377 s (mostly loading the 6 GB file under memory pressure; Llama seconds below).

| Llama 3.2 1B, default options | Accepted (of 6) | Grounded | Dropped | Llama seconds | Per topic (accepted, grounded) |
|---|---|---|---|---|---|
| INT4 8da4w (`/tmp/e_base.jsonl`) | 3 | 18 | 56 | 163 | healthy n0, early_blight Y5, late_blight n1, septoria Y4, bacterial_spot n1, yellow_leaf_curl Y7 |
| **FP32** (`/tmp/e_fp32.jsonl`) | **6** | 21 | 46 | 412 | healthy Y3, early_blight Y4, late_blight Y2, septoria Y4, bacterial_spot Y4, yellow_leaf_curl Y4 |

late_blight raw_text, INT4 (rejected: too_few_grounded_sentences:1): see step 4.1 (seven sentences, five of them "The
disease is caused by a fungus ...").

late_blight raw_text, FP32 (accepted, 2 grounded):
```
1. Black spots on leaves and stems.
2. Rapidly spreading lesions on leaves and stems.
3. White spots on leaves.
4. Greenish-brown fruit with soft rot and decay.
5. Leaves turn yellow and die.
6. Fruits turn green and decay.
7. Fruits turn green and decay.
```
Kept: "Black spots on leaves and stems. White spots on leaves."

Result: with the same prompt and options FP32 is accepted on all six diseases and does not invent causes ("caused by a
fungus" appears in the INT4 text only). The difference between the two runs is the weight quantization, so the
rejected INT4 answers come largely from quantization, not only from the 1B model size. Cost of FP32: 2.5x the Llama time
on this PC and about 6 GB of memory (the Pi 5 has 8 GB).

`python tools/perf_model.py --pte <fp32 .pte>` (size check):
```
== Llama weights ==
layers 16, dim 2048, heads 32 (KV heads 8), feed-forward 8192, vocabulary 128256
  layers           580.0 MiB
  output_layer    1002.0 MiB
  embedding        156.6 MiB
  norms              0.3 MiB
  .pte file       5717.1 MiB
  WARNING: no hypothesis within 5 % of the file size; the predictions below are approximate
  NOTE: the output layer looks unquantized (fp32); it is read on every token
```
The script's size hypotheses are built for quantized exports; for FP32 they do not fit (expected).

Related measurement (same day, separate Kaggle run, not part of this branch): the same 1B model in FP16 PyTorch, on the
same six diseases with three prompt variants each, was accepted on 17 of 18 prompts, consistent with this result.

## Step 8 - Pi bundle

| Check | Result |
|---|---|
| ARM configure (`-DCMAKE_TOOLCHAIN_FILE=cpp/arm-toolchain.cmake`, CMake 3.31.10) | exit 0 |
| ARM build | exit 0, 13/13 steps, 0 warnings, 0 errors, 0 undefined references |
| `build/arm/krishirakshak` | ELF 64-bit LSB pie executable, ARM aarch64 |
| `bash cpp/package_pi.sh` | exit 0, `dist/krishirakshak-pi` = **2.9 GB** (Llama 1B and 3B .pte, tokenizer, 3B params, FP32 + INT8 ONNX models); not copied anywhere |
