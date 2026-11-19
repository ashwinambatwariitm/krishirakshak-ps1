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
  speak(text, lang = "en", onEndCallback = null, fallbackText = null) {
    if (!this.synth) {
      alert("Text-to-Speech is not supported on this browser.");
      return;
    }

    // If already speaking, stop first
    this.stop();

    // Voice for the language: the 9 translation languages and English, Indian variants (hi-IN, ta-IN, ...).
    // If the phone has no voice for a translation language, the English text is read instead (fallbackText):
    // an English voice reading Marathi or Tamil script is not understandable.
    const voices = this.synth.getVoices();
    const hasVoice = (code) => voices.some(v => v.lang.toLowerCase().replace("_", "-").startsWith(code));
    if (fallbackText && lang !== "en" && voices.length > 0 && !hasVoice(lang)) {
      text = fallbackText;
      lang = "en";
    }

    const cleanText = text.replace(/\[.*?\]/g, "").trim();
    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = `${lang}-IN`;
    utterance.rate = 0.92; // Slightly slower, clearer tempo for farmers
    utterance.pitch = 1.0;

    // Pick best matching voice if available (an Indian voice first)
    const matchedVoice = voices.find(v => v.lang.toLowerCase().replace("_", "-") === `${lang}-in`) ||
                         voices.find(v => v.lang.toLowerCase().startsWith(lang));
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
      document.body.classList.add("tts-active");
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      document.body.classList.remove("tts-active");
      if (onEndCallback) onEndCallback();
    };

    utterance.onerror = (e) => {
      console.warn("TTS error:", e);
      this.isSpeaking = false;
      document.body.classList.remove("tts-active");
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
