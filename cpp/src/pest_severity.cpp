/*
 * pest_severity.cpp - see pest_severity.hpp. Same rule and constants as the Python reference
 * app/pipeline/pest_severity.py.
 */
#include "pest_severity.hpp"

#include <algorithm>
#include <cmath>
#include <map>
#include <set>

namespace kr {

namespace {

const std::set<std::string> kColony = {"aphids", "whitefly", "mites", "thrips", "leafhoppers", "mealybug"};
const std::set<std::string> kChewing = {"caterpillars", "helicoverpa_fruit_borer", "spodoptera_tobacco_caterpillar",
                                        "cutworm", "tuta_absoluta_pinworm", "serpentine_leaf_miner"};

// Published extracts quoted with each level: knowledge-base topic + a phrase of the extract
struct Quote { const char* topic; const char* phrase; };
Quote scoutingQuote(const std::string& topic, const std::string& group) {
    if (topic == "thrips") return {"thrips", "For thrips:"};
    if (topic == "serpentine_leaf_miner") return {"serpentine_leaf_miner", "For leaf miner:"};
    if (group == "colony") return {"aesa_monitoring", "For sucking pests:"};                 // NIPHM AESA
    if (group == "chewing") return {"helicoverpa_fruit_borer", "For Helicoverpa and Spodoptera:"};
    return {"aesa_monitoring", "select five spots randomly"};
}
bool thresholdQuote(const std::string& topic, Quote& q) {
    // Only economic threshold in the knowledge base that applies to a detectable insect: fruit borer (TNAU)
    if (topic == "helicoverpa_fruit_borer" || topic == "caterpillars") {
        q = {"helicoverpa_fruit_borer", "Economic Threshold Level (ETL): 8 eggs"};
        return true;
    }
    return false;
}

std::string levelFor(const std::string& group, int count) {
    if (group == "chewing") return count >= 3 ? "high" : "moderate";
    return count >= 20 ? "high" : (count >= 5 ? "moderate" : "low");   // colony and uncertain
}

int levelRank(const std::string& level) { return level == "high" ? 3 : (level == "moderate" ? 2 : 1); }

// Share of the photo covered by the union of the boxes, measured on a 256 x 256 grid (exact enough for a display
// value; overlapping boxes of one colony are counted once).
double unionShare(const std::vector<cv::Rect2f>& boxes, int w, int h) {
    constexpr int G = 256;
    std::vector<unsigned char> grid(G * G, 0);
    for (const auto& b : boxes) {
        const int x0 = std::max(0, static_cast<int>(std::floor(b.x / w * G)));
        const int y0 = std::max(0, static_cast<int>(std::floor(b.y / h * G)));
        const int x1 = std::min(G, static_cast<int>(std::ceil((b.x + b.width) / w * G)));
        const int y1 = std::min(G, static_cast<int>(std::ceil((b.y + b.height) / h * G)));
        for (int y = y0; y < y1; ++y)
            for (int x = x0; x < x1; ++x) grid[y * G + x] = 1;
    }
    return static_cast<double>(std::count(grid.begin(), grid.end(), 1)) / (G * G);
}

nlohmann::json quoteJson(const KnowledgeBase& kb, const Quote& q, const std::string& lang) {
    KbChunk c;
    if (!kb.findChunk(q.topic, q.phrase, lang, c)) return nullptr;
    return {{"text", c.text}, {"source_org", c.sourceOrg}, {"source_title", c.sourceTitle}, {"url", c.url}};
}

}  // namespace

std::vector<PestSeverity> pestSeverity(const std::vector<PestDetection>& pests, const KnowledgeBase& kb,
                                       int imageWidth, int imageHeight) {
    std::map<std::string, std::vector<cv::Rect2f>> byTopic;
    for (const auto& p : pests) byTopic[kb.pestTopic(p.speciesId, p.speciesReliable, p.topic)].push_back(p.box);
    std::vector<PestSeverity> out;
    for (const auto& [topic, boxes] : byTopic) {
        PestSeverity s;
        s.topic = topic;
        s.group = kColony.count(topic) ? "colony" : (kChewing.count(topic) ? "chewing" : "uncertain");
        s.count = static_cast<int>(boxes.size());
        s.boxShare = unionShare(boxes, imageWidth, imageHeight);
        s.level = levelFor(s.group, s.count);
        out.push_back(s);
    }
    std::stable_sort(out.begin(), out.end(), [](const PestSeverity& a, const PestSeverity& b) {
        if (levelRank(a.level) != levelRank(b.level)) return levelRank(a.level) > levelRank(b.level);
        return a.count > b.count;
    });
    return out;
}

nlohmann::json pestSeverityJson(const std::vector<PestSeverity>& sev, const KnowledgeBase& kb, const std::string& lang) {
    nlohmann::json arr = nlohmann::json::array();
    for (const auto& s : sev) {
        Quote t{};
        const bool hasThreshold = thresholdQuote(s.topic, t);
        arr.push_back({{"topic", s.topic}, {"name", kb.topicName(s.topic, lang)}, {"group", s.group},
                       {"count", s.count}, {"box_share", std::round(s.boxShare * 1000.0) / 1000.0},
                       {"level", s.level}, {"basis", "insects_in_this_photo"},
                       {"scouting", quoteJson(kb, scoutingQuote(s.topic, s.group), lang)},
                       {"threshold", hasThreshold ? quoteJson(kb, t, lang) : nlohmann::json(nullptr)}});
    }
    return arr;
}

}  // namespace kr
