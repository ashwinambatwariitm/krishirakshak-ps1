# Benchmarks on the Raspberry Pi 5

All runs on the test Raspberry Pi 5 (8 GB, Raspberry Pi OS 64-bit, official 27 W supply, active cooler, no
throttling), with the bundle made by `cpp/package_pi.sh`. The final end-to-end test of the whole application is in
[../e2e_pi5/README.md](../e2e_pi5/README.md).

| Folder | What was measured | Used for |
|---|---|---|
| `2026-11-17_llama1b/` | First full benchmark of the bundle: vision models FP32 vs INT8 on 5 tomato photos, Llama 3.2 1B INT4, ONNX Runtime thread spinning on/off (`ort_spin_ab.txt`), memory bandwidth, Llama performance model (`perf_model.txt`) | INT8 vision timings, spinning test and decode / prefill efficiency quoted in the technical report |
| `2026-11-18_llama1b_3b/` | Repeat of the 17 Nov run with the 3B model added: vision FP32 vs INT8, Llama 3.2 1B INT4 (English) and 3B INT4 (English and Hindi), spinning on/off, memory bandwidth, performance model (`perf_model*.txt`) | 1B vs 3B on the Pi, repeat of the 17 Nov numbers |
| `2026-11-18_llama1b_lora/` | Base 1B vs LoRA-tuned 1B (INT4) on the same 5 photos, `run.sh` is the script used | choice of the LoRA model, input answers for the translation tests |
| `2026-11-21_llama_precision/` | Llama 1B FP32 vs INT4 and base vs LoRA with the final prompt: `demo6/` (6 demo topics) and `all27/` (all 27 topics) | FP32 / INT4 comparison and LoRA cost (technical report, section A6) |
| `2026-11-21_power/` | Board power, CPU load and temperature while idle, during vision only and during full answers (`tools/pi_power_profile.py`) | power figures: 1.45 W idle, 5.52 W mean during a full answer |

`run.log` (in the 17 and 18 Nov folders) is the console output of the run (device, kernel, temperature and throttling state first).
