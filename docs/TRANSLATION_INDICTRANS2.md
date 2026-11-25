# IndicTrans2 translation

KrishiRakshak shows its advice in 10 languages. The knowledge base and all screen labels were translated in advance.
Llama's answer is written in English, checked sentence by sentence against the sources, and only the accepted English
text is translated live on the Raspberry Pi 5 by IndicTrans2. This page describes the deployed translator, the
model, and the first experiment that led to it. Section A7 of the technical report has the summary.

## Deployed design

- Model: IndicTrans2 English-to-Indic distilled 200M (AI4Bharat), converted from the public Hugging Face checkpoint
  with `tools/convert_indictrans2_ct2.py` to CTranslate2 4.6.0 with INT8 weights (210 MB on disk). The standard
  CTranslate2 converter rejects this checkpoint, so the converter maps the weights directly. The converted FP32
  model gives the same per-token log-probabilities as the Hugging Face model (largest difference 6e-6).
- Runtime: the C++ program on the Pi (`cpp/src/translator.cpp`) with a C++ port of the text processing
  (`cpp/src/indic_text.cpp`, byte-identical to the Python toolkit on 3,609 cases, `cpp/tests/indic_text_test.cpp`).
  The dependencies are built by `cpp/tools/build_translation_deps.sh`.
- Settings: 2 threads and the whole answer as one batch. With 4 threads one sentence took 3.68 s instead of
  0.48 s, because decoding is limited by memory bandwidth. libctranslate2 is linked with -Bsymbolic (1.21 s instead
  of 1.70 s median per answer next to ExecuTorch).
- Safeguards: disease and pest names are protected and replaced by their reviewed local names, a sentence that loops,
  hits the length limit or loses a placeholder is withheld and shown in English, and every translated block has
  "Show English".

Measured on the Raspberry Pi 5 ([results/indictrans2/ct2_pi5/README.md](../results/indictrans2/ct2_pi5/README.md)):

| | Result |
| --- | --- |
| C++ translator, 36 answers (4 per language) | median 1.21 s per answer, p95 1.96 s, peak memory 371 MB |
| Same answers in Python on the Pi | median 1.23 s, peak memory 442 MB, identical translations |
| Loops or truncated outputs, 1,242 sentence-language pairs | 0 / 0 |
| Final end-to-end test, 360 runs ([results/e2e_pi5](../results/e2e_pi5/README.md)) | median 1.09 s per answer (0.70-5.49 s), all 67 accepted Llama sentences translated in every language |

Review status (as in the technical report): Marathi was reviewed and corrected by a native speaker in the team,
Hindi in part. Telugu, Kannada, Tamil, Bengali, Gujarati, Odia and Punjabi are machine translations not yet reviewed
by native speakers. The automatic checks prove that numbers, names and script are kept. They do not prove that the
meaning is right.

## Verified model and dependencies

- Model: [AI4Bharat IndicTrans2 En-Indic distilled 200M](https://huggingface.co/ai4bharat/indictrans2-en-indic-dist-200M).
  Revision: `2cfd0a20057756d756bf3e53528f492afc52f91a`. The loaded model reports 211,776,512 unique parameters.
- Licence: MIT, verified in the downloaded checkpoint's `LICENSE` and the
  [upstream repository](https://github.com/AI4Bharat/IndicTrans2/blob/main/LICENSE). Its copyright and permission
  notice are kept with the model release.
- Tokenizer and model require `trust_remote_code=True`. The pinned revision is downloaded once, its Python files
  inspected, and it is then loaded from the local folder with `local_files_only=True`, `HF_HUB_OFFLINE=1` and
  `TRANSFORMERS_OFFLINE=1`.
- Text processing: `IndicProcessor` from
  [VarunGumma/IndicTransToolkit](https://github.com/VarunGumma/IndicTransToolkit) 1.1.1, with `inference=True`
  (ported to C++ for the Pi).
- Python pins for the evaluation tools are in `tools/indictrans2_requirements.txt`.
- Citation: Gala et al., "IndicTrans2: Towards High-Quality and Accessible Machine Translation Models for all 22
  Scheduled Indian Languages", Transactions on Machine Learning Research (2023),
  [paper](https://openreview.net/forum?id=vfT4YuzAYA).

| Language | App code | IndicTrans2 target code |
| --- | --- | --- |
| Hindi | hi | hin_Deva |
| Telugu | te | tel_Telu |
| Marathi | mr | mar_Deva |
| Kannada | kn | kan_Knda |
| Tamil | ta | tam_Taml |
| Bengali | bn | ben_Beng |
| Gujarati | gu | guj_Gujr |
| Odia | or | ory_Orya |
| Punjabi | pa | pan_Guru |

All use the source code `eng_Latn`. Codes are checked against the
[upstream language list](https://github.com/AI4Bharat/IndicTrans2#indictrans2).

## First experiment: PyTorch on the development PC (18 Nov 2026)

The first experiment ran the Hugging Face PyTorch model on the development PC (WSL2, Intel Core i5-12500H, CPU only).
It measured quality, speed and memory and showed why PyTorch was not suitable for the Pi. Its files are in
`results/indictrans2/` and are kept as a record.

### Reproduce

Model files and Python environments stay outside the repository. Access to the gated model must be approved on
Hugging Face.

```bash
bash tools/setup_indictrans2_wsl.sh $HOME/indictrans2_assets
source $HOME/indictrans2_assets/venv/bin/activate
export TRANSLATION_MODEL=$HOME/indictrans2_assets/model
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
```

Exit 0 means no automatic failures, exit 2 means the run completed with withheld sentences (expected for the
Punjabi repetition), exit 1 means an initialisation or input failure.

### Evaluation protocol

- Inputs: 5 accepted Pi answers and 16 accepted held-out answers (21 answers). `inventory.json` records the input
  SHA-256 hashes and the commit of the reference knowledge-base snapshot used for scoring.
- Reference: 38 non-chemical knowledge-base extracts with earlier machine translations. The 23 chemical rows are
  excluded before their text is read, and chemical names and doses are never translated.
- Checks per sentence: numbers (every number of the English text must appear unchanged), protected product names
  and doses (masked before translation and restored byte for byte), repetition and truncation. A failed sentence is
  withheld.
- Quality: sacrebleu chrF (character order 6, word order 0, beta 2) against the reference. chrF measures agreement
  with an earlier machine translation, not accuracy.

<!-- QUALITY_RESULTS -->

The evaluation completed 1431 aligned sentence-language records: 35 withheld and 0 execution errors. The review sheet of that run (`results/indictrans2/review_sheet.csv`, PyTorch FP32 output, kept as a record) has 54 rows (six demo topics in nine languages).

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

Each language is scored against all 38 non-chemical reference extracts. Neither side was reviewed at the time. Withheld counts include numeric, literal, truncation and repetition failures. Some conservative numeric failures are formatting changes.

<!-- END_QUALITY_RESULTS -->

### Speed and memory (development PC)

Batch size 1, beam size 5, four threads, the same two-sentence late-blight answer in each language, three passes per
backend in a fresh process. Peak memory is the whole process (Linux `ru_maxrss`), including loading and quantization.

<!-- SPEED_RESULTS -->

| WSL backend | Load seconds | Load/quantization peak MiB | Overall peak MiB |
| --- | ---: | ---: | ---: |
| fp32 | 7.013 | 710.4 | 1673.3 |
| dynamic-int8 | 8.627 | 1792.7 | 1971.7 |
| CTranslate2 INT8 | Not convertible with the standard converter at that time | - | - |

| Language | FP32 first / warm s | Dynamic INT8 first / warm s | FP32/INT8 chrF |
| --- | ---: | ---: | ---: |
| hi | 0.974 / 1.102 | 0.757 / 1.423 | 80.73 |
| te | 0.727 / 1.071 | 0.909 / 1.022 | 63.40 |
| mr | 0.704 / 1.096 | 0.927 / 1.259 | 100.00 |
| kn | 0.721 / 1.291 | 0.865 / 0.994 | 89.77 |
| ta | 0.762 / 1.593 | 0.944 / 0.924 | 78.24 |
| bn | 0.734 / 1.525 | 0.976 / 0.932 | 82.91 |
| gu | 0.744 / 1.543 | 1.050 / 1.070 | 52.36 |
| or | 0.689 / 1.348 | 0.796 / 0.849 | 100.00 |
| pa | 7.261 / 14.687 | 13.470 / 14.562 | 89.82 |

The FP32/INT8 comparison covers only two late-blight sentences per language. Several languages change substantially, so close agreement is not demonstrated across the dataset. Punjabi's slow repetitive candidate is withheld, but its generation time remains included. Both measured backends exceed the 600 MB memory budget set for translation on the Pi.

<!-- END_SPEED_RESULTS -->

### Conversion attempt

```bash
ct2-transformers-converter --model "$TRANSLATION_MODEL" --output_dir /tmp/indictrans2_ct2 \
  --quantization int8 --trust_remote_code
```

This fails with `ValueError: No conversion is registered for the model configuration IndicTransConfig` (full error in
`results/indictrans2/failures.json`). [CTranslate2's supported Transformers
configurations](https://opennmt.net/CTranslate2/guides/transformers.html) do not include IndicTrans.

## What changed after this experiment

- A converter for the Hugging Face checkpoint was written (`tools/convert_indictrans2_ct2.py`), so the model runs on
  CTranslate2 INT8: 210 MB on disk instead of 0.8 GB, peak memory 370-440 MB on the Pi instead of 1.63 GiB.
- The Punjabi loop is gone: the late-blight answer in Punjabi takes 0.8-1.5 s on the Pi instead of 12.6 s on the PC.
- 2 threads and one batch per answer replaced the 4 threads used here (layout comparison in
  [results/indictrans2/ct2_pi5/README.md](../results/indictrans2/ct2_pi5/README.md)).
- The Python runtime was replaced by C++ in the application, with word-for-word identical translations on the Pi.
- Review must use translations produced on the Pi: INT8 on Arm gives the same text as on the PC in only 64% of the
  sentences. The PyTorch review sheet above is therefore a record only.
