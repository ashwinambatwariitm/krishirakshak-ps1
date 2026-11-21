/*
 * translator.cpp - see translator.hpp.
 *
 * Per answer:
 *   each English sentence -> indic_text::preprocessEnglish -> "eng_Latn <tgt>" tags + SentencePiece pieces
 *   all sentences -> one CTranslate2 translate_batch call (beam 5, at most 256 tokens in and out)
 *   each result   -> indic_text::decodePieces -> indic_text::postprocess -> checks
 * The decoding options are the ones used when the model was evaluated in Python
 * (ctranslate2.Translator.translate_batch with beam_size=5, max_decoding_length=256, max_input_length=256).
 */
#include "translator.hpp"

#include "common.hpp"
#include "indic_text.hpp"

#include <ctranslate2/translator.h>
#include <sentencepiece_processor.h>

#include <fstream>
#include <stdexcept>

namespace kr {

namespace {

constexpr size_t kMaxTokens = 256;   // model limit for source and target (max_source/target_positions)

bool fileExists(const std::string& path) { return static_cast<bool>(std::ifstream(path)); }

class Ct2Translator : public Translator {
public:
    Ct2Translator(const std::string& modelDir, const std::string& spmPath, int threads, int beamSize)
        : beamSize_(beamSize) {
        const auto status = spm_.Load(spmPath);
        if (!status.ok()) throw std::runtime_error("SentencePiece: " + status.ToString());
        // One worker (replica) with `threads` threads; CPU, compute type as saved (INT8 weights).
        ctranslate2::ReplicaPoolConfig config;
        config.num_threads_per_replica = static_cast<size_t>(threads);
        translator_ = std::make_unique<ctranslate2::Translator>(modelDir, ctranslate2::Device::CPU,
                                                                ctranslate2::ComputeType::DEFAULT,
                                                                std::vector<int>{0}, false, config);
    }

    TranslationOutput translate(const std::vector<std::string>& sentences, const std::string& lang,
                                const Terms& terms) override {
        Timer timer;
        TranslationOutput out;
        out.lang = lang;
        const std::string flores = indic_text::floresCode(lang);
        if (flores.empty()) throw std::invalid_argument("translation not available for language: " + lang);

        // 1) pre-processing and tokenisation; empty sentences are not sent to the model
        std::vector<indic_text::PlaceholderMap> maps;
        std::vector<std::vector<std::string>> batch;
        std::vector<size_t> index;   // batch row -> sentence
        out.sentences.resize(sentences.size());
        for (size_t i = 0; i < sentences.size(); ++i) {
            out.sentences[i].english = sentences[i];
            // Terms first: each one becomes an ASCII marker word ("KRTERMA") that the glossary and the Moses
            // tokenizer leave alone, and after pre-processing a placeholder restored as the local text
            std::string english = sentences[i];
            std::vector<std::pair<std::string, std::string>> markers;   // marker -> local text
            for (size_t k = 0; k < terms.size() && k < 26; ++k) {
                if (terms[k].first.empty() || terms[k].second.empty()) continue;
                const std::string marker = std::string("KRTERM") + static_cast<char>('A' + k);
                std::string lower = english, term = terms[k].first;
                std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);
                std::transform(term.begin(), term.end(), term.begin(), ::tolower);
                bool found = false;
                for (size_t pos = lower.find(term); pos != std::string::npos; pos = lower.find(term, pos + marker.size())) {
                    english.replace(pos, term.size(), marker);
                    lower.replace(pos, term.size(), marker);
                    found = true;
                }
                if (found) markers.emplace_back(marker, terms[k].second);
            }
            // glossary (plain English translates correctly), then the IndicTrans2 pre-processing
            indic_text::Prepared p = indic_text::preprocessEnglish(indic_text::plainEnglish(english), flores);
            for (const auto& m : markers) indic_text::addTermPlaceholder(p, m.first, m.second);
            // p.text = "eng_Latn <tgt> <text>": the two tags are tokens of their own, the text goes to SentencePiece
            const size_t a = p.text.find(' '), b = p.text.find(' ', a + 1);
            const std::string body = b == std::string::npos ? std::string() : p.text.substr(b + 1);
            if (body.empty()) continue;
            std::vector<std::string> tokens = {p.text.substr(0, a), p.text.substr(a + 1, b - a - 1)};
            std::vector<std::string> pieces;
            const auto status = spm_.Encode(body, &pieces);
            if (!status.ok()) throw std::runtime_error("SentencePiece: " + status.ToString());
            tokens.insert(tokens.end(), pieces.begin(), pieces.end());
            batch.push_back(std::move(tokens));
            maps.push_back(p.placeholders);
            index.push_back(i);
        }

        // 2) the model: all sentences of the answer in one batch
        if (!batch.empty()) {
            ctranslate2::TranslationOptions options;
            options.beam_size = static_cast<size_t>(beamSize_);
            options.max_input_length = kMaxTokens;
            options.max_decoding_length = kMaxTokens;
            Timer modelTimer;
            const std::vector<ctranslate2::TranslationResult> results = translator_->translate_batch(batch, options);
            out.modelMs = modelTimer.ms();

            // 3) post-processing and checks
            for (size_t r = 0; r < results.size(); ++r) {
                TranslatedSentence& s = out.sentences[index[r]];
                const std::vector<std::string>& pieces = results[r].hypotheses.at(0);
                s.complete = pieces.size() < kMaxTokens;
                s.text = indic_text::postprocess(indic_text::decodePieces(pieces), flores, maps[r]);
                s.repetition = indic_text::hasRepetition(s.text);
                const bool placeholderLeft = s.text.find("<ID") != std::string::npos ||
                                             s.text.find("[ID") != std::string::npos;
                s.ok = s.complete && !s.repetition && !placeholderLeft && !s.text.empty();
            }
        }
        for (const TranslatedSentence& s : out.sentences) {
            if (s.english.empty()) continue;
            if (!s.ok) ++out.withheld;
            const std::string& shown = s.ok ? s.text : s.english;
            if (!shown.empty()) out.text += (out.text.empty() ? "" : " ") + shown;
        }
        out.ms = timer.ms();
        return out;
    }

private:
    int beamSize_;
    sentencepiece::SentencePieceProcessor spm_;
    std::unique_ptr<ctranslate2::Translator> translator_;
};

}  // namespace

nlohmann::json TranslationOutput::toJson() const {
    nlohmann::json j;
    j["lang"] = lang;
    j["text"] = text;
    j["withheld"] = withheld;
    j["ms"] = ms;
    j["model_ms"] = modelMs;
    j["reviewed"] = false;   // machine translation, not yet checked by a fluent speaker
    nlohmann::json rows = nlohmann::json::array();
    for (const TranslatedSentence& s : sentences)
        rows.push_back({{"english", s.english}, {"text", s.text}, {"ok", s.ok},
                        {"complete", s.complete}, {"repetition", s.repetition}});
    j["sentences"] = rows;
    return j;
}

const std::vector<std::string>& Translator::supportedLanguages() {
    static const std::vector<std::string> langs = {"hi", "te", "mr", "kn", "ta", "bn", "gu", "or", "pa"};
    return langs;
}

std::unique_ptr<Translator> Translator::create(const std::string& modelDir, const std::string& spmPath, int threads,
                                               int beamSize) {
    if (!fileExists(modelDir + "/model.bin") || !fileExists(spmPath)) return nullptr;
    return std::make_unique<Ct2Translator>(modelDir, spmPath, threads, beamSize);
}

}  // namespace kr
