/*
 * disease_classifier.cpp - see disease_classifier.hpp.
 */
#include "disease_classifier.hpp"

#include "common.hpp"

#include <json.hpp>
#include <opencv2/imgproc.hpp>

#include <algorithm>
#include <cmath>
#include <numeric>

namespace kr {

namespace {
std::string baseName(const std::string& path) {
    const auto pos = path.find_last_of('/');
    return pos == std::string::npos ? path : path.substr(pos + 1);
}
}  // namespace

DiseaseClassifier::DiseaseClassifier(const std::string& onnxPath, const std::string& specJsonPath, int threads,
                                     bool allowSpinning)
    : session_(onnxPath, threads, allowSpinning), modelName_(baseName(onnxPath)) {
    const auto spec = nlohmann::json::parse(readFile(specJsonPath));
    classes_ = spec.at("classes").get<std::vector<std::string>>();
    size_ = spec.at("img_size").get<int>();
    for (int c = 0; c < 3; ++c) {
        mean_[c] = spec.at("mean")[c].get<float>();
        std_[c] = spec.at("std")[c].get<float>();
    }
    input_.resize(static_cast<size_t>(3) * size_ * size_);
}

std::vector<ClassProbability> DiseaseClassifier::predict(const cv::Mat& imageRgb) {
    cv::Mat resized;
    cv::resize(imageRgb, resized, cv::Size(size_, size_), 0, 0, cv::INTER_LINEAR);

    // HWC uint8 -> CHW float, (pixel / 255 - mean) / std, written straight into the input buffer
    const int plane = size_ * size_;
    for (int y = 0; y < size_; ++y) {
        const cv::Vec3b* row = resized.ptr<cv::Vec3b>(y);
        for (int x = 0; x < size_; ++x) {
            for (int c = 0; c < 3; ++c) {
                input_[c * plane + y * size_ + x] = (row[x][c] / 255.0f - mean_[c]) / std_[c];
            }
        }
    }

    Ort::Value out = session_.run(input_, {1, 3, size_, size_});
    const float* logits = out.GetTensorData<float>();
    const size_t n = classes_.size();

    // Numerically stable softmax in double precision (same as the Python reference)
    const double maxLogit = *std::max_element(logits, logits + n);
    std::vector<double> p(n);
    double sum = 0.0;
    for (size_t i = 0; i < n; ++i) sum += (p[i] = std::exp(static_cast<double>(logits[i]) - maxLogit));

    std::vector<ClassProbability> result(n);
    for (size_t i = 0; i < n; ++i) result[i] = {classes_[i], static_cast<float>(p[i] / sum)};
    std::stable_sort(result.begin(), result.end(),
                     [](const ClassProbability& a, const ClassProbability& b) { return a.probability > b.probability; });
    return result;
}

}  // namespace kr
