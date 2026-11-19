# Verification: laptop demo (WSL, Ubuntu 22.04)

Date: 19 Nov 2026. Machine: Windows laptop, WSL2 Ubuntu 22.04.5, 16 logical CPUs, 9 GB memory visible to WSL.

## Commits

| What | Commit |
|---|---|
| grounding-fixes (step 1) | 0995ded |
| PR #6 grounding-fixes -> main | merge 943345a |
| PR #5 kb-translations-v3 -> main | merge f883488 (main used for the bundle) |
| laptop-demo: start and packaging scripts | f3697fb |
| laptop-demo: older gh support, checksum report | 4c4c541 (release target) |

PR #6: https://github.com/ashwinambatwariitm/krishirakshak-ps1/pull/6 (opened here; merged by the repository owner
together with PR #5).

## Build and tests

Configured with CMake from ~/.venvs/et (ExecuTorch needs CMake >= 3.24), ExecuTorch, CTranslate2 and SentencePiece.

| Check | grounding-fixes 0995ded | merged main f883488 |
|---|---|---|
| Build (Release) | 0 warnings, 0 errors | 0 warnings, 0 errors |
| Llama advisor / translator linked | yes / yes | yes / yes |
| ctest | 3/3 passed | 3/3 passed |
| tools/check_grounding_port.py on results/pi5_bench/\*/\*.json (55 files) | 0 differences in 28 answers | 0 differences in 28 answers |

## Bundle

`tools/package_laptop.sh` with `KR_BIN=build/x86-main/krishirakshak` (the build of main f883488).

- krishirakshak-laptop-x86_64.tar.gz: 92,134,489 bytes, sha256 `4c6c8f1cf10822cd3c0870ca997a9f206317a580c693eac6933353ba258b4545`
- Unpacked: 258 MB, no model files.
- Contents: `krishirakshak` (binary, sha256 9c321cee4baa318c...), `kr_laptop.sh`, `README.txt`, `lib/` (129 shared
  libraries: ONNX Runtime 1.23.2, CTranslate2 4.6.0, OpenCV 4.5.4 of Ubuntu 22.04 and their dependencies),
  `app/web` (farmer app), `app/kb/tomato_kb.json` and `app/kb/translations/` (9 language files and
  local_names.json), `results/` (model specifications: disease, pest labels and config, severity), `photos/`
  (5 PlantDoc test photos), `licences/indictrans2_LICENSE`. ExecuTorch is linked statically.

ldd with `LD_LIBRARY_PATH=lib`: 137 entries, 0 "not found". Outside the bundle only the system runtime: libc, libm,
libpthread, libdl, librt, libresolv (glibc), libstdc++ and libgcc_s.

## Test as a new user (empty folder)

`tar -xzf`, then `./kr_laptop.sh` before setup prints "models missing: run ./kr_laptop.sh setup first" (exit 1).

`./kr_laptop.sh setup`: 114 s, 1.1 GB in models/. sha256 checked against the release checksum files for 7 files
(models-v3: severity model, SentencePiece model, IndicTrans2 archive; llm-v2: LoRA .pte, licence, use policy;
llm-v1: tokenizer). Release models-v2 has no checksum file: its two files (disease and pest ONNX) were compared with
the repository copies and the sha256 values in models/README.md: identical.

Server: `./kr_laptop.sh` under `/usr/bin/time -v`, photo photos/Tomato_Early_blight_leaf.jpg, POST /api/analyse.

| Run | Start-up | Request | HTTP / status | Result | Time |
|---|---|---|---|---|---|
| with Llama | 2.9 s (load 2652 ms) | lang=en | 200 / answered | Early blight, Llama text 259 chars, accepted | 4.2 s and 13.2 s (two runs) |
| with Llama | | lang=mr | 200 / answered | shown in English (see problems) | 14.3 s and 15.2 s |
| with Llama | | lang=en&translate=mr (what the app sends) | 200 / answered | Marathi name and Llama advice translated (233 chars) | 23.8 s and 19.6 s |
| --no-llama | 0.8 s (load 599 ms) | lang=en | 200 / answered | verified extracts, no Llama text | 0.18 s |
| --no-llama | | lang=mr | 200 / answered | English | 0.20 s |
| --no-llama | | lang=en&translate=mr | 200 / answered | Marathi name and Marathi extracts | 0.18 s |

`/api/info`: llama = models/llama3_2_1b_krishirakshak_lora_8da4w.pte (with Llama) or "not loaded (template mode)",
translator = models/indictrans2_en_indic_200M_ct2_int8, 9 translation languages. `--no-llama` prints
"starting without Llama: the advice shows the verified extracts only".

Peak memory (maximum resident set size): 1,539,408 KB with Llama (about 1.5 GB), 494,228 KB without (about 0.5 GB).

Ubuntu 24.04: the same extracted folder in a clean `ubuntu:24.04` container: 0 libraries not found, server started,
photos/Tomato_leaf_late_blight.jpg with lang=en&translate=mr: answered, Late blight with its Marathi name, Llama
accepted, Marathi translation 183 chars, 5.8 s.

Test folders were deleted afterwards.

## Release

https://github.com/ashwinambatwariitm/krishirakshak-ps1/releases/tag/laptop-demo-v1 (target laptop-demo 4c4c541):
krishirakshak-laptop-x86_64.tar.gz and SHA256SUMS.txt. Checked from an empty folder:
`gh release download laptop-demo-v1 -R ashwinambatwariitm/krishirakshak-ps1` downloads both files,
`sha256sum -c` OK, the extracted binary is identical to the build of main.

## Problems found

1. The gh of Ubuntu 22.04 (apt, version 2.4.0) has no `--clobber` and no `-O` for `release download`; the first
   version of `setup` failed with it. Fixed in 4c4c541 (only options that version knows); this is the gh a teammate
   gets with `sudo apt install gh` on 22.04.
2. `setup` needs four releases, not two: the disease and pest ONNX models are only in models-v2 and the Llama
   tokenizer only in llm-v1. The release notes say so.
3. Release models-v2 has no SHA256SUMS.txt, so `setup` cannot check those two files (it says so for each); adding
   one to models-v2 would close this.
4. `lang=` accepts only en and hi; `lang=mr` returns the answer in English. Regional languages are requested with
   `translate=<lang>`, which is what the farmer app sends, so the app is not affected.
5. Llama time per request on this laptop varied between 4 and 15 s for the same photo (WSL, other programs running);
   translation adds a few seconds. Times are for this laptop under WSL, not for the Raspberry Pi 5.
6. The first server timings in this session showed 99 s start-up; that was the test script waiting on the wrong
   file (the server writes its "serving on" line to stderr, which /usr/bin/time had captured). Measured again with
   the corrected script: 2.9 s and 0.8 s as above.
