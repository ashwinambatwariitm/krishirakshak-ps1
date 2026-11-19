"""Offline, sentence-aligned IndicTrans2 evaluation. See docs/TRANSLATION_INDICTRANS2.md."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import resource
import sys
import time
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from llm.grounding import Grounding

MODEL_ID = "ai4bharat/indictrans2-en-indic-dist-200M"
REVISION = "2cfd0a20057756d756bf3e53528f492afc52f91a"
LANGUAGES = dict(zip("hi te mr kn ta bn gu or pa".split(),
                     "hin_Deva tel_Telu mar_Deva kan_Knda tam_Taml ben_Beng guj_Gujr ory_Orya pan_Guru".split()))
DIGIT_ZERO = dict(zip(LANGUAGES, [0x966, 0xc66, 0x966, 0xce6, 0xbe6, 0x9e6, 0xae6, 0xb66, 0xa66]))
# Preserve punctuation within numbers: 1.0 is not interchangeable with 10 or 1.
NUMBER = re.compile(r"(?<!\w)[+-]?\d+(?:[.,]\d+)*(?:\s*[-\u2013\u2014]\s*\d+(?:[.,]\d+)*)?|\d+(?:[.,]\d+)*")
# Names in the evaluation KB, including biological products and named cultivars.
PROTECTED = ["Trichoderma asperellum (viride)", "Trichoderma asperellum",
             "Pseudomonas fluorescens", "Trichoderma harzianum", "Trichoderma viride",
             "neem seed kernel extract (NSKE)", "azadirachtin", "Azadirachtin",
             "Beauveria bassiana", "Lecanicillium lecanii", "Metarhizium anisopliae",
             "Bacillus thuringiensis var.", "kurstaki", "Ha/Sl NPV", "Neem oil",
             "Arka Abhed F1", "Arka Ananya", "Kashi Vishesh", "Kashi Amrit",
             "COTH 2", "TNAU Tomato Hybrid Co3"]
# Protect application rates, concentrations and their units verbatim, including
# compound scientific notation. Timing/temperature remain subject to number checks.
DOSE = re.compile(r"(?:@\s*)?\d+(?:[.,]\d+)*(?:\s*[-x^]\s*\d+)*\s*"
                  r"(?:%(?:\s*(?:W/W|EC))?|(?:cfu|kg|ml|g|l|LE)(?:\s*/\s*(?:kg|ac|acre|ha|litre|ml))?\b"
                  r"|/\s*(?:acre|ha|ac)\b|traps/ha\b)(?:\s+seeds)?", re.I)


def dump(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="ascii")


def number_check(english, translation, language):
    def tokens(text):
        return NUMBER.findall(text)

    def canonical(token):
        return re.sub(r"\s+", "", token).replace("\u2013", "-").replace("\u2014", "-")

    expected = [canonical(t) for t in tokens(english)]
    actual = tokens(translation)
    normalized, scripts, invalid = [], set(), []
    for token in actual:
        norm = ""
        for ch in token:
            if ch.isdecimal():
                value = unicodedata.decimal(ch)
                norm += str(value)
                if "0" <= ch <= "9":
                    scripts.add("ASCII")
                elif DIGIT_ZERO[language] <= ord(ch) <= DIGIT_ZERO[language] + 9:
                    scripts.add(LANGUAGES[language].split("_")[1])
                else:
                    invalid.append(ch)
            else:
                norm += ch
        normalized.append(canonical(norm))
    missing = list((Counter(expected) - Counter(normalized)).elements())
    extra = list((Counter(normalized) - Counter(expected)).elements())
    return {"passed": not (missing or extra or invalid), "expected": expected,
            "observed": actual, "normalized": normalized, "digit_scripts": sorted(scripts),
            "missing": missing, "extra": extra, "invalid_digits": invalid}


def protect(text, terms):
    """Use email entities, which IndicProcessor masks, then restore exact literals.

    Missing or repeated entities fail closed. The glossary is explicit: arbitrary
    new product names must be supplied through protected_terms or --protect.
    """
    spans = [m.span() for m in DOSE.finditer(text)]
    for term in sorted(set(PROTECTED + terms), key=len, reverse=True):
        if term:
            spans.extend(m.span() for m in re.finditer(re.escape(term), text, re.I))
    merged = []
    for start, end in sorted(spans):
        if merged and start < merged[-1][1]:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    if "@keep.invalid" in text:
        raise ValueError("Reserved protection marker in input")
    mapping = {"literal" + str(i) + "@keep.invalid": text[a:b]
               for i, (a, b) in enumerate(merged)}
    for (a, b), marker in reversed(list(zip(merged, mapping))):
        text = text[:a] + marker + text[b:]
    return text, mapping


def repeated_output(text):
    """Catch observed decoder loops without claiming to validate meaning."""
    words = text.split()
    for width in range(1, 5):
        for start in range(len(words) - 4 * width + 1):
            block = words[start:start + width]
            if words[start:start + 4 * width] == block * 4:
                return True
    return False


def load_answers(path):
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict) and "llama" in data:
        return [{"id": Path(path).stem, "topic": data["disease"]["topic"],
                 "text": data["llama"]["text"], "accepted": data["llama"].get("accepted", False),
                 "sources": [c for b in data.get("advice_blocks", []) for c in b.get("chunks", [])]}]
    if isinstance(data, dict) and "answers" in data:
        data = data["answers"]
    if not isinstance(data, list):
        raise ValueError("Expected a Pi answer, list of answers, or {answers: [...]}")
    return [dict(row, id=row.get("id", Path(path).stem + "_" + str(i)),
                 text=row.get("kept", row.get("text", "")))
            if isinstance(row, dict) else {"id": str(i), "text": row}
            for i, row in enumerate(data)]


def align(sentence, sources, grounding):
    """Reproduce the guard's first highest-overlap source selection, with provenance.

    Older result files do not save source IDs for kept sentences. This is marked
    reconstructed, not represented as provenance captured by the original run.
    """
    words = grounding.words(sentence)
    content = [grounding.token(w) for w in words
               if len(w) >= grounding.min_len and w not in grounding.stop
               and grounding.token(w) not in grounding.stop and w not in grounding.negations]
    best, hits = None, 0
    for source in sources:
        for source_sentence in Grounding.split_sentences(source.get("text", source.get("en", ""))):
            tokens = {grounding.token(w) for w in grounding.words(source_sentence)}
            count = sum(w in tokens for w in content)
            if count > hits:
                hits, best = count, (source, source_sentence)
    if best and grounding.keep_grounded(sentence, [best[1]])[1]:
        source, text = best
        return {"method": "reconstructed_guard_match", "extract_id": source.get("id"),
                "source_id": source.get("source_id", source.get("source")),
                "section": source.get("section"), "english": text}
    return {"method": "unresolved", "extract_id": None}


class Translator:
    def __init__(self, model_dir, backend="fp32", threads=4, beams=5):
        start = time.perf_counter()
        model_dir = Path(model_dir).resolve()
        if model_dir.is_relative_to(ROOT):
            raise ValueError("Model files must be outside the repository")
        config = json.loads((model_dir / "config.json").read_text())
        if (config.get("encoder_layers"), config.get("encoder_embed_dim"),
                config.get("decoder_layers")) != (18, 512, 18):
            raise ValueError("Only the 200M distilled architecture is allowed")
        # Keep executable-code cache writable and outside the repository; no downloads.
        os.environ.setdefault("HF_MODULES_CACHE", "/tmp/indictrans2_modules")
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["USE_TF"] = "0"
        os.environ["USE_FLAX"] = "0"
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        from IndicTransToolkit.processor import IndicProcessor
        torch.set_num_threads(threads)
        torch.set_num_interop_threads(1)
        self.torch, self.processor_cls, self.beams = torch, IndicProcessor, beams
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_dir), trust_remote_code=True,
                                                       local_files_only=True)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            str(model_dir), trust_remote_code=True, local_files_only=True,
            torch_dtype=torch.float32, attn_implementation="eager").eval()
        self.parameter_count = sum(p.numel() for p in self.model.parameters())
        if backend == "dynamic-int8":
            # Quantization peak includes the FP32 load; report it rather than hiding it.
            self.model = torch.ao.quantization.quantize_dynamic(
                self.model, {torch.nn.Linear}, dtype=torch.qint8, inplace=True)
        self.load_seconds = time.perf_counter() - start
        self.load_peak_rss_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

    def translate(self, english, language, terms=()):
        start = time.perf_counter()
        protected, mapping = protect(english, list(terms))
        # Fresh processor prevents a failed generation from leaking its queued
        # entity map into a later sentence.
        processor = self.processor_cls(inference=True)
        batch = processor.preprocess_batch([protected], src_lang="eng_Latn", tgt_lang=LANGUAGES[language])
        inputs = self.tokenizer(batch, return_tensors="pt", truncation=False, padding=True)
        if inputs["input_ids"].shape[1] > 256:
            raise ValueError("Sentence exceeds model's 256-token source limit")
        with self.torch.inference_mode():
            output = self.model.generate(**inputs, num_beams=self.beams, max_length=256,
                                         do_sample=False, use_cache=True)
        decoded = self.tokenizer.batch_decode(output, skip_special_tokens=True,
                                              clean_up_tokenization_spaces=True)
        translation = processor.postprocess_batch(decoded, lang=LANGUAGES[language])[0]
        entities_ok = all(translation.count(marker) == 1 for marker in mapping)
        for marker, original in mapping.items():
            translation = translation.replace(marker, original)
        # Never display a truncated generation or an unresolved placeholder.
        complete = int(output[0, -1]) == self.tokenizer.eos_token_id
        entities_ok = entities_ok and not re.search(r"<ID\d+>|@keep\.invalid", translation)
        return translation, bool(entities_ok and complete and translation.strip()), time.perf_counter() - start


def translate_answers(engine, answers, languages, extra_terms=()):
    facts = json.loads((ROOT / "results/llama_lora/prompt_facts.json").read_text())
    grounding = Grounding(facts["grounding"])
    topic_sources = {t["topic"]: t["grounding_facts"] for t in facts["topics"]}
    result = []
    for answer in answers:
        for language in languages:
            item = {"id": answer["id"], "topic": answer.get("topic"), "language": language,
                    "input_accepted": answer.get("accepted", True), "sentences": [], "display_text": ""}
            start = time.perf_counter()
            for index, english in enumerate(Grounding.split_sentences(answer["text"])):
                source = answer.get("source") or align(
                    english, answer.get("sources", topic_sources.get(answer.get("topic"), [])), grounding)
                row = {"index": index, "english": english, "translation": None, "language": language,
                       "source": source, "number_check": None, "seconds": 0, "display_text": ""}
                if answer.get("section") == "chemical" or source.get("section") == "chemical":
                    row.update(status="verbatim_chemical", display_text=english)
                elif not item["input_accepted"]:
                    row["status"] = "input_not_accepted"
                else:
                    try:
                        terms = list(extra_terms) + answer.get("protected_terms", [])
                        terms += [answer.get("product", ""), answer.get("dose", "")]
                        translated, entities_ok, seconds = engine.translate(english, language, terms)
                        check = number_check(english, translated, language)
                        repetition = repeated_output(translated)
                        ok = check["passed"] and entities_ok and not repetition
                        row.update(translation=translated, number_check=check, seconds=seconds,
                                   cache_hit=getattr(engine, "last_cache_hit", False),
                                   protected_text_check=entities_ok,
                                   repetition_check=not repetition,
                                   status="machine_translated" if ok else "withheld",
                                   display_text=translated if ok else "")
                    except Exception as exc:
                        row.update(status="error", error=type(exc).__name__ + ": " + str(exc))
                item["sentences"].append(row)
            item["seconds"] = time.perf_counter() - start
            item["display_text"] = " ".join(r["display_text"] for r in item["sentences"] if r["display_text"])
            result.append(item)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inp = parser.add_mutually_exclusive_group(required=True)
    inp.add_argument("--input", type=Path)
    inp.add_argument("--text", action="append")
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--backend", choices=["fp32", "dynamic-int8"], default="fp32")
    parser.add_argument("--languages", nargs="+", choices=list(LANGUAGES), default=list(LANGUAGES))
    parser.add_argument("--protect", action="append", default=[])
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--beams", type=int, default=5)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if min(args.threads, args.beams, args.repeat) < 1:
        parser.error("threads, beams and repeat must be positive")
    answers = load_answers(args.input) if args.input else [
        {"id": str(i), "text": t} for i, t in enumerate(args.text)]
    metadata = {"model": MODEL_ID, "revision": REVISION, "backend": args.backend,
                "threads": args.threads, "beams": args.beams, "batch_size": 1}
    try:
        engine = Translator(args.model_dir, args.backend, args.threads, args.beams)
        runs = []
        for _ in range(args.repeat):
            runs.append(translate_answers(engine, answers, args.languages, args.protect))
        metadata.update(load_seconds=engine.load_seconds, load_peak_rss_mb=engine.load_peak_rss_mb,
                        parameter_count=engine.parameter_count,
                        peak_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
        dump(args.output, {"metadata": metadata, "runs": runs})
        if any(s["status"] in {"error", "withheld"} for run in runs for a in run for s in a["sentences"]):
            return 2
    except Exception as exc:
        dump(args.output, {"metadata": metadata, "error": type(exc).__name__ + ": " + str(exc)})
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
