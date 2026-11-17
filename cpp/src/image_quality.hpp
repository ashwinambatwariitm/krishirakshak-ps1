/*
 * image_quality.hpp - quality gate run before any model: reject photos that are too small, too dark,
 * too bright or too blurred, so that a poor photo never gets a confident diagnosis.
 *
 * Thresholds are engineering defaults (same values as the Python reference app/pipeline/quality.py);
 * they still have to be checked on PlantDoc validation photos and Pi camera photos (ROADMAP task B3).
 */
#pragma once

#include <opencv2/core.hpp>
#include <string>
#include <vector>

namespace kr {

struct QualityResult {
    bool ok = true;
    std::vector<std::string> issues;   // too_small, too_dark, too_bright, too_blurred
    int width = 0, height = 0;
    double brightness = 0.0;           // mean grey level 0-255
    double sharpness = 0.0;            // variance of the Laplacian on a 512 px copy
};

struct QualityThresholds {
    int minSidePx = 128;
    double darkMean = 35.0;
    double brightMean = 225.0;
    double blurVar = 20.0;
    int analysisSide = 512;
};

// imageRgb: 8-bit 3-channel RGB image.
QualityResult checkQuality(const cv::Mat& imageRgb, const QualityThresholds& t = {});

// Decodes JPEG/PNG bytes into an RGB image; returns an empty Mat if the bytes are not an image.
cv::Mat decodeImageRgb(const std::string& bytes);

}  // namespace kr
