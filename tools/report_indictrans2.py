"""Summarize isolated benchmark runs and compare FP32/dynamic INT8 candidates."""
import json
import re
import statistics

from sacrebleu.metrics import CHRF
from translate_indictrans2 import ROOT, LANGUAGES, dump


def update_document(bench, quality):
    total = sum(r["sentences"] for r in quality["languages"].values())
    withheld = sum(r["withheld"] for r in quality["languages"].values())
    errors = sum(r["errors"] for r in quality["languages"].values())
    qlines = ["The evaluation completed {} aligned sentence-language records: {} withheld and {} execution errors. "
              "The fluent-speaker review sheet has 54 rows (six demo topics in nine languages).".format(total, withheld, errors), "",
              "| Language | Reference chrF | Number passes / checked | Number-bearing pass rate | Withheld | Errors |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for lang, row in quality["languages"].items():
        qlines.append("| {} | {:.2f} | {}/{} ({:.2%}) | {:.2%} | {} | {} |".format(
            lang, row["reference_chrf"], row["number_passed"], row["number_checked"],
            row["number_pass_rate"], row["number_bearing_pass_rate"], row["withheld"], row["errors"]))
    qlines.extend(["", "Each language is scored against all 38 non-chemical reference extracts. "
                   "Neither side is reviewed. Withheld counts include numeric, literal, truncation "
                   "and repetition failures; some conservative numeric failures are formatting changes."])
    slines = ["| WSL backend | Load seconds | Load/quantization peak MiB | Overall peak MiB |",
              "| --- | ---: | ---: | ---: |"]
    for name, row in bench["backends"].items():
        slines.append("| {} | {:.3f} | {:.1f} | {:.1f} |".format(
            name, row["load_seconds"], row["load_peak_rss_mb"], row["peak_rss_mb"]))
    slines.extend(["| CTranslate2 INT8 | Not available | Not measured | Not measured |", "",
                   "| Language | FP32 first / warm s | Dynamic INT8 first / warm s | FP32/INT8 chrF | Pi INT8 scenario s (not measured) |",
                   "| --- | ---: | ---: | ---: | ---: |"])
    for lang, row in bench["languages"].items():
        low, high = row["pi_int8_seconds_scenario_not_measurement"]
        slines.append("| {} | {:.3f} / {:.3f} | {:.3f} / {:.3f} | {:.2f} | {:.2f}-{:.2f} |".format(
            lang, row["fp32_first_seconds"], row["fp32_warm_median_seconds"],
            row["int8_first_seconds"], row["int8_warm_median_seconds"], row["fp32_int8_chrf"], low, high))
    slines.extend(["", "The FP32/INT8 comparison covers only two late-blight sentences per language. "
                   "Several languages change substantially, so close agreement is not demonstrated "
                   "across the dataset. Punjabi's slow repetitive candidate is withheld, but its "
                   "generation time remains included. Both measured backends exceed 600 MB peak RSS."])
    path = ROOT / "docs/TRANSLATION_INDICTRANS2.md"
    text = path.read_text(encoding="ascii")
    for name, lines in [("QUALITY_RESULTS", qlines), ("SPEED_RESULTS", slines)]:
        start, end = "<!-- " + name + " -->", "<!-- END_" + name + " -->"
        block = start + "\n\n" + "\n".join(lines) + "\n\n" + end
        if end in text:
            text = re.sub(re.escape(start) + ".*?" + re.escape(end), lambda _: block, text, flags=re.S)
        else:
            text = text.replace(start, block)
    path.write_text(text, encoding="ascii")


def main():
    out = ROOT / "results/indictrans2"
    fp = json.loads((out / "bench_fp32.json").read_text())
    quant = json.loads((out / "bench_dynamic_int8.json").read_text())
    metric = CHRF()
    summary = {"environment": "WSL2 x86_64, Intel Core i5-12500H, four inference threads",
               "sample": "Pi late-blight accepted answer, two sentences, one answer per language",
               "timing": "First traversal and median of the following two traversals; no concurrent inference",
               "rss_units": "MiB (Linux ru_maxrss / 1024), includes imports, loading and quantization",
               "pi": {"measured": False, "reason": "WSL-only per project owner; no Pi downloads or inference"},
               "backends": {"fp32": fp["metadata"], "dynamic-int8": quant["metadata"]},
               "languages": {}}
    for lang in LANGUAGES:
        a = [[r for r in run if r["language"] == lang][0] for run in fp["runs"]]
        b = [[r for r in run if r["language"] == lang][0] for run in quant["runs"]]
        source = [s["translation"] or "" for s in a[0]["sentences"]]
        target = [s["translation"] or "" for s in b[0]["sentences"]]
        fp_warm = statistics.median(r["seconds"] for r in a[1:])
        int_warm = statistics.median(r["seconds"] for r in b[1:])
        summary["languages"][lang] = {
            "fp32_first_seconds": a[0]["seconds"], "fp32_warm_median_seconds": fp_warm,
            "int8_first_seconds": b[0]["seconds"], "int8_warm_median_seconds": int_warm,
            "fp32_int8_chrf": metric.corpus_score(target, [source]).score,
            "exact_sentence_matches": sum(x == y for x, y in zip(source, target)),
            "sentences_compared": len(source),
            "fp32_repeat_candidates_identical": all(
                [s["translation"] or "" for s in r["sentences"]] == source for r in a),
            "int8_repeat_candidates_identical": all(
                [s["translation"] or "" for s in r["sentences"]] == target for r in b),
            "pi_int8_seconds_scenario_not_measurement": [2 * int_warm, 5 * int_warm]}
    summary["pi_estimate_caveat"] = (
        "2x-5x laptop warm time is an illustrative slowdown scenario, not a calibrated prediction. "
        "ARM kernels, cooling, runtime support and memory may invalidate it. No Pi speed claim follows.")
    summary["chrf_signature"] = str(metric.get_signature())
    dump(out / "bench_summary.json", summary)
    if (out / "summary.json").exists():
        update_document(summary, json.loads((out / "summary.json").read_text()))


if __name__ == "__main__":
    main()
