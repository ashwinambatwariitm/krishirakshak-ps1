"""Python copy of the sentence-level grounding check of the C++ application (cpp/src/output_guard.cpp,
keepGroundedSentences), used to build and score the LoRA training data on Kaggle without the C++ build.

The word lists (stop words, negations, same-meaning groups, ...) and the thresholds are read from the file written by
    build/x86/grounding_test . --dump-facts results/llama_lora/prompt_facts.json
so both implementations always use the same lists. tools/check_grounding_port.py compares this module with the C++
check on saved Llama answers; the two must give the same decisions.

A sentence of the Llama answer is kept only if
  - it has at least min_content_words different content words (3+ letters, not stop words, stemmed, same-meaning
    words merged), so headers and one-word fragments are not counted as advice,
  - at least min_overlap of them occur in ONE sentence of the retrieved extracts, and all of them when the sentence
    has fewer than full_match_below content words (one changed word in a short sentence changes its meaning),
  - a negated sentence is supported by a source sentence negated in the same way: an instruction ("avoid", "do not")
    by an instruction, a statement ("is not") by a statement, so an instruction is never reversed,
  - a sentence stating a cause ("caused by", "due to") is supported by a source sentence stating one,
  - an instruction (it starts with an action verb) is not supported by a symptoms or spread extract, so a symptom
    is never turned into advice ("Prevent seedlings from rotting" from "Complete rotting of seedlings"),
  - every number in it appears in that source sentence, and if it uses any number of the source sentence it uses
    all of them (a schedule is never kept without its dose); the same for month names,
  - a disease name in it ("early blight": a word before blight, mildew, canker or mosaic) is in that source sentence,
  - it is not a repeat of an earlier sentence.

Facts can be given as plain strings or as {"text": ..., "section": ...}; the instruction rule needs the section.
"""
import re

_WORD = re.compile(r"[a-z']+")


class Grounding:
    def __init__(self, config):
        self.stop = set(config["stop_words"])
        self.negations = set(config["negations"])
        self.same = dict(config["same_meaning"])
        self.suffixes = list(config["stem_suffixes"])
        self.min_overlap = float(config["min_overlap"])
        self.min_len = int(config["min_word_length"])
        self.cause_stems = set(config["cause_stems"])
        self.min_content = int(config.get("min_content_words", 1))
        self.full_below = int(config.get("full_match_below", 0))
        self.instruction_negations = set(config.get("instruction_negations", []))
        self.action_verbs = set(config.get("action_verbs", []))
        self.description_sections = set(config.get("description_sections", []))
        self.months = set(config.get("months", []))
        self.name_heads = set(config.get("name_heads", []))

    # --- the helpers mirror output_guard.cpp one to one ---
    def stem(self, w):
        for suf in self.suffixes:
            if len(w) > len(suf) + 3 and w.endswith(suf):
                return w[: -len(suf)]
        return w

    def token(self, w):
        s = self.stem(w)
        return self.same.get(s, s)

    @staticmethod
    def words(s):
        # C++: ASCII letters and apostrophes, lower-cased; everything else separates words
        return _WORD.findall("".join(ch.lower() if ch.isascii() else " " for ch in s))

    @staticmethod
    def split_sentences(text):
        out, cur = [], ""
        for i, ch in enumerate(text):
            cur += ch
            end = ch in ".!?\n;"
            if end and (i + 1 == len(text) or text[i + 1] in " \t\n\r\f\v" or ch == "\n"):
                s = cur.strip(" \n")
                if s:
                    out.append(s)
                cur = ""
        s = cur.strip(" \n")
        if s:
            out.append(s)
        return out

    def has_negation(self, ws):
        return any(w in self.negations or (len(w) > 3 and w.endswith("n't")) for w in ws)

    def negation_kinds(self, ws):
        """{"instruction"} for "avoid", "do not", "don't", "never"; {"statement"} for "is not", "no", "without"."""
        kinds = set()
        for i, w in enumerate(ws):
            if w in self.instruction_negations:
                kinds.add("instruction")
            elif w == "not" and i > 0 and ws[i - 1] == "do":
                kinds.add("instruction")
            elif w in self.negations or (len(w) > 3 and w.endswith("n't")):
                kinds.add("statement")
        return kinds

    def has_cause(self, ws):
        return any(self.stem(w) in self.cause_stems for w in ws)

    def is_instruction(self, ws):
        return bool(ws) and ws[0] in self.action_verbs

    @staticmethod
    def numbers(s):
        out, cur = [], ""
        for ch in s + " ":
            if ch.isdigit() or (cur and ch in ".,"):
                cur += ch
            else:
                cur = cur.rstrip(".,")
                if cur:
                    out.append(cur)
                cur = ""
        return out

    def month_set(self, ws):
        return {w for w in ws if w in self.months}

    def name_pairs(self, ws):
        """Disease names such as "early blight": a content word followed by a name head word."""
        return {(ws[i - 1], w) for i, w in enumerate(ws) if i > 0 and w in self.name_heads
                and len(ws[i - 1]) >= self.min_len and ws[i - 1] not in self.stop}

    def content_words(self, ws):
        """Different content words of a sentence, in order of first use."""
        out = []
        for w in ws:
            s = self.token(w)
            if len(w) >= self.min_len and w not in self.stop and s not in self.stop and w not in self.negations \
                    and s not in out:
                out.append(s)
        return out

    def keep_grounded(self, text, facts):
        """Returns (kept text, number of kept sentences, dropped sentences), like keepGroundedSentences().
        facts: strings or {"text", "section"} dicts."""
        sources = []
        for fact in facts:
            fact_text, section = (fact, "") if isinstance(fact, str) else (fact["text"], fact.get("section", ""))
            for s in self.split_sentences(fact_text):
                ws = self.words(s)
                sources.append({"raw": s, "tokens": {self.token(w) for w in ws}, "neg": self.negation_kinds(ws),
                                "cause": self.has_cause(ws), "numbers": set(self.numbers(s)),
                                "months": self.month_set(ws), "names": self.name_pairs(ws), "describes": section in self.description_sections})
        kept, dropped, seen = [], [], set()
        for sentence in self.split_sentences(text):
            ws = self.words(sentence)
            key = "".join(w + " " for w in ws)
            if key in seen:
                dropped.append(sentence)
                continue
            seen.add(key)
            content = self.content_words(ws)
            if len(content) < max(1, self.min_content):
                dropped.append(sentence)
                continue
            best, best_hits = None, 0
            for src in sources:
                h = sum(c in src["tokens"] for c in content)
                if h > best_hits:
                    best, best_hits = src, h
            need = len(content) if len(content) < self.full_below else self.min_overlap * len(content)
            ok = best is not None and best_hits >= need
            neg = self.negation_kinds(ws)
            if ok and neg:
                ok = bool(neg & best["neg"])                                   # never reverse an instruction
            if ok and self.has_cause(ws):
                ok = best["cause"]                                             # never invent a cause
            if ok and self.is_instruction(ws):
                ok = not best["describes"]                                     # never turn a symptom into advice
            if ok:
                nums = set(self.numbers(sentence))
                ok = nums <= best["numbers"] and (not nums or best["numbers"] <= nums)   # no invented or lost numbers
            if ok:
                months = self.month_set(ws)
                ok = months <= best["months"] and (not months or best["months"] <= months)
            if ok:
                ok = self.name_pairs(ws) <= best["names"]                      # never rename the disease
            (kept if ok else dropped).append(sentence)
        # Sentences written one per line often have no full stop; add one so the joined text reads as sentences
        kept = [s if s[-1] in ".!?;:" else s.rstrip(", ") + "." for s in kept]
        return " ".join(kept), len(kept), dropped
