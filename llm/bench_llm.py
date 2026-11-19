"""Benchmark Llama .pte files with the real application prompts (INT4 vs FP32 table for the report).

For each .pte file and each test case (diagnosis + language), records: model load time, prompt tokens, time to first
token, tokens per second, peak resident memory of the process, and whether the answer passed the output check.

Usage:
    python -m llm.bench_llm models/llama3_2_1b_instruct_8da4w.pte /mnt/c/krishirakshak_store/llama_export/llama3_2_1b_instruct_fp32.pte \
        --tokenizer models/llama3_2_tokenizer.model --csv results/llama_bench_wsl.csv

Run each .pte in a separate process (this script does that) so the peak-memory numbers do not mix.
"""
import argparse
import csv
import json
import resource
import subprocess
import sys
from pathlib import Path

CASES = [("late_blight", "en"), ("early_blight", "en"), ("yellow_leaf_curl_virus", "en"), ("bacterial_spot", "en"),
         ("late_blight", "hi"), ("early_blight", "hi"), ("mites", "en")]


def run_one(pte, tokenizer):
    """Child process: load one .pte, run every case, print one JSON line per case."""
    from app.pipeline.advisor import LlamaAdvisor
    from app.pipeline.coordinator import DEFAULT_CONFIG
    from app.pipeline.guard import check_output
    from app.pipeline.knowledge import KnowledgeBase

    kb = KnowledgeBase(DEFAULT_CONFIG["kb_db"], DEFAULT_CONFIG["kb_json"])
    advisor = LlamaAdvisor(pte, tokenizer)
    for topic, lang in CASES:
        facts = kb.retrieve_for_diagnosis(topic, lang)
        line = f"Diagnosis: {kb.topic_name(topic, 'en')} on a tomato leaf (model confidence 92%)."
        text, stats = advisor.advise(line, facts, lang)
        ok, reasons = check_output(text, facts, lang, diagnosed_topic=topic)
        peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        print(json.dumps({"pte": Path(pte).name, "pte_mb": round(Path(pte).stat().st_size / 2**20),
                          "load_s": round(advisor.load_seconds, 2), "topic": topic, "lang": lang, **stats,
                          "peak_rss_mb": round(peak_mb), "check_ok": ok, "reasons": ";".join(reasons),
                          "text": text}, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pte", nargs="+")
    parser.add_argument("--tokenizer", required=True)
    parser.add_argument("--csv", default="results/llama_bench.csv")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        run_one(args.pte[0], args.tokenizer)
        return
    rows = []
    for pte in args.pte:
        # The runner also prints the generated tokens to stdout as raw bytes; a Hindi character split across two
        # tokens is not valid UTF-8 on its own, so decode leniently and pick out the JSON result lines
        out = subprocess.run([sys.executable, "-m", "llm.bench_llm", pte, "--tokenizer", args.tokenizer, "--child"],
                             capture_output=True, check=True).stdout.decode("utf-8", errors="replace")
        for line in out.splitlines():
            if '{"pte"' in line:
                rows.append(json.loads(line[line.index('{"pte"'):]))
                r = rows[-1]
                print(f"{r['pte']:40s} {r['topic']:24s} {r['lang']} ttft {r.get('time_to_first_token_s')} s  "
                      f"{r.get('tokens_per_s')} tok/s  rss {r['peak_rss_mb']} MB  check {r['check_ok']}")
    Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=sorted({k for r in rows for k in r}))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {args.csv}")


if __name__ == "__main__":
    main()
