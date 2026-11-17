# Architecture, performance and scaling notes (working draft)

Status: working notes for the team (17 November 2026). Numbers marked "WSL" were measured on the development PC
(Intel i5-12500H, WSL2, models limited to 2-4 threads like the Pi); Raspberry Pi 5 numbers are still to be measured
with `run_benchmarks.sh` from the Pi bundle (`cpp/package_pi.sh`).

## 1. End-to-end flow for one photo

```
 Farmer phone / browser                       Raspberry Pi 5 (fully offline)
 ----------------------        ------------------------------------------------------------------------
  photo + language (en/hi) --> web_server.hpp   POST /api/analyse   (POSIX sockets, page compiled in)
                                     |
                                     v
                               decode JPEG (OpenCV) -> RGB image
                                     |
                          [1] QUALITY GATE (OpenCV: size, brightness, Laplacian blur)
                                     |  fail -> "retake photo" message (stop)
                                     v
                  +------------------+------------------+
                  |   run in PARALLEL (std::async)      |
          [2a] DISEASE CLASSIFIER                 [2b] PEST DETECTOR
          EfficientNet-B0, 224 x 224              YOLOv8n, 640 x 640 letterbox
          ONNX Runtime C++, 2 threads             ONNX Runtime C++, 2 threads
          -> 6 class probabilities                -> boxes + IP102 species (NMS in C++)
                  +------------------+------------------+
                                     |
                          [3] DECISION: top probability >= 0.85 ? answer : "uncertain"
                                     |
                          [4] ESTIMATED SEVERITY (OpenCV HSV lesion share; diseased leaves only)
                                     |
                          [5] RETRIEVAL (SQLite + FTS5, compiled in)
                              topic = diagnosed disease + each pest group
                              -> verified ICAR / NIPHM / TNAU extracts, spray table, safety rules
                                     |
                          [6] LLAMA 3.2 1B INT4 (ExecuTorch C++ runtime, XNNPACK, 4 threads)
                              English only: rephrase the extracts in simple words
                                     |
                          [7] OUTPUT CHECK
                              - no chemical or dose that is not in the sources
                              - every sentence supported by ONE source sentence
                                (same negation, same numbers); duplicates removed
                                     |
                                     v
                               JSON result -> web page: diagnosis, notes, Llama summary (if it passes),
                                              verified extracts with sources, spray table, timings

 Follow-up question --> POST /api/ask -> [5] BM25 search -> [6] Llama -> [7] check -> answer + cited extracts
```

## 2. Architecture: one C++ binary (`krishirakshak`)

| Layer | Module | Technology |
|---|---|---|
| Interface | `main.cpp` (CLI), `web_server.hpp` + `web_page.hpp` (`--serve`) | C++17, POSIX sockets, HTML compiled in |
| Coordinator | `pipeline.cpp` | Loads all models once; runs the stages; builds the JSON result |
| Vision pipeline | `image_quality.cpp`, `disease_classifier.cpp`, `pest_detector.cpp`, `severity.cpp` | ONNX Runtime 1.23 C++ API + OpenCV |
| Knowledge pipeline | `knowledge_base.cpp` (reads `app/kb/tomato_kb.json`) | SQLite 3.54 + FTS5, compiled into the binary |
| Advisory pipeline | `llama_advisor.cpp` (loads `llama3_2_1b_instruct_8da4w.pte`) | ExecuTorch 1.5.1 C++ (LLM runner, XNNPACK; KleidiAI kernels on Arm) - required by PS1 |
| Safety | `output_guard.cpp` | C++ (UTF-8 aware checks, regex, sentence-level grounding) |
| Build time only (PC / Kaggle) | training, ONNX export + INT8, Llama `.pte` export | Python / PyTorch - never runs on the Pi |

Build and run instructions: `cpp/README.md`.

## 3. Time for one photo (WSL, median of 5 warm runs)

| Stage | FP32 vision | INT8 vision |
|---|---|---|
| [1] Quality gate | 1.7 ms | 1.7 ms |
| [2a] Disease classifier | 11 ms | 16 ms |
| [2b] Pest detector | 63 ms | 90 ms |
| [2] Vision wall time (both in parallel) | 64 ms | 90 ms |
| [4] Severity | 1.8 ms | 1.8 ms |
| [5] Retrieval | 0.2 ms | 0.2 ms |
| Photo to diagnosis + verified advice (no Llama) | 67 ms | 94 ms |
| [6] Llama: read 295-token prompt (time to first token) | 5.5 s | 5.5 s |
| [6] Llama: generate 86 tokens at 12.5 tokens/s | 6.9 s | 6.9 s |
| Total with Llama summary (English) | about 12.5 s | about 12.5 s |
| Total in Hindi (Llama loaded, reviewed Hindi extracts shown) | 0.14 s | - |
| One-time start-up (load all models) | 3.7 s | - |

Observations:

- Llama takes about 99% of the time. The page can show the diagnosis and verified advice immediately and add the
  Llama summary when it is ready.
- INT8 is slower than FP32 on the Intel CPU (INT8 activations are not ONNX Runtime's fast path on x86). On Arm the
  INT8 path is expected to be faster; the Pi measurement decides which models ship.
- On x86, running the two vision models one after the other with 4 threads each (56 ms) was faster than in parallel
  with 2 + 2 threads (64 ms), because the pest model dominates. The Pi benchmark decides the default
  (`--sequential`, `--threads N`).

## 4. Memory (peak RSS of the whole process, WSL)

| Configuration | Peak RAM |
|---|---|
| Vision + knowledge base only (`--no-llama`, FP32 models) | 205 MB |
| Same with INT8 models | 193 MB |
| Full application with Llama 1B INT4 | about 1.10 GB |

Approximate split by pipeline:

| Pipeline | RAM |
|---|---|
| Disease model session (FP32 / INT8) | about 59 / 20 MB (earlier ONNX benchmark) |
| Pest model session (FP32 / INT8) | about 46 / 17 MB |
| ONNX Runtime + OpenCV + binary + working buffers | about 100 MB |
| Knowledge base (61 extracts, in-memory SQLite) | < 1 MB |
| Llama advisory pipeline | about 900 MB (820 MB INT4 model, memory-mapped, + KV cache for 1024 tokens + activations) |

On the 8 GB Raspberry Pi 5 more than 6 GB stays free; the FP32 Llama baseline (about 5 GB) also fits when run alone.

## 5. Use of the four Cortex-A76 cores

```
time ->  [quality]  [disease 2 thr | pest 2 thr]  [severity, retrieval]  [Llama: XNNPACK pool, 4 threads]  [check]
cores     1 core     cores 0-1      cores 2-3        1 core               cores 0-3 (prefill + every token)    1 core
```

- Vision: the disease classifier and the pest detector run at the same time on separate threads (`std::async`), each
  with its own ONNX Runtime session of 2 intra-op threads (2 + 2 = 4 cores), the same pattern as the
  road-anomaly-detection project (2 workers x 2 threads).
- Llama runs after vision and gets all 4 cores through the ExecuTorch thread pool (`--llama-threads`). XNNPACK splits
  every matrix multiplication across the cores; on the Pi, KleidiAI micro-kernels use the A76 dot-product
  instructions for the INT4/INT8 matrix products.
- Stages never overlap: peak memory stays low and each stage gets the whole CPU. The web server accepts connections on
  their own threads, but a mutex lets one photo through the pipeline at a time.
- Tunable without recompiling: `--threads N`, `--sequential`, `--llama-threads N`.

## 6. Llama behaviour and the output check

Llama 3.2 1B, tested on WSL, sometimes refused, repeated a sentence many times, invented a cause ("caused by a
fungus" for late blight, a water mould), reversed an instruction ("do not remove the infected leaf") or stitched an
answer from unrelated extracts ("harvest 28 days after transplanting"). Hindi output was fluent but meaningless.

Design consequences:

- The farmer always sees the verified extracts and the spray table exactly as published, with the source.
- Llama is asked only to rephrase the extracts (one sentence per fact, one-shot example in the prompt).
- Every Llama sentence must be supported by one source sentence (75% content-word overlap, same negation, same
  numbers); unsupported sentences are dropped. With fewer than 2 supported sentences the Llama text is not shown.
- Hindi pages show the reviewed Hindi extracts (no Llama text).
- `cpp/tests/grounding_test.cpp` keeps the unsafe sentences above as a regression test.

In the WSL tests the Llama summary passed for about half of the diseases; for the others only the verified extracts
were shown.

## 7. Scaling to more crops and more diseases

### 7.1 Accuracy falls as classes increase (main challenge)

| Model | Classes | Lab accuracy (PlantVillage) | Field macro F1 (PlantDoc) |
|---|---|---|---|
| v3 | 5 tomato | 97% | 0.78 |
| v5 | 6 tomato | 98.7% | 0.69 |
| v4 | 10 tomato | 98.4% | 0.62 |

- Lab accuracy stays near 98%, field accuracy drops with every class: more look-alikes (bacterial spot vs septoria
  was the main new confusion in v4). Across crops it gets worse (early blight on tomato and potato, leaf spots on
  chilli, brinjal and tomato).
- Field photos are the bottleneck: PlantDoc has few field photos per class and none for some tomato classes (target
  spot, spider mites). Every new crop needs labelled field photos, ideally including own photos from Indian farms.

### 7.2 The model must know which crop it is looking at

The disease model only knows tomato and already gave a confident wrong answer on a non-tomato photo (an IP102 rice
leaf was called "bacterial spot, 73%"; ROADMAP task A1). With several crops a wrong crop means completely wrong
advice, so a crop step is needed before the disease step.

### 7.3 Architecture options

| Option | How it works | Pros | Cons |
|---|---|---|---|
| A. One large model | One EfficientNet-B0 for all crops x diseases (e.g. 38 classes) | Simple; same speed; about 16.2 MB, practically the same size (about 5 KB per extra class, measured) | Lowest field accuracy; errors can name the wrong crop; every change needs a full retrain |
| B. Crop router + one model per crop | Small crop classifier, then that crop's disease model, loaded on demand | Each disease model keeps the 4-6 class accuracy; crops added independently | Two models in a row (+10-20 ms); more models to train and validate; about 56 MB on disk for 14 crops in INT8 (estimate) |
| C. Farmer selects the crop, then B | Crop chosen on the web page + a "is this the selected crop?" check | Most reliable; matches how KVK experts work; simplest to build | One extra tap |

Recommendation for Phase 2: C with B underneath. Only one disease model is loaded at a time, so memory stays about
200 MB + Llama.

### 7.4 Advice database: curation grows with every crop x disease

- Each new combination needs extracts from ICAR, NIPHM and TNAU with sources, Hindi translation and expert review.
  NIPHM publishes AESA-based IPM packages per crop (potato, chilli and others), so the sources exist; the work is
  curation and review.
- Safety: pesticide label claims (CIB&RC) are crop-specific. A product approved for tomato is not automatically
  approved for chilli. Spray options must be keyed by crop + disease, and retrieval must filter by crop, otherwise
  a tomato spray could be returned for a chilli question.
- Topic keys change from `late_blight` to `tomato.late_blight`, `potato.late_blight`; small change in the C++ code.

### 7.5 Pests

- The IP102 detector already covers 102 insects across many crops; it scales without change.
- A species-to-crop mapping is needed (flag a rice pest on a chilli photo as unlikely).
- Species naming is reliable for 34 of 102 species; the rest need a second-stage classifier (ROADMAP A5).

### 7.6 What does not get harder

| Area | Effect of more crops / diseases |
|---|---|
| Vision speed on the Pi | Unchanged for options A and C; +10-20 ms for a crop router |
| RAM | Unchanged (one disease model loaded at a time, about 20-60 MB) |
| Llama (ExecuTorch) | Unchanged: it only sees the extracts retrieved for one topic, so prompt length and time stay the same |
| Output check | Unchanged: it checks against whatever was retrieved |
| C++ design | Pipeline, threading and web server stay; the knowledge base gets a crop field |

### 7.7 Validation and thresholds

The 0.85 "uncertain" threshold was tuned for 6 tomato classes. Each crop or model needs its own threshold, tuned on
that crop's field validation photos, plus its own field test set, per-class accuracy report and parity test.

### 7.8 Suggested path

- Phase 1 (deadline 23 November 2026): one crop, 6 classes, as advised by the organisers; this is what is validated.
- Phase 2: crop selection + check (option C), then one crop at a time. Potato is a natural second crop (late and
  early blight overlap with tomato; NIPHM has a potato IPM package). Per crop: field photos -> per-crop model ->
  threshold -> curated advice extracts -> Hindi review.
