/*
 * image_quality.cpp - see image_quality.hpp.
 */
#include "image_quality.hpp"

#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>

namespace kr {

QualityResult checkQuality(const cv::Mat& imageRgb, const QualityThresholds& t) {
    QualityResult r;
    r.width = imageRgb.cols;
    r.height = imageRgb.rows;
    if (std::min(r.width, r.height) < t.minSidePx) r.issues.push_back("too_small");

    // Analyse a copy whose longer side is 512 px, so phone and Pi camera photos are compared alike.
    // Integer truncation of the new size matches int() in the Python reference.
    const double scale = static_cast<double>(t.analysisSide) / std::max(r.width, r.height);
    const int w = std::max(1, static_cast<int>(r.width * scale));
    const int h = std::max(1, static_cast<int>(r.height * scale));
    cv::Mat small, grey, lap;
    cv::resize(imageRgb, small, cv::Size(w, h), 0, 0, cv::INTER_AREA);
    cv::cvtColor(small, grey, cv::COLOR_RGB2GRAY);

    r.brightness = cv::mean(grey)[0];
    cv::Laplacian(grey, lap, CV_64F);
    cv::Scalar mean, stddev;
    cv::meanStdDev(lap, mean, stddev);              // population statistics, same as numpy .var()
    r.sharpness = stddev[0] * stddev[0];

    if (r.brightness < t.darkMean) r.issues.push_back("too_dark");
    else if (r.brightness > t.brightMean) r.issues.push_back("too_bright");
    if (r.sharpness < t.blurVar) r.issues.push_back("too_blurred");
    r.ok = r.issues.empty();
    return r;
}

cv::Mat decodeImageRgb(const std::string& bytes) {
    if (bytes.empty()) return {};
    cv::Mat raw(1, static_cast<int>(bytes.size()), CV_8UC1, const_cast<char*>(bytes.data()));
    cv::Mat bgr = cv::imdecode(raw, cv::IMREAD_COLOR);
    if (bgr.empty()) return {};
    cv::Mat rgb;
    cv::cvtColor(bgr, rgb, cv::COLOR_BGR2RGB);     // all models were trained on RGB input
    return rgb;
}

}  // namespace kr
