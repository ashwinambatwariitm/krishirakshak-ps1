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
#include <utility>

namespace kr {

class LlamaAdvisor;   // defined in llama_advisor.hpp, only when built with ExecuTorch
class Translator;     // defined in translator.hpp, only when built with CTranslate2

struct PipelineConfig {
    std::string repoRoot = ".";       // other paths are relative to this unless absolute
    std::string diseaseOnnx = "models/tomato_disease_v5_effb0_6class.onnx";
    std::string diseaseSpec = "results/int8_ptq/tomato_disease_v5_effb0_6class.json";
    // Pest detector by advice group (aphid, whitefly, thrips, mite, caterpillar, other insect; training/src/pest_groups.py):
    // on 578 out-of-source tomato pest photos it finds 85% of insects (IP102 species model 67%) and gives the right
    // advice for 26% of photos (species model 13%, with the reliable-group rule 20%): results/pest_groups/. The IP102
    // species model stays usable by pointing these four paths back to results/pest_yolov8n_with_negatives/.
    std::string pestOnnx = "models/pest_yolov8n_groups.onnx";
    std::string pestSpec = "results/pest_groups/pest_yolov8n_groups.json";
    std::string pestLabels = "results/pest_groups/pest_labels.json";
    std::string pestConfig = "results/pest_groups/pest_config.json";
    std::string severityOnnx = "models/severity_lraspp_mnv3.onnx";            // leaf + lesion segmentation
    std::string severitySpec = "results/severity/severity_spec.json";
    // "Is this a tomato leaf?" check (training/src/leaf_check.py). The specification JSON holds the class order and
    // the rejection threshold chosen on validation. If the files are missing the check is skipped (older bundles).
    std::string leafCheckOnnx = "models/tomato_leaf_check_effb0.onnx";
    std::string leafCheckSpec = "results/leaf_check/tomato_leaf_check_effb0.json";
    std::string kbJson = "app/kb/tomato_kb.json";
    // LoRA-tuned Llama 3.2 1B (training/src/llama_lora_distill.py): on the Pi 5 it gave more accepted answers than
    // the base 1B (5/5 vs 3/5 photos) in half the time (results/pi5_bench/2026-11-18_llama1b_lora/).
    // The base model stays available: --llama-pte models/llama3_2_1b_instruct_8da4w.pte
    std::string llamaPte = "models/llama3_2_1b_krishirakshak_lora_8da4w.pte";
    std::string llamaTokenizer = "models/llama3_2_tokenizer.model";
    std::string translateModel = "models/indictrans2_en_indic_200M_ct2_int8";   // CTranslate2 model folder
    std::string translateSpm = "models/indictrans2_model.SRC";                  // SentencePiece source model
    float diseaseThreshold = 0.85f;   // results/disease_v5_threshold/threshold.json
    int visionThreads = 2;
    int severityThreads = 4;          // runs after the two vision models, alone on the four cores            // per model; disease and pest run in parallel -> 4 cores
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
    // Llama summary of one knowledge-base topic without a photo, through the same Llama call and checks as
    // analyse() (diagnosis line with confidence 92 %, spread "medium" except for a healthy leaf). For measuring
    // prompts and models: krishirakshak --eval-advisor demo|all|TOPIC,TOPIC
    nlohmann::json evalAdvisor(const std::string& topic);
    bool llamaReady() const;
    bool translatorReady() const;

private:
    std::string path(const std::string& p) const;
    // Translates accepted English text; null JSON if no translator, no target language or nothing to translate.
    nlohmann::json translate(const std::string& english, const std::string& translateTo, nlohmann::json& timings);
    // Llama summary of the extracts, then the grounding check, the safety checks and the minimum number of grounded
    // sentences. Returns the "llama" object of the result (text is null when rejected).
    nlohmann::json runAdvisor(const std::string& diagnosisLine, const std::vector<KbChunk>& facts,
                              const std::string& topic, const std::string& lang);
    PipelineConfig cfg_;
    std::unique_ptr<DiseaseClassifier> disease_;
    std::unique_ptr<DiseaseClassifier> leafCheck_;   // same preprocessing as the disease model, two classes
    float leafRejectThreshold_ = 1.0f;               // P(other) at or above which a photo is not a tomato leaf
    std::pair<double, bool> checkLeaf(const cv::Mat& imageRgb);   // (P(other), is tomato); (0, true) if no model
    std::unique_ptr<PestDetector> pest_;
    std::unique_ptr<SeverityModel> severity_;
    std::unique_ptr<KnowledgeBase> kb_;
    std::unique_ptr<LlamaAdvisor> llama_;
    std::unique_ptr<Translator> translator_;
    double loadMs_ = 0.0;
};

}  // namespace kr
