/*
 * pipeline.cpp - see pipeline.hpp. Output fields match the Python reference app/pipeline/coordinator.py.
 */
#include "pipeline.hpp"

#include "common.hpp"
#include "llama_advisor.hpp"
#include "output_guard.hpp"

#include <future>
#include <set>

namespace kr {

namespace {

// Below this many source-supported sentences the Llama text is not shown (the verified extracts still are)
constexpr int kMinGroundedSentences = 2;

nlohmann::json chunkJson(const KbChunk& c) {
    return {{"id", c.id}, {"topic", c.topic}, {"section", c.section}, {"text", c.text}, {"product", c.product},
            {"dose", c.dose}, {"note", c.note}, {"source_id", c.sourceId}, {"source_org", c.sourceOrg},
            {"source_title", c.sourceTitle}, {"url", c.url}};
}

}  // namespace

// Destructor defined here, where LlamaAdvisor is a complete type (needed by unique_ptr)
Pipeline::~Pipeline() = default;

std::string Pipeline::path(const std::string& p) const {
    return (!p.empty() && p[0] == '/') ? p : cfg_.repoRoot + "/" + p;
}

Pipeline::Pipeline(PipelineConfig cfg) : cfg_(std::move(cfg)) {
    Timer t;
    disease_ = std::make_unique<DiseaseClassifier>(path(cfg_.diseaseOnnx), path(cfg_.diseaseSpec), cfg_.visionThreads);
    pest_ = std::make_unique<PestDetector>(path(cfg_.pestOnnx), path(cfg_.pestSpec), path(cfg_.pestLabels),
                                           path(cfg_.pestConfig), cfg_.visionThreads);
    kb_ = std::make_unique<KnowledgeBase>(path(cfg_.kbJson));
#ifdef KR_WITH_LLM
    if (cfg_.useLlama)
        llama_ = LlamaAdvisor::create(path(cfg_.llamaPte), path(cfg_.llamaTokenizer), 160, 0.0f, cfg_.llamaThreads);
#endif
    loadMs_ = t.ms();
}

bool Pipeline::llamaReady() const { return llama_ != nullptr; }

nlohmann::json Pipeline::info() const {
    return {{"disease_model", disease_->modelName()}, {"pest_model", pest_->modelName()},
            {"llama", llamaReady() ? cfg_.llamaPte : "not loaded (template mode)"},
            {"kb_version", kb_->version()}, {"kb_reviewed", kb_->reviewed()},
            {"vision_threads_per_model", cfg_.visionThreads}, {"load_ms", loadMs_}, {"runtime", "C++"}};
}

nlohmann::json Pipeline::analyse(const cv::Mat& imageRgb, const std::string& lang) {
    nlohmann::json result = {{"lang", lang}};
    nlohmann::json timings;
    Timer total;

    Timer t;
    const QualityResult q = checkQuality(imageRgb);
    timings["quality"] = t.ms();
    result["quality"] = {{"ok", q.ok}, {"issues", q.issues},
                         {"metrics", {{"width", q.width}, {"height", q.height}, {"brightness", q.brightness},
                                      {"sharpness", q.sharpness}}}};
    if (!q.ok) {
        result["status"] = "retake_photo";
        nlohmann::json msgs = nlohmann::json::array();
        for (const auto& issue : q.issues) msgs.push_back(kb_->qualityMessage(issue, lang));
        result["messages"] = msgs;
        timings["total"] = total.ms();
        result["timings_ms"] = timings;
        return result;
    }

    // Disease classifier and pest detector are independent: run them at the same time on separate cores
    std::vector<ClassProbability> ranking;
    std::vector<PestDetection> pests;
    double diseaseMs = 0, pestMs = 0;
    t.reset();
    if (cfg_.parallelVision) {
        auto pestJob = std::async(std::launch::async, [&] { Timer tp; auto r = pest_->predict(imageRgb); pestMs = tp.ms(); return r; });
        Timer td;
        ranking = disease_->predict(imageRgb);
        diseaseMs = td.ms();
        pests = pestJob.get();
    } else {
        Timer td; ranking = disease_->predict(imageRgb); diseaseMs = td.ms();
        Timer tp; pests = pest_->predict(imageRgb); pestMs = tp.ms();
    }
    timings["vision_wall"] = t.ms();
    timings["disease"] = diseaseMs;
    timings["pest"] = pestMs;

    const auto& top = ranking.front();
    const bool answered = top.probability >= cfg_.diseaseThreshold;
    const std::string topic = answered ? top.label : "";
    nlohmann::json topK = nlohmann::json::array();
    for (size_t i = 0; i < std::min<size_t>(3, ranking.size()); ++i)
        topK.push_back({{"class", ranking[i].label}, {"probability", ranking[i].probability}});
    result["disease"] = {{"top", topK}, {"answered", answered}, {"topic", answered ? nlohmann::json(topic) : nullptr},
                         {"name", answered ? nlohmann::json(kb_->topicName(topic, lang)) : nullptr},
                         {"reliability", answered ? nlohmann::json(kb_->reliability(topic)) : nullptr},
                         {"urgent", answered && kb_->urgent(topic)}};

    nlohmann::json pestJson = nlohmann::json::array();
    std::set<std::string> pestTopics;
    bool anyUnreliable = false;
    for (const auto& p : pests) {
        const std::string pt = kb_->pestTopic(p.speciesId, p.speciesReliable);
        pestTopics.insert(pt);
        anyUnreliable |= !p.speciesReliable;
        pestJson.push_back({{"species_id", p.speciesId}, {"species", p.species}, {"species_reliable", p.speciesReliable},
                            {"confidence", p.confidence}, {"topic", pt}, {"name", kb_->topicName(pt, lang)},
                            {"box_xyxy", {p.box.x, p.box.y, p.box.x + p.box.width, p.box.y + p.box.height}}});
    }
    result["pests"] = pestJson;

    if (answered && topic != "healthy") {
        t.reset();
        const SeverityResult s = estimateSeverity(imageRgb);
        timings["severity"] = t.ms();
        result["severity"] = {{"level", s.level},
                              {"lesion_share", s.lesionShare < 0 ? nlohmann::json(nullptr) : nlohmann::json(s.lesionShare)},
                              {"method", "hsv_colour_ratio"}};
    }

    // Verified extracts: the diagnosed disease first, then each distinct pest topic (sorted, like the reference)
    t.reset();
    std::vector<std::string> topics;
    if (answered) topics.push_back(topic);
    topics.insert(topics.end(), pestTopics.begin(), pestTopics.end());
    nlohmann::json blocks = nlohmann::json::array();
    std::vector<std::vector<KbChunk>> blockChunks;
    bool anySpray = false;
    for (const auto& tp : topics) {
        blockChunks.push_back(kb_->retrieveForDiagnosis(tp, lang));
        nlohmann::json chunks = nlohmann::json::array();
        for (const auto& c : blockChunks.back()) {
            chunks.push_back(chunkJson(c));
            anySpray |= c.section == "chemical";
        }
        blocks.push_back({{"topic", tp}, {"name", kb_->topicName(tp, lang)}, {"chunks", chunks}});
    }
    result["advice_blocks"] = blocks;
    timings["retrieval"] = t.ms();

    nlohmann::json msgs = nlohmann::json::array();
    if (!answered) msgs.push_back(kb_->message("uncertain", lang));
    if (answered && kb_->reliability(topic) == "low") msgs.push_back(kb_->message("expert_confirm", lang));
    if (anyUnreliable) msgs.push_back(kb_->message("pest_species_uncertain", lang));
    if (anySpray) msgs.push_back(kb_->message("chemical_rule", lang));
    result["messages"] = msgs;
    result["status"] = topics.empty() ? "uncertain" : "answered";
    result["llama"] = nullptr;

#ifdef KR_WITH_LLM
    if (llama_ && !topics.empty() && lang == "en") {
        // One-line structured summary for Llama (English); the facts are in the answer language
        std::string line;
        if (answered) {
            char conf[16];
            std::snprintf(conf, sizeof(conf), "%.0f%%", top.probability * 100.0);
            line = "Diagnosis: " + kb_->topicName(topic, "en") + " on a tomato leaf (model confidence " + conf + ").";
            if (result.contains("severity") && result["severity"]["level"] != "unknown")
                line += " Estimated spread on the photographed leaf: " + result["severity"]["level"].get<std::string>() + ".";
            if (kb_->urgent(topic)) line += " This disease is urgent: it spreads very fast.";
            if (kb_->reliability(topic) == "low")
                line += " The photo result is not certain; the farmer should confirm with the local KVK.";
        } else {
            line = "An insect pest was found on the tomato plant: " + kb_->topicName(topics.front(), "en") + ".";
        }
        t.reset();
        const LlamaOutput out = llama_->advise(line, blockChunks.front(), lang);
        timings["llama"] = t.ms();
        // 1. drop sentences not supported by the sources; 2. safety/language checks on what remains
        const GroundingResult gr = keepGroundedSentences(out.text, blockChunks.front());
        GuardResult g = checkOutput(gr.kept, blockChunks.front(), lang, topics.front());
        if (gr.keptCount < kMinGroundedSentences) {
            g.ok = false;
            g.reasons.push_back("too_few_grounded_sentences:" + std::to_string(gr.keptCount));
        }
        result["llama"] = {{"text", g.ok ? nlohmann::json(gr.kept) : nullptr}, {"accepted", g.ok},
                           {"rejected_reasons", g.reasons}, {"dropped_sentences", gr.dropped},
                           {"raw_text", out.text}, {"stats", out.stats}};
    } else if (llama_ && lang == "hi") {
        // Llama 3.2 1B produced fluent but meaningless Hindi in tests: the Hindi page shows the reviewed Hindi
        // extracts only.
        result["llama"] = {{"text", nullptr}, {"accepted", false}, {"rejected_reasons", {"hindi_uses_reviewed_extracts"}}};
    }
#endif
    timings["total"] = total.ms();
    result["timings_ms"] = timings;
    return result;
}

nlohmann::json Pipeline::followUp(const std::string& question, const std::string& topic, const std::string& lang) {
    const auto facts = kb_->search(question, topic, 4, lang);
    nlohmann::json out = {{"question", question}, {"answer", nullptr}, {"accepted", false}};
    nlohmann::json f = nlohmann::json::array();
    for (const auto& c : facts) f.push_back(chunkJson(c));
    out["facts"] = f;
    if (facts.empty()) {
        out["answer"] = kb_->message("uncertain", lang);
        return out;
    }
#ifdef KR_WITH_LLM
    if (llama_ && lang == "en") {        // Hindi: the reviewed Hindi extracts are shown instead (see analyse)
        const LlamaOutput o = llama_->answer(question, facts, lang);
        const GroundingResult gr = keepGroundedSentences(o.text, facts);
        GuardResult g = checkOutput(gr.kept, facts, lang);
        if (gr.keptCount < 1) {
            g.ok = false;
            g.reasons.push_back("no_grounded_sentence");
        }
        out["answer"] = g.ok ? nlohmann::json(gr.kept) : nullptr;
        out["accepted"] = g.ok;
        out["rejected_reasons"] = g.reasons;
        out["dropped_sentences"] = gr.dropped;
        out["raw_text"] = o.text;
        out["stats"] = o.stats;
    }
#endif
    return out;
}

}  // namespace kr
