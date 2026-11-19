"""Summarise C++ advisor evaluations (krishirakshak --eval-advisor) and prepare the manual distortion review.

Each run folder in results/llama_eval/<run>/ holds eval.jsonl (one JSON line per topic plus a summary line, written by
the C++ application) and run_info.txt (prompt file and options). This script prints one table row per run and writes
review.md into the run folder: for every accepted answer, each kept sentence next to the source sentence that supports
it best, so a person can check that no kept sentence changes the meaning of its source (a "distortion"). It also writes
answers.json and summary.json with the same keys as llm/eval_advisor.py (task deliverable D2).

Usage:
    python -m llm.summarize_eval results/llama_eval/baseline_demo results/llama_eval/v1_demo ...
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from llm.grounding import Grounding  # noqa: E402

LIST_MARKER = re.compile(r"^([IVXLC]+|\d+|[a-z])[.)]$")


def load_run(folder):
    rows, summary = [], None
    for line in (folder / "eval.jsonl").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue          # the application also prints empty lines
        obj = json.loads(line)
        if "summary" in obj:
            summary = obj["summary"]
        elif isinstance(obj.get("llama"), dict):
            rows.append(obj)
    return rows, summary


def best_source(ground, sentence, sources):
    """The source sentence with the most shared content words (same tokens as the grounding check)."""
    content = {ground.token(w) for w in ground.words(sentence) if len(w) >= ground.min_len and w not in ground.stop}
    best, hits = "", -1
    for s in sources:
        h = len(content & {ground.token(w) for w in ground.words(s)})
        if h > hits:
            best, hits = s, h
    return best, hits, len(content)


def main():
    data = json.loads((REPO / "results" / "llama_lora" / "prompt_facts.json").read_text(encoding="utf-8"))
    ground = Grounding(data["grounding"])
    facts = {t["topic"]: [s for f in t["grounding_facts"] for s in ground.split_sentences(f["text"])]
             for t in data["topics"]}
    llama_facts = {t["topic"]: t["llama_facts"] for t in data["topics"]}

    print("| run | accepted | refused first | grounded | dropped | list markers dropped | rejected topics |")
    print("|---|---|---|---|---|---|---|")
    for arg in sys.argv[1:]:
        folder = Path(arg)
        rows, summary_line = load_run(folder)
        acc = [r for r in rows if r["llama"]["accepted"]]
        refused = [r["topic"] for r in rows if "first_attempt" in r["llama"]["stats"]]
        grounded = sum(r["llama"]["grounded_sentences"] for r in rows)
        dropped = [d for r in rows for d in r["llama"]["dropped_sentences"]]
        markers = sum(bool(LIST_MARKER.match(d.strip())) for d in dropped)
        rejected = [r["topic"] for r in rows if not r["llama"]["accepted"]]
        print(f"| {folder.name} | {len(acc)}/{len(rows)} | {len(refused)} | {grounded} ({grounded / max(1, len(rows)):.1f}/topic) "
              f"| {len(dropped)} | {markers} | {', '.join(rejected)} |")

        info = (folder / "run_info.txt").read_text(encoding="utf-8").strip() if (folder / "run_info.txt").exists() else ""
        out = [f"# Distortion review - {folder.name}", "", info, "",
               "For every accepted answer: each kept sentence (K) and the source sentence that supports it best (S), with "
               "the number of shared content words. Mark a kept sentence as a distortion if it changes the meaning of "
               "its source (wrong cause, wrong plant part, instruction made stronger or weaker, generic claim).", ""]
        for r in rows:
            L = r["llama"]
            refused_note = " (refused first, retry answer)" if "first_attempt" in L["stats"] else ""
            out.append(f"## {r['topic']} - {'ACCEPTED' if L['accepted'] else 'rejected'}, "
                       f"{L['grounded_sentences']} kept{refused_note}")
            if not L["accepted"]:
                out.append(f"Reasons: {', '.join(L['rejected_reasons'])}")
                out.append("")
                continue
            # Kept sentences as the check saw them: the raw text split like the check splits it, minus the dropped
            # ones. (The application joins kept sentences with spaces, so lines without a full stop run together in
            # L["text"]; that is how the farmer sees them, but each line was checked on its own.)
            dropped = list(L["dropped_sentences"])
            kept = []
            for s in ground.split_sentences(L["raw_text"]):
                if s in dropped:
                    dropped.remove(s)
                else:
                    kept.append(s)
            for s in kept:
                src, hits, n = best_source(ground, s, facts[r["topic"]])
                out += [f"- K: {s}", f"  S ({hits}/{n}): {src}"]
            out.append("")
        (folder / "review.md").write_text("\n".join(out) + "\n", encoding="utf-8")
        write_json(folder, rows, summary_line, info, llama_facts)


def write_json(folder, rows, summary_line, info, llama_facts):
    """answers.json and summary.json with the same keys as llm/eval_advisor.py, so C++ and Python runs compare."""
    answers = []
    for r in rows:
        L, stats = r["llama"], r["llama"]["stats"]
        first = stats.get("first_attempt")
        answers.append({"topic": r["topic"], "accepted": L["accepted"], "grounded": L["grounded_sentences"],
                        "refused_first": first is not None, "first_answer": first["text"] if first else None,
                        "dropped": len(L["dropped_sentences"]), "seconds": round(stats.get("total_s", 0.0), 1),
                        "facts": llama_facts.get(r["topic"], []), "answer": L["raw_text"], "kept": L["text"],
                        "dropped_sentences": L["dropped_sentences"], "rejected_reasons": L["rejected_reasons"]})
    (folder / "answers.json").write_text(json.dumps(answers, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    n = max(1, len(answers))
    prompt = re.search(r"prompt=(\S+)", info)
    options = re.search(r"options=(.*)", info)
    summary = {"runtime": "C++ krishirakshak --eval-advisor",
               "pte": Path((summary_line or {}).get("config", {}).get("llama", "")).name,
               "prompt": Path(prompt[1]).name if prompt else "",
               "options": options[1].strip() if options else "",
               "topics": len(answers), "accepted": sum(a["accepted"] for a in answers),
               "refused_first": sum(a["refused_first"] for a in answers),
               "mean_grounded": round(sum(a["grounded"] for a in answers) / n, 2),
               "mean_dropped": round(sum(a["dropped"] for a in answers) / n, 2),
               "rejected_topics": [a["topic"] for a in answers if not a["accepted"]]}
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
