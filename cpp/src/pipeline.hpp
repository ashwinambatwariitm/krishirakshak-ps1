/*
 * pipeline.hpp - the complete offline pipeline for one photo.
 *
 *   photo -> quality gate -> [disease classifier || pest detector]   (two threads, 2 ONNX threads each)
 *         -> decision (answer only above the 0.85 threshold, else "uncertain") -> estimated severity
 *         -> retrieval of verified ICAR/NIPHM/TNAU extracts -> Llama explanation (ExecuTorch) -> output check
 *         -> optional translation of the accepted English explanation (IndicTrans2 on CTranslate2, 9 languages)
 *         -> result as JSON (for the CLI, the web page and the parity test against the Python reference)
 *
 * Translation only ever sees text that passed the grounding and safety checks (checked in English); the English
 * stays in the result and on the page, and the translation is marked as not reviewed.
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
class Translator;     // defined in translator.hpp, only when built with CTranslate2

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
    std::string translateModel = "models/indictrans2_en_indic_200M_ct2_int8";   // CTranslate2 model folder
    std::string translateSpm = "models/indictrans2_model.SRC";                  // SentencePiece source model
    float diseaseThreshold = 0.85f;   // results/disease_v5_threshold/threshold.json
    int visionThreads = 2;            // per model; disease and pest run in parallel -> 4 cores
    int llamaThreads = 4;             // XNNPACK thread pool for Llama (runs after vision, so it gets all 4 cores)
    // Translation runs after Llama. 2 threads, whole answer in one batch: fastest on the Pi 5 (4 threads is several
    // times slower; results/indictrans2/ct2_pi5/README.md)
    int translateThreads = 2;
    bool useLlama = true;
    bool useTranslator = true;
    bool parallelVision = true;
    // ONNX Runtime worker threads normally keep spinning for a while after each run, waiting for more work. Here
    // Llama runs right after vision on the same four cores, so spinning threads would take CPU time from it.
    bool ortSpin = false;
};

class Pipeline {
public:
    explicit Pipeline(PipelineConfig cfg);
    ~Pipeline();

    // lang: page and knowledge-base language (en, hi). translateTo: optional two-letter code (hi, ta, ...) into
    // which the accepted English Llama text is also translated; empty = no translation.
    nlohmann::json analyse(const cv::Mat& imageRgb, const std::string& lang, const std::string& translateTo = "");
    nlohmann::json followUp(const std::string& question, const std::string& topic, const std::string& lang,
                            const std::string& translateTo = "");
    nlohmann::json info() const;
    bool llamaReady() const;
    bool translatorReady() const;

private:
    std::string path(const std::string& p) const;
    // Translates accepted English text; null JSON if no translator, no target language or nothing to translate.
    nlohmann::json translate(const std::string& english, const std::string& translateTo, nlohmann::json& timings);
    PipelineConfig cfg_;
    std::unique_ptr<DiseaseClassifier> disease_;
    std::unique_ptr<PestDetector> pest_;
    std::unique_ptr<KnowledgeBase> kb_;
    std::unique_ptr<LlamaAdvisor> llama_;
    std::unique_ptr<Translator> translator_;
    double loadMs_ = 0.0;
};

}  // namespace kr
