/*
 * grounding_test.cpp - regression test for the sentence-level grounding check (output_guard.cpp).
 *
 * Each "dropped" case is a real unsafe sentence that Llama 3.2 1B produced during development (reversed
 * instruction, invented cause, answer stitched from unrelated extracts, changed number). Each "kept" case is a
 * faithful rewrite that must survive. Run from the repository root: build/x86/grounding_test
 */
#include "knowledge_base.hpp"
#include "output_guard.hpp"
#include <iostream>
int main(int argc, char** argv) {
    const std::string root = argc > 1 ? argv[1] : ".";
    kr::KnowledgeBase kb(root + "/app/kb/tomato_kb.json");
    struct Case { const char* topic; const char* question; const char* text; bool expectKept; };
    const Case cases[] = {
        {"late_blight", nullptr, "Remove infected plant parts.", true},
        {"late_blight", nullptr, "Avoid overhead irrigation.", true},
        {"late_blight", nullptr, "The disease is caused by a fungus that grows on the leaves and stems.", false},
        {"yellow_leaf_curl_virus", nullptr, "Do not try to remove the infected leaf or destroy it.", false},
        {"yellow_leaf_curl_virus", nullptr, "Remove and destroy infected plants in the nursery.", true},
        {"yellow_leaf_curl_virus", nullptr, "The tomato leaf curl virus is not spreading quickly.", false},
        {"late_blight", "when can I harvest after spraying", "You can harvest tomatoes 28 days after transplanting, but only after the first true leaves appear.", false},
        {"late_blight", "when can I harvest after spraying", "Do not apply pesticides during the 7 days before harvest.", true},
        {"late_blight", "when can I harvest after spraying", "Do not apply pesticides during the 3 days before harvest.", false},
    };
    int fails = 0;
    for (const auto& c : cases) {
        const auto facts = c.question ? kb.search(c.question, c.topic, 4, "en") : kb.retrieveForDiagnosis(c.topic, "en");
        const bool kept = kr::keepGroundedSentences(c.text, facts).keptCount == 1;
        fails += kept != c.expectKept;
        std::cout << (kept == c.expectKept ? "PASS " : "FAIL ") << (kept ? "kept    " : "dropped ") << c.text << "\n";
    }
    std::cout << fails << " failures\n";
    return fails != 0;
}
