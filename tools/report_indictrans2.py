"""Summarize isolated benchmark runs and compare FP32/dynamic INT8 candidates."""
import json
from pathlib import Path
import statistics

from sacrebleu.metrics import CHRF
from translate_indictrans2 import ROOT, LANGUAGES, dump


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
            "pi_int8_seconds_scenario_not_measurement": [2 * int_warm, 5 * int_warm]}
    summary["pi_estimate_caveat"] = (
        "2x-5x laptop warm time is an illustrative slowdown scenario, not a calibrated prediction. "
        "ARM kernels, cooling, runtime support and memory may invalidate it. No Pi speed claim follows.")
    summary["chrf_signature"] = str(metric.get_signature())
    dump(out / "bench_summary.json", summary)


if __name__ == "__main__":
    main()
