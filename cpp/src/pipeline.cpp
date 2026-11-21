/*
 * pipeline.cpp - see pipeline.hpp. Output fields match the Python reference app/pipeline/coordinator.py.
 */
#include "pipeline.hpp"

#include "common.hpp"
#include "llama_advisor.hpp"
#include "output_guard.hpp"
#include "pest_severity.hpp"
#include "translator.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <future>
#include <set>

namespace kr {

namespace {

// Below this many source-supported sentences the Llama text is not shown (the verified extracts still are)
constexpr int kMinGroundedSentences = 2;

// Languages of the knowledge-base translations (app/kb/tomato_kb.json, tools/translate_kb.py)
const std::set<std::string> kKbLanguages = {"hi", "te", "mr", "kn", "ta", "bn", "gu", "or", "pa"};

// Language the farmer reads: the chosen translation language, otherwise the page language (en / hi)
std::string displayLanguage(const std::string& lang, const std::string& translateTo) {
    return kKbLanguages.count(translateTo) ? translateTo : lang;
}

nlohmann::json chunkJson(const KbChunk& c) {
    return {{"id", c.id}, {"topic", c.topic}, {"section", c.section}, {"text", c.text}, {"text_en", c.textEn},
            {"product", c.product},
            {"dose", c.dose}, {"note", c.note}, {"note_en", c.noteEn}, {"source_id", c.sourceId}, {"source_org", c.sourceOrg},
            {"source_title", c.sourceTitle}, {"url", c.url}};
}

}  // namespace

// Destructor defined here, where LlamaAdvisor and Translator are complete types (needed by unique_ptr)
Pipeline::~Pipeline() = default;

std::string Pipeline::path(const std::string& p) const {
    return (!p.empty() && p[0] == '/') ? p : cfg_.repoRoot + "/" + p;
}

Pipeline::Pipeline(PipelineConfig cfg) : cfg_(std::move(cfg)) {
    Timer t;
    disease_ = std::make_unique<DiseaseClassifier>(path(cfg_.diseaseOnnx), path(cfg_.diseaseSpec), cfg_.visionThreads,
                                                    cfg_.ortSpin);
    pest_ = std::make_unique<PestDetector>(path(cfg_.pestOnnx), path(cfg_.pestSpec), path(cfg_.pestLabels),
                                           path(cfg_.pestConfig), cfg_.visionThreads, cfg_.ortSpin);
    // Optional tomato-leaf check: loaded only when both files exist, so older model bundles keep working
    if (std::ifstream(path(cfg_.leafCheckOnnx)).good() && std::ifstream(path(cfg_.leafCheckSpec)).good()) {
        leafCheck_ = std::make_unique<DiseaseClassifier>(path(cfg_.leafCheckOnnx), path(cfg_.leafCheckSpec),
                                                          cfg_.visionThreads, cfg_.ortSpin);
        const auto spec = nlohmann::json::parse(readFile(path(cfg_.leafCheckSpec)));
        leafRejectThreshold_ = spec.at("reject_threshold").get<float>();
    }
    kb_ = std::make_unique<KnowledgeBase>(path(cfg_.kbJson));
    kb_->setReliablePestGroups(pest_->reliableGroups());
    severity_ = std::make_unique<SeverityModel>(path(cfg_.severityOnnx), path(cfg_.severitySpec),
                                                cfg_.severityThreads, cfg_.ortSpin);
#ifdef KR_WITH_LLM
    if (cfg_.useLlama)
        llama_ = LlamaAdvisor::create(path(cfg_.llamaPte), path(cfg_.llamaTokenizer), 160, 0.0f, cfg_.llamaThreads);
#endif
#ifdef KR_WITH_TRANSLATION
    if (cfg_.useTranslator)
        translator_ = Translator::create(path(cfg_.translateModel), path(cfg_.translateSpm), cfg_.translateThreads);
#endif
    loadMs_ = t.ms();
}

std::pair<double, bool> Pipeline::checkLeaf(const cv::Mat& imageRgb) {
    if (!leafCheck_) return {0.0, true};
    double pOther = 0.0;
    for (const auto& c : leafCheck_->predict(imageRgb))
        if (c.label == "other") pOther = c.probability;
    return {pOther, pOther < leafRejectThreshold_};
}

bool Pipeline::llamaReady() const { return llama_ != nullptr; }
bool Pipeline::translatorReady() const { return translator_ != nullptr; }

nlohmann::json Pipeline::translate(const std::string& english, const std::string& translateTo,
                                   nlohmann::json& timings) {
#ifdef KR_WITH_TRANSLATION
    if (!translator_ || translateTo.empty() || english.empty()) return nullptr;
    const auto& langs = Translator::supportedLanguages();
    if (std::find(langs.begin(), langs.end(), translateTo) == langs.end()) return nullptr;
    const TranslationOutput out = translator_->translate(sentencesOf(english), translateTo);
    timings["translation"] = out.ms;
    return out.toJson();
#else
    (void)english; (void)translateTo; (void)timings;
    return nullptr;
#endif
}

nlohmann::json Pipeline::info() const {
    return {{"disease_model", disease_->modelName()}, {"pest_model", pest_->modelName()}, {"severity_model", severity_->modelName()},
            {"leaf_check_model", leafCheck_ ? nlohmann::json(leafCheck_->modelName()) : nlohmann::json("not loaded")},
            {"llama", llamaReady() ? cfg_.llamaPte : "not loaded (template mode)"},
            {"translator", translatorReady() ? cfg_.translateModel : "not loaded"},
#ifdef KR_WITH_TRANSLATION
            {"translation_languages", translatorReady() ? nlohmann::json(Translator::supportedLanguages())
                                                        : nlohmann::json::array()},
#else
            {"translation_languages", nlohmann::json::array()},
#endif
            {"kb_version", kb_->version()}, {"kb_reviewed", kb_->reviewed()},
            {"vision_threads_per_model", cfg_.visionThreads},
            {"ort_spinning", cfg_.ortSpin}, {"load_ms", loadMs_}, {"runtime", "C++"},
            {"cpu_temp_c", readCpuTempC()}, {"cpu_freq_mhz", readCpuFreqMhz()},
            {"supported_crops", nlohmann::json::array({"tomato"})}};
}

nlohmann::json Pipeline::analyse(const cv::Mat& imageRgb, const std::string& lang, const std::string& translateTo) {
    const std::string show = displayLanguage(lang, translateTo);   // texts shown to the farmer
    nlohmann::json result = {{"lang", lang}, {"display_lang", show}, {"translation", nullptr}};
    nlohmann::json timings;
    Timer total;
    const double tempStartC = readCpuTempC();
    const bool tooHot = tempStartC >= cfg_.llamaMaxTempC;

    Timer t;
    const QualityResult q = checkQuality(imageRgb);
    timings["quality"] = t.ms();
    result["quality"] = {{"ok", q.ok}, {"issues", q.issues},
                         {"metrics", {{"width", q.width}, {"height", q.height}, {"brightness", q.brightness},
                                      {"sharpness", q.sharpness}}}};
    if (!q.ok) {
        result["status"] = "retake_photo";
        nlohmann::json msgs = nlohmann::json::array();
        for (const auto& issue : q.issues) msgs.push_back(kb_->qualityMessage(issue, show));
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
    // The leaf check runs in the disease thread, just before the disease model (both read the same 224 x 224 input)
    std::pair<double, bool> leaf{0.0, true};
    double leafMs = 0;
    if (cfg_.parallelVision) {
        auto pestJob = std::async(std::launch::async, [&] { Timer tp; auto r = pest_->predict(imageRgb); pestMs = tp.ms(); return r; });
        Timer tl; leaf = checkLeaf(imageRgb); leafMs = tl.ms();
        Timer td;
        ranking = disease_->predict(imageRgb);
        diseaseMs = td.ms();
        pests = pestJob.get();
    } else {
        Timer tl; leaf = checkLeaf(imageRgb); leafMs = tl.ms();
        Timer td; ranking = disease_->predict(imageRgb); diseaseMs = td.ms();
        Timer tp; pests = pest_->predict(imageRgb); pestMs = tp.ms();
    }
    timings["vision_wall"] = t.ms();
    timings["disease"] = diseaseMs;
    timings["pest"] = pestMs;
    const bool isTomato = leaf.second;
    // On a photo that is not a tomato leaf, boxes of the group model's "other insect" class are dropped: they are the
    // main source of false insects there (a face, a flower or a whole leaf boxed as "other insect"), and they would
    // only give generic advice. Insects of the tomato pest groups (aphid, whitefly, thrips, mite, caterpillar) are
    // kept on every photo. The IP102 species model has no topic per class and is not affected.
    if (!isTomato)
        pests.erase(std::remove_if(pests.begin(), pests.end(),
                                   [](const PestDetection& p) { return p.topic == "insect_other"; }),
                    pests.end());
    // Crop detected in the photo (Phase 1: the tomato-leaf check; Phase 2: a crop-identification model fills the same
    // field). null when no leaf of a supported crop was found. The farmer never selects the crop.
    result["crop"] = isTomato ? nlohmann::json{{"name", "tomato"}, {"source", leafCheck_ ? "leaf_check" : "assumed"}}
                              : nlohmann::json(nullptr);
    if (leafCheck_) {
        timings["leaf_check"] = leafMs;
        result["leaf_check"] = {{"is_tomato_leaf", isTomato}, {"p_other", leaf.first},
                                {"threshold", leafRejectThreshold_}, {"model", leafCheck_->modelName()}};
    }

    // Not a tomato leaf: no disease name, confidence, severity or disease advice (the disease model only knows
    // tomato classes and would name a tomato disease for any photo). Insects found by the pest detector are kept.
    const auto& top = ranking.front();
    const bool answered = isTomato && top.probability >= cfg_.diseaseThreshold;
    const std::string topic = answered ? top.label : "";
    nlohmann::json topK = nlohmann::json::array();
    for (size_t i = 0; isTomato && i < std::min<size_t>(3, ranking.size()); ++i)
        topK.push_back({{"class", ranking[i].label}, {"probability", ranking[i].probability}});
    result["disease"] = {{"top", topK}, {"answered", answered}, {"topic", answered ? nlohmann::json(topic) : nullptr},
                         {"name", answered ? nlohmann::json(kb_->topicName(topic, show)) : nullptr},
                         {"reliability", answered ? nlohmann::json(kb_->reliability(topic)) : nullptr},
                         {"urgent", answered && kb_->urgent(topic)}, {"not_tomato_leaf", !isTomato}};

    nlohmann::json pestJson = nlohmann::json::array();
    std::set<std::string> pestTopics;
    bool anyUnreliable = false;
    for (const auto& p : pests) {
        const std::string pt = kb_->pestTopic(p.speciesId, p.speciesReliable, p.topic);
        pestTopics.insert(pt);
        anyUnreliable |= !p.speciesReliable;
        pestJson.push_back({{"species_id", p.speciesId}, {"species", p.species}, {"species_reliable", p.speciesReliable},
                            {"confidence", p.confidence}, {"topic", pt}, {"name", kb_->topicName(pt, show)},
                            {"box_xyxy", {p.box.x, p.box.y, p.box.x + p.box.width, p.box.y + p.box.height}}});
    }
    result["pests"] = pestJson;
    // Pest severity of this photo: one level per pest topic, with the published scouting method / threshold
    const std::vector<PestSeverity> pestSev = pestSeverity(pests, *kb_, imageRgb.cols, imageRgb.rows);
    result["pest_severity"] = pestSeverityJson(pestSev, *kb_, show);

    if (answered && topic != "healthy") {
        t.reset();
        const SeverityResult s = severity_->estimate(imageRgb, topic);
        timings["severity"] = t.ms();
        auto share = [](double v) { return v < 0 ? nlohmann::json(nullptr) : nlohmann::json(std::round(v * 1000) / 1000); };
        result["severity"] = {{"level", s.level}, {"lesion_share", share(s.lesionShare)},
                              {"leaf_share", share(s.leafShare)}, {"method", "lesion_segmentation"},
                              {"model", severity_->modelName()}, {"validated", s.validated}};
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
            chunks.push_back(chunkJson(kb_->localized(c, show)));
            anySpray |= c.section == "chemical";
        }
        blocks.push_back({{"topic", tp}, {"name", kb_->topicName(tp, show)}, {"chunks", chunks}});
    }
    result["advice_blocks"] = blocks;
    timings["retrieval"] = t.ms();

    // Severe cases go to an extension worker (organisers' demo flow: "explain uncertainty and route severe cases to an
    // extension worker"): lesions on at least 25% of the leaf ("high"), an urgent disease (late blight), a virus disease
    // (severity "not_applicable" for a disease: leaf curl and mosaic viruses have no cure, infected plants are removed and
    // the whitefly or other spread is controlled), or a high pest level for this photo. The app also gets the flag.
    const std::string sevLevel = result.contains("severity") ? result["severity"].value("level", "") : "";
    const bool virus = answered && topic != "healthy" && sevLevel == "not_applicable";
    const bool severe = (answered && (kb_->urgent(topic) || sevLevel == "high" || virus)) ||
                        std::any_of(pestSev.begin(), pestSev.end(), [](const PestSeverity& s) { return s.level == "high"; });
    result["refer_to_expert"] = severe;
    result["supported_crops"] = nlohmann::json::array({"tomato"});   // crops whose leaf diseases are checked
    auto messagesIn = [&](const std::string& l) {
        nlohmann::json m = nlohmann::json::array();
        // Leaf disease and pests are equal tasks: a photo without a leaf of a supported crop but with insects is a pest
        // result, with a short note that no leaf disease was checked; "not_tomato" only when neither was found
        if (!isTomato) m.push_back(kb_->message(pests.empty() ? "not_tomato" : "no_leaf_checked", l));
        else if (!answered) m.push_back(kb_->message("uncertain", l));
        if (severe) m.push_back(kb_->message("severe_route", l));
        if (answered && kb_->reliability(topic) == "low") m.push_back(kb_->message("expert_confirm", l));
        if (anyUnreliable) m.push_back(kb_->message("pest_species_uncertain", l));
        if (anySpray) m.push_back(kb_->message("chemical_rule", l));
        return m;
    };
    result["messages"] = messagesIn(show);

    // English version of every text shown in another language, so the app can switch the result to English and
    // back without analysing the photo again (Llama's English text is in llama.text)
    if (show != "en") {
        nlohmann::json enBlocks = nlohmann::json::array();
        for (size_t b = 0; b < topics.size(); ++b) {
            nlohmann::json chunks = nlohmann::json::array();
            for (const auto& c : blockChunks[b]) chunks.push_back(chunkJson(kb_->localized(c, "en")));
            enBlocks.push_back({{"topic", topics[b]}, {"name", kb_->topicName(topics[b], "en")}, {"chunks", chunks}});
        }
        nlohmann::json pestNames = nlohmann::json::array();
        for (const auto& p : pests) pestNames.push_back(kb_->topicName(kb_->pestTopic(p.speciesId, p.speciesReliable, p.topic), "en"));
        result["en"] = {{"disease_name", answered ? nlohmann::json(kb_->topicName(topic, "en")) : nullptr},
                        {"pest_names", pestNames}, {"messages", messagesIn("en")}, {"advice_blocks", enBlocks},
                        {"pest_severity", pestSeverityJson(pestSev, *kb_, "en")}};
    }
    result["status"] = !topics.empty() ? "answered" : (isTomato ? "uncertain" : "not_tomato");
    result["llama"] = nullptr;

#ifdef KR_WITH_LLM
    if (llama_ && !topics.empty() && lang == "en" && tooHot) {
        // Thermal guard: no Llama while the CPU is this hot; the verified extracts are the advice
        result["llama"] = {{"text", nullptr}, {"accepted", false}, {"rejected_reasons", {"device_too_hot"}}};
    } else if (llama_ && !topics.empty() && lang == "en" &&
               static_cast<int>(blockChunks.front().size()) < kMinGroundedSentences) {
        // Too few source extracts (the generic insect topic has one): the answer could never have the minimum number
        // of grounded sentences, so Llama is not run (saves about 3 s); the verified extract is the advice
        result["llama"] = {{"text", nullptr}, {"accepted", false}, {"rejected_reasons", {"too_few_source_extracts"}}};
    } else if (llama_ && !topics.empty() && lang == "en") {
        // One-line structured summary for Llama (English); the facts are in the answer language
        std::string line;
        if (answered) {
            char conf[16];
            std::snprintf(conf, sizeof(conf), "%.0f%%", top.probability * 100.0);
            line = "Diagnosis: " + kb_->topicName(topic, "en") + " on a tomato leaf (model confidence " + conf + ").";
            // Severity from the validated lesion model only (61% level agreement with plant pathologists on
            // held-out field photos; the colour rule used before, 31%, is no longer used)
            if (result.contains("severity") && result["severity"]["validated"] == true)
                line += " Estimated spread on the photographed leaf: " + result["severity"]["level"].get<std::string>() + ".";
            if (kb_->urgent(topic)) line += " This disease is urgent: it spreads very fast.";
            if (kb_->reliability(topic) == "low")
                line += " The photo result is not certain; the farmer should confirm with the local KVK.";
        } else {
            // Same line as --eval-advisor. The insect count is not given to Llama: with the sentence "Insects of this
            // kind counted in the photo: N" the 1B model echoed it or wrote one sentence only, so every caterpillar,
            // mite and aphid photo was rejected (Pi full test, 2026-11-21). The count is shown in the app instead.
            line = "An insect pest was found on the tomato plant: " + kb_->topicName(topics.front(), "en") + ".";
        }
        t.reset();
        result["llama"] = runAdvisor(line, blockChunks.front(), topics.front(), lang);
        timings["llama"] = t.ms();
        // Only accepted (grounded and checked) English text is translated
        if (result["llama"]["accepted"].get<bool>())
            result["translation"] = translate(result["llama"]["text"].get<std::string>(), translateTo, timings);
    } else if (llama_ && lang == "hi") {
        // Llama 3.2 1B produced fluent but meaningless Hindi in tests: the Hindi page shows the reviewed Hindi
        // extracts only.
        result["llama"] = {{"text", nullptr}, {"accepted", false}, {"rejected_reasons", {"hindi_uses_reviewed_extracts"}}};
    }
#endif
    timings["total"] = total.ms();
    result["timings_ms"] = timings;
    // Device state for the technical details and the report: temperature before and after this photo, CPU clock
    result["device"] = {{"cpu_temp_start_c", tempStartC}, {"cpu_temp_end_c", readCpuTempC()},
                        {"cpu_freq_mhz", readCpuFreqMhz()}, {"llama_skipped_hot", tooHot && !topics.empty()}};
    return result;
}

#ifdef KR_WITH_LLM
nlohmann::json Pipeline::runAdvisor(const std::string& diagnosisLine, const std::vector<KbChunk>& facts,
                                    const std::string& topic, const std::string& lang) {
    const LlamaOutput out = llama_->advise(diagnosisLine, facts, lang);
    // 1. drop sentences not supported by the sources; 2. safety/language checks on what remains
    const GroundingResult gr = keepGroundedSentences(out.text, facts);
    GuardResult g = checkOutput(gr.kept, facts, lang, topic);
    if (gr.keptCount < kMinGroundedSentences) {
        g.ok = false;
        g.reasons.push_back("too_few_grounded_sentences:" + std::to_string(gr.keptCount));
    }
    return {{"text", g.ok ? nlohmann::json(gr.kept) : nullptr}, {"accepted", g.ok},
            {"grounded_sentences", gr.keptCount}, {"rejected_reasons", g.reasons},
            {"dropped_sentences", gr.dropped}, {"raw_text", out.text}, {"stats", out.stats}};
}
#endif

nlohmann::json Pipeline::evalAdvisor(const std::string& topic) {
    nlohmann::json r = {{"topic", topic}, {"name", kb_->topicName(topic, "en")}, {"llama", nullptr}};
    const auto facts = kb_->retrieveForDiagnosis(topic, "en");
    r["facts"] = static_cast<int>(facts.size());
#ifdef KR_WITH_LLM
    if (!llama_ || facts.empty()) return r;
    // Same diagnosis line as analyse() builds for a photo; a healthy leaf gets no spread estimate there
    std::string line;
    if (kb_->isPest(topic)) {
        line = "An insect pest was found on the tomato plant: " + kb_->topicName(topic, "en") + ".";
    } else {
        line = "Diagnosis: " + kb_->topicName(topic, "en") + " on a tomato leaf (model confidence 92%).";
        if (topic != "healthy") line += " Estimated spread on the photographed leaf: medium.";
        if (kb_->urgent(topic)) line += " This disease is urgent: it spreads very fast.";
        if (kb_->reliability(topic) == "low")
            line += " The photo result is not certain; the farmer should confirm with the local KVK.";
    }
    r["diagnosis_line"] = line;
    r["llama"] = runAdvisor(line, facts, topic, "en");
#endif
    return r;
}

nlohmann::json Pipeline::followUp(const std::string& question, const std::string& topic, const std::string& lang,
                                  const std::string& translateTo) {
    const auto facts = kb_->search(question, topic, 4, lang);
    nlohmann::json out = {{"question", question}, {"answer", nullptr}, {"accepted", false}, {"translation", nullptr}};
    nlohmann::json f = nlohmann::json::array();
    const std::string show = displayLanguage(lang, translateTo);
    for (const auto& c : facts) f.push_back(chunkJson(kb_->localized(c, show)));
    out["facts"] = f;
    if (facts.empty()) {
        out["answer"] = kb_->message("uncertain", show);
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
        if (g.ok) {
            nlohmann::json timings;
            out["translation"] = translate(gr.kept, translateTo, timings);
        }
    }
#endif
    (void)translateTo;   // used only with Llama
    return out;
}

}  // namespace kr
