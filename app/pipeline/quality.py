"""Image quality gate: reject photos that are too small, too dark, too bright or too blurred before any model runs.

A poor photo should never get a confident diagnosis; the farmer is asked to take another one instead.

The thresholds below are engineering defaults chosen to reject only clearly unusable photos. Checking them on photos
taken in Indian farms is part of the Phase 2 field-photo work (item P1 of the technical report).
"""
import cv2
import numpy as np

MIN_SIDE_PX = 128          # shorter side of the photo
DARK_MEAN = 35             # mean grey level (0-255) below this: too dark
BRIGHT_MEAN = 225          # mean grey level above this: too bright / washed out
BLUR_VAR = 20.0            # variance of the Laplacian (on a 512 px copy) below this: too blurred
ANALYSIS_SIDE = 512        # blur is measured on a copy resized to this longer side, so phone and Pi photos compare


def check_quality(image_rgb):
    """Return {"ok": bool, "issues": [codes], "metrics": {...}}. Issue codes: too_small, too_dark, too_bright,
    too_blurred (the user interface and the knowledge base turn each code into a message)."""
    h, w = image_rgb.shape[:2]
    issues = []
    if min(h, w) < MIN_SIDE_PX:
        issues.append("too_small")

    scale = ANALYSIS_SIDE / max(h, w)
    small = cv2.resize(image_rgb, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    grey = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    brightness = float(grey.mean())
    sharpness = float(cv2.Laplacian(grey, cv2.CV_64F).var())

    if brightness < DARK_MEAN:
        issues.append("too_dark")
    elif brightness > BRIGHT_MEAN:
        issues.append("too_bright")
    if sharpness < BLUR_VAR:
        issues.append("too_blurred")

    return {"ok": not issues, "issues": issues,
            "metrics": {"width": w, "height": h, "brightness": round(brightness, 1),
                        "sharpness": round(sharpness, 1)}}


def decode_image(data):
    """Decode image bytes (upload or camera frame) into an RGB uint8 array; returns None if it is not an image."""
    array = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if array is None:
        return None
    return cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
