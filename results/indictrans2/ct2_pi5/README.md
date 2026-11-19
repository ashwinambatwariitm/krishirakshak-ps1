# IndicTrans2 on CTranslate2: Raspberry Pi 5 results

Translation of the English advice into 9 Indian languages (hi, te, mr, kn, ta, bn, gu, or, pa) with
IndicTrans2 en-indic distilled 200M, run on the CTranslate2 runtime with INT8 weights.
All numbers below were measured on the Raspberry Pi 5 (8 GB, Raspberry Pi OS, no throttling,
54-59 C) unless marked otherwise.

## Why CTranslate2

The PyTorch evaluation (`tools/translate_indictrans2.py`, `results/indictrans2/summary.json`) peaked at
1.63 GiB (FP32) and 1.93 GiB (dynamic INT8) and looped on Punjabi (12.6 s for one answer).
The CTranslate2 Transformers converter rejects the IndicTrans2 configuration, and the official
fairseq/CTranslate2 archive is gated, so `tools/convert_indictrans2_ct2.py` converts the public Hugging Face
checkpoint directly (the model is a fairseq pre-norm Transformer). The converted FP32 model gives the same
per-token log-probabilities as the Hugging Face model (largest difference 6e-6).

| | PyTorch FP32 (WSL) | CTranslate2 INT8 (Pi 5) |
|---|---|---|
| Model on disk | 0.8 GB | 210 MB |
| Peak memory | 1.63 GiB | 370-440 MB |
| Punjabi late-blight answer | 12.6 s (loop) | 0.8-1.5 s, no loop |
| Loops / truncated outputs (1,242 sentence-language pairs) | 2 | 0 / 0 |

## Threads and batching (Python runtime, `python_layout_*.json`)

Same 108 Llama answers (12 per language, 270 sentences), INT8:

| Layout | Median per answer | p95 | Worst | Total | Peak memory |
|---|---|---|---|---|---|
| A: 1 worker x 2 threads, one sentence at a time | 1.80 s | 3.30 s | 5.0 s | 212 s | 416 MB |
| B: 4 workers x 1 thread, one sentence each | 2.04 s | 4.10 s | 6.2 s | 252 s | 623 MB |
| C: 2 workers x 2 threads | 2.41 s | 4.51 s | 6.7 s | 285 s | 495 MB |
| D: 1 worker x 4 threads, whole answer in one batch | 8.56 s | 12.4 s | 19.6 s | 919 s | 447 MB |
| **E: 1 worker x 2 threads, whole answer in one batch** | **1.19 s** | **1.83 s** | **3.1 s** | **133 s** | **442 MB** |

All layouts produce identical translations. Decoding is limited by memory bandwidth (every step reads the
weights), so one batch per answer is best; 4 OpenMP threads are several times slower on the Pi 5
(single sentence: 0.48 s with 2 threads, 3.68 s with 4). The pipeline uses layout E.

## C++ translator (`cpp/src/translator.cpp`)

The C++ translator uses the CTranslate2 C++ API and a C++ port of the Python text processing
(`cpp/src/indic_text.cpp`; byte-identical to the Python reference on 3,609 cases, `cpp/tests/indic_text_test.cpp`).

Same 36 answers (4 per language), 2 threads, whole answer in one batch (`linkcheck*.json`):

| | Median | p95 | Total | Peak memory | Memory after load | Model load |
|---|---|---|---|---|---|---|
| Python | 1.23 s | 1.99 s | 48.5 s | 442 MB | 406 MB | ~0.9 s |
| C++ (final build) | 1.21 s | 1.96 s | 48.0 s | 371 MB | 244 MB | 0.2 s |

Translations are word-for-word identical to the Python runs on the Pi (270/270 sentences with the final
library build, 99/99 in the link check).

Two build details matter (`cpp/tools/build_translation_deps.sh`):

1. **Build CTranslate2 like the official wheel** (OpenBLAS 0.3.21 TARGET=ARMV8, generic Armv8 code).
   A build tuned for the Cortex-A76 (OpenBLAS 0.3.28 CORTEXA76, -mcpu=cortex-a76) changed 28 of 270
   translations (different floating-point summation order, beam search on near ties) and was not faster
   (`cpp_108_answers_cortexa76_build.json` vs `cpp_108_answers_wheel_build.json`).
2. **Link libctranslate2 with -Bsymbolic.** The krishirakshak binary also contains ExecuTorch; its static
   libraries export their own copies of C++ standard-library template code, and the dynamic linker then
   made libctranslate2 use those: 1.70 s instead of 1.21 s median per answer (`linkcheck2_*.json`).
   OpenMP wait policy and the libgomp version made no difference (`linkcheck_*.json`).

## INT8 output differs between machines

INT8 kernels differ between x86 (WSL) and Arm: the same model and input give the same text on the Pi in
only 64% of the sentences compared with WSL, and INT8 matches FP32 in 55%. The review by fluent speakers
must therefore use translations produced on the Pi (`python_all_sentences_int8_2threads.json`, identical
to the C++ output), not the PyTorch FP32 review sheet.

Machine translations are not reviewed yet. Known errors seen in the outputs: "necrotic" translated as
"impure" (Hindi), "marginal" as "retail" (Marathi), "vegetative" as "botanical" (Kannada),
"bull's eye" translated literally.

## Files

| File | Content |
|---|---|
| `python_latency_int8_{2,4}threads.json` | late-blight answer, 9 languages, warm median of 5 runs |
| `python_all_sentences_int8_2threads.json` | all 1,242 sentence-language pairs (Pi output for review) |
| `python_layout_{A..E}.json` | threading/batching layouts, 108 answers |
| `cpp_108_answers_{wheel,cortexa76}_build.json` | C++ translator, two CTranslate2 builds |
| `linkcheck*_*.json` | C++ with/without ExecuTorch, -Bsymbolic, OpenMP settings, 36 answers |
