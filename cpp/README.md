# KrishiRakshak C++ on-device pipeline

One executable, `krishirakshak`, runs the whole offline pipeline on the Raspberry Pi 5 (or on a PC for development):

| Stage | Implementation |
|---|---|
| Photo quality gate, estimated severity | OpenCV (`image_quality.cpp`, `severity.cpp`) |
| Tomato disease classifier (v5 EfficientNet-B0) and IP102 pest detector (YOLOv8n) | ONNX Runtime C++ API, run in parallel (2 + 2 threads) (`disease_classifier.cpp`, `pest_detector.cpp`) |
| Verified advice extracts (ICAR, NIPHM, TNAU) | SQLite + FTS5 compiled into the binary, loaded from `app/kb/tomato_kb.json` (`knowledge_base.cpp`) |
| Plain-language summary | Llama 3.2 1B Instruct, INT4 (8da4w), ExecuTorch C++ runtime with XNNPACK (`llama_advisor.cpp`) |
| Safety of Llama text | Output check + sentence-level grounding against the retrieved extracts (`output_guard.cpp`) |
| Farmer web page | Embedded POSIX-socket HTTP server, page compiled in (`web_server.hpp`, `web_page.hpp`) |

Llama is used only for the advisory step, through ExecuTorch, as required by PS1. The vision models are a separate
ONNX Runtime pipeline.

## Dependencies (outside the repository)

| Dependency | Version | Default location |
|---|---|---|
| ONNX Runtime C++ release | 1.23.2 (x64 and aarch64 tarballs from GitHub) | `~/x86_libs/`, `~/arm_libs/` |
| OpenCV | system package on x86; 4.10 for aarch64 | system, `~/arm_libs/opencv_4.10_arm` |
| SQLite amalgamation | 3.54.1 | `~/third_party_src/sqlite-amalgamation-3540100` |
| nlohmann/json | 3.12.0 (`json.hpp`) | `~/third_party_src/json.hpp` |
| ExecuTorch (optional, for Llama) | 1.5.1, built from source with `tools/cmake/preset/llm.cmake` | `~/x86_libs/executorch`, `~/arm_libs/executorch` |

ExecuTorch must be cloned into a folder named exactly `executorch`. Build it with CMake >= 3.24, e.g.:

```
cmake -S ~/third_party_src/executorch -B ~/et-build/x86 -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX=$HOME/x86_libs/executorch \
  -DEXECUTORCH_BUILD_PRESET_FILE=$HOME/third_party_src/executorch/tools/cmake/preset/llm.cmake \
  -DEXECUTORCH_BUILD_EXECUTOR_RUNNER=OFF -DEXECUTORCH_BUILD_EXTENSION_ASR_RUNNER=OFF
cmake --build ~/et-build/x86 -j8 --target install
```

For the Pi add `-DCMAKE_TOOLCHAIN_FILE=cpp/arm-toolchain.cmake` and install to `~/arm_libs/executorch`. Do not pass
`-mcpu=cortex-a76` to the ExecuTorch build: it makes XNNPACK use the C++ `_Float16` type, which GCC 11 does not
support. XNNPACK selects its Arm kernels (dot-product, FP16, i8mm) at run time anyway.

## Build

```
# development machine, vision + knowledge base only
cmake -S cpp -B build/x86 && cmake --build build/x86 -j

# development machine, with ExecuTorch Llama
cmake -S cpp -B build/x86-llm -G Ninja -DEXECUTORCH_ROOT=$HOME/x86_libs/executorch && cmake --build build/x86-llm -j

# Raspberry Pi 5
cmake -S cpp -B build/arm -G Ninja -DCMAKE_TOOLCHAIN_FILE=cpp/arm-toolchain.cmake \
  -DEXECUTORCH_ROOT=$HOME/arm_libs/executorch && cmake --build build/arm -j
```

Model files go into `models/` (see `models/README.md`): the ONNX models and the Llama `.pte` + tokenizer.

## Run

```
build/x86-llm/krishirakshak --root . leaf.jpg                 # JSON result (English)
build/x86-llm/krishirakshak --root . --lang hi leaf.jpg       # Hindi (reviewed Hindi extracts)
build/x86-llm/krishirakshak --root . --ask "when can I harvest after spraying" --topic late_blight
build/x86-llm/krishirakshak --root . --serve 8080             # web page at http://<pi-ip>:8080/
```

Options: `--int8` (INT8 vision models), `--no-llama`, `--sequential`, `--threads N` (per vision model),
`--llama-threads N`, `--ort-spin`, `--brief`, `--list FILE`.

`--ort-spin` lets ONNX Runtime's worker threads busy-wait after each run (its default). The application turns this
off: Llama runs on the same four cores right after vision, and spinning threads would take CPU time from it. On the
development PC, 10 photos took the same wall time either way, but 45 % more CPU time with spinning (10.3 s vs
14.8 s user time); the outputs are identical. `run_benchmarks.sh` repeats this A/B on the Pi.

## Llama prompt prefix cache

Every diagnosis prompt starts with the same system instructions and example; only the diagnosis line and the facts
change. The application prefills that fixed prefix once, at load time, and keeps its KV cache entries. Each
request then moves the cache position back to the end of the prefix and prefills only its own tokens. The attention
kernel reads only cache positions below the current one, so entries left over from the previous request are never
used. On every request the application checks that the prefix and the rest tokenize to exactly the tokens of the
whole prompt, and falls back to a full prefill otherwise. The follow-up answer uses a different system prompt;
switching between the two re-prefills the other prefix.

- `--no-prefix-cache` prefills the whole prompt every time (A/B comparison).
- The result JSON shows `prompt_tokens`, `prefilled_tokens` and `prefix_cache` (`hit`, `miss`, `split_mismatch`,
  `off`) in `llama.stats`; the start-up line shows `llama_info.prefix_tokens` and `prefix_prefill_ms`.
- The gain is per request, so it shows in `--serve` mode and in CLI runs with several photos; a single-photo CLI
  run pays the prefix prefill during start-up instead.
- With temperature 0 the Llama text should be the same with and without the cache; `run_benchmarks.sh` compares it.

## Performance model: how fast could it be?

A timing alone does not say whether the application uses the Pi well. `tools/perf_model.py` computes the best
possible Llama speed from the hardware and the model size, and compares the measurement with it:

| Llama phase | What limits it | Best possible time |
|---|---|---|
| Prefill (prompt, all tokens at once) | compute: each weight is reused for every prompt token | multiply-adds / peak int8 multiply-adds per second |
| Decode (one token per step) | memory bandwidth: each token reads all weights once | weight bytes per token / measured read bandwidth |

Efficiency = best possible time / measured time. Much below 100 % means time is lost (threads, operators outside the
XNNPACK delegate, throttling); above 100 % means the model of the hardware or of the weights is wrong.

- `membw` (built with the application, no dependencies) measures read and copy bandwidth with 1-4 threads and a
  working-set sweep that shows the L1 / L2 / L3 / DRAM steps.
- `tools/perf_model.py` models the Llama weights (4-bit groups with scales, embedding table, output layer, KV
  cache) and checks the model against the real `.pte` size. Several storage hypotheses are compared; the closest
  one tells, for example, whether the output layer (128256 x 2048, a fifth of the model) is quantized.
- `llm/inspect_pte.py` (export environment) lists the operators that run outside the XNNPACK delegate and warns
  about heavy ones (matrix products, embedding, attention) that would run on the slow generic kernels.

```
build/arm/membw > membw.json                                   # on the Pi (run_benchmarks.sh does this)
python -m tools.perf_model --pte models/llama3_2_1b_instruct_8da4w.pte --membw bench/membw.json \
    --measured 'bench/*_llama_en.json'
python -m llm.inspect_pte models/llama3_2_1b_instruct_8da4w.pte  # needs the executorch Python package
```

Without measurements, the model gives the limits for the default prompt (295 tokens, 86 generated).

## Tests

```
(cd build/x86 && ctest)                                        # grounding check regression test
python -m tools.cpp_parity --data-root <data folder>           # C++ vs Python reference on 188 PlantDoc test photos
```

Parity result (WSL, FP32 models): quality decision identical on 188/188 photos; on the 185 accepted photos the top-1
disease is identical on 185/185 (max probability difference 3e-8), severity level on 185/185 and pest detections on
184/185 (one box edge differs by one pixel at a .5 rounding boundary).

## Llama behaviour (measured on WSL, 2026-11-17)

Llama 3.2 1B sometimes refuses, repeats itself, invents a cause or reverses an instruction. The application therefore
always shows the verified extracts and the spray table as published, and shows Llama text only for sentences that
are supported by one retrieved source sentence (same negation, same numbers). Hindi pages use the reviewed Hindi
extracts, because the 1B model produced fluent but meaningless Hindi. `cpp/tests/grounding_test.cpp` contains the
unsafe sentences seen in testing.
