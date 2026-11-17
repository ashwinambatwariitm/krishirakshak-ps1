/*
 * pest_detector.hpp - IP102 insect pest detector (YOLOv8n fine-tuned with insect-free leaves) on ONNX Runtime.
 *
 * Input: square 640 x 640 letterbox with grey (114) padding, same rounding as Ultralytics LetterBox, RGB / 255.
 * Output (1, 106, 8400): cx, cy, w, h + 102 class scores per candidate. Decoding and non-maximum suppression are
 * done here with the Ultralytics rules: one class per candidate, class-aware NMS (IoU 0.7), at most 300 boxes.
 * Species are named only for ids that were reliable on the IP102 test set (pest_config.json).
 */
#pragma once

#include "onnx_session.hpp"

#include <opencv2/core.hpp>
#include <set>
#include <string>
#include <vector>

namespace kr {

struct PestDetection {
    int speciesId = -1;
    std::string species;
    bool speciesReliable = false;
    float confidence = 0.f;
    cv::Rect2f box;            // x1, y1, width, height in original photo pixels
};

class PestDetector {
public:
    PestDetector(const std::string& onnxPath, const std::string& specJsonPath, const std::string& labelsJsonPath,
                 const std::string& pestConfigJsonPath, int threads);

    std::vector<PestDetection> predict(const cv::Mat& imageRgb);

    const std::string& modelName() const { return modelName_; }
    float confThreshold() const { return confThreshold_; }

private:
    OnnxSession session_;
    std::vector<std::string> names_;
    std::set<int> reliableIds_;
    int size_ = 640;
    float confThreshold_ = 0.2f;
    float iouThreshold_ = 0.7f;
    std::string modelName_;
    std::vector<float> input_;
};

}  // namespace kr
