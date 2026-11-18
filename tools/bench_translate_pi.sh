#!/usr/bin/env bash
# Future manual benchmark only. No downloads, installation, SSH or model transfer.
# The current evaluation is WSL-only at the project owner's request.
set -euo pipefail
if [ "$#" -lt 2 ]; then
    echo "Usage: bash tools/bench_translate_pi.sh MODEL_DIR OUTPUT_JSON [fp32|dynamic-int8]"
    exit 1
fi
if [ "$(uname -m)" != "aarch64" ]; then
    echo "This script requires native aarch64. Use the Python CLI for WSL simulation."
    exit 1
fi
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 USE_TF=0 USE_FLAX=0 OMP_NUM_THREADS=4
python3 tools/translate_indictrans2.py \
    --model-dir "$1" --backend "${3:-dynamic-int8}" --threads 4 --repeat 3 \
    --input results/pi5_bench/2026-11-18_llama1b_lora/lora_Tomato_leaf_late_blight.json \
    --output "$2"
