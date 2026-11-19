/**
 * KrishiRakshak App Configuration (embedded in the Android APK: API defaults to the Pi hotspot)
 * 
 * NFR-5 requirement: The API base address is configured in ONE setting.
 * Empty string ("") means same server (used when Pi serves the static files).
 * If testing from a local development server or separate port, change API_BASE
 * or use the in-app settings override in the About screen.
 */
const CONFIG = {
  // Base URL for the KrishiRakshak API (e.g., "" on Pi, or "http://localhost:8080" for mock server)
  API_BASE: localStorage.getItem("KR_API_BASE") || "http://10.42.0.1:8080",

  // Timeout in milliseconds (FR-2: Pi ExecuTorch Llama 3B inference can take ~45s)
  TIMEOUT_MS: 60000,

  // Default interface language ("en" or "hi")
  DEFAULT_LANG: localStorage.getItem("KR_LANG") || "en",

  // Machine translation of the checked Llama advice: "" = none, or hi te mr kn ta bn gu or pa
  // (the device translates on the Pi with IndicTrans2; the English advice is always shown too)
  TRANSLATE_LANG: localStorage.getItem("KR_TRANSLATE") || "",

  // Version
  APP_VERSION: "1.0.0 (Phase 1)"
};

// Global export
window.CONFIG = CONFIG;
