#!/usr/bin/env bash
# KrishiRakshak on a laptop (Linux x86_64, or Windows with WSL Ubuntu): the same C++ pipeline and farmer app as on
# the Raspberry Pi 5, for team members without a Pi. Everything runs offline once the models are downloaded.
#
#   ./kr_laptop.sh setup        download the models from the project's GitHub releases (once, about 1.1 GB;
#                               needs the GitHub CLI "gh" logged in to an account with access to the repository)
#   ./kr_laptop.sh              start the app: open http://localhost:8080 in a browser
#   ./kr_laptop.sh --no-llama   start without Llama (laptops with less than 4 GB of free memory; the advice then
#                               comes from the knowledge base only)
#   PORT=9000 ./kr_laptop.sh    another port
#
# Other options are passed to the program (./krishirakshak --help).
set -euo pipefail
cd "$(dirname "$0")"

REPO="ashwinambatwariitm/krishirakshak-ps1"
# release tag | file | where it goes
FILES=(
  "models-v2|tomato_disease_v5_effb0_6class.onnx|models"
  "models-v2|pest_yolov8n_ip102_negatives.onnx|models"
  "models-v3|severity_lraspp_mnv3.onnx|models"
  "models-v3|indictrans2_model.SRC|models"
  "models-v3|indictrans2_en_indic_200M_ct2_int8.tar.gz|models"
  "llm-v2|llama3_2_1b_krishirakshak_lora_8da4w.pte|models"
  "llm-v2|LLAMA_3.2_LICENSE.txt|licences"
  "llm-v2|LLAMA_3.2_USE_POLICY.md|licences"
  "llm-v1|llama3_2_tokenizer.model|models"
)

setup() {
  if ! command -v gh > /dev/null; then
    echo "The GitHub CLI is needed:  sudo apt install gh   then   gh auth login" >&2
    echo "(or download the files listed in README.txt from the releases page by hand into models/)" >&2
    exit 1
  fi
  mkdir -p models licences .sums
  for row in "${FILES[@]}"; do
    IFS='|' read -r tag file dir <<< "$row"
    if [ -f "$dir/$file" ] || { [ "$file" = indictrans2_en_indic_200M_ct2_int8.tar.gz ] &&
                                 [ -f models/indictrans2_en_indic_200M_ct2_int8/model.bin ]; }; then
      echo "have $file"; continue
    fi
    echo "downloading $file ($tag) ..."
    # Only options that the older gh of Ubuntu 22.04 (apt) also knows: no --clobber, no -O
    gh release download "$tag" -R "$REPO" -p "$file" -D "$dir"
    # Check the file against the release's SHA256SUMS.txt (when the release lists it)
    mkdir -p ".sums/$tag"
    [ -f ".sums/$tag/SHA256SUMS.txt" ] || gh release download "$tag" -R "$REPO" -p SHA256SUMS.txt -D ".sums/$tag" \
      2> /dev/null || true
    want="$(awk -v f="$file" '$2 == f || $2 == "*"f {print $1}' ".sums/$tag/SHA256SUMS.txt" 2> /dev/null || true)"
    if [ -n "$want" ]; then
      have="$(sha256sum "$dir/$file" | cut -d' ' -f1)"
      [ "$have" = "$want" ] || { echo "checksum mismatch for $file" >&2; rm -f "$dir/$file"; exit 1; }
      echo "  sha256 ok"
    else
      echo "  (release $tag lists no checksum for this file)"
    fi
  done
  if [ -f models/indictrans2_en_indic_200M_ct2_int8.tar.gz ]; then
    tar -xzf models/indictrans2_en_indic_200M_ct2_int8.tar.gz -C models
    rm models/indictrans2_en_indic_200M_ct2_int8.tar.gz
  fi
  echo "models ready. Start the app with: ./kr_laptop.sh"
}

if [ "${1:-}" = setup ]; then setup; exit 0; fi

for f in models/tomato_disease_v5_effb0_6class.onnx models/pest_yolov8n_ip102_negatives.onnx \
         models/severity_lraspp_mnv3.onnx; do
  [ -f "$f" ] || { echo "models missing: run  ./kr_laptop.sh setup  first" >&2; exit 1; }
done
PORT="${PORT:-8080}"
# Fail early when another program (or a second copy of this one) already uses the port
if (exec 3<> "/dev/tcp/127.0.0.1/${PORT}") 2> /dev/null; then
  echo "port ${PORT} is already in use: stop the other program, or start with  PORT=8081 ./kr_laptop.sh" >&2
  exit 1
fi
if [ ! -f models/llama3_2_1b_krishirakshak_lora_8da4w.pte ] && [[ " $* " != *" --no-llama "* ]]; then
  echo "Llama model missing: run  ./kr_laptop.sh setup  first (or start with --no-llama)" >&2
  exit 1
fi
[[ " $* " == *" --no-llama "* ]] && echo "starting without Llama: the advice shows the verified extracts only"
echo "KrishiRakshak: open http://localhost:${PORT} in a browser (stop with Ctrl+C)"
# The bundled libraries (ONNX Runtime, CTranslate2, OpenCV and their dependencies) are used first
LD_LIBRARY_PATH="$PWD/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" exec ./krishirakshak --root . --serve "$PORT" \
  --web app/web "$@"
