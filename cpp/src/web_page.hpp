/*
 * web_page.hpp - the farmer web page, compiled into the binary (no external files, fonts or scripts, so it works
 * with no internet). The page sends the photo to POST /api/analyse and renders the JSON result:
 * diagnosis, notes, Llama explanation, verified extracts with their source, spray table as published, follow-up
 * question box, and a technical panel with timings.
 */
#pragma once

#include <string>

namespace web {

inline std::string farmerPageHtml() {
    return R"HTML(<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>KrishiRakshak</title>
<style>
:root{--bg:#f6f7f2;--card:#fff;--ink:#1d2a1d;--muted:#5d6b5d;--accent:#2f6b2f;--warn:#9a5b00;--bad:#a12a2a;--line:#dfe5da}
body{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--ink)}
header{background:var(--accent);color:#fff;padding:12px 16px}header h1{margin:0;font-size:1.3rem}
header p{margin:2px 0 0;font-size:.85rem;opacity:.9}
main{max-width:860px;margin:0 auto;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin-bottom:14px}
button{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:10px 18px;font-size:1rem}
.row{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-start}
.thumb{max-width:220px;border-radius:8px}.diag{font-size:1.4rem;font-weight:700}
.urgent{color:var(--bad);font-weight:700}.note{border-left:4px solid var(--warn);padding:6px 10px;background:#fff8ec;margin:8px 0}
.llama{border-left:4px solid var(--accent);padding:8px 12px;background:#f0f7ef}
table{border-collapse:collapse;width:100%;font-size:.92rem}th,td{text-align:left;border-bottom:1px solid var(--line);padding:6px;vertical-align:top}
.src,.muted{color:var(--muted);font-size:.82rem}details summary{cursor:pointer;color:var(--muted)}
</style></head><body>
<header><h1>KrishiRakshak</h1><p>Offline tomato disease and pest advisor - runs fully on this device (C++ on Arm)</p></header>
<main>
<div class="card"><div class="row">
 <div><b>Leaf photo</b><br><input id="photo" type="file" accept="image/*" capture="environment"></div>
 <div><b>Language</b><br><select id="lang"><option value="en">English</option>
   <option value="hi">&#2361;&#2367;&#2306;&#2342;&#2368; (Hindi)</option></select></div>
 <div><br><button onclick="analyse()">Check plant</button></div></div></div>
<div id="out"></div>
<p class="muted" id="foot"></p>
</main>
<script>
let lastTopic = null;
const el = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text !== undefined) e.textContent = text; return e; };
fetch('/api/info').then(r => r.json()).then(i => {
  document.getElementById('foot').textContent = 'Advice is taken from ICAR, NIPHM and TNAU publications. Knowledge base ' +
    i.kb_version + (i.kb_reviewed ? '' : ' (draft, under expert review)') + '. Built with Llama.';
});
async function analyse() {
  const f = document.getElementById('photo').files[0], out = document.getElementById('out');
  if (!f) return;
  const lang = document.getElementById('lang').value;
  out.textContent = 'Checking...';
  const img = URL.createObjectURL(f);
  // Streaming: the diagnosis and the verified advice appear after about 0.3 s, the Llama text while it is written,
  // and the checked final result replaces both. Falls back to the one-shot endpoint if streaming is not available.
  try {
    const resp = await fetch('/api/analyse_stream?lang=' + lang, {method: 'POST', body: f});
    if (!resp.ok || !resp.body) throw new Error('no stream');
    const reader = resp.body.getReader(), dec = new TextDecoder();
    let buf = '', live = null, gotFinal = false;
    for (;;) {
      const {done, value} = await reader.read();
      if (done) break;
      buf += dec.decode(value, {stream: true});
      let nl;
      while ((nl = buf.indexOf('\n')) >= 0) {
        const line = buf.slice(0, nl); buf = buf.slice(nl + 1);
        if (!line.trim()) continue;
        const ev = JSON.parse(line);
        if (ev.event === 'result') {
          render(ev.data, img, lang);
          const c = el('div', 'card llama'); c.appendChild(el('b', '', 'Llama 3.2 1B is writing a summary of the sources below...'));
          live = el('p', 'muted', ''); c.appendChild(live);
          const first = document.getElementById('out').children[1];
          document.getElementById('out').insertBefore(c, first || null);
        } else if (ev.event === 'token' && live) {
          live.textContent += ev.text;
        } else if (ev.event === 'final') {
          gotFinal = true; render(ev.data, img, lang);
        } else if (ev.event === 'error') {
          throw new Error(ev.message);
        }
      }
    }
    if (gotFinal) return;
  } catch (e) { /* fall back below */ }
  const r = await (await fetch('/api/analyse?lang=' + lang, {method: 'POST', body: f})).json();
  render(r, img, lang);
}
function render(r, img, lang) {
  const out = document.getElementById('out'); out.innerHTML = '';
  const head = el('div', 'card'), row = el('div', 'row'), info = el('div');
  const im = el('img', 'thumb'); im.src = img; row.appendChild(im); row.appendChild(info); head.appendChild(row);
  if (r.status === 'retake_photo') info.appendChild(el('div', 'diag', 'Please take another photo'));
  else if (r.disease) {
    info.appendChild(el('div', 'diag', r.disease.name || 'Not certain'));
    if (r.disease.answered) info.appendChild(el('div', 'muted', 'Model confidence ' + Math.round(r.disease.top[0].probability * 100) + '%'));
    if (r.disease.urgent) info.appendChild(el('div', 'urgent', 'Urgent - act today'));
    if (r.severity && r.severity.level !== 'unknown') info.appendChild(el('div', 'muted', 'Estimated spread on this leaf: ' + r.severity.level + ' (rough estimate from photo colours)'));
  }
  (r.pests || []).forEach(p => info.appendChild(el('div', '', 'Insect found: ' + p.name + ' (' + p.species + ', ' + Math.round(p.confidence * 100) + '%)')));
  (r.messages || []).forEach(m => head.appendChild(el('div', 'note', m)));
  out.appendChild(head);
  lastTopic = r.disease ? r.disease.topic : null;
  if (r.llama && r.llama.text) {
    const c = el('div', 'card llama'); c.appendChild(el('b', '', 'Advice (Llama 3.2 1B on this device, from the sources below)'));
    c.appendChild(el('p', '', r.llama.text)); out.appendChild(c);
  }
  (r.advice_blocks || []).forEach(b => {
    const c = el('div', 'card'); c.appendChild(el('h3', '', b.name));
    b.chunks.filter(x => x.section !== 'chemical').forEach(x => {
      const p = el('p'); p.appendChild(el('b', '', x.section.replace('_', ' ') + ': ')); p.appendChild(document.createTextNode(x.text + ' '));
      p.appendChild(el('span', 'src', '[' + x.source_org + ']')); c.appendChild(p);
    });
    const sprays = b.chunks.filter(x => x.section === 'chemical');
    if (sprays.length) {
      const t = el('table'), h = el('tr'); ['Spray option (as published)', 'Dose', 'Source'].forEach(s => h.appendChild(el('th', '', s))); t.appendChild(h);
      sprays.forEach(x => { const tr = el('tr'), td = el('td', '', x.product); if (x.note) td.appendChild(el('div', 'src', x.note));
        tr.appendChild(td); tr.appendChild(el('td', '', x.dose)); tr.appendChild(el('td', 'src', x.source_org)); t.appendChild(tr); });
      c.appendChild(t);
    }
    out.appendChild(c);
  });
  const ask = el('div', 'card'); ask.innerHTML = '<b>Ask a question</b><div class="row"><input id="q" style="flex:1;min-width:200px;padding:8px" placeholder="e.g. when can I harvest after spraying?"><button onclick="askQ()">Ask</button></div><div id="ans"></div>';
  out.appendChild(ask);
  const d = el('details', 'card'); d.appendChild(el('summary', '', 'Technical details'));
  d.appendChild(el('pre', 'muted', JSON.stringify({timings_ms: r.timings_ms, llama: r.llama && {stats: r.llama.stats, accepted: r.llama.accepted, rejected: r.llama.rejected_reasons}}, null, 1)));
  out.appendChild(d);
  window._lang = lang;
}
async function askQ() {
  const q = document.getElementById('q').value, ans = document.getElementById('ans'); ans.textContent = '...';
  const j = await (await fetch('/api/ask', {method: 'POST', body: JSON.stringify({question: q, topic: lastTopic, lang: window._lang || 'en'})})).json();
  ans.innerHTML = '';
  if (j.answer) ans.appendChild(el('p', 'llama', j.answer));
  j.facts.forEach(f => ans.appendChild(el('p', '', f.text + ' [' + f.source_org + ']')));
}
</script></body></html>)HTML";
}

}  // namespace web
