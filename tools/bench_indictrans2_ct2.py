"""Benchmark IndicTrans2 200M on CTranslate2 in Python (no torch/transformers at run time).

The text pipeline mirrors tools/translate_indictrans2.py (Hugging Face PyTorch tool):
IndicProcessor.preprocess -> "src tgt text" -> [src, tgt] + SPM pieces -> CT2 beam 5,
max 256 -> join pieces -> HF-style cleanup -> IndicProcessor.postprocess.

  --mode latency : late-blight answer, warm median of --repeat runs per language
  --mode parity  : every (sentence, language) of the PyTorch FP32 evaluation
                   (results/indictrans2/translations.json); exact-match rate
Always reports peak RSS (ru_maxrss) of this process.

Used on the Raspberry Pi 5 with tools/bench_indictrans2_ct2_pi.sh; results in results/indictrans2/ct2_pi5/.
"""
import argparse
import json
import resource
import statistics
import time
from pathlib import Path

LANGUAGES = dict(zip("hi te mr kn ta bn gu or pa".split(),
                     "hin_Deva tel_Telu mar_Deva kan_Knda tam_Taml ben_Beng guj_Gujr ory_Orya pan_Guru".split()))


def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def repeated_output(text):
    # Same loop detector as tools/translate_indictrans2.py.
    words = text.split()
    for width in range(1, 5):
        for start in range(len(words) - 4 * width + 1):
            block = words[start:start + width]
            if words[start:start + 4 * width] == block * 4:
                return True
    return False


def hf_cleanup(s):
    # transformers' clean_up_tokenization, used by the batch_decode call of the PyTorch tool.
    for a, b in ((" .", "."), (" ?", "?"), (" !", "!"), (" ,", ","), (" ' ", "'"),
                 (" n't", "n't"), (" 'm", "'m"), (" 's", "'s"), (" 've", "'ve"), (" 're", "'re")):
        s = s.replace(a, b)
    return s


class CT2Translator:
    def __init__(self, ct2_dir, spm_dir, threads, beams):
        import glob
        import importlib.util
        import sys
        # Block heavy frameworks: ctranslate2's optional converters and
        # IndicTransToolkit/__init__ would otherwise pull in TF/torch/transformers
        # (~1 GB RSS) that the runtime never uses.
        for m in ("torch", "tensorflow", "transformers", "sacrebleu", "jax", "flax", "matplotlib"):
            sys.modules[m] = None
        import ctranslate2
        import sentencepiece as spm
        # Locate the package without running its __init__ (which imports transformers).
        pkg = importlib.util.find_spec("IndicTransToolkit").submodule_search_locations[0]
        so = glob.glob(str(Path(pkg) / "processor*.so"))[0]
        spec = importlib.util.spec_from_file_location("IndicTransToolkit.processor", so)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.proc_cls = mod.IndicProcessor
        self.sp = spm.SentencePieceProcessor(model_file=str(Path(spm_dir) / "model.SRC"))
        self.tr = ctranslate2.Translator(str(ct2_dir), device="cpu",
                                         intra_threads=threads, inter_threads=1)
        self.beams = beams

    def translate(self, english, lang):
        t0 = time.perf_counter()
        proc = self.proc_cls(inference=True)
        tgt = LANGUAGES[lang]
        pre = proc.preprocess_batch([english], src_lang="eng_Latn", tgt_lang=tgt)[0]
        src_tag, tgt_tag, text = pre.split(" ", 2)
        tokens = [src_tag, tgt_tag] + self.sp.encode(text, out_type=str)
        res = self.tr.translate_batch([tokens], beam_size=self.beams,
                                      max_decoding_length=256, max_input_length=256)
        hyp = res[0].hypotheses[0]
        complete = len(hyp) < 256
        raw = hf_cleanup("".join(hyp).replace("\u2581", " ").strip())
        out = proc.postprocess_batch([raw], lang=tgt)[0]
        return out, complete, time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ct2", required=True)
    ap.add_argument("--spm-dir", required=True)
    ap.add_argument("--hf-results", required=True)
    ap.add_argument("--mode", choices=["latency", "parity"], required=True)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--beams", type=int, default=5)
    ap.add_argument("--repeat", type=int, default=5)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    answers = json.loads(Path(args.hf_results).read_text())["answers"]
    t0 = time.perf_counter()
    eng = CT2Translator(args.ct2, args.spm_dir, args.threads, args.beams)
    report = {"ct2": args.ct2, "threads": args.threads, "beams": args.beams,
              "load_seconds": time.perf_counter() - t0, "load_peak_rss_mb": rss_mb()}

    if args.mode == "latency":
        rows = {}
        for a in answers:
            if a["id"] != "lora_Tomato_leaf_late_blight":
                continue
            lang = a["language"]
            sents = [s["english"] for s in a["sentences"]]
            eng.translate(sents[0], lang)  # warm-up
            times, outs = [], None
            for _ in range(args.repeat):
                r = [eng.translate(s, lang) for s in sents]
                times.append(sum(x[2] for x in r))
                outs = r
            hf = [s["translation"] for s in a["sentences"]]
            rows[lang] = {"median_seconds": statistics.median(times),
                          "hf_fp32_seconds": a["seconds"],
                          "sentences": len(sents),
                          "repetition": any(repeated_output(o[0]) for o in outs),
                          "complete": all(o[1] for o in outs),
                          "matches_hf_fp32": sum(o[0] == h for o, h in zip(outs, hf)),
                          "ct2": [o[0] for o in outs], "hf": hf}
        report["latency"] = rows
    else:
        seen, rows = set(), []
        for a in answers:
            for s in a["sentences"]:
                key = (s["english"], s["language"])
                if key in seen:
                    continue
                seen.add(key)
                out, complete, sec = eng.translate(s["english"], s["language"])
                rows.append({"language": s["language"], "english": s["english"],
                             "hf_fp32": s["translation"], "ct2": out, "seconds": sec,
                             "match": out == s["translation"], "complete": complete,
                             "repetition": repeated_output(out),
                             "hf_repetition": not s.get("repetition_check", True)})
        by = {}
        for r in rows:
            b = by.setdefault(r["language"], {"n": 0, "match": 0, "rep": 0, "hf_rep": 0,
                                              "incomplete": 0, "seconds": 0.0})
            b["n"] += 1
            b["match"] += r["match"]
            b["rep"] += r["repetition"]
            b["hf_rep"] += r["hf_repetition"]
            b["incomplete"] += not r["complete"]
            b["seconds"] += r["seconds"]
        report["parity_by_language"] = by
        report["parity_rows"] = rows

    report["peak_rss_mb"] = rss_mb()
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k not in ("parity_rows",)},
                     ensure_ascii=False)[:4000])


if __name__ == "__main__":
    main()
