"""Numbers the report quotes from an end-to-end run (one JSON per photo and language in DIR/<lang>/).

    python3 tools/e2e/e2e_stats.py RUN_DIR/api [OTHER_RUN_DIR/api]     # one run, or two runs side by side
"""
import glob, json, os, statistics as S, sys, collections

LANGS = ["en", "hi", "mr", "te", "kn", "ta", "bn", "gu", "or", "pa"]


def load(d):
    rows = []
    for l in LANGS:
        for f in sorted(glob.glob(f"{d}/{l}/*.json")):
            r = json.load(open(f))
            r["_lang"], r["_photo"] = l, os.path.basename(f)[:-5]
            rows.append(r)
    return rows


def med(v, nd=1):
    v = sorted(v)
    return f"{S.median(v):.{nd}f} ({v[0]:.{nd}f}-{v[-1]:.{nd}f}, n={len(v)})" if v else "-"


def stats(d):
    R = load(d)
    T = lambda k: [r["timings_ms"][k] for r in R if k in r.get("timings_ms", {})]
    tr = [r for r in R if r.get("translation")]
    en_ll = [r for r in R if r["_lang"] == "en" and (r.get("llama") or {}).get("text")]
    acc = [r["llama"]["stats"] for r in R if (r.get("llama") or {}).get("text") and r["llama"].get("stats")]
    sev = [v for v in T("severity") if v > 1]
    temps = [r["device"]["cpu_temp_end_c"] for r in R if r.get("device")]
    clocks = collections.Counter(r["device"]["cpu_freq_mhz"] for r in R if r.get("device"))
    hot = sum(r["device"].get("llama_skipped_hot", False) for r in R if r.get("device"))
    out = {
        "runs": len(R), "errors": sum("error" in r for r in R),
        "status": dict(collections.Counter(r.get("status") for r in R)),
        "quality ms": med(T("quality")), "leaf check ms": med(T("leaf_check")), "disease ms": med(T("disease")),
        "pest ms": med(T("pest")), "vision wall ms": med(T("vision_wall")), "severity ms (run)": med(sev),
        "retrieval ms": med(T("retrieval")), "llama s": med([v / 1000 for v in T("llama")], 2),
        "translation s": med([r["timings_ms"]["translation"] / 1000 for r in tr if "translation" in r["timings_ms"]], 2),
        "total translated s": med([r["timings_ms"]["total"] / 1000 for r in tr], 2),
        "total English with Llama s": med([r["timings_ms"]["total"] / 1000 for r in en_ll], 2),
        "not tomato ms": med([r["timings_ms"]["total"] for r in R if r.get("status") == "not_tomato"]),
        "llama accepted answers": len(acc),
        "prompt tokens": med([a["prompt_tokens"] for a in acc], 0), "generated tokens": med([a["generated_tokens"] for a in acc], 0),
        "first token s": med([a["time_to_first_token_s"] for a in acc], 1), "tokens/s": med([a["tokens_per_s"] for a in acc], 1),
        "cpu temp end C": med(temps, 1), "cpu clock MHz": dict(clocks), "llama skipped hot": hot,
        "llama share of translated answer %": round(100 * S.median([r["timings_ms"]["llama"] for r in tr if "llama" in r["timings_ms"]]) /
                                                 S.median([r["timings_ms"]["total"] for r in tr]), 1) if tr else "-",
    }
    # translation completeness: accepted English Llama sentences translated in every language
    per_lang = collections.Counter()
    for r in R:
        if r["_lang"] != "en" and r.get("translation") and r["translation"].get("sentences"):
            per_lang[r["_lang"]] += len(r["translation"]["sentences"])
    out["translated sentences per language"] = dict(per_lang)
    return out


dirs = sys.argv[1:]
res = [stats(d) for d in dirs]
for k in res[0]:
    print(f"{k:38s} " + "  |  ".join(str(r.get(k)) for r in res))
