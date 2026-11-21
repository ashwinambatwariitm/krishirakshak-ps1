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
    this.durationTimer = null;

    document.addEventListener("DOMContentLoaded", () => {
      const stopBtn = document.getElementById("btn-tts-float-stop");
      if (stopBtn) stopBtn.addEventListener("click", () => this.stop());
    });
  }

  showFloatingBar(lang) {
    const bar = document.getElementById("tts-floating-bar");
    const textEl = document.getElementById("tts-float-text");
    if (!bar) return;
    const names = { hi: "Hindi", te: "Telugu", mr: "Marathi", kn: "Kannada", ta: "Tamil", bn: "Bengali",
                    gu: "Gujarati", or: "Odia", pa: "Punjabi", en: "English" };
    const langName = names[lang] || lang || "English";
    if (textEl) {
      const template = (window.t && window.t("speaking_label")) ? window.t("speaking_label") : "Speaking advice in {lang}...";
      textEl.textContent = template.replace("{lang}", langName);
    }
    bar.classList.remove("hidden");
  }

  hideFloatingBar() {
    const bar = document.getElementById("tts-floating-bar");
    if (bar) bar.classList.add("hidden");
    document.querySelectorAll(".btn-voice.speaking").forEach(b => b.classList.remove("speaking"));
  }

  isAvailable() {
    if (window.AndroidTTS && typeof window.AndroidTTS.isAvailable === "function") {
      return true;
    }
    return !!window.speechSynthesis;
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
    // Strategy 1: Native Android TTS Interface (100% offline in Android APK WebView)
    if (window.AndroidTTS && typeof window.AndroidTTS.speak === "function") {
      this.stop();
      const clean = (t) => (t || "")
        .replace(/\[.*?\]/g, "")
        .replace(/\*\*/g, "")
        .replace(/\*/g, "")
        .replace(/\u2022/g, "")
        .replace(/#+/g, "")
        .trim();
      const cleanText = clean(text);
      if (!cleanText) {
        if (onEndCallback) onEndCallback();
        return;
      }
      try {
        this.isSpeaking = true;
        document.body.classList.add("tts-active");
        this.showFloatingBar(lang);
        window.AndroidTTS.speak(cleanText, lang);

        const wordCount = cleanText.split(/\s+/).length;
        const estDurationMs = Math.min(60000, Math.max(3000, (wordCount / 2.3) * 1000));
        if (this.durationTimer) clearTimeout(this.durationTimer);
        this.durationTimer = setTimeout(() => {
          this.stop();
          if (onEndCallback) onEndCallback();
        }, estDurationMs);
        return;
      } catch (err) {
        console.warn("AndroidTTS bridge error:", err);
      }
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
      this.hideFloatingBar();
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
        this.showFloatingBar(a.lang || lang);
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
    if (this.durationTimer) {
      clearTimeout(this.durationTimer);
      this.durationTimer = null;
    }
    if (window.AndroidTTS && typeof window.AndroidTTS.stop === "function") {
      try { window.AndroidTTS.stop(); } catch (e) {}
    }
    if (this.synth) {
      this.synth.cancel();
    }
    this.isSpeaking = false;
    document.body.classList.remove("tts-active");
    this.hideFloatingBar();
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
