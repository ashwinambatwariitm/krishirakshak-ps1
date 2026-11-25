/*
 * pest_detector.hpp - insect pest detector (YOLOv8n) on ONNX Runtime.
 *
 * Deployed model: 6 advice groups (aphid, whitefly, thrips, mite, caterpillar, other insect), trained with
 * insect-free leaves (training/src/pest_groups.py, results/pest_groups). The earlier IP102 species model (102
 * classes, results/pest_yolov8n_with_negatives) is still supported: class names come from the labels file and the
 * advice topic of each class from pest_config.json ("topic_by_class" for the group model).
 *
 * Input: square 640 x 640 letterbox with grey (114) padding, same rounding as Ultralytics LetterBox, RGB / 255.
 * Output (1, 4 + classes, 8400): cx, cy, w, h + class scores per candidate. Decoding and non-maximum suppression are
 * done here with the Ultralytics rules: one class per candidate, class-aware NMS (IoU 0.7), at most 300 boxes.
 * Only classes listed as reliable in pest_config.json ("reliable_species_ids": aphid, thrips, caterpillar for the
 * group model) get their topic's specific advice, the others get the general insect advice.
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
