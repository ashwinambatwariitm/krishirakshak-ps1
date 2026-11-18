# Phase 2 Ideas and Open Issues
**KrishiRakshak Farmer App | Deliverable D5**

---

## 1. Native Android App (Option B in Work Order)
* **Standalone APK via Android WebView / TWA (Trusted Web Activity):**
  A production-ready Android wrapper is structured under `app/android/`. It packages the offline static assets directly into the Android `assets/` directory or points to `http://10.42.0.1:8080` when connected to the Pi hotspot.
* **CameraX & On-Device Framing Guidance:**
  Integrate Android CameraX with a real-time viewfinder overlay guiding farmers on leaf positioning, focus distance, and ambient lighting before taking the shot (reducing `retake_photo` occurrences).
* **Local SQLite Caching:**
  Upgrade scan history to Room DB / SQLite for persistent storage of past diagnoses, crop health trends over the season, and field coordinates.

## 2. Offline Text-to-Speech (TTS) Voice Advisor (FR-15)
* Implement Android's native offline Text-to-Speech engine (`android.speech.tts.TextToSpeech`) for both Hindi (`hi_IN`) and regional languages (Marathi `mr_IN`, Telugu `te_IN`, Tamil `ta_IN`).
* Farmers can tap a prominent speaker button (🔊) to listen to Llama's simplified advice and spray warnings aloud in their field without needing to read small text.

## 3. Audio & Voice Q&A Input
* Add offline voice input using Android's native speech recognizer (`SpeechRecognizer`) for asking follow-up questions in spoken Hindi or regional dialects.

## 4. Multi-Crop Expansion
* Beyond tomato diseases, expand the knowledge base and classifier to potato, chilli, cotton, and paddy crops as new models are trained by the core team.

## 5. Automated Hotspot Provisioning
* Use Wi-Fi Network Suggestion API on Android 10+ so the phone automatically detects and binds to the Pi's Wi-Fi hotspot (`KrishiRakshak-Pi5`) without manual network switching.
