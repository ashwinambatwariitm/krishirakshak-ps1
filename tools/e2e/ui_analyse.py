"""Checks of an app run (ui_full.py) against the API run of the same photos: screen per status, title, Llama card
shown exactly when Llama's text was accepted, measured values, spray rows, red alert for severe cases, no overflow, app
font loaded, no JavaScript errors.

    python3 tools/e2e/ui_analyse.py RUN_DIR/app/results.jsonl RUN_DIR/api
"""
import json, sys, collections
RESULTS, API = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(RESULTS)]
api = {}
for r in rows:
    try: api[(r["lang"], r["photo"])] = json.load(open(f"{API}/{r['lang']}/{r['photo']}.json"))
    except Exception: pass
VIEW = {"answered": "result", "retake_photo": "retake", "not_tomato": "retake", "uncertain": "uncertain"}
problems = collections.defaultdict(list)
for r in rows:
    k = f"{r['lang']}/{r['photo']}"
    if "error" in r: problems["run error"].append(f"{k}: {r['error'][:120]}"); continue
    a = api.get((r["lang"], r["photo"]))
    if a and a.get("status") != r["status"]: problems["status differs from API run"].append(f"{k}: api {a.get('status')} app {r['status']}")
    if VIEW.get(r["status"]) != r["view"]: problems["wrong screen"].append(f"{k}: {r['status']} -> {r['view']}")
    if not r["title"]: problems["empty title"].append(k)
    if r["llama_expected"] != r["llama_shown"]: problems["Llama card shown != accepted"].append(k)
    if r["llama_shown"] and r["llama_items"] == 0: problems["Llama card without sentences"].append(k)
    if r["status"] == "answered" and r["disease_answered"] and r["metrics"] < 1: problems["no measured values"].append(k)
    if r["status"] == "answered" and r["spray_rows"] != r["spray_expected"]: problems["spray rows missing"].append(f"{k}: {r['spray_rows']}/{r['spray_expected']}")
    if r["refer"] and r["alerts_danger"] < 1: problems["severe case without red alert"].append(k)
    if r["overflow"]: problems["wider than the screen"].append(k)
    if r["tips_outside_home"]: problems["tips card on a result screen"].append(k)
    if not r.get("font_ok"): problems["app font not loaded"].append(k)
    if r["js_errors"]: problems["JS errors"].append(f"{k}: {r['js_errors'][:2]}")
by_lang = collections.Counter(r["lang"] for r in rows)
print(f"runs: {len(rows)}  per language: {dict(by_lang)}")
print("status:", dict(collections.Counter(r.get("status") for r in rows)))
print("Llama card shown:", sum(r.get("llama_shown", False) for r in rows), "| expected:", sum(r.get("llama_expected", False) for r in rows))
print("median seconds:", sorted(r["seconds"] for r in rows)[len(rows)//2])
if not problems: print("PROBLEMS: none")
for name, items in problems.items():
    print(f"PROBLEM {name}: {len(items)}"); [print("   ", i) for i in items[:8]]
