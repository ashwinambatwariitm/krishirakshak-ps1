/*
 * pipeline.hpp - the complete offline pipeline for one photo.
 *
 *   photo -> quality gate -> [disease classifier || pest detector]   (two threads, 2 ONNX threads each)
 *         -> decision (answer only above the 0.85 threshold, else "uncertain") -> estimated severity
 *         -> retrieval of verified ICAR/NIPHM/TNAU extracts -> Llama explanation (ExecuTorch) -> output check
 *         -> result as JSON (for the CLI, the web page and the parity test against the Python reference)
 *
 * All models are loaded once in the constructor. analyse() is not re-entrant: requests run one after another,
 * which keeps peak memory low and lets each stage use all four Cortex-A76 cores.
 */
#pragma once

#include "disease_classifier.hpp"
#include "image_quality.hpp"
#include "knowledge_base.hpp"
#include "pest_detector.hpp"
#include "severity.hpp"

#include <json.hpp>

#include <memory>
#include <string>

namespace kr {

class LlamaAdvisor;   // defined in llama_advisor.hpp, only when built with ExecuTorch

struct PipelineConfig {
    std::string repoRoot = ".";       // other paths are relative to this unless absolute
    std::string diseaseOnnx = "models/tomato_disease_v5_effb0_6class.onnx";
    std::string diseaseSpec = "results/int8_ptq/tomato_disease_v5_effb0_6class.json";
    std::string pestOnnx = "models/pest_yolov8n_ip102_negatives.onnx";
    std::string pestSpec = "results/int8_ptq/pest_yolov8n_ip102_negatives.json";
    std::string pestLabels = "results/pest_yolov8n_with_negatives/pest_labels.json";
    std::string pestConfig = "results/pest_yolov8n_with_negatives/pest_config.json";
    std::string kbJson = "app/kb/tomato_kb.json";
    std::string llamaPte = "models/llama3_2_1b_instruct_8da4w.pte";
    std::string llamaTokenizer = "models/llama3_2_tokenizer.model";
    float diseaseThreshold = 0.85f;   // results/disease_v5_threshold/threshold.json
    int visionThreads = 2;            // per model; disease and pest run in parallel -> 4 cores
    int llamaThreads = 4;             // XNNPACK thread pool for Llama (runs after vision, so it gets all 4 cores)
    bool useLlama = true;
    bool parallelVision = true;
    // ONNX Runtime worker threads normally keep spinning for a while after each run, waiting for more work. Here
    // Llama runs right after vision on the same four cores, so spinning threads would take CPU time from it.
    bool ortSpin = false;
    // Keep the KV cache of the fixed start of the Llama prompt between requests (see llama_advisor.cpp).
    // Off by default: on WSL the diagnosis answers changed with it (under investigation, tools/prefill_check).
    bool llamaPrefixCache = false;
};

class Pipeline {
public:
    explicit Pipeline(PipelineConfig cfg);
    ~Pipeline();

    nlohmann::json analyse(const cv::Mat& imageRgb, const std::string& lang);
    nlohmann::json followUp(const std::string& question, const std::string& topic, const std::string& lang);
    nlohmann::json info() const;
    bool llamaReady() const;

private:
    std::string path(const std::string& p) const;
    PipelineConfig cfg_;
    std::unique_ptr<DiseaseClassifier> disease_;
    std::unique_ptr<PestDetector> pest_;
    std::unique_ptr<KnowledgeBase> kb_;
    std::unique_ptr<LlamaAdvisor> llama_;
    double loadMs_ = 0.0;
};

}  // namespace kr
