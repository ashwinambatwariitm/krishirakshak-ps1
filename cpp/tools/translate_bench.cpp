/*
 * translate_bench.cpp - timing and parity run of the C++ translation stage (translator.cpp) on saved Llama
 * answers, for comparison with the Python CTranslate2 runs on the same device.
 *
 * Input: JSON {"answers": [{"id", "language", "sentences": [{"english": ...}, ...]}, ...]} (the reference file of
 * the IndicTrans2 evaluation). Each answer is translated as one batch, as in the pipeline. Output JSON: per-answer
 * time, every translated sentence, load time and peak memory (ru_maxrss).
 *
 *   translate_bench --model models/indictrans2_en_indic_200M_ct2_int8 --spm models/indictrans2_model.SRC \
 *                   --answers hf_reference.json [--threads 2] [--per-lang N] --out cpp_translate.json
 */
#include "common.hpp"
#include "translator.hpp"

#include <json.hpp>

#include <sys/resource.h>

#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <string>

namespace {

double peakRssMb() {
    rusage ru{};
    getrusage(RUSAGE_SELF, &ru);
    return static_cast<double>(ru.ru_maxrss) / 1024.0;   // kilobytes on Linux
}

}  // namespace

int main(int argc, char** argv) {
    std::string model, spm, answersPath, outPath;
    int threads = 2, perLang = 1000000;
    for (int i = 1; i + 1 < argc; i += 2) {
        const std::string a = argv[i], v = argv[i + 1];
        if (a == "--model") model = v;
        else if (a == "--spm") spm = v;
        else if (a == "--answers") answersPath = v;
        else if (a == "--out") outPath = v;
        else if (a == "--threads") threads = std::stoi(v);
        else if (a == "--per-lang") perLang = std::stoi(v);
        else { std::cerr << "unknown option " << a << "\n"; return 2; }
    }
    if (model.empty() || spm.empty() || answersPath.empty() || outPath.empty()) {
        std::cerr << "usage: translate_bench --model DIR --spm model.SRC --answers FILE --out FILE "
                     "[--threads 2] [--per-lang N]\n";
        return 2;
    }

    kr::Timer loadTimer;
    auto translator = kr::Translator::create(model, spm, threads);
    if (!translator) { std::cerr << "model files not found\n"; return 2; }
    const double loadMs = loadTimer.ms();
    const double loadRss = peakRssMb();

    std::ifstream in(answersPath);
    const auto data = nlohmann::json::parse(in);
    std::map<std::string, int> perLangCount;
    nlohmann::json rows = nlohmann::json::array();
    std::vector<double> times;
    double total = 0.0;
    int sentences = 0, withheld = 0;
    for (const auto& a : data["answers"]) {
        const std::string lang = a["language"];
        if (a["sentences"].empty() || perLangCount[lang] >= perLang) continue;
        ++perLangCount[lang];
        std::vector<std::string> english;
        for (const auto& s : a["sentences"]) english.push_back(s["english"]);
        const kr::TranslationOutput out = translator->translate(english, lang);
        times.push_back(out.ms / 1000.0);
        total += out.ms / 1000.0;
        sentences += static_cast<int>(english.size());
        withheld += out.withheld;
        nlohmann::json row = out.toJson();
        row["id"] = a["id"];
        row["seconds"] = out.ms / 1000.0;
        rows.push_back(row);
    }
    std::sort(times.begin(), times.end());
    const auto pct = [&](double p) { return times.empty() ? 0.0 : times[static_cast<size_t>(p * (times.size() - 1))]; };
    nlohmann::json summary = {{"threads", threads}, {"answers", times.size()}, {"sentences", sentences},
                              {"withheld", withheld}, {"total_seconds", total},
                              {"median_answer_seconds", pct(0.5)}, {"p95_answer_seconds", pct(0.95)},
                              {"max_answer_seconds", times.empty() ? 0.0 : times.back()},
                              {"load_ms", loadMs}, {"rss_after_load_mb", loadRss}, {"peak_rss_mb", peakRssMb()}};
    std::ofstream(outPath) << nlohmann::json{{"summary", summary}, {"answers", rows}}.dump(1);
    std::cout << summary.dump() << "\n";
    return 0;
}
