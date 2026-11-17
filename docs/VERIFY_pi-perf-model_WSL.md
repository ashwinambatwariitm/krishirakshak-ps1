# Verification of branch pi-perf-model on the WSL build machine

- Branch verified: `pi-perf-model`, commit `fe9104b` ("Add Pi performance model, memory bandwidth benchmark and pte
  delegation check")
- Machine: development PC with ExecuTorch, the Llama `.pte` and the ARM toolchain (Intel i5-12500H, WSL2, Ubuntu 22.04,
  12 GB RAM for WSL)
- Date: 17 November 2026
- Rules followed: no code changed, nothing committed or pushed to `pi-perf-model`. This report lives on the separate
  branch `verify/pi-perf-model-wsl`. (Source file timestamps were touched once to force a recompile for the warning
  count in step 6; no contents changed.)

## Result

All six steps succeeded (exit code 0). Nothing failed.

| Step | Result |
|---|---|
| 1. Branch | `fe9104b` on top as expected |
| 2. x86 build with ExecuTorch + tests | Built `krishirakshak`, `grounding_test`, `membw`; no compiler warnings or errors; `ctest` 1/1 passed |
| 3. Delegation check | Ran in `~/.venvs/et` without import errors; output below |
| 4. Spinning A/B with Llama | Diagnosis identical in all 6 runs; table below |
| 5. Performance model | Closest storage hypothesis: "scales 2 B, output layer int4", 804.1 MiB vs 820.6 MiB `.pte` (-2.0%) |
| 6. Pi build + bundle | `membw` and `krishirakshak` are aarch64 ELF; bundle 910 MB; contains `membw` and `tools/perf_model.py`; 166 compiler warnings, all from OpenCV 4.10 headers (see below) |

## Step 2 - build and tests (x86, ExecuTorch)

- Build: no compiler warnings or errors. Targets `krishirakshak`, `grounding_test`, `membw` present.
- `ctest --output-on-failure`: `1/1 Test #1: grounding ... Passed`, 100% tests passed.
- Only message: CMake developer warning at `cpp/CMakeLists.txt:91 (find_package)`:
  policy CMP0144 is not set; `find_package` ignores the variable `EXECUTORCH_ROOT`. Harmless.

## Step 3 - delegation check (raw output)

Command: `~/.venvs/et/bin/python -m llm.inspect_pte models/llama3_2_1b_instruct_8da4w.pte --json /tmp/llama_pte_ops.json`
(the `.pte` was in `models/`)

```
models/llama3_2_1b_instruct_8da4w.pte: 820.6 MiB, 391 data segments (820.4 MiB)

method forward
  delegate XnnpackBackend: 164 calls, payload 0.2 MiB
  outside a delegate: 409 calls
      128 x executorch_prim::et_view.default
       66 x aten::slice_copy.Tensor_out
       64 x aten::squeeze_copy.dims_out
       34 x aten::select_copy.int_out
       33 x aten::_local_scalar_dense
       33 x aten::mean.out
       32 x llama::update_cache.out
       16 x llama::custom_sdpa.out
        1 x aten::sym_size.int
        1 x quantized_decomposed::embedding_4bit.dtype_out  <-- heavy operator outside the delegate
        1 x executorch_prim::add.Scalar

WARNING: 1 heavy operator type(s) run outside the delegate (see above)
wrote /tmp/llama_pte_ops.json
```

## Step 4 - ONNX Runtime spinning A/B with Llama

Photo: PlantDoc test `test_Tomato leaf late blight_1.jpg`. Runs alternated off/on, CPU idle before the runs.

| mode | run | time_to_first_token_s | tokens_per_s | timings_ms.total |
|---|---|---|---|---|
| off | 1 | 7.77 | 13.60 | 14291 |
| on | 1 | 7.59 | 15.94 | 13140 |
| off | 2 | 7.27 | 16.55 | 12587 |
| on | 2 | 5.62 | 17.14 | 10749 |
| off | 3 | 6.81 | 14.20 | 13002 |
| on | 3 | 6.69 | 15.40 | 12410 |

- Diagnosis identical in all 6 runs: `late_blight`, probability 0.950692, answered; Llama text accepted every time.
- On WSL, `--ort-spin` was slightly faster in all three pairs (mean time to first token 6.63 s vs 7.28 s, decode
  16.2 vs 14.8 tokens/s). The run-to-run spread is of the same size as the difference, so this does not settle the
  default; the Pi A/B in `run_benchmarks.sh` should decide it.

## Step 5 - performance model (raw output)

`build/x86-llm/membw --mb 256 --threads 4`:

```
{
  "tool": "membw",
  "buffer_mb": 256,
  "repetitions": 5,
  "hardware_threads": 16,
  "read_gbps": {"1": 18.95, "2": 31.66, "3": 38.56, "4": 42.66},
  "copy_gbps": {"1": 35.38, "2": 38.40, "3": 40.19, "4": 39.44},
  "sweep_read_gbps_1thread": {"16": 73.26, "32": 72.20, "64": 72.33, "128": 72.32, "256": 70.54, "512": 67.38, "1024": 37.25, "2048": 30.17, "4096": 70.83, "8192": 55.50, "16384": 23.62, "32768": 19.76, "65536": 18.31, "131072": 18.90, "262144": 18.50},
  "checksum": 799
}
```

`python3 -m tools.perf_model --pte models/llama3_2_1b_instruct_8da4w.pte --params .../original/params.json
--membw /tmp/membw_wsl.json --measured '/tmp/spin_off_*.json'`:

```
== Llama weights ==
layers 16, dim 2048, heads 32 (KV heads 8), feed-forward 8192, vocabulary 128256
  layers           522.0 MiB
  output_layer     140.9 MiB
  embedding        140.9 MiB
  norms              0.3 MiB
  .pte file        820.6 MiB
  hypotheses (closest first):
    scales 2 B, output layer int4:    804.1 MiB  (-2.0%)
    scales 4 B, output layer int4:    893.4 MiB  (+8.9%)
    scales 2 B, output layer int8:    929.3 MiB  (+13.3%)
    scales 4 B, output layer int8:   1018.6 MiB  (+24.1%)
    scales 2 B, output layer fp32:   1665.2 MiB  (+102.9%)
    scales 4 B, output layer fp32:   1738.8 MiB  (+111.9%)

== KV cache ==
  1024 positions x 4 B:     64.0 MiB (with 32 KV heads instead of 8 it would be    256.0 MiB)

== Hardware ==
  read bandwidth: 42.66 GB/s (membw, 4 threads)
  peak int8 compute: 307 GMAC/s (theoretical Pi 5)

== Predicted limits vs measured ==
  spin_off_1.json: prompt 295 tokens, generated 86
    prefill    290.2 GMAC -> >=   0.94 s | measured   7.77 s | efficiency  12.2%
    decode     684.3 MiB/token -> <=  59.45 tok/s | measured  13.60 tok/s | efficiency  22.9%
  spin_off_2.json: prompt 295 tokens, generated 86
    prefill    290.2 GMAC -> >=   0.94 s | measured   7.27 s | efficiency  13.0%
    decode     684.3 MiB/token -> <=  59.45 tok/s | measured  16.55 tok/s | efficiency  27.8%
  spin_off_3.json: prompt 295 tokens, generated 86
    prefill    290.2 GMAC -> >=   0.94 s | measured   6.81 s | efficiency  13.9%
    decode     684.3 MiB/token -> <=  59.45 tok/s | measured  14.20 tok/s | efficiency  23.9%
```

- Closest storage hypothesis: "scales 2 B, output layer int4" = 804.1 MiB vs 820.6 MiB `.pte`, error -2.0%.
- Decode efficiency on WSL: 22.9 - 27.8% of the memory-bandwidth limit. Prefill efficiency is not meaningful on WSL
  (the compute peak is the Raspberry Pi 5 value).

## Step 6 - Pi build and bundle

- `cmake -S cpp -B build/arm -G Ninja -DCMAKE_TOOLCHAIN_FILE=cpp/arm-toolchain.cmake -DEXECUTORCH_ROOT=$HOME/arm_libs/executorch`:
  exit 0 (the existing `build/arm` cache was reused). Messages: the CMP0144 developer warning and a list of optional
  ExecuTorch backends "not found" (e.g. `aoti_cuda_backend`), both informational.
- `cmake --build build/arm -j`: exit 0, with 166 compiler warnings, all
  `-Wdeprecated-enum-enum-conversion` inside OpenCV 4.10's header `opencv2/core/mat.inl.hpp`; none in project code.
  Cause: Abseil (a dependency of the ExecuTorch tokenizers) exports `INTERFACE_COMPILE_FEATURES cxx_std_20`
  (`lib/cmake/absl/abslTargets.cmake`), so the project targets compile as `-std=gnu++20` instead of C++17; under
  C++20 GCC flags this OpenCV header code. The x86 build is also `gnu++20` but silent, because it uses the system
  OpenCV 4.5 headers, which GCC treats as system headers.
- `file`:
  - `build/arm/membw`: ELF 64-bit LSB pie executable, ARM aarch64, dynamically linked
  - `build/arm/krishirakshak`: ELF 64-bit LSB pie executable, ARM aarch64, dynamically linked
- `bash cpp/package_pi.sh`: exit 0, bundle `dist/krishirakshak-pi` = 910 MB.
  - `membw` present (aarch64, 25,528 bytes)
  - `tools/perf_model.py` present (13,049 bytes)
  - `run_benchmarks.sh` calls both

## Failures

None.

## Possible follow-ups (not done; code was not changed)

- Silence or fix the 166 OpenCV warnings on the ARM build, e.g. include the OpenCV headers as system headers
  (`target_include_directories(... SYSTEM ...)`) or compile the project explicitly as C++17 where Abseil allows it.
- Set CMake policy CMP0144 (or rename `EXECUTORCH_ROOT`) to remove the developer warning.
- Decide the ONNX Runtime spinning default from the Pi A/B, not from WSL.
