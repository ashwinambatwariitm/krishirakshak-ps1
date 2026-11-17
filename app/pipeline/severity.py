"""Estimated disease severity from the share of discoloured leaf area (OpenCV colour thresholds).

This is an estimate, not a measured severity: no dataset with expert severity labels was available, and the colour
rule cannot separate the leaf from a busy field background. The result is always reported as "estimated" and is
never used to change the diagnosis.

Method (on a 512 px copy of the photo, HSV colour space, OpenCV hue range 0-179):
1. Plant tissue = pixels that are reasonably saturated and not very dark (removes grey/black backgrounds).
2. Healthy tissue = plant pixels with a green hue (35-85).
3. Lesion share = plant pixels that are not green (yellow, brown, black spots) / all plant pixels.
"""
import cv2
import numpy as np

ANALYSIS_SIDE = 512
SAT_MIN, VAL_MIN = 40, 40     # plant tissue mask
GREEN_HUE = (35, 85)          # healthy green in OpenCV hue units
LEVELS = [(0.10, "low"), (0.25, "moderate"), (1.01, "high")]   # lesion share upper bounds


def estimate_severity(image_rgb):
    """Return {"level": low|moderate|high|unknown, "lesion_share": float or None, "method": str}."""
    h, w = image_rgb.shape[:2]
    scale = ANALYSIS_SIDE / max(h, w)
    small = cv2.resize(image_rgb, (max(1, int(w * scale)), max(1, int(h * scale))), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(small, cv2.COLOR_RGB2HSV)
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    plant = (sat >= SAT_MIN) & (val >= VAL_MIN)
    # Close small holes so dark lesion centres inside the leaf still count as leaf
    plant = cv2.morphologyEx(plant.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)).astype(bool)
    green = (hue >= GREEN_HUE[0]) & (hue <= GREEN_HUE[1]) & (sat >= SAT_MIN)

    plant_px = int(plant.sum())
    if plant_px < 0.05 * plant.size:        # almost no leaf found: do not guess
        return {"level": "unknown", "lesion_share": None, "method": "hsv_colour_ratio"}
    share = float((plant & ~green).sum()) / plant_px
    level = next(name for bound, name in LEVELS if share < bound)
    return {"level": level, "lesion_share": round(share, 3), "method": "hsv_colour_ratio"}
