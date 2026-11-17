/*
 * output_guard.cpp - see output_guard.hpp. Same rules as the Python reference app/pipeline/guard.py.
 */
#include "output_guard.hpp"

#include <algorithm>
#include <cctype>
#include <cstring>
#include <map>
#include <regex>
#include <set>

namespace kr {

namespace {

// Active ingredients that must never appear unless they are in the retrieved extracts. Includes ingredients
// that are not in the knowledge base at all, to catch invented advice.
const std::vector<std::string> kChemicalWords = {
    "acephate", "azadirachtin", "azoxystrobin", "bifenthrin", "captan", "carbaryl", "carbendazim", "carbofuran",
    "chlorantraniliprole", "chlorothalonil", "chlorpyrifos", "copper", "cyantraniliprole", "cyazofamid", "cymoxanil",
    "cypermethrin", "dazomet", "deltamethrin", "difenoconazole", "dimethoate", "emamectin", "endosulfan",
    "famoxadone", "fenazaquin", "fenvalerate", "flubendiamide", "fluxapyroxad", "glyphosate", "hexaconazole",
    "imidacloprid", "indoxacarb", "iprodione", "kitazin", "malathion", "mancozeb", "metalaxyl", "methomyl", "metiram",
    "monocrotophos", "novaluron", "oxychloride", "oxydemeton", "paraquat", "phorate", "phosalone", "profenofos",
    "propiconazole", "propineb", "pyraclostrobin", "quinalphos", "spinosad", "spiromesifen", "streptocycline",
    "streptomycin", "sulphur", "sulfur", "tebuconazole", "tetracycline", "thiamethoxam", "thiophanate", "trichlorfon",
    "trifloxystrobin", "zineb", "ziram"};

const std::map<std::string, std::string> kDiseaseWords = {
    {"early_blight", "early blight"}, {"late_blight", "late blight"}, {"septoria_leaf_spot", "septoria"},
    {"bacterial_spot", "bacterial"}, {"yellow_leaf_curl_virus", "leaf curl"}};

// Number (optionally a range) followed by a unit. Hindi units are written as UTF-8 byte escapes:
// mili (\xE0\xA4\xAE...), gram, kilo, litre.
const std::regex kDoseRe(
    "(\\d+(?:[.,]\\d+)?(?:\\s*-\\s*\\d+(?:[.,]\\d+)?)?)\\s*"
    "(?:ml|mL|g|gm|gram|grams|kg|l|lit|litre|litres|liter|liters|ppm|%"
    "|\xE0\xA4\xAE\xE0\xA4\xBF\xE0\xA4\xB2\xE0\xA5\x80"
    "|\xE0\xA4\x97\xE0\xA5\x8D\xE0\xA4\xB0\xE0\xA4\xBE\xE0\xA4\xAE"
    "|\xE0\xA4\x95\xE0\xA4\xBF\xE0\xA4\xB2\xE0\xA5\x8B"
    "|\xE0\xA4\xB2\xE0\xA5\x80\xE0\xA4\x9F\xE0\xA4\xB0)"
    "(?![A-Za-z])");

// Devanagari digits U+0966-U+096F are encoded as E0 A5 A6 .. E0 A5 AF; replace them by ASCII digits.
std::string asciiDigits(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (size_t i = 0; i < s.size(); ++i) {
        const auto b = [&](size_t k) { return static_cast<unsigned char>(s[k]); };
        if (i + 2 < s.size() && b(i) == 0xE0 && b(i + 1) == 0xA5 && b(i + 2) >= 0xA6 && b(i + 2) <= 0xAF) {
            out += static_cast<char>('0' + (b(i + 2) - 0xA6));
            i += 2;
        } else {
            out += s[i];
        }
    }
    return out;
}

std::string lowerAscii(std::string s) {
    for (auto& ch : s) if (static_cast<unsigned char>(ch) < 128) ch = static_cast<char>(std::tolower(ch));
    return s;
}

// Lower case, ASCII digits, no whitespace: "2.5 g/litre" and "2.5g/litre" compare equal.
std::string norm(const std::string& s) {
    std::string out;
    for (char ch : lowerAscii(asciiDigits(s))) if (!std::isspace(static_cast<unsigned char>(ch))) out += ch;
    return out;
}

// Counts Devanagari and Latin letters in UTF-8 text.
void countScripts(const std::string& s, size_t& devanagari, size_t& latin) {
    devanagari = latin = 0;
    for (size_t i = 0; i < s.size();) {
        const auto c = static_cast<unsigned char>(s[i]);
        if (c < 0x80) {
            if (std::isalpha(c)) ++latin;
            ++i;
        } else if ((c & 0xF0) == 0xE0 && i + 2 < s.size()) {        // 3-byte sequence
            const unsigned cp = ((c & 0x0F) << 12) | ((static_cast<unsigned char>(s[i + 1]) & 0x3F) << 6) |
                                (static_cast<unsigned char>(s[i + 2]) & 0x3F);
            if (cp >= 0x0900 && cp <= 0x097F) ++devanagari;
            i += 3;
        } else {
            i += ((c & 0xE0) == 0xC0) ? 2 : ((c & 0xF8) == 0xF0 ? 4 : 1);
        }
    }
}

bool containsWord(const std::string& text, const std::string& word) {
    for (size_t pos = text.find(word); pos != std::string::npos; pos = text.find(word, pos + 1)) {
        const bool leftOk = pos == 0 || !std::isalnum(static_cast<unsigned char>(text[pos - 1]));
        const size_t end = pos + word.size();
        const bool rightOk = end >= text.size() || !std::isalnum(static_cast<unsigned char>(text[end]));
        if (leftOk && rightOk) return true;
    }
    return false;
}

}  // namespace

GuardResult checkOutput(const std::string& text, const std::vector<KbChunk>& facts, const std::string& lang,
                        const std::string& diagnosedTopic, size_t maxChars) {
    GuardResult r;
    std::string allowedRaw;
    for (const auto& c : facts) allowedRaw += c.textEn + " " + c.text + " " + c.product + " " + c.dose + " ";
    const std::string allowed = norm(allowedRaw);

    const auto b = text.find_first_not_of(" \n\t");
    const std::string stripped = b == std::string::npos ? "" : text.substr(b, text.find_last_not_of(" \n\t") - b + 1);
    // Length in characters (UTF-8 code points = bytes that are not continuation bytes 10xxxxxx)
    const size_t chars = std::count_if(stripped.begin(), stripped.end(),
                                       [](char ch) { return (static_cast<unsigned char>(ch) & 0xC0) != 0x80; });
    if (chars < 20) r.reasons.push_back("empty_or_too_short");
    if (chars > maxChars) r.reasons.push_back("too_long");

    const std::string low = lowerAscii(stripped);
    for (const auto& w : kChemicalWords)
        if (containsWord(low, w) && allowed.find(w) == std::string::npos)
            r.reasons.push_back("chemical_not_in_sources:" + w);

    const std::string digits = asciiDigits(stripped);
    for (std::sregex_iterator it(digits.begin(), digits.end(), kDoseRe), end; it != end; ++it)
        if (allowed.find(norm(it->str())) == std::string::npos) r.reasons.push_back("dose_not_in_sources:" + it->str());

    size_t dev = 0, lat = 0;
    countScripts(stripped, dev, lat);
    if (dev + lat > 0) {
        const double shareHi = static_cast<double>(dev) / (dev + lat);
        if (lang == "hi" && shareHi < 0.6) r.reasons.push_back("not_hindi");
        if (lang == "en" && shareHi > 0.1) r.reasons.push_back("not_english");
    }

    const auto diag = kDiseaseWords.find(diagnosedTopic);
    if (lang == "en" && diag != kDiseaseWords.end()) {
        for (const auto& [topic, word] : kDiseaseWords)
            if (topic != diagnosedTopic && low.find(word) != std::string::npos &&
                diag->second.find(word) == std::string::npos)
                r.reasons.push_back("other_disease_named:" + word);
    }
    r.ok = r.reasons.empty();
    return r;
}

namespace {

const std::set<std::string> kGroundStop = {
    "this", "that", "these", "those", "with", "from", "your", "they", "them", "their", "there", "have", "will",
    "should", "would", "could", "about", "into", "also", "very", "more", "most", "some", "such", "than", "then",
    "when", "what", "which", "while", "because", "make", "sure", "help", "farmer", "dear", "tomato", "plant",
    "plants", "disease", "first", "step", "important", "please", "keep", "good", "news", "take", "action"};
const std::set<std::string> kNegations = {"not", "never", "avoid", "dont", "don't", "no", "without", "nor"};

// Very small stemmer: enough to match "removing"/"removed"/"removes" with "remove", "leaves" with "leaf" roughly
std::string stem(std::string w) {
    for (const char* suf : {"ing", "ed", "es", "s"}) {
        const size_t n = std::strlen(suf);
        if (w.size() > n + 3 && w.compare(w.size() - n, n, suf) == 0) { w.erase(w.size() - n); break; }
    }
    return w;
}

std::vector<std::string> words(const std::string& s) {
    std::vector<std::string> out;
    std::string w;
    for (unsigned char ch : s + " ") {
        if (std::isalpha(ch) || ch == '\'') w += static_cast<char>(std::tolower(ch));
        else { if (!w.empty()) out.push_back(w); w.clear(); }
    }
    return out;
}

std::vector<std::string> splitSentences(const std::string& text) {
    std::vector<std::string> out;
    std::string cur;
    for (size_t i = 0; i < text.size(); ++i) {
        cur += text[i];
        // ';' also ends a unit: negation must be checked per clause ("Remove and destroy infected plants;
        // do not transplant infected seedlings" must not support "Do not remove the infected leaf")
        const bool end = text[i] == '.' || text[i] == '!' || text[i] == '?' || text[i] == '\n' || text[i] == ';';
        if (end && (i + 1 == text.size() || std::isspace(static_cast<unsigned char>(text[i + 1])) || text[i] == '\n')) {
            const auto b = cur.find_first_not_of(" \n");
            if (b != std::string::npos) out.push_back(cur.substr(b, cur.find_last_not_of(" \n") - b + 1));
            cur.clear();
        }
    }
    const auto b = cur.find_first_not_of(" \n");
    if (b != std::string::npos) out.push_back(cur.substr(b));
    return out;
}

bool hasNegation(const std::vector<std::string>& ws) {
    for (const auto& w : ws) if (kNegations.count(w) || (w.size() > 3 && w.compare(w.size() - 3, 3, "n't") == 0)) return true;
    return false;
}

}  // namespace

GroundingResult keepGroundedSentences(const std::string& text, const std::vector<KbChunk>& facts, double minOverlap) {
    // Each source sentence is kept separately: an answer sentence must be supported by ONE source sentence.
    // (Checking against the combined vocabulary of all extracts let a stitched answer through in testing:
    //  "You can harvest tomatoes 28 days after transplanting" = NPV spray schedule + bacterial-spot nursery text.)
    struct Source {
        std::string raw;
        std::vector<std::string> words;
        std::set<std::string> stems;
        bool negated;
    };
    std::vector<Source> sources;
    for (const auto& c : facts)
        for (const auto& s : splitSentences(c.textEn)) {
            Source src{s, words(s), {}, false};
            for (const auto& w : src.words) src.stems.insert(stem(w));
            src.negated = hasNegation(src.words);
            sources.push_back(std::move(src));
        }

    // Numbers written in a sentence (e.g. "28", "2.5"); each must appear in the supporting source sentence
    auto numbers = [](const std::string& s) {
        std::vector<std::string> out;
        std::string cur;
        for (char ch : s + " ") {
            if (std::isdigit(static_cast<unsigned char>(ch)) || (!cur.empty() && (ch == '.' || ch == ','))) cur += ch;
            else { while (!cur.empty() && !std::isdigit(static_cast<unsigned char>(cur.back()))) cur.pop_back();
                   if (!cur.empty()) out.push_back(cur); cur.clear(); }
        }
        return out;
    };

    GroundingResult r;
    std::set<std::string> seen;        // normalised sentences already kept (the 1B model sometimes repeats itself)
    for (const auto& sentence : splitSentences(text)) {
        const auto ws = words(sentence);
        std::string key;
        for (const auto& w : ws) key += w + " ";
        if (!seen.insert(key).second) { r.dropped.push_back(sentence); continue; }
        std::vector<std::string> content;
        for (const auto& w : ws) {
            const std::string s = stem(w);
            if (w.size() >= 4 && !kGroundStop.count(w) && !kGroundStop.count(s) && !kNegations.count(w))
                content.push_back(s);
        }
        if (content.empty()) { r.dropped.push_back(sentence); continue; }

        // Best single supporting source sentence
        const Source* best = nullptr;
        size_t bestHits = 0;
        for (const auto& src : sources) {
            size_t h = 0;
            for (const auto& w : content) h += src.stems.count(w) > 0;
            if (h > bestHits) bestHits = h, best = &src;
        }
        bool grounded = best && static_cast<double>(bestHits) / content.size() >= minOverlap;
        if (grounded && hasNegation(ws)) grounded = best->negated;          // never reverse an instruction
        if (grounded)
            for (const auto& n : numbers(sentence))
                if (best->raw.find(n) == std::string::npos) { grounded = false; break; }   // no invented numbers
        if (grounded) {
            r.kept += (r.kept.empty() ? "" : " ") + sentence;
            ++r.keptCount;
        } else {
            r.dropped.push_back(sentence);
        }
    }
    return r;
}

}  // namespace kr
