/*
 * llama_advisor.cpp - Llama 3.2 1B Instruct through the ExecuTorch C++ LLM runner (see llama_advisor.hpp).
 *
 * Prompt design (measured on WSL, 2026-11-17): the full Hindi extracts made a 755-token prompt and a 28 s prefill,
 * so Llama now always receives a compact set of English facts (symptoms, spread, field practices; at most
 * kMaxFacts extracts) and is asked to answer in the requested language. Spray rows are never given to Llama.
 *
 * Tokens arrive as raw UTF-8 byte pieces; they are appended to one std::string, so a Devanagari character split
 * across two tokens is reassembled correctly (the Python binding fails on such splits).
 *
 * Runtime: the building blocks of ExecuTorch's LLM runner (Module, TextDecoderRunner, TextPrefiller,
 * TextTokenGenerator), assembled as create_text_llm_runner() does in ExecuTorch 1.5.1. The high-level
 * TextLLMRunner hides the token generator, and the generator is needed for:
 *   - streaming: every token piece goes to the caller (web page) as soon as it is decoded;
 *   - steering the decoding towards the facts with a logit processor (FactSteering below, off by default).
 */
#include "llama_advisor.hpp"

#include "common.hpp"

// ExecuTorch marks the runner building blocks as experimental through the "deprecated" attribute, which would
// produce one warning per use. The API is pinned to ExecuTorch 1.5.1 (cpp/README.md).
#pragma GCC diagnostic ignored "-Wdeprecated-declarations"

#include <executorch/extension/llm/runner/constants.h>
#include <executorch/extension/llm/runner/io_manager/io_manager.h>
#include <executorch/extension/llm/runner/llm_runner_helper.h>
#include <executorch/extension/llm/runner/stats.h>
#include <executorch/extension/llm/runner/text_decoder_runner.h>
#include <executorch/extension/llm/runner/text_prefiller.h>
#include <executorch/extension/llm/runner/text_token_generator.h>
#include <executorch/extension/llm/sampler/logit_processor.h>
#include <executorch/extension/llm/sampler/sampler.h>
#include <executorch/extension/module/module.h>
#include <executorch/extension/threadpool/threadpool.h>
#include <pytorch/tokenizers/tokenizer.h>

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <limits>
#include <set>
#include <unordered_map>
#include <unordered_set>

namespace kr {

namespace {

namespace llm = ::executorch::extension::llm;
using ::executorch::extension::Module;
using ::executorch::runtime::Error;

constexpr int kMaxFacts = 4;
const char* kAllowedSections[] = {"symptoms", "cultural"};   // what it is, and what to do in the field

const char* languageName(const std::string& lang) { return lang == "hi" ? "Hindi" : "English"; }

// Byte offset just past the last sentence terminator ('.', '!', '?' or the Devanagari danda U+0964, UTF-8
// E0 A5 A4), or npos if the text has none.
size_t lastSentenceEnd(const std::string& text) {
    size_t best = std::string::npos;
    auto consider = [&](size_t pos, size_t len) {
        if (pos != std::string::npos && (best == std::string::npos || pos + len > best)) best = pos + len;
    };
    consider(text.rfind('.'), 1);
    consider(text.rfind('!'), 1);
    consider(text.rfind('?'), 1);
    consider(text.rfind("\xE0\xA5\xA4"), 3);
    return best;
}

std::string llama3Chat(const std::string& system, const std::string& user) {
    return "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n" + system +
           "<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n" + user +
           "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n";
}

// Compact numbered list of English facts for the diagnosis prompt
std::string factsBlock(const std::vector<KbChunk>& facts) {
    std::string out;
    int n = 0;
    for (const auto& c : facts) {
        if (std::find(std::begin(kAllowedSections), std::end(kAllowedSections), c.section) == std::end(kAllowedSections))
            continue;
        out += std::to_string(++n) + ". " + c.textEn + "\n";
        if (n == kMaxFacts) break;
    }
    return out;
}

void replaceAll(std::string& s, const std::string& from, const std::string& to) {
    for (size_t p = s.find(from); p != std::string::npos; p = s.find(from, p + to.size())) s.replace(p, from.size(), to);
}

// True for the short refusals Llama 3.2 1B produces ("I can't fulfill this request.", "I cannot help with that.")
bool looksLikeRefusal(const std::string& text) {
    std::string low;
    for (unsigned char ch : text.substr(0, 60)) low += static_cast<char>(std::tolower(ch));
    for (const char* p : {"i can't", "i cannot", "i can not", "i'm unable", "i am unable", "i won't"})
        if (low.rfind(p, 0) == 0) return true;
    return false;
}

// Detects a repeated sentence while tokens stream in. Text is split at '.', '!', '?', ';' and new lines. A completed
// sentence counts as a repeat when it is the same as an earlier one, or nearly the same: at least 80 % of their
// content words shared (Jaccard), as in "The disease is highly contagious and can spread quickly through the air."
// followed later by "The disease is also highly contagious and can spread quickly through the air." (Pi 5 run,
// 2026-11-18: not caught by exact matching, so 1B decoded to the 160-token limit). List markers ("IV.") and
// fragments are too short to count.
class RepeatDetector {
public:
    // Adds the next token piece; returns true when it completes a sentence that repeats an earlier one.
    bool addAndCheck(const std::string& piece) {
        for (char ch : piece) {
            if (ch == '.' || ch == '!' || ch == '?' || ch == ';' || ch == '\n') {
                const bool repeated = finishSentence();
                current_.clear();
                if (repeated) return true;
            } else {
                current_ += ch;
            }
        }
        return false;
    }

private:
    static bool isStopword(const std::string& w) {
        static const std::set<std::string> kStop = {"the", "and", "can", "also", "this", "that", "with", "from",
                                                    "into", "are", "was", "for", "its", "their", "very", "will"};
        return kStop.count(w) > 0;
    }

    bool finishSentence() {
        std::string key, word;
        std::set<std::string> words;
        int letters = 0;
        auto endWord = [&] {
            if (word.size() >= 3 && !isStopword(word)) words.insert(word);
            word.clear();
        };
        for (unsigned char ch : current_) {
            if (std::isalpha(ch)) {
                const char c = static_cast<char>(std::tolower(ch));
                key += c;
                word += c;
                ++letters;
            } else {
                endWord();
                if (std::isspace(ch) && !key.empty() && key.back() != ' ') key += ' ';
            }
        }
        endWord();
        if (letters < 12) return false;          // list markers ("IV"), fragments: not a sentence
        if (!seen_.insert(key).second) return true;
        if (words.size() >= 4) {
            for (const auto& prev : seenWords_) {
                size_t common = 0;
                for (const auto& w : words) common += prev.count(w);
                const size_t uni = words.size() + prev.size() - common;
                if (uni > 0 && common * 10 >= uni * 8) return true;
            }
            seenWords_.push_back(words);
        }
        return false;
    }
    std::string current_;
    std::set<std::string> seen_;
    std::vector<std::set<std::string>> seenWords_;
};

// Logit processor that steers decoding towards the facts given to Llama (both parts off by default):
//   bias:    adds `bias` to the logit of every token that occurs in the facts, so wording from the sources wins
//            close calls ("Remove infected plant parts" instead of a paraphrase the grounding check would drop);
//   blocked: forbids tokens of cause words that the facts do not contain. On the Pi, 1B wrote "The disease is
//            caused by a fungus" for late blight (a water mould); the facts never name a cause, so the sentence
//            could only be invented.
// The first token comes from prefill, which does not run logit processors; steering starts with the second.
class FactSteering final : public llm::LogitProcessor {
public:
    FactSteering(std::vector<uint64_t> boosted, std::vector<uint64_t> blocked, float bias)
        : boosted_(std::move(boosted)), blocked_(std::move(blocked)), bias_(bias) {}

    Error process(::executorch::aten::Tensor logits) override {
        if (logits.scalar_type() != ::executorch::aten::ScalarType::Float) return Error::Ok;   // fp32 export only
        const size_t vocab = logits.size(logits.dim() - 1);
        float* row = logits.mutable_data_ptr<float>() + (logits.numel() - vocab);              // last position
        for (uint64_t id : boosted_) if (id < vocab) row[id] += bias_;
        for (uint64_t id : blocked_) if (id < vocab) row[id] = -std::numeric_limits<float>::infinity();
        return Error::Ok;
    }

private:
    std::vector<uint64_t> boosted_, blocked_;
    float bias_;
};

// Words that name a cause or a pathogen group. Llama may write them only when the facts contain them.
const char* kCauseWords[] = {"fungus", "fungi", "fungal", "bacteria", "bacterial", "bacterium", "virus", "viral",
                             "caused", "infection", "mould", "mold", "pathogen"};

class ExecuTorchLlama final : public LlamaAdvisor {
public:
    explicit ExecuTorchLlama(const LlamaOptions& options) : opt_(options) {}

    // Builds the runtime pieces the way create_text_llm_runner() does (ExecuTorch 1.5.1) and loads the methods.
    bool load(const std::string& ptePath, const std::string& tokenizerPath) {
        tokenizer_ = llm::load_tokenizer(tokenizerPath);
        if (!tokenizer_ || !tokenizer_->is_loaded()) return false;
        module_ = std::make_unique<Module>(ptePath, Module::LoadMode::MmapUseMlockIgnoreErrors);
        auto meta = llm::get_llm_metadata(tokenizer_.get(), module_.get());
        if (meta.error() != Error::Ok) return false;
        metadata_ = meta.get();
        if (!metadata_.at(llm::kUseKVCache)) return false;     // the decode loop below needs a KV cache
        auto eos = std::make_unique<std::unordered_set<uint64_t>>(llm::get_eos_ids(tokenizer_.get(), module_.get()));
        ioManager_ = std::make_unique<llm::IOManager>(*module_);
        const auto vocab = static_cast<int32_t>(metadata_.at(llm::kVocabSize));
        decoder_ = std::make_unique<llm::TextDecoderRunner>(module_.get(), ioManager_.get(), "forward",
                                                            std::make_unique<llm::Sampler>(vocab, opt_.temperature),
                                                            &stats_);
        prefiller_ = std::make_unique<llm::TextPrefiller>(decoder_.get(), true, metadata_.at(llm::kEnableDynamicShape),
                                                          metadata_.at(llm::kMaxSeqLen));
        generator_ = std::make_unique<llm::TextTokenGenerator>(tokenizer_.get(), decoder_.get(), true, std::move(eos),
                                                               &stats_);
        if (prefiller_->load() != Error::Ok || ioManager_->load() != Error::Ok || generator_->load() != Error::Ok)
            return false;
        maxContext_ = metadata_.at(llm::kMaxContextLen);
        return true;
    }

    LlamaOutput advise(const std::string& diagnosisLine, const std::vector<KbChunk>& facts,
                       const std::string& lang, const TokenFn& onToken) override {
        // Rephrase-only prompt (tests showed the 1B model refusing on "do not name pesticides" wording and reversing
        // instructions when asked to "explain"): Llama rewrites each fact in simple words and nothing else.
        // The one-shot example is deliberately about another topic (grain storage): on the Raspberry Pi 5 the
        // earlier example (crop debris, overhead irrigation - also late blight advice) was copied as the answer and
        // repeated until the token limit. Copied example sentences are not in the extracts, so the grounding check
        // drops them.
        // "Keep the key words" (2026-11-18): Llama 3.2 3B rewrote faithfully but in its own words ("yellow edge" for
        // "yellow margin"), so the grounding check dropped correct sentences; asking it to keep the technical terms
        // raised the accepted answers on the five test photos from 6/10 to 7/10 (1B + 3B) with no distortion.
        // The same text is in prompts/advise_keep_words.txt for experiments with KR_ADVISOR_PROMPT.
        const std::string system =
            std::string("You rewrite agricultural extension text for tomato farmers in India. Rewrite each FACT in "
                        "simple ") +
            languageName(lang) + " as one short sentence. Keep the key words of the fact: the names of symptoms, "
            "plant parts, pests and actions (for example \"concentric rings\", \"margin\", \"lesions\", \"crop "
            "debris\", \"crop rotation\") stay as they are; only make the sentence shorter and easier to read. Keep "
            "the meaning of every fact exactly: do not add new advice, causes, months or numbers, do not leave out an "
            "instruction and never turn an instruction into its opposite. Write each fact once, as plain sentences "
            "without a title, list markers or an introduction.\n\n"
            "Example (a different topic, only to show the style).\nFACTS:\n1. Cleaning of storage bins before "
            "filling with grain.\n2. Avoid storing grain in damp bags.\nRewritten facts:\nClean the storage bins "
            "before filling them with grain. Avoid storing grain in damp bags.";
        std::string user = diagnosisLine + "\n\nFACTS:\n" + factsBlock(facts) + "\nRewritten facts:";

        // Development option: KR_ADVISOR_PROMPT=<file> replaces the prompt above, so prompt variants can be tried on
        // the Pi without rebuilding. File format: system text, a line "----USER----", user template; placeholders
        // {language}, {diagnosis}, {facts}.
        std::string sys = system;
        if (const char* path = std::getenv("KR_ADVISOR_PROMPT")) {
            const std::string file = readFile(path);
            const auto sep = file.find("----USER----");
            if (sep != std::string::npos) {
                auto fill = [&](std::string s) {
                    replaceAll(s, "{language}", languageName(lang));
                    replaceAll(s, "{diagnosis}", diagnosisLine);
                    replaceAll(s, "{facts}", factsBlock(facts));
                    const auto b = s.find_first_not_of("\n"), e = s.find_last_not_of("\n");
                    return b == std::string::npos ? std::string() : s.substr(b, e - b + 1);
                };
                sys = fill(file.substr(0, sep));
                user = fill(file.substr(sep + std::strlen("----USER----")));
            }
        }

        const std::string steerText = factsBlock(facts);
        LlamaOutput out = generate(llama3Chat(sys, user), lang, steerText, onToken);
        // Llama 3.2 1B sometimes refuses this harmless task outright ("I can't fulfill this request."), measured on
        // the Pi for 2 of 5 diseases. A refusal is short (about 2.5 s), so one retry with a plain fallback prompt
        // costs little; the stats report both attempts.
        if (looksLikeRefusal(out.text)) {
            const std::string fallbackSystem = "You are a helpful agricultural extension worker in India.";
            const std::string fallbackUser = "Here is advice for a tomato farmer:\n" + factsBlock(facts) +
                                             "\nSay the same advice again in simple " + languageName(lang) +
                                             ", one short sentence for each point.";
            if (onToken) onToken("\n\n");   // the streamed refusal stays visible; the retry follows it
            LlamaOutput retry = generate(llama3Chat(fallbackSystem, fallbackUser), lang, steerText, onToken);
            retry.stats["first_attempt"] = {{"refused", true}, {"text", out.text}, {"stats", out.stats}};
            return retry;
        }
        return out;
    }

    LlamaOutput answer(const std::string& question, const std::vector<KbChunk>& facts,
                       const std::string& lang, const TokenFn& onToken) override {
        const std::string system =
            std::string("You are KrishiRakshak, an assistant for tomato farmers in India. Answer the farmer's question "
                        "using ONLY the FACTS given by the user. If the FACTS do not answer the question, say that you "
                        "do not know and suggest asking the local KVK. Copy any product name and dose exactly as "
                        "written in the FACTS. Write in simple ") +
            languageName(lang) + ", in at most 4 short sentences, as plain text.";
        std::string lines;
        for (size_t i = 0; i < facts.size(); ++i) lines += std::to_string(i + 1) + ". " + facts[i].textEn + "\n";
        return generate(llama3Chat(system, "QUESTION: " + question + "\n\nFACTS:\n" + lines), lang, lines, onToken);
    }

private:
    std::vector<uint64_t> encode(const std::string& text) const {
        auto r = tokenizer_->encode(text, /*bos=*/0, /*eos=*/0);   // <|begin_of_text|> is part of the prompt text
        return r.ok() ? r.get() : std::vector<uint64_t>{};
    }

    // The steering processor for one request, or nullptr when both options are off.
    std::shared_ptr<FactSteering> makeSteering(const std::string& factsText) const {
        if (opt_.factBias == 0.0f && !opt_.blockCauseWords) return nullptr;
        std::unordered_set<uint64_t> factTokens;
        for (uint64_t id : encode(factsText)) factTokens.insert(id);
        std::vector<uint64_t> boosted, blocked;
        if (opt_.factBias != 0.0f) boosted.assign(factTokens.begin(), factTokens.end());
        if (opt_.blockCauseWords) {
            for (const char* w : kCauseWords) {
                const std::string word(w);
                std::string cap = word;
                cap[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(cap[0])));
                for (const std::string& form : {" " + word, " " + cap, cap}) {
                    const auto ids = encode(form);
                    // Only whole words that are one token: blocking the first piece of a longer word could also
                    // block unrelated words that start with the same piece.
                    if (ids.size() == 1 && !factTokens.count(ids[0])) blocked.push_back(ids[0]);
                }
            }
        }
        return std::make_shared<FactSteering>(std::move(boosted), std::move(blocked), opt_.factBias);
    }

    LlamaOutput generate(const std::string& prompt, const std::string& lang, const std::string& factsText,
                         const TokenFn& onToken) {
        LlamaOutput out;
        Timer total;
        stats_.reset();
        std::vector<uint64_t> tokens = encode(prompt);
        const int64_t promptTokens = static_cast<int64_t>(tokens.size());
        // Devanagari needs several tokens per word, so Hindi answers get a larger budget
        int maxNew = lang == "hi" ? opt_.maxNewTokens * 2 : opt_.maxNewTokens;
        maxNew = static_cast<int>(std::min<int64_t>(maxNew, maxContext_ - promptTokens - 1));

        generator_->clear_logit_processors();
        const auto steering = makeSteering(factsText);
        if (steering) generator_->add_logit_processor(steering);

        // Repetition stop: when a sentence is completed that repeats an earlier one, the 1B model is looping
        // (seen on the Pi: sentences repeated until the token limit, 6-11 s of wasted decoding). Generation is
        // stopped there; the grounding check removes the duplicate afterwards.
        RepeatDetector repeats;
        bool stoppedOnRepeat = false;
        auto onPiece = [&](const std::string& piece) {
            out.text += piece;
            if (onToken) onToken(piece);
            if (!stoppedOnRepeat && repeats.addAndCheck(piece)) {
                stoppedOnRepeat = true;
                generator_->stop();
            }
        };

        bool ok = false;
        double firstTokenMs = 0.0, decodeStartMs = 0.0;
        int64_t generated = 0;
        int64_t pos = 0;   // every request starts at cache position 0; stale entries above it are never read
        if (!tokens.empty() && maxNew > 0) {
            auto first = prefiller_->prefill(tokens, pos, opt_.temperature);   // pos -> end of the prompt
            if (first.ok()) {
                firstTokenMs = total.ms();
                const uint64_t cur = first.get();
                auto piece = tokenizer_->decode(cur, cur);
                if (piece.ok()) onPiece(piece.get());
                decodeStartMs = total.ms();
                if (!stoppedOnRepeat) {
                    auto gen = generator_->generate({cur}, pos, maxNew - 1, opt_.temperature, onPiece);
                    if (gen.ok()) {
                        generated = gen.get();
                        ok = true;
                    }
                } else {
                    ok = true;
                }
            }
        }
        generator_->clear_logit_processors();
        const double totalMs = total.ms();

        // Remove the end-of-turn marker if the tokenizer emitted it as text, and trim
        for (const std::string marker : {"<|eot_id|>", "<|end_of_text|>"}) {
            const auto p = out.text.find(marker);
            if (p != std::string::npos) out.text.erase(p);
        }
        // Drop a lead-in line such as "Here's an explanation in simple English:"
        const auto firstNl = out.text.find('\n');
        if (firstNl != std::string::npos && firstNl > 0 && out.text[out.text.find_last_not_of(" ", firstNl - 1)] == ':')
            out.text.erase(0, firstNl + 1);
        // If the token budget ended mid-sentence, cut back to the last complete sentence
        // ('.', '!', '?' or the Devanagari danda U+0964, UTF-8 E0 A5 A4)
        const size_t end = lastSentenceEnd(out.text);
        if (end != std::string::npos) out.text.erase(end);
        const auto b = out.text.find_first_not_of(" \n");
        out.text = b == std::string::npos ? "" : out.text.substr(b, out.text.find_last_not_of(" \n") - b + 1);

        // Same fields as before (TextLLMRunner semantics): generated_tokens counts the tokens after the first one
        const double genMs = std::max(1.0, totalMs - decodeStartMs);
        out.stats = {{"ok", ok},
                     {"prompt_tokens", promptTokens},
                     {"generated_tokens", generated},
                     {"time_to_first_token_s", firstTokenMs / 1000.0},
                     {"tokens_per_s", generated * 1000.0 / genMs},
                     {"total_s", totalMs / 1000.0},
                     {"stopped_on_repeat", stoppedOnRepeat},
                     {"fact_bias", opt_.factBias},
                     {"block_cause_words", opt_.blockCauseWords}};
        return out;
    }

    LlamaOptions opt_;
    std::unique_ptr<::tokenizers::Tokenizer> tokenizer_;
    std::unique_ptr<Module> module_;   // must outlive the runner pieces below
    std::unordered_map<std::string, int64_t> metadata_;
    llm::Stats stats_;
    std::unique_ptr<llm::IOManager> ioManager_;
    std::unique_ptr<llm::TextDecoderRunner> decoder_;
    std::unique_ptr<llm::TextPrefiller> prefiller_;
    std::unique_ptr<llm::TextTokenGenerator> generator_;
    int64_t maxContext_ = 0;
};

}  // namespace

std::unique_ptr<LlamaAdvisor> LlamaAdvisor::create(const std::string& ptePath, const std::string& tokenizerPath,
                                                   const LlamaOptions& options) {
    {
        std::ifstream a(ptePath), b(tokenizerPath);
        if (!a || !b) return nullptr;            // template mode: extracts only
    }
    // XNNPACK work is spread over this thread pool; 4 = the four Cortex-A76 cores of the Raspberry Pi 5
    if (options.threads > 0)
        ::executorch::extension::threadpool::get_threadpool()->_unsafe_reset_threadpool(options.threads);
    auto llama = std::make_unique<ExecuTorchLlama>(options);
    if (!llama->load(ptePath, tokenizerPath)) return nullptr;
    return llama;
}

}  // namespace kr
