"""Check that the Python grounding check (llm/grounding.py) gives the same decisions as the C++ one.

Runs the C++ check in replay mode on saved krishirakshak results and the Python copy on the same Llama texts, and
compares the kept sentences of every answer. Exit status 1 on any difference.

Usage:
    python tools/check_grounding_port.py build/x86/grounding_test results/llama_lora/prompt_facts.json bench/*_en.json
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from llm.grounding import Grounding  # noqa: E402


def main():
    binary, facts_path, *results = sys.argv[1:]
    data = json.load(open(facts_path, encoding="utf-8"))
    g = Grounding(data["grounding"])
    facts = {t["topic"]: t["grounding_facts"] for t in data["topics"]}   # text and section
    out = subprocess.run([binary, ".", "--replay", *results], capture_output=True, text=True, check=True).stdout
    # C++ prints "ACCEPT|REJECT <file> (<topic>): kept N, ..." followed by "    kept: <text>"
    cpp = dict(re.findall(r"^(?:ACCEPT|REJECT) (\S+) \(.*?\): kept \d+.*\n    kept: (.*)$", out, re.M))
    differences = 0
    for path in results:
        r = json.load(open(path, encoding="utf-8"))
        if path not in cpp:
            continue
        kept, n, _ = g.keep_grounded(r["llama"]["raw_text"], facts[r["disease"]["topic"]])
        same = kept == cpp[path]
        differences += not same
        print(("same " if same else "DIFF ") + Path(path).name + f" ({n} kept)")
        if not same:
            print("   C++   :", cpp[path], "\n   Python:", kept)
    print(f"{differences} differences in {len(cpp)} answers")
    sys.exit(1 if differences else 0)


if __name__ == "__main__":
    main()
