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
      // A pest result has no disease name: the insects found are the result (names and the best box confidence)
      const pests = result.pests || [];
      const pestNames = [...new Set(pests.map(p => p.name).filter(Boolean))].join(", ");
      const top = result.disease.top && result.disease.top[0];
      this.saveToHistory({
        timestamp: Date.now(),
        diseaseName: result.disease.name || pestNames || "Unknown",
        confidence: result.disease.name && top ? top.probability
                    : pests.reduce((m, p) => Math.max(m, p.confidence || 0), 0),
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
