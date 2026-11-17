"""Build the offline advisory database (SQLite + FTS5 full-text index) from app/kb/tomato_kb.json.

The JSON file is the reviewed source of truth: every chunk is an extract from an ICAR, NIPHM or TNAU publication,
with the source recorded. This script only restructures it for fast lookup on the device:

    chunks      one row per extract (topic, section, source, English and Hindi text, product and dose for sprays)
    chunks_fts  FTS5 index over the English text, product names and topic names, used to answer follow-up
                questions with BM25 ranking (no neural embedding model needed, so it runs on the Pi CPU in ~1 ms)
    sources     the publications (organisation, title, URL)
    meta        version, review status, access date

Usage:  python -m app.kb.build_kb            (writes app/kb/tomato_kb.sqlite)
"""
import json
import sqlite3
from pathlib import Path

KB_DIR = Path(__file__).resolve().parent
SRC = KB_DIR / "tomato_kb.json"
DB = KB_DIR / "tomato_kb.sqlite"

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE sources (id TEXT PRIMARY KEY, org TEXT, title TEXT, url TEXT);
CREATE TABLE topics (id TEXT PRIMARY KEY, kind TEXT, name_en TEXT, name_hi TEXT, info_json TEXT);
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    topic TEXT REFERENCES topics(id),
    section TEXT,              -- symptoms, spread, cultural, biological, resistant_varieties, chemical, safety
    source TEXT REFERENCES sources(id),
    text_en TEXT, text_hi TEXT,
    product TEXT, dose TEXT, note TEXT   -- filled only for section = chemical
);
CREATE VIRTUAL TABLE chunks_fts USING fts5(text, topic_name, content='', tokenize='porter unicode61');
"""


def chunk_text(chunk):
    """English text of a chunk; for a spray option the product, dose and note form the text."""
    if chunk["section"] == "chemical":
        return f"Spray {chunk['product']} @ {chunk['dose']}. {chunk.get('note', '')}".strip()
    return chunk["en"]


def build(src=SRC, db=DB):
    """Create the SQLite file from the JSON knowledge base; returns the number of chunks."""
    kb = json.loads(Path(src).read_text())
    for chunk in kb["chunks"]:
        if chunk["topic"] not in kb["topics"] or chunk["source"] not in kb["sources"]:
            raise ValueError(f"unknown topic or source in chunk: {chunk}")
    db = Path(db)
    db.unlink(missing_ok=True)
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    for key in ("version", "accessed", "content_reviewed", "hindi_reviewed", "built_from"):
        con.execute("INSERT INTO meta VALUES (?, ?)", (key, json.dumps(kb[key])))
    for sid, s in kb["sources"].items():
        con.execute("INSERT INTO sources VALUES (?, ?, ?, ?)", (sid, s["org"], s["title"], s["url"]))
    for tid, t in kb["topics"].items():
        con.execute("INSERT INTO topics VALUES (?, ?, ?, ?, ?)",
                    (tid, t["kind"], t["name"]["en"], t["name"]["hi"], json.dumps(t)))
    for i, c in enumerate(kb["chunks"], start=1):
        text = chunk_text(c)
        con.execute("INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (i, c["topic"], c["section"], c["source"], text, c.get("hi"),
                     c.get("product"), c.get("dose"), c.get("note")))
        con.execute("INSERT INTO chunks_fts (rowid, text, topic_name) VALUES (?, ?, ?)",
                    (i, text, kb["topics"][c["topic"]]["name"]["en"]))
    con.commit()
    con.close()
    return len(kb["chunks"])


if __name__ == "__main__":
    n = build()
    print(f"wrote {DB} ({n} chunks)")
