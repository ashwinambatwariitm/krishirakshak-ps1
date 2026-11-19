"""Merge new verified extracts (ICAR, NIPHM, TNAU) into the advisory knowledge base app/kb/tomato_kb.json.

Inputs:
    app/kb/extracts/niphm_candidates.json       extracts from the NIPHM AESA-based IPM package for tomato
    app/kb/extracts/tnau_icar_candidates.json   extracts from TNAU Agritech pages, the TNAU vegetable IPM schedule
                                                and the ICAR Indian Horticulture articles
    app/kb/extracts/pesticide_regulation.json   pesticides banned / restricted in India, with the reference used
Each candidate extract was copied from its source with only line-break, spacing and hyphenation clean-up; each one
records a locator (section / page). The checks used before merging are described in docs/KNOWLEDGE_BASE.md.

Rules applied here:
- extracts that name a pesticide banned in India are dropped (spray rows and advice text alike);
- spray rows of restricted pesticides are kept with a note "Restricted use in India ..." appended;
- extracts listed in EXCLUDE (doubtful doses found in review) are dropped;
- exact duplicates (same topic, section and text) are dropped;
- the existing extracts keep their order and come first, so earlier behaviour (Llama prompt facts, tests) is unchanged.

Usage:  python3 tools/kb_merge_extracts.py            (rewrites app/kb/tomato_kb.json, prints a summary)
"""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KB = REPO / "app" / "kb" / "tomato_kb.json"
EXTRACTS = REPO / "app" / "kb" / "extracts"

# Found in review: the source prints 0.03 ml/l here, but 0.3 ml/l for the same product everywhere else in the same
# document, so the dose is not trusted.
EXCLUDE = [
    {"source": "TNAU_IPM_VEG", "product": "Imidacloprid 200 SL", "dose": "0.03ml/l"},
]


def norm(s):
    return re.sub(r"\s+", " ", s.strip().lower())


def names_in(text, names):
    """Pesticide names (from a list) that occur as words in text."""
    low = text.lower()
    return [n for n in names if re.search(r"(?<![a-z])" + re.escape(n.lower()) + r"(?![a-z])", low)]


def main():
    kb = json.loads(KB.read_text())
    reg = json.loads((EXTRACTS / "pesticide_regulation.json").read_text())
    banned = reg["banned"]
    restricted = reg["restricted"]

    existing = {(c["topic"], c["section"], norm(c.get("en") or c.get("product", "") + c.get("dose", "")))
                for c in kb["chunks"]}
    report = {"added": 0, "dropped_banned": [], "dropped_excluded": 0, "dropped_duplicate": 0, "restricted_noted": 0}

    for fname in ("tnau_icar_candidates.json", "niphm_candidates.json"):
        cand = json.loads((EXTRACTS / fname).read_text())
        # Sources: the NIPHM file reuses the existing NIPHM id; the TNAU/ICAR file brings new ids
        for sid, s in cand.get("sources", {}).items():
            kb["sources"].setdefault(sid, {"org": s["org"], "title": s["title"], "url": s["url"]})
        for tid, t in cand.get("new_topics", {}).items():
            if tid not in kb["topics"]:
                kb["topics"][tid] = {"name": {"en": t["name_en"], "hi": t["name_en"]}, "kind": t["kind"],
                                     "hindi_name_missing": True}
        for c in cand["chunks"]:
            if c["source"] not in kb["sources"]:
                raise SystemExit(f"unknown source {c['source']} in {fname}")
            if c["topic"] not in kb["topics"]:
                raise SystemExit(f"unknown topic {c['topic']} in {fname}")
            text = " ".join(str(c.get(k, "")) for k in ("en", "product", "dose", "note"))
            hit = names_in(text, banned)
            if hit:
                report["dropped_banned"].append(f"{c['topic']}/{c['section']}: {', '.join(hit)}")
                continue
            if any(all(c.get(k) == v for k, v in ex.items()) for ex in EXCLUDE):
                report["dropped_excluded"] += 1
                continue
            key = (c["topic"], c["section"], norm(c.get("en") or c.get("product", "") + c.get("dose", "")))
            if key in existing:
                report["dropped_duplicate"] += 1
                continue
            existing.add(key)
            out = {k: c[k] for k in ("topic", "section", "source") if k in c}
            if c["section"] == "chemical":
                out.update(product=c["product"], dose=c["dose"], note=c.get("note", ""))
            else:
                out["en"] = c["en"]
            out["locator"] = c.get("locator", "")
            kb["chunks"].append(out)
            report["added"] += 1

    # The restricted-use note applies to every spray row, including the extracts that were already in the base
    # (idempotent: a row that already carries the note is left alone)
    for c in kb["chunks"]:
        if c["section"] == "chemical" and names_in(c["product"], restricted) and reg["restricted_note"] not in c.get("note", ""):
            c["note"] = (c.get("note", "") + " " if c.get("note") else "") + reg["restricted_note"]
            report["restricted_noted"] += 1

    kb["version"] = "tomato_kb_v3"
    kb["pesticide_regulation"] = {"reference": reg["reference"], "checked": reg["checked"]}
    KB.write_text(json.dumps(kb, ensure_ascii=True, indent=1) + "\n")
    print(f"extracts now {len(kb['chunks'])}, topics {len(kb['topics'])}, sources {len(kb['sources'])}")
    print(f"added {report['added']}, duplicates dropped {report['dropped_duplicate']}, "
          f"doubtful doses dropped {report['dropped_excluded']}, restricted noted {report['restricted_noted']}")
    print(f"dropped because a banned pesticide is named: {len(report['dropped_banned'])}")
    for line in report["dropped_banned"]:
        print("   ", line)


if __name__ == "__main__":
    main()
