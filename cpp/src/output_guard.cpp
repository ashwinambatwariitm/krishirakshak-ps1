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

// "plant" is not a stop word (Llama 3.2 1B wrote "killing the entire plant" from "entire leaves are killed"). Words
// of three letters are compared ("rot", "dry", "air"), so the three-letter function words are stop words.
const std::set<std::string> kGroundStop = {
    "this", "that", "these", "those", "with", "from", "your", "they", "them", "their", "there", "have", "will",
    "should", "would", "could", "about", "into", "also", "very", "more", "most", "some", "such", "than", "then",
    "when", "what", "which", "while", "because", "make", "sure", "help", "farmer", "dear", "tomato", "disease",
    "first", "step", "important", "please", "keep", "good", "news", "take", "action", "only", "found", "seen", "appear", "become", "time",
    "the", "and", "for", "are", "was", "can", "may", "its", "has", "had", "but", "you", "all", "any", "our", "out",
    "own", "per", "via", "yet", "how", "why", "who", "use", "get", "let", "put", "see", "way", "too", "now", "due",
    "etc", "few", "off", "one", "his", "her", "she", "him", "ask"};
const std::set<std::string> kNegations = {"not", "never", "avoid", "dont", "don't", "no", "without", "nor"};
// Negations that make an instruction ("avoid ...", "do not ...", "never ..."); the others make a statement ("is not")
const std::set<std::string> kInstructionNegations = {"avoid", "never", "dont", "don't"};
constexpr size_t kMinWordLength = 3;
// A kept sentence needs two different content words: headers and one-word fragments ("**Pests**", "Wilting") are
// not advice, and one matching word was 100% of their content words.
constexpr size_t kMinContentWords = 2;
// Below five content words every word must come from the source sentence: with four words the 0.75 bar let one
// changed word through ("Spots become slightly wrinkled" from "... slightly raised").
constexpr size_t kFullMatchBelow = 5;
// A sentence that starts with one of these verbs is an instruction. It must not be supported by a description of
// the disease (symptoms, spread): "Prevent seedlings from rotting completely" came from "Complete rotting of
// seedlings", "Leave the rest of the body outside" from a description of the caterpillar.
const std::set<std::string> kActionVerbs = {
    "add", "adopt", "allow", "apply", "avoid", "burn", "check", "clean", "collect", "cover", "cut", "dip", "discard",
    "dispose", "do", "don't", "dont", "drench", "ensure", "erect", "fix", "follow", "get", "give", "grow", "improve",
    "increase", "infect", "inspect", "install", "irrigate", "keep", "leave", "maintain", "make", "minimise",
    "minimize", "mix", "monitor", "mulch", "never", "pick", "place", "plant", "practice", "practise", "prevent",
    "provide", "prune", "put", "reduce", "release", "remove", "rotate", "select", "soak", "sow", "spray", "stake",
    "stop", "take", "transplant", "treat", "try", "uproot", "use", "wash"};
// Field actions for the invented-action rule (stems): what the farmer physically does to the crop or field
const std::set<std::string> kFieldActions = {
    "plant", "grow", "sow", "transplant", "spray", "apply", "burn", "uproot", "prune", "irrigat", "irrigate", "flood",
    "drench", "dip", "soak", "mulch", "plough", "harvest", "remov", "remove", "destroy", "releas", "release",
    "install", "collect", "rotat", "rotate"};
const std::set<std::string> kDescriptionSections = {"spread", "symptoms"};
// A sentence that names a month must name all months of its source ("Disease appears in September" from
// "... September to November"). "may" is left out: it is mostly the verb.
const std::set<std::string> kMonths = {"january", "february", "march", "april", "june", "july", "august",
                                       "september", "october", "november", "december"};
// A word before one of these is part of a disease name and must be the same as in the source ("Fruit blight" was
// written for "Early blight", with 6 of 7 words matching).
const std::set<std::string> kNameHeads = {"blight", "canker", "mildew", "mosaic"};

// Very small stemmer: enough to match "removing"/"removed"/"removes" with "remove", "leaves" with "leaf" roughly
std::string stem(std::string w) {
    for (const char* suf : {"ing", "ed", "es", "s"}) {
        const size_t n = std::strlen(suf);
        if (w.size() > n + 3 && w.compare(w.size() - n, n, suf) == 0) { w.erase(w.size() - n); break; }
    }
    return w;
}

// Plain-language words that Llama uses for the same thing as the extension text (added after tests with Llama 3.2
// 3B, which rephrases faithfully: "yellow edge" for "yellow margin", "spots" for "lesions", "leftover crop debris").
// Each word maps to one shared token, applied to the source and the answer alike, so the 0.75 overlap bar is
// unchanged. Only same-meaning words are grouped; on purpose there is no entry for cause words such as "fungus"
// (late blight is a water mould) and none that could merge two different instructions.
const std::map<std::string, std::string> kSameMeaning = {
    {"leaf", "leaf"}, {"leav", "leaf"}, {"foliage", "leaf"}, {"leaflet", "leaf"},
    {"spot", "spot"}, {"lesion", "spot"}, {"patch", "spot"}, {"speck", "spot"},
    {"edge", "margin"}, {"margin", "margin"}, {"border", "margin"},
    {"ring", "ring"}, {"circle", "ring"}, {"circular", "ring"}, {"concentric", "ring"},
    {"hurt", "damag"}, {"damag", "damag"}, {"damage", "damag"}, {"injur", "damag"}, {"injury", "damag"},
    {"harm", "damag"},
    {"debri", "debris"}, {"debris", "debris"}, {"residue", "debris"}, {"leftover", "debris"},
    {"fast", "rapid"}, {"quick", "rapid"}, {"quickly", "rapid"}, {"rapid", "rapid"}, {"rapidly", "rapid"},
    {"whole", "entire"}, {"entire", "entire"}, {"complete", "entire"}, {"completely", "entire"},
    {"kill", "kill"}, {"death", "kill"}, {"die", "kill"}, {"dies", "kill"},
    {"rotate", "rotation"}, {"rotation", "rotation"},
    {"rain", "rain"}, {"rainy", "rain"}, {"rainfall", "rain"},
    {"small", "small"}, {"tiny", "small"}, {"minute", "small"},
    {"middle", "centre"}, {"centre", "centre"}, {"center", "centre"},
    {"move", "progress"}, {"progress", "progress"},
    {"infect", "infect"}, {"infection", "infect"},
    {"attach", "attach"}, {"attachment", "attach"},
    {"yellow", "yellow"}, {"yellowish", "yellow"},
    {"stunt", "stunt"}, {"dwarf", "stunt"},
    {"rot", "rot"}, {"rotten", "rot"}, {"rott", "rot"}, {"decay", "rot"},
    {"spor", "spore"}, {"spore", "spore"}, {"sporulation", "spore"},
    {"shape", "shape"}, {"shap", "shape"},
    {"remove", "remove"}, {"remov", "remove"}, {"removal", "remove"}, {"rid", "remove"},
    {"discoloration", "discolour"}, {"discolouration", "discolour"},
    {"larva", "larva"}, {"larvae", "larva"},
    {"need", "need"}, {"necessary", "need"},
};

// stem() followed by the same-meaning mapping
std::string token(const std::string& w) {
    const std::string s = stem(w);
    const auto it = kSameMeaning.find(s);
    return it == kSameMeaning.end() ? s : it->second;
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

// A sentence that states a cause must be supported by a source sentence that states one (added after Llama 3.2 3B
// wrote "This is caused by whiteflies" from "The virus is spread by whiteflies": the carrier became the cause, while
// three of four content words still matched)
const std::set<std::string> kCauseStems = {"caus", "cause", "due"};
bool hasCause(const std::vector<std::string>& ws) {
    for (const auto& w : ws) if (kCauseStems.count(stem(w))) return true;
    return false;
}

bool isNegation(const std::string& w) {
    return kNegations.count(w) || (w.size() > 3 && w.compare(w.size() - 3, 3, "n't") == 0);
}

// Kinds of negation in a sentence: 1 = instruction ("avoid", "do not", "never"), 2 = statement ("is not", "no")
int negationKinds(const std::vector<std::string>& ws) {
    int kinds = 0;
    for (size_t i = 0; i < ws.size(); ++i) {
        if (kInstructionNegations.count(ws[i]) || (ws[i] == "not" && i > 0 && ws[i - 1] == "do")) kinds |= 1;
        else if (isNegation(ws[i])) kinds |= 2;
    }
    return kinds;
}

bool isInstruction(const std::vector<std::string>& ws) { return !ws.empty() && kActionVerbs.count(ws[0]) > 0; }

std::set<std::string> monthsOf(const std::vector<std::string>& ws) {
    std::set<std::string> out;
    for (const auto& w : ws) if (kMonths.count(w)) out.insert(w);
    return out;
}

// Disease names: a content word followed by a name head word ("early blight")
std::set<std::string> namesOf(const std::vector<std::string>& ws) {
    std::set<std::string> out;
    for (size_t i = 1; i < ws.size(); ++i)
        if (kNameHeads.count(ws[i]) && ws[i - 1].size() >= kMinWordLength && !kGroundStop.count(ws[i - 1]))
            out.insert(ws[i - 1] + " " + ws[i]);
    return out;
}

// Numbers written in a sentence (e.g. "28", "2.5")
std::set<std::string> numbersOf(const std::string& s) {
    std::set<std::string> out;
    std::string cur;
    for (char ch : s + " ") {
        if (std::isdigit(static_cast<unsigned char>(ch)) || (!cur.empty() && (ch == '.' || ch == ','))) {
            cur += ch;
            continue;
        }
        while (!cur.empty() && !std::isdigit(static_cast<unsigned char>(cur.back()))) cur.pop_back();
        if (!cur.empty()) out.insert(cur);
        cur.clear();
    }
    return out;
}

template <class T> bool subset(const std::set<T>& a, const std::set<T>& b) {
    return std::includes(b.begin(), b.end(), a.begin(), a.end());
}

}  // namespace

nlohmann::json groundingConfig() {
    return {{"stop_words", kGroundStop}, {"negations", kNegations}, {"same_meaning", kSameMeaning},
            {"stem_suffixes", {"ing", "ed", "es", "s"}}, {"cause_stems", kCauseStems}, {"min_overlap", 0.75},
            {"min_word_length", kMinWordLength}, {"min_content_words", kMinContentWords},
            {"full_match_below", kFullMatchBelow}, {"instruction_negations", kInstructionNegations},
            {"action_verbs", kActionVerbs}, {"description_sections", kDescriptionSections}, {"months", kMonths},
            {"name_heads", kNameHeads}};
}

GroundingResult keepGroundedSentences(const std::string& text, const std::vector<KbChunk>& facts, double minOverlap) {
    // Each source sentence is kept separately: an answer sentence must be supported by ONE source sentence.
    // (Checking against the combined vocabulary of all extracts let a stitched answer through in testing:
    //  "You can harvest tomatoes 28 days after transplanting" = NPV spray schedule + bacterial-spot nursery text.)
    struct Source {
        std::set<std::string> stems, numbers, months, names;
        int negation;
        bool cause, describes;
    };
    std::vector<Source> sources;
    for (const auto& c : facts)
        for (const auto& s : splitSentences(c.textEn)) {
            const auto ws = words(s);
            Source src{{}, numbersOf(s), monthsOf(ws), namesOf(ws), negationKinds(ws), hasCause(ws),
                       kDescriptionSections.count(c.section) > 0};
            for (const auto& w : ws) src.stems.insert(token(w));
            sources.push_back(std::move(src));
        }

    GroundingResult r;
    std::set<std::string> seen;        // normalised sentences already kept (the 1B model sometimes repeats itself)
    for (const auto& sentence : splitSentences(text)) {
        const auto ws = words(sentence);
        std::string key;
        for (const auto& w : ws) key += w + " ";
        if (!seen.insert(key).second) { r.dropped.push_back(sentence); continue; }
        std::vector<std::string> content;          // different content words, in order of first use
        for (const auto& w : ws) {
            const std::string s = token(w);
            if (w.size() >= kMinWordLength && !kGroundStop.count(w) && !kGroundStop.count(s) && !kNegations.count(w) &&
                std::find(content.begin(), content.end(), s) == content.end())
                content.push_back(s);
        }
        if (content.size() < kMinContentWords) { r.dropped.push_back(sentence); continue; }

        // Best single supporting source sentence
        const Source* best = nullptr;
        size_t bestHits = 0;
        for (const auto& src : sources) {
            size_t h = 0;
            for (const auto& w : content) h += src.stems.count(w) > 0;
            if (h > bestHits) bestHits = h, best = &src;
        }
        const double need = content.size() < kFullMatchBelow ? static_cast<double>(content.size())
                                                             : minOverlap * static_cast<double>(content.size());
        bool grounded = best && static_cast<double>(bestHits) >= need;
        const int negation = negationKinds(ws);
        if (grounded && negation) grounded = (negation & best->negation) != 0;   // never reverse an instruction
        if (grounded && hasCause(ws)) grounded = best->cause;                    // never invent a cause
        if (grounded && isInstruction(ws)) grounded = !best->describes;          // never turn a symptom into advice
        if (grounded) {                                     // no invented number, and no number left out of a schedule
            const auto nums = numbersOf(sentence);
            grounded = subset(nums, best->numbers) && (nums.empty() || subset(best->numbers, nums));
        }
        if (grounded) {
            const auto months = monthsOf(ws);
            grounded = subset(months, best->months) && (months.empty() || subset(best->months, months));
        }
        if (grounded) grounded = subset(namesOf(ws), best->names);               // never rename the disease
        if (grounded) {
            // Never invent a field action: a field action word ("plant", "planting", "sprayed"; at the start of the
            // sentence or as an -ing / -ed form, so the nouns "plants" and "sprays" are not counted) must be in the
            // supporting source sentence; "plant" and "grow" count as the same action. Pi full test, 2026-11-21:
            // "Planting tomatoes in deep summer ploughing exposes larvae and pupae." matched 6 of 8 words of "Deep
            // summer ploughing exposes larvae and pupae." (the 0.75 bar) and was shown for every caterpillar photo.
            for (size_t i = 0; grounded && i < ws.size(); ++i) {
                const std::string& w = ws[i];
                const bool verbForm = i == 0 || (w.size() > 5 && (w.compare(w.size() - 3, 3, "ing") == 0 ||
                                                                  w.compare(w.size() - 2, 2, "ed") == 0));
                const std::string st = stem(w);
                if (!verbForm || !kFieldActions.count(st)) continue;
                grounded = best->stems.count(token(w)) > 0 || (st == "plant" && best->stems.count("grow") > 0) ||
                           (st == "grow" && best->stems.count("plant") > 0);
            }
        }
        if (grounded) {
            // Sentences written one per line often have no full stop; add one so the joined text reads as sentences
            std::string s = sentence;
            if (std::strchr(".!?;:", s.back()) == nullptr) {
                while (!s.empty() && (s.back() == ',' || s.back() == ' ')) s.pop_back();
                s += '.';
            }
            r.kept += (r.kept.empty() ? "" : " ") + s;
            ++r.keptCount;
        } else {
            r.dropped.push_back(sentence);
        }
    }
    return r;
}

std::vector<std::string> sentencesOf(const std::string& text) { return splitSentences(text); }

}  // namespace kr
