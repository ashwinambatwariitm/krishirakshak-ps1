"""Python copy of the sentence-level grounding check of the C++ application (cpp/src/output_guard.cpp,
keepGroundedSentences), used to build and score the LoRA training data on Kaggle without the C++ build.

The word lists (stop words, negations, same-meaning groups) and the threshold are read from the file written by
    build/x86/grounding_test . --dump-facts results/llama_lora/prompt_facts.json
so both implementations always use the same lists. tools/check_grounding_port.py compares this module with the C++
check on saved Llama answers; the two must give the same decisions.

A sentence of the Llama answer is kept only if
  - at least min_overlap of its content words (4+ letters, not stop words, stemmed, same-meaning words merged) occur
    in ONE sentence of the retrieved extracts,
  - a negated sentence ("do not ...") is supported by a negated source sentence (an instruction is never reversed),
  - a sentence stating a cause ("caused by", "due to") is supported by a source sentence stating one,
  - every number in it appears in that source sentence,
  - it is not a repeat of an earlier sentence.
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

    def has_cause(self, ws):
        return any(self.stem(w) in self.cause_stems for w in ws)

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

    def keep_grounded(self, text, fact_texts):
        """Returns (kept text, number of kept sentences, dropped sentences), like keepGroundedSentences()."""
        sources = []
        for fact in fact_texts:
            for s in self.split_sentences(fact):
                ws = self.words(s)
                sources.append((s, {self.token(w) for w in ws}, self.has_negation(ws), self.has_cause(ws)))
        kept, dropped, seen = [], [], set()
        for sentence in self.split_sentences(text):
            ws = self.words(sentence)
            key = "".join(w + " " for w in ws)
            if key in seen:
                dropped.append(sentence)
                continue
            seen.add(key)
            content = []
            for w in ws:
                s = self.token(w)
                if len(w) >= self.min_len and w not in self.stop and s not in self.stop and w not in self.negations:
                    content.append(s)
            if not content:
                dropped.append(sentence)
                continue
            best, best_hits = None, 0
            for src in sources:
                h = sum(c in src[1] for c in content)
                if h > best_hits:
                    best, best_hits = src, h
            ok = best is not None and best_hits / len(content) >= self.min_overlap
            if ok and self.has_negation(ws):
                ok = best[2]
            if ok and self.has_cause(ws):
                ok = best[3]
            if ok and any(n not in best[0] for n in self.numbers(sentence)):
                ok = False
            (kept if ok else dropped).append(sentence)
        return " ".join(kept), len(kept), dropped
