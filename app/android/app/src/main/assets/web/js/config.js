/**
 * KrishiRakshak App Configuration (Embedded in Android APK)
 * 
 * Default server is the Raspberry Pi 5 hotspot address: http://10.42.0.1:8080
 * Can be overridden in localStorage via the in-app About screen settings.
 */
const CONFIG = {
  // Base URL for the KrishiRakshak API (defaults to Pi hotspot IP)
  API_BASE: localStorage.getItem("KR_API_BASE") || "http://10.42.0.1:8080",

  // Timeout in milliseconds (FR-2: 60s for on-device inference)
  TIMEOUT_MS: 60000,

  // Default interface language ("en" or "hi")
  DEFAULT_LANG: localStorage.getItem("KR_LANG") || "en",

  // Version
  APP_VERSION: "1.0.0 (Android Native APK)"
};

window.CONFIG = CONFIG;
