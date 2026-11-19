/**
 * KrishiRakshak Hybrid API Client
 * 
 * Complies with docs/APP_API.md:
 * - GET /api/info
 * - POST /api/analyse?lang=en|hi (Raw photo bytes in body)
 * - POST /api/ask (JSON body: { question, topic, lang })
 * 
 * Free Cloud AI Fallback:
 * If the Raspberry Pi is offline or unreachable, seamlessly queries
 * the Free Cloud AI (Pollinations Llama/OpenAI, zero key required) or
 * user's free Gemini API key.
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

  /**
   * Fetch device info
   */
  async getInfo() {
    const url = `${this.getBaseUrl()}/api/info`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

    try {
      const res = await fetch(url, {
        method: "GET",
        signal: controller.signal
      });
      clearTimeout(timeout);
      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      clearTimeout(timeout);
      throw err;
    }
  }

  /**
   * Send raw photo bytes to POST /api/analyse
   */
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
        headers: {
          "Content-Type": imageBlob.type || "image/jpeg"
        },
        body: imageBlob,
        signal: controller.signal
      });

      clearTimeout(timer);

      if (!res.ok) {
        throw new Error(`Device responded with HTTP ${res.status}`);
      }

      const json = await res.json();
      return json;
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

  /**
   * Ask Question (Hybrid: Pi on-device -> Free Cloud AI fallback)
   */
  async askQuestion(question, topic = null, lang = "en") {
    // 1. Try On-Device Raspberry Pi Server First
    try {
      const piRes = await this.askPiDevice(question, topic, lang);
      if (piRes && (piRes.answer || (piRes.facts && piRes.facts.length > 0))) {
        return piRes;
      }
    } catch (piErr) {
      console.log("[KrishiRakshak] Pi server unavailable for Q&A, attempting Free Cloud AI:", piErr.message);
    }

    // 2. Fallback to Free Cloud AI (Pollinations / Gemini)
    return await this.askCloudAi(question, topic, lang);
  }

  async askPiDevice(question, topic, lang) {
    const url = `${this.getBaseUrl()}/api/ask`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 20000);

    const res = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json; charset=utf-8"
      },
      body: JSON.stringify({
        question: question.trim(),
        topic: topic || "",
        lang: lang
      }),
      signal: controller.signal
    });

    clearTimeout(timer);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  }

  /**
   * Free Cloud AI query (Pollinations text API or Google Gemini)
   */
  async askCloudAi(question, topic, lang = "en") {
    const customKey = this.getCustomAiKey();

    // If user provided a Gemini key, use Google Gemini Flash
    if (customKey && customKey.startsWith("AIza")) {
      return await this.askGemini(question, topic, lang, customKey);
    }

    // Default: Pollinations Free AI API (100% Free, Zero Key Required)
    const systemPrompt = lang === "hi"
      ? "आप कृषिरक्षक AI हैं, जो भारतीय किसानों के लिए एक सहायक कृषि विशेषज्ञ है। हमेशा सरल, संक्षिप्त और व्यावहारिक हिंदी में उत्तर दें।"
      : "You are KrishiRakshak AI, an agricultural expert assisting Indian farmers. Give concise, practical, and scientifically sound farming advice.";

    const body = {
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: `Topic: ${topic || "Tomato Farming"}. Question: ${question}` }
      ],
      model: "openai"
    };

    const res = await fetch("https://text.pollinations.ai/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    if (!res.ok) {
      throw new Error("Free AI cloud endpoint busy. Please try again.");
    }

    const answerText = await res.text();
    return {
      accepted: true,
      answer: answerText.trim(),
      source: "KrishiRakshak Cloud AI (Free)"
    };
  }

  async askGemini(question, topic, lang, key) {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${key}`;
    const prompt = `You are KrishiRakshak AI expert. Answer this tomato farmer's question in ${lang === "hi" ? "Hindi" : "English"} simply and accurately: ${question}`;

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
