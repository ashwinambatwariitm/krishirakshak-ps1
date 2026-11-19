/*
 * indic_text.hpp - text processing around the IndicTrans2 translation model (English -> Indian languages).
 *
 * C++ port of the Python reference used when the model was evaluated (IndicTransToolkit 1.1.1 IndicProcessor
 * with inference=True, sacremoses 0.2.0 MosesPunctNormalizer/MosesTokenizer for English, indicnlp
 * UnicodeIndicTransliterator and trivial_detokenize). The model only sees text prepared exactly this way, so
 * the port follows the Python rules step by step, including their quirks; tests/indic_text_test.cpp checks it
 * against outputs saved from the Python code.
 *
 *   English sentence -> preprocessEnglish() -> "eng_Latn tam_Taml <Moses tokens>" -> SentencePiece -> model
 *   model pieces -> decodePieces() -> Devanagari-script text -> postprocess() -> text in the target script
 *
 * IndicTrans2 writes every Indic language in Devanagari script; postprocess() converts it to the target script
 * (Tamil, Telugu, ...) with the Unicode offset rule of indicnlp.
 *
 * One deliberate difference: Python numbers placeholders (<ID1>, <ID2>, ...) in the iteration order of a set,
 * which changes from run to run; here they are numbered in order of first appearance (deterministic).
 */
#pragma once

#include <string>
#include <utility>
#include <vector>

namespace kr::indic_text {

// Placeholder -> original text, in insertion order (restored in this order, like the Python dict).
using PlaceholderMap = std::vector<std::pair<std::string, std::string>>;

struct Prepared {
    std::string text;            // "eng_Latn <tgt> <tokenised English>", input of the SentencePiece step
    PlaceholderMap placeholders; // numbers, URLs, e-mails replaced by <IDn> before translation
};

// Prepares one English sentence for translation into tgtLang (FLORES code, e.g. "hin_Deva").
Prepared preprocessEnglish(const std::string& english, const std::string& tgtLang);

// Joins the SentencePiece pieces produced by the model into text (as the Hugging Face tokenizer's decode with
// clean_up_tokenization_spaces=True, which was used for the evaluated translations).
std::string decodePieces(const std::vector<std::string>& pieces);

// Restores placeholders, converts Devanagari to the target script and re-attaches punctuation.
std::string postprocess(const std::string& decoded, const std::string& tgtLang, const PlaceholderMap& placeholders);

// True if some block of 1-4 words repeats 4 times in a row (decoder loop), same rule as the Python tool.
bool hasRepetition(const std::string& text);

// Two-letter UI language code (hi, ta, ...) -> FLORES code used by the model (hin_Deva, tam_Taml, ...).
// Returns an empty string for a language the translator does not support.
std::string floresCode(const std::string& lang);

// Intermediate steps, exposed for the parity test.
std::string mosesNormalize(const std::string& text);
std::string mosesTokenize(const std::string& text);
std::string transliterateFromDevanagari(const std::string& text, const std::string& isoLang);
std::string detokenizeIndic(const std::string& text);

}  // namespace kr::indic_text
