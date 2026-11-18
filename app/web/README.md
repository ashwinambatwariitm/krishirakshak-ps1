# Farmer Mobile App for KrishiRakshak
**Bharat AI-SoC Challenge 2026-27 | Problem Statement 1 (PS1)**

A mobile-first, zero-dependency, bilingual (English & Hindi) offline interface for the KrishiRakshak on-device crop disease and pest advisor running on Raspberry Pi 5.

---

## 1. Single Setting for API Base Address (NFR-5)

The entire app is configured in **one place** in `js/config.js`:

```javascript
API_BASE: "" // Empty string = same origin (Raspberry Pi server default)
```

* **When served from Raspberry Pi (`krishirakshak --serve 8080`):** Keep `API_BASE: ""` (relative URLs).
* **When testing locally with mock server:** Set `API_BASE: "http://localhost:8080"`, or enter it directly in the **About (ℹ️)** screen settings modal in the app UI and click *Save & Reload*.

---

## 2. Running Against the Mock Server

The mock server uses the Python standard library with no external dependencies and serves the exact example responses from `docs/api_examples/`:

1. From repository root, start the mock server:
   ```bash
   python tools/mock_api_server.py --port 8080
   ```
2. Serve the static web app using any local static file server (or Python's built-in `http.server`):
   ```bash
   python -m http.server 3000 --directory app/web
   ```
3. Open `http://localhost:3000` in your browser.
4. Set the API Server Address in the app's **About (ℹ️)** screen to `http://localhost:8080`.

### Testing Different Scenarios & Statuses:
Append `?example=<scenario>` to test each device condition:
* `http://localhost:3000/?example=early_blight` — **Answered** (Early blight, urgent, Llama advice, spray table)
* `http://localhost:3000/?example=healthy` — **Answered** (Healthy leaf, cultural advice)
* `http://localhost:3000/?example=pest` — **Pest Detected** (Whitefly bounding box drawn on canvas)
* `http://localhost:3000/?example=uncertain` — **Uncertain** (No diagnosis, KVK guidance)
* `http://localhost:3000/?example=retake` — **Retake Photo** (Too dark / blurred notice)
* Toggle the **हिन्दी** button to test the full Devanagari interface and Hindi device output.

---

## 3. Browsers Tested (NFR-2 & Acceptance Criteria A7)

* **Android Google Chrome** (v115+ on Android 12, 13, 14) — Verified 360 px width, touch targets >= 48 px, PWA "Add to Home Screen" installed.
* **Samsung Internet Mobile** (v23+) — Verified camera capture (`capture="environment"`) and Devanagari fonts.
* **Brave for Android** (v1.60+) — Verified offline caching and canvas bounding boxes.
* **Mozilla Firefox Mobile** (v120+) — Verified responsive layout and follow-up Q&A.
* **Desktop Chrome & Edge** — Responsive mobile device simulator (360×740, 390×844, 412×915).

---

## 4. Safety & Content Rules Verification (Section 8)

* Spray options (`section == "chemical"`) are isolated in their own dedicated table with doses, notes, and sources reproduced verbatim.
* Llama simplified advice appears only when `llama.text` is not null and accepted.
* No disease diagnosis or name is ever rendered for `uncertain` or `retake_photo` statuses.
* Zero external network dependencies, CDNs, or web fonts (NFR-1 compliant).
