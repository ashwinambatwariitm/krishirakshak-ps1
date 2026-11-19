"""Compare CTranslate2 threading layouts on whole Llama answers (Pi 5).

Each layout runs in its own process (peak RSS is per process):
  A  1 worker x 2 threads, sentences one after another          (current)
  B  4 workers x 1 thread, one sentence per worker in parallel
  C  2 workers x 2 threads, two sentences at a time
  D  1 worker x 4 threads, all sentences of the answer in one batch
  E  1 worker x 2 threads, all sentences in one batch
Timing covers CT2 only; preprocessing (~6 ms/sentence) is done up front.

Run in the Pi bundle folder (model_int8/, spm/model.SRC, hf_reference.json; see
tools/bench_indictrans2_ct2_pi.sh):
    python bench_indictrans2_layouts.py LAYOUT --per-lang 12 --out layout_LAYOUT.json
Result (Pi 5, 108 answers): E is fastest -- results/indictrans2/ct2_pi5/README.md
"""
import argparse
import glob
import importlib.util
import json
import resource
import statistics
import sys
import time
from pathlib import Path

for m in ("torch", "tensorflow", "transformers", "sacrebleu", "jax", "flax", "matplotlib"):
    sys.modules[m] = None  # keep the runtime lean, as in bench_ct2.py
import ctranslate2
import sentencepiece as spm

LAYOUTS = {  # name: (inter_threads, intra_threads, mode)
    "A": (1, 2, "serial"),
    "B": (4, 1, "parallel"),
    "C": (2, 2, "parallel"),
    "D": (1, 4, "batch"),
    "E": (1, 2, "batch"),
}
LANGUAGES = dict(zip("hi te mr kn ta bn gu or pa".split(),
                     "hin_Deva tel_Telu mar_Deva kan_Knda tam_Taml ben_Beng guj_Gujr ory_Orya pan_Guru".split()))
OPTS = dict(beam_size=5, max_decoding_length=256, max_input_length=256)


def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def load_processor():
    pkg = importlib.util.find_spec("IndicTransToolkit").submodule_search_locations[0]
    spec = importlib.util.spec_from_file_location("IndicTransToolkit.processor",
                                                  glob.glob(str(Path(pkg) / "processor*.so"))[0])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.IndicProcessor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("layout", choices=LAYOUTS)
    ap.add_argument("--per-lang", type=int, default=20, help="answers per language")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    inter, intra, mode = LAYOUTS[args.layout]

    # Same answer set for every layout: first N multi-sentence-capable answers per language.
    answers, count = [], {}
    for a in json.loads(Path("hf_reference.json").read_text())["answers"]:
        if count.get(a["language"], 0) < args.per_lang and a["sentences"]:
            count[a["language"]] = count.get(a["language"], 0) + 1
            answers.append(a)

    Proc = load_processor()
    sp = spm.SentencePieceProcessor(model_file="spm/model.SRC")

    def tokens(english, lang):
        pre = Proc(inference=True).preprocess_batch([english], src_lang="eng_Latn",
                                                    tgt_lang=LANGUAGES[lang])[0]
        s, t, text = pre.split(" ", 2)
        return [s, t] + sp.encode(text, out_type=str)

    jobs = [(a["id"], a["language"], [tokens(s["english"], a["language"]) for s in a["sentences"]])
            for a in answers]

    tr = ctranslate2.Translator("model_int8", device="cpu", inter_threads=inter, intra_threads=intra)
    tr.translate_batch([jobs[0][2][0]], **OPTS)  # warm-up
    load_rss = rss_mb()

    rows = []
    for aid, lang, batch in jobs:
        t0 = time.perf_counter()
        if mode == "serial":
            hyps = [tr.translate_batch([x], **OPTS)[0].hypotheses[0] for x in batch]
        elif mode == "parallel":
            # One job per sentence; CT2 dispatches them to its worker pool.
            futures = tr.translate_batch(batch, max_batch_size=1, asynchronous=True, **OPTS)
            hyps = [f.result().hypotheses[0] for f in futures]
        else:
            hyps = [r.hypotheses[0] for r in tr.translate_batch(batch, **OPTS)]
        dt = time.perf_counter() - t0
        rows.append({"id": aid, "language": lang, "sentences": len(batch), "seconds": dt,
                     "outputs": ["".join(h) for h in hyps]})

    secs = sorted(r["seconds"] for r in rows)
    summary = {"layout": args.layout, "inter_threads": inter, "intra_threads": intra, "mode": mode,
               "answers": len(rows), "sentences": sum(r["sentences"] for r in rows),
               "total_seconds": sum(secs), "median_answer_seconds": statistics.median(secs),
               "p95_answer_seconds": secs[int(0.95 * (len(secs) - 1))], "max_answer_seconds": secs[-1],
               "rss_after_load_mb": load_rss, "peak_rss_mb": rss_mb()}
    Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
