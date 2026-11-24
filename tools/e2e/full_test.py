"""End-to-end API test, run on the Raspberry Pi next to the running service (http://127.0.0.1:8080).

Every test photo in every language through /api/analyse, with Llama and translation on. Writes one JSON per photo and
language to OUT/<lang>/<folder>__<photo>.json and a progress log. A run can be resumed: finished answers are skipped.

    python3 tools/e2e/full_test.py PHOTOS_DIR OUT_DIR      # PHOTOS_DIR/<group>/<photo>.jpg
"""
import glob, json, os, sys, time, urllib.request
PHOTOS, OUT = sys.argv[1], sys.argv[2]
LANGS = ["en", "hi", "mr", "te", "kn", "ta", "bn", "gu", "or", "pa"]
photos = sorted(glob.glob(f"{PHOTOS}/*/*.jpg"))
t0 = time.time(); n = 0
for f in photos:
    for l in LANGS:
        d = f"{OUT}/{l}"; os.makedirs(d, exist_ok=True)
        out = f"{d}/{os.path.basename(os.path.dirname(f))}__{os.path.basename(f)[:-4]}.json"
        if os.path.exists(out): continue
        q = "lang=en" + ("" if l == "en" else f"&translate={l}")
        req = urllib.request.Request(f"http://127.0.0.1:8080/api/analyse?{q}", data=open(f, "rb").read(), method="POST")
        s = time.time()
        try:
            res = json.loads(urllib.request.urlopen(req, timeout=300).read())
        except Exception as e:
            res = {"error": str(e)}
        res["_seconds"] = round(time.time() - s, 2)
        json.dump(res, open(out, "w"), ensure_ascii=False)
        n += 1
        with open(f"{OUT}/progress.log", "a") as p:
            p.write(f"{time.strftime('%H:%M:%S')} {n}/{len(photos)*len(LANGS)} {l} {os.path.basename(f)} {res.get('status')} {res['_seconds']}s\n")
print(f"done {n} in {(time.time()-t0)/60:.1f} min")
