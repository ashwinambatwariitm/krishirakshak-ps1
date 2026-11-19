"""Translate the verified knowledge base (app/kb/tomato_kb.json) into the 9 regional languages, once, offline.

The application then shows the verified extracts in the farmer's language straight from the file (no translation at
run time) - the same text every time, so a fluent speaker can review and correct it once.

What is translated, per language (hi te mr kn ta bn gu or pa):
  - extract text ("en" -> "<lang>"), chemical-row notes ("note" -> "note_i18n"[lang]),
  - topic names (topics[*].name[lang]) and the fixed interface messages (messages, any {"en": ...} leaf).
What is never translated: spray product names and doses (copied as published), sources, URLs. Hindi that exists
already (team translation) is kept; machine translations are listed per item in "mt" and per language in
"<lang>_reviewed": false. Messages with a {placeholder} are left in English (the app falls back to English).

Model: IndicTrans2 en-indic 200M on CTranslate2 INT8 (models/indictrans2_en_indic_200M_ct2_int8, the model of the
application), with the IndicTransToolkit pre/post-processing. Glossary: before translation, technical English
terms are rewritten in plain English that the model translates correctly (GLOSSARY below; found in the translations
reviewed so far: "bull's eye" was translated literally, "necrotic" as "impure", "margin" as "retail"). The English
text in the knowledge base is not changed.

Usage (translation venv: ctranslate2, sentencepiece, indictranstoolkit). Runs on a GPU (Kaggle notebook
ps1-kb-translate, FP16, a few minutes for 9 languages) or on a CPU (INT8, about 10 minutes per language):
    python tools/translate_kb.py [--langs hi te ...] [--limit N] [--out app/kb/tomato_kb.json]
           [--model-dir DIR --spm FILE] [--device cuda --compute-type float16]
"""
import argparse
import importlib.util
import glob
import json
import re
import sys
import time
from pathlib import Path

for _m in ("torch", "tensorflow", "transformers", "jax", "flax"):
    sys.modules[_m] = None   # not needed; keeps the run light
import ctranslate2
import sentencepiece as spm

ROOT = Path(__file__).resolve().parents[1]
LANGS = {"hi": "hin_Deva", "te": "tel_Telu", "mr": "mar_Deva", "kn": "kan_Knda", "ta": "tam_Taml",
         "bn": "ben_Beng", "gu": "guj_Gujr", "or": "ory_Orya", "pa": "pan_Guru"}

# English -> plain English, applied to the model input only (word boundaries, case-insensitive; longest first)
GLOSSARY = [
    (r"bull'?s[- ]eye pattern", "target-like pattern"),
    (r"bull'?s[- ]eye", "target-like"),
    (r"concentric rings", "rings inside each other"),
    (r"necrotic", "dead and dry"),
    (r"necrosis", "drying and death of the tissue"),
    (r"water-soaked", "wet-looking"),
    (r"chlorotic", "yellowish"),
    (r"chlorosis", "yellowing"),
    (r"sporulation", "fungal growth"),
    (r"downy", "soft, fluffy"),
    (r"defoliation", "falling of leaves"),
    (r"foliage", "leaves"),
    (r"inoculum", "source of infection"),
    (r"vegetative (phase|stage)", "leafy growth stage"),
    (r"lesions", "spots"),
    (r"lesion", "spot"),
    (r"(the )?marginal portions? of( the)?", "the edges of the"),   # "edge portion" -> "retail portion" (mr, FP16)
    (r"marginal", "edge"),
    (r"margins", "edges"),
    (r"margin", "edge"),
    (r"mycelium", "fungal threads"),
    (r"sclerotia", "small hard fungal bodies"),
    (r"pycnidia", "tiny dark fungal dots"),
    (r"ooze", "sticky liquid"),
    (r"mottling", "patchy colouring"),
    (r"stunting", "poor growth"),
]


# Known wrong renderings found in reviews (language, text, meaning); every run reports how many remain
KNOWN_BAD = [
    ("mr", "\u0915\u093f\u0930\u0915\u094b\u0933", "retail (for marginal)"),
    ("hi", "\u0928\u093e\u092a\u093e\u0915", "impure (for necrotic)"),
    ("hi", "\u092c\u0948\u0932 \u0915\u0940 \u0906\u0902\u0916", "ox's eye (for bull's eye)"),
    ("mr", "\u092c\u0948\u0932\u093e\u091a\u094d\u092f\u093e", "ox's (for bull's eye)"),
    ("kn", "\u0cb8\u0cb8\u0ccd\u0caf\u0cb6\u0cbe\u0cb8\u0ccd\u0ca4\u0ccd\u0cb0\u0cc0\u0caf", "botanical (for vegetative)"),
]


def simplify(text):
    for pattern, plain in GLOSSARY:
        text = re.sub(r"\b" + pattern + r"\b", lambda m: plain.capitalize() if m.group(0)[0].isupper() else plain,
                      text, flags=re.I)
    return text


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


class KbTranslator:
    def __init__(self, model_dir, spm_path, device, compute_type, threads):
        self.Proc = load_processor()
        self.sp = spm.SentencePieceProcessor(model_file=str(spm_path))
        if device == "cuda":
            self.tr = ctranslate2.Translator(str(model_dir), device="cuda", compute_type=compute_type)
        else:
            self.tr = ctranslate2.Translator(str(model_dir), device="cpu", compute_type=compute_type,
                                             inter_threads=max(1, threads // 4), intra_threads=4)
        self.max_batch = 32 if device == "cuda" else 8
        print(f"model {model_dir} on {device} ({compute_type})", flush=True)

    def translate(self, texts, lang, batch=64):
        flores = LANGS[lang]
        out = []
        for i in range(0, len(texts), batch):
            chunk = texts[i:i + batch]
            procs, toks = [], []
            for t in chunk:
                p = self.Proc(inference=True)
                pre = p.preprocess_batch([simplify(t)], src_lang="eng_Latn", tgt_lang=flores)[0]
                a, b, body = pre.split(" ", 2)
                procs.append(p)
                toks.append([a, b] + self.sp.encode(body, out_type=str))
            res = self.tr.translate_batch(toks, beam_size=5, max_decoding_length=256, max_input_length=256,
                                          max_batch_size=self.max_batch)
            for p, r in zip(procs, res):
                hyp = r.hypotheses[0]
                if len(hyp) >= 256:                       # truncated: keep English rather than half a sentence
                    out.append(None)
                    continue
                out.append(p.postprocess_batch([hf_cleanup("".join(hyp).replace("▁", " ").strip())],
                                               lang=flores)[0])
        return out


def translate_ui(tr, ui_path, js_path, langs):
    """Interface labels of the farmer app in the other languages, written as a JavaScript file the app loads.
    {placeholders} are protected with a number that must come back exactly once; otherwise the label stays English."""
    en = json.loads(Path(ui_path).read_text(encoding="utf-8"))
    keys = list(en)
    marker = "37"
    # Short labels have no context: "Check Plant" became "check the factory" in Tamil. Interface labels only: "plant"
    # -> "tomato plant" (the app is about tomato plants)
    def ui_context(t):
        return re.sub(r"\b(?<!tomato )plants?\b", lambda m: "tomato " + m.group(0).lower(), t, flags=re.I)
    src = [re.sub(r"\{\w+\}", marker, ui_context(simplify(en[k]))) for k in keys]
    out = {}
    for lang in langs:
        out[lang] = {}
        for k, t in zip(keys, tr.translate(src, lang)):
            ph = re.findall(r"\{\w+\}", en[k])
            if not t:
                continue
            if ph:
                if t.count(marker) != 1 or len(ph) != 1:
                    continue
                t = t.replace(marker, ph[0])
            out[lang][k] = t
        print(f"ui {lang}: {len(out[lang])}/{len(keys)} labels", flush=True)
    Path(js_path).write_text(
        "/* GENERATED by tools/translate_kb.py (IndicTrans2, machine translation, not yet reviewed): interface labels\n"
        " * of the farmer app in the regional languages; English and Hindi are in i18n.js. */\n"
        "window.I18N_REGIONAL = " + json.dumps(out, ensure_ascii=True, indent=1) + ";\n", encoding="ascii")


def message_leaves(node, path=()):
    """All {"en": text, ...} dictionaries inside the messages tree, with their path."""
    if isinstance(node, dict):
        if isinstance(node.get("en"), str):
            yield path, node
        for k, v in node.items():
            if k not in ("en", "hi") and isinstance(v, dict):
                yield from message_leaves(v, path + (k,))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default=str(ROOT / "app/kb/tomato_kb.json"))
    ap.add_argument("--out", default=None, help="default: overwrite --kb")
    ap.add_argument("--langs", nargs="+", default=list(LANGS))
    ap.add_argument("--limit", type=int, default=0, help="only the first N extracts (trial run)")
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--model-dir", default=str(ROOT / "models/indictrans2_en_indic_200M_ct2_int8"))
    ap.add_argument("--spm", default=str(ROOT / "models/indictrans2_model.SRC"))
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    ap.add_argument("--compute-type", default="default", help="e.g. float16 on a GPU, int8 on a CPU")
    ap.add_argument("--ui", help="English interface labels of the farmer app (JSON {key: text}, from app/web/js/i18n.js)")
    ap.add_argument("--ui-js", help="output: app/web/js/i18n_regional.js with the labels in the other languages")
    args = ap.parse_args()

    kb = json.loads(Path(args.kb).read_text(encoding="utf-8"))
    tr = KbTranslator(args.model_dir, args.spm, args.device, args.compute_type, args.threads)
    chunks = kb["chunks"][: args.limit or None]
    msgs = [(p, d) for p, d in message_leaves(kb["messages"]) if "{" not in d["en"]]
    skipped_msgs = [".".join(p) for p, d in message_leaves(kb["messages"]) if "{" in d["en"]]

    t0 = time.time()
    for lang in args.langs:
        # 1. extract text (keep existing Hindi team translations)
        todo = [c for c in chunks if c.get("en") and not (lang == "hi" and c.get("hi") and "hi" not in c.get("mt", []))]
        for c, t in zip(todo, tr.translate([c["en"] for c in todo], lang)):
            if t:
                c[lang] = t
                c["mt"] = sorted(set(c.get("mt", [])) | {lang})
        # 2. notes of the spray rows (product and dose are never translated)
        notes = [c for c in chunks if c.get("note")]
        for c, t in zip(notes, tr.translate([c["note"] for c in notes], lang)):
            if t:
                c.setdefault("note_i18n", {})[lang] = t
        # 3. topic names and fixed messages (existing Hindi kept)
        topics = [v for v in kb["topics"].values() if not (lang == "hi" and v["name"].get("hi"))]
        # names: short and easily mistranslated ("Early blight" -> "early disease"), so the English name is kept
        # in brackets, as in the team's Hindi names ("... (Early blight)")
        for v, t in zip(topics, tr.translate([v["name"]["en"] for v in topics], lang)):
            if t:
                v["name"][lang] = f"{t} ({v['name']['en']})"
        leaves = [d for _, d in msgs if not (lang == "hi" and d.get("hi"))]
        for d, t in zip(leaves, tr.translate([d["en"] for d in leaves], lang)):
            if t:
                d[lang] = t
        kb[f"{lang}_reviewed"] = False
        print(f"{lang}: {len(todo)} extracts, {len(notes)} notes, {len(topics)} names, {len(leaves)} messages "
              f"({time.time() - t0:.0f} s)", flush=True)

    bad = {f"{lang}: {meaning}": sum(1 for c in chunks if word in (c.get(lang) or ""))
           for lang, word, meaning in KNOWN_BAD}
    print("known wrong renderings left:", bad, flush=True)
    kb["translations"] = {
        "languages": list(LANGS),
        "method": f"IndicTrans2 en-indic 200M (CTranslate2, {args.device} {args.compute_type}) with a plain-English "
                  "glossary (tools/translate_kb.py)",
        "machine_translated": "items list their machine-translated languages in 'mt'; Hindi without 'mt' is the "
                              "team translation",
        "never_translated": "spray product names, doses, sources",
        "messages_left_in_english": skipped_msgs,
        "review": "Machine translations; to be reviewed by fluent speakers (see <lang>_reviewed).",
        "known_wrong_renderings_left": bad,
    }
    if args.ui and args.ui_js:
        translate_ui(tr, args.ui, args.ui_js, [l for l in args.langs if l != "hi"])   # Hindi labels: team version
    out = Path(args.out or args.kb)
    out.write_text(json.dumps(kb, ensure_ascii=True, indent=1) + "\n", encoding="ascii")
    print("written", out)


if __name__ == "__main__":
    main()
