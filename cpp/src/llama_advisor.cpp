/*
 * llama_advisor.cpp - Llama 3.2 1B Instruct through the ExecuTorch C++ LLM runner (see llama_advisor.hpp).
 *
 * Prompt design (measured on WSL, 2026-11-17): the full Hindi extracts made a 755-token prompt and a 28 s prefill,
 * so Llama now always receives a compact set of English facts (symptoms, spread, field practices; at most
 * kMaxFacts extracts) and is asked to answer in the requested language. Spray rows are never given to Llama.
 *
 * Tokens arrive as raw UTF-8 byte pieces; they are appended to one std::string, so a Devanagari character split
 * across two tokens is reassembled correctly (the Python binding fails on such splits).
 */
#include "llama_advisor.hpp"

#include "common.hpp"

#include <executorch/extension/llm/runner/llm_runner_helper.h>
#include <executorch/extension/llm/runner/text_llm_runner.h>
#include <executorch/extension/threadpool/threadpool.h>

#include <fcntl.h>
#include <unistd.h>

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <set>
#include <thread>

namespace kr {

namespace {

namespace llm = ::executorch::extension::llm;

// TextLLMRunner also prints every generated token to stdout. The application receives the tokens through the
// callback, and stdout carries the JSON result in CLI mode, so stdout is redirected to /dev/null while Llama
// generates and restored afterwards (RAII, also on exceptions).
class StdoutSilencer {
public:
    StdoutSilencer() {
        std::fflush(stdout);
        saved_ = ::dup(STDOUT_FILENO);
        const int devNull = ::open("/dev/null", O_WRONLY);
        if (saved_ >= 0 && devNull >= 0) ::dup2(devNull, STDOUT_FILENO);
        if (devNull >= 0) ::close(devNull);
    }
    ~StdoutSilencer() {
        std::fflush(stdout);
        if (saved_ >= 0) {
            ::dup2(saved_, STDOUT_FILENO);
            ::close(saved_);
        }
    }
    StdoutSilencer(const StdoutSilencer&) = delete;
    StdoutSilencer& operator=(const StdoutSilencer&) = delete;

private:
    int saved_ = -1;
};

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

// Detects a repeated sentence while tokens stream in. Text is split at '.', '!', '?', ';' and new lines; each
// completed sentence is normalised (lower-case letters only, list markers such as "IV." are too short to count) and
// compared with the sentences seen before in this answer.
class RepeatDetector {
public:
    // Adds the next token piece; returns true when it completes a sentence that was already written.
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
    bool finishSentence() {
        std::string key;
        int letters = 0;
        for (unsigned char ch : current_) {
            if (std::isalpha(ch)) { key += static_cast<char>(std::tolower(ch)); ++letters; }
            else if (std::isspace(ch) && !key.empty() && key.back() != ' ') key += ' ';
        }
        if (letters < 12) return false;          // list markers ("IV"), fragments: not a sentence
        return !seen_.insert(key).second;
    }
    std::string current_;
    std::set<std::string> seen_;
};

class ExecuTorchLlama final : public LlamaAdvisor {
public:
    ExecuTorchLlama(std::unique_ptr<llm::TextLLMRunner> runner, int maxNewTokens, float temperature)
        : runner_(std::move(runner)), maxNewTokens_(maxNewTokens), temperature_(temperature) {}

    LlamaOutput advise(const std::string& diagnosisLine, const std::vector<KbChunk>& facts,
                       const std::string& lang) override {
        // Rephrase-only prompt (tests showed the 1B model refusing on "do not name pesticides" wording and reversing
        // instructions when asked to "explain"): Llama rewrites each fact in simple words and nothing else.
        // The one-shot example is deliberately about another topic (grain storage): on the Raspberry Pi 5 the
        // earlier example (crop debris, overhead irrigation - also late blight advice) was copied as the answer and
        // repeated until the token limit. Copied example sentences are not in the extracts, so the grounding check
        // drops them.
        const std::string system =
            std::string("You rewrite agricultural extension text for tomato farmers in India. Rewrite each FACT in "
                        "simple ") +
            languageName(lang) + " as one short sentence. Keep the meaning of every fact exactly: do not add new "
            "advice, do not leave out an instruction and never turn an instruction into its opposite. Write each "
            "fact once, as plain sentences without a title, list markers or an introduction.\n\n"
            "Example (a different topic, only to show the style).\nFACTS:\n1. Cleaning of storage bins before "
            "filling with grain.\n2. Avoid storing grain in damp bags.\nRewritten facts:\nClean the bins before you "
            "put grain in them. Do not keep grain in wet bags.";
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

        LlamaOutput out = generate(llama3Chat(sys, user), lang);
        // Llama 3.2 1B sometimes refuses this harmless task outright ("I can't fulfill this request."), measured on
        // the Pi for 2 of 5 diseases. A refusal is short (about 2.5 s), so one retry with a plain fallback prompt
        // costs little; the stats report both attempts.
        if (looksLikeRefusal(out.text)) {
            const std::string fallbackSystem = "You are a helpful agricultural extension worker in India.";
            const std::string fallbackUser = "Here is advice for a tomato farmer:\n" + factsBlock(facts) +
                                             "\nSay the same advice again in simple " + languageName(lang) +
                                             ", one short sentence for each point.";
            LlamaOutput retry = generate(llama3Chat(fallbackSystem, fallbackUser), lang);
            retry.stats["first_attempt"] = {{"refused", true}, {"text", out.text}, {"stats", out.stats}};
            return retry;
        }
        return out;
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

private:
    LlamaOutput generate(const std::string& prompt, const std::string& lang) {
        llm::GenerationConfig cfg;
        cfg.echo = false;
        // Devanagari needs several tokens per word, so Hindi answers get a larger budget
        cfg.max_new_tokens = lang == "hi" ? maxNewTokens_ * 2 : maxNewTokens_;
        cfg.temperature = temperature_;
        cfg.num_bos = 0;   // <|begin_of_text|> is already part of the prompt text
        cfg.num_eos = 0;

        LlamaOutput out;
        // llm::Stats has a const member (not assignable), so copy the fields we report
        struct {
            long inferenceStart = 0, firstToken = 0, inferenceEnd = 0;
            int64_t promptTokens = 0, generatedTokens = 0;
        } st;
        runner_->reset();                       // clear the KV cache of the previous request
        Timer t;
        StdoutSilencer quiet;
        // Repetition stop: when a sentence is completed that was already written, the 1B model is looping
        // (seen on the Pi: two sentences alternated until the token limit, 11 s of wasted decoding). Generation is
        // stopped there; the grounding check removes the duplicate afterwards.
        RepeatDetector repeats;
        bool stoppedOnRepeat = false;
        const auto err = runner_->generate(
            prompt, cfg,
            [&](const std::string& piece) {
                out.text += piece;
                if (!stoppedOnRepeat && repeats.addAndCheck(piece)) {
                    stoppedOnRepeat = true;
                    runner_->stop();
                }
            },
            [&](const llm::Stats& s) {
                st.inferenceStart = s.inference_start_ms;
                st.firstToken = s.first_token_ms;
                st.inferenceEnd = s.inference_end_ms;
                st.promptTokens = s.num_prompt_tokens;
                st.generatedTokens = s.num_generated_tokens;
            });
        const double totalMs = t.ms();

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

        const double genMs = std::max<long>(1, st.inferenceEnd - st.firstToken);
        out.stats = {{"ok", err == ::executorch::runtime::Error::Ok},
                     {"prompt_tokens", st.promptTokens},
                     {"generated_tokens", st.generatedTokens},
                     {"time_to_first_token_s", (st.firstToken - st.inferenceStart) / 1000.0},
                     {"tokens_per_s", st.generatedTokens * 1000.0 / genMs},
                     {"total_s", totalMs / 1000.0},
                     {"stopped_on_repeat", stoppedOnRepeat}};
        return out;
    }

    std::unique_ptr<llm::TextLLMRunner> runner_;
    int maxNewTokens_;
    float temperature_;
};

}  // namespace

std::unique_ptr<LlamaAdvisor> LlamaAdvisor::create(const std::string& ptePath, const std::string& tokenizerPath,
                                                   int maxNewTokens, float temperature, int threads) {
    {
        std::ifstream a(ptePath), b(tokenizerPath);
        if (!a || !b) return nullptr;            // template mode: extracts only
    }
    // XNNPACK work is spread over this thread pool; 4 = the four Cortex-A76 cores of the Raspberry Pi 5
    if (threads > 0) ::executorch::extension::threadpool::get_threadpool()->_unsafe_reset_threadpool(threads);

    auto tokenizer = llm::load_tokenizer(tokenizerPath);
    if (!tokenizer) return nullptr;
    auto runner = llm::create_text_llm_runner(ptePath, std::move(tokenizer), std::optional<const std::string>{});
    if (!runner || runner->load() != ::executorch::runtime::Error::Ok) return nullptr;
    return std::make_unique<ExecuTorchLlama>(std::move(runner), maxNewTokens, temperature);
}

}  // namespace kr
