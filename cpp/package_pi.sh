#!/usr/bin/env bash
# Collect everything the Raspberry Pi 5 needs into one folder (dist/krishirakshak-pi), laid out like the repository
# root so the binary runs with "--root .":
#
#   krishirakshak, grounding_test       aarch64 binaries (build/arm, see cpp/README.md)
#   membw                               memory bandwidth benchmark (input of the performance model)
#   tools/perf_model.py                 predicted limits vs measured speed (Python standard library only)
#   lib/libonnxruntime.so*              ONNX Runtime 1.23.2 for aarch64
#   models/                             ONNX vision models (FP32 + INT8), Llama .pte + tokenizer
#   results/...json                     model input/output specifications and thresholds
#   app/kb/tomato_kb.json               advice knowledge base (ICAR, NIPHM, TNAU extracts)
#   run_benchmarks.sh                   timing runs used for the report
#
# OpenCV is NOT copied: install it on the Pi with  sudo apt install libopencv-dev  (Raspberry Pi OS Trixie ships
# OpenCV 4.10, the version the binary is linked against).
#
# Usage:  bash cpp/package_pi.sh        then   rsync -a dist/krishirakshak-pi/ pi@<pi-ip>:~/krishirakshak/
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${REPO}/dist/krishirakshak-pi"
ORT="${ORT_ROOT:-$HOME/arm_libs/onnxruntime-linux-aarch64-1.23.2}"

mkdir -p "${OUT}/lib" "${OUT}/models" "${OUT}/results/int8_ptq" "${OUT}/results/pest_yolov8n_with_negatives" \
         "${OUT}/app/kb" "${OUT}/photos" "${OUT}/tools"

cp "${REPO}/build/arm/krishirakshak" "${REPO}/build/arm/grounding_test" "${REPO}/build/arm/membw" "${OUT}/"
cp "${REPO}/tools/perf_model.py" "${OUT}/tools/"
cp -P "${ORT}"/lib/libonnxruntime.so* "${OUT}/lib/"
for m in tomato_disease_v5_effb0_6class tomato_disease_v5_effb0_6class_int8 \
         pest_yolov8n_ip102_negatives pest_yolov8n_ip102_negatives_int8; do
  cp "${REPO}/models/${m}.onnx" "${OUT}/models/"
done
cp "${REPO}/models/llama3_2_1b_instruct_8da4w.pte" "${REPO}/models/llama3_2_tokenizer.model" "${OUT}/models/"
# Llama 3.2 3B (exported on Kaggle, training/src/llama3b_export.py), if present; select it with --llama-pte
if [ -f "${REPO}/models/llama3_2_3b_instruct_8da4w.pte" ]; then
  cp "${REPO}/models/llama3_2_3b_instruct_8da4w.pte" "${REPO}/models/llama3_2_3b_params.json" "${OUT}/models/"
fi
cp "${REPO}"/results/int8_ptq/*.json "${OUT}/results/int8_ptq/"
cp "${REPO}"/results/pest_yolov8n_with_negatives/{pest_labels,pest_config}.json "${OUT}/results/pest_yolov8n_with_negatives/"
cp "${REPO}/app/kb/tomato_kb.json" "${OUT}/app/kb/"

# A few labelled field photos for the first run on the Pi (optional; skipped if the data folder is absent)
DATA="${KR_DATA:-$HOME/ARM_AgriTech/data/plantdoc_cls/test}"
if [ -d "${DATA}" ]; then
  for d in Tomato_leaf_late_blight Tomato_Early_blight_leaf Tomato_leaf_yellow_virus Tomato_Septoria_leaf_spot Tomato_leaf; do
    f="$(ls "${DATA}/${d}" | head -1)"
    cp "${DATA}/${d}/${f}" "${OUT}/photos/${d}.jpg"
  done
fi

cat > "${OUT}/run_benchmarks.sh" <<'EOF'
#!/usr/bin/env bash
# Run on the Pi from this folder. Prints the device state, measures the memory bandwidth, then times the pipeline
# (FP32 and INT8 vision, ONNX Runtime spinning off/on, Llama). Results are written to bench/, one file per run, and
# the performance model compares the Llama runs with the limits of the hardware (bench/perf_model.txt).
set -u
cd "$(dirname "$0")"
mkdir -p bench
echo "model: $(tr -d '\0' < /proc/device-tree/model)"; echo "kernel: $(uname -r)"
vcgencmd measure_temp 2>/dev/null; vcgencmd get_throttled 2>/dev/null
./grounding_test . || exit 1
echo "memory bandwidth ..."
./membw --mb 256 --threads 4 > bench/membw.json && cat bench/membw.json
for p in photos/*.jpg; do
  n="$(basename "$p" .jpg)"
  /usr/bin/time -f "%e s wall, peak RSS %M KB" ./krishirakshak --root . --no-llama --fp32 "$p" > "bench/${n}_fp32_vision.json"
  /usr/bin/time -f "%e s wall, peak RSS %M KB" ./krishirakshak --root . --no-llama --int8 "$p" > "bench/${n}_int8_vision.json"
done
# ONNX Runtime spinning A/B: every photo 5 times in one process. Wall time should be about equal; the user CPU time
# shows what spinning threads burn after each run (time that Llama gets when spinning is off)
PHOTOS="$(for i in 1 2 3 4 5; do ls photos/*.jpg; done | tr '\n' ' ')"
for mode in "" "--ort-spin"; do
  /usr/bin/time -f "vision x5 ${mode:-no-spin}: %e s wall, %U s user CPU, %S s system CPU" \
    ./krishirakshak --root . --no-llama --brief $mode $PHOTOS > /dev/null
done 2>&1 | grep wall | tee bench/ort_spin_ab.txt
for p in photos/Tomato_leaf_late_blight.jpg photos/Tomato_Early_blight_leaf.jpg; do
  n="$(basename "$p" .jpg)"
  /usr/bin/time -f "%e s wall, peak RSS %M KB" ./krishirakshak --root . "$p" > "bench/${n}_llama_en.json"
done
# The same A/B with Llama, the case that matters: does spinning after vision slow Llama down on 4 cores?
# The order alternates (off-on, on-off, off-on) so that warm caches and clock boost do not favour one mode.
P=photos/Tomato_leaf_late_blight.jpg
for i in 1 2 3; do
  if [ $((i % 2)) -eq 1 ]; then order="off on"; else order="on off"; fi
  for mode in $order; do
    flag=""; [ "$mode" = on ] && flag="--ort-spin"
    ./krishirakshak --root . $flag "$P" > "bench/llama_spin_${mode}_${i}.json" 2>/dev/null
  done
done
python3 -c '
import glob, json
print("mode run time_to_first_token_s tokens_per_s total_ms")
for f in sorted(glob.glob("bench/llama_spin_*.json")):
    d = json.load(open(f)); s = (d.get("llama") or {}).get("stats") or {}
    mode, run = f[:-5].split("_")[-2:]
    print(mode, run, s.get("time_to_first_token_s"), round(s.get("tokens_per_s", 0), 2), round(d["timings_ms"]["total"]))
' | tee -a bench/ort_spin_ab.txt
vcgencmd measure_temp 2>/dev/null; vcgencmd get_throttled 2>/dev/null
python3 tools/perf_model.py --pte models/llama3_2_1b_instruct_8da4w.pte --membw bench/membw.json \
  --measured 'bench/*_llama_en.json' --json bench/perf_model.json | tee bench/perf_model.txt
# Llama 3.2 3B, if it is in the bundle: the same photos in English and Hindi, and its own performance model
B3=models/llama3_2_3b_instruct_8da4w.pte
if [ -f "$B3" ]; then
  for p in photos/Tomato_leaf_late_blight.jpg photos/Tomato_Early_blight_leaf.jpg; do
    n="$(basename "$p" .jpg)"
    for lang in en hi; do
      /usr/bin/time -f "%e s wall, peak RSS %M KB" ./krishirakshak --root . --llama-pte "$B3" --lang $lang "$p" \
        > "bench/${n}_llama3b_${lang}.json"
    done
  done
  python3 tools/perf_model.py --pte "$B3" --params models/llama3_2_3b_params.json --membw bench/membw.json \
    --measured 'bench/*_llama3b_en.json' --json bench/perf_model_3b.json | tee bench/perf_model_3b.txt
fi
echo "results in bench/"
EOF
chmod +x "${OUT}/run_benchmarks.sh" "${OUT}/krishirakshak" "${OUT}/grounding_test" "${OUT}/membw"

du -sh "${OUT}"
echo "Copy to the Pi:  rsync -a ${OUT}/ pi@<pi-ip>:~/krishirakshak/"
