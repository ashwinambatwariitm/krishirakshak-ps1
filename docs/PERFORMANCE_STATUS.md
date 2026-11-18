# On-device performance - status and what has been done (18 November 2026)

One page with the current state of speed and memory work on the Raspberry Pi 5, for comparison with other on-device
LLM work. Details: `docs/ARCHITECTURE_AND_SCALING.md` (pipeline, cores, memory), `docs/RESULTS.md` (model accuracy),
raw Pi results in `results/pi5_bench/`.

## 1. Hardware and software

| Item | Value |
|---|---|
| Device | Raspberry Pi 5 Model B, 8 GB, 4x Cortex-A76 @ 2.4 GHz, CPU only (no NPU used), Raspberry Pi OS (kernel 6.12) |
| Memory bandwidth (measured, `membw`) | read 14.1 GB/s (1 thread), 12.6 GB/s (4 threads); copy 8.5 GB/s (4 threads) |
| LLM runtime | ExecuTorch 1.5.1, C++ `TextLLMRunner`, XNNPACK delegate (KleidiAI micro-kernels on the A76, int8 dot product) |
| Vision runtime | ONNX Runtime 1.23.2 C++ API, OpenCV 4.10 |
| Program | one C++ binary (`cpp/`), all models loaded once at start-up, web server on the device |

## 2. Measured on the Pi (`results/pi5_bench/`)

| | Llama 3.2 1B Instruct | Llama 3.2 3B Instruct |
|---|---|---|
| .pte file (INT4 8da4w) | 0.86 GB | 2.06 GB |
| Model load | 2.6 s | 6.2 s |
| Prompt (prefill) | 338-400 tokens in 2.9-3.5 s (about 115 tokens/s) | 338-400 tokens in 7.9-9.4 s (about 43 tokens/s) |
| Decode | 13.2-13.6 tokens/s | 4.5-4.8 tokens/s |
| Upper limit from memory bandwidth | 17.4-17.5 tokens/s -> 76-78% reached | 6.6 tokens/s -> 68-72% reached |
| Prefill vs compute limit (307 GMAC/s int8, theoretical) | 37-38% | 40% |
| Whole program, peak RAM | 1.10 GB | 2.44 GB |
| One photo end to end (vision + advice) | 11-16 s | 38-45 s |

| Vision (per photo, both models in parallel) | FP32 | INT8 (mixed precision) |
|---|---|---|
| Disease classifier (EfficientNet-B0) | 73 ms | 55 ms |
| Pest detector (YOLOv8n, 640x640) | 259 ms | 120 ms |
| Vision wall time | 260 ms | 120 ms (default on the Pi) |

Bytes read per generated token (performance model, `tools/perf_model.py`): 1B 688-693 MiB (layers 522 MiB, output
layer 141 MiB, rest KV cache); 3B 1814-1829 MiB (layers 1512 MiB, output layer 211 MiB). Decode is limited by memory
bandwidth, prefill by compute.

## 3. What is implemented (and where)

| # | Optimisation | Effect / note | Where |
|---|---|---|---|
| 1 | INT4 weights, group size 32, 8-bit dynamic activations (8da4w) | 4x smaller than FP32; decode reads 688 MiB/token (1B) | `llm/export_llama.sh`, `training/src/llama3b_export.py` |
| 2 | 4-bit embedding table (`embedding_quantize=4,32`), INT4 output layer | output layer is 20% of the bytes per token for 1B | same |
| 3 | KV cache + SDPA custom op (`use_sdpa_with_kv_cache`), dynamic shapes | prompt in one prefill call, then one token per step | export flags |
| 4 | XNNPACK delegation of every heavy operator | checked per .pte: no matmul / linear outside the delegate | `llm/inspect_pte.py` |
| 5 | Context 1024 (fp32 KV cache: 64 MiB for 1B, 224 MiB for 3B) | prompt about 300-400 tokens + 160 new tokens fits | export flags |
| 6 | Short prompt: only English facts, at most 4 extracts (symptoms, cultural), Hindi extracts never sent | full Hindi extracts made a 755-token prompt and a 28 s prefill; now 300-400 tokens | `cpp/src/llama_advisor.cpp` |
| 7 | Model loaded once at start-up, weights memory-mapped | no per-request load cost | `cpp/src/llama_advisor.cpp`, `pipeline.cpp` |
| 8 | 4 XNNPACK threads for Llama; stages never overlap (vision 2+2 threads in parallel, then Llama alone on 4 cores) | each stage gets the whole CPU, low peak RAM | `pipeline.cpp`, `--llama-threads` |
| 9 | ONNX Runtime thread spinning off | no effect on Llama speed (A/B on the Pi: 13.3 tokens/s either way), saves CPU | `--ort-spin` for A/B |
| 10 | Stop on a repeated sentence; at most 160 new tokens; greedy decoding | the 1B model could loop until the token limit | `RepeatDetector` in `llama_advisor.cpp` |
| 11 | One retry with a plain prompt after a refusal (about 2.5 s) | 1B refused 2 of 5 diseases on the Pi | `llama_advisor.cpp` |
| 12 | INT8 vision with mixed precision (sensitive early blocks kept in FP32) | 2.2x faster vision on the Pi, same accuracy | `training/src/int8_ptq.py`, `results/int8_ptq/` |
| 13 | Performance model: predicted limits from weight bytes, KV cache and measured bandwidth vs measured speed | tells how far from the hardware limit each part is | `tools/perf_model.py`, `cpp/tools/membw` |

## 4. Tried and not adopted

| What | Result | Status / evidence |
|---|---|---|
| Reuse the KV cache of the fixed prompt prefix between requests | time to first token 2.8-5.7 s instead of 5.5-7.7 s (WSL), but the answers changed and all 6 failed the output check (0/6 vs 6/6) | off by default; branch `llama-prefix-cache`, reports `docs/VERIFY_llama-prefix-cache_WSL.md` and `VERIFY_prefill_*_WSL.md` on the `verify/*` branches |
| Why: split prefill is not identical to a single prefill (INT4 model) | continuing with 1-2 tokens is exact; with a second chunk of 4-285 tokens the logits differ by 1-2.6 (same top-1 token, different later text) | open: the FP32 baseline needed to separate quantisation from kernel effects was not exported |
| Llama 3.2 3B instead of 1B | better English wording, 3x slower (4.7 vs 13.4 tokens/s), 2.4 GB RAM | 1B stays the default; 3B selectable with `--llama-pte` |
| Fully INT8 vision models | 9 points lower accuracy (EfficientNet-B0); MobileNetV3 collapsed | mixed precision instead (item 12) |
| Hindi text from Llama 1B | fluent but often wrong | Hindi shows reviewed extracts; no Llama in Hindi |

## 5. Open ideas (not implemented)

| Idea | Expected effect | Note |
|---|---|---|
| Prune the output layer to the vocabulary actually used (ExecuTorch `output_prune_map`) | output layer is 141 of 688 MiB per token (1B): up to about 20% faster decode | needs a token whitelist for English + Hindi |
| Smaller KV cache values (fp16 / int8 instead of fp32) | less memory per position; matters more for long prompts and 3B | export option, check accuracy |
| Exact prefix caching (fix the split-prefill difference) | about 2-3 s less time to first token | needs the FP32 comparison first |
| Better prefill efficiency (37-40% of the compute limit) | prefill could be up to about 2x faster | thread count / affinity, chunk sizes, kernel choice |
| Speculative decoding (small draft model) or a distilled / LoRA-tuned 1B | fewer refusals and dropped sentences matter as much as raw speed | LoRA distillation notebook in progress: `training/src/llama_lora_distill.py` |
| Stream tokens to the web page | the farmer sees text after 3 s instead of waiting 15 s | web server change only |
| Hailo NPU (AI HAT+) for vision | frees the CPU for Llama | PS1 allows it; Llama must stay on the CPU with ExecuTorch |

## 6. How to reproduce the numbers

```
bash cpp/package_pi.sh && rsync -a dist/krishirakshak-pi/ pi@<pi-ip>:~/krishirakshak/
ssh pi@<pi-ip> 'cd ~/krishirakshak && ./run_benchmarks.sh'      # writes bench/ (vision, spin A/B, Llama 1B and 3B, perf model)
python -m llm.inspect_pte models/llama3_2_1b_instruct_8da4w.pte  # operators inside / outside XNNPACK
python -m llm.eval_advisor --pte models/llama3_2_1b_instruct_8da4w.pte --tokenizer models/llama3_2_tokenizer.model
```
