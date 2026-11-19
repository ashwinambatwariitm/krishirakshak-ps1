/*
 * severity.cpp - see severity.hpp.
 *
 * Pre-processing (severity_spec.json): RGB, resize the whole photo to 448 x 448 with INTER_AREA (no letterbox),
 * pixel / 255, ImageNet mean / std, NCHW float32. Output: logits 1 x 2 x 448 x 448 (leaf, lesion); a pixel belongs to
 * a mask when its logit > 0 (sigmoid > 0.5). Shares are measured at the network resolution.
 */
#include "severity.hpp"

#include "common.hpp"

#include <json.hpp>
#include <opencv2/imgproc.hpp>

#include <set>

namespace kr {

namespace {

// Diseases whose severity is not an area of lesions (virus: curling, mottling, stunting) or that have none
const std::set<std::string> kNoAreaLevel = {"healthy", "yellow_leaf_curl_virus", "tomato_mosaic", "mosaic_virus"};
constexpr double kMinLeafShare = 0.02;   // below this no leaf was found: do not guess

std::string baseName(const std::string& path) {
    const auto slash = path.find_last_of('/');
    return slash == std::string::npos ? path : path.substr(slash + 1);
}

}  // namespace

SeverityModel::SeverityModel(const std::string& onnxPath, const std::string& specJsonPath, int threads,
                             bool allowSpinning)
    : session_(onnxPath, threads, allowSpinning), modelName_(baseName(onnxPath)) {
    const auto spec = nlohmann::json::parse(readFile(specJsonPath));
    const auto& in = spec.at("input");
    size_ = in.at("size").get<int>();
    for (int c = 0; c < 3; ++c) {
        mean_[c] = in.at("mean").at(c).get<float>();
        std_[c] = in.at("std").at(c).get<float>();
    }
    input_.resize(static_cast<size_t>(3) * size_ * size_);
}

SeverityResult SeverityModel::estimate(const cv::Mat& imageRgb, const std::string& topic) {
    SeverityResult r;
    if (kNoAreaLevel.count(topic)) {
        r.level = "not_applicable";
        return r;
    }
    cv::Mat small;
    cv::resize(imageRgb, small, cv::Size(size_, size_), 0, 0, cv::INTER_AREA);
    const size_t plane = static_cast<size_t>(size_) * size_;
    for (int y = 0; y < size_; ++y) {
        const auto* row = small.ptr<cv::Vec3b>(y);
        for (int x = 0; x < size_; ++x)
            for (int c = 0; c < 3; ++c)
                input_[c * plane + static_cast<size_t>(y) * size_ + x] = (row[x][c] / 255.0f - mean_[c]) / std_[c];
    }
    Ort::Value out = session_.run(input_, {1, 3, size_, size_});
    const float* logits = out.GetTensorData<float>();   // [leaf plane][lesion plane]
    size_t leaf = 0, lesion = 0;
    for (size_t i = 0; i < plane; ++i) {
        if (logits[i] > 0.0f) {
            ++leaf;
            if (logits[plane + i] > 0.0f) ++lesion;
        }
    }
    r.leafShare = static_cast<double>(leaf) / plane;
    if (r.leafShare < kMinLeafShare) return r;   // unknown
    r.lesionShare = static_cast<double>(lesion) / leaf;
    r.level = r.lesionShare < 0.10 ? "low" : (r.lesionShare < 0.25 ? "moderate" : "high");
    r.validated = true;
    return r;
}

}  // namespace kr
