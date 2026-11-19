# IndicTrans2 offline translation experiment

## Scope and decision

This experiment runs in WSL2 on the laptop CPU, which serves as the functional
simulator. It is not an ARM emulator or a native Raspberry Pi performance test.
The project owner explicitly requested WSL-only downloads and execution, with
results copied to `C:\Users\ajink\Downloads\IndicTrans2_results`. No model,
package or result was downloaded to the Pi and no inference ran there. An initial
read-only connectivity check, before that clarification, found a reachable Pi 5.

Do not enable these unreviewed translations for farmer use. A successful number
check does not prove correct meaning. The late-blight smoke test already exposed
repetitive Punjabi output, and technical disease vocabulary needs human review.
The implementation suppresses numeric, protected-entity, truncation, empty-output
and repeated-phrase failures. Meaning, negation, units and farmer comprehension
still require fluent-speaker and domain review for all nine languages.

The standard CTranslate2 Transformers converter does not support this checkpoint's
`IndicTransConfig`. The tested fallback is PyTorch dynamic INT8 on Linear layers.
It is not a CTranslate2 model, does not provide a deployable C++ artifact, and its
peak memory exceeds the approximate 600 MB translation budget. C++ integration
below is a proposal pending conversion and preprocessing parity work.

## Verified model and dependencies

- Model: [AI4Bharat IndicTrans2 En-Indic distilled 200M](https://huggingface.co/ai4bharat/indictrans2-en-indic-dist-200M).
  Revision: `2cfd0a20057756d756bf3e53528f492afc52f91a`. The loaded model reports
  211,776,512 unique parameters. Only this distilled model was loaded; no Llama
  model or 1B translation model was loaded.
- Licence: MIT, verified in the downloaded checkpoint's `LICENSE` and the
  [upstream repository](https://github.com/AI4Bharat/IndicTrans2/blob/main/LICENSE).
  Retain its copyright and permission notice in any model distribution.
- Tokenizer and model require `trust_remote_code=True`. Download the pinned
  revision once, inspect its Python files, then load from the local directory with
  `local_files_only=True`, `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`.
- Processing: `from IndicTransToolkit.processor import IndicProcessor`, with
  `inference=True`. The repository linked by AI4Bharat is
  [VarunGumma/IndicTransToolkit](https://github.com/VarunGumma/IndicTransToolkit),
  not `AI4Bharat/IndicTransToolkit`. Use version 1.1.1 for this experiment.
- Runtime pins are in `tools/indictrans2_requirements.txt`. The measured environment
  uses PyTorch 2.5.1+cu121 on CPU, Transformers 4.51.3 and four threads. The clean
  reproduction recipe installs the CPU-only PyTorch build; allocator/import RSS
  may differ. TensorFlow and Flax imports are disabled.
- Citation: Gala et al., "IndicTrans2: Towards High-Quality and Accessible Machine
  Translation Models for all 22 Scheduled Indian Languages", Transactions on
  Machine Learning Research (2023), [paper](https://openreview.net/forum?id=vfT4YuzAYA).

| UI code | IndicTrans2 target code |
| --- | --- |
| hi | hin_Deva |
| te | tel_Telu |
| mr | mar_Deva |
| kn | kan_Knda |
| ta | tam_Taml |
| bn | ben_Beng |
| gu | guj_Gujr |
| or | ory_Orya |
| pa | pan_Guru |

All use source `eng_Latn`. Codes are verified against the
[upstream language list](https://github.com/AI4Bharat/IndicTrans2#indictrans2).

## Reproduce in WSL

Run from the repository root. All model files and Python environments belong
outside this repository. Access to the gated model must already be approved on
Hugging Face; use an existing login or an environment token, never a committed key.

```bash
bash tools/setup_indictrans2_wsl.sh /home/studinstru/ARM_AgriTech/indictrans2_assets
source /home/studinstru/ARM_AgriTech/indictrans2_assets/venv/bin/activate
export TRANSLATION_MODEL=/home/studinstru/ARM_AgriTech/indictrans2_assets/model
python tools/test_translate_indictrans2.py
python tools/translate_indictrans2.py \
  --model-dir "$TRANSLATION_MODEL" \
  --input results/pi5_bench/2026-11-18_llama1b_lora/lora_Tomato_leaf_late_blight.json \
  --output results/indictrans2/smoke_all_languages.json
python tools/eval_indictrans2.py --model-dir "$TRANSLATION_MODEL"
python tools/translate_indictrans2.py \
  --model-dir "$TRANSLATION_MODEL" --repeat 3 \
  --input results/pi5_bench/2026-11-18_llama1b_lora/lora_Tomato_leaf_late_blight.json \
  --output results/indictrans2/bench_fp32.json
python tools/translate_indictrans2.py \
  --model-dir "$TRANSLATION_MODEL" --backend dynamic-int8 --repeat 3 \
  --input results/pi5_bench/2026-11-18_llama1b_lora/lora_Tomato_leaf_late_blight.json \
  --output results/indictrans2/bench_dynamic_int8.json
python tools/report_indictrans2.py
python tools/check_repo.py
python tools/export_indictrans2_results.py /mnt/c/Users/ajink/Downloads/IndicTrans2_results
```

Run benchmarks sequentially with no other inference jobs. Exit 0 means no
automatic failures, exit 2 means completed with withheld/error sentences, and
exit 1 means initialization or input failure. Exit 2 is expected for the observed
Punjabi repetition; inspect JSON rather than treating that exit as a crash.

For individual sentences use `--text 'Remove infected leaves.'`. For custom JSON,
use a list of objects with `id`, `topic`, `text`, `accepted`, optional `section`,
`product`, `dose`, `protected_terms`, and optional `source` provenance. The CLI
also reads native Pi answer files and the held-out list's `kept` fields. Raw
`text` in an unaccepted held-out answer is never substituted for `kept`.

`--languages hi te` limits output languages; omitting it selects all nine.
`--protect 'Product name'` supplies additional verbatim terms. The built-in
glossary covers the evaluation KB's biological products and named cultivars;
new KB products must be supplied explicitly. This is not a general product-name
recognizer.

The repository review CSV is ASCII, using literal Unicode escapes in its
translation column. The Windows export includes a BOM-marked UTF-8 review CSV
and a self-contained `review.html` showing the actual scripts. The HTML is a
review artifact and displays withheld candidates as well; it is not the app UI.
The export refuses to overwrite an existing destination.

The measured session used `/tmp/indictrans2_venv/bin/python`. A persistent copy
of the downloaded checkpoint is at
`/home/studinstru/ARM_AgriTech/indictrans2_assets/model`; its file sizes and hashes
are in `model_manifest.json`. The setup script recreates an independent persistent
environment after a reboot. The Python environment and weights are not exported
to Windows; only results, the report and review files are exported.

## Evaluation protocol

`inventory.json` records input SHA-256 hashes and the reference branch commit.
The evaluator pins `kb-translations` at
`faa26afdfe7e96e6124fcf652c6264872ad5acb1`; use `--reference-revision` explicitly
to evaluate a later snapshot.
There are five accepted Pi answers and 16 accepted answers among the 18 held-out
rows, for 21 answers. One held-out row has empty `kept`; another has a single kept
sentence but `accepted=false`. Both are excluded and listed with their reason.
The reference branch has 61 rows: exactly 38 non-chemical extracts and 23 chemical
rows. Chemical rows are excluded before their text is read or tokenized.

The evaluation caches identical sentence/language/protected-term inputs. A
`cache_hit=true` sentence records lookup time rather than model inference time;
these records are never used for performance claims. `--resume` validates the
input hashes, model revision and inference settings before keeping completed
answer records. This run resumed after 15 answers to correct percentage-span
spacing before processing the KB; previously completed answers contained no
affected protected spans. All dedicated speed benchmarks disable this cache.

Sentence splitting calls `Grounding.split_sentences` directly, including its
semicolon/newline and abbreviation behavior. Each output retains answer ID,
topic, language, sentence index, English, candidate translation, number check,
protected-text check, repetition check, elapsed seconds, status and display text.
Older Llama files do not record the supporting extract for each kept sentence.
The tool reconstructs the first highest-overlap guard match using the saved
facts and marks it `reconstructed_guard_match`, or records `unresolved`. It does
not invent authoritative provenance. KB rows retain their reference extract index.
Held-out grounding facts contain section/text only, so reconstructed source IDs
can remain null even when the supporting English source sentence is identified.

Numbers are compared as multisets of complete numeric tokens, including decimal
and grouping separators, ranges, signs and multiplicity. ASCII or the selected
target script's decimal digits are accepted and the script is recorded. Added,
missing, changed or wrong-script numbers fail. Range dash variants and spacing
are normalized; numeric formatting changes such as `1,000` to `1000` conservatively
fail. This check cannot establish that a quantity remains attached to the right
action, or that a negation, unit or disease term is correct.

Product names and dose spans are replaced by email-shaped entities before
IndicProcessor runs. Its entity masking keeps those literals out of translation;
the exact original bytes are restored afterwards. Missing or repeated entities
withhold the sentence. No chemical-row text is passed to the model, including in
custom input. Chemical output stays verbatim. Biological product/dose protection
also applies to non-chemical extracts. The protection can reduce fluency and
must be examined in review.

Quality uses sacrebleu chrF, default character order 6, word order 0, beta 2,
case-sensitive. The stored metric signature identifies the version/options.
Reference agreement is computed at the whole-extract level after concatenating
aligned sentence candidates. Failed candidates remain in the research score;
they never enter `display_text`. Neither reference translations nor new
translations are reviewed. chrF is an agreement signal, not an accuracy score.
All-sentence number rates are reported alongside number-bearing-only rates so
sentences without numbers do not hide weaknesses. The review sheet selects one
accepted answer for each of six demo topics, preferring Pi answers, for 54 rows.

<!-- QUALITY_RESULTS -->

The evaluation completed 1431 aligned sentence-language records: 35 withheld and 0 execution errors. The fluent-speaker review sheet has 54 rows (six demo topics in nine languages).

| Language | Reference chrF | Number passes / checked | Number-bearing pass rate | Withheld | Errors |
| --- | ---: | ---: | ---: | ---: | ---: |
| hi | 44.91 | 158/159 (99.37%) | 96.77% | 1 | 0 |
| te | 57.04 | 157/159 (98.74%) | 93.55% | 2 | 0 |
| mr | 55.50 | 158/159 (99.37%) | 96.77% | 1 | 0 |
| kn | 58.70 | 153/159 (96.23%) | 80.65% | 6 | 0 |
| ta | 62.97 | 153/159 (96.23%) | 80.65% | 6 | 0 |
| bn | 58.42 | 152/159 (95.60%) | 77.42% | 7 | 0 |
| gu | 56.91 | 158/159 (99.37%) | 96.77% | 1 | 0 |
| or | 44.75 | 152/159 (95.60%) | 77.42% | 7 | 0 |
| pa | 55.71 | 158/159 (99.37%) | 96.77% | 4 | 0 |

Each language is scored against all 38 non-chemical reference extracts. Neither side is reviewed. Withheld counts include numeric, literal, truncation and repetition failures; some conservative numeric failures are formatting changes.

<!-- END_QUALITY_RESULTS -->

## Speed, memory and conversion

Measurements use WSL2 x86_64 on an Intel Core i5-12500H with about 9.7 GiB RAM
visible to WSL, CPU only, batch size 1, beam size 5 and four intra-op threads.
One thread is used for inter-op scheduling. The benchmark is the same accepted
late-blight answer, two sentences, separately translated into each language.
Each backend gets a fresh process; three traversals expose first-use and warm
behavior. Load time includes imports, tokenizer/model load and, for INT8,
in-place dynamic quantization. No downloads occur during a measured run.
The operating-system file cache is warm; these are not cold-boot load times.
Two warm samples per language are descriptive measurements, not confidence
intervals or a guarantee for other answer lengths.

Peak RSS is Linux `ru_maxrss` for the complete process lifetime in MiB, including
model loading, quantization and inference. It is not just weight size or a
steady-state estimate. Dynamic quantization retains FP32 embeddings and must
first load FP32 weights; it is not guaranteed to lower this peak.

<!-- SPEED_RESULTS -->

| WSL backend | Load seconds | Load/quantization peak MiB | Overall peak MiB |
| --- | ---: | ---: | ---: |
| fp32 | 7.013 | 710.4 | 1673.3 |
| dynamic-int8 | 8.627 | 1792.7 | 1971.7 |
| CTranslate2 INT8 | Not available | Not measured | Not measured |

| Language | FP32 first / warm s | Dynamic INT8 first / warm s | FP32/INT8 chrF | Pi INT8 scenario s (not measured) |
| --- | ---: | ---: | ---: | ---: |
| hi | 0.974 / 1.102 | 0.757 / 1.423 | 80.73 | 2.85-7.12 |
| te | 0.727 / 1.071 | 0.909 / 1.022 | 63.40 | 2.04-5.11 |
| mr | 0.704 / 1.096 | 0.927 / 1.259 | 100.00 | 2.52-6.30 |
| kn | 0.721 / 1.291 | 0.865 / 0.994 | 89.77 | 1.99-4.97 |
| ta | 0.762 / 1.593 | 0.944 / 0.924 | 78.24 | 1.85-4.62 |
| bn | 0.734 / 1.525 | 0.976 / 0.932 | 82.91 | 1.86-4.66 |
| gu | 0.744 / 1.543 | 1.050 / 1.070 | 52.36 | 2.14-5.35 |
| or | 0.689 / 1.348 | 0.796 / 0.849 | 100.00 | 1.70-4.24 |
| pa | 7.261 / 14.687 | 13.470 / 14.562 | 89.82 | 29.12-72.81 |

The FP32/INT8 comparison covers only two late-blight sentences per language. Several languages change substantially, so close agreement is not demonstrated across the dataset. Punjabi's slow repetitive candidate is withheld, but its generation time remains included. Both measured backends exceed 600 MB peak RSS.

<!-- END_SPEED_RESULTS -->

The direct conversion attempt was:

```bash
HF_MODULES_CACHE=/tmp/indictrans2_modules ct2-transformers-converter \
  --model "$TRANSLATION_MODEL" --output_dir /tmp/indictrans2_ct2 \
  --quantization int8 --trust_remote_code
```

It fails with `ValueError: No conversion is registered for the model configuration
IndicTransConfig`. The full error is in `results/indictrans2/failures.json`.
[CTranslate2's supported Transformers configurations](https://opennmt.net/CTranslate2/guides/transformers.html)
do not include IndicTrans. AI4Bharat documents
[CT2 inference](https://github.com/AI4Bharat/IndicTrans2#ct2-inference) with an
already ported checkpoint, plus a Fairseq checkpoint layout; that documentation
does not make the Hugging Face custom architecture convertible by this command.
The authorized PyTorch dynamic INT8 fallback was used instead of downloading a
different or larger model. ONNX export was not needed for this fallback.

No native Pi inference was performed, per the owner's WSL-only instruction.
`bench_summary.json` includes a clearly labelled 2x-5x laptop slowdown scenario
for planning, not a calibrated Pi prediction. CPU kernels, ARM INT8 support,
thermal throttling and co-resident runtimes can change both time and memory.
The approximately 3 s/answer and 600 MB budgets are not demonstrated on Pi.

`tools/bench_translate_pi.sh` is a future manual, offline-only harness for the
tested PyTorch backends. It installs and downloads nothing. It does not pretend
to benchmark CTranslate2 without a successfully converted model. A future CT2
run needs a prevalidated distilled CT2 artifact and an aarch64 wheel installed
in a separate environment: `python3 -m venv /tmp/translation_pi_venv`, then
`/tmp/translation_pi_venv/bin/pip install --only-binary=:all: ctranslate2==4.6.0`.
That command is documentation only and was not executed on the Pi. Check Python
wheel compatibility before deployment; the inspected Pi has Python 3.13.5.
[CTranslate2 documents Linux aarch64 wheel support](https://opennmt.net/CTranslate2/installation.html).

## Proposed C++ application stage

1. Generate English with Llama, then run the existing grounding check unchanged.
2. Extend the guard result to save the supporting extract ID and exact source
   sentence/span alongside every kept sentence. Do not reconstruct provenance
   heuristically inside the production UI.
3. For a chosen language, use a reviewed translation of the exact supporting KB
   extract when available. Review metadata must be per language and extract
   version, with source-text hash, reviewer and review date. Existing global
   flags and unreviewed branch strings do not establish that approval. If the
   whole extract replaces a paraphrase, label it as the source extract and
   deduplicate repeated extracts; do not imply it is a verbatim Llama translation.
4. Otherwise translate the kept English sentence, protecting products and doses.
   Apply all checks after postprocessing. Suppress a failed target sentence and
   retain the English/source fallback. Label accepted target output
   `machine translated`; number checks alone do not justify a reviewed label.
5. Keep the original chemical spray table on its existing code path, with product
   names and doses exactly as published. It never enters the translator.

Run translation sequentially after Llama and outside the UI thread. Suspend
ExecuTorch generation and ONNX Runtime inference before using a single CT2
translator with one inter-thread worker and four intra-op threads. Avoid three
runtimes each occupying all cores. Use a bounded one-answer queue, cancellation
on a new diagnosis/language, cached approved results keyed by model/KB versions,
and explicit generation/input limits. Translation errors should not hide the
diagnosis or original published advice. Benchmark the co-resident process as
well as isolated translation; 1.1 GB Llama plus a theoretical translator weight
size is not a measured whole-app memory budget on an 8 GB Pi.

The intended native implementation uses CTranslate2's C++ `Translator` API and
SentencePiece, once the distilled model has a validated converter. A correct
conversion must preserve separate source/target dictionaries, tied target
embeddings/output projection, 18 encoder/18 decoder layers, pre-layer norms,
embedding layer norms, GELU, scaled embeddings and sinusoidal positions. Test FP32 versus converted
INT8 on all nine languages, not just a successful load. Hugging Face source
token IDs are not automatically SentencePiece IDs; apply the saved dictionary
mapping and the converter's BOS/EOS conventions.

Port and test these IndicProcessor 1.1.1 steps before claiming C++ parity:

- Punctuation/whitespace normalization, digit normalization, regex-based entity
  masking, and sentence-local placeholder maps. Add application-owned literal
  protection before these steps, and verify restoration after all processing.
- English Moses punctuation normalization and tokenization without HTML escaping;
  prepend `eng_Latn` and the exact target language tag before source tokenization.
- Separate source and target SentencePiece models and vocabularies, correct
  special tokens, source length validation and target decoding limits.
- Target placeholder restoration, Devanagari-to-target transliteration and Indic
  detokenization, including the toolkit's Odia-specific character correction.
  Hindi/Marathi retain Devanagari. Entity maps must never leak between sentences.
- Unicode-aware number checks and the application's verbatim protection,
  repetition and error handling. Golden tests should compare preprocessed tokens,
  decoded candidates and final strings with this Python reference.

SentencePiece alone does not implement IndicProcessor. Port the required English
and nine-language paths explicitly, preserving upstream licences for copied code.
Do not import a Python interpreter into the C++ app and call that a native CT2 path.

## aarch64 build plan and size planning

The following is a build proposal, not a tested artifact. Use matching target
sysroot libraries; disable x86 MKL and CUDA. Pin upstream releases and vendor
their notices when implementing it. An example external dependency build layout:

Prerequisites in WSL are CMake, Make, Git, `gcc-aarch64-linux-gnu`,
`g++-aarch64-linux-gnu`, and a matching aarch64 C++/OpenMP runtime sysroot.
Nothing in this build plan installs software or downloads files onto the Pi.

```bash
export TRANSLATION_NATIVE=/tmp/indictrans2_native
mkdir -p "$TRANSLATION_NATIVE"
git clone --recursive --branch v4.6.0 https://github.com/OpenNMT/CTranslate2.git "$TRANSLATION_NATIVE/ct2"
git clone --branch v0.2.1 https://github.com/google/sentencepiece.git "$TRANSLATION_NATIVE/sentencepiece"
cmake -S "$TRANSLATION_NATIVE/ct2" -B "$TRANSLATION_NATIVE/build_ct2" \
  -DCMAKE_TOOLCHAIN_FILE="$PWD/cpp/arm-toolchain.cmake" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$TRANSLATION_NATIVE/stage" \
  -DWITH_MKL=OFF -DWITH_CUDA=OFF -DWITH_DNNL=OFF -DWITH_RUY=ON \
  -DOPENMP_RUNTIME=COMP -DBUILD_TESTS=OFF -DBUILD_CLI=OFF
cmake --build "$TRANSLATION_NATIVE/build_ct2" -j4
cmake --install "$TRANSLATION_NATIVE/build_ct2"
cmake -S "$TRANSLATION_NATIVE/sentencepiece" -B "$TRANSLATION_NATIVE/build_spm" \
  -DCMAKE_TOOLCHAIN_FILE="$PWD/cpp/arm-toolchain.cmake" \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$TRANSLATION_NATIVE/stage" \
  -DSPM_ENABLE_SHARED=ON -DSPM_BUILD_TEST=OFF
cmake --build "$TRANSLATION_NATIVE/build_spm" -j4
cmake --install "$TRANSLATION_NATIVE/build_spm"
```

Check target INT8 capability and backend selection; a successful cross-link is
not a demonstration of useful ARM performance. The installed target libraries
must be supplied via an appropriate target `CMAKE_PREFIX_PATH`/sysroot when
building the app, and required shared libraries packaged beside it. Inspect ELF
architecture with `file`/`readelf`, strip release binaries, then measure on-device
RSS and latency after a later explicit deployment decision.

Build flags follow the pinned
[CTranslate2 CMake options](https://github.com/OpenNMT/CTranslate2/blob/v4.6.0/CMakeLists.txt)
and [SentencePiece CMake options](https://github.com/google/sentencepiece/blob/v0.2.1/CMakeLists.txt).
Ruy supplies an ARM-capable matrix backend; do not disable MKL without selecting
a replacement backend.

Planning estimates only: a stripped CT2 CPU shared library may be roughly
10-40 MB, SentencePiece about 1-3 MB, and added application/preprocessing code
about 1-5 MB, excluding ICU/other dependencies. The downloaded tokenizer models
and dictionaries together are about 8 MB. A converted INT8 model could occupy
roughly 250-550 MB depending on embedding quantization and duplicated tied
weights. These are not measured build sizes or a 600 MB RSS guarantee. Record
actual file sizes and dependency closure when the converter/build exists.

## Review and release criteria

All nine languages need fluent-speaker review before a farmer-facing demo.
The WSL review preview may be used to collect that review, with unreviewed status
visible. Punjabi requires decoding/terminology investigation before even a
smooth live preview. Existing KB machine translations also need review before
they can be used as the preferred reviewed-extract path.

Review each selected answer for source meaning, disease vocabulary, negation,
quantities, preserved product/dose spans and understandable farmer language.
Record `yes`/`no` in both review columns; blank is not approval. Expand review to
number-bearing and withheld extracts before release. Fix source-English errors
upstream rather than expecting translation to correct them. No language is
certified by a chrF score, numeric pass rate, or the absence of a runtime error.

Before native integration, require a supported 200M conversion, C++ preprocessing
parity, target-device measurements within the agreed budget or a revised budget,
and reviewed language content. Until then use English accepted text and published
spray rows, or genuinely reviewed KB translations where available.
