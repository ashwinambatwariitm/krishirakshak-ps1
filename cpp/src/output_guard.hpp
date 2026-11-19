/*
 * output_guard.hpp - checks text written by Llama before it is shown to the farmer.
 *
 * Llama only rephrases retrieved extracts. An answer is rejected (and the application shows the verified extracts
 * without the Llama text) when it names a pesticide or a dose that is not in the retrieved extracts, is empty or
 * too long, is not mainly in the requested language, or names a different disease than the one diagnosed.
 * Text is UTF-8; Hindi is detected by counting Devanagari code points (U+0900 - U+097F).
 */
#pragma once

#include "knowledge_base.hpp"

#include <string>
#include <vector>

namespace kr {

struct GuardResult {
    bool ok = true;
    std::vector<std::string> reasons;
};

GuardResult checkOutput(const std::string& text, const std::vector<KbChunk>& facts, const std::string& lang,
                        const std::string& diagnosedTopic = "", size_t maxChars = 1200);

// Sentence-level grounding check for English Llama text (added after tests where Llama 3.2 1B reversed a source
// instruction: "do not remove the infected leaf"). A sentence is kept only if
//   - it has at least two different content words (3+ letters, not stop words, simple suffix stemming), and at
//     least minOverlap of them occur in ONE source sentence, all of them when it has fewer than five,
//   - a negation is matched by the same kind of negation in that source sentence (instruction: avoid, do not,
//     never; statement: is not, no, without), and a stated cause by a stated cause,
//   - an instruction (starts with an action verb) is not supported by a symptoms or spread extract,
//   - its numbers and month names are those of the source sentence (none invented, none left out once one is
//     used), and a disease name in it ("early blight") is the one in the source sentence.
// The rules and their test cases come from the 1B evaluation in docs/llama_1b_quality.md.
struct GroundingResult {
    std::string kept;                       // grounded sentences in their original order, each ending with punctuation
    std::vector<std::string> dropped;       // sentences removed, for the technical panel and the report
    int keptCount = 0;
};

// minOverlap 0.75: at 0.6 "The disease is caused by a fungus ..." passed for late blight (a water mould; the
// sources never said "fungus"). Repeated sentences (the 1B model can loop) are dropped as well.
GroundingResult keepGroundedSentences(const std::string& text, const std::vector<KbChunk>& facts,
                                      double minOverlap = 0.75);

// Splits English text into sentences with the same rule as the grounding check, so the translator receives
// exactly the sentences that were checked.
std::vector<std::string> sentencesOf(const std::string& text);

// The word lists of the grounding check (stop words, negations, same-meaning groups) and its threshold, so the
// Python copy used to build and score LoRA training data (llm/grounding.py) applies exactly the same rule.
nlohmann::json groundingConfig();

}  // namespace kr
