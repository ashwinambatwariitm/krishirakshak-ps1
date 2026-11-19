"""Write the expected outputs of the Python IndicTrans2 text processing, for the C++ parity test
(cpp/tests/indic_text_test.cpp checks cpp/src/indic_text.cpp against this file).

Cases:
  - every English sentence of the IndicTrans2 evaluation (results/indictrans2/translations.json) plus
    hand-written edge cases (numbers, units, URLs, e-mails, quotes, ellipses, non-breaking spaces, Indic digits):
      Moses normaliser, Moses tokenizer, full pre-processing for each target language;
  - model outputs for a subset of sentences x 9 languages (CTranslate2 INT8 model, decoded pieces):
      post-processing (placeholders, Devanagari -> target script, detokenisation), repetition check;
  - hand-written Devanagari strings for the detokeniser and the transliterator.
The file is written with ASCII escapes (repository files are ASCII only).

Build-time tool (translation venv with ctranslate2, sentencepiece, IndicTransToolkit):
    python cpp/tools/make_indic_text_oracle.py --ct2 ~/models/indictrans2_en_indic_200M_ct2_int8 \
        --spm-dir <HF snapshot with model.SRC> --out results/indictrans2/indic_text_oracle.json
"""
import argparse
import json
import sys
from pathlib import Path

for _m in ("torch", "tensorflow", "transformers", "jax", "flax"):
    sys.modules[_m] = None   # not needed; keeps this tool light
import importlib.util
import glob

import ctranslate2
import sentencepiece as spm
from indicnlp.tokenize import indic_detokenize
from indicnlp.transliterate.unicode_transliterate import UnicodeIndicTransliterator
from sacremoses import MosesPunctNormalizer, MosesTokenizer

ROOT = Path(__file__).resolve().parents[2]
LANGS = {"hi": "hin_Deva", "te": "tel_Telu", "mr": "mar_Deva", "kn": "kan_Knda", "ta": "tam_Taml",
         "bn": "ben_Beng", "gu": "guj_Gujr", "or": "ory_Orya", "pa": "pan_Guru"}
ISO = {"hin_Deva": "hi", "tel_Telu": "te", "mar_Deva": "mr", "kan_Knda": "kn", "tam_Taml": "ta",
       "ben_Beng": "bn", "guj_Gujr": "gu", "ory_Orya": "or", "pan_Guru": "pa"}

EDGE_ENGLISH = [
    "Spray mancozeb 2.5 g/L at 10-day intervals; remove infected leaves (about 25%).",
    "Apply 1,000 kg/ha of farmyard manure and 120:60:60 kg NPK per hectare.",
    "Use 0.3% copper oxychloride ( COC ) or 0.25 % chlorothalonil , twice .",
    '"Early blight" causes spots, which merge; leaves turn "yellow".',
    "Don't spray when it's raining... wait 2-3 days.",
    "Mr. Kumar's farm: visit www.icar.org.in or https://tnau.ac.in/agri for details.",
    "Email help@niphm.gov.in, call 1800-180-1551 (toll free).",
    "Temperature 20\u201325 \u00b0C and RH > 90 % favour the disease.",
    "Leaves turn yellow\u2026 then brown.",
    "Use 'Ridomil Gold' @ 2 g/L.",
    "Spray at 7 to 10 day intervals (e.g. 3 sprays), i.e. weekly.",
    "No. 5 fungicide; see pp. 12-14 and No 6.",
    "It is 1 1/2 inches long and 3.5cm wide.",
    "Ratio 1:2:3, dose 25 kg/ha; #tomato @krishi",
    "Spots \u2014 dark brown \u2014 appear on \u2018lower\u2019 leaves and \u201colder\u201d ones.",
    "Dose 2\u00a0g per litre\u00a0; temp 20\u00a0% and 3\u00a04 days\u00a0!",
    "Wait.... then spray.. again",
    "Spray \u096b times with \u0968.\u096b ml.",
    "Rogue out plants at 30, 45 and 60 DAT ; burn them .",
    "Remove leaves (lower ones)and destroy them ( do not compost ).",
    "Use resistant varieties like Arka Rakshak, Arka Samrat etc.",
    "Avoid overhead irrigation \u2013 use drip.",
    "The farmer's field had 5 's' shaped lesions; it 's bad.",
    "",
]

EDGE_DEVANAGARI = [   # tokenised model-style outputs, for detokeniser + transliterator cases
    "\u0938\u094d\u092a\u094d\u0930\u0947 ( \u0932\u0917\u092d\u0917 25 % ) \u0915\u0930\u0947\u0902 \u0964",
    "1 , 000 \u0915\u093f\u0932\u094b ; 10 : 30 \u092c\u091c\u0947 \u0964",
    "\u0926\u0935\u093e ' \u0930\u093f\u0921\u094b\u092e\u093f\u0932 ' \u0914\u0930 \" \u092e\u0948\u0902\u0915\u094b\u091c\u0947\u092c \" \u0964",
    "2 / 3 \u092d\u093e\u0917 - \u092a\u0924\u094d\u0924\u0947 / \u0924\u0928\u0947 \u0965",
    "\u0916 \u0917 \u0918 \u091b \u091d \u0920 \u0922 \u0925 \u0927 \u092b \u092c \u092d \u0936 \u0937 \u0915\u093c \u0921\u093c",
    "\u0909\u092a\u091a\u093e\u0930 # 1 [ \u0926\u0947\u0916\u0947\u0902 ] { \u0928\u094b\u091f } < \u0915\u0941\u091b > @ \u0928\u093e\u092e",
    "` \u0909\u0926\u094d\u0927\u0930\u0923 ` \u0914\u0930 \u092b\u093f\u0930 ` \u0926\u0942\u0938\u0930\u093e",
]


def load_processor():
    pkg = importlib.util.find_spec("IndicTransToolkit").submodule_search_locations[0]
    spec = importlib.util.spec_from_file_location("IndicTransToolkit.processor",
                                                  glob.glob(str(Path(pkg) / "processor*.so"))[0])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.IndicProcessor


def hf_cleanup(s):
    for a, b in ((" .", "."), (" ?", "?"), (" !", "!"), (" ,", ","), (" ' ", "'"),
                 (" n't", "n't"), (" 'm", "'m"), (" 's", "'s"), (" 've", "'ve"), (" 're", "'re")):
        s = s.replace(a, b)
    return s


def repeated_output(text):
    words = text.split()
    for width in range(1, 5):
        for start in range(len(words) - 4 * width + 1):
            if words[start:start + 4 * width] == words[start:start + width] * 4:
                return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ct2", required=True)
    ap.add_argument("--spm-dir", required=True)
    ap.add_argument("--translations", default=str(ROOT / "results/indictrans2/translations.json"))
    ap.add_argument("--model-subset", type=int, default=40, help="sentences translated per language")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    Proc = load_processor()
    data = json.loads(Path(args.translations).read_text())
    english = []
    for a in data["answers"]:
        for s in a["sentences"]:
            if s["english"] not in english:
                english.append(s["english"])
    english_all = english + [e for e in EDGE_ENGLISH if e not in english]

    norm, tok = MosesPunctNormalizer(lang="en"), MosesTokenizer(lang="en")
    moses = [{"input": e, "normalized": norm.normalize(e), "tokenized": " ".join(tok.tokenize(e, escape=False))}
             for e in english_all]

    pre = []
    for e in english_all:
        for lang, flores in LANGS.items():
            p = Proc(inference=True)
            out = p.preprocess_batch([e], src_lang="eng_Latn", tgt_lang=flores)[0]
            pre.append({"english": e, "tgt": flores, "expected": out})

    # Model outputs for post-processing cases (the post-processing input is the decoded model text).
    sp = spm.SentencePieceProcessor(model_file=str(Path(args.spm_dir) / "model.SRC"))
    tr = ctranslate2.Translator(args.ct2, device="cpu", intra_threads=4)
    subset = english[:args.model_subset] + [e for e in EDGE_ENGLISH if e]
    post = []
    for lang, flores in LANGS.items():
        rows = []
        for e in subset:
            p = Proc(inference=True)
            text = p.preprocess_batch([e], src_lang="eng_Latn", tgt_lang=flores)[0]
            a, b, body = text.split(" ", 2)
            rows.append((e, p, [a, b] + sp.encode(body, out_type=str)))
        results = tr.translate_batch([r[2] for r in rows], beam_size=5, max_decoding_length=256,
                                     max_input_length=256)
        for (e, p, _), res in zip(rows, results):
            pieces = res.hypotheses[0]
            decoded = hf_cleanup("".join(pieces).replace("\u2581", " ").strip())
            final = p.postprocess_batch([decoded], lang=flores)[0]
            post.append({"english": e, "tgt": flores, "pieces": pieces, "decoded": decoded,
                         "expected": final, "repetition": repeated_output(final)})

    xl = UnicodeIndicTransliterator()
    devanagari = []
    for s in EDGE_DEVANAGARI:
        for lang, flores in LANGS.items():
            devanagari.append({"input": s, "iso": ISO[flores],
                               "transliterated": xl.transliterate(s, "hi", ISO[flores]),
                               "detokenized": indic_detokenize.trivial_detokenize(s, ISO[flores])})

    out = {"note": "Generated by cpp/tools/make_indic_text_oracle.py from the Python reference "
                   "(IndicTransToolkit 1.1.1, sacremoses 0.2.0, indic-nlp-library-itt 0.1.1).",
           "moses": moses, "preprocess": pre, "postprocess": post, "devanagari": devanagari}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=True, indent=0))
    print(f"moses {len(moses)}  preprocess {len(pre)}  postprocess {len(post)}  devanagari {len(devanagari)}")


if __name__ == "__main__":
    main()
