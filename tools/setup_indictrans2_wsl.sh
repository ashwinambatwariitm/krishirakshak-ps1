#!/usr/bin/env bash
# Run in WSL. Downloads stay outside the repository. No Pi commands.
set -euo pipefail
if [ "$#" -ne 1 ]; then
    echo "Usage: bash tools/setup_indictrans2_wsl.sh ABSOLUTE_ASSET_DIRECTORY_OUTSIDE_REPO"
    exit 1
fi
translation_assets="$1"
python3 - "$translation_assets" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1]).resolve()
if not Path(sys.argv[1]).is_absolute() or p.is_relative_to(Path.cwd().resolve()):
    raise SystemExit("Use an absolute assets path outside the repository")
PY
mkdir -p "$translation_assets"
python3 -m venv "$translation_assets/venv"
"$translation_assets/venv/bin/python" -m pip install --upgrade pip
"$translation_assets/venv/bin/python" -m pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
"$translation_assets/venv/bin/python" -m pip install -r tools/indictrans2_requirements.txt
# Model access must already be approved on Hugging Face. Use the existing login
# or HF_TOKEN; do not put credentials in this script or in repository files.
"$translation_assets/venv/bin/python" - "$translation_assets/model" <<'PY'
from huggingface_hub import snapshot_download
import sys
snapshot_download(
    "ai4bharat/indictrans2-en-indic-dist-200M",
    revision="2cfd0a20057756d756bf3e53528f492afc52f91a",
    local_dir=sys.argv[1], ignore_patterns=["*.bin", "*.msgpack", "*.h5", "*.ot"])
PY
