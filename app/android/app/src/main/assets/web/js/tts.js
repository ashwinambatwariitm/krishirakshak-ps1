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
   * Speak given text in current language (en-IN or hi-IN)
   * @param {string} text Text to read aloud
   * @param {string} lang "en" or "hi"
   * @param {Function} [onEndCallback]
   */
  speak(text, lang = "en", onEndCallback = null) {
    if (!this.synth) {
      alert("Text-to-Speech is not supported on this browser.");
      return;
    }

    // If already speaking, stop first
    this.stop();

    const cleanText = text.replace(/\[.*?\]/g, "").trim();
    if (!cleanText) return;

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = lang === "hi" ? "hi-IN" : "en-IN";
    utterance.rate = 0.92; // Slightly slower, clearer tempo for farmers
    utterance.pitch = 1.0;

    // Pick best matching voice if available
    const voices = this.synth.getVoices();
    const targetPrefix = lang === "hi" ? "hi" : "en";
    const matchedVoice = voices.find(v => v.lang.startsWith(targetPrefix));
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

  toggle(text, lang = "en", buttonEl = null) {
    if (this.isSpeaking) {
      this.stop();
      if (buttonEl) buttonEl.classList.remove("speaking");
    } else {
      if (buttonEl) buttonEl.classList.add("speaking");
      this.speak(text, lang, () => {
        if (buttonEl) buttonEl.classList.remove("speaking");
      });
    }
  }
}

window.voiceAdvisor = new VoiceAdvisor();
