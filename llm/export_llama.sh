#!/usr/bin/env bash
# Export Llama 3.2 1B Instruct to ExecuTorch .pte files (run once on a PC; the .pte is then copied to the device).
#
#   INT4 (primary, deployed):  8da4w = 8-bit dynamic activations, 4-bit weights (group size 32),
#                              4-bit embeddings, KV cache + SDPA, XNNPACK backend (Arm NEON / KleidiAI kernels)
#   FP32 baseline:             same graph without quantization, XNNPACK backend (for the comparison table)
#
# Requirements:
#   - Python environment with executorch (see app/README.md)
#   - Access to meta-llama/Llama-3.2-1B-Instruct on Hugging Face (accept the Llama 3.2 licence) and `hf auth login`
#     This is the ONLY step that uses the internet; the application never does.
#
# Large files go to STORE (default: the Windows C: drive under WSL, which has more free space than the WSL disk).
#
# Usage:  bash llm/export_llama.sh [int4|fp32|all]
set -euo pipefail

WHAT="${1:-int4}"
STORE="${KR_STORE:-/mnt/c/krishirakshak_store}"
# Only the download cache moves to STORE; the login token stays in the default location (~/.cache/huggingface)
export HF_HUB_CACHE="${STORE}/hf_home/hub"
OUT="${STORE}/llama_export"
REPO_ID="meta-llama/Llama-3.2-1B-Instruct"
CONTEXT=1024        # prompt (diagnosis + retrieved extracts, about 400-600 tokens) + up to 160 new tokens
mkdir -p "${OUT}"

# 1. Download only the original Meta checkpoint, params and tokenizer (about 2.5 GB)
CKPT_DIR="${OUT}/Llama-3.2-1B-Instruct"
if [ ! -f "${CKPT_DIR}/original/consolidated.00.pth" ]; then
  hf download "${REPO_ID}" --include "original/*" --local-dir "${CKPT_DIR}"
fi
CKPT="${CKPT_DIR}/original/consolidated.00.pth"
PARAMS="${CKPT_DIR}/original/params.json"
TOKENIZER="${CKPT_DIR}/original/tokenizer.model"

COMMON=(
  base.model_class=llama3_2
  "base.checkpoint=${CKPT}"
  "base.params=${PARAMS}"
  'base.metadata="{\"get_bos_id\":128000, \"get_eos_ids\":[128009, 128001]}"'
  model.use_kv_cache=True
  model.use_sdpa_with_kv_cache=True
  model.dtype_override=fp32
  "export.max_seq_length=${CONTEXT}"
  "export.max_context_length=${CONTEXT}"
  "export.output_dir=${OUT}"
  backend.xnnpack.enabled=True
  backend.xnnpack.extended_ops=True
)

if [ "${WHAT}" = "int4" ] || [ "${WHAT}" = "all" ]; then
  python -m executorch.extension.llm.export.export_llm "${COMMON[@]}" \
    quantization.qmode=8da4w quantization.group_size=32 'quantization.embedding_quantize="4,32"' \
    export.output_name=llama3_2_1b_instruct_8da4w.pte
fi
if [ "${WHAT}" = "fp32" ] || [ "${WHAT}" = "all" ]; then
  python -m executorch.extension.llm.export.export_llm "${COMMON[@]}" \
    export.output_name=llama3_2_1b_instruct_fp32.pte
fi

# export_llm writes the .pte to the current directory (export.output_dir is not applied to output_name); move it
for f in llama3_2_1b_instruct_8da4w.pte llama3_2_1b_instruct_fp32.pte; do
  [ -f "${f}" ] && mv "${f}" "${OUT}/"
done
cp -n "${TOKENIZER}" "${OUT}/llama3_2_tokenizer.model"
cp -n "${PARAMS}" "${OUT}/llama3_2_params.json"     # model shape, read by tools/perf_model.py --params
# Every heavy operator should run inside the XNNPACK delegate; anything left outside runs on slow generic kernels
for f in "${OUT}"/llama3_2_1b_instruct_*.pte; do
  [ -f "${f}" ] && { python -m llm.inspect_pte "${f}" || echo "llm/inspect_pte.py failed for ${f}"; }
done
ls -la "${OUT}"
echo "Copy the INT4 .pte and the tokenizer into models/ (the application loads them from there)."
