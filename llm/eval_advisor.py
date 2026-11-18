"""Measure how well the Llama advisor rewrites the verified extracts, on a laptop (no Raspberry Pi, no photos).

For each topic (disease or pest) the script builds exactly the prompt the application builds after a diagnosis
(diagnosis line + the extracts Llama receives, with the prompt in prompts/, and the application's single retry with
a plain prompt when Llama refuses), runs the .pte with ExecuTorch's
TextLLMRunner (the same runtime as the application, here on the laptop CPU), and scores every answer with the
application's grounding check (llm/grounding.py, identical to cpp/src/output_guard.cpp):

  accepted          the application would show the Llama text (at least two grounded sentences)
  grounded          number of sentences kept (each supported by one source sentence)
  dropped           sentences removed (invented, reversed, stitched, other wording)

Greedy decoding gives the same text on a laptop as on the Pi (only the speed differs), so prompt and model changes
can be measured here and confirmed on the Pi later.

Usage:
    python -m llm.eval_advisor --pte models/llama3_2_1b_instruct_8da4w.pte --tokenizer models/llama3_2_tokenizer.model
    python -m llm.eval_advisor ... --topics demo                # the six demo diseases (default)
    python -m llm.eval_advisor ... --topics all                 # every disease and pest with two or more facts
    python -m llm.eval_advisor ... --prompt prompts/my_variant.txt --out results/llama_eval/my_variant

Prompt file format (same as KR_ADVISOR_PROMPT of the C++ application): system text, a line "----USER----", user
template; placeholders {language}, {diagnosis}, {facts}.
Outputs in --out: answers.json (every answer with kept and dropped sentences) and summary.json; a table is printed.
English only (the application shows reviewed extracts, not Llama text, for Hindi).
"""
import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from llm.grounding import Grounding  # noqa: E402

DEMO = ["healthy", "early_blight", "late_blight", "septoria_leaf_spot", "bacterial_spot", "yellow_leaf_curl_virus"]
MIN_GROUNDED = 2   # kMinGroundedSentences in cpp/src/pipeline.cpp


def diagnosis_line(t, confidence=92, spread="medium"):
    """Same text as Pipeline::analyse (pipeline.cpp) builds for Llama."""
    if t["kind"] == "pest":
        return f"An insect pest was found on the tomato plant: {t['name']}."
    line = f"Diagnosis: {t['name']} on a tomato leaf (model confidence {confidence}%)."
    if spread:
        line += f" Estimated spread on the photographed leaf: {spread}."
    if t["urgent"]:
        line += " This disease is urgent: it spreads very fast."
    if t["reliability"] == "low":
        line += " The photo result is not certain; the farmer should confirm with the local KVK."
    return line


def chat(system, user):
    return ("<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n" + system + "<|eot_id|>"
            "<|start_header_id|>user<|end_header_id|>\n\n" + user + "<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n\n")


def facts_block(t):
    return "".join(f"{i}. {f}\n" for i, f in enumerate(t["llama_facts"], 1))


def looks_like_refusal(text):
    """Same test as looksLikeRefusal() in llama_advisor.cpp."""
    low = text[:60].lower()
    return low.startswith(("i can't", "i cannot", "i can not", "i'm unable", "i am unable", "i won't"))


def fallback_prompt(t):
    """The application's single retry after a refusal (llama_advisor.cpp)."""
    return chat("You are a helpful agricultural extension worker in India.",
                "Here is advice for a tomato farmer:\n" + facts_block(t) +
                "\nSay the same advice again in simple English, one short sentence for each point.")


def build_prompt(prompt_text, t):
    system_t, user_t = prompt_text.split("----USER----")
    facts = facts_block(t)
    d = diagnosis_line(t)

    def fill(s):  # as the KR_ADVISOR_PROMPT loader: placeholders, then leading/trailing new lines removed
        return s.replace("{language}", "English").replace("{diagnosis}", d).replace("{facts}", facts).strip("\n")
    return chat(fill(system_t), fill(user_t))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pte", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--prompt", default=str(REPO / "prompts" / "advise_keep_words.txt"))
    ap.add_argument("--facts", default=str(REPO / "results" / "llama_lora" / "prompt_facts.json"))
    ap.add_argument("--topics", default="demo", help="demo, all, or a comma-separated list of topic ids")
    ap.add_argument("--max-new-tokens", type=int, default=160)
    ap.add_argument("--out", default=str(REPO / "results" / "llama_eval" / "run"))
    args = ap.parse_args()

    data = json.load(open(args.facts, encoding="utf-8"))
    ground = Grounding(data["grounding"])
    topics = {t["topic"]: t for t in data["topics"]}
    if args.topics == "demo":
        names = DEMO
    elif args.topics == "all":
        names = [k for k, t in topics.items() if t["kind"] in ("disease", "pest") and len(t["llama_facts"]) >= 2]
    else:
        names = [s.strip() for s in args.topics.split(",")]
    prompt_text = Path(args.prompt).read_text(encoding="utf-8")

    # The two imports register the operators of the exported graph (custom SDPA attention, 4-bit embedding)
    import executorch.extension.llm.custom_ops.custom_ops  # noqa: F401
    import executorch.kernels.quantized  # noqa: F401
    from executorch.extension.llm.runner import GenerationConfig, TextLLMRunner
    runner = TextLLMRunner(args.pte, args.tokenizer)
    config = GenerationConfig(echo=False, max_new_tokens=args.max_new_tokens, temperature=0.0, num_bos=0, num_eos=0)

    rows = []
    for name in names:
        t = topics[name]
        start = time.time()

        def run(prompt):
            pieces = []
            runner.reset()   # clear the KV cache of the previous answer
            runner.generate(prompt, config, token_callback=pieces.append)
            return "".join(pieces).replace("<|eot_id|>", "").strip()
        text = first = run(build_prompt(prompt_text, t))
        refused = looks_like_refusal(first)
        if refused:      # the application retries once with a plain prompt
            text = run(fallback_prompt(t))
        kept, n, dropped = ground.keep_grounded(text, [f["text"] for f in t["grounding_facts"]])
        rows.append({"topic": name, "accepted": n >= MIN_GROUNDED and len(kept) <= 1200, "grounded": n,
                     "refused_first": refused, "first_answer": first if refused else None,
                     "dropped": len(dropped), "seconds": round(time.time() - start, 1), "facts": t["llama_facts"],
                     "answer": text, "kept": kept, "dropped_sentences": dropped})
        r = rows[-1]
        print(f"{'ACCEPT' if r['accepted'] else 'REJECT'} {name:32s} grounded {n:2d}  dropped {len(dropped):2d}  "
              f"{'(refused, retried) ' if refused else ''}({r['seconds']} s)", flush=True)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    json.dump(rows, open(out / "answers.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    summary = {"pte": Path(args.pte).name, "prompt": Path(args.prompt).name, "topics": len(rows),
               "accepted": sum(r["accepted"] for r in rows), "refused_first": sum(r["refused_first"] for r in rows),
               "mean_grounded": round(sum(r["grounded"] for r in rows) / max(1, len(rows)), 2),
               "mean_dropped": round(sum(r["dropped"] for r in rows) / max(1, len(rows)), 2)}
    json.dump(summary, open(out / "summary.json", "w"), indent=2)
    print(f"\naccepted {summary['accepted']}/{summary['topics']} | mean grounded sentences {summary['mean_grounded']} | "
          f"mean dropped {summary['mean_dropped']}  -> {out}")


if __name__ == "__main__":
    main()
