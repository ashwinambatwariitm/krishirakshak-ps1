/*
 * llama_advisor.hpp - advisory stage: Llama 3.2 1B Instruct on the device through the ExecuTorch C++ runtime
 * (XNNPACK backend, 4-bit weights). This is the generation part of the RAG system.
 *
 * Llama receives the diagnosis and the verified extracts retrieved from the knowledge base and writes a short
 * explanation in English or Hindi. It does not diagnose and does not write spray doses (spray options are shown
 * exactly as published). Every answer passes output_guard before it is shown.
 *
 * The interface is always available; the implementation (llama_advisor.cpp) is compiled only when the project is
 * built with ExecuTorch (-DEXECUTORCH_ROOT=...). Without it the pipeline runs in template mode (extracts only).
 */
#pragma once

#include "knowledge_base.hpp"

#include <json.hpp>

#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace kr {

struct LlamaOutput {
    std::string text;
    nlohmann::json stats;    // prompt/generated tokens, time to first token, tokens per second, total seconds
};

// Called with every generated text piece as soon as it is decoded (for streaming to the web page).
using TokenFn = std::function<void(const std::string&)>;

struct LlamaOptions {
    int maxNewTokens = 160;
    float temperature = 0.0f;
    int threads = 4;               // XNNPACK thread pool (4 on the Raspberry Pi 5; 0 = ExecuTorch default)
    // Decoding steered towards the facts (both off by default; measured with --eval-advisor before enabling):
    float factBias = 0.0f;         // added to the logit of every token that occurs in the facts given to Llama
    bool blockCauseWords = false;  // forbid single-token cause words (fungus, bacteria, virus...) absent from the facts
};

class LlamaAdvisor {
public:
    virtual ~LlamaAdvisor() = default;

    // Explanation of a diagnosis from the retrieved extracts (spray rows are not given to Llama).
    virtual LlamaOutput advise(const std::string& diagnosisLine, const std::vector<KbChunk>& facts,
                               const std::string& lang, const TokenFn& onToken = {}) = 0;
    // Answer to a follow-up question from the retrieved extracts (product names and doses copied verbatim).
    virtual LlamaOutput answer(const std::string& question, const std::vector<KbChunk>& facts,
                               const std::string& lang, const TokenFn& onToken = {}) = 0;

    // Loads the .pte and tokenizer from local disk; returns nullptr if the files are missing.
    static std::unique_ptr<LlamaAdvisor> create(const std::string& ptePath, const std::string& tokenizerPath,
                                                const LlamaOptions& options);
};

}  // namespace kr
