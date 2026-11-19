/*
 * knowledge_base.hpp - offline advisory knowledge base (the retrieval part of the RAG system).
 *
 * Source of truth: app/kb/tomato_kb.json - extracts from ICAR, NIPHM and TNAU publications, each with its source.
 * At start-up the JSON is loaded into an in-memory SQLite database with an FTS5 full-text index (SQLite is compiled
 * into the binary), so there is no separate database file to deploy or keep in sync.
 *
 * Two kinds of retrieval:
 *   retrieveForDiagnosis(topic)  deterministic: all extracts of the diagnosed disease/pest in reading order
 *                                (symptoms, spread, field practices, biological, resistant varieties), then at most
 *                                three spray options (per-litre ICAR doses first), then the safety rules
 *   search(question)             BM25 ranking over the English extracts for follow-up questions
 */
#pragma once

#include <json.hpp>

#include <map>
#include <memory>
#include <string>
#include <vector>

struct sqlite3;

namespace kr {

struct KbChunk {
    int id = 0;
    std::string topic, section, text, textEn;
    std::string product, dose, note;                 // only for section == "chemical"
    std::string noteEn;                              // the published note (note may be a translation)
    std::string sourceId, sourceOrg, sourceTitle, url;
};

class KnowledgeBase {
public:
    explicit KnowledgeBase(const std::string& jsonPath);
    ~KnowledgeBase();
    KnowledgeBase(const KnowledgeBase&) = delete;
    KnowledgeBase& operator=(const KnowledgeBase&) = delete;

    std::vector<KbChunk> retrieveForDiagnosis(const std::string& topic, const std::string& lang, int maxSprays = 3) const;
    std::vector<KbChunk> search(const std::string& question, const std::string& topic, int k,
                                const std::string& lang) const;
    // The first extract of a topic whose English text contains `phrase` (used to quote a specific published rule,
    // e.g. the NIPHM scouting method); false if there is none.
    bool findChunk(const std::string& topic, const std::string& phrase, const std::string& lang, KbChunk& out) const;

    // An extract shown in another language: text (and spray-row note) from the translations stored in the JSON,
    // English where a translation is missing; textEn, product and dose stay as published.
    KbChunk localized(KbChunk c, const std::string& lang) const;

    // Names and fixed messages in lang (en, hi or a translation language), English where a translation is missing
    std::string topicName(const std::string& topic, const std::string& lang) const;
    std::string message(const std::string& key, const std::string& lang) const;          // fixed reviewed text
    std::string qualityMessage(const std::string& issue, const std::string& lang) const;
    std::string reliability(const std::string& topic) const;                              // good / medium / low
    bool urgent(const std::string& topic) const;
    bool isPest(const std::string& topic) const;                                          // kind == "pest"
    std::string pestTopic(int speciesId, bool speciesReliable) const;
    std::string version() const { return kb_.value("version", ""); }
    bool reviewed() const { return kb_.value("content_reviewed", false); }

private:
    std::vector<KbChunk> query(const std::string& sql, const std::vector<std::string>& args,
                               const std::string& lang) const;
    void localize(KbChunk& c, const std::string& lang) const;
    nlohmann::json kb_;
    sqlite3* db_ = nullptr;
    std::map<int, std::string> pestTopicBySpecies_;
};

}  // namespace kr
