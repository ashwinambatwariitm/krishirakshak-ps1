/**
 * KrishiRakshak Offline Voice Read-Aloud (Text-to-Speech)
 * Meets FR-15: Read advice aloud using the phone's built-in offline TTS engine.
 */

class VoiceAdvisor {
  constructor() {
    this.synth = window.speechSynthesis;
    this.isSpeaking = false;
    this.currentUtterance = null;
    this.runId = 0;
  }

  // Android app: the WebView has no speechSynthesis; MainActivity exposes the phone's own offline engine
  hasNative() {
    return !!(window.AndroidTTS && typeof window.AndroidTTS.speak === "function");
  }

  isAvailable() {
    return this.hasNative() || !!window.speechSynthesis;
  }

  /**
   * Android app: speak through the phone's engine. Same order of attempts as the browser path (the language,
   * Hindi for Marathi, then the English text); the bridge returns false when no installed voice exists for a
   * language, and calls nativeDone(id) when the text has been spoken.
   */
  speakNative(text, lang, onEndCallback, fallbackText) {
    this.stop();
    const run = ++this.runId;
    const clean = (t) => (t || "").replace(/\[.*?\]/g, "").trim();
    const attempts = [];
    if (lang !== "en") {
      attempts.push({ text, lang });
      if (lang === "mr") attempts.push({ text, lang: "hi" });
      attempts.push({ text: fallbackText, lang: "en" });
    } else {
      attempts.push({ text, lang: "en" });
    }
    const names = { hi: "Hindi", te: "Telugu", mr: "Marathi", kn: "Kannada", ta: "Tamil", bn: "Bengali",
                    gu: "Gujarati", or: "Odia", pa: "Punjabi" };
    for (let i = 0; i < attempts.length; i++) {
      const a = attempts[i];
      if (!clean(a.text)) continue;
      if (lang !== "en" && a.lang === "en") {
        this.notify((window.t ? window.t("tts_no_voice") : "No {lang} voice on this phone.").replace("{lang}", names[lang] || lang));
      }
      const id = `kr${run}x${i}`;
      let ok = false;
      try {
        ok = window.AndroidTTS.isAvailable() && window.AndroidTTS.speak(clean(a.text), a.lang, id);
      } catch (e) {
        console.warn("AndroidTTS error:", e);
      }
      if (ok) {
        this.isSpeaking = true;
        document.body.classList.add("tts-active");
        this.nativeEnd = { id, cb: onEndCallback };
        return;
      }
    }
    this.notify(window.t ? window.t("tts_not_started") : "Speech did not start.");
    if (onEndCallback) onEndCallback();
  }

  // Called by MainActivity when the phone's engine has finished (or failed) the text with this id
  nativeDone(id) {
    if (!this.nativeEnd || this.nativeEnd.id !== id) return;
    const cb = this.nativeEnd.cb;
    this.nativeEnd = null;
    this.isSpeaking = false;
    document.body.classList.remove("tts-active");
    if (cb) cb();
  }

  /**
   * Speak given text in the given language (en, hi or a translation language: <lang>-IN voice)
   * @param {string} text Text to read aloud
   * @param {string} lang "en", "hi", "mr", "ta", ...
   * @param {Function} [onEndCallback]
   * @param {string} [fallbackText] English text read instead when the phone has no voice for lang
   */
  // The phone's voice list loads after the page on Android Chrome: wait for it (at most 2 s)
  voicesReady() {
    const now = this.synth.getVoices();
    if (now.length > 0) return Promise.resolve(now);
    return new Promise(resolve => {
      const done = () => resolve(this.synth.getVoices());
      this.synth.addEventListener("voiceschanged", done, { once: true });
      setTimeout(done, 2000);
    });
  }

  // Short message at the bottom of the screen (why nothing is spoken, or what is read instead)
  notify(message) {
    let el = document.getElementById("kr-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "kr-toast";
      el.className = "kr-toast";
      document.body.appendChild(el);
    }
    el.textContent = message;
    el.classList.add("show");
    clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => el.classList.remove("show"), 7000);
  }

  async speak(text, lang = "en", onEndCallback = null, fallbackText = null) {
    if (this.hasNative()) {
      this.speakNative(text, lang, onEndCallback, fallbackText);
      return;
    }
    if (!this.synth) {
      this.notify(window.t ? window.t("tts_unsupported") : "Text-to-Speech is not supported on this browser.");
      if (onEndCallback) onEndCallback();
      return;
    }
    this.stop();
    const run = ++this.runId;   // a newer press of a voice button cancels the remaining attempts of this one

    // Voices come from the phone's speech engine. Android lists a language even when its voice data is not
    // downloaded; offline (the Pi's hotspot has no internet) such a voice fails with "synthesis-failed". So the
    // attempts are tried in order until one starts: voices of the language (offline ones first), for Marathi a
    // Hindi voice (same Devanagari script), then the English text with an English voice.
    const voices = await this.voicesReady();
    const norm = (v) => v.lang.toLowerCase().replace("_", "-");
    const byLang = (code) => voices.filter(v => norm(v).startsWith(code))
      .sort((x, y) => (y.localService - x.localService) || ((norm(y) === `${code}-in`) - (norm(x) === `${code}-in`)));
    const clean = (t) => (t || "").replace(/\[.*?\]/g, "").trim();
    const attempts = [];
    // At most two voices per language; for English the engine's default is also tried (voice list can be empty)
    const add = (t, code, list, orDefault) => {
      if (!clean(t)) return;
      list.slice(0, 2).forEach(v => attempts.push({ text: clean(t), lang: code, voice: v }));
      if (list.length === 0 && orDefault) attempts.push({ text: clean(t), lang: code, voice: null });
    };
    if (lang !== "en") {
      add(text, lang, byLang(lang), false);
      if (lang === "mr") add(text, "hi", byLang("hi"), false);
      add(fallbackText, "en", byLang("en"), true);
    } else {
      add(text, "en", byLang("en"), true);
    }
    if (attempts.length === 0) {
      if (onEndCallback) onEndCallback();
      return;
    }

    const names = { hi: "Hindi", te: "Telugu", mr: "Marathi", kn: "Kannada", ta: "Tamil", bn: "Bengali",
                    gu: "Gujarati", or: "Odia", pa: "Punjabi" };
    const finish = () => {
      this.isSpeaking = false;
      document.body.classList.remove("tts-active");
      if (onEndCallback) onEndCallback();
    };
    const tryAttempt = (i) => {
      if (run !== this.runId) return;
      if (i >= attempts.length) {
        this.notify(window.t ? window.t("tts_not_started") : "Speech did not start.");
        finish();
        return;
      }
      const a = attempts[i];
      // Falling back to the English text: say why (the voice for the chosen language is missing or not downloaded)
      if (lang !== "en" && a.lang === "en" && (i === 0 || attempts[i - 1].lang !== "en")) {
        const msg = (window.t ? window.t("tts_no_voice") : "No {lang} voice on this phone.").replace("{lang}", names[lang] || lang);
        this.notify(msg);
      }
      const u = new SpeechSynthesisUtterance(a.text);
      u.lang = `${a.lang}-IN`;
      if (a.voice) u.voice = a.voice;
      u.rate = 0.92;   // slightly slower, clearer tempo for farmers
      u.pitch = 1.0;
      let started = false, moved = false;
      const next = () => { if (!moved) { moved = true; clearTimeout(timer); this.synth.cancel(); tryAttempt(i + 1); } };
      const timer = setTimeout(() => { if (!started) next(); }, 4000);   // engine never started
      u.onstart = () => {
        started = true;
        clearTimeout(timer);
        this.isSpeaking = true;
        document.body.classList.add("tts-active");
      };
      u.onend = () => { clearTimeout(timer); if (!moved && run === this.runId) finish(); };
      u.onerror = (e) => {
        console.warn("TTS error:", e.error, a.lang, a.voice && a.voice.name);
        if (e.error === "interrupted" || e.error === "canceled") { clearTimeout(timer); if (!moved && run === this.runId) finish(); return; }
        if (!started) next(); else { clearTimeout(timer); finish(); }
      };
      this.currentUtterance = u;
      this.synth.speak(u);
    };
    tryAttempt(0);
  }

  stop() {
    this.runId++;
    this.nativeEnd = null;
    if (this.hasNative()) {
      try { window.AndroidTTS.stop(); } catch (e) { /* engine not ready */ }
    }
    if (this.synth) this.synth.cancel();
    this.isSpeaking = false;
    document.body.classList.remove("tts-active");
  }

  toggle(text, lang = "en", buttonEl = null, fallbackText = null) {
    if (this.isSpeaking) {
      this.stop();
      if (buttonEl) buttonEl.classList.remove("speaking");
    } else {
      if (buttonEl) buttonEl.classList.add("speaking");
      this.speak(text, lang, () => {
        if (buttonEl) buttonEl.classList.remove("speaking");
      }, fallbackText);
    }
  }
}

window.voiceAdvisor = new VoiceAdvisor();
