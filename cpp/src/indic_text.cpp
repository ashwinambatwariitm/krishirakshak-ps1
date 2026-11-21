/*
 * indic_text.cpp - see indic_text.hpp.
 *
 * Text is processed as UTF-32 (one char32_t per code point) so character classes and offsets work like Python
 * str. Each Python regular expression is ported as a small scanning function that reproduces re.sub behaviour:
 * matches are found left to right and do not overlap (the characters of one match cannot start the next).
 * The four placeholder patterns are more complex and use std::wregex (wchar_t is 32-bit on Linux).
 */
#include "indic_text.hpp"

#include "text_tables.hpp"

#include <algorithm>
#include <cctype>
#include <map>
#include <regex>
#include <stdexcept>

namespace kr::indic_text {

namespace {

using U32 = std::u32string;
using namespace kr::text_tables;

static_assert(sizeof(wchar_t) == 4, "std::wregex is used on UTF-32 text");

// ------------------------------------------------------------------------------------------------------------
// UTF-8 <-> UTF-32
// ------------------------------------------------------------------------------------------------------------

U32 toU32(const std::string& s) {
    U32 out;
    out.reserve(s.size());
    for (size_t i = 0; i < s.size();) {
        const unsigned char c = static_cast<unsigned char>(s[i]);
        char32_t cp = 0xFFFD;
        size_t len = 1;
        if (c < 0x80) {
            cp = c;
        } else if ((c >> 5) == 0x6 && i + 1 < s.size()) {
            cp = ((c & 0x1Fu) << 6) | (static_cast<unsigned char>(s[i + 1]) & 0x3Fu);
            len = 2;
        } else if ((c >> 4) == 0xE && i + 2 < s.size()) {
            cp = ((c & 0x0Fu) << 12) | ((static_cast<unsigned char>(s[i + 1]) & 0x3Fu) << 6) |
                 (static_cast<unsigned char>(s[i + 2]) & 0x3Fu);
            len = 3;
        } else if ((c >> 3) == 0x1E && i + 3 < s.size()) {
            cp = ((c & 0x07u) << 18) | ((static_cast<unsigned char>(s[i + 1]) & 0x3Fu) << 12) |
                 ((static_cast<unsigned char>(s[i + 2]) & 0x3Fu) << 6) | (static_cast<unsigned char>(s[i + 3]) & 0x3Fu);
            len = 4;
        }
        out.push_back(cp);
        i += len;
    }
    return out;
}

std::string toU8(const U32& s) {
    std::string out;
    out.reserve(s.size() * 3);
    for (char32_t cp : s) {
        if (cp < 0x80) {
            out.push_back(static_cast<char>(cp));
        } else if (cp < 0x800) {
            out.push_back(static_cast<char>(0xC0 | (cp >> 6)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        } else if (cp < 0x10000) {
            out.push_back(static_cast<char>(0xE0 | (cp >> 12)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        } else {
            out.push_back(static_cast<char>(0xF0 | (cp >> 18)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 12) & 0x3F)));
            out.push_back(static_cast<char>(0x80 | ((cp >> 6) & 0x3F)));
            out.push_back(static_cast<char>(0x80 | (cp & 0x3F)));
        }
    }
    return out;
}

U32 u(const char* ascii) { return toU32(ascii); }

// ------------------------------------------------------------------------------------------------------------
// Character classes (generated tables, see cpp/tools/gen_text_tables.py)
// ------------------------------------------------------------------------------------------------------------

template <size_t N>
bool inTable(const CodeRange (&table)[N], char32_t c) {
    const CodeRange* end = table + N;
    const CodeRange* it = std::upper_bound(table, end, c, [](char32_t v, const CodeRange& r) { return v < r.first; });
    return it != table && c <= (it - 1)->last;
}

bool isSpace(char32_t c) { return inTable(kPySpace, c); }     // Python \s, str.strip(), str.split()
bool isDigit(char32_t c) { return inTable(kPyDigit, c); }     // Python \d
bool isWord(char32_t c) { return inTable(kPyWord, c); }       // Python \w
bool isN(char32_t c) { return inTable(kIsN, c); }             // Moses IsN
bool isAlnum(char32_t c) { return inTable(kIsAlnum, c); }     // Moses IsAlnum (+ viramas, nuktas)
bool isAlpha(char32_t c) { return inTable(kIsAlpha, c); }     // Moses IsAlpha (+ viramas, nuktas)
bool isLower(char32_t c) { return inTable(kIsLower, c); }     // Moses IsLower
bool isAsciiLetter(char32_t c) { return (c >= U'a' && c <= U'z') || (c >= U'A' && c <= U'Z'); }

// ------------------------------------------------------------------------------------------------------------
// String helpers with Python semantics
// ------------------------------------------------------------------------------------------------------------

// str.replace(from, to): all non-overlapping occurrences, left to right.
U32 replaceAll(const U32& s, const U32& from, const U32& to) {
    if (from.empty()) return s;
    U32 out;
    size_t pos = 0;
    for (size_t hit; (hit = s.find(from, pos)) != U32::npos; pos = hit + from.size()) {
        out.append(s, pos, hit - pos);
        out += to;
    }
    out.append(s, pos, U32::npos);
    return out;
}

// str.strip() (Unicode whitespace).
U32 strip(const U32& s) {
    size_t b = 0, e = s.size();
    while (b < e && isSpace(s[b])) ++b;
    while (e > b && isSpace(s[e - 1])) --e;
    return s.substr(b, e - b);
}

// str.split() (runs of Unicode whitespace, no empty items).
std::vector<U32> splitWs(const U32& s) {
    std::vector<U32> out;
    size_t i = 0;
    while (i < s.size()) {
        while (i < s.size() && isSpace(s[i])) ++i;
        size_t j = i;
        while (j < s.size() && !isSpace(s[j])) ++j;
        if (j > i) out.push_back(s.substr(i, j - i));
        i = j;
    }
    return out;
}

U32 join(const std::vector<U32>& parts, const U32& sep) {
    U32 out;
    for (size_t i = 0; i < parts.size(); ++i) {
        if (i) out += sep;
        out += parts[i];
    }
    return out;
}

// re.sub(pred+, repl): every maximal run of characters matching pred becomes repl.
template <class Pred>
U32 collapseRuns(const U32& s, Pred pred, const U32& repl) {
    U32 out;
    for (size_t i = 0; i < s.size();) {
        if (pred(s[i])) {
            while (i < s.size() && pred(s[i])) ++i;
            out += repl;
        } else {
            out.push_back(s[i++]);
        }
    }
    return out;
}

// re.sub over a 3-character window "(A)(x)(B)" where A and B are classes and x is a fixed character;
// emit(a, b) builds the replacement. Matches consume all three characters.
template <class PredA, class PredB, class Emit>
U32 sub3(const U32& s, PredA a, char32_t mid, PredB b, Emit emit) {
    U32 out;
    size_t i = 0;
    while (i < s.size()) {
        if (i + 2 < s.size() && a(s[i]) && s[i + 1] == mid && b(s[i + 2])) {
            out += emit(s[i], s[i + 2]);
            i += 3;
        } else {
            out.push_back(s[i++]);
        }
    }
    return out;
}

// re.sub(r"(\d)<sep>(\d)", r"\1<joiner>\2")-style rule with a literal middle string.
U32 subDigitSepDigit(const U32& s, const U32& sep, const U32& joiner) {
    U32 out;
    size_t i = 0;
    while (i < s.size()) {
        const size_t j = i + 1 + sep.size();
        if (j < s.size() && isDigit(s[i]) && s.compare(i + 1, sep.size(), sep) == 0 && isDigit(s[j])) {
            out.push_back(s[i]);
            out += joiner;
            out.push_back(s[j]);
            i = j + 1;
        } else {
            out.push_back(s[i++]);
        }
    }
    return out;
}

// re.sub(r"(\d)<sep>%", r"\1%").
U32 subDigitSepPercent(const U32& s, const U32& sep) {
    U32 out;
    size_t i = 0;
    while (i < s.size()) {
        const size_t j = i + 1 + sep.size();
        if (j < s.size() && isDigit(s[i]) && s.compare(i + 1, sep.size(), sep) == 0 && s[j] == U'%') {
            out.push_back(s[i]);
            out.push_back(U'%');
            i = j + 1;
        } else {
            out.push_back(s[i++]);
        }
    }
    return out;
}

// re.sub(r"\) ([.!:?;,])", r")\1")
U32 subParenSpacePunct(const U32& s) {
    static const U32 punct = u(".!:?;,");
    U32 out;
    size_t i = 0;
    while (i < s.size()) {
        if (i + 2 < s.size() && s[i] == U')' && s[i + 1] == U' ' && punct.find(s[i + 2]) != U32::npos) {
            out.push_back(U')');
            out.push_back(s[i + 2]);
            i += 3;
        } else {
            out.push_back(s[i++]);
        }
    }
    return out;
}

// re.sub(r'"([,.]+)', r'\1"')
U32 subQuoteThenCommaDots(const U32& s) {
    U32 out;
    size_t i = 0;
    while (i < s.size()) {
        if (s[i] == U'"' && i + 1 < s.size() && (s[i + 1] == U',' || s[i + 1] == U'.')) {
            size_t j = i + 1;
            while (j < s.size() && (s[j] == U',' || s[j] == U'.')) ++j;
            out.append(s, i + 1, j - i - 1);
            out.push_back(U'"');
            i = j;
        } else {
            out.push_back(s[i++]);
        }
    }
    return out;
}

// Replaces each character found in `chars` by `to`.
U32 mapChars(const U32& s, const U32& chars, const U32& to) {
    U32 out;
    for (char32_t c : s) {
        if (chars.find(c) != U32::npos) out += to;
        else out.push_back(c);
    }
    return out;
}

// ------------------------------------------------------------------------------------------------------------
// IndicProcessor._punc_norm
// ------------------------------------------------------------------------------------------------------------

const char32_t NBSP = 0xA0;

U32 puncNorm(U32 s) {
    s = replaceAll(s, U"\r", U"");                                           // \r -> ""
    {   // \(\s* -> "("
        U32 out;
        for (size_t i = 0; i < s.size(); ++i) {
            out.push_back(s[i]);
            if (s[i] == U'(') while (i + 1 < s.size() && isSpace(s[i + 1])) ++i;
        }
        s = out;
    }
    {   // \s*\) -> ")": a whitespace run directly before ')' is removed
        U32 out;
        for (size_t i = 0; i < s.size();) {
            if (isSpace(s[i])) {
                size_t j = i;
                while (j < s.size() && isSpace(s[j])) ++j;
                if (j < s.size() && s[j] == U')') i = j;
                else { out.append(s, i, j - i); i = j; }
            } else {
                out.push_back(s[i++]);
            }
        }
        s = out;
    }
    for (char32_t p : {U':', U';'}) {   // \s:\s? -> ":"   and   \s;\s? -> ";"
        U32 out;
        for (size_t i = 0; i < s.size();) {
            if (i + 1 < s.size() && isSpace(s[i]) && s[i + 1] == p) {
                out.push_back(p);
                i += 2;
                if (i < s.size() && isSpace(s[i])) ++i;
            } else {
                out.push_back(s[i++]);
            }
        }
        s = out;
    }
    s = mapChars(s, U32{U'`', 0xB4, 0x2018, 0x201A, 0x2019}, U"'");
    s = mapChars(s, U32{0x201E, 0x201C, 0x201D, 0xAB, 0xBB}, U"\"");
    s = mapChars(s, U32{0x2013, 0x2014}, U"-");
    s = replaceAll(s, U32{NBSP, U'%'}, U"%");
    s = replaceAll(s, U32{U'n', 0xBA, NBSP}, U32{U'n', 0xBA, U' '});
    s = replaceAll(s, U32{NBSP, 0xBA, U'C'}, U32{U' ', 0xBA, U'C'});
    for (char32_t p : {U'?', U'!', U';'}) s = replaceAll(s, U32{NBSP, p}, U32{p});   // \xa0[?!;] -> strip()
    s = replaceAll(s, U32{U',', NBSP}, U", ");
    // second group of patterns
    s = collapseRuns(s, [](char32_t c) { return c == U' '; }, U" ");        // [ ]{2,} -> " "
    s = subParenSpacePunct(s);
    s = subDigitSepPercent(s, U" ");
    s = subQuoteThenCommaDots(s);
    s = subDigitSepDigit(s, U32{NBSP}, U".");
    return strip(s);
}

// IndicProcessor digit table: digits of Indic scripts (and a few others) -> ASCII digits.
char32_t asciiDigit(char32_t c) {
    static const std::map<char32_t, char32_t> table = [] {
        std::map<char32_t, char32_t> m;
        // zero digit of each script; the table maps zero..nine of every script below
        const char32_t zeros[] = {0x09E6, 0x0AE6, 0x0CE6, 0x0966, 0x0660, 0xABF0, 0x0B66, 0x0A66, 0x1C50, 0x06F0};
        for (char32_t z : zeros)
            for (char32_t d = 0; d < 10; ++d) m[z + d] = U'0' + d;
        m.erase(0x0661); m.erase(0x0662); m.erase(0x0663); m.erase(0x0664);   // Arabic-Indic: only zero is mapped
        m.erase(0x0665); m.erase(0x0666); m.erase(0x0667); m.erase(0x0668); m.erase(0x0669);
        for (char32_t d = 1; d < 10; ++d) m[0x0C66 + d] = U'0' + d;             // Telugu: one..nine (no zero)
        return m;
    }();
    const auto it = table.find(c);
    return it == table.end() ? c : it->second;
}

// ------------------------------------------------------------------------------------------------------------
// IndicProcessor._wrap_with_placeholders
// ------------------------------------------------------------------------------------------------------------

// Bracket expression listing the code points of a generated table, for std::wregex.
template <size_t N>
std::wstring bracket(const CodeRange (&table)[N], const std::wstring& extra = L"") {
    auto lit = [](char32_t c) {
        std::wstring s;
        if (c == U'\\' || c == U']' || c == U'[' || c == U'^' || c == U'-') s.push_back(L'\\');
        s.push_back(static_cast<wchar_t>(c));
        return s;
    };
    std::wstring b = L"[";
    for (const CodeRange& r : table) {
        b += lit(r.first);
        if (r.last != r.first) b += L"-" + lit(r.last);
    }
    return b + extra + L"]";
}

std::wstring toW(const U32& s) { return std::wstring(s.begin(), s.end()); }
U32 fromW(const std::wstring& s) { return U32(s.begin(), s.end()); }

// All non-overlapping matches of a regex, in order (re.findall for patterns without groups).
std::vector<U32> findAll(const U32& text, const std::wregex& re) {
    std::vector<U32> out;
    const std::wstring w = toW(text);
    for (std::wsregex_iterator it(w.begin(), w.end(), re), end; it != end; ++it) out.push_back(fromW(it->str()));
    return out;
}

// _URL_PATTERN: \b(?<![\w/.])(?:(?:https?|ftp)://)?(?:(?:[\w-]+\.)+(?!\.))(?:[\w/\-?#&=%.]+)+(?!\.\w+)\b
// std::regex has no look-behind and an ASCII-only \b, so the start and end conditions are checked here and
// only the middle part is a regex. For a start position Python's backtracking returns the longest end that
// satisfies the conditions, so ends are tried from the longest down.
std::vector<U32> findUrls(const U32& s) {
    static const std::wstring W = bracket(kPyWord);
    static const std::wstring WD = bracket(kPyWord, L"\\-");
    static const std::wstring X = bracket(kPyWord, L"/\\-?#&=%.");
    static const std::wregex core(L"(?:(?:https?|ftp)://)?(?:" + WD + L"+\\.)+(?!\\.)" + X + L"+");
    (void)W;
    auto inX = [](char32_t c) { return isWord(c) || c == U'/' || c == U'-' || c == U'?' || c == U'#' || c == U'&' ||
                                       c == U'=' || c == U'%' || c == U'.'; };
    auto boundary = [&](size_t e) {
        const bool before = e > 0 && isWord(s[e - 1]);
        const bool after = e < s.size() && isWord(s[e]);
        return before != after;
    };
    std::vector<U32> out;
    size_t pos = 0;
    while (pos < s.size()) {
        bool found = false;
        for (size_t p = pos; p < s.size() && !found; ++p) {
            if (!isWord(s[p])) continue;
            if (p > 0 && (isWord(s[p - 1]) || s[p - 1] == U'/' || s[p - 1] == U'.')) continue;
            // quick filter: after an optional scheme, a [\w-]+ run must be followed by '.'
            size_t q = p;
            for (const char* scheme : {"https://", "http://", "ftp://"}) {
                const U32 sch = u(scheme);
                if (s.compare(p, sch.size(), sch) == 0) { q = p + sch.size(); break; }
            }
            size_t r = q;
            while (r < s.size() && (isWord(s[r]) || s[r] == U'-')) ++r;
            if (r == q || r >= s.size() || s[r] != U'.') continue;
            size_t maxEnd = q;
            while (maxEnd < s.size() && inX(s[maxEnd])) ++maxEnd;
            for (size_t e = maxEnd; e > p && !found; --e) {
                if (e < s.size() && s[e] == U'.' && e + 1 < s.size() && isWord(s[e + 1])) continue;  // (?!\.\w+)
                if (!boundary(e)) continue;
                const std::wstring cand = toW(s.substr(p, e - p));
                if (std::regex_match(cand, core)) {
                    out.push_back(s.substr(p, e - p));
                    pos = e;
                    found = true;
                }
            }
        }
        if (!found) break;
    }
    return out;
}

// Placeholder spellings the model may produce for <IDn>, and Indic spellings of "ID" seen in its outputs
// (IndicTransToolkit _INDIC_FAILURE_CASES, including its missing comma that joins two entries).
const std::vector<std::string>& indicFailureCases() {
    static const std::vector<std::string> cases = [] {
        const std::vector<U32> u32 = {
            U"\u0622\u06cc \u0688\u06cc ",
            U"\uabd1\uabe5\uabcf\uabd7\uabe4",
            U"\u0906\u0908\u0921\u0940",
            U"\u0906\u0908 . \u0921\u0940 . ",
            U"\u0906\u0908 . \u0921\u0940 .",
            U"\u0906\u0908. \u0921\u0940. ",
            U"\u0906\u0908. \u0921\u0940.",
            U"\u0906\u092f. \u0921\u0940. ",
            U"\u0906\u092f. \u0921\u0940.",
            U"\u0906\u092f . \u0921\u0940 . ",
            U"\u0906\u092f . \u0921\u0940 .\u0906\u0907 . \u0921\u0940 . ",   // two entries joined in Python
            U"\u0906\u0907 . \u0921\u0940 .",
            U"\u0906\u0907. \u0921\u0940. ",
            U"\u0906\u0907. \u0921\u0940.",
            U"\u0910\u091f\u093f",
            U"\u0622\u0626\u06cc \u0688\u06cc ",
            U"\u1c5f\u1c6d\u1c70\u1c64 \u1c7e",
            U"\u0906\u092f\u0921\u0940",
            U"\u0910\u0921\u093f",
            U"\u0906\u0907\u0921\u093f",
            U"\u1c5f\u1c6d\u1c70\u1c64",
        };
        std::vector<std::string> v;
        for (const U32& c : u32) v.push_back(toU8(c));
        return v;
    }();
    return cases;
}

void addPlaceholderKeys(PlaceholderMap& map, int n, const std::string& match) {
    const std::string id = std::to_string(n);
    for (const char* stem : {"ID", "id"}) {
        const std::string t = stem;
        for (const std::string& key : {"<" + t + id + ">", "< " + t + id + " >", "[" + t + id + "]", "[ " + t + id + " ]",
                                       "[" + t + " " + id + "]", "<" + t + id + "]", "< " + t + id + "]",
                                       "<" + t + id + " ]"})
            map.emplace_back(key, match);
    }
    for (const std::string& c : indicFailureCases()) {
        for (const std::string& key : {"<" + c + id + ">", "< " + c + id + " >", "< " + c + " " + id + " >",
                                       "<" + c + " " + id + "]", "< " + c + " " + id + " ]", "[" + c + id + "]",
                                       "[" + c + " " + id + "]", "[ " + c + id + " ]", "[ " + c + " " + id + " ]",
                                       c + " " + id, c + id})
            map.emplace_back(key, match);
    }
}

U32 wrapWithPlaceholders(U32 text, PlaceholderMap& map) {
    static const std::wstring D = bracket(kPyDigit);
    static const std::wstring S = bracket(kPySpace);
    static const std::wregex email(L"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}");
    static const std::wregex numeral(
        L"~?" + D + L"+\\.?" + D + L"*" + S + L"?%?" + S + L"?-?" + S + L"?~?" + D + L"+\\.?" + D + L"*" + S + L"?%" +
        L"|~?" + D + L"+%" +
        L"|" + D + L"+[-/.,:']" + D + L"+[-/.,:'+]" + D + L"+(?:\\." + D + L"+)?" +
        L"|" + D + L"+[-/.:'+]" + D + L"+(?:\\." + D + L"+)?");
    static const std::wregex other(L"[A-Za-z0-9]*[#|@]" + bracket(kPyWord) + L"+");

    int serial = 1;
    for (int which = 0; which < 4; ++which) {
        std::vector<U32> matches = which == 0 ? findAll(text, email)
                                 : which == 1 ? findUrls(text)
                                 : which == 2 ? findAll(text, numeral)
                                              : findAll(text, other);
        // set(): unique matches; first-appearance order (Python's set order is not reproducible)
        std::vector<U32> unique;
        for (const U32& m : matches)
            if (std::find(unique.begin(), unique.end(), m) == unique.end()) unique.push_back(m);
        for (const U32& m : unique) {
            if (which == 1 && replaceAll(m, U".", U"").size() < 4) continue;
            if (which == 2 && replaceAll(replaceAll(replaceAll(m, U" ", U""), U".", U""), U":", U"").size() < 4) continue;
            addPlaceholderKeys(map, serial, toU8(m));
            text = replaceAll(text, m, u(("<ID" + std::to_string(serial) + ">").c_str()));
            ++serial;
        }
    }
    text = collapseRuns(text, isSpace, U" ");
    text = replaceAll(text, U">/", U">");
    return replaceAll(text, U"]/", U"]");
}

// ------------------------------------------------------------------------------------------------------------
// sacremoses MosesPunctNormalizer(lang="en") -- default options: penn=True, norm_quote_commas=True,
// norm_numbers=True
// ------------------------------------------------------------------------------------------------------------

U32 mosesNormalizeU(U32 s) {
    auto spaces = [](const U32& t) { return collapseRuns(t, [](char32_t c) { return c == U' '; }, U" "); };
    // EXTRA_WHITESPACE
    s = replaceAll(s, U"\r", U"");
    s = replaceAll(s, U"(", U" (");
    s = replaceAll(s, U")", U") ");
    s = spaces(s);
    s = subParenSpacePunct(s);
    s = replaceAll(s, U"( ", U"(");
    s = replaceAll(s, U" )", U")");
    s = subDigitSepPercent(s, U" ");
    s = replaceAll(s, U" :", U":");
    s = replaceAll(s, U" ;", U";");
    // NORMALIZE_UNICODE_IF_NOT_PENN
    s = replaceAll(s, U"`", U"'");
    s = replaceAll(s, U"''", U" \" ");
    // NORMALIZE_UNICODE
    s = replaceAll(s, U32{0x201E}, U"\"");
    s = replaceAll(s, U32{0x201C}, U"\"");
    s = replaceAll(s, U32{0x201D}, U"\"");
    s = replaceAll(s, U32{0x2013}, U"-");
    s = replaceAll(s, U32{0x2014}, U" - ");
    s = spaces(s);
    s = replaceAll(s, U32{0xB4}, U"'");
    for (char32_t q : {char32_t(0x2018), char32_t(0x2019)})
        s = sub3(s, isAsciiLetter, q, isAsciiLetter, [](char32_t a, char32_t b) { return U32{a, U'\'', b}; });
    s = replaceAll(s, U32{0x2018}, U"'");
    s = replaceAll(s, U32{0x201A}, U"'");
    s = replaceAll(s, U32{0x2019}, U"'");
    s = replaceAll(s, U"''", U"\"");
    s = replaceAll(s, U32{0xB4, 0xB4}, U"\"");
    s = replaceAll(s, U32{0x2026}, U"...");
    // FRENCH_QUOTES
    s = replaceAll(s, U32{NBSP, 0xAB, NBSP}, U"\"");
    s = replaceAll(s, U32{0xAB, NBSP}, U"\"");
    s = replaceAll(s, U32{0xAB}, U"\"");
    s = replaceAll(s, U32{NBSP, 0xBB, NBSP}, U"\"");
    s = replaceAll(s, U32{NBSP, 0xBB}, U"\"");
    s = replaceAll(s, U32{0xBB}, U"\"");
    // HANDLE_PSEUDO_SPACES
    s = replaceAll(s, U32{NBSP, U'%'}, U"%");
    s = replaceAll(s, U32{U'n', 0xBA, NBSP}, U32{U'n', 0xBA, U' '});
    s = replaceAll(s, U32{NBSP, U':'}, U":");
    s = replaceAll(s, U32{NBSP, 0xBA, U'C'}, U32{U' ', 0xBA, U'C'});
    s = replaceAll(s, U32{NBSP, U'c', U'm'}, U" cm");
    s = replaceAll(s, U32{NBSP, U'?'}, U"?");
    s = replaceAll(s, U32{NBSP, U'!'}, U"!");
    s = replaceAll(s, U32{NBSP, U';'}, U";");
    s = replaceAll(s, U32{U',', NBSP}, U", ");
    s = spaces(s);
    // EN_QUOTATION_FOLLOWED_BY_COMMA, OTHER (numbers)
    s = subQuoteThenCommaDots(s);
    s = subDigitSepDigit(s, U32{NBSP}, U".");
    return strip(s);
}

// ------------------------------------------------------------------------------------------------------------
// sacremoses MosesTokenizer(lang="en").tokenize(text, escape=False) -- aggressive_dash_splits=False
// ------------------------------------------------------------------------------------------------------------

struct Prefixes {
    std::vector<U32> nonbreaking;   // full entries, e.g. "Mr", "No #NUMERIC_ONLY#"
    std::vector<U32> numericOnly;   // "No", "Art", "pp": stay attached only before a number
};

const Prefixes& enPrefixes() {
    static const Prefixes p = [] {
        Prefixes r;
        const U32 marker = U" #NUMERIC_ONLY#";
        for (const char* w : kEnNonbreakingPrefixes) {
            const U32 x = u(w);
            r.nonbreaking.push_back(x);
            // NUMERIC_ONLY_PREFIXES: w.rpartition(" ")[0] for entries containing the marker
            if (x.find(marker) != U32::npos) r.numericOnly.push_back(x.substr(0, x.rfind(U' ')));
        }
        return r;
    }();
    return p;
}

bool contains(const std::vector<U32>& v, const U32& x) { return std::find(v.begin(), v.end(), x) != v.end(); }

U32 handleNonbreakingPrefixes(const U32& text) {
    const Prefixes& P = enPrefixes();
    std::vector<U32> tokens = splitWs(text);
    const size_t n = tokens.size();
    for (size_t i = 0; i < n; ++i) {
        const U32& token = tokens[i];
        if (token.size() < 2 || token.back() != U'.') continue;   // ^(\S+)\.$
        const U32 prefix = token.substr(0, token.size() - 1);
        const bool anyAlpha = std::any_of(prefix.begin(), prefix.end(), isAlpha);
        if ((prefix.find(U'.') != U32::npos && anyAlpha) ||
            (contains(P.nonbreaking, prefix) && !contains(P.numericOnly, prefix)) ||
            (i != n - 1 && !tokens[i + 1].empty() && isLower(tokens[i + 1][0]))) {
            // unchanged
        } else if (contains(P.numericOnly, prefix) && i + 1 < n && !tokens[i + 1].empty() &&
                   tokens[i + 1][0] >= U'0' && tokens[i + 1][0] <= U'9') {
            // unchanged
        } else {
            tokens[i] = prefix + U" .";
        }
    }
    return join(tokens, U" ");
}

U32 mosesTokenizeU(U32 s) {
    s = collapseRuns(s, isSpace, U" ");                                        // DEDUPLICATE_SPACE
    s.erase(std::remove_if(s.begin(), s.end(), [](char32_t c) { return c < 0x20; }), s.end());   // ASCII_JUNK
    s = strip(s);
    {   // PAD_NOT_ISALNUM: ([^IsAlnum\s.'`,-]) -> " \1 "
        U32 out;
        for (char32_t c : s) {
            if (!isAlnum(c) && !isSpace(c) && c != U'.' && c != U'\'' && c != U'`' && c != U',' && c != U'-') {
                out.push_back(U' ');
                out.push_back(c);
                out.push_back(U' ');
            } else {
                out.push_back(c);
            }
        }
        s = out;
    }
    {   // replace_multidots: runs of 2+ dots -> " DOT...DOTMULTI" (+ " " unless at the end)
        U32 out;
        for (size_t i = 0; i < s.size();) {
            if (s[i] == U'.' && i + 1 < s.size() && s[i + 1] == U'.') {
                size_t j = i;
                while (j < s.size() && s[j] == U'.') ++j;
                out += U" ";
                for (size_t k = i; k < j; ++k) out += U"DOT";
                out += U"MULTI";
                if (j < s.size()) out += U" ";
                i = j;
            } else {
                out.push_back(s[i++]);
            }
        }
        s = out;
    }
    auto notN = [](char32_t c) { return !isN(c); };
    {   // COMMA_SEPARATE_1: ([^IsN])[,] -> "\1 , "
        U32 out;
        size_t i = 0;
        while (i < s.size()) {
            if (i + 1 < s.size() && notN(s[i]) && s[i + 1] == U',') {
                out.push_back(s[i]);
                out += U" , ";
                i += 2;
            } else {
                out.push_back(s[i++]);
            }
        }
        s = out;
    }
    {   // COMMA_SEPARATE_2: [,]([^IsN]) -> " , \1"
        U32 out;
        size_t i = 0;
        while (i < s.size()) {
            if (i + 1 < s.size() && s[i] == U',' && notN(s[i + 1])) {
                out += U" , ";
                out.push_back(s[i + 1]);
                i += 2;
            } else {
                out.push_back(s[i++]);
            }
        }
        s = out;
    }
    // COMMA_SEPARATE_3: ([IsN])[,]$ -> "\1 , "
    if (s.size() >= 2 && s.back() == U',' && isN(s[s.size() - 2])) s = s.substr(0, s.size() - 1) + U" , ";
    // ENGLISH_SPECIFIC_APOSTROPHE
    auto notAlpha = [](char32_t c) { return !isAlpha(c); };
    auto notAlphaN = [](char32_t c) { return !isAlpha(c) && !isN(c); };
    auto spaced = [](char32_t a, char32_t b) { return U32{a, U' ', U'\'', U' ', b}; };
    s = sub3(s, notAlpha, U'\'', notAlpha, spaced);
    s = sub3(s, notAlphaN, U'\'', isAlpha, spaced);
    s = sub3(s, isAlpha, U'\'', notAlpha, spaced);
    s = sub3(s, isAlpha, U'\'', isAlpha, [](char32_t a, char32_t b) { return U32{a, U' ', U'\'', b}; });
    s = sub3(s, isN, U'\'', [](char32_t c) { return c == U's'; },
             [](char32_t a, char32_t b) { return U32{a, U' ', U'\'', b}; });
    s = handleNonbreakingPrefixes(s);
    s = strip(collapseRuns(s, isSpace, U" "));
    // TRAILING_DOT_APOSTROPHE: \.' ?$ -> " . ' "
    if (s.size() >= 2 && s.compare(s.size() - 2, 2, U".'") == 0) s = s.substr(0, s.size() - 2) + U" . ' ";
    else if (s.size() >= 3 && s.compare(s.size() - 3, 3, U".' ") == 0) s = s.substr(0, s.size() - 3) + U" . ' ";
    {   // restore_multidots: (?:DOT)+MULTI -> one dot per DOT
        U32 out;
        for (size_t i = 0; i < s.size();) {
            size_t j = i, dots = 0;
            while (s.compare(j, 3, U"DOT") == 0) { j += 3; ++dots; }
            if (dots > 0 && s.compare(j, 5, U"MULTI") == 0) {
                out.append(dots, U'.');
                i = j + 5;
            } else {
                out.push_back(s[i++]);
            }
        }
        s = out;
    }
    return join(splitWs(s), U" ");   // return_str=False -> text.split(); joined by the caller with " "
}

// ------------------------------------------------------------------------------------------------------------
// indicnlp: UnicodeIndicTransliterator.transliterate(text, "hi", lang) and trivial_detokenize
// ------------------------------------------------------------------------------------------------------------

char32_t scriptBase(const std::string& iso) {
    static const std::map<std::string, char32_t> base = {
        {"pa", 0x0A00}, {"gu", 0x0A80}, {"or", 0x0B00}, {"ta", 0x0B80}, {"te", 0x0C00}, {"kn", 0x0C80},
        {"ml", 0x0D00}, {"si", 0x0D80}, {"hi", 0x0900}, {"mr", 0x0900}, {"kK", 0x0900}, {"sa", 0x0900},
        {"ne", 0x0900}, {"sd", 0x0900}, {"bn", 0x0980}, {"as", 0x0980}};
    const auto it = base.find(iso);
    return it == base.end() ? 0 : it->second;
}

// Tamil has no letters for voiced/aspirated plosives: they map to the unvoiced, unaspirated letter of the row.
int correctTamilOffset(int offset) {
    if (offset >= 0x15 && offset <= 0x28 && offset != 0x1C && !((offset - 0x15) % 5 == 0 || (offset - 0x15) % 5 == 4))
        offset = 0x15 + 5 * ((offset - 0x15) / 5);
    if (offset == 0x2B || offset == 0x2C || offset == 0x2D) offset = 0x2A;
    if (offset == 0x36) offset = 0x37;
    return offset;
}

U32 transliterateU(const U32& text, const std::string& iso) {
    const char32_t to = scriptBase(iso);
    if (to == 0) return text;
    U32 out;
    out.reserve(text.size());
    for (char32_t c : text) {
        const long offset = static_cast<long>(c) - 0x0900;
        if (offset >= 0 && offset <= 0x6F && c != 0x0964 && c != 0x0965) {   // danda and double danda stay
            const int o = iso == "ta" ? correctTamilOffset(static_cast<int>(offset)) : static_cast<int>(offset);
            out.push_back(to + static_cast<char32_t>(o));
        } else {
            out.push_back(c);
        }
    }
    return out;
}

U32 detokenizeIndicU(U32 s) {
    {   // number sequences "12 , 5" -> "12,5" (pattern ([0-9]+ [,.:/] )+[0-9]+), with the Python loop's rule
        // that a match starting exactly where the previous one ended (or at 0) is left unchanged
        static const std::wregex numSeq(L"([0-9]+ [,.:/] )+[0-9]+");
        const std::wstring w = toW(s);
        U32 out;
        size_t prev = 0;
        for (std::wsregex_iterator it(w.begin(), w.end(), numSeq), end; it != end; ++it) {
            const size_t start = static_cast<size_t>(it->position()), stop = start + static_cast<size_t>(it->length());
            if (start > prev) {
                out.append(s, prev, start - prev);
                out += replaceAll(s.substr(start, stop - start), U" ", U"");
                prev = stop;
            }
        }
        out.append(s, prev, U32::npos);
        s = out;
    }
    auto attach = [&s](const U32& set, bool spaceBefore, bool spaceAfter) {
        U32 out;
        size_t i = 0;
        while (i < s.size()) {
            const size_t c = spaceBefore ? i + 1 : i;
            const size_t len = (spaceBefore ? 1 : 0) + 1 + (spaceAfter ? 1 : 0);
            if (i + len <= s.size() && (!spaceBefore || s[i] == U' ') && set.find(s[c]) != U32::npos &&
                (!spaceAfter || s[c + 1] == U' ')) {
                out.push_back(s[c]);
                i += len;
            } else {
                out.push_back(s[i++]);
            }
        }
        s = out;
    };
    attach(u("-/\\"), true, true);                                                   // pat_lra
    attach(u("!%)]},.:;>?") + U32{0x0964, 0x0965}, true, false);                     // pat_la
    attach(u("#$([{<@"), false, true);                                               // pat_ra
    for (char32_t q : {U'\'', U'"', U'`'}) {   // quotes alternate: opening attaches right, closing left
        U32 marked;
        int count = 0;
        for (char32_t c : s) {
            if (c == q) marked += (count++ % 2 == 0) ? U"@RA" : U"@LA";
            else marked.push_back(c);
        }
        const U32 qs(1, q);
        marked = replaceAll(marked, U"@RA ", qs);
        marked = replaceAll(marked, U" @LA", qs);
        marked = replaceAll(marked, U"@RA", qs);
        s = replaceAll(marked, U"@LA", qs);
    }
    return s;
}

const std::map<std::string, std::string>& floresToIso() {
    static const std::map<std::string, std::string> m = {
        {"asm_Beng", "as"}, {"ben_Beng", "bn"}, {"guj_Gujr", "gu"}, {"hin_Deva", "hi"}, {"kan_Knda", "kn"},
        {"mal_Mlym", "ml"}, {"mar_Deva", "mr"}, {"npi_Deva", "ne"}, {"ory_Orya", "or"}, {"pan_Guru", "pa"},
        {"san_Deva", "hi"}, {"tam_Taml", "ta"}, {"tel_Telu", "te"}, {"eng_Latn", "en"}};
    return m;
}

}  // namespace

// ------------------------------------------------------------------------------------------------------------
// Public interface
// ------------------------------------------------------------------------------------------------------------

std::string floresCode(const std::string& lang) {
    static const std::map<std::string, std::string> m = {
        {"hi", "hin_Deva"}, {"te", "tel_Telu"}, {"mr", "mar_Deva"}, {"kn", "kan_Knda"}, {"ta", "tam_Taml"},
        {"bn", "ben_Beng"}, {"gu", "guj_Gujr"}, {"or", "ory_Orya"}, {"pa", "pan_Guru"}};
    const auto it = m.find(lang);
    return it == m.end() ? std::string() : it->second;
}

std::string plainEnglish(const std::string& english) {
    // Same rules as GLOSSARY in tools/translate_kb.py (the knowledge-base translations): technical terms rewritten
    // in plain English that the model translates correctly ("bull's eye" was translated literally, "necrotic" as
    // "impure", "margin" as "retail"). Applied only to the input of the translator.
    static const std::vector<std::pair<std::regex, std::string>> rules = [] {
        const std::vector<std::pair<const char*, const char*>> g = {
        {R"(bull'?s[- ]eye pattern)", "target-like pattern"},
        {R"(bull'?s[- ]eye)", "target-like"},
        {R"(concentric rings)", "rings inside each other"},
        {R"(necrotic)", "dead and dry"},
        {R"(necrosis)", "drying and death of the tissue"},
        {R"(water-soaked)", "wet-looking"},
        {R"(chlorotic)", "yellowish"},
        {R"(chlorosis)", "yellowing"},
        {R"(sporulation)", "fungal growth"},
        {R"(downy)", "soft, fluffy"},
        {R"(defoliation)", "falling of leaves"},
        {R"(foliage)", "leaves"},
        {R"(inoculum)", "source of infection"},
        {R"(vegetative (phase|stage))", "leafy growth stage"},
        {R"(lesions)", "spots"},
        {R"(lesion)", "spot"},
        {R"((the )?marginal portions? of( the)?)", "the edges of the"},
        {R"(marginal)", "edge"},
        {R"(margins)", "edges"},
        {R"(margin)", "edge"},
        {R"(mycelium)", "fungal threads"},
        {R"(sclerotia)", "small hard fungal bodies"},
        {R"(pycnidia)", "tiny dark fungal dots"},
        {R"(ooze)", "sticky liquid"},
        {R"(mottling)", "patchy colouring"},
        {R"(stunting)", "poor growth"},
        // Found in the Llama answers of the Pi full test (2026-11-21): "blighted" as "broken" (mr), "blight" as
        // "boils" (hi), "light-pale" as "striped", "host-specific" as "nutrient-specific", "cultivars" as
        // "cultivation" (mr)
        {R"(blighted)", "dried up"},
        {R"(leaf spots and blight)", "leaf spots and drying of leaves"},
        {R"(blight appears)", "the disease appears"},
        {R"(light-pale green)", "pale green"},
        {R"(host-specific)", "crop-specific"},
        {R"(cultivars)", "varieties"},
        {R"(cultivar)", "variety"},
        {R"(pre-?mature)", "early"},
        {R"(midrib)", "middle vein of the leaf"},
        };
        std::vector<std::pair<std::regex, std::string>> r;
        for (const auto& [pattern, plain] : g)
            r.emplace_back(std::regex(std::string("\\b") + pattern + "\\b", std::regex::icase | std::regex::ECMAScript),
                           plain);
        return r;
    }();
    std::string s = english;
    for (const auto& [re, plain] : rules) {
        std::string out;
        auto begin = std::sregex_iterator(s.begin(), s.end(), re);
        size_t last = 0;
        for (auto it = begin; it != std::sregex_iterator(); ++it) {
            out.append(s, last, static_cast<size_t>(it->position()) - last);
            std::string rep = plain;
            if (!it->str().empty() && std::isupper(static_cast<unsigned char>(it->str()[0])))
                rep[0] = static_cast<char>(std::toupper(static_cast<unsigned char>(rep[0])));   // keep sentence case
            out += rep;
            last = static_cast<size_t>(it->position() + it->length());
        }
        out.append(s, last, std::string::npos);
        s = out;
    }
    return s;
}

std::string mosesNormalize(const std::string& text) { return toU8(mosesNormalizeU(toU32(text))); }
std::string mosesTokenize(const std::string& text) { return toU8(mosesTokenizeU(toU32(text))); }
std::string transliterateFromDevanagari(const std::string& text, const std::string& isoLang) {
    return toU8(transliterateU(toU32(text), isoLang));
}
std::string detokenizeIndic(const std::string& text) { return toU8(detokenizeIndicU(toU32(text))); }

Prepared preprocessEnglish(const std::string& english, const std::string& tgtLang) {
    if (floresToIso().count(tgtLang) == 0 || tgtLang == "eng_Latn")
        throw std::invalid_argument("unsupported target language: " + tgtLang);
    Prepared p;
    U32 s = puncNorm(toU32(english));                       // 1) punctuation normalisation
    for (char32_t& c : s) c = asciiDigit(c);                // 2) numerals to ASCII, then placeholders
    s = wrapWithPlaceholders(s, p.placeholders);
    s = mosesTokenizeU(mosesNormalizeU(strip(s)));          // 3) English: Moses normaliser + tokenizer
    p.text = "eng_Latn " + tgtLang + " " + toU8(strip(s));
    return p;
}

void addTermPlaceholder(Prepared& p, const std::string& marker, const std::string& replacement) {
    if (p.text.find(marker) == std::string::npos) return;
    // Next free placeholder number: the highest n of the "<IDn>" keys already in the map, plus one
    int next = 1;
    for (const auto& kv : p.placeholders)
        if (kv.first.rfind("<ID", 0) == 0 && kv.first.back() == '>') {
            const std::string digits = kv.first.substr(3, kv.first.size() - 4);
            if (!digits.empty() && std::all_of(digits.begin(), digits.end(), ::isdigit))
                next = std::max(next, std::stoi(digits) + 1);
        }
    const std::string id = "<ID" + std::to_string(next) + ">";
    for (size_t pos = p.text.find(marker); pos != std::string::npos; pos = p.text.find(marker, pos + id.size()))
        p.text.replace(pos, marker.size(), id);
    // The model often writes a placeholder at the start of a sentence without its closing bracket ("<ID1 ...",
    // "<ID1. ..."; Pi, 2026-11-21). These forms go first, before the regular keys, whose bare "ID1" would leave the
    // "<" behind; a full stop right after such an open placeholder is the model's, not the source's.
    const std::string n = std::to_string(next);
    PlaceholderMap open;
    // (Kannada attaches its case ending directly: "<ID1ANNU ..." -> name + ending.) The closed form stays first.
    for (const char* t : {"<ID", "<id", "< ID", "< id"}) {
        open.emplace_back(std::string(t) + n + ">", replacement);
        open.emplace_back(std::string(t) + n + " >", replacement);
        open.emplace_back(std::string(t) + n + ". ", replacement + " ");
        open.emplace_back(std::string(t) + n + " ", replacement + " ");
        if (next < 10) open.emplace_back(std::string(t) + n, replacement);   // "<ID1" is not the start of "<ID10"
    }
    p.placeholders.insert(p.placeholders.begin(), open.begin(), open.end());
    addPlaceholderKeys(p.placeholders, next, replacement);
}

std::string decodePieces(const std::vector<std::string>& pieces) {
    std::string joined;
    for (const std::string& piece : pieces) joined += piece;
    U32 s = strip(replaceAll(toU32(joined), U32{0x2581}, U" "));   // SentencePiece word marker -> space
    // transformers clean_up_tokenization (applied in this order)
    for (const auto& r : std::vector<std::pair<const char*, const char*>>{
             {" .", "."}, {" ?", "?"}, {" !", "!"}, {" ,", ","}, {" ' ", "'"}, {" n't", "n't"},
             {" 'm", "'m"}, {" 's", "'s"}, {" 've", "'ve"}, {" 're", "'re"}})
        s = replaceAll(s, u(r.first), u(r.second));
    return toU8(s);
}

// Numbers the model returned as a placeholder written in the target script (Odia "<\u0b06\u0b07. \u0b21\u0b3f. 1>",
// Bengali, Kannada, Tamil, Telugu ...): IndicTransToolkit lists the spellings of "ID" only for a few scripts, so
// these stayed in the text as "<... 1>" instead of the number (found in 76 knowledge-base translations). Any
// "<...n>" or "@...n>" left after the regular replacement is the placeholder n: it gets its original text back.
// Not in the Python toolkit, so the byte-exact comparison with it covers only texts without such leftovers.
U32 restoreLeftoverPlaceholders(const U32& text, const PlaceholderMap& placeholders) {
    std::map<int, U32> original;
    for (const auto& kv : placeholders) {
        const std::string& k = kv.first;
        if (k.size() > 4 && k.rfind("<ID", 0) == 0 && k.back() == '>') {
            const std::string n = k.substr(3, k.size() - 4);
            if (!n.empty() && std::all_of(n.begin(), n.end(), [](char c) { return c >= '0' && c <= '9'; }))
                original.emplace(std::stoi(n), toU32(kv.second));
        }
    }
    if (original.empty()) return text;
    static const std::wregex leftover(L"(@?)(?:<[^<>\\n]{0,30}?|[^\\s<>@]{1,12}[ .]{0,4}[^\\s<>@]{0,12}?[ .]{0,3})([0-9]+)\\s*[>\\]]");
    const std::wstring w = toW(text);
    std::wstring out;
    size_t last = 0;
    for (std::wsregex_iterator m(w.begin(), w.end(), leftover), end; m != end; ++m) {
        const auto found = original.find(std::stoi((*m)[2].str()));
        // only "<...n>" or "@...n>" forms, so ordinary text with a ">" is not touched
        const bool bracketed = m->str().find(L'<') != std::wstring::npos;
        if (found == original.end() || (!bracketed && (*m)[1].str().empty())) continue;
        out += w.substr(last, m->position() - last) + (*m)[1].str() + toW(found->second);
        last = m->position() + m->length();
    }
    out += w.substr(last);
    return fromW(out);
}

std::string postprocess(const std::string& decoded, const std::string& tgtLang, const PlaceholderMap& placeholders) {
    const auto it = floresToIso().find(tgtLang);
    if (it == floresToIso().end() || tgtLang == "eng_Latn")
        throw std::invalid_argument("unsupported target language: " + tgtLang);
    U32 s = toU32(decoded);
    // Odia fix of IndicTransToolkit; it runs before transliteration, as in the Python code
    if (tgtLang.rfind("ory", 0) == 0) s = replaceAll(s, U32{0x0B2F, 0x0B3C}, U32{0x0B5F});
    for (const auto& kv : placeholders) s = replaceAll(s, toU32(kv.first), toU32(kv.second));
    s = restoreLeftoverPlaceholders(s, placeholders);
    // once more on the final text: before detokenizing, a leftover can still be spread out ("@ X . Y . 3 >")
    return toU8(restoreLeftoverPlaceholders(detokenizeIndicU(transliterateU(s, it->second)), placeholders));
}

bool hasRepetition(const std::string& text) {
    const std::vector<U32> words = splitWs(toU32(text));
    for (size_t width = 1; width <= 4; ++width) {
        if (words.size() < 4 * width) continue;
        for (size_t start = 0; start + 4 * width <= words.size(); ++start) {
            bool same = true;
            for (size_t k = width; k < 4 * width && same; ++k) same = words[start + k] == words[start + k % width];
            if (same) return true;
        }
    }
    return false;
}

}  // namespace kr::indic_text
