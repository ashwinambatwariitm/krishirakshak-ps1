/**
 * KrishiRakshak API Client
 * 
 * Complies with docs/APP_API.md:
 * - GET /api/info
 * - POST /api/analyse?lang=en|hi&translate=ta (Raw photo bytes in body; translate is optional)
 * - POST /api/ask (JSON body: { question, topic, lang, translate })
 * 
 * 60s timeout handling for on-device inference (FR-2).
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

  /**
   * Fetch device info: models, KB version, review status
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
   * Send raw photo bytes to POST /api/analyse?lang=en|hi
   * @param {Blob|File} imageBlob Raw binary image
   * @param {string} lang "en" or "hi"
   * @param {string} [exampleParam] Optional mock selector (e.g. "uncertain", "retake", "pest")
   * @param {string} [translate] Optional language for the machine translation of the advice ("" = none)
   */
  async analyseImage(imageBlob, lang = "en", exampleParam = "", translate = "") {
    let query = `?lang=${encodeURIComponent(lang)}`;
    if (translate) {
      query += `&translate=${encodeURIComponent(translate)}`;
    }
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
   * Ask follow-up question
   * @param {string} question 
   * @param {string|null} topic 
   * @param {string} lang 
   * @param {string} [translate] Optional language for the machine translation of the answer
   */
  async askQuestion(question, topic = null, lang = "en", translate = "") {
    const url = `${this.getBaseUrl()}/api/ask`;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 45000);

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json; charset=utf-8"
        },
        body: JSON.stringify({
          question: question.trim(),
          topic: topic || "",
          lang: lang,
          translate: translate || ""
        }),
        signal: controller.signal
      });

      clearTimeout(timer);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      return await res.json();
    } catch (err) {
      clearTimeout(timer);
      throw err;
    }
  }
}

window.apiService = new ApiService();
