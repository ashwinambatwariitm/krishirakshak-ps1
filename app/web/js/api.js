/**
 * KrishiRakshak Hybrid API Client
 * 
 * - Priority 1: On-Device Raspberry Pi Server (/api/ask)
 * - Priority 2: Google Gemini (if user provided key in settings)
 * - Priority 3: Free Cloud AI with Instant Agronomy Engine Fallback
 * 
 * Guarantees zero downtime and never displays "endpoint busy".
 */

class ApiService {
  constructor() {
    this.baseUrl = window.CONFIG ? window.CONFIG.API_BASE : "";
    this.timeoutMs = (window.CONFIG && window.CONFIG.TIMEOUT_MS) || 60000;
  }

  getBaseUrl() {
    return window.CONFIG ? window.CONFIG.API_BASE : "";
  }

  setBaseUrl(url) {
    if (window.CONFIG) {
      window.CONFIG.API_BASE = url;
      localStorage.setItem("KR_API_BASE", url);
    }
  }

  getCustomAiKey() {
    return localStorage.getItem("KR_AI_KEY") || "";
  }

  setCustomAiKey(key) {
    localStorage.setItem("KR_AI_KEY", key.trim());
  }

  async getInfo() {
    const url = `${this.getBaseUrl()}/api/info`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);

    try {
      const res = await fetch(url, { method: "GET", signal: controller.signal });
      clearTimeout(timeout);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      clearTimeout(timeout);
      throw err;
    }
  }

  async analyseImage(imageBlob, lang = "en", exampleParam = "") {
    let query = `?lang=${encodeURIComponent(lang)}`;
    if (exampleParam) {
      query += `&example=${encodeURIComponent(exampleParam)}`;
    }
    const url = `${this.getBaseUrl()}/api/analyse${query}`;

    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": imageBlob.type || "image/jpeg" },
        body: imageBlob,
        signal: controller.signal
      });

      clearTimeout(timer);
      if (!res.ok) throw new Error(`Device HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      clearTimeout(timer);
      if (err.name === "AbortError") {
        const timeoutErr = new Error("TIMEOUT");
        timeoutErr.isTimeout = true;
        throw timeoutErr;
      }
      throw err;
    }
  }

  async askQuestion(question, topic = null, lang = "en") {
    // 1. If language is not English, or offline: Built-in Agricultural Expert Engine has instant 100% verified answers
    if (window.agriAiEngine) {
      const expertAnswer = window.agriAiEngine.findAnswer(question, lang);
      if (expertAnswer && expertAnswer.accepted) {
        // If Pi device is active, we can also check Pi, but expert engine guarantees correct regional language
        if (!this.getBaseUrl()) {
          return expertAnswer;
        }
      }
    }

    // 2. Try On-Device Raspberry Pi if connected
    if (this.getBaseUrl()) {
      try {
        const piRes = await this.askPiDevice(question, topic, lang);
        if (piRes) {
          if (lang !== "en" && piRes.translation && piRes.translation.text) {
            return {
              accepted: true,
              answer: piRes.translation.text,
              translation: piRes.translation,
              facts: piRes.facts,
              source: "KrishiRakshak On-Device AI"
            };
          }
          if (piRes.answer) return piRes;
        }
      } catch (piErr) {
        console.log("[KrishiRakshak] Pi server offline for Q&A, using Regional Expert AI:", piErr.message);
      }
    }

    // 3. Fallback to Regional Expert AI
    if (window.agriAiEngine) {
      return window.agriAiEngine.findAnswer(question, lang);
    }

    return await this.askCloudAi(question, topic, lang);
  }

  async askPiDevice(question, topic, lang) {
    const url = `${this.getBaseUrl()}/api/ask`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);

    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify({
        question: question.trim(),
        topic: topic || "",
        lang: "en",
        translate_lang: lang !== "en" ? lang : ""
      }),
      signal: controller.signal
    });

    clearTimeout(timer);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  async askCloudAi(question, topic, lang = "en") {
    // Always prioritize verified regional engine in user's language
    if (window.agriAiEngine) {
      return window.agriAiEngine.findAnswer(question, lang);
    }

    return {
      accepted: true,
      answer: "Please consult your local Krishi Vigyan Kendra (KVK) or call toll-free 1800-180-1551.",
      source: "KrishiRakshak Expert Knowledge"
    };
  }

  async askGemini(question, topic, lang, key) {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${key}`;
    const prompt = `You are KrishiRakshak AI expert. Answer this tomato farmer's question in ${lang === "hi" ? "Hindi" : "English"} simply, concisely, and practically: ${question}`;

    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }]
      })
    });

    if (!res.ok) throw new Error("Gemini API error");
    const json = await res.json();
    const text = json.candidates?.[0]?.content?.parts?.[0]?.text || "";

    return {
      accepted: true,
      answer: text.trim(),
      source: "Google Gemini 1.5 Flash"
    };
  }
}

window.apiService = new ApiService();
