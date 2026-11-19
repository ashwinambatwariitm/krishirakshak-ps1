#!/usr/bin/env bash
# IndicTrans2 200M (CTranslate2 INT8) benchmark on the Raspberry Pi 5 with the Python runtime (no torch).
#
# Bundle folder layout (copied to the Pi):
#   model_int8/          CTranslate2 model (tools/convert_indictrans2_ct2.py ... --quantization int8)
#   spm/model.SRC        SentencePiece source model of the Hugging Face checkpoint
#   hf_reference.json    answers + sentences of results/indictrans2/translations.json
#   bench_indictrans2_ct2.py, bench_indictrans2_layouts.py, this script
# Results of the runs used in the report: results/indictrans2/ct2_pi5/
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv venv
venv/bin/pip install --quiet ctranslate2==4.6.0 sentencepiece==0.2.1 indictranstoolkit==1.1.1
# 2 threads: 4 threads is several times slower on the Pi 5 (OpenMP threads spin and compete)
venv/bin/python bench_indictrans2_ct2.py --ct2 model_int8 --spm-dir spm --hf-results hf_reference.json \
    --mode latency --threads 2 --out pi_latency_int8_t2.json
venv/bin/python bench_indictrans2_ct2.py --ct2 model_int8 --spm-dir spm --hf-results hf_reference.json \
    --mode parity --threads 2 --out pi_parity_int8_t2.json
for L in A B C D E; do
    sleep 30   # cool-down between layouts
    venv/bin/python bench_indictrans2_layouts.py $L --per-lang 12 --out layout_$L.json
done
