"""Reproduce the accepted-answer and unreviewed-KB translation evaluation."""
import argparse
from collections import Counter
import csv
import hashlib
import importlib.metadata
import json
import platform
import resource
import subprocess
import time

from translate_indictrans2 import ROOT, LANGUAGES, MODEL_ID, REVISION, Translator, dump, load_answers, translate_answers


class EvaluationCache:
    """Reuse identical sentence/language/literal inputs, never for speed benchmarks."""
    def __init__(self, engine, prior):
        self.engine, self.cache, self.last_cache_hit, self.hits = engine, {}, False, 0
        for answer in prior:
            for sentence in answer["sentences"]:
                if sentence.get("translation") is not None:
                    key = (sentence["english"], answer["language"], ())
                    self.cache[key] = (sentence["translation"], sentence["protected_text_check"])

    def translate(self, english, language, terms=()):
        start = time.perf_counter()
        key = (english, language, tuple(sorted(t for t in terms if t)))
        self.last_cache_hit = key in self.cache
        if self.last_cache_hit:
            self.hits += 1
            text, ok = self.cache[key]
            return text, ok, time.perf_counter() - start
        text, ok, seconds = self.engine.translate(english, language, terms)
        self.cache[key] = (text, ok)
        return text, ok, seconds


def prepare(reference_revision="faa26afdfe7e96e6124fcf652c6264872ad5acb1"):
    answers, excluded, inputs = [], [], []
    paths = sorted((ROOT / "results/pi5_bench/2026-11-18_llama1b_lora").glob("lora_*.json"))
    paths.append(ROOT / "results/llama_lora/kaggle_full_run/eval_lora_1b_pte_int4.json")
    for path in paths:
        inputs.append({"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        for row in load_answers(path):
            if row.get("accepted", True) and row["text"].strip():
                answers.append(row)
            else:
                excluded.append({"id": row["id"], "reason": "not accepted or empty", "kept": row["text"]})
    reference_commit = subprocess.check_output(["git", "rev-parse", reference_revision], cwd=ROOT, text=True).strip()
    raw = subprocess.check_output(["git", "show", reference_commit + ":app/kb/tomato_kb.json"], cwd=ROOT)
    kb = json.loads(raw)
    references, chemicals = [], []
    for i, row in enumerate(kb["chunks"]):
        if row["section"] == "chemical":
            chemicals.append("kb_" + str(i))
            continue
        item = dict(row, id="kb_" + str(i), text=row["en"], accepted=True,
                    source={"method": "reference_extract", "extract_id": i,
                            "source_id": row["source"], "section": row["section"]})
        references.append(item)
    return answers, references, {"inputs": inputs, "reference_commit": reference_commit,
                                "reference_sha256": hashlib.sha256(raw).hexdigest(),
                                "accepted_answers": len(answers), "excluded_answers": excluded,
                                "reference_extracts": len(references), "excluded_chemical_rows": chemicals,
                                "both_translation_sets_reviewed": False}


def summarize(out, answers, references, translated, metadata):
    from sacrebleu.metrics import CHRF
    metric = CHRF()
    reference_by_id = {r["id"]: r for r in references}
    metrics = {}
    for language in LANGUAGES:
        rows = [r for r in translated if r["language"] == language]
        sentences = [s for r in rows for s in r["sentences"]]
        checked = [s for s in sentences if s["number_check"] is not None]
        with_numbers = [s for s in checked if s["number_check"]["expected"]]
        kb_rows = [r for r in rows if r["id"] in reference_by_id]
        # Include withheld candidates in agreement metrics, never in display output.
        complete = [r for r in kb_rows if all(s["translation"] is not None for s in r["sentences"])]
        hypotheses = [" ".join(s["translation"] for s in r["sentences"]) for r in complete]
        refs = [reference_by_id[r["id"]][language] for r in complete]
        metrics[language] = {
            "sentences": len(sentences), "number_checked": len(checked),
            "number_passed": sum(s["number_check"]["passed"] for s in checked),
            "number_pass_rate": sum(s["number_check"]["passed"] for s in checked) / len(checked) if checked else None,
            "sentences_with_numbers": len(with_numbers),
            "number_bearing_pass_rate": sum(s["number_check"]["passed"] for s in with_numbers) / len(with_numbers) if with_numbers else None,
            "withheld": sum(s["status"] == "withheld" for s in sentences),
            "errors": sum(s["status"] == "error" for s in sentences),
            "protected_text_or_completion_failures": sum(s.get("protected_text_check") is False for s in sentences),
            "repetition_failures": sum(s.get("repetition_check") is False for s in sentences),
            "digit_scripts": dict(Counter(script for s in checked for script in s["number_check"]["digit_scripts"])),
            "reference_extracts_scored": len(complete),
            "reference_chrf": metric.corpus_score(hypotheses, [refs]).score if hypotheses else None}
    metadata["chrf_signature"] = str(metric.get_signature())
    dump(out / "summary.json", {"metadata": metadata, "languages": metrics})
    # Choose one Pi answer per topic when available, then the first accepted
    # held-out answer. Six topics (including healthy) x nine languages.
    chosen = {}
    for a in answers:
        chosen.setdefault(a["topic"], a["id"])
    with (out / "review_sheet.csv").open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["id", "language", "english", "translation", "meaning_correct",
                         "understandable_for_farmer", "comment"])
        for row in translated:
            if chosen.get(row["topic"]) != row["id"]:
                continue
            english = " ".join(s["english"] for s in row["sentences"])
            target = " ".join(s["translation"] or "" for s in row["sentences"])
            # Repo is ASCII. The Windows export also supplies a decoded UTF-8 sheet.
            writer.writerow([row["id"], row["language"], english,
                             target.encode("unicode_escape").decode("ascii"), "", "", ""])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--backend", choices=["fp32", "dynamic-int8"], default="fp32")
    parser.add_argument("--output-dir", type=lambda s: ROOT / s, default=ROOT / "results/indictrans2")
    parser.add_argument("--resume", action="store_true", help="Resume matching completed answer records")
    parser.add_argument("--reference-revision", default="faa26afdfe7e96e6124fcf652c6264872ad5acb1")
    args = parser.parse_args()
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    answers, references, inventory = prepare(args.reference_revision)
    dump(out / "inventory.json", inventory)
    dump(out / "reference_inputs.json", references)
    metadata = dict(inventory, model=MODEL_ID, revision=REVISION, backend=args.backend,
                    platform=platform.platform(), threads=4, beams=5, batch_size=1,
                    packages={p: importlib.metadata.version(p) for p in
                              ["torch", "transformers", "indictranstoolkit", "sacrebleu", "ctranslate2",
                               "sentencepiece", "huggingface-hub", "tokenizers", "safetensors",
                               "sacremoses", "indic-nlp-library-itt", "numpy", "regex"]})
    translated = []
    if args.resume and (out / "translations.json").exists():
        prior = json.loads((out / "translations.json").read_text())
        for key in ["inputs", "reference_sha256", "backend", "model", "revision", "threads", "beams"]:
            if prior["metadata"][key] != metadata[key]:
                raise ValueError("Resume metadata mismatch: " + key)
        translated = prior["answers"]
    engine = Translator(args.model_dir, args.backend)
    metadata.update(load_seconds=engine.load_seconds, load_peak_rss_mb=engine.load_peak_rss_mb,
                    parameter_count=engine.parameter_count, resumed_answer_languages=len(translated),
                    sentence_cache="Identical input/language/protected terms reused; cache_hit records lookup timing")
    cached = EvaluationCache(engine, translated)
    completed = {(a["id"], a["language"]) for a in translated}
    start = time.perf_counter()
    for i, answer in enumerate(answers + references):
        missing = [lang for lang in LANGUAGES if (answer["id"], lang) not in completed]
        if not missing:
            continue
        translated.extend(translate_answers(cached, [answer], missing))
        dump(out / "translations.json", {"metadata": metadata, "answers": translated})
        print(str(i + 1) + "/" + str(len(answers + references)) + " " + answer["id"], flush=True)
    metadata.update(current_session_seconds=time.perf_counter() - start, cache_hits=cached.hits,
                    answer_seconds_total=sum(a["seconds"] for a in translated),
                    peak_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024)
    dump(out / "translations.json", {"metadata": metadata, "answers": translated})
    summarize(out, answers, references, translated, metadata)


if __name__ == "__main__":
    main()
