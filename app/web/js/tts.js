/**
 * KrishiRakshak Offline Voice Read-Aloud (Text-to-Speech)
 * Meets FR-15: Read advice aloud using the phone's built-in offline TTS engine.
 */

class VoiceAdvisor {
  constructor() {
    this.synth = window.speechSynthesis;
    this.isSpeaking = false;
    this.currentUtterance = null;
  }

  isAvailable() {
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
    if (!this.synth) {
      this.notify(window.t ? window.t("tts_unsupported") : "Text-to-Speech is not supported on this browser.");
      if (onEndCallback) onEndCallback();
      return;
    }
    this.stop();

    // Voice for the language (hi-IN, mr-IN, ta-IN, ...). Voices come from the phone's speech engine and must be
    // installed for each language (and work offline on the Pi's hotspot). Without one, the English text is read
    // (an English voice cannot read Marathi or Tamil script) and the farmer is told how to install the voice.
    const voices = await this.voicesReady();
    const norm = (v) => v.lang.toLowerCase().replace("_", "-");
    const hasVoice = (code) => voices.some(v => norm(v).startsWith(code));
    if (lang !== "en" && !hasVoice(lang)) {
      const names = { hi: "Hindi", te: "Telugu", mr: "Marathi", kn: "Kannada", ta: "Tamil", bn: "Bengali",
                      gu: "Gujarati", or: "Odia", pa: "Punjabi" };
      const msg = (window.t ? window.t("tts_no_voice") : "No {lang} voice on this phone.").replace("{lang}", names[lang] || lang);
      this.notify(msg);
      if (!fallbackText) {
        if (onEndCallback) onEndCallback();
        return;
      }
      text = fallbackText;
      lang = "en";
    }

    const cleanText = text.replace(/\[.*?\]/g, "").trim();
    if (!cleanText) {
      if (onEndCallback) onEndCallback();
      return;
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = `${lang}-IN`;
    utterance.rate = 0.92; // Slightly slower, clearer tempo for farmers
    utterance.pitch = 1.0;
    // Pick best matching voice (an Indian voice first)
    const matchedVoice = voices.find(v => norm(v) === `${lang}-in`) || voices.find(v => norm(v).startsWith(lang));
    if (matchedVoice) utterance.voice = matchedVoice;

    // If the engine never starts (voice not downloaded, online-only voice without internet), say so
    const startTimer = setTimeout(() => {
      if (!this.isSpeaking) {
        this.synth.cancel();
        this.notify(window.t ? window.t("tts_not_started") : "Speech did not start.");
        if (onEndCallback) onEndCallback();
      }
    }, 5000);

    utterance.onstart = () => {
      clearTimeout(startTimer);
      this.isSpeaking = true;
      document.body.classList.add("tts-active");
    };
    utterance.onend = () => {
      clearTimeout(startTimer);
      this.isSpeaking = false;
      document.body.classList.remove("tts-active");
      if (onEndCallback) onEndCallback();
    };
    utterance.onerror = (e) => {
      clearTimeout(startTimer);
      console.warn("TTS error:", e);
      this.isSpeaking = false;
      document.body.classList.remove("tts-active");
      if (e.error !== "interrupted" && e.error !== "canceled")
        this.notify((window.t ? window.t("tts_not_started") : "Speech did not start.") + ` (${e.error})`);
      if (onEndCallback) onEndCallback();
    };

    this.currentUtterance = utterance;
    this.synth.speak(utterance);
  }

  stop() {
    if (this.synth) {
      this.synth.cancel();
      this.isSpeaking = false;
      document.body.classList.remove("tts-active");
    }
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
