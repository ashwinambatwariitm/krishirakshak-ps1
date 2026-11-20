"""Build the Kaggle notebooks from the editable training scripts.

The training code is kept as plain Python scripts in training/src/, split into notebook cells with "# %%" lines
(markdown cells start with "# %% [markdown]"). This script turns each script into a Jupyter notebook under kaggle/.
Edit the scripts, not the generated notebooks, then rebuild.

Usage:
    python training/build_notebooks.py                         # notebooks only
    python training/build_notebooks.py --kaggle-user NAME      # notebooks + kernel-metadata.json for "kaggle kernels push"

With --kaggle-user, each kaggle/<run>/ folder can be uploaded and started with:
    kaggle kernels push -p kaggle/<run>
"""
import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "training" / "src"

PLANTVILLAGE = "abdallahalidev/plantvillage-dataset"
PLANTDOC_BOXES = "yusufmurtaza01/plantdoc-object-detection-dataset"
PLANTDOC_FOLDERS = "nirmalsankalana/plantdoc-dataset"
IP102 = "parserpixy/ip102-dataset"
CHILI_PESTS = "indraagustian/red-chili-pepper-pests-dataset"
DISEASE_DATA = [PLANTVILLAGE, PLANTDOC_BOXES, PLANTDOC_FOLDERS]

# One entry per Kaggle notebook. "after" names one or more notebooks whose outputs (trained weights) must be attached;
# "gpu": False runs the notebook on CPU only (no GPU quota used); "models" lists Kaggle model instances to attach.
NOTEBOOKS = [
    dict(src="tomato_disease.py", slug="ps1-tomato-disease", title="PS1 Tomato Disease", datasets=DISEASE_DATA),
    dict(src="tomato_disease_v2.py", slug="ps1-tomato-disease-v2", title="PS1 Tomato Disease v2", datasets=DISEASE_DATA),
    dict(src="tomato_disease_v3.py", slug="ps1-tomato-disease-v3", title="PS1 Tomato Disease v3", datasets=DISEASE_DATA),
    dict(src="tomato_disease_v4.py", slug="ps1-tomato-disease-v4", title="PS1 Tomato Disease v4", datasets=DISEASE_DATA),
    dict(src="ip102_pest.py", slug="ps1-ip102-pest", title="PS1 IP102 Pest", datasets=[IP102, PLANTVILLAGE]),
    dict(src="ip102_pest_negft.py", slug="ps1-ip102-pest-negft", title="PS1 IP102 Pest NegFT",
         datasets=[IP102, PLANTVILLAGE, PLANTDOC_FOLDERS], after="ps1-ip102-pest"),
    dict(src="tomato_disease_v5.py", slug="ps1-tomato-disease-v5", title="PS1 Tomato Disease v5", datasets=DISEASE_DATA,
         after="ps1-tomato-disease-v4"),
    dict(src="disease_v5_threshold.py", slug="ps1-disease-v5-threshold", title="PS1 Disease v5 Threshold",
         datasets=DISEASE_DATA, after="ps1-tomato-disease-v5", gpu=False),
    # Private dataset with Meta's original 3B checkpoint (Kaggle's own copy, metaresearch/llama-3.2, was not
    # accepting access requests); the notebook also finds the checkpoint in that Kaggle model if it is attached
    dict(src="llama3b_export.py", slug="ps1-llama3b-export", title="PS1 Llama3B Export",
         datasets=["ashwinambatwar/llama32-3b-instruct-original"], gpu=False),
    dict(src="llama_lora_distill.py", slug="ps1-llama-lora-distill", title="PS1 Llama LoRA Distill",
         datasets=["ashwinambatwar/llama32-1b-instruct-original", "ashwinambatwar/llama32-3b-instruct-original",
                   "ashwinambatwar/krishirakshak-lora-inputs"]),
    # Disease severity: leaf + lesion segmentation (Roboflow CC BY 4.0 copy, field lesion masks, PlantDoc backgrounds)
    dict(src="lesion_seg.py", slug="ps1-lesion-seg", title="PS1 Lesion Seg",
         datasets=["ashwinambatwar/tomato-leaf-lesion-seg-rf", "fakhrealam9537/leaf-disease-segmentation-dataset",
                   PLANTDOC_FOLDERS]),
    # Knowledge base in 9 regional languages (IndicTrans2 on CTranslate2, GPU FP16; inputs uploaded from the repo)
    dict(src="kb_translate.py", slug="ps1-kb-translate", title="PS1 KB Translate",
         datasets=["ashwinambatwar/krishirakshak-kb-translate-inputs"]),
    # The current app pest model (FP32 ONNX from release models-v2) is attached as a private dataset for the comparison
    dict(src="pest_groups.py", slug="ps1-pest-groups", title="PS1 Pest Groups",
         datasets=[IP102, CHILI_PESTS, PLANTVILLAGE, PLANTDOC_FOLDERS, "ashvinambatwar/krishirakshak-pest-app-model"]),
    dict(src="int8_ptq.py", slug="ps1-int8-ptq", title="PS1 INT8 PTQ", datasets=DISEASE_DATA + [IP102],
         after=["ps1-tomato-disease-v4", "ps1-tomato-disease-v5", "ps1-ip102-pest-negft"], gpu=False),
]


def to_cells(text):
    """Split a '# %%' percent-format script into notebook cells (markdown cells keep their text)."""
    cells = []
    for chunk in re.split(r"^# %%", text, flags=re.M)[1:]:
        header, _, body = chunk.partition("\n")
        lines = body.strip("\n").splitlines()
        cell_id = f"cell-{len(cells):02d}"
        if header.strip() == "[markdown]":
            source = "\n".join(line[2:] if line.startswith("# ") else line.lstrip("#") for line in lines)
            cells.append({"cell_type": "markdown", "id": cell_id, "metadata": {},
                          "source": source.splitlines(keepends=True)})
        else:
            cells.append({"cell_type": "code", "id": cell_id, "metadata": {}, "execution_count": None, "outputs": [],
                          "source": "\n".join(lines).splitlines(keepends=True)})
    return cells


def main():
    """Build every notebook (and its Kaggle metadata when --kaggle-user is given)."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--kaggle-user", help="your Kaggle username; also writes kernel-metadata.json files")
    parser.add_argument("--out", default=str(REPO / "kaggle"), help="output folder (default: kaggle/)")
    args = parser.parse_args()

    for nb in NOTEBOOKS:
        folder = Path(args.out) / nb["slug"].replace("-", "_")
        folder.mkdir(parents=True, exist_ok=True)
        notebook_file = nb["slug"].replace("-", "_") + ".ipynb"
        notebook = {
            "cells": to_cells((SRC / nb["src"]).read_text()),
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                         "language_info": {"name": "python"}},
            "nbformat": 4, "nbformat_minor": 5,
        }
        (folder / notebook_file).write_text(json.dumps(notebook, indent=1) + "\n")

        if args.kaggle_user:
            # Private notebook with internet and (unless gpu=False) a GPU; the GPU type (choose T4) is set in the web UI.
            after = nb.get("after") or []
            after = [after] if isinstance(after, str) else after
            meta = {"id": f"{args.kaggle_user}/{nb['slug']}", "title": nb["title"], "code_file": notebook_file,
                    "language": "python", "kernel_type": "notebook", "is_private": True,
                    "enable_gpu": nb.get("gpu", True),
                    "enable_internet": True, "dataset_sources": nb["datasets"], "competition_sources": [],
                    "kernel_sources": [f"{args.kaggle_user}/{a}" for a in after],
                    "model_sources": nb.get("models", [])}
            (folder / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
        print(folder / notebook_file)


if __name__ == "__main__":
    main()
