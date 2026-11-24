"""End-to-end app test: every test photo in every language through the farmer app in a phone-size headless Chromium,
against the running Pi. Writes one JSON line per run to OUT_DIR/results.jsonl and a screenshot per run to
OUT_DIR/<lang>/<photo>.png. A run can be resumed: finished runs are skipped. Needs the playwright Python package.

    python3 tools/e2e/ui_full.py OUT_DIR PHOTOS_DIR [http://<pi-address>:8080/]
"""
import glob, json, os, sys, time
from playwright.sync_api import sync_playwright
OUT, T = sys.argv[1], sys.argv[2]
URL = sys.argv[3] if len(sys.argv) > 3 else "http://10.42.0.1:8080/"
LANGS = ["en", "hi", "mr", "te", "kn", "ta", "bn", "gu", "or", "pa"]
SAMPLE = {"en": "A", "hi": "\u0915", "mr": "\u0915", "te": "\u0c15", "kn": "\u0c95", "ta": "\u0b95", "bn": "\u0995", "gu": "\u0a95", "or": "\u0b15", "pa": "\u0a15"}
photos = sorted(glob.glob(f"{T}/*/*.jpg"))
done = set()
res_path = f"{OUT}/results.jsonl"
if os.path.exists(res_path):
    for l in open(res_path): r = json.loads(l); done.add((r["lang"], r["photo"]))
CHECK = """(lang) => {
  const d = window.appState.analysisResult || {};
  const vis = (id) => { const e = document.getElementById(id); return !!(e && e.offsetParent !== null && !e.classList.contains('hidden')); };
  const view = window.appState.currentView;
  const title = view === 'result' ? document.getElementById('res-disease-name').textContent.trim()
              : (document.querySelector('#view-' + view + ' h2') || {}).textContent || '';
  const chem = (d.advice_blocks || []).flatMap(b => (b.chunks || []).filter(c => c.section === 'chemical')).length;
  return {
    status: d.status || null, view, title: title.trim(),
    llama_expected: !!(d.llama && d.llama.text && d.llama.accepted !== false),
    llama_shown: vis('res-llama-card'), llama_items: document.querySelectorAll('#res-llama-list li').length,
    metrics: document.querySelectorAll('#res-metrics .metric').length, disease_answered: !!(d.disease && d.disease.answered),
    pests: (d.pests || []).length, spray_rows: document.querySelectorAll('#res-spray-list .spray-row').length, spray_expected: chem,
    advice_cards: document.querySelectorAll('#res-advice-blocks .advice-card').length,
    alerts_danger: document.querySelectorAll('#res-messages-container .kr-alert.danger').length, refer: !!d.refer_to_expert,
    overflow: document.documentElement.scrollWidth > window.innerWidth + 1,
    tips_outside_home: !!document.querySelector('.tips-card') && document.querySelector('.tips-card').offsetParent !== null && view !== 'home',
  };
}"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for lang in LANGS:
        ctx = b.new_context(viewport={"width": 412, "height": 915}); pg = ctx.new_page()
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        pg.goto(URL, wait_until="networkidle"); pg.select_option("#select-translate", "" if lang == "en" else lang)
        os.makedirs(f"{OUT}/{lang}", exist_ok=True)
        for f in photos:
            name = os.path.basename(os.path.dirname(f)) + "__" + os.path.basename(f)[:-4]
            if (lang, name) in done: continue
            errs.clear(); t0 = time.time(); row = {"lang": lang, "photo": name}
            try:
                pg.goto(URL, wait_until="networkidle")
                pg.query_selector("#gallery-input").set_input_files(f)
                pg.wait_for_selector("#view-crop:not(.hidden)", timeout=15000); pg.click("#btn-crop-whole")
                pg.wait_for_selector("#view-result:not(.hidden), #view-retake:not(.hidden), #view-uncertain:not(.hidden)", timeout=240000)
                pg.wait_for_timeout(700)
                row.update(pg.evaluate(CHECK, lang))
                row["font_ok"] = pg.evaluate(f"document.fonts.check('16px \"KR Sans\"', '{SAMPLE[lang]}')")
                pg.screenshot(path=f"{OUT}/{lang}/{name}.png")
            except Exception as e:
                row["error"] = str(e)[:300]
            row["js_errors"] = list(errs); row["seconds"] = round(time.time() - t0, 1)
            with open(res_path, "a") as fh: fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        ctx.close()
    b.close()
print("done")
