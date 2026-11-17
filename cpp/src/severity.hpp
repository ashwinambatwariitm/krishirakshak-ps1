/*
 * severity.hpp - estimated disease severity from the share of discoloured leaf area (HSV colour rule).
 *
 * This is an estimate, not a measured severity: no dataset with expert severity labels was available and the
 * colour rule cannot separate the leaf from a busy field background. It is always reported as "estimated" and
 * never changes the diagnosis. Same method and constants as the Python reference app/pipeline/severity.py.
 */
#pragma once

#include <opencv2/core.hpp>
#include <string>

namespace kr {

struct SeverityResult {
    std::string level = "unknown";   // low, moderate, high, unknown
    double lesionShare = -1.0;       // -1 when unknown
};

SeverityResult estimateSeverity(const cv::Mat& imageRgb);

}  // namespace kr
