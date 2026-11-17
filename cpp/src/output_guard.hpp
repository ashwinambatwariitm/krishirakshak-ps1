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
//   - at least minOverlap of its content words (4+ letters, not stop words, simple suffix stemming) occur in the
//     retrieved extracts, and
//   - if it contains a negation (not, never, avoid, don't ...), the best-matching source sentence contains one too.
struct GroundingResult {
    std::string kept;                       // grounded sentences, in their original order
    std::vector<std::string> dropped;       // sentences removed, for the technical panel and the report
    int keptCount = 0;
};

// minOverlap 0.75: at 0.6 "The disease is caused by a fungus ..." passed for late blight (a water mould; the
// sources never said "fungus"). Repeated sentences (the 1B model can loop) are dropped as well.
GroundingResult keepGroundedSentences(const std::string& text, const std::vector<KbChunk>& facts,
                                      double minOverlap = 0.75);

}  // namespace kr
