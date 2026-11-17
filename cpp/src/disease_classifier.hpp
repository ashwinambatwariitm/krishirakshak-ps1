/*
 * disease_classifier.hpp - tomato leaf disease classifier (v5 EfficientNet-B0, six classes) on ONNX Runtime.
 *
 * Preprocessing matches training/evaluation exactly: RGB, direct resize to 224 x 224 (bilinear), pixel / 255,
 * ImageNet mean/std, NCHW float32. Class order, size and normalisation are read from the specification JSON
 * written by the INT8 export (results/int8_ptq/<model>.json), never hard-coded.
 */
#pragma once

#include "onnx_session.hpp"

#include <opencv2/core.hpp>
#include <array>
#include <string>
#include <vector>

namespace kr {

struct ClassProbability {
    std::string label;
    float probability;
};

class DiseaseClassifier {
public:
    DiseaseClassifier(const std::string& onnxPath, const std::string& specJsonPath, int threads,
                      bool allowSpinning = false);

    // All classes, sorted from most to least likely.
    std::vector<ClassProbability> predict(const cv::Mat& imageRgb);

    const std::vector<std::string>& classes() const { return classes_; }
    const std::string& modelName() const { return modelName_; }

private:
    OnnxSession session_;
    std::vector<std::string> classes_;
    int size_ = 224;
    std::array<float, 3> mean_{}, std_{};
    std::string modelName_;
    std::vector<float> input_;           // reused input buffer (no allocation per photo)
};

}  // namespace kr
