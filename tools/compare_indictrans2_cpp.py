"""Compare the C++ translate_bench output on the Pi with the Python CTranslate2 results on the same Pi.

Usage: python tools/compare_indictrans2_cpp.py CPP.json PYTHON_ALL_SENTENCES.json PYTHON_LAYOUT_E.json
(files in results/indictrans2/ct2_pi5/)

Python parity file: one sentence per call, 2 threads (pi_parity_int8_t2.json, rows with language/english/ct2).
Python layout E: whole answer per batch, 2 threads, first 12 answers per language (layout_E.json, timing).
"""
import json
import statistics
import sys

cpp = json.load(open(sys.argv[1]))
py = json.load(open(sys.argv[2]))
lay = json.load(open(sys.argv[3]))

ref = {(r["language"], r["english"]): r["ct2"] for r in py["parity_rows"]}
same = diff = missing = 0
by_lang = {}
examples = []
for a in cpp["answers"]:
    for s in a["sentences"]:
        key = (a["lang"], s["english"])
        if key not in ref:
            missing += 1
            continue
        b = by_lang.setdefault(a["lang"], [0, 0])
        if s["text"] == ref[key]:
            same += 1
            b[0] += 1
        else:
            diff += 1
            b[1] += 1
            if len(examples) < 4:
                examples.append((a["lang"], s["english"], ref[key], s["text"]))
print("C++ vs Python on the Pi (final text): same %d, different %d, not in reference %d" % (same, diff, missing))
print({k: "%d/%d" % (v[0], v[0] + v[1]) for k, v in by_lang.items()})
for e in examples:
    print("--", e[0], e[1][:70]); print("   py :", ascii(e[2])[:140]); print("   cpp:", ascii(e[3])[:140])

# Timing on the same 108 answers as layout E (first 12 answers per language)
lay_ids = [(r["id"], r["language"]) for r in lay["rows"]]
cpp_t = {(a["id"], a["lang"]): a["seconds"] for a in cpp["answers"]}
c = sorted(cpp_t[k] for k in lay_ids if k in cpp_t)
p = sorted(r["seconds"] for r in lay["rows"])
q = lambda v, f: v[int(f * (len(v) - 1))]
print("same 108 answers   python E: median %.2f p95 %.2f max %.2f total %.0f | C++: median %.2f p95 %.2f max %.2f total %.0f"
      % (statistics.median(p), q(p, .95), p[-1], sum(p), statistics.median(c), q(c, .95), c[-1], sum(c)))
s = cpp["summary"]
print("C++ all %d answers: median %.2f p95 %.2f max %.2f, load %.0f ms, RSS after load %.0f MB, peak %.0f MB, withheld %d"
      % (s["answers"], s["median_answer_seconds"], s["p95_answer_seconds"], s["max_answer_seconds"], s["load_ms"],
         s["rss_after_load_mb"], s["peak_rss_mb"], s["withheld"]))
print("python layout E peak RSS %.0f MB, rss after load %.0f MB" % (lay["summary"]["peak_rss_mb"], lay["summary"]["rss_after_load_mb"]))
