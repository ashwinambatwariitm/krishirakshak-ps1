/**
 * App State Management & Local Storage History (FR-14)
 */

class AppState {
  constructor() {
    this.currentView = "home";
    this.capturedBlob = null;
    this.capturedUrl = null;
    this.analysisResult = null;
    this.lastTopic = null;
    this.mockExample = ""; // For developer / mock testing
    this.historyKey = "KR_SCAN_HISTORY";
  }

  setCapturedImage(blob) {
    if (this.capturedUrl) {
      URL.revokeObjectURL(this.capturedUrl);
    }
    this.capturedBlob = blob;
    this.capturedUrl = URL.createObjectURL(blob);
  }

  setResult(result) {
    this.analysisResult = result;
    this.lastTopic = (result && result.disease && result.disease.topic) ? result.disease.topic : null;

    // Save to local history if answered
    if (result && result.status === "answered" && result.disease) {
      this.saveToHistory({
        timestamp: Date.now(),
        diseaseName: result.disease.name || "Unknown",
        confidence: result.disease.top && result.disease.top[0] ? result.disease.top[0].probability : 0,
        urgent: !!result.disease.urgent,
        status: result.status,
        pestCount: (result.pests || []).length
      });
    }
  }

  getHistory() {
    try {
      const raw = localStorage.getItem(this.historyKey);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  saveToHistory(entry) {
    try {
      const history = this.getHistory();
      history.unshift(entry);
      // Keep only last 10 entries to preserve space (NFR-6)
      const trimmed = history.slice(0, 10);
      localStorage.setItem(this.historyKey, JSON.stringify(trimmed));
    } catch (e) {
      console.warn("Could not save to history:", e);
    }
  }

  clearHistory() {
    localStorage.removeItem(this.historyKey);
  }
}

window.appState = new AppState();
