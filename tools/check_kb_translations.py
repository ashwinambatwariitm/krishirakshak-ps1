"""Check translation coverage and preservation of the original tomato knowledge base.

Usage: python tools/check_kb_translations.py --original /tmp/kb_orig.json \
    --new app/kb/tomato_kb.json
Indices in diagnostics are zero based. Uses only the Python standard library.
"""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
import unicodedata


LANGUAGES = ("hi", "te", "mr", "kn", "ta", "bn", "gu", "or", "pa")
SCRIPTS = dict(zip(LANGUAGES, (
    (0x0900, 0x097F), (0x0C00, 0x0C7F), (0x0900, 0x097F),
    (0x0C80, 0x0CFF), (0x0B80, 0x0BFF), (0x0980, 0x09FF),
    (0x0A80, 0x0AFF), (0x0B00, 0x0B7F), (0x0A00, 0x0A7F),
)))
SECTION_LABELS = {
    "monitoring": "Monitoring", "nutrition": "Nutrition",
    "natural_enemies": "Natural enemies", "mechanical": "Mechanical control",
}
REVIEW_SENTENCE = (
    "The regional language texts are machine translations that must be reviewed "
    "by fluent speakers."
)
PLACEHOLDERS = re.compile(r"\{[^{}]+\}")
NUMBERS = re.compile(r"[0-9]+(?:\.[0-9]+)?")


def text_objects(value, path):
    """Yield all message objects, including arbitrarily nested ones."""
    if isinstance(value, dict):
        if "en" in value:
            yield path, value
        for key, child in value.items():
            yield from text_objects(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from text_objects(child, f"{path}[{index}]")


def check(original, new):
    problems = []

    def preserve(old, current, path="root"):
        # Comparing every original field also protects identifiers, ordering,
        # regulatory data, existing Hindi, and fields added in future versions.
        if type(old) is not type(current):
            problems.append(f"{path}: type changed")
        elif isinstance(old, dict):
            retained = [key for key in current if key in old]
            if retained != list(old):
                problems.append(f"{path}: original keys removed or reordered")
            for key, value in old.items():
                if key not in current:
                    problems.append(f"{path}.{key}: original field missing")
                elif path == "root" and key == "built_from":
                    if current[key] != value + " " + REVIEW_SENTENCE:
                        problems.append("root.built_from: must append only the review sentence")
                else:
                    preserve(value, current[key], f"{path}.{key}")
            for key in current.keys() - old.keys():
                allowed = (
                    ("en" in old and key in LANGUAGES)
                    or (path == "root" and key in {f"{l}_reviewed" for l in LANGUAGES[1:]})
                    or (path == "root.messages.sections" and key in SECTION_LABELS)
                    or (path.startswith("root.chunks[") and old.get("section") == "chemical"
                        and "note" in old and key == "note_i18n")
                )
                if not allowed:
                    problems.append(f"{path}.{key}: unexpected new field")
        elif isinstance(old, list):
            if len(old) != len(current):
                problems.append(f"{path}: length changed ({len(old)} -> {len(current)})")
            for index, (before, after) in enumerate(zip(old, current)):
                preserve(before, after, f"{path}[{index}]")
        elif old != current:
            problems.append(f"{path}: original value changed")

    preserve(original, new)
    for lang in LANGUAGES[1:]:
        if new.get(f"{lang}_reviewed") is not False:
            problems.append(f"root.{lang}_reviewed: must be false")

    chunks = new.get("chunks", [])
    topics = new.get("topics", {})
    messages = new.get("messages", {})
    if not isinstance(chunks, list):
        problems.append("chunks: expected a list")
        chunks = []
    if not isinstance(topics, dict):
        problems.append("topics: expected an object")
        topics = {}
    if not isinstance(messages, dict):
        problems.append("messages: expected an object")
        messages = {}

    groups = {
        "chunks": [(f"chunks[{i}]", c) for i, c in enumerate(chunks)
                   if isinstance(c, dict) and "en" in c],
        "topic names": [(f"topics.{key}.name", topic.get("name", {}))
                        for key, topic in topics.items() if isinstance(topic, dict)],
        "messages": list(text_objects(messages, "messages")),
    }
    sections = messages.get("sections", {})
    if not isinstance(sections, dict):
        sections = {}
    for key, english in SECTION_LABELS.items():
        label = sections.get(key)
        if not isinstance(label, dict) or label.get("en") != english:
            problems.append(f"messages.sections.{key}: missing or incorrect English label")

    def validate(path, obj, source=None):
        if not isinstance(obj, dict):
            problems.append(f"{path}: expected a translation object")
            return
        source = obj.get("en") if source is None else source
        if not isinstance(source, str):
            problems.append(f"{path}: missing string source")
            return
        actual_order = [key for key in obj if key in LANGUAGES]
        if actual_order != list(LANGUAGES):
            problems.append(f"{path}: language keys must occur in order {', '.join(LANGUAGES)}")
        for lang in LANGUAGES:
            target = obj.get(lang)
            loc = f"{path}.{lang}"
            # An empty original chemical note contains nothing to translate.
            if path.endswith(".note_i18n") and source == "" and target == "":
                continue
            if not isinstance(target, str) or not target.strip():
                problems.append(f"{loc}: missing or empty translation")
                continue
            expected = Counter(PLACEHOLDERS.findall(source))
            actual = Counter(PLACEHOLDERS.findall(target))
            if expected != actual:
                problems.append(f"{loc}: placeholders differ: {dict(expected)} -> {dict(actual)}")
            missing = Counter(NUMBERS.findall(source)) - Counter(NUMBERS.findall(target))
            if missing:
                problems.append(f"{loc}: missing numbers {dict(missing)}")
            if any(ch.isdecimal() and ch not in "0123456789" for ch in target):
                problems.append(f"{loc}: contains non-Western digits")
            low, high = SCRIPTS[lang]
            if not any(low <= ord(ch) <= high and unicodedata.category(ch).startswith("L")
                       for ch in target):
                problems.append(f"{loc}: no letters in the expected script")

    for entries in groups.values():
        for path, obj in entries:
            validate(path, obj)
    notes = 0
    for i, chunk in enumerate(chunks):
        if isinstance(chunk, dict) and chunk.get("section") == "chemical" and "note" in chunk:
            notes += 1
            validate(f"chunks[{i}].note_i18n", chunk.get("note_i18n"), chunk["note"])

    print("Language | Chunks | Topic names | Messages")
    print("---------|--------|-------------|---------")
    for lang in LANGUAGES:
        cells = []
        for entries in groups.values():
            filled = sum(isinstance(obj, dict) and isinstance(obj.get(lang), str)
                         and bool(obj[lang].strip()) for _, obj in entries)
            cells.append(f"{filled}/{len(entries)}")
        print(f"{lang:8} | " + " | ".join(cells))
    print(f"Chemical notes checked: {notes}")
    for problem in problems:
        print(f"ERROR: {problem}")
    print(f"{len(problems)} problems")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    args = parser.parse_args()
    try:
        original = json.loads(args.original.read_text(encoding="utf-8"))
        new = json.loads(args.new.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1
    if not isinstance(original, dict) or not isinstance(new, dict):
        print("ERROR: both JSON roots must be objects")
        return 1
    return int(bool(check(original, new)))


if __name__ == "__main__":
    sys.exit(main())
