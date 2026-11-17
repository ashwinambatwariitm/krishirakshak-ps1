/*
 * severity.cpp - see severity.hpp.
 *
 * Method (on a 512 px copy, OpenCV HSV with hue 0-179):
 *   plant tissue  = saturation >= 40 and value >= 40, holes closed with a 7x7 morphological close
 *   green tissue  = hue in [35, 85] and saturation >= 40
 *   lesion share  = plant pixels that are not green / all plant pixels
 *   level         = low (< 10%), moderate (< 25%), high (otherwise)
 */
#include "severity.hpp"

#include <opencv2/imgproc.hpp>

namespace kr {

namespace {
constexpr int kAnalysisSide = 512;
constexpr int kSatMin = 40, kValMin = 40;
constexpr int kGreenHueLo = 35, kGreenHueHi = 85;
}  // namespace

SeverityResult estimateSeverity(const cv::Mat& imageRgb) {
    SeverityResult r;
    const double scale = static_cast<double>(kAnalysisSide) / std::max(imageRgb.cols, imageRgb.rows);
    const int w = std::max(1, static_cast<int>(imageRgb.cols * scale));
    const int h = std::max(1, static_cast<int>(imageRgb.rows * scale));
    cv::Mat small, hsv;
    cv::resize(imageRgb, small, cv::Size(w, h), 0, 0, cv::INTER_AREA);
    cv::cvtColor(small, hsv, cv::COLOR_RGB2HSV);

    // Masks are 0/255 uint8 images
    cv::Mat plant, green;
    cv::inRange(hsv, cv::Scalar(0, kSatMin, kValMin), cv::Scalar(255, 255, 255), plant);
    cv::inRange(hsv, cv::Scalar(kGreenHueLo, kSatMin, 0), cv::Scalar(kGreenHueHi, 255, 255), green);
    cv::morphologyEx(plant, plant, cv::MORPH_CLOSE, cv::Mat::ones(7, 7, CV_8U));

    const double plantPx = cv::countNonZero(plant);
    if (plantPx < 0.05 * plant.total()) return r;   // almost no leaf found: do not guess

    cv::Mat notGreen, lesion;
    cv::bitwise_not(green, notGreen);
    cv::bitwise_and(plant, notGreen, lesion);
    r.lesionShare = cv::countNonZero(lesion) / plantPx;
    r.level = r.lesionShare < 0.10 ? "low" : (r.lesionShare < 0.25 ? "moderate" : "high");
    return r;
}

}  // namespace kr
