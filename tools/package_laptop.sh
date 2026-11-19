#!/usr/bin/env bash
# Laptop demo package (dist/krishirakshak-laptop-x86_64.tar.gz) for team members without a Raspberry Pi: the x86_64
# build with Llama and translation (build/x86-llm, see cpp/README.md), the libraries it needs, the farmer app, the
# knowledge base and the small model specifications. The large models are not included: cpp/laptop/kr_laptop.sh
# downloads them from the GitHub releases.
#
# The libraries are bundled (OpenCV of Ubuntu 22.04 with its dependencies, ONNX Runtime, CTranslate2), except the C
# and C++ runtime of the system, so the package also runs on newer Ubuntu releases (tested on 24.04).
#
# Usage:  bash tools/package_laptop.sh
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
BIN="${KR_BIN:-${REPO}/build/x86-llm/krishirakshak}"   # another build folder: KR_BIN=<path>/krishirakshak
NAME=krishirakshak-laptop
OUT="${REPO}/dist/${NAME}"

# The binary must have both Llama (ExecuTorch, linked statically) and the translator (libctranslate2)
ldd "${BIN}" | grep -q libctranslate2 || { echo "build/x86-llm is built without CTranslate2" >&2; exit 1; }
rm -rf "${OUT}"
mkdir -p "${OUT}/lib" "${OUT}/models" "${OUT}/licences" "${OUT}/app/kb/translations" "${OUT}/photos" \
         "${OUT}/results/int8_ptq" "${OUT}/results/pest_yolov8n_with_negatives" "${OUT}/results/severity"
cp "${BIN}" "${OUT}/"

# Shared libraries the binary loads, except the system C/C++ runtime (always present, newer on newer releases)
ldd "${BIN}" | awk '$3 ~ /^\// {print $3}' \
  | grep -vE '/(libc|libm|libpthread|libdl|librt|libresolv|libstdc\+\+|libgcc_s)\.so|ld-linux' \
  | while read -r lib; do cp -L "${lib}" "${OUT}/lib/"; done

cp "${REPO}"/results/int8_ptq/{tomato_disease_v5_effb0_6class,pest_yolov8n_ip102_negatives}.json \
   "${OUT}/results/int8_ptq/"
cp "${REPO}"/results/pest_yolov8n_with_negatives/{pest_labels,pest_config}.json \
   "${OUT}/results/pest_yolov8n_with_negatives/"
cp "${REPO}/results/severity/severity_spec.json" "${OUT}/results/severity/"
cp "${REPO}/app/kb/tomato_kb.json" "${OUT}/app/kb/"
cp "${REPO}"/app/kb/translations/*.json "${OUT}/app/kb/translations/"
cp -r "${REPO}/app/web" "${OUT}/app/web"
cp "${REPO}/models/indictrans2_LICENSE" "${OUT}/licences/"
# A few labelled field photos (PlantDoc test split) to try the app with
DATA="${KR_DATA:-$HOME/ARM_AgriTech/data/plantdoc_cls/test}"
for d in Tomato_leaf_late_blight Tomato_Early_blight_leaf Tomato_leaf_yellow_virus Tomato_Septoria_leaf_spot Tomato_leaf; do
  f="$(ls "${DATA}/${d}" | head -1)"
  cp "${DATA}/${d}/${f}" "${OUT}/photos/${d}.jpg"
done
cp "${REPO}/cpp/laptop/kr_laptop.sh" "${REPO}/cpp/laptop/README.txt" "${OUT}/"
chmod +x "${OUT}/kr_laptop.sh" "${OUT}/krishirakshak"

tar -czf "${REPO}/dist/${NAME}-x86_64.tar.gz" -C "${REPO}/dist" "${NAME}"
ls -la "${REPO}/dist/${NAME}-x86_64.tar.gz"
