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

  // Header Controls (the language is chosen with the "Advice also in" picker on the home screen)

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
      if (window.appState.viewingEnglish) {   // leave the English view: back to the chosen language
        window.appState.viewingEnglish = false;
        window.setLanguage(window.CONFIG.TRANSLATE_LANG || "en");
      }
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

  // Speech-to-Text Microphone for Kisan AI
  setupSpeechToText();

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
      const diagName = getLocalizedDiseaseName(res.disease);
      const pct = Math.round((res.disease.top && res.disease.top[0]?.probability ? res.disease.top[0].probability : 0.9) * 100);
      const english = `Diagnosis Result: ${res.disease.name || diagName}. Model confidence: ${pct} percent.` +
                      (res.disease.urgent ? " Urgent: act today." : "");
      const textToRead = `${window.t("diagnosis_result")}: ${diagName}. ${window.t("confidence")}: ${pct}%.` +
                         (res.disease.urgent ? ` ${window.t("urgent_badge")}.` : "");
      window.voiceAdvisor.toggle(textToRead, lang, btnVoiceDiag, english);
    });
  }

  const btnVoiceLlama = document.getElementById("btn-voice-llama");
  if (btnVoiceLlama) {
    btnVoiceLlama.addEventListener("click", () => {
      const res = window.appState.analysisResult;
      if (!res) return;
      const lang = window.getLanguage();
      const tr = window.appState.viewingEnglish ? null : res.translation;
      const trText = tr ? (tr.text || (Array.isArray(tr.sentences) ? tr.sentences.join(" ") : "")) : "";
      if (trText) {
        window.voiceAdvisor.toggle(trText, tr.lang || lang, btnVoiceLlama, res.llama?.text);
      } else if (res.llama && res.llama.text) {
        window.voiceAdvisor.toggle(res.llama.text, "en", btnVoiceLlama);
      } else {
        const adviceText = getVerifiedAdviceText(res);
        if (adviceText) {
          window.voiceAdvisor.toggle(adviceText, lang, btnVoiceLlama, getVerifiedAdviceEnglish(res));
        }
      }
    });
  }

  const btnVoiceAdvice = document.getElementById("btn-voice-advice");
  if (btnVoiceAdvice) {
    btnVoiceAdvice.addEventListener("click", () => {
      const res = window.appState.analysisResult;
      if (!res) return;
      const adviceText = getVerifiedAdviceText(res);
      if (!adviceText) return;
      const lang = window.getLanguage();
      window.voiceAdvisor.toggle(adviceText, lang, btnVoiceAdvice, getVerifiedAdviceEnglish(res));
    });
  }

  const btnVoiceAi = document.getElementById("btn-voice-ai-answer");
  if (btnVoiceAi) {
    btnVoiceAi.addEventListener("click", () => {
      const ansEl = document.getElementById("qa-answer-text");
      if (!ansEl || !ansEl.textContent) return;
      const lang = window.getLanguage();
      const tr = window.appState.lastAnswerTranslation;
      const trText = tr ? (tr.text || (Array.isArray(tr.sentences) ? tr.sentences.join(" ") : "")) : "";
      if (trText) {
        window.voiceAdvisor.toggle(trText, tr.lang || lang, btnVoiceAi, ansEl.textContent);
      } else {
        window.voiceAdvisor.toggle(ansEl.textContent, "en", btnVoiceAi);
      }
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

  // Warm up /api/info; also shows the "Advice also in" picker when the device has the translator
  setupTranslatePicker();
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

  // The device always runs the advice in English (Llama and its checks) and translates it into the chosen language
  const lang = "en";

  try {
    const data = await window.apiService.analyseImage(blob, lang, window.appState.mockExample,
                                                      window.CONFIG.TRANSLATE_LANG || "");
    window.appState.setResult(data);
    window.appState.viewingEnglish = false;
    routeResultStatus(data);
    updateResultLanguageButton();
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
 * Localized disease name from topic or translation
 */
function getLocalizedDiseaseName(disease) {
  if (!disease) return window.t("diagnosis_result");
  const topic = disease.topic || "";
  if (topic) {
    const locTopic = window.t("topic_" + topic);
    if (locTopic && locTopic !== "topic_" + topic) return locTopic;
    const locDirect = window.t(topic);
    if (locDirect && locDirect !== topic) return locDirect;
  }
  return disease.name || window.t("diagnosis_result");
}

/**
 * Build verified advice text from official advice blocks (FR-7)
 */
function getVerifiedAdviceText(data) {
  if (!data || !Array.isArray(data.advice_blocks)) return "";
  const texts = [];
  data.advice_blocks.forEach(block => {
    if (block.name) texts.push(block.name);
    const chunks = (block.chunks || []).filter(c => c.section !== "chemical");
    chunks.forEach(c => {
      if (c && c.text) texts.push(c.text);
    });
  });
  return texts.join(". ");
}

/**
 * Build English fallback text for verified advice blocks
 */
function getVerifiedAdviceEnglish(data) {
  if (!data || !Array.isArray(data.advice_blocks)) return "";
  const texts = [];
  data.advice_blocks.forEach(block => {
    const chunks = (block.chunks || []).filter(c => c.section !== "chemical");
    chunks.forEach(c => {
      if (c) texts.push(c.text_en || c.text || "");
    });
  });
  return texts.join(". ");
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

  diseaseNameEl.textContent = getLocalizedDiseaseName(disease);

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

  // Disease spread is shown only from a validated method: the earlier colour estimate is sent with
  // validated=false (it matched the expert level in 31% of field photos, results/severity_plantseg/README.md)
  if (data.severity && data.severity.validated === true && data.severity.level && data.severity.level !== "unknown") {
    const lvl = data.severity.level.toLowerCase();
    const localizedLvl = window.t(`spread_${lvl}`) || lvl;
    spreadBadge.textContent = `${window.t("spread_level")}: ${localizedLvl}`;
    spreadBadge.classList.remove("hidden");
  } else {
    spreadBadge.classList.add("hidden");
  }

  if (Array.isArray(data.pests) && data.pests.length > 0) {
    // One entry per insect type with a count ("Aphids x 3"); the species is added only when the name does not
    // already contain it (the name is often "Aphids (Aphids)" style already)
    const counts = new Map();
    data.pests.forEach(p => {
      let label = p.name || "";
      if (p.species_reliable && p.species && !label.toLowerCase().includes(String(p.species).toLowerCase()))
        label = `${label} (${p.species})`;
      counts.set(label, (counts.get(label) || 0) + 1);
    });
    const pestStrings = [...counts].map(([label, n]) => (n > 1 ? `${label} \u00d7 ${n}` : label));
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

  // 3a. Disease severity of the photographed leaf
  renderDiseaseSeverity(document.getElementById("res-disease-severity"), data.severity, disease);

  // 3b. Pest severity (level for this photo only, with the published scouting method)
  renderPestSeverity(document.getElementById("res-pest-severity"), data.pest_severity);

  // 4. Llama Advice Card (FR-6)
  const llamaContainer = document.getElementById("res-llama-card");
  const llamaTextEl = document.getElementById("res-llama-text");
  const hasLlama = data.llama && data.llama.text && data.llama.accepted !== false;
  if (hasLlama) {
    llamaTextEl.textContent = data.llama.text;
    llamaContainer.classList.remove("hidden");
  } else {
    llamaContainer.classList.add("hidden");
  }
  renderTranslation(document.getElementById("res-llama-translation"), data.translation, llamaTextEl);
  // A translation was asked for, but the AI explanation did not pass the device's safety check (only checked
  // text is translated): say so instead of showing nothing
  const mtNote = document.getElementById("res-mt-unavailable");
  const llamaRejected = data.llama && (data.llama.accepted === false || !data.llama.text);
  if (mtNote) mtNote.classList.toggle("hidden", !(window.CONFIG.TRANSLATE_LANG && llamaRejected));

  const btnVoiceAdvice = document.getElementById("btn-voice-advice");
  if (btnVoiceAdvice) {
    const hasAdvice = Array.isArray(data.advice_blocks) && data.advice_blocks.some(b => (b.chunks || []).length > 0);
    btnVoiceAdvice.classList.toggle("hidden", !(hasAdvice && !hasLlama));
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
        // Extracts shown from the knowledge-base translations (machine translation, not yet reviewed)
        const translated = nonChemicalChunks.filter(c => c.text_en && c.text !== c.text_en);
        if (translated.length > 0) {
          const mtNote = document.createElement("div");
          mtNote.className = "translation-label";
          mtNote.textContent = window.t("kb_mt_note");
          blockEl.appendChild(mtNote);
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

        if (translated.length > 0) {   // the published English, one tap away
          const original = document.createElement("details");
          original.className = "translation-original";
          const summary = document.createElement("summary");
          summary.textContent = window.t("mt_show_english");
          original.appendChild(summary);
          nonChemicalChunks.forEach(c => {
            const p = document.createElement("p");
            p.textContent = `${c.text_en || c.text} [${c.source_org || ""}]`;
            original.appendChild(p);
          });
          blockEl.appendChild(original);
        }

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
      tdDose.textContent = spray.dose || "\u2014";

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
  const lang = "en";   // see startAnalysis

  try {
    const res = await window.apiService.askQuestion(question, topic, lang, window.CONFIG.TRANSLATE_LANG || "");
    loadingEl.classList.add("hidden");
    resContainer.classList.remove("hidden");

    let qaTranslation = document.getElementById("qa-answer-translation");
    if (!qaTranslation) {
      qaTranslation = document.createElement("div");
      qaTranslation.id = "qa-answer-translation";
      qaTranslation.className = "translation-block hidden";
      answerEl.insertAdjacentElement("afterend", qaTranslation);
    }
    if (res.answer && res.accepted !== false) {
      answerEl.textContent = res.answer;
      renderTranslation(qaTranslation, res.translation, answerEl);
    } else {
      renderTranslation(qaTranslation, null, answerEl);
    }
    window.appState.lastAnswerTranslation = res.accepted !== false ? res.translation : null;

    if (res.answer && res.accepted !== false) {
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
    document.getElementById("info-disease-model").textContent = info.disease_model || "\u2014";
    document.getElementById("info-pest-model").textContent = info.pest_model || "\u2014";
    document.getElementById("info-llama-model").textContent = info.llama || "\u2014";
    
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
    metaDiv.textContent = `${date} \u2022 ${window.t("confidence")}: ${conf}%`;

    row.appendChild(titleDiv);
    row.appendChild(metaDiv);
    container.appendChild(row);
  });
}


/**
 * Machine translation of the checked English advice (device field "translation"), shown under the English text
 * and marked as not reviewed. Sentences that failed the device's translation check stay in English.
 */
function renderTranslation(container, tr, englishEl) {
  if (!container) return;
  container.innerHTML = "";
  if (englishEl) englishEl.classList.remove("hidden");
  if (!tr) {
    container.classList.add("hidden");
    return;
  }
  const text = tr.text || (Array.isArray(tr.sentences) ? tr.sentences.join(" ") : "");
  if (!text) {
    container.classList.add("hidden");
    return;
  }
  const label = document.createElement("div");
  label.className = "translation-label";
  label.textContent = window.t("mt_title");
  const body = document.createElement("p");
  body.className = "translation-text";
  body.lang = tr.lang || "";
  body.textContent = text;
  container.appendChild(label);
  container.appendChild(body);
  if (tr.withheld) {
    const note = document.createElement("div");
    note.className = "translation-note";
    note.textContent = window.t("mt_withheld");
    container.appendChild(note);
  }
  // The translation replaces the English text on screen; the English stays one tap away (the translation is not
  // yet reviewed, so a helper or extension worker can check it)
  if (englishEl && englishEl.textContent) {
    const original = document.createElement("details");
    original.className = "translation-original";
    const summary = document.createElement("summary");
    summary.textContent = window.t("mt_show_english");
    const en = document.createElement("p");
    en.textContent = englishEl.textContent;
    original.appendChild(summary);
    original.appendChild(en);
    container.appendChild(original);
    englishEl.classList.add("hidden");
  }
  container.classList.remove("hidden");
}

/**
 * Pest severity (device field "pest_severity"): one row per pest found in the photo with its count and level for
 * this photo only, the published economic threshold where one exists, and the published way to check the field.
 */
function renderPestSeverity(container, rows) {
  if (!container) return;
  container.innerHTML = "";
  if (!Array.isArray(rows) || rows.length === 0) {
    container.classList.add("hidden");
    return;
  }
  const title = document.createElement("h3");
  title.textContent = window.t("pest_sev_title");
  container.appendChild(title);
  rows.forEach(r => {
    const row = document.createElement("div");
    row.className = "pest-sev-row";
    const head = document.createElement("div");
    head.className = "pest-sev-head";
    const name = document.createElement("strong");
    name.textContent = `${r.name}: ${r.count}`;
    const badge = document.createElement("span");
    badge.className = `tag-badge pest-level-${r.level}`;
    badge.textContent = window.t(`level_${r.level}`) || r.level;
    head.appendChild(name);
    head.appendChild(badge);
    row.appendChild(head);
    const basis = document.createElement("div");
    basis.className = "pest-sev-note";
    basis.textContent = window.t("pest_sev_photo_only") + (r.group === "uncertain" ? " " + window.t("pest_sev_uncertain") : "");
    row.appendChild(basis);
    if (r.threshold && r.threshold.text) {
      const thr = document.createElement("div");
      thr.className = "alert-note";
      thr.textContent = `${window.t("pest_threshold")}: ${r.threshold.text} [${r.threshold.source_org}]`;
      row.appendChild(thr);
    }
    if (r.scouting && r.scouting.text) {
      const sc = document.createElement("div");
      sc.className = "pest-sev-scouting";
      sc.textContent = `${window.t("pest_scouting")}: ${r.scouting.text} [${r.scouting.source_org}]`;
      row.appendChild(sc);
    }
    container.appendChild(row);
  });
  container.classList.remove("hidden");
}

/**
 * Single unified language picker in header.
 */
async function setupTranslatePicker() {
  const select = document.getElementById("select-translate");
  if (!select) return;
  select.value = window.CONFIG.TRANSLATE_LANG || "";
  // One language choice for the whole app: labels, advice and the verified practices in the chosen language
  const applyInterfaceLanguage = () => {
    window.setLanguage(select.value || "en");   // labels in the chosen language (English where one is missing)
    if (typeof updateWeatherUI === "function") updateWeatherUI();
    updateResultLanguageButton();
  };
  select.addEventListener("change", () => {
    window.CONFIG.TRANSLATE_LANG = select.value;
    localStorage.setItem("KR_TRANSLATE", select.value);
    applyInterfaceLanguage();
  });
  applyInterfaceLanguage();
  try {
    const info = await window.apiService.getInfo();
    const langs = (info && info.translation_languages) || [];
    if (langs.length > 0) {
      Array.from(select.options).forEach(o => { o.hidden = o.value !== "" && !langs.includes(o.value); });
    }
  } catch (e) {
    // Keep language picker accessible for offline interface
  }
}


/**
 * Disease severity (device field "severity"): level of the photographed leaf from the share of the leaf area with
 * disease, measured by the segmentation model on the Pi. Shown only from the validated model ("validated": true);
 * virus diseases get "not_applicable" (their symptoms are curling and mottling, not lesion areas).
 */
function renderDiseaseSeverity(container, sev, disease) {
  if (!container) return;
  container.innerHTML = "";
  const show = sev && ((sev.validated === true && sev.level && sev.level !== "unknown") ||
                       sev.level === "not_applicable");
  if (!show || !disease || !disease.answered) {
    container.classList.add("hidden");
    return;
  }
  const title = document.createElement("h3");
  title.textContent = window.t("sev_title");
  container.appendChild(title);
  if (sev.level === "not_applicable") {
    const p = document.createElement("p");
    p.textContent = window.t("sev_not_applicable");
    container.appendChild(p);
  } else {
    const head = document.createElement("div");
    head.className = "pest-sev-head";
    const badge = document.createElement("span");
    badge.className = `tag-badge pest-level-${sev.level}`;
    badge.textContent = window.t(`level_${sev.level}`) || sev.level;
    head.appendChild(badge);
    if (typeof sev.lesion_share === "number") {
      const pct = document.createElement("strong");
      pct.textContent = window.t("sev_share").replace("{pct}", Math.round(sev.lesion_share * 100));
      head.appendChild(pct);
    }
    container.appendChild(head);
    if (typeof sev.lesion_share === "number") {
      const bar = document.createElement("div");
      bar.className = "sev-bar";
      const fill = document.createElement("div");
      fill.className = `sev-bar-fill pest-level-${sev.level}`;
      fill.style.width = `${Math.min(100, Math.round(sev.lesion_share * 100))}%`;
      bar.appendChild(fill);
      container.appendChild(bar);
    }
    const scale = document.createElement("div");
    scale.className = "pest-sev-note";
    scale.textContent = window.t("sev_scale");
    container.appendChild(scale);
  }
  if (sev.level !== "not_applicable") {
    const note = document.createElement("div");
    note.className = "pest-sev-note";
    note.textContent = window.t("sev_note");
    container.appendChild(note);
  }
  container.classList.remove("hidden");
}


/**
 * Result language switch (top right of the result screen): the chosen language <-> English, without analysing the
 * photo again. The device sends the English of every translated text in data.en (and Llama's English in
 * llama.text), so the result is only drawn again.
 */
function englishView(data) {
  const v = JSON.parse(JSON.stringify(data));
  const en = data.en || {};
  v.translation = null;                        // Llama's English text is shown
  v.display_lang = "en";
  if (v.disease && en.disease_name) v.disease.name = en.disease_name;
  if (Array.isArray(v.pests) && Array.isArray(en.pest_names)) v.pests.forEach((p, i) => { p.name = en.pest_names[i] || p.name; });
  if (en.messages) v.messages = en.messages;
  if (en.advice_blocks) v.advice_blocks = en.advice_blocks;
  if (en.pest_severity) v.pest_severity = en.pest_severity;
  return v;
}

function languageLabel(code) {
  const opt = Array.from(document.querySelectorAll("#select-translate option")).find(o => o.value === code);
  return opt ? opt.textContent.split(" (")[0] : code;     // e.g. the native name of the chosen language
}

function updateResultLanguageButton() {
  const btn = document.getElementById("btn-result-lang");
  const data = window.appState.analysisResult;
  const chosen = window.CONFIG.TRANSLATE_LANG || "";
  if (!btn) return;
  const available = data && chosen && data.display_lang && data.display_lang !== "en";
  btn.classList.toggle("hidden", !available);
  if (available) btn.textContent = window.appState.viewingEnglish ? languageLabel(chosen) : "English";
}

function toggleResultLanguage() {
  const data = window.appState.analysisResult;
  const chosen = window.CONFIG.TRANSLATE_LANG || "";
  if (!data || !chosen) return;
  if (window.voiceAdvisor) window.voiceAdvisor.stop();
  window.appState.viewingEnglish = !window.appState.viewingEnglish;
  window.setLanguage(window.appState.viewingEnglish ? "en" : chosen);      // interface labels too
  renderAnsweredScreen(window.appState.viewingEnglish ? englishView(data) : data);
  updateResultLanguageButton();
}

document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("btn-result-lang");
  if (btn) btn.addEventListener("click", toggleResultLanguage);
});

/**
 * Speech-to-Text for Kisan AI Voice Questions
 * Supports:
 * Strategy 1: Android native SpeechRecognizer bridge (window.AndroidSTT, 100% offline with on-device speech model)
 * Strategy 2: Web Speech API (window.SpeechRecognition || window.webkitSpeechRecognition)
 */
function setupSpeechToText() {
  const btnMic = document.getElementById("btn-mic-question");
  const inputQuestion = document.getElementById("input-question");
  const micHint = document.getElementById("mic-status-hint");
  if (!btnMic || !inputQuestion) return;

  let recognition = null;
  let isListening = false;

  const notifyToast = (msg) => {
    if (window.voiceAdvisor && typeof window.voiceAdvisor.notify === "function") {
      window.voiceAdvisor.notify(msg);
    } else {
      let el = document.getElementById("kr-toast");
      if (!el) {
        el = document.createElement("div");
        el.id = "kr-toast";
        el.className = "kr-toast";
        document.body.appendChild(el);
      }
      el.textContent = msg;
      el.classList.add("show");
      setTimeout(() => el.classList.remove("show"), 5000);
    }
  };

  const stopListeningUI = () => {
    isListening = false;
    btnMic.classList.remove("listening");
    if (micHint) micHint.classList.add("hidden");
  };

  const startListeningUI = () => {
    isListening = true;
    btnMic.classList.add("listening");
    if (micHint) {
      micHint.textContent = window.t("mic_listening") || "Listening... Speak now";
      micHint.classList.remove("hidden");
    }
  };

  // Callback exposed to Android Native STT Bridge
  window.onSpeechResult = (text) => {
    stopListeningUI();
    if (text && text.trim()) {
      inputQuestion.value = text.trim();
      inputQuestion.focus();
    }
  };

  window.onSpeechError = (err) => {
    stopListeningUI();
    if (err !== "cancelled" && err !== "no_match") {
      notifyToast(window.t("mic_error") || "Voice input could not recognize speech.");
    }
  };

  btnMic.addEventListener("click", () => {
    if (isListening) {
      if (recognition) {
        try { recognition.stop(); } catch (e) {}
      }
      stopListeningUI();
      return;
    }

    const lang = window.getLanguage() || "en";

    // Strategy 1: Android native STT Bridge
    if (window.AndroidSTT && typeof window.AndroidSTT.startListening === "function") {
      startListeningUI();
      try {
        window.AndroidSTT.startListening(lang);
      } catch (err) {
        stopListeningUI();
        console.warn("AndroidSTT bridge error:", err);
      }
      return;
    }

    // Strategy 2: Web Speech API (Chrome / Edge / Android WebView)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        const localeMap = {
          en: "en-IN",
          hi: "hi-IN",
          mr: "mr-IN",
          te: "te-IN",
          ta: "ta-IN",
          kn: "kn-IN",
          bn: "bn-IN",
          gu: "gu-IN",
          pa: "pa-IN",
          or: "or-IN"
        };
        recognition.lang = localeMap[lang] || "en-IN";

        recognition.onstart = () => {
          startListeningUI();
        };

        recognition.onresult = (event) => {
          stopListeningUI();
          if (event.results && event.results[0] && event.results[0][0]) {
            const transcript = event.results[0][0].transcript;
            if (transcript) {
              inputQuestion.value = transcript.trim();
              inputQuestion.focus();
            }
          }
        };

        recognition.onerror = (event) => {
          stopListeningUI();
          if (event.error !== "no-speech") {
            notifyToast(window.t("mic_error") || "Voice input error: " + event.error);
          }
        };

        recognition.onend = () => {
          stopListeningUI();
        };

        recognition.start();
      } catch (e) {
        stopListeningUI();
        console.warn("Speech recognition initialization failed:", e);
        notifyToast(window.t("mic_not_supported") || "Speech recognition not available on this browser.");
      }
    } else {
      notifyToast(window.t("mic_not_supported") || "Voice input is not supported on this browser.");
    }
  });
}
