"""Disease severity of the photographed leaf: a segmentation model finds the leaf and the diseased area on it.

Severity = lesion area / leaf area; levels low (< 10%), moderate (10-25%), high (>= 25%). Same method as the C++
application (cpp/src/severity.cpp); model and data: training/src/lesion_seg.py, results/severity/.

Validation on 91 held-out tomato field photos with lesion masks checked by plant pathologists (PlantSeg, evaluation
only, results/severity_plantseg/README.md): level agrees with the expert level on 61% of the photos (colour rule
used before: 31%), 74% without the two virus diseases. Virus diseases (leaf curl, mosaic) get no level
("not_applicable"): their symptoms are curling and mottling, not lesion areas.
"""
import json
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

NO_AREA_LEVEL = {"healthy", "yellow_leaf_curl_virus", "tomato_mosaic", "mosaic_virus"}
MIN_LEAF_SHARE = 0.02
LEVELS = [(0.10, "low"), (0.25, "moderate"), (1.01, "high")]   # lesion share upper bounds


class SeverityModel:
    def __init__(self, onnx_path, spec_path, threads=4):
        spec = json.loads(Path(spec_path).read_text())
        self.size = spec["input"]["size"]
        self.mean = np.array(spec["input"]["mean"], np.float32)
        self.std = np.array(spec["input"]["std"], np.float32)
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        self.sess = ort.InferenceSession(str(onnx_path), sess_options=options, providers=["CPUExecutionProvider"])
        self.input_name = self.sess.get_inputs()[0].name
        self.name = Path(onnx_path).name

    def estimate(self, image_rgb, topic):
        """Return {"level", "lesion_share", "leaf_share", "method", "model", "validated"}."""
        out = {"level": "unknown", "lesion_share": None, "leaf_share": None, "method": "lesion_segmentation",
               "model": self.name, "validated": False}
        if topic in NO_AREA_LEVEL:
            out["level"] = "not_applicable"
            return out
        x = cv2.resize(image_rgb, (self.size, self.size), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
        x = ((x - self.mean) / self.std).transpose(2, 0, 1)[None]
        logits = self.sess.run(None, {self.input_name: x})[0][0]
        leaf = logits[0] > 0
        lesion = (logits[1] > 0) & leaf
        leaf_share = float(leaf.mean())
        out["leaf_share"] = round(leaf_share, 3)
        if leaf_share < MIN_LEAF_SHARE:      # no leaf found: do not guess
            return out
        share = float(lesion.sum()) / float(leaf.sum())
        out.update(level=next(name for bound, name in LEVELS if share < bound), lesion_share=round(share, 3),
                   validated=True)
        return out
