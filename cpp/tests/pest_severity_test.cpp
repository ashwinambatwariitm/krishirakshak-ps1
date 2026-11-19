/*
 * pest_severity_test.cpp - checks the per-photo pest severity rule (pest_severity.cpp) on constructed detections,
 * with the real knowledge base: level bands, grouping of species into topics, ordering, box union share, and that
 * every level quotes the published scouting method (and the fruit-borer threshold for caterpillars).
 * The Python reference (app/pipeline/pest_severity.py) is checked on the same cases by
 * tools/check_pest_severity.py. Run from the repository root: build/x86/pest_severity_test .
 */
#include "knowledge_base.hpp"
#include "pest_severity.hpp"

#include <iostream>
#include <string>

namespace {

int fails = 0;
void expect(bool ok, const std::string& what) {
    std::cout << (ok ? "  ok   " : "  FAIL ") << what << "\n";
    fails += !ok;
}

// n detections of one IP102 species, laid out in a row of 40 x 40 px boxes (photo 1000 x 1000)
std::vector<kr::PestDetection> insects(int speciesId, bool reliable, int n, float overlapStep = 50.f) {
    std::vector<kr::PestDetection> v;
    for (int i = 0; i < n; ++i) {
        kr::PestDetection d;
        d.speciesId = speciesId;
        d.speciesReliable = reliable;
        d.confidence = 0.5f;
        d.box = cv::Rect2f(10.f + overlapStep * (i % 18), 10.f + 60.f * (i / 18), 40.f, 40.f);
        v.push_back(d);
    }
    return v;
}

}  // namespace

int main(int argc, char** argv) {
    const std::string root = argc > 1 ? argv[1] : ".";
    kr::KnowledgeBase kb(root + "/app/kb/tomato_kb.json");
    const int APHIDS = 24, RED_SPIDER = 21, ARMY_WORM = 23;   // IP102 ids; only aphids is a reliable species

    std::cout << "level bands (aphids = colony insects)\n";
    for (auto [n, want] : std::vector<std::pair<int, const char*>>{{1, "low"}, {4, "low"}, {5, "moderate"},
                                                                    {19, "moderate"}, {20, "high"}, {35, "high"}}) {
        const auto s = kr::pestSeverity(insects(APHIDS, true, n), kb, 1000, 1000);
        expect(s.size() == 1 && s[0].topic == "aphids" && s[0].group == "colony" && s[0].count == n &&
                   s[0].level == want,
               std::to_string(n) + " aphids -> " + want);
    }

    std::cout << "species not identified reliably -> insect_other (uncertain, colony bands)\n";
    {
        const auto s = kr::pestSeverity(insects(RED_SPIDER, false, 6), kb, 1000, 1000);
        expect(s.size() == 1 && s[0].topic == "insect_other" && s[0].group == "uncertain" && s[0].level == "moderate",
               "6 unreliable red spider -> insect_other moderate");
    }

    std::cout << "chewing larvae (caterpillars topic, if the species were reliable)\n";
    {
        // army worm (23) belongs to the caterpillars topic; mark it reliable to exercise the chewing bands
        auto one = kr::pestSeverity(insects(ARMY_WORM, true, 1), kb, 1000, 1000);
        auto three = kr::pestSeverity(insects(ARMY_WORM, true, 3), kb, 1000, 1000);
        const bool isCaterpillar = !one.empty() && one[0].topic == "caterpillars";
        expect(isCaterpillar && one[0].group == "chewing" && one[0].level == "moderate", "1 caterpillar -> moderate");
        expect(isCaterpillar && three[0].level == "high", "3 caterpillars -> high");
        const auto j = kr::pestSeverityJson(one, kb, "en");
        expect(j[0]["threshold"].is_object() &&
                   j[0]["threshold"]["text"].get<std::string>().find("single larva per plant") != std::string::npos,
               "caterpillars quote the published fruit-borer threshold (single larva per plant)");
        expect(j[0]["scouting"].is_object() &&
                   j[0]["scouting"]["text"].get<std::string>().find("number of larvae") != std::string::npos,
               "caterpillars quote the NIPHM larvae count");
    }

    std::cout << "mixed photo: ordering and quotes\n";
    {
        auto pests = insects(APHIDS, true, 25);
        for (const auto& d : insects(RED_SPIDER, false, 2)) pests.push_back(d);
        const auto s = kr::pestSeverity(pests, kb, 1000, 1000);
        expect(s.size() == 2 && s[0].topic == "aphids" && s[0].level == "high" && s[1].topic == "insect_other" &&
                   s[1].level == "low",
               "most severe first: aphids high, then insect_other low");
        const auto j = kr::pestSeverityJson(s, kb, "en");
        expect(j[0]["scouting"]["text"].get<std::string>().find("five randomly selected leaves") != std::string::npos &&
                   j[0]["scouting"]["source_org"].get<std::string>().find("NIPHM") != std::string::npos,
               "aphids quote the NIPHM five-leaves count, with its source");
        expect(j[0]["threshold"].is_null(), "no threshold invented where the knowledge base has none");
        expect(j[1]["scouting"].is_object(), "uncertain insects quote the general scouting method");
        expect(j[0]["basis"] == "insects_in_this_photo", "level is labelled as this photo only");
    }

    std::cout << "box share: overlapping boxes counted once\n";
    {
        const auto apart = kr::pestSeverity(insects(APHIDS, true, 4, 50.f), kb, 1000, 1000);
        const auto stacked = kr::pestSeverity(insects(APHIDS, true, 4, 0.f), kb, 1000, 1000);
        expect(apart[0].boxShare > 3.5 * stacked[0].boxShare, "4 separate boxes cover ~4x the area of 4 stacked ones");
        expect(stacked[0].boxShare > 0.001 && stacked[0].boxShare < 0.003, "one 40x40 box on 1000x1000 ~ 0.16%");
    }

    std::cout << (fails ? "FAILED" : "ALL PASSED") << "\n";
    return fails != 0;
}
