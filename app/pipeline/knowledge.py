"""Retrieval from the offline advisory database (the "R" of the RAG system).

Two kinds of retrieval:

1. After a diagnosis (retrieve_for_diagnosis): the topic is known from the vision models, so the chunks are selected
   by topic and section in a fixed order (symptoms, spread, field practices, biological control, resistant varieties,
   spray options, safety). This is deterministic: the same diagnosis always gets the same verified extracts.
2. Follow-up questions (search): BM25 full-text search (SQLite FTS5) over the English extracts, optionally boosted
   towards the current topic.

Every chunk returned carries its source (organisation, title, URL), so the user interface can cite it and the
output check can verify that Llama only repeats facts that were retrieved.
"""
import json
import re
import sqlite3
from pathlib import Path

SECTION_ORDER = ["symptoms", "spread", "cultural", "mechanical", "biological", "natural_enemies", "resistant_varieties",
                 "monitoring", "nutrition", "chemical", "safety"]
MAX_PER_SECTION = 3     # extracts shown per section for one diagnosis (same rule as the C++ knowledge_base.cpp)
# Spray options are shown with a per-litre dose first (easiest for a farmer to measure), then per-acre/ha ones
SOURCE_PRIORITY = {"ICAR_LB": 0, "ICAR_IPM": 1, "NIPHM": 2}

# Common words that carry no meaning for retrieval (otherwise "how to stop whitefly" matches on "to")
STOPWORDS = set("""a an and are as at be by can could do does for from how i if in is it its me my of on or our
should so that the their them then there these this to us was we what when where which who why will with you your
use using get""".split())
# Farmer words -> words used in the source documents
SYNONYMS = {"harvest": ["harvest", "waiting"], "spray": ["spray"], "medicine": ["spray"], "dawai": ["spray"],
            "dose": ["spray"], "pesticide": ["pesticide", "spray"], "fungicide": ["spray"], "organic": ["neem",
            "trichoderma", "biological"], "neem": ["neem", "azadirachtin"], "insects": ["insect", "pest"],
            "variety": ["variety", "varieties", "resistant"], "seed": ["seed", "seeds"]}


class KnowledgeBase:
    """Read-only access to app/kb/tomato_kb.sqlite plus the user interface messages from tomato_kb.json."""

    def __init__(self, db_path, json_path):
        self.con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        kb = json.loads(Path(json_path).read_text())
        self.chunks_json = kb["chunks"]         # translations per extract (tools/translate_kb.py); id = index + 1
        self.messages = kb["messages"]
        self.topics = kb["topics"]
        self.sources = {r["id"]: dict(r) for r in self.con.execute("SELECT * FROM sources")}
        self.meta = {r["key"]: json.loads(r["value"]) for r in self.con.execute("SELECT * FROM meta")}
        # Map IP102 species ids to a pest topic (aphids, thrips, mites, caterpillars); others -> insect_other
        self.pest_topic_by_species = {sid: tid for tid, t in self.topics.items() for sid in t.get("species_ids", [])}

    @staticmethod
    def _in_language(entry, lang):
        """Text of a {"en": ..., "<lang>": ...} entry, English where the language is missing."""
        return entry.get(lang) or entry["en"]

    def topic_name(self, topic, lang):
        return self._in_language(self.topics[topic]["name"], lang)

    def message(self, key, lang, **fmt):
        """Fixed, reviewed user interface text (uncertain, quality problems, chemical rule ...)."""
        text = self._in_language(self.messages[key], lang)
        return text.format(**fmt) if fmt else text

    def _row(self, r, lang):
        src = self.sources[r["source"]]
        # Display text in lang from the translations stored with each extract; text_en stays the published English
        # (Llama and the checks use it). Spray products and doses are never translated, only the note.
        j = self.chunks_json[r["id"] - 1]
        note = r["note"]
        if r["section"] == "chemical":
            text = r["text_en"]
            note = (j.get("note_i18n") or {}).get(lang) or note
        else:
            text = (j.get(lang) if lang != "en" else None) or r["text_en"]
        return {"id": r["id"], "topic": r["topic"], "section": r["section"], "text": text, "text_en": r["text_en"],
                "product": r["product"], "dose": r["dose"], "note": note,
                "source_id": r["source"], "source_org": src["org"], "source_title": src["title"], "url": src["url"]}

    def find_chunk(self, topic, phrase, lang="en"):
        """The first extract of a topic whose English text contains `phrase` (quotes one published rule), or None."""
        r = self.con.execute("SELECT * FROM chunks WHERE topic = ? AND instr(text_en, ?) > 0 ORDER BY id LIMIT 1",
                             (topic, phrase)).fetchone()
        return self._row(r, lang) if r else None

    def retrieve_for_diagnosis(self, topic, lang="en", max_sprays=3):
        """Verified extracts for one diagnosed disease or pest, in reading order."""
        rows = [self._row(r, lang) for r in self.con.execute("SELECT * FROM chunks WHERE topic = ?", (topic,))]
        sprays = sorted((c for c in rows if c["section"] == "chemical"),
                        key=lambda c: (SOURCE_PRIORITY.get(c["source_id"], 9), c["id"]))[:max_sprays]
        others = sorted((c for c in rows if c["section"] != "chemical"),
                        key=lambda c: (SECTION_ORDER.index(c["section"]), c["id"]))
        per_section = {}
        kept = []
        for c in others:
            if c["section"] == "safety":
                continue
            per_section[c["section"]] = per_section.get(c["section"], 0) + 1
            if per_section[c["section"]] <= MAX_PER_SECTION:
                kept.append(c)
        chunks = kept + sprays
        if sprays:  # safety rules always follow spray advice
            chunks += [self._row(r, lang) for r in self.con.execute(
                "SELECT * FROM chunks WHERE topic = 'general' AND section = 'safety' ORDER BY id")]
        return chunks

    def search(self, question, topic=None, k=4, lang="en"):
        """BM25 search for a follow-up question. Chunks of the current topic get a ranking bonus."""
        words = [w for w in re.findall(r"[A-Za-z0-9]+", question.lower()) if w not in STOPWORDS]
        terms = sorted({t for w in words for t in SYNONYMS.get(w, [w])})
        if not terms:
            return []
        query = " OR ".join(f'"{t}"' for t in terms)
        rows = self.con.execute(
            "SELECT c.*, bm25(chunks_fts) AS score FROM chunks_fts JOIN chunks c ON c.id = chunks_fts.rowid "
            "WHERE chunks_fts MATCH ? ORDER BY score LIMIT 30", (query,)).fetchall()
        # bm25() is lower = better; subtract a fixed bonus for the topic being discussed
        ranked = sorted(rows, key=lambda r: r["score"] - (2.0 if topic and r["topic"] == topic else 0.0))
        return [self._row(r, lang) for r in ranked[:k]]

    def pest_topic(self, species_id, species_reliable):
        """Knowledge-base topic for a detected insect; unreliable species names fall back to insect_other."""
        if not species_reliable:
            return "insect_other"
        return self.pest_topic_by_species.get(species_id, "insect_other")
