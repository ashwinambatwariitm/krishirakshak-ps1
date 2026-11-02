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
DISEASE_DATA = [PLANTVILLAGE, PLANTDOC_BOXES, PLANTDOC_FOLDERS]

# One entry per Kaggle notebook. "after" names another notebook whose output (trained weights) must be attached.
NOTEBOOKS = [
    dict(src="tomato_disease.py", slug="ps1-tomato-disease", title="PS1 Tomato Disease", datasets=DISEASE_DATA),
    dict(src="tomato_disease_v2.py", slug="ps1-tomato-disease-v2", title="PS1 Tomato Disease v2", datasets=DISEASE_DATA),
    dict(src="tomato_disease_v3.py", slug="ps1-tomato-disease-v3", title="PS1 Tomato Disease v3", datasets=DISEASE_DATA),
    dict(src="tomato_disease_v4.py", slug="ps1-tomato-disease-v4", title="PS1 Tomato Disease v4", datasets=DISEASE_DATA),
    dict(src="ip102_pest.py", slug="ps1-ip102-pest", title="PS1 IP102 Pest", datasets=[IP102, PLANTVILLAGE]),
    dict(src="ip102_pest_negft.py", slug="ps1-ip102-pest-negft", title="PS1 IP102 Pest NegFT",
         datasets=[IP102, PLANTVILLAGE, PLANTDOC_FOLDERS], after="ps1-ip102-pest"),
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
            # Private notebook with GPU and internet; the GPU type (choose T4) is set in the Kaggle web UI.
            meta = {"id": f"{args.kaggle_user}/{nb['slug']}", "title": nb["title"], "code_file": notebook_file,
                    "language": "python", "kernel_type": "notebook", "is_private": True, "enable_gpu": True,
                    "enable_internet": True, "dataset_sources": nb["datasets"], "competition_sources": [],
                    "kernel_sources": [f"{args.kaggle_user}/{nb['after']}"] if nb.get("after") else []}
            (folder / "kernel-metadata.json").write_text(json.dumps(meta, indent=2) + "\n")
        print(folder / notebook_file)


if __name__ == "__main__":
    main()
