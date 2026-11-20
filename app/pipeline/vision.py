"""Vision stage: tomato disease classifier and insect pest detector, both run with ONNX Runtime on the CPU.

Preprocessing matches the evaluation in training/src/int8_ptq.py exactly, so the answers here equal the published
test results in docs/RESULTS.md:

- Disease: RGB, direct resize to 224 x 224 (bilinear), pixel / 255, ImageNet mean/std, NCHW float32.
- Pest: RGB, square 640 x 640 letterbox with grey (114) padding (same rounding as Ultralytics LetterBox), pixel / 255.
  The model output is (1, 106, 8400): cx, cy, w, h + 102 class scores per candidate. Non-maximum suppression (NMS) is
  done here, with the same rules as Ultralytics: one class per candidate, class-aware NMS, IoU 0.7, at most 300 boxes.

Each model reads its input/output specification from the JSON file written by the INT8 export
(results/int8_ptq/<model>.json), so class order and thresholds are never copied by hand.
"""
import json
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort


def make_session(onnx_path, threads):
    """Create an ONNX Runtime CPU session. threads=4 matches the four Cortex-A76 cores of the Raspberry Pi 5."""
    options = ort.SessionOptions()
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    return ort.InferenceSession(str(onnx_path), sess_options=options, providers=["CPUExecutionProvider"])


class DiseaseClassifier:
    """Tomato leaf disease classifier (v5, six classes). Returns class probabilities for one RGB image."""

    def __init__(self, onnx_path, spec_path, threads=4):
        self.spec = json.loads(Path(spec_path).read_text())
        self.classes = self.spec["classes"]
        self.size = int(self.spec["img_size"])
        self.mean = np.array(self.spec["mean"], np.float32)
        self.std = np.array(self.spec["std"], np.float32)
        self.session = make_session(onnx_path, threads)
        self.input_name = self.session.get_inputs()[0].name
        self.name = Path(onnx_path).name

    def preprocess(self, image_rgb):
        """RGB uint8 (H, W, 3) -> normalised (1, 3, size, size) float32."""
        x = cv2.resize(image_rgb, (self.size, self.size), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
        x = (x - self.mean) / self.std
        return np.ascontiguousarray(x.transpose(2, 0, 1)[None])

    def predict(self, image_rgb):
        """Return a list of {"class", "probability"} sorted from most to least likely."""
        logits = self.session.run(None, {self.input_name: self.preprocess(image_rgb)})[0][0].astype(np.float64)
        probs = np.exp(logits - logits.max())
        probs /= probs.sum()
        order = np.argsort(-probs)
        return [{"class": self.classes[i], "probability": float(probs[i])} for i in order]


def letterbox(image_rgb, size=640, pad_value=114):
    """Resize keeping the aspect ratio and pad to size x size, exactly like Ultralytics LetterBox(auto=False).

    Returns the padded image and (ratio, left, top), needed to map boxes back to the original image.
    """
    h, w = image_rgb.shape[:2]
    ratio = min(size / h, size / w)
    new_w, new_h = int(round(w * ratio)), int(round(h * ratio))
    dw, dh = (size - new_w) / 2, (size - new_h) / 2
    if (w, h) != (new_w, new_h):
        image_rgb = cv2.resize(image_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    padded = cv2.copyMakeBorder(image_rgb, top, bottom, left, right, cv2.BORDER_CONSTANT,
                                value=(pad_value, pad_value, pad_value))
    return padded, (ratio, left, top)


def nms(boxes, scores, iou_threshold):
    """Greedy non-maximum suppression. boxes (n, 4) x1y1x2y2; returns kept indices, highest score first."""
    order = np.argsort(-scores)
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    keep = []
    while order.size:
        i = order[0]
        keep.append(i)
        rest = order[1:]
        x1 = np.maximum(boxes[i, 0], boxes[rest, 0])
        y1 = np.maximum(boxes[i, 1], boxes[rest, 1])
        x2 = np.minimum(boxes[i, 2], boxes[rest, 2])
        y2 = np.minimum(boxes[i, 3], boxes[rest, 3])
        inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
        iou = inter / (areas[i] + areas[rest] - inter + 1e-9)
        order = rest[iou <= iou_threshold]
    return np.array(keep, dtype=int)


class PestDetector:
    """IP102 insect pest detector (YOLOv8n fine-tuned with insect-free leaves)."""

    MAX_DET = 300        # Ultralytics default
    MAX_WH = 7680        # class offset used by Ultralytics for class-aware NMS

    def __init__(self, onnx_path, spec_path, labels_path, pest_config_path, threads=4):
        self.spec = json.loads(Path(spec_path).read_text())
        self.names = json.loads(Path(labels_path).read_text())["names"]
        pest_config = json.loads(Path(pest_config_path).read_text())
        self.reliable_ids = set(pest_config["reliable_species_ids"])
        # Knowledge-base topics whose advice is given even when the species is uncertain (optional key)
        self.reliable_groups = set(pest_config.get("reliable_groups", []))
        self.size = int(self.spec["img_size"])
        self.conf_threshold = float(self.spec["conf_threshold"])
        self.iou_threshold = float(self.spec["nms_iou"])
        self.session = make_session(onnx_path, threads)
        self.input_name = self.session.get_inputs()[0].name
        self.name = Path(onnx_path).name

    def predict(self, image_rgb):
        """Return detected insects: species, whether the species name is reliable, confidence and box."""
        padded, (ratio, left, top) = letterbox(image_rgb, self.size)
        x = np.ascontiguousarray(padded.transpose(2, 0, 1)[None], dtype=np.float32) / 255.0
        out = self.session.run(None, {self.input_name: x})[0][0].T          # (8400, 4 + classes)
        class_scores = out[:, 4:]
        cls = class_scores.argmax(1)
        conf = class_scores[np.arange(len(cls)), cls]
        mask = conf > self.conf_threshold
        if not mask.any():
            return []
        xywh, conf, cls = out[mask, :4], conf[mask], cls[mask]
        boxes = np.concatenate([xywh[:, :2] - xywh[:, 2:] / 2, xywh[:, :2] + xywh[:, 2:] / 2], axis=1)
        keep = nms(boxes + cls[:, None] * self.MAX_WH, conf, self.iou_threshold)[: self.MAX_DET]

        h, w = image_rgb.shape[:2]
        detections = []
        for i in keep:
            # Undo the letterbox: remove the padding, undo the scaling, clip to the photo
            x1, y1, x2, y2 = boxes[i]
            box = [float(np.clip((x1 - left) / ratio, 0, w)), float(np.clip((y1 - top) / ratio, 0, h)),
                   float(np.clip((x2 - left) / ratio, 0, w)), float(np.clip((y2 - top) / ratio, 0, h))]
            species_id = int(cls[i])
            detections.append({"species_id": species_id, "species": self.names[species_id].strip(),
                               "species_reliable": species_id in self.reliable_ids,
                               "confidence": float(conf[i]), "box_xyxy": [round(v, 1) for v in box]})
        return detections
