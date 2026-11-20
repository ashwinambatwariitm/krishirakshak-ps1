/*
 * pest_detector.hpp - IP102 insect pest detector (YOLOv8n fine-tuned with insect-free leaves) on ONNX Runtime.
 *
 * Input: square 640 x 640 letterbox with grey (114) padding, same rounding as Ultralytics LetterBox, RGB / 255.
 * Output (1, 106, 8400): cx, cy, w, h + 102 class scores per candidate. Decoding and non-maximum suppression are
 * done here with the Ultralytics rules: one class per candidate, class-aware NMS (IoU 0.7), at most 300 boxes.
 * Species are named only for ids that were reliable on the IP102 test set (pest_config.json); advice groups that are
 * reliable as a group (pest_config.json "reliable_groups", results/pest_groups_ip102) get their topic's advice even when
 * the species is not.
 */
#pragma once

#include "onnx_session.hpp"

#include <opencv2/core.hpp>
#include <map>
#include <set>
#include <string>
#include <vector>

namespace kr {

struct PestDetection {
    int speciesId = -1;
    std::string species;
    bool speciesReliable = false;
    std::string topic;         // knowledge-base topic of the class (group model's pest_config); empty for IP102 species
    float confidence = 0.f;
    cv::Rect2f box;            // x1, y1, width, height in original photo pixels
};

class PestDetector {
public:
    PestDetector(const std::string& onnxPath, const std::string& specJsonPath, const std::string& labelsJsonPath,
                 const std::string& pestConfigJsonPath, int threads, bool allowSpinning = false);

    std::vector<PestDetection> predict(const cv::Mat& imageRgb);

    const std::string& modelName() const { return modelName_; }
    float confThreshold() const { return confThreshold_; }
    // Knowledge-base pest topics whose advice is given when the detected species belongs to them, even if the
    // species itself is not reliable (pest_config.json "reliable_groups")
    const std::set<std::string>& reliableGroups() const { return reliableGroups_; }

private:
    OnnxSession session_;
    std::vector<std::string> names_;
    std::set<int> reliableIds_;
    std::map<int, std::string> topicByClass_;
    std::set<std::string> reliableGroups_;
    int size_ = 640;
    float confThreshold_ = 0.2f;
    float iouThreshold_ = 0.7f;
    std::string modelName_;
    std::vector<float> input_;
};

}  // namespace kr
