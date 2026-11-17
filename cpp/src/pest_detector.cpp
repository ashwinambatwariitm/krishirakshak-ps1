/*
 * pest_detector.cpp - see pest_detector.hpp.
 */
#include "pest_detector.hpp"

#include "common.hpp"

#include <json.hpp>
#include <opencv2/imgproc.hpp>

#include <algorithm>
#include <cmath>
#include <numeric>

namespace kr {

namespace {

constexpr int kMaxDet = 300;          // Ultralytics default
constexpr float kMaxWh = 7680.f;      // class offset used by Ultralytics for class-aware NMS

std::string baseName(const std::string& path) {
    const auto pos = path.find_last_of('/');
    return pos == std::string::npos ? path : path.substr(pos + 1);
}

std::string trim(const std::string& s) {
    const auto b = s.find_first_not_of(' ');
    const auto e = s.find_last_not_of(' ');
    return b == std::string::npos ? "" : s.substr(b, e - b + 1);
}

// Python's round() rounds halves to even; std::nearbyint does the same in the default FE_TONEAREST mode.
// All letterbox arithmetic is in double, like the Python/Ultralytics reference, so padding matches to the pixel.
int roundHalfEven(double v) { return static_cast<int>(std::nearbyint(v)); }

struct Letterbox {
    double ratio;
    int left, top;
};

Letterbox letterbox(const cv::Mat& src, int size, cv::Mat& dst) {
    const int h = src.rows, w = src.cols;
    const double ratio = std::min(static_cast<double>(size) / h, static_cast<double>(size) / w);
    const int newW = roundHalfEven(w * ratio);
    const int newH = roundHalfEven(h * ratio);
    const double dw = (size - newW) / 2.0, dh = (size - newH) / 2.0;
    cv::Mat resized = src;
    if (newW != w || newH != h) cv::resize(src, resized, cv::Size(newW, newH), 0, 0, cv::INTER_LINEAR);
    const int top = roundHalfEven(dh - 0.1), bottom = roundHalfEven(dh + 0.1);
    const int left = roundHalfEven(dw - 0.1), right = roundHalfEven(dw + 0.1);
    cv::copyMakeBorder(resized, dst, top, bottom, left, right, cv::BORDER_CONSTANT, cv::Scalar(114, 114, 114));
    return {ratio, left, top};
}

float iou(const cv::Rect2f& a, const cv::Rect2f& b) {
    const float inter = (a & b).area();
    return inter / (a.area() + b.area() - inter + 1e-9f);
}

}  // namespace

PestDetector::PestDetector(const std::string& onnxPath, const std::string& specJsonPath,
                           const std::string& labelsJsonPath, const std::string& pestConfigJsonPath, int threads)
    : session_(onnxPath, threads), modelName_(baseName(onnxPath)) {
    const auto spec = nlohmann::json::parse(readFile(specJsonPath));
    size_ = spec.at("img_size").get<int>();
    confThreshold_ = spec.at("conf_threshold").get<float>();
    iouThreshold_ = spec.at("nms_iou").get<float>();
    // Keep the parsed documents in named variables: a range-for over parse(...).at(...) would iterate a reference
    // into a temporary that is destroyed before the loop body runs.
    const auto labels = nlohmann::json::parse(readFile(labelsJsonPath));
    for (const auto& n : labels.at("names")) names_.push_back(trim(n.get<std::string>()));
    const auto pestConfig = nlohmann::json::parse(readFile(pestConfigJsonPath));
    for (const auto& id : pestConfig.at("reliable_species_ids")) reliableIds_.insert(id.get<int>());
    input_.resize(static_cast<size_t>(3) * size_ * size_);
}

std::vector<PestDetection> PestDetector::predict(const cv::Mat& imageRgb) {
    cv::Mat padded;
    const Letterbox lb = letterbox(imageRgb, size_, padded);

    const int plane = size_ * size_;
    for (int y = 0; y < size_; ++y) {
        const cv::Vec3b* row = padded.ptr<cv::Vec3b>(y);
        for (int x = 0; x < size_; ++x)
            for (int c = 0; c < 3; ++c) input_[c * plane + y * size_ + x] = row[x][c] / 255.0f;
    }

    Ort::Value out = session_.run(input_, {1, 3, size_, size_});
    const auto shape = out.GetTensorTypeAndShapeInfo().GetShape();     // (1, 4 + classes, candidates)
    const int rows = static_cast<int>(shape[1]), cand = static_cast<int>(shape[2]);
    const float* data = out.GetTensorData<float>();

    // 1. Best class per candidate, keep those above the confidence threshold
    std::vector<cv::Rect2f> boxes, shifted;
    std::vector<float> scores;
    std::vector<int> classes;
    for (int i = 0; i < cand; ++i) {
        int best = 0;
        float bestScore = data[4 * cand + i];
        for (int k = 1; k < rows - 4; ++k) {
            const float s = data[(4 + k) * cand + i];
            if (s > bestScore) bestScore = s, best = k;
        }
        if (bestScore <= confThreshold_) continue;
        const float cx = data[i], cy = data[cand + i], w = data[2 * cand + i], h = data[3 * cand + i];
        const cv::Rect2f box(cx - w / 2, cy - h / 2, w, h);
        boxes.push_back(box);
        // Offsetting boxes by class id keeps boxes of different classes from suppressing each other
        shifted.emplace_back(box.x + best * kMaxWh, box.y + best * kMaxWh, box.width, box.height);
        scores.push_back(bestScore);
        classes.push_back(best);
    }

    // 2. Greedy class-aware NMS, highest score first
    std::vector<int> order(scores.size());
    std::iota(order.begin(), order.end(), 0);
    std::stable_sort(order.begin(), order.end(), [&](int a, int b) { return scores[a] > scores[b]; });
    std::vector<int> keep;
    std::vector<bool> removed(order.size(), false);
    for (size_t i = 0; i < order.size() && static_cast<int>(keep.size()) < kMaxDet; ++i) {
        if (removed[i]) continue;
        keep.push_back(order[i]);
        for (size_t j = i + 1; j < order.size(); ++j)
            if (!removed[j] && iou(shifted[order[i]], shifted[order[j]]) > iouThreshold_) removed[j] = true;
    }

    // 3. Undo the letterbox: remove padding, undo scaling, clip to the photo
    std::vector<PestDetection> result;
    const float W = static_cast<float>(imageRgb.cols), H = static_cast<float>(imageRgb.rows);
    for (int k : keep) {
        const cv::Rect2f& b = boxes[k];
        const float r = static_cast<float>(lb.ratio);
        const float x1 = std::clamp((b.x - lb.left) / r, 0.f, W);
        const float y1 = std::clamp((b.y - lb.top) / r, 0.f, H);
        const float x2 = std::clamp((b.x + b.width - lb.left) / r, 0.f, W);
        const float y2 = std::clamp((b.y + b.height - lb.top) / r, 0.f, H);
        PestDetection d;
        d.speciesId = classes[k];
        d.species = names_.at(classes[k]);
        d.speciesReliable = reliableIds_.count(classes[k]) > 0;
        d.confidence = scores[k];
        d.box = cv::Rect2f(x1, y1, x2 - x1, y2 - y1);
        result.push_back(d);
    }
    return result;
}

}  // namespace kr
