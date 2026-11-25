/*
 * translator.hpp - translation stage: English advice -> Indian languages on the device, with IndicTrans2
 * (en-indic distilled 200M) running on the CTranslate2 C++ runtime (INT8 weights, ~210 MB on disk).
 *
 * The model was converted from the Hugging Face checkpoint with tools/convert_indictrans2_ct2.py.
 * Measured on the Raspberry Pi 5 (Python runtime with the same CTranslate2 build options, 108 Llama answers):
 *   - all sentences of an answer in ONE batch with 2 threads: median 1.19 s per answer, peak memory ~440 MB;
 *   - 4 threads is several times slower (OpenMP threads spin and compete), and 4 single-thread workers or
 *     2 workers x 2 threads are slower than one batch, because decoding is limited by memory bandwidth.
 * Translation runs after Llama; the two free cores stay available to the rest of the pipeline.
 *
 * Every translated sentence is checked: an output that hit the length limit, loops (a block of words repeated
 * four times) or still contains a placeholder is withheld and only the English sentence is shown.
 * The translations are machine output and are marked as unreviewed until a fluent speaker has checked them.
 */
#pragma once

#include <json.hpp>

#include <memory>
#include <string>
#include <vector>

namespace kr {

struct TranslatedSentence {
    std::string english;
    std::string text;            // translation in the target script (empty if the sentence was empty)
    bool complete = true;        // false if decoding stopped at the length limit
    bool repetition = false;     // decoder loop detected
    bool ok = false;             // shown to the farmer only if true
};

struct TranslationOutput {
    std::string lang;                         // two-letter code: hi, ta, ...
    std::vector<TranslatedSentence> sentences;
    std::string text;                         // the sentences that passed the checks, joined with spaces
    int withheld = 0;                         // sentences that failed a check (English is shown instead)
    double ms = 0.0;                          // pre-processing + model + post-processing
    double modelMs = 0.0;                     // CTranslate2 translate_batch only
    nlohmann::json toJson() const;
};

class Translator {
public:
    virtual ~Translator() = default;

    // English term -> text shown instead in the target language (the reviewed local disease or pest name)
    using Terms = std::vector<std::pair<std::string, std::string>>;

    // Translates the sentences of one answer as one batch. lang is a two-letter code (see supportedLanguages()).
    // Each term found in a sentence (case-insensitive) is not translated by the model: it is replaced by its given
    // local text, so "Early blight" becomes the knowledge base's Marathi name, not a literal "early disease".
    virtual TranslationOutput translate(const std::vector<std::string>& sentences, const std::string& lang,
                                        const Terms& terms = {}) = 0;

    static const std::vector<std::string>& supportedLanguages();   // hi te mr kn ta bn gu or pa

    // Loads the CTranslate2 model folder and the SentencePiece source model (model.SRC) from local disk;
    // returns nullptr if the files are missing.
    // threads: CTranslate2 threads (2 on the Raspberry Pi 5, see above); beamSize: 5 as in the evaluation.
    static std::unique_ptr<Translator> create(const std::string& modelDir, const std::string& spmPath,
                                              int threads = 2, int beamSize = 5);
};

}  // namespace kr
