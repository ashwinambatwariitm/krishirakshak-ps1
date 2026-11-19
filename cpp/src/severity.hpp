/*
 * severity.hpp - disease severity of the photographed leaf: a segmentation model finds the leaf and the diseased
 * area on it; severity = lesion area / leaf area, levels low (< 10%), moderate (10-25%), high (>= 25%).
 *
 * Model: LR-ASPP MobileNetV3-Large, 2 outputs (leaf, lesion), input 448 x 448, trained on Kaggle
 * (training/src/lesion_seg.py) with leaf + disease-area polygons (Roboflow Universe "tomato" by A Tomato segment,
 * CC BY 4.0), field lesion masks (Kaggle leaf-disease-segmentation-dataset, CC0, PlantDoc photos CC BY 4.0) and
 * PlantDoc field backgrounds. Same method as the Python reference app/pipeline/severity.py.
 *
 * Validation (results/severity_plantseg/README.md), 91 held-out tomato field photos with lesion masks checked by
 * plant pathologists (PlantSeg, evaluation only): level agrees with the expert level on 61% of the photos (colour
 * rule used before: 31%), 74% without the two virus diseases. For the virus diseases (leaf curl, mosaic) the
 * symptoms are curling and mottling, not lesion areas, and the model's level agreed only 4 of 20 times: no level is
 * reported for them ("not_applicable"). The level is always called an estimate for the photographed leaf.
 */
#pragma once

#include "onnx_session.hpp"

#include <opencv2/core.hpp>

#include <array>
#include <string>
#include <vector>

namespace kr {

struct SeverityResult {
    std::string level = "unknown";   // low, moderate, high, not_applicable (virus), unknown (no leaf found)
    double lesionShare = -1.0;       // lesion pixels / leaf pixels; -1 when not measured
    double leafShare = -1.0;         // leaf pixels / photo pixels; -1 when not measured
    bool validated = false;          // true when the level comes from the validated model for this disease
};

class SeverityModel {
public:
    SeverityModel(const std::string& onnxPath, const std::string& specJsonPath, int threads,
                  bool allowSpinning = false);

    // topic: diagnosed disease (knowledge-base topic); decides whether an area-based level applies.
    SeverityResult estimate(const cv::Mat& imageRgb, const std::string& topic);

    const std::string& modelName() const { return modelName_; }

private:
    OnnxSession session_;
    int size_ = 448;
    std::array<float, 3> mean_{}, std_{};
    std::string modelName_;
    std::vector<float> input_;
};

}  // namespace kr
