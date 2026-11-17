/*
 * llama_advisor.cpp - Llama 3.2 1B Instruct through the ExecuTorch C++ LLM runtime (see llama_advisor.hpp).
 *
 * Prompt design (measured on WSL, 2026-11-17): the full Hindi extracts made a 755-token prompt and a 28 s prefill,
 * so Llama now always receives a compact set of English facts (symptoms, spread, field practices; at most
 * kMaxFacts extracts) and is asked to answer in the requested language. Spray rows are never given to Llama.
 *
 * Prefix cache. Every diagnosis prompt starts with the same system instructions and example; only the diagnosis
 * line and the facts change. Prefill is the slow, compute-bound phase (about 5-7 s on WSL for 295 tokens), and its
 * cost grows with the number of prompt tokens. So the fixed start of the prompt is prefilled ONCE (at load time),
 * and each request rewinds the KV cache position to the end of that prefix and prefills only its own tokens:
 *
 *     KV cache positions:  [0 ........ P)  [P ............ P+S)  [P+S ...... )
 *                           fixed prefix    this request's part    generated tokens
 *                           (kept)          (overwritten each time)
 *
 * This is safe because the attention kernel only reads cache positions below the current position (positions
 * left over from the previous request are never read; ExecuTorch's own reset() relies on the same property when
 * it rewinds to 0 without clearing the cache). Two conditions are checked on every request, with a fall back to a
 * full prefill when either fails:
 *   - tokenizing prefix and rest separately gives exactly the tokens of the whole prompt (otherwise the cached
 *     prefix would not be the start of this prompt);
 *   - the prefix currently in the cache is the one this prompt needs (the follow-up answer has another system
 *     prompt; switching re-prefills the new prefix, and the next diagnosis switches back).
 *
 * The high-level TextLLMRunner cannot do this (its position counter is private and reset() always goes back to
 * 0), so this file drives the runner's building blocks directly: Module, TextDecoderRunner, TextPrefiller and
 * TextTokenGenerator, assembled the same way as create_text_llm_runner() in ExecuTorch 1.5.1.
 *
 * Tokens arrive as raw UTF-8 byte pieces; they are appended to one std::string, so a Devanagari character split
 * across two tokens is reassembled correctly.
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
#include <executorch/extension/llm/sampler/sampler.h>
#include <executorch/extension/module/module.h>
#include <executorch/extension/threadpool/threadpool.h>
#include <pytorch/tokenizers/tokenizer.h>

#include <algorithm>
#include <cstdlib>
#include <fstream>
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

// Llama 3 chat format, split into the part that is the same for every request of one kind (system prompt up to
// the start of the user turn) and the part that changes (user turn and the assistant header).
struct ChatPrompt {
    std::string prefix;
    std::string rest;
};

ChatPrompt llama3Chat(const std::string& system, const std::string& user) {
    return {"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n" + system +
                "<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n",
            user + "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"};
}

std::string advisorSystemPrompt(const std::string& lang) {
    // Rephrase-only prompt (tests showed the 1B model refusing on "do not name pesticides" wording and reversing
    // instructions when asked to "explain"): Llama rewrites each fact in simple words and nothing else.
    return std::string("You rewrite agricultural extension text for tomato farmers in India. Rewrite each FACT in "
                       "simple ") +
           languageName(lang) + " as one short sentence. Keep the meaning of every fact exactly: do not add new "
           "advice, do not leave out an instruction and never turn an instruction into its opposite. Write each "
           "fact once, as plain sentences without a title, list markers or an introduction.\n\n"
           "Example.\nFACTS:\n1. Removal and destruction of crop debris.\n2. Avoid overhead irrigation.\n"
           "Rewritten facts:\nRemove the old plant waste from the field and destroy it. Do not water the plants "
           "from above.";
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

// Removes end markers and lead-in lines and cuts the text back to the last complete sentence.
void tidy(std::string& text) {
    for (const std::string marker : {"<|eot_id|>", "<|end_of_text|>"}) {
        const auto p = text.find(marker);
        if (p != std::string::npos) text.erase(p);
    }
    // Drop a lead-in line such as "Here's an explanation in simple English:"
    const auto firstNl = text.find('\n');
    if (firstNl != std::string::npos && firstNl > 0 && text[text.find_last_not_of(" ", firstNl - 1)] == ':')
        text.erase(0, firstNl + 1);
    const size_t end = lastSentenceEnd(text);
    if (end != std::string::npos) text.erase(end);
    const auto b = text.find_first_not_of(" \n");
    text = b == std::string::npos ? "" : text.substr(b, text.find_last_not_of(" \n") - b + 1);
}

class ExecuTorchLlama final : public LlamaAdvisor {
public:
    ExecuTorchLlama(int maxNewTokens, float temperature, bool prefixCache)
        : maxNewTokens_(maxNewTokens), temperature_(temperature), prefixCache_(prefixCache) {}

    // Builds the runtime pieces the way create_text_llm_runner() does (ExecuTorch 1.5.1) and loads the methods.
    bool load(const std::string& ptePath, const std::string& tokenizerPath) {
        tokenizer_ = llm::load_tokenizer(tokenizerPath);
        if (!tokenizer_ || !tokenizer_->is_loaded()) return false;
        module_ = std::make_unique<Module>(ptePath, Module::LoadMode::MmapUseMlockIgnoreErrors);
        auto meta = llm::get_llm_metadata(tokenizer_.get(), module_.get());
        if (meta.error() != Error::Ok) return false;
        metadata_ = meta.get();
        if (!metadata_.at(llm::kUseKVCache)) return false;   // the prefix cache and the decode loop need a KV cache
        auto eos = std::make_unique<std::unordered_set<uint64_t>>(llm::get_eos_ids(tokenizer_.get(), module_.get()));
        ioManager_ = std::make_unique<llm::IOManager>(*module_);
        const auto vocab = static_cast<int32_t>(metadata_.at(llm::kVocabSize));
        decoder_ = std::make_unique<llm::TextDecoderRunner>(module_.get(), ioManager_.get(), "forward",
                                                            std::make_unique<llm::Sampler>(vocab, temperature_),
                                                            &stats_);
        prefiller_ = std::make_unique<llm::TextPrefiller>(decoder_.get(), true,
                                                          metadata_.at(llm::kEnableDynamicShape),
                                                          metadata_.at(llm::kMaxSeqLen));
        generator_ = std::make_unique<llm::TextTokenGenerator>(tokenizer_.get(), decoder_.get(), true,
                                                               std::move(eos), &stats_);
        if (prefiller_->load() != Error::Ok || ioManager_->load() != Error::Ok || generator_->load() != Error::Ok)
            return false;
        maxContext_ = metadata_.at(llm::kMaxContextLen);
        // Prefill the diagnosis prefix now, so that the first farmer request already benefits
        if (prefixCache_) {
            Timer t;
            ensurePrefix(llama3Chat(advisorSystemPrompt("en"), "").prefix);
            prefixLoadMs_ = t.ms();
        }
        return true;
    }

    LlamaOutput advise(const std::string& diagnosisLine, const std::vector<KbChunk>& facts,
                       const std::string& lang) override {
        const std::string user = diagnosisLine + "\n\nFACTS:\n" + factsBlock(facts) + "\nRewritten facts:";
        return generate(llama3Chat(advisorSystemPrompt(lang), user), lang);
    }

    LlamaOutput answer(const std::string& question, const std::vector<KbChunk>& facts,
                       const std::string& lang) override {
        const std::string system =
            std::string("You are KrishiRakshak, an assistant for tomato farmers in India. Answer the farmer's question "
                        "using ONLY the FACTS given by the user. If the FACTS do not answer the question, say that you "
                        "do not know and suggest asking the local KVK. Copy any product name and dose exactly as "
                        "written in the FACTS. Write in simple ") +
            languageName(lang) + ", in at most 4 short sentences, as plain text.";
        std::string lines;
        for (size_t i = 0; i < facts.size(); ++i) lines += std::to_string(i + 1) + ". " + facts[i].textEn + "\n";
        return generate(llama3Chat(system, "QUESTION: " + question + "\n\nFACTS:\n" + lines), lang);
    }

    nlohmann::json info() const override {
        return {{"prefix_cache", prefixCache_}, {"prefix_tokens", prefixTokens_}, {"prefix_prefill_ms", prefixLoadMs_},
                {"max_context", maxContext_}};
    }

private:
    std::vector<uint64_t> encode(const std::string& text) {
        auto r = tokenizer_->encode(text, /*bos=*/0, /*eos=*/0);   // <|begin_of_text|> is part of the text
        return r.ok() ? r.get() : std::vector<uint64_t>{};
    }

    // Makes sure the KV cache positions [0, prefixTokens_) hold `prefix`. Returns false on a runtime error.
    bool ensurePrefix(const std::string& prefix) {
        if (cachedPrefix_ == prefix && prefixTokens_ > 0) return true;
        cachedPrefix_.clear();
        prefixTokens_ = 0;
        auto tokens = encode(prefix);
        if (tokens.empty()) return false;
        int64_t pos = 0;
        auto res = prefiller_->prefill(tokens, pos, temperature_);   // advances pos to the end of the prefix
        if (!res.ok()) return false;
        cachedPrefix_ = prefix;
        prefixTokens_ = pos;
        return true;
    }

    LlamaOutput generate(const ChatPrompt& prompt, const std::string& lang) {
        LlamaOutput out;
        Timer total;
        stats_.reset();
        // Debug: KR_DUMP_PROMPT=file writes the full prompt text (input of cpp/tools/prefill_check)
        if (const char* dump = std::getenv("KR_DUMP_PROMPT")) std::ofstream(dump) << prompt.prefix + prompt.rest;
        const auto all = encode(prompt.prefix + prompt.rest);

        // Decide what to prefill: only the rest (prefix cached) or the whole prompt
        std::vector<uint64_t> toPrefill;
        int64_t pos = 0;
        bool reused = false;
        std::string cacheNote;
        if (prefixCache_) {
            const auto head = encode(prompt.prefix);
            const auto tail = encode(prompt.rest);
            const bool splitOk = !head.empty() && head.size() + tail.size() == all.size() &&
                                 std::equal(head.begin(), head.end(), all.begin()) &&
                                 std::equal(tail.begin(), tail.end(), all.begin() + head.size());
            if (!splitOk) {
                cacheNote = "split_mismatch";
            } else {
                const bool hit = cachedPrefix_ == prompt.prefix && prefixTokens_ > 0;
                cacheNote = hit ? "hit" : "miss";
                if (ensurePrefix(prompt.prefix)) {
                    toPrefill = tail;
                    pos = prefixTokens_;
                    reused = true;
                }
            }
        }
        if (!reused) {
            cachedPrefix_.clear();   // a full prefill overwrites the cached prefix positions
            prefixTokens_ = 0;
            toPrefill = all;
            pos = 0;
        }

        int64_t generated = 0;
        bool ok = false;
        int64_t firstTokenMs = 0, genStartMs = 0;
        const int64_t prefilled = static_cast<int64_t>(toPrefill.size());
        // Devanagari needs several tokens per word, so Hindi answers get a larger budget
        int maxNew = lang == "hi" ? maxNewTokens_ * 2 : maxNewTokens_;
        maxNew = static_cast<int>(std::min<int64_t>(maxNew, maxContext_ - pos - prefilled - 1));
        if (!toPrefill.empty() && maxNew > 0) {
            auto first = prefiller_->prefill(toPrefill, pos, temperature_);   // pos -> end of the prompt
            if (first.ok()) {
                // from the start of the request: includes tokenizing and, on a cache miss, the prefix prefill
                firstTokenMs = static_cast<int64_t>(total.ms());
                const uint64_t cur = first.get();
                auto piece = tokenizer_->decode(cur, cur);
                if (piece.ok()) out.text += piece.get();
                genStartMs = static_cast<int64_t>(total.ms());
                auto gen = generator_->generate({cur}, pos, maxNew - 1, temperature_,
                                                [&](const std::string& p) { out.text += p; });
                if (gen.ok()) {
                    generated = gen.get();   // tokens after the first one, as TextLLMRunner counted them
                    ok = true;
                }
            }
        }
        if (!ok) {
            cachedPrefix_.clear();   // state unknown after an error: prefill the prefix again next time
            prefixTokens_ = 0;
        }
        const double totalMs = total.ms();
        tidy(out.text);

        const double genMs = std::max<double>(1.0, totalMs - genStartMs);
        out.stats = {{"ok", ok},
                     {"prompt_tokens", static_cast<int64_t>(all.size())},
                     {"prefilled_tokens", prefilled},
                     {"prefix_cache", prefixCache_ ? cacheNote : "off"},
                     {"generated_tokens", generated},
                     {"time_to_first_token_s", firstTokenMs / 1000.0},
                     // decode rate: tokens after the first one (which comes from prefill) per second of decoding
                     {"tokens_per_s", generated > 0 ? generated * 1000.0 / genMs : 0.0},
                     {"total_s", totalMs / 1000.0}};
        return out;
    }

    int maxNewTokens_;
    float temperature_;
    bool prefixCache_;
    std::unique_ptr<::tokenizers::Tokenizer> tokenizer_;
    std::unique_ptr<Module> module_;   // must outlive the runner pieces below
    std::unordered_map<std::string, int64_t> metadata_;
    llm::Stats stats_;
    std::unique_ptr<llm::IOManager> ioManager_;
    std::unique_ptr<llm::TextDecoderRunner> decoder_;
    std::unique_ptr<llm::TextPrefiller> prefiller_;
    std::unique_ptr<llm::TextTokenGenerator> generator_;
    int64_t maxContext_ = 0;
    std::string cachedPrefix_;     // prompt text whose KV entries are in positions [0, prefixTokens_)
    int64_t prefixTokens_ = 0;
    double prefixLoadMs_ = 0.0;
};

}  // namespace

std::unique_ptr<LlamaAdvisor> LlamaAdvisor::create(const std::string& ptePath, const std::string& tokenizerPath,
                                                   int maxNewTokens, float temperature, int threads,
                                                   bool prefixCache) {
    {
        std::ifstream a(ptePath), b(tokenizerPath);
        if (!a || !b) return nullptr;            // template mode: extracts only
    }
    // XNNPACK work is spread over this thread pool; 4 = the four Cortex-A76 cores of the Raspberry Pi 5
    if (threads > 0) ::executorch::extension::threadpool::get_threadpool()->_unsafe_reset_threadpool(threads);

    auto llama = std::make_unique<ExecuTorchLlama>(maxNewTokens, temperature, prefixCache);
    if (!llama->load(ptePath, tokenizerPath)) return nullptr;
    return llama;
}

}  // namespace kr
