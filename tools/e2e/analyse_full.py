"""Checks of an end-to-end API run (output of full_test.py).

For every photo: the expected kind of result per photo group, the same status, diagnosis and Llama text in every
language, a translation for every accepted Llama answer (no flagged, repeated or truncated sentence, the right script,
no number lost), names and messages in the chosen script, no leftover placeholder codes. Prints the Llama result per
photo and every issue found.

    python3 tools/e2e/analyse_full.py RUN_DIR/api
"""
import json, glob, os, re, sys, collections
D = sys.argv[1]
LANGS = ["en", "hi", "mr", "te", "kn", "ta", "bn", "gu", "or", "pa"]
SCRIPT = {"hi": (0x0900, 0x097F), "mr": (0x0900, 0x097F), "bn": (0x0980, 0x09FF), "pa": (0x0A00, 0x0A7F), "gu": (0x0A80, 0x0AFF),
          "or": (0x0B00, 0x0B7F), "ta": (0x0B80, 0x0BFF), "te": (0x0C00, 0x0C7F), "kn": (0x0C80, 0x0CFF)}
DIG = {chr(b + i): str(i) for b in (0x0966, 0x09E6, 0x0A66, 0x0AE6, 0x0B66, 0x0BE6, 0x0C66, 0x0CE6) for i in range(10)}
nums = lambda t: collections.Counter(re.findall(r"\d+(?:\.\d+)?", "".join(DIG.get(c, c) for c in t or "")))
def script_share(t, l):
    lo, hi = SCRIPT[l]; letters = [c for c in t if c.isalpha()]
    return sum(lo <= ord(c) <= hi for c in letters) / max(1, len(letters))
code = re.compile(r"<[^<>]{0,30}?\d\s*[>\]]")
EXPECT_DISEASE = {"Tomato_Early_blight_leaf": "early_blight", "Tomato_Septoria_leaf_spot": "septoria_leaf_spot", "Tomato_leaf": "healthy",
                  "Tomato_leaf_late_blight": "late_blight", "Tomato_leaf_yellow_virus": "yellow_leaf_curl_virus"}
GROUP = {"black_cutworm": "caterpillar", "army_worm": "caterpillar", "cabbage_army_worm": "caterpillar", "red_spider": "mite", "aphids": "aphid", "odontothrips_loti": "thrips"}
issues = collections.defaultdict(list); llama_rows = []
photos = sorted(os.path.basename(f)[:-5] for f in glob.glob(f"{D}/en/*.json"))
for ph in photos:
    folder, name = ph.split("__")
    R = {l: json.load(open(f"{D}/{l}/{ph}.json")) for l in LANGS if os.path.exists(f"{D}/{l}/{ph}.json")}
    if len(R) != 10: issues[ph].append(f"only {len(R)} languages"); continue
    en = R["en"]
    if "error" in en: issues[ph].append("request error " + en["error"]); continue
    st, topic = en.get("status"), (en.get("disease") or {}).get("topic")
    groups = sorted({p["species"] for p in en.get("pests", [])})
    # expected result per folder
    if folder == "1_tomato_disease" and topic != EXPECT_DISEASE.get(name): issues[ph].append(f"disease {topic} != {EXPECT_DISEASE.get(name)}")
    if folder == "3_insects":
        key = re.sub(r"^IP\d+_", "", name)
        if st != "retake_photo" and GROUP[key] not in groups: issues[ph].append(f"pest groups {groups}, expected {GROUP[key]}")
        if topic: issues[ph].append(f"disease named on insect photo: {topic}")
    if folder == "4_not_tomato" and topic: issues[ph].append(f"disease on non-tomato photo: {topic}")
    if folder == "5_chilli_field_pests" and topic: issues[ph].append(f"disease on chilli photo: {topic}")
    # every language: same status / topic / Llama text, translation complete
    L = en.get("llama") or {}
    llama_en = L.get("text"); llama_rows.append((ph, st, topic, groups, bool(llama_en), (L.get("rejected_reasons") or []), en["_seconds"]))
    for l in LANGS[1:]:
        r = R[l]
        if "error" in r: issues[ph].append(f"{l}: request error"); continue
        if r.get("status") != st or (r.get("disease") or {}).get("topic") != topic: issues[ph].append(f"{l}: different result {r.get('status')} {(r.get('disease') or {}).get('topic')}")
        rl = (r.get("llama") or {}).get("text")
        if rl != llama_en: issues[ph].append(f"{l}: Llama text differs from English run")
        if r.get("display_lang") != l and st not in ("retake_photo",): issues[ph].append(f"{l}: display_lang {r.get('display_lang')}")
        if llama_en:
            tr = r.get("translation") or {}
            sents = tr.get("sentences") or []
            if not sents: issues[ph].append(f"{l}: Llama accepted but no translation"); continue
            ttxt = " ".join(s.get("text", "") for s in sents)
            if not all(s.get("ok", True) for s in sents): issues[ph].append(f"{l}: translator flagged {sum(not s.get('ok', True) for s in sents)} sentence(s)")
            if any(s.get("repetition") for s in sents): issues[ph].append(f"{l}: repetition in translation")
            if code.search(ttxt): issues[ph].append(f"{l}: leftover code in translation")
            if script_share(ttxt, l) < 0.6: issues[ph].append(f"{l}: translation script share {script_share(ttxt, l):.2f}")
            miss = [n for n, c in nums(llama_en).items() if nums(ttxt)[n] < c]
            if miss: issues[ph].append(f"{l}: numbers missing in translation {miss}")
        # names and messages in the language
        name_l = (r.get("disease") or {}).get("name") or ""
        if name_l and script_share(name_l, l) < 0.3: issues[ph].append(f"{l}: disease name not in script: {name_l}")
        for p in r.get("pests", []):
            if script_share(re.sub(r"\([A-Za-z ,/()-]*\)$", "", p.get("name", "")), l) < 0.5: issues[ph].append(f"{l}: pest name not in script"); break
        for m in r.get("messages", []):
            if code.search(m): issues[ph].append(f"{l}: code in message")
            if script_share(m, l) < 0.5: issues[ph].append(f"{l}: message not in script: {m[:50]}")
        for b in r.get("advice_blocks", []):
            for c in b.get("chunks", []):
                if code.search(c.get("text", "") + c.get("note", "")): issues[ph].append(f"{l}: code in extract")
print("photos:", len(photos), "| results:", sum(len(glob.glob(f'{D}/{l}/*.json')) for l in LANGS))
print("\nLlama per photo (English run):")
for ph, st, topic, groups, acc, why, sec in llama_rows:
    print(f"  {ph[:44]:45} {st:12} {str(topic):22} {','.join(groups):18} llama={'OK' if acc else '-'} {','.join(why)[:40]} {sec}s")
print("\nissues:", sum(len(v) for v in issues.values()), "in", len(issues), "photos")
for ph, v in issues.items():
    c = collections.Counter(re.sub(r"^(\w\w): ", "", x) for x in v)
    print(" ", ph[:50], "->", "; ".join(f"{k}" + (f" (x{n})" if n > 1 else "") for k, n in c.items())[:300])
