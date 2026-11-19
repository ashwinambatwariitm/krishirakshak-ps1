/*
 * indic_text_test.cpp - parity test of the C++ IndicTrans2 text processing (indic_text.cpp) against outputs saved
 * from the Python reference (results/indictrans2/indic_text_oracle.json, cpp/tools/make_indic_text_oracle.py).
 *
 * Checked, byte for byte:
 *   - Moses normaliser and tokenizer on every evaluation sentence and on hand-written edge cases;
 *   - complete pre-processing (model input text) for 9 target languages;
 *   - decoding of model pieces, post-processing (placeholders, Devanagari -> target script, detokenisation)
 *     and the repetition check, on model outputs for 9 languages;
 *   - transliteration and detokenisation of hand-written Devanagari strings.
 * The only accepted difference is the numbering of placeholders when a sentence has two or more of them
 * (Python numbers them in set order, which is not reproducible; see indic_text.hpp).
 *
 * No model is needed. Run from the repository root:  build/x86/indic_text_test .
 */
#include "indic_text.hpp"

#include <json.hpp>

#include <fstream>
#include <iostream>
#include <regex>
#include <string>

namespace {

namespace it = kr::indic_text;

// Non-ASCII bytes as \xNN, so failures print readably in any terminal.
std::string show(const std::string& s) {
    static const char* hex = "0123456789abcdef";
    std::string out;
    for (unsigned char c : s) {
        if (c >= 0x20 && c < 0x7F) out.push_back(static_cast<char>(c));
        else { out += "\\x"; out.push_back(hex[c >> 4]); out.push_back(hex[c & 15]); }
    }
    return out;
}

struct Counter {
    std::string name;
    int pass = 0, fail = 0, shown = 0;
    void check(bool ok, const std::string& what, const std::string& got, const std::string& want) {
        if (ok) { ++pass; return; }
        ++fail;
        if (shown++ < 5)
            std::cout << "  FAIL " << name << ": " << show(what) << "\n    got:  " << show(got)
                      << "\n    want: " << show(want) << "\n";
    }
    void report() const { std::cout << name << ": " << pass << " passed, " << fail << " failed\n"; }
};

int countPlaceholders(const std::string& s) {
    static const std::regex id("<ID[0-9]+>");
    return static_cast<int>(std::distance(std::sregex_iterator(s.begin(), s.end(), id), std::sregex_iterator()));
}

std::string anonymiseIds(const std::string& s) { return std::regex_replace(s, std::regex("<ID[0-9]+>"), "<ID#>"); }

}  // namespace

int main(int argc, char** argv) {
    const std::string root = argc > 1 ? argv[1] : ".";
    const std::string path = root + "/results/indictrans2/indic_text_oracle.json";
    std::ifstream in(path);
    const auto oracle = nlohmann::json::parse(in, nullptr, false);
    if (oracle.is_discarded()) {
        std::cerr << "cannot read " << path << "\n";
        return 2;
    }

    Counter norm{"moses normalize"}, tok{"moses tokenize"}, pre{"preprocess"}, dec{"decode pieces"},
        post{"postprocess"}, rep{"repetition check"}, xl{"transliterate"}, detok{"detokenize"};
    int reordered = 0;

    for (const auto& c : oracle["moses"]) {
        const std::string input = c["input"];
        norm.check(it::mosesNormalize(input) == c["normalized"].get<std::string>(), input,
                   it::mosesNormalize(input), c["normalized"]);
        tok.check(it::mosesTokenize(input) == c["tokenized"].get<std::string>(), input, it::mosesTokenize(input),
                  c["tokenized"]);
    }
    for (const auto& c : oracle["preprocess"]) {
        const std::string english = c["english"], want = c["expected"];
        const std::string got = it::preprocessEnglish(english, c["tgt"]).text;
        bool ok = got == want;
        if (!ok && countPlaceholders(want) >= 2 && anonymiseIds(got) == anonymiseIds(want)) {
            ok = true;   // same text, placeholders numbered in a different order
            ++reordered;
        }
        pre.check(ok, english + " -> " + c["tgt"].get<std::string>(), got, want);
    }
    for (const auto& c : oracle["postprocess"]) {
        const std::string english = c["english"], tgt = c["tgt"];
        const std::string decoded = it::decodePieces(c["pieces"].get<std::vector<std::string>>());
        dec.check(decoded == c["decoded"].get<std::string>(), english, decoded, c["decoded"]);
        const it::Prepared p = it::preprocessEnglish(english, tgt);
        if (countPlaceholders(p.text) >= 2) continue;   // model text uses Python's numbering
        const std::string got = it::postprocess(c["decoded"].get<std::string>(), tgt, p.placeholders);
        post.check(got == c["expected"].get<std::string>(), english + " -> " + tgt, got, c["expected"]);
        rep.check(it::hasRepetition(got) == c["repetition"].get<bool>(), got, it::hasRepetition(got) ? "true" : "false",
                  c["repetition"].get<bool>() ? "true" : "false");
    }
    for (const auto& c : oracle["devanagari"]) {
        const std::string input = c["input"], iso = c["iso"];
        const std::string t = it::transliterateFromDevanagari(input, iso);
        xl.check(t == c["transliterated"].get<std::string>(), input + " -> " + iso, t, c["transliterated"]);
        const std::string d = it::detokenizeIndic(input);
        detok.check(d == c["detokenized"].get<std::string>(), input, d, c["detokenized"]);
    }

    int fails = 0;
    for (const Counter* k : {&norm, &tok, &pre, &dec, &post, &rep, &xl, &detok}) {
        k->report();
        fails += k->fail;
    }
    std::cout << "placeholder numbering differs only (accepted): " << reordered << "\n";
    std::cout << (fails ? "FAILED" : "ALL PASSED") << "\n";
    return fails != 0;
}
