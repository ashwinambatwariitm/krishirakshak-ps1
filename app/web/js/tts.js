/**
 * KrishiRakshak Multi-Tier Voice Read-Aloud (Text-to-Speech)
 * 
 * Works 100% offline in Android WebView via Android Native TTS bridge (AndroidTTS),
 * works in desktop & mobile Chrome/Safari/Edge via Web Speech API (SpeechSynthesis),
 * and provides HTML5 Audio streaming fallback for browsers without native TTS.
 * Never throws blocking alert popups.
 */

class VoiceAdvisor {
  constructor() {
    this.synth = window.speechSynthesis;
    this.isSpeaking = false;
    this.currentUtterance = null;
    this.currentAudio = null;
    this.activeButton = null;
    this.durationTimer = null;
  }

  isAvailable() {
    if (window.AndroidTTS && typeof window.AndroidTTS.isAvailable === "function") {
      return true;
    }
    return !!window.speechSynthesis || typeof Audio !== "undefined";
  }

  /**
   * Speak given text in the given language
   * @param {string} text Text to read aloud
   * @param {string} lang "en", "hi", "mr", "te", "ta", "kn", "bn", "gu", "pa", "or"
   * @param {Function} [onEndCallback]
   */
  speak(text, lang = "en", onEndCallback = null) {
    this.stop();

    const cleanText = (text || "")
      .replace(/\[.*?\]/g, "")
      .replace(/\*\*/g, "")
      .replace(/\*/g, "")
      .replace(/•/g, "")
      .replace(/#+/g, "")
      .replace(/[-_]{2,}/g, "")
      .trim();

    if (!cleanText) {
      if (onEndCallback) onEndCallback();
      return;
    }

    this.onEndHandler = onEndCallback;

    // Strategy 1: Native Android TTS Interface (100% Offline in Android APK WebView)
    if (window.AndroidTTS && typeof window.AndroidTTS.speak === "function") {
      try {
        this.isSpeaking = true;
        document.body.classList.add("tts-active");
        window.AndroidTTS.speak(cleanText, lang);

        // Approximate duration for farmer UI button state
        const wordCount = cleanText.split(/\s+/).length;
        const estDurationMs = Math.min(60000, Math.max(3000, (wordCount / 2.3) * 1000));

        if (this.durationTimer) clearTimeout(this.durationTimer);
        this.durationTimer = setTimeout(() => {
          this.stop();
        }, estDurationMs);
        return;
      } catch (err) {
        console.warn("AndroidTTS bridge error, trying browser fallback:", err);
      }
    }

    // Strategy 2: Web Speech API (Standard Chrome / Edge / Safari / Firefox)
    if (this.synth) {
      try {
        const voices = this.synth.getVoices ? this.synth.getVoices() : [];
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = `${lang}-IN`;
        utterance.rate = 0.92; // Clear, comfortable tempo for rural farmers
        utterance.pitch = 1.0;

        if (voices.length > 0) {
          const matchedVoice = voices.find(v => v.lang.toLowerCase().replace("_", "-") === `${lang}-in`) ||
                               voices.find(v => v.lang.toLowerCase().startsWith(lang));
          if (matchedVoice) {
            utterance.voice = matchedVoice;
          }
        }

        utterance.onstart = () => {
          this.isSpeaking = true;
          document.body.classList.add("tts-active");
        };

        utterance.onend = () => {
          this.stop();
        };

        utterance.onerror = (e) => {
          console.warn("SpeechSynthesis error, trying audio fallback:", e);
          this.playAudioFallback(cleanText, lang);
        };

        this.currentUtterance = utterance;
        this.synth.speak(utterance);
        return;
      } catch (synthErr) {
        console.warn("SpeechSynthesis exception:", synthErr);
      }
    }

    // Strategy 3: HTML5 Audio Stream Fallback
    this.playAudioFallback(cleanText, lang);
  }

  playAudioFallback(text, lang) {
    try {
      this.isSpeaking = true;
      document.body.classList.add("tts-active");

      // Short chunk for streaming audio
      const chunk = text.slice(0, 180);
      const url = `https://translate.google.com/translate_tts?ie=UTF-8&tl=${encodeURIComponent(lang)}&client=tw-ob&q=${encodeURIComponent(chunk)}`;
      const audio = new Audio(url);
      this.currentAudio = audio;

      audio.onended = () => {
        this.stop();
      };
      audio.onerror = () => {
        this.stop();
      };

      audio.play().catch(e => {
        console.log("Audio playback prevented:", e.message);
        this.stop();
      });
    } catch (e) {
      this.stop();
    }
  }

  stop() {
    if (this.durationTimer) {
      clearTimeout(this.durationTimer);
      this.durationTimer = null;
    }

    if (window.AndroidTTS && typeof window.AndroidTTS.stop === "function") {
      try { window.AndroidTTS.stop(); } catch (e) {}
    }

    if (this.synth) {
      try { this.synth.cancel(); } catch (e) {}
    }

    if (this.currentAudio) {
      try {
        this.currentAudio.pause();
        this.currentAudio = null;
      } catch (e) {}
    }

    this.isSpeaking = false;
    document.body.classList.remove("tts-active");

    if (this.activeButton) {
      this.activeButton.classList.remove("speaking");
      this.activeButton = null;
    }

    if (this.onEndHandler) {
      const cb = this.onEndHandler;
      this.onEndHandler = null;
      cb();
    }
  }

  toggle(text, lang = "en", buttonEl = null) {
    if (this.isSpeaking) {
      this.stop();
    } else {
      if (buttonEl) {
        this.activeButton = buttonEl;
        buttonEl.classList.add("speaking");
      }
      this.speak(text, lang, () => {
        if (buttonEl) buttonEl.classList.remove("speaking");
        this.activeButton = null;
      });
    }
  }
}

// Global initialization
window.VoiceAdvisor = VoiceAdvisor;
window.voiceAdvisor = new VoiceAdvisor();
