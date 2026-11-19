/*
 * knowledge_base.cpp - see knowledge_base.hpp. Behaviour matches the Python reference app/pipeline/knowledge.py.
 */
#include "knowledge_base.hpp"

#include "common.hpp"

#include <sqlite3.h>

#include <algorithm>
#include <cctype>
#include <set>
#include <stdexcept>

namespace kr {

namespace {

const std::vector<std::string> kSectionOrder = {"symptoms", "spread", "cultural", "mechanical", "biological",
                                                "natural_enemies", "resistant_varieties", "monitoring", "nutrition",
                                                "chemical", "safety"};
// Extracts shown per section for one diagnosis (the knowledge base has up to ~35 per topic since tomato_kb_v3);
// the oldest extracts come first, so the facts given to Llama are unchanged. Follow-up search sees all extracts.
constexpr int kMaxPerSection = 3;
// Spray options: per-litre ICAR doses first (easiest for a farmer to measure), then NIPHM, then the rest
const std::map<std::string, int> kSourcePriority = {{"ICAR_LB", 0}, {"ICAR_IPM", 1}, {"NIPHM", 2}};

// Words with no retrieval value (otherwise "how to stop whitefly" matches on "to")
const std::set<std::string> kStopwords = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "could", "do", "does", "for", "from", "how", "i", "if",
    "in", "is", "it", "its", "me", "my", "of", "on", "or", "our", "should", "so", "that", "the", "their", "them",
    "then", "there", "these", "this", "to", "us", "was", "we", "what", "when", "where", "which", "who", "why",
    "will", "with", "you", "your", "use", "using", "get"};
// Farmer words -> words used in the source documents
const std::map<std::string, std::vector<std::string>> kSynonyms = {
    {"harvest", {"harvest", "waiting"}}, {"medicine", {"spray"}}, {"dawai", {"spray"}}, {"dose", {"spray"}},
    {"pesticide", {"pesticide", "spray"}}, {"fungicide", {"spray"}}, {"organic", {"neem", "trichoderma", "biological"}},
    {"neem", {"neem", "azadirachtin"}}, {"insects", {"insect", "pest"}}, {"variety", {"variety", "varieties", "resistant"}},
    {"seed", {"seed", "seeds"}}};

void exec(sqlite3* db, const std::string& sql) {
    char* err = nullptr;
    if (sqlite3_exec(db, sql.c_str(), nullptr, nullptr, &err) != SQLITE_OK) {
        const std::string msg = err ? err : "unknown";
        sqlite3_free(err);
        throw std::runtime_error("sqlite: " + msg);
    }
}

// RAII prepared statement
struct Stmt {
    sqlite3_stmt* s = nullptr;
    Stmt(sqlite3* db, const std::string& sql) {
        if (sqlite3_prepare_v2(db, sql.c_str(), -1, &s, nullptr) != SQLITE_OK)
            throw std::runtime_error(std::string("sqlite prepare: ") + sqlite3_errmsg(db));
    }
    ~Stmt() { sqlite3_finalize(s); }
    void bind(int i, const std::string& v) { sqlite3_bind_text(s, i, v.c_str(), -1, SQLITE_TRANSIENT); }
    void bind(int i, int v) { sqlite3_bind_int(s, i, v); }
    std::string col(int i) const {
        const auto* t = sqlite3_column_text(s, i);
        return t ? reinterpret_cast<const char*>(t) : "";
    }
};

std::string chunkText(const nlohmann::json& c) {
    if (c.at("section") == "chemical") {
        std::string t = "Spray " + c.at("product").get<std::string>() + " @ " + c.at("dose").get<std::string>() + ".";
        const std::string note = c.value("note", "");
        return note.empty() ? t : t + " " + note;
    }
    return c.at("en").get<std::string>();
}

}  // namespace

KnowledgeBase::KnowledgeBase(const std::string& jsonPath) {
    kb_ = nlohmann::json::parse(readFile(jsonPath));
    if (sqlite3_open(":memory:", &db_) != SQLITE_OK) throw std::runtime_error("cannot open in-memory sqlite");
    exec(db_, "CREATE TABLE sources (id TEXT PRIMARY KEY, org TEXT, title TEXT, url TEXT);"
              "CREATE TABLE chunks (id INTEGER PRIMARY KEY, topic TEXT, section TEXT, source TEXT, text_en TEXT,"
              " text_hi TEXT, product TEXT, dose TEXT, note TEXT);"
              "CREATE VIRTUAL TABLE chunks_fts USING fts5(text, topic_name, content='', tokenize='porter unicode61');");

    exec(db_, "BEGIN");
    for (auto& [sid, s] : kb_.at("sources").items()) {
        Stmt st(db_, "INSERT INTO sources VALUES (?,?,?,?)");
        st.bind(1, sid); st.bind(2, s.at("org").get<std::string>());
        st.bind(3, s.at("title").get<std::string>()); st.bind(4, s.at("url").get<std::string>());
        sqlite3_step(st.s);
    }
    int id = 0;
    for (const auto& c : kb_.at("chunks")) {
        ++id;
        const std::string topic = c.at("topic"), text = chunkText(c);
        if (!kb_.at("topics").contains(topic) || !kb_.at("sources").contains(c.at("source").get<std::string>()))
            throw std::runtime_error("knowledge base: unknown topic or source in chunk " + std::to_string(id));
        Stmt st(db_, "INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?,?)");
        st.bind(1, id); st.bind(2, topic); st.bind(3, c.at("section").get<std::string>());
        st.bind(4, c.at("source").get<std::string>()); st.bind(5, text); st.bind(6, c.value("hi", ""));
        st.bind(7, c.value("product", "")); st.bind(8, c.value("dose", "")); st.bind(9, c.value("note", ""));
        sqlite3_step(st.s);
        Stmt fts(db_, "INSERT INTO chunks_fts (rowid, text, topic_name) VALUES (?,?,?)");
        fts.bind(1, id); fts.bind(2, text);
        fts.bind(3, kb_.at("topics").at(topic).at("name").at("en").get<std::string>());
        sqlite3_step(fts.s);
    }
    exec(db_, "COMMIT");

    for (auto& [tid, t] : kb_.at("topics").items())
        if (t.contains("species_ids"))
            for (int sid : t.at("species_ids")) pestTopicBySpecies_[sid] = tid;
}

KnowledgeBase::~KnowledgeBase() { sqlite3_close(db_); }

std::vector<KbChunk> KnowledgeBase::query(const std::string& sql, const std::vector<std::string>& args,
                                          const std::string& lang) const {
    Stmt st(db_, sql);
    for (size_t i = 0; i < args.size(); ++i) st.bind(static_cast<int>(i + 1), args[i]);
    std::vector<KbChunk> out;
    while (sqlite3_step(st.s) == SQLITE_ROW) {
        KbChunk c;
        c.id = sqlite3_column_int(st.s, 0);
        c.topic = st.col(1); c.section = st.col(2); c.sourceId = st.col(3);
        c.textEn = st.col(4);
        const std::string hi = st.col(5);
        c.text = (lang == "hi" && !hi.empty()) ? hi : c.textEn;
        c.product = st.col(6); c.dose = st.col(7); c.note = st.col(8);
        const auto& src = kb_.at("sources").at(c.sourceId);
        c.sourceOrg = src.at("org"); c.sourceTitle = src.at("title"); c.url = src.at("url");
        out.push_back(std::move(c));
    }
    return out;
}

std::vector<KbChunk> KnowledgeBase::retrieveForDiagnosis(const std::string& topic, const std::string& lang,
                                                         int maxSprays) const {
    auto rows = query("SELECT * FROM chunks WHERE topic = ? ORDER BY id", {topic}, lang);
    std::vector<KbChunk> sprays, others;
    for (auto& c : rows) (c.section == "chemical" ? sprays : others).push_back(c);

    auto prio = [](const KbChunk& c) {
        const auto it = kSourcePriority.find(c.sourceId);
        return it == kSourcePriority.end() ? 9 : it->second;
    };
    std::stable_sort(sprays.begin(), sprays.end(), [&](const KbChunk& a, const KbChunk& b) { return prio(a) < prio(b); });
    if (static_cast<int>(sprays.size()) > maxSprays) sprays.resize(maxSprays);

    auto secIdx = [](const KbChunk& c) {
        return std::find(kSectionOrder.begin(), kSectionOrder.end(), c.section) - kSectionOrder.begin();
    };
    std::stable_sort(others.begin(), others.end(), [&](const KbChunk& a, const KbChunk& b) { return secIdx(a) < secIdx(b); });

    std::vector<KbChunk> out;
    std::map<std::string, int> perSection;
    for (auto& c : others)
        if (c.section != "safety" && ++perSection[c.section] <= kMaxPerSection) out.push_back(c);
    out.insert(out.end(), sprays.begin(), sprays.end());
    if (!sprays.empty()) {   // the safety rules always follow spray advice
        auto safety = query("SELECT * FROM chunks WHERE topic = 'general' AND section = 'safety' ORDER BY id", {}, lang);
        out.insert(out.end(), safety.begin(), safety.end());
    }
    return out;
}

std::vector<KbChunk> KnowledgeBase::search(const std::string& question, const std::string& topic, int k,
                                           const std::string& lang) const {
    // Tokenise to lower-case ASCII words, drop stop words, expand synonyms
    std::set<std::string> terms;
    std::string word;
    auto flush = [&]() {
        if (!word.empty() && !kStopwords.count(word)) {
            const auto it = kSynonyms.find(word);
            if (it == kSynonyms.end()) terms.insert(word);
            else terms.insert(it->second.begin(), it->second.end());
        }
        word.clear();
    };
    for (unsigned char ch : question) {
        if (std::isalnum(ch) && ch < 128) word += static_cast<char>(std::tolower(ch));
        else flush();
    }
    flush();
    if (terms.empty()) return {};

    std::string match;
    for (const auto& t : terms) match += (match.empty() ? "\"" : " OR \"") + t + "\"";

    // bm25() is lower = better; chunks of the topic being discussed get a fixed bonus
    Stmt st(db_, "SELECT c.id, c.topic, bm25(chunks_fts) FROM chunks_fts JOIN chunks c ON c.id = chunks_fts.rowid "
                 "WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT 30");
    st.bind(1, match);
    std::vector<std::pair<double, int>> ranked;
    while (sqlite3_step(st.s) == SQLITE_ROW) {
        const double score = sqlite3_column_double(st.s, 2) - (!topic.empty() && st.col(1) == topic ? 2.0 : 0.0);
        ranked.emplace_back(score, sqlite3_column_int(st.s, 0));
    }
    std::stable_sort(ranked.begin(), ranked.end(), [](const auto& a, const auto& b) { return a.first < b.first; });

    std::vector<KbChunk> out;
    for (int i = 0; i < std::min<int>(k, static_cast<int>(ranked.size())); ++i) {
        auto rows = query("SELECT * FROM chunks WHERE id = ?", {std::to_string(ranked[i].second)}, lang);
        out.insert(out.end(), rows.begin(), rows.end());
    }
    return out;
}

bool KnowledgeBase::findChunk(const std::string& topic, const std::string& phrase, const std::string& lang,
                              KbChunk& out) const {
    // instr() is an exact, case-sensitive substring test (LIKE would treat % and _ in the phrase as wildcards)
    const auto rows = query("SELECT * FROM chunks WHERE topic = ? AND instr(text_en, ?) > 0 ORDER BY id LIMIT 1",
                            {topic, phrase}, lang);
    if (rows.empty()) return false;
    out = rows.front();
    return true;
}

std::string KnowledgeBase::topicName(const std::string& topic, const std::string& lang) const {
    return kb_.at("topics").at(topic).at("name").at(lang);
}
std::string KnowledgeBase::message(const std::string& key, const std::string& lang) const {
    return kb_.at("messages").at(key).at(lang);
}
std::string KnowledgeBase::qualityMessage(const std::string& issue, const std::string& lang) const {
    return kb_.at("messages").at("quality").at(issue).at(lang);
}
std::string KnowledgeBase::reliability(const std::string& topic) const {
    return kb_.at("topics").at(topic).value("model_reliability", "");
}
bool KnowledgeBase::urgent(const std::string& topic) const {
    return kb_.at("topics").at(topic).value("urgent", false);
}
std::string KnowledgeBase::pestTopic(int speciesId, bool speciesReliable) const {
    if (!speciesReliable) return "insect_other";
    const auto it = pestTopicBySpecies_.find(speciesId);
    return it == pestTopicBySpecies_.end() ? "insect_other" : it->second;
}

}  // namespace kr
