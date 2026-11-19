/*
 * grounding_test.cpp - regression test for the sentence-level grounding check (output_guard.cpp).
 *
 * Each "dropped" case is a real unsafe sentence that Llama 3.2 1B produced during development (reversed
 * instruction, invented cause, answer stitched from unrelated extracts, changed number). Each "kept" case is a
 * faithful rewrite that must survive. Run from the repository root: build/x86/grounding_test
 *
 * Replay mode re-checks the Llama text of saved krishirakshak results (JSON, one result per file) with the current
 * check, without running Llama again; used to measure changes to the check on real 1B / 3B answers:
 *   build/x86/grounding_test . --replay bench/*_llama*_en.json
 *
 * Dump mode writes, for every knowledge-base topic, the extracts the pipeline retrieves for a diagnosis and the
 * ones Llama receives, plus the grounding word lists; input of the LoRA training notebook:
 *   build/x86/grounding_test . --dump-facts results/llama_lora/prompt_facts.json
 */
#include "knowledge_base.hpp"
#include "output_guard.hpp"
#include <fstream>
#include <iostream>
#include <string>

namespace {

// Same acceptance rule as Pipeline::analyse: grounded sentences, then the safety/language checks, then at least
// two grounded sentences (kMinGroundedSentences in pipeline.cpp)
int replay(const kr::KnowledgeBase& kb, int argc, char** argv, int first) {
    int accepted = 0, total = 0;
    for (int i = first; i < argc; ++i) {
        std::ifstream in(argv[i]);
        const auto r = nlohmann::json::parse(in, nullptr, false);
        if (r.is_discarded() || !r.contains("llama") || !r["llama"].contains("raw_text") || !r.contains("disease")) {
            std::cout << "skip " << argv[i] << " (no English Llama text)\n";
            continue;
        }
        const std::string topic = r["disease"].value("topic", "");
        const auto facts = kb.retrieveForDiagnosis(topic, "en");
        const auto gr = kr::keepGroundedSentences(r["llama"]["raw_text"].get<std::string>(), facts);
        const auto g = kr::checkOutput(gr.kept, facts, "en", topic);
        const bool ok = g.ok && gr.keptCount >= 2;
        accepted += ok; ++total;
        std::cout << (ok ? "ACCEPT " : "REJECT ") << argv[i] << " (" << topic << "): kept " << gr.keptCount
                  << ", dropped " << gr.dropped.size() << "\n    kept: " << gr.kept << "\n";
        for (const auto& d : gr.dropped) std::cout << "    dropped: " << d << "\n";
    }
    std::cout << accepted << " of " << total << " answers accepted\n";
    return 0;
}

// Same selection as factsBlock() in llama_advisor.cpp: symptoms and cultural extracts, at most four
constexpr int kMaxFacts = 4;
bool givenToLlama(const kr::KbChunk& c) { return c.section == "symptoms" || c.section == "cultural"; }

int dumpFacts(const kr::KnowledgeBase& kb, const std::string& root, const std::string& outPath) {
    std::ifstream in(root + "/app/kb/tomato_kb.json");
    const auto kbJson = nlohmann::json::parse(in);
    nlohmann::json out = {{"kb_version", kb.version()}, {"grounding", kr::groundingConfig()}, {"topics", nlohmann::json::array()}};
    for (const auto& [topic, info] : kbJson["topics"].items()) {
        const auto facts = kb.retrieveForDiagnosis(topic, "en");
        nlohmann::json all = nlohmann::json::array(), given = nlohmann::json::array();
        for (const auto& c : facts) {
            all.push_back({{"section", c.section}, {"text", c.textEn}});
            if (givenToLlama(c) && static_cast<int>(given.size()) < kMaxFacts) given.push_back(c.textEn);
        }
        out["topics"].push_back({{"topic", topic}, {"kind", info.value("kind", "")}, {"name", kb.topicName(topic, "en")}, {"urgent", kb.urgent(topic)},
                                 {"reliability", kb.reliability(topic)}, {"grounding_facts", all}, {"llama_facts", given}});
    }
    std::ofstream(outPath) << out.dump(1) << "\n";
    std::cout << "wrote " << out["topics"].size() << " topics to " << outPath << "\n";
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    const std::string root = argc > 1 ? argv[1] : ".";
    kr::KnowledgeBase kb(root + "/app/kb/tomato_kb.json");
    if (argc > 2 && std::string(argv[2]) == "--replay") return replay(kb, argc, argv, 3);
    if (argc > 3 && std::string(argv[2]) == "--dump-facts") return dumpFacts(kb, root, argv[3]);
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
        // Llama 3.2 3B: the carrier became the cause (source: "The virus is spread by whiteflies (Bemisia tabaci)")
        {"yellow_leaf_curl_virus", nullptr, "This is caused by whiteflies (Bemisia tabaci).", false},
        {"yellow_leaf_curl_virus", nullptr, "The virus is spread by whiteflies (Bemisia tabaci).", true},
        // Llama 3.2 3B faithful rewrites in plain words (same-meaning groups: edge = margin, spots = lesions)
        {"septoria_leaf_spot", nullptr, "Small, round spots with a grey center and dark edge on leaves.", true},
        {"early_blight", nullptr, "Get rid of the leftover crop debris.", true},
        // Llama 3.2 1B, laptop evaluation 18-19 Nov 2026 (docs/llama_1b_quality.md). All were KEPT by the check at
        // the time; they mark the grounding gaps to close (short words such as "rot" not checked, "plant" a stop word,
        // a negated rewrite matched to a negated "avoid" source, a symptom turned into an instruction, a changed or
        // invented word allowed because 3 of 4 words match, a one-word header).
        // Reversal - source: "Avoid use of infested farmyard manure, soil crop debris and compost in the field."
        {"collar_rot", nullptr, "The disease is not spread through the use of infested farmyard manure, soil crop debris, and compost in the field.", false},
        // Wrong plant part / generic claim - source: "Water-soaked black lesions on leaves and stems." and
        // "It enlarges rapidly until entire leaves are killed ..."
        {"late_blight", nullptr, "The disease is a black rot on tomato leaves.", false},
        {"late_blight", nullptr, "The disease is killing the entire plant.", false},
        // Symptom turned into an instruction - source: "Pre-emergence phase: Complete rotting of seedlings."
        {"damping_off", nullptr, "Prevent seedlings from rotting completely.", false},
        // Reads as an instruction to infect - source: "... infection of the young, juvenile tissues of the collar ..."
        {"damping_off", nullptr, "Infect young, juvenile tissues of the collar.", false},
        // Purpose taken from the prompt's one-shot example (grain storage) - source: "Use raised beds of 15 cm height."
        {"damping_off", nullptr, "Use raised beds of 15 cm height to dry grain.", false},
        // Schedule changed and dose left out - source: "Apply neem cake ... @ 250 kg/ha at planting and repeat after 25 days."
        {"serpentine_leaf_miner", nullptr, "Apply neem cake to furrows (open)/beds (polyhouse) every 25 days.", false},
        // Symptom changed - source: "Centre of spots become slightly raised, tan coloured and rough."
        {"bacterial_canker", nullptr, "Spots become slightly wrinkled.", false},
        // Wrong plant part - source: "Lower leaves drop before wilting."
        {"bacterial_wilt", nullptr, "The wilting is happening on the lower leaves.", false},
        // Made stronger - source: "Generally lower portion of fruits are infected which are coming in soil contact."
        {"fruit_rots", nullptr, "The disease is most severe in the lower portion of the fruit.", false},
        // Wrong disease name - source: "Early blight is first observed on the plants as small, black lesions ..."
        {"early_blight", nullptr, "Fruit blight observed on plants as small black lesions.", false},
        // Season changed - source: "Disease appear in severe forms during the month of September to November."
        {"yellow_leaf_curl_virus", nullptr, "Disease appears in September.", false},
        // Nonsense joined from two facts - source: "Young larvae feed on tender foliage."
        {"helicoverpa_fruit_borer", nullptr, "Larvae feed on the leaves while feeding the caterpillar.", false},
        // Description turned into an instruction - source: "While feeding the caterpillar thrust its head inside
        // leaving the rest of the body outside."
        {"helicoverpa_fruit_borer", nullptr, "Leave the rest of the body outside.", false},
        // Number without its meaning - source: "Grow simultaneously 40 days old American tall marigold and 25 days old
        // tomato seedling at 1:16 rows."
        {"helicoverpa_fruit_borer", nullptr, "Grow simultaneously 40.", false},
        // A markdown header is not advice, but one matching word is 100% of its content words and it counted towards
        // the two grounded sentences (an answer of headers and fragments only was accepted)
        {"tuta_absoluta_pinworm", nullptr, "**Pests**", false},
        // Faithful 1B rewrites that must stay
        {"healthy", nullptr, "Use only necessary, label-claimed pesticides.", true},
        {"septoria_leaf_spot", nullptr, "Spots start on lower leaves and gradually advance upwards.", true},
        {"fruit_rots", nullptr, "Staking of plant to avoid fruit contact.", true},
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
