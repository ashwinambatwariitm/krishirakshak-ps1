/**
 * KrishiRakshak Main Application Logic
 * 
 * Supports:
 * - Disease & Pest Detection Flow (FR-1 to FR-8)
 * - Kisan AI Chat & Quick Chips (FR-9)
 * - Offline Text-to-Speech Voice Advisor (FR-15)
 * - Field Weather & Spray Suitability Meter
 * - Bottom Navigation for Farmers
 */

document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

function initApp() {
  // Initialize language
  window.updateStaticDOMText();

  // Bottom Navigation Tabs
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => {
      const targetTab = item.getAttribute("data-tab");
      switchTab(targetTab);
    });
  });

  // Header Controls
  document.getElementById("btn-lang-toggle").addEventListener("click", () => {
    const nextLang = window.getLanguage() === "en" ? "hi" : "en";
    window.setLanguage(nextLang);
    updateWeatherUI();
  });

  document.getElementById("btn-about").addEventListener("click", () => {
    openAboutModal();
  });

  document.getElementById("btn-history").addEventListener("click", () => {
    openHistoryModal();
  });

  document.getElementById("btn-modal-close").addEventListener("click", () => {
    closeModal();
  });

  document.getElementById("btn-history-close").addEventListener("click", () => {
    closeHistoryModal();
  });

  document.getElementById("btn-clear-history").addEventListener("click", () => {
    window.appState.clearHistory();
    renderHistoryList();
  });

  // Camera & Gallery inputs
  const cameraInput = document.getElementById("camera-input");
  const galleryInput = document.getElementById("gallery-input");
  const btnCamera = document.getElementById("btn-take-photo");
  const btnGallery = document.getElementById("btn-choose-gallery");

  if (btnCamera && cameraInput) {
    btnCamera.addEventListener("click", () => cameraInput.click());
    cameraInput.addEventListener("change", (e) => handleImageSelected(e));
  }

  if (btnGallery && galleryInput) {
    btnGallery.addEventListener("click", () => galleryInput.click());
    galleryInput.addEventListener("change", (e) => handleImageSelected(e));
  }

  // Waiting screen retry
  document.getElementById("btn-retry-analysis").addEventListener("click", () => {
    if (window.appState.capturedBlob) {
      startAnalysis(window.appState.capturedBlob);
    } else {
      showView("home");
    }
  });

  document.getElementById("btn-cancel-analysis").addEventListener("click", () => {
    showView("home");
  });

  // Retake photo action
  document.getElementById("btn-retake-action").addEventListener("click", () => {
    showView("home");
    setTimeout(() => {
      if (cameraInput) cameraInput.click();
    }, 200);
  });

  // Uncertain retake action
  document.getElementById("btn-uncertain-retake").addEventListener("click", () => {
    showView("home");
    setTimeout(() => {
      if (cameraInput) cameraInput.click();
    }, 200);
  });

  // Back to home buttons
  document.querySelectorAll(".btn-home-back").forEach(btn => {
    btn.addEventListener("click", () => {
      if (window.voiceAdvisor) window.voiceAdvisor.stop();
      showView("home");
    });
  });

  // Kisan AI / Follow-up Q&A ask button & chips
  const btnAsk = document.getElementById("btn-ask");
  const inputQuestion = document.getElementById("input-question");
  if (btnAsk && inputQuestion) {
    btnAsk.addEventListener("click", () => handleAskQuestion());
    inputQuestion.addEventListener("keydown", (e) => {
      if (e.key === "Enter") handleAskQuestion();
    });
  }

  // Clickable prompt suggestion chips
  document.querySelectorAll(".chip-btn").forEach(chip => {
    chip.addEventListener("click", () => {
      const query = chip.getAttribute("data-query");
      if (inputQuestion) {
        inputQuestion.value = query;
        handleAskQuestion();
      }
    });
  });

  // Voice Read-Aloud (Text-to-Speech) Listeners (FR-15)
  const btnVoiceDiag = document.getElementById("btn-voice-diagnosis");
  if (btnVoiceDiag) {
    btnVoiceDiag.addEventListener("click", () => {
      const res = window.appState.analysisResult;
      if (!res || !res.disease) return;
      const lang = window.getLanguage();
      let textToRead = "";
      if (lang === "hi") {
        textToRead = `जांच परिणाम: ${res.disease.name}। मॉडल सटीकता: ${Math.round((res.disease.top[0]?.probability || 0.9) * 100)} प्रतिशत।`;
        if (res.disease.urgent) textToRead += " ध्यान दें: तत्काल कार्रवाई करें।";
      } else {
        textToRead = `Diagnosis Result: ${res.disease.name}. Model confidence: ${Math.round((res.disease.top[0]?.probability || 0.9) * 100)} percent.`;
        if (res.disease.urgent) textToRead += " Urgent: act today.";
      }
      window.voiceAdvisor.toggle(textToRead, lang, btnVoiceDiag);
    });
  }

  const btnVoiceLlama = document.getElementById("btn-voice-llama");
  if (btnVoiceLlama) {
    btnVoiceLlama.addEventListener("click", () => {
      const res = window.appState.analysisResult;
      if (!res || !res.llama || !res.llama.text) return;
      const lang = window.getLanguage();
      window.voiceAdvisor.toggle(res.llama.text, lang, btnVoiceLlama);
    });
  }

  const btnVoiceAi = document.getElementById("btn-voice-ai-answer");
  if (btnVoiceAi) {
    btnVoiceAi.addEventListener("click", () => {
      const ansEl = document.getElementById("qa-answer-text");
      if (!ansEl || !ansEl.textContent) return;
      const lang = window.getLanguage();
      window.voiceAdvisor.toggle(ansEl.textContent, lang, btnVoiceAi);
    });
  }

  // Developer mock selector (if testing with query parameter ?example=...)
  const urlParams = new URLSearchParams(window.location.search);
  const mockParam = urlParams.get("example");
  if (mockParam) {
    window.appState.mockExample = mockParam;
  }

  // Initialize weather assessment
  updateWeatherUI();

  // Register Service Worker for offline PWA
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  }

  // Warm up /api/info
  window.apiService.getInfo().catch(() => {});
}

/**
 * Switch bottom navigation tabs
 */
function switchTab(tabName) {
  if (window.voiceAdvisor) window.voiceAdvisor.stop();

  document.querySelectorAll(".nav-item").forEach(item => {
    if (item.getAttribute("data-tab") === tabName) {
      item.classList.add("active");
    } else {
      item.classList.remove("active");
    }
  });

  const tabs = ["scan", "ai", "weather", "guide"];
  tabs.forEach(t => {
    const el = document.getElementById(`tab-${t}-content`);
    if (el) {
      if (t === tabName) {
        el.classList.remove("hidden");
      } else {
        el.classList.add("hidden");
      }
    }
  });

  window.scrollTo({ top: 0, behavior: "smooth" });
}

/**
 * Switch view within Scan tab
 */
function showView(viewName) {
  switchTab("scan");
  const views = ["home", "waiting", "result", "uncertain", "retake"];
  views.forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) {
      if (v === viewName) {
        el.classList.remove("hidden");
      } else {
        el.classList.add("hidden");
      }
    }
  });

  window.appState.currentView = viewName;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

/**
 * Handle image file selection
 */
function handleImageSelected(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;

  event.target.value = "";
  window.appState.setCapturedImage(file);
  startAnalysis(file);
}

/**
 * Start analysis request with waiting screen
 */
async function startAnalysis(blob) {
  showView("waiting");

  const thumb = document.getElementById("waiting-photo-thumb");
  if (thumb && window.appState.capturedUrl) {
    thumb.src = window.appState.capturedUrl;
  }

  document.getElementById("waiting-progress").classList.remove("hidden");
  document.getElementById("waiting-error-box").classList.add("hidden");

  const lang = window.getLanguage();

  try {
    const data = await window.apiService.analyseImage(blob, lang, window.appState.mockExample);
    window.appState.setResult(data);
    routeResultStatus(data);
  } catch (err) {
    console.error("Analysis error:", err);
    document.getElementById("waiting-progress").classList.add("hidden");
    const errorBox = document.getElementById("waiting-error-box");
    const errorMsg = document.getElementById("waiting-error-msg");
    errorBox.classList.remove("hidden");

    if (err.isTimeout) {
      errorMsg.textContent = window.t("timeout_error");
    } else {
      errorMsg.textContent = window.t("device_error");
    }
  }
}

/**
 * Route result based on status field: answered, uncertain, or retake_photo
 */
function routeResultStatus(data) {
  const status = data.status || "uncertain";

  if (status === "answered") {
    renderAnsweredScreen(data);
    showView("result");
  } else if (status === "retake_photo") {
    renderRetakeScreen(data);
    showView("retake");
  } else {
    renderUncertainScreen(data);
    showView("uncertain");
  }
}

/**
 * Render Status: answered Screen
 */
function renderAnsweredScreen(data) {
  // 1. Photo with pest bounding boxes canvas (FR-13)
  const canvas = document.getElementById("result-photo-canvas");
  if (canvas && window.appState.capturedUrl) {
    window.PestCanvas.render(canvas, window.appState.capturedUrl, data.pests || []);
  }

  // 2. Result Header (FR-4)
  const disease = data.disease || {};
  const diseaseNameEl = document.getElementById("res-disease-name");
  const confidenceEl = document.getElementById("res-confidence");
  const urgentBadge = document.getElementById("res-urgent-badge");
  const spreadBadge = document.getElementById("res-spread-badge");
  const pestsBadge = document.getElementById("res-pests-badge");

  diseaseNameEl.textContent = disease.name || window.t("diagnosis_result");

  if (disease.top && disease.top[0] && typeof disease.top[0].probability === "number") {
    const pct = Math.round(disease.top[0].probability * 100);
    confidenceEl.textContent = `${window.t("confidence")}: ${pct}%`;
    confidenceEl.classList.remove("hidden");
  } else {
    confidenceEl.classList.add("hidden");
  }

  if (disease.urgent) {
    urgentBadge.textContent = window.t("urgent_badge");
    urgentBadge.classList.remove("hidden");
  } else {
    urgentBadge.classList.add("hidden");
  }

  if (data.severity && data.severity.level && data.severity.level !== "unknown") {
    const lvl = data.severity.level.toLowerCase();
    const localizedLvl = window.t(`spread_${lvl}`) || lvl;
    spreadBadge.textContent = `${window.t("spread_level")}: ${localizedLvl}`;
    spreadBadge.classList.remove("hidden");
  } else {
    spreadBadge.classList.add("hidden");
  }

  if (Array.isArray(data.pests) && data.pests.length > 0) {
    const pestStrings = data.pests.map(p => {
      if (p.species_reliable && p.species) {
        return `${p.name} (${p.species})`;
      }
      return p.name;
    });
    pestsBadge.textContent = `${window.t("insect_found")}: ${pestStrings.join(", ")}`;
    pestsBadge.classList.remove("hidden");
  } else {
    pestsBadge.classList.add("hidden");
  }

  // 3. Official Notices (FR-5)
  const messagesContainer = document.getElementById("res-messages-container");
  messagesContainer.innerHTML = "";
  if (Array.isArray(data.messages) && data.messages.length > 0) {
    data.messages.forEach(msg => {
      const msgCard = document.createElement("div");
      msgCard.className = "alert-note";
      msgCard.textContent = msg;
      messagesContainer.appendChild(msgCard);
    });
    messagesContainer.classList.remove("hidden");
  } else {
    messagesContainer.classList.add("hidden");
  }

  // 4. Llama Advice Card (FR-6)
  const llamaContainer = document.getElementById("res-llama-card");
  const llamaTextEl = document.getElementById("res-llama-text");
  if (data.llama && data.llama.text && data.llama.accepted !== false) {
    llamaTextEl.textContent = data.llama.text;
    llamaContainer.classList.remove("hidden");
  } else {
    llamaContainer.classList.add("hidden");
  }

  // 5. Advice Blocks (FR-7)
  const adviceContainer = document.getElementById("res-advice-blocks");
  adviceContainer.innerHTML = "";
  const sectionOrder = ["symptoms", "spread", "cultural", "mechanical", "biological", "monitoring", "safety", "general"];

  if (Array.isArray(data.advice_blocks)) {
    data.advice_blocks.forEach(block => {
      const chunks = block.chunks || [];
      const nonChemicalChunks = chunks.filter(c => c.section !== "chemical");

      if (nonChemicalChunks.length > 0) {
        const blockEl = document.createElement("div");
        blockEl.className = "card advice-card";

        if (block.name) {
          const blockTitle = document.createElement("h3");
          blockTitle.className = "advice-block-title";
          blockTitle.textContent = block.name;
          blockEl.appendChild(blockTitle);
        }

        const grouped = {};
        nonChemicalChunks.forEach(c => {
          const sec = c.section || "general";
          if (!grouped[sec]) grouped[sec] = [];
          grouped[sec].push(c);
        });

        const sortedSections = Object.keys(grouped).sort((a, b) => {
          let ia = sectionOrder.indexOf(a);
          let ib = sectionOrder.indexOf(b);
          if (ia === -1) ia = 99;
          if (ib === -1) ib = 99;
          return ia - ib;
        });

        sortedSections.forEach((sec, idx) => {
          const secWrapper = document.createElement("details");
          secWrapper.className = "advice-section-accordion";
          if (idx < 2) secWrapper.open = true;

          const summary = document.createElement("summary");
          const secTitle = window.t(`section_${sec}`) || sec.replace(/_/g, " ").toUpperCase();
          summary.textContent = secTitle;
          secWrapper.appendChild(summary);

          const listEl = document.createElement("div");
          listEl.className = "accordion-content";

          grouped[sec].forEach(chunk => {
            const item = document.createElement("div");
            item.className = "advice-chunk";

            const textSpan = document.createElement("span");
            textSpan.textContent = chunk.text + " ";
            item.appendChild(textSpan);

            if (chunk.source_org) {
              const srcBadge = document.createElement("span");
              srcBadge.className = "source-badge";
              srcBadge.textContent = `[${chunk.source_org}]`;
              if (chunk.source_title) {
                srcBadge.title = chunk.source_title;
              }
              item.appendChild(srcBadge);
            }

            listEl.appendChild(item);
          });

          secWrapper.appendChild(listEl);
          blockEl.appendChild(secWrapper);
        });

        adviceContainer.appendChild(blockEl);
      }
    });
  }

  // 6. Chemical Spray Options Table (FR-8)
  const sprayContainer = document.getElementById("res-spray-container");
  const sprayTbody = document.getElementById("res-spray-tbody");
  sprayTbody.innerHTML = "";

  const allSprays = [];
  if (Array.isArray(data.advice_blocks)) {
    data.advice_blocks.forEach(block => {
      (block.chunks || []).forEach(c => {
        if (c.section === "chemical") allSprays.push(c);
      });
    });
  }

  if (allSprays.length > 0) {
    allSprays.forEach(spray => {
      const tr = document.createElement("tr");

      const tdProd = document.createElement("td");
      const prodName = document.createElement("strong");
      prodName.textContent = spray.product || "";
      tdProd.appendChild(prodName);

      if (spray.note) {
        const noteDiv = document.createElement("div");
        noteDiv.className = "table-note";
        noteDiv.textContent = spray.note;
        tdProd.appendChild(noteDiv);
      }

      const tdDose = document.createElement("td");
      tdDose.textContent = spray.dose || "—";

      const tdSrc = document.createElement("td");
      tdSrc.className = "source-cell";
      tdSrc.textContent = spray.source_org || "";

      tr.appendChild(tdProd);
      tr.appendChild(tdDose);
      tr.appendChild(tdSrc);
      sprayTbody.appendChild(tr);
    });
    sprayContainer.classList.remove("hidden");
  } else {
    sprayContainer.classList.add("hidden");
  }

  // Technical Details Drawer (FR-12)
  renderTechnicalDetails(data);
}

/**
 * Handle Follow-up Question in Kisan AI Tab (FR-9)
 */
async function handleAskQuestion() {
  const inputEl = document.getElementById("input-question");
  const question = inputEl.value.trim();
  if (!question) return;

  const loadingEl = document.getElementById("qa-loading");
  const resContainer = document.getElementById("qa-response-container");
  const answerEl = document.getElementById("qa-answer-text");
  const factsContainer = document.getElementById("qa-facts-list");
  const fallbackNotice = document.getElementById("qa-rejected-notice");

  loadingEl.classList.remove("hidden");
  resContainer.classList.add("hidden");
  fallbackNotice.classList.add("hidden");
  factsContainer.innerHTML = "";

  const topic = window.appState.lastTopic;
  const lang = window.getLanguage();

  try {
    const res = await window.apiService.askQuestion(question, topic, lang);
    loadingEl.classList.add("hidden");
    resContainer.classList.remove("hidden");

    if (res.answer && res.accepted !== false) {
      answerEl.textContent = res.answer;
      answerEl.parentElement.classList.remove("hidden");
      fallbackNotice.classList.add("hidden");
    } else {
      answerEl.parentElement.classList.add("hidden");
      fallbackNotice.classList.remove("hidden");
    }

    if (Array.isArray(res.facts) && res.facts.length > 0) {
      res.facts.forEach(fact => {
        const factItem = document.createElement("div");
        factItem.className = "fact-item";

        const textSpan = document.createElement("span");
        textSpan.textContent = fact.text + " ";
        factItem.appendChild(textSpan);

        if (fact.source_org) {
          const srcBadge = document.createElement("span");
          srcBadge.className = "source-badge";
          srcBadge.textContent = `[${fact.source_org}]`;
          factItem.appendChild(srcBadge);
        }

        factsContainer.appendChild(factItem);
      });
      document.getElementById("qa-facts-wrapper").classList.remove("hidden");
    } else {
      document.getElementById("qa-facts-wrapper").classList.add("hidden");
    }

  } catch (err) {
    loadingEl.classList.add("hidden");
    alert("Could not get answer: " + err.message);
  }
}

/**
 * Update Weather & Spray Suitability UI
 */
function updateWeatherUI() {
  if (!window.fieldWeather) return;

  const evaluation = window.fieldWeather.evaluateSprayConditions();
  const banner = document.getElementById("spray-status-banner");
  const statusText = document.getElementById("spray-status-text");
  const issuesBox = document.getElementById("spray-issues-box");

  if (!banner || !statusText || !issuesBox) return;

  const lang = window.getLanguage();

  if (evaluation.isFavorable) {
    banner.className = "spray-meter-banner favorable";
    statusText.textContent = window.t("spray_favorable");
    issuesBox.innerHTML = "";
  } else {
    banner.className = "spray-meter-banner unfavorable";
    statusText.textContent = window.t("spray_unfavorable");
    issuesBox.innerHTML = "";
    evaluation.issues.forEach(issue => {
      const p = document.createElement("div");
      p.className = "alert-note";
      p.textContent = lang === "hi" ? issue.hi : issue.en;
      issuesBox.appendChild(p);
    });
  }
}

/**
 * Render Status: uncertain Screen
 */
function renderUncertainScreen(data) {
  const msgContainer = document.getElementById("uncertain-messages");
  msgContainer.innerHTML = "";

  const messages = data.messages || [];
  if (messages.length > 0) {
    messages.forEach(m => {
      const p = document.createElement("div");
      p.className = "alert-note";
      p.textContent = m;
      msgContainer.appendChild(p);
    });
  } else {
    const defMsg = document.createElement("div");
    defMsg.className = "alert-note";
    defMsg.textContent = window.t("uncertain_tip_1");
    msgContainer.appendChild(defMsg);
  }
}

/**
 * Render Status: retake_photo Screen
 */
function renderRetakeScreen(data) {
  const issuesContainer = document.getElementById("retake-issues-list");
  issuesContainer.innerHTML = "";

  const messages = data.messages || [];
  if (messages.length > 0) {
    messages.forEach(m => {
      const li = document.createElement("li");
      li.className = "alert-note";
      li.textContent = m;
      issuesContainer.appendChild(li);
    });
  } else if (data.quality && Array.isArray(data.quality.issues)) {
    data.quality.issues.forEach(issue => {
      const li = document.createElement("li");
      li.className = "alert-note";
      li.textContent = window.t(`issue_${issue}`) || issue;
      issuesContainer.appendChild(li);
    });
  }
}

/**
 * Render Technical Details Drawer (FR-12)
 */
function renderTechnicalDetails(data) {
  const pre = document.getElementById("tech-details-json");
  if (!pre) return;

  const timings = data.timings_ms || {};
  const stats = (data.llama && data.llama.stats) || {};

  const summary = {
    timings_ms: {
      total: timings.total ? `${Math.round(timings.total)} ms` : undefined,
      disease_classifier: timings.disease ? `${Math.round(timings.disease)} ms` : undefined,
      pest_detector: timings.pest ? `${Math.round(timings.pest)} ms` : undefined,
      llama_executorch: timings.llama ? `${Math.round(timings.llama)} ms` : undefined,
      quality_check: timings.quality ? `${Math.round(timings.quality)} ms` : undefined
    },
    llama_stats: {
      tokens_per_second: stats.tokens_per_s ? stats.tokens_per_s.toFixed(2) : undefined,
      generated_tokens: stats.generated_tokens,
      prompt_tokens: stats.prompt_tokens,
      time_to_first_token_s: stats.time_to_first_token_s
    }
  };

  pre.textContent = JSON.stringify(summary, null, 2);
}

/**
 * About Modal
 */
async function openAboutModal() {
  const modal = document.getElementById("about-modal");
  modal.classList.remove("hidden");

  const inputBase = document.getElementById("setting-api-base");
  if (inputBase) {
    inputBase.value = window.apiService.getBaseUrl();
  }

  const saveBtn = document.getElementById("btn-save-setting");
  if (saveBtn) {
    saveBtn.onclick = () => {
      window.apiService.setBaseUrl(inputBase.value.trim());
      alert("API Base Address Saved.");
      closeModal();
    };
  }

  try {
    const info = await window.apiService.getInfo();
    document.getElementById("info-disease-model").textContent = info.disease_model || "—";
    document.getElementById("info-pest-model").textContent = info.pest_model || "—";
    document.getElementById("info-llama-model").textContent = info.llama || "—";
    
    const kbText = `${info.kb_version || "tomato_kb"} (${info.kb_reviewed ? window.t("kb_reviewed") : window.t("kb_draft")})`;
    document.getElementById("info-kb-version").textContent = kbText;
    document.getElementById("info-runtime").textContent = `${info.runtime || "C++"} on Arm (ExecuTorch)`;
  } catch (err) {
    console.warn("Could not fetch /api/info:", err);
  }
}

function closeModal() {
  document.getElementById("about-modal").classList.add("hidden");
}

/**
 * History Modal
 */
function openHistoryModal() {
  document.getElementById("history-modal").classList.remove("hidden");
  renderHistoryList();
}

function closeHistoryModal() {
  document.getElementById("history-modal").classList.add("hidden");
}

function renderHistoryList() {
  const container = document.getElementById("history-items-container");
  container.innerHTML = "";

  const history = window.appState.getHistory();
  if (history.length === 0) {
    const emptyP = document.createElement("p");
    emptyP.className = "muted text-center";
    emptyP.textContent = window.t("no_history");
    container.appendChild(emptyP);
    return;
  }

  history.forEach(item => {
    const row = document.createElement("div");
    row.style.padding = "10px";
    row.style.borderBottom = "1px solid var(--line-border)";
    row.style.display = "flex";
    row.style.justifyContent = "space-between";
    row.style.alignItems = "center";

    const titleDiv = document.createElement("div");
    titleDiv.style.fontWeight = "700";
    titleDiv.style.color = "var(--primary-dark)";
    titleDiv.textContent = item.diseaseName;

    const metaDiv = document.createElement("div");
    metaDiv.style.fontSize = "0.85rem";
    metaDiv.style.color = "var(--ink-muted)";
    const date = new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const conf = Math.round(item.confidence * 100);
    metaDiv.textContent = `${date} • ${window.t("confidence")}: ${conf}%`;

    row.appendChild(titleDiv);
    row.appendChild(metaDiv);
    container.appendChild(row);
  });
}
