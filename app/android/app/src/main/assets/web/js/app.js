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
      window.voiceAdvisor.toggle(spokenResult(res, window.t), lang, btnVoiceDiag,
                                 lang === "en" ? null : spokenResult(englishView(res), tEnglish));
    });
  }

  // Verified extracts read aloud (in the language shown); the only spoken advice when Llama's text was not
  // accepted, e.g. for a healthy leaf or most insect photos
  const btnVoiceAdvice = document.getElementById("btn-voice-advice");
  if (btnVoiceAdvice) {
    btnVoiceAdvice.addEventListener("click", () => {
      const res = window.appState.analysisResult;
      if (!res) return;
      const lang = window.appState.viewingEnglish ? "en" : window.getLanguage();
      const text = adviceText(res, false);
      if (!text) return;
      window.voiceAdvisor.toggle(text, lang, btnVoiceAdvice, lang === "en" ? null : adviceText(res, true));
    });
  }

  const btnVoiceLlama = document.getElementById("btn-voice-llama");
  if (btnVoiceLlama) {
    btnVoiceLlama.addEventListener("click", () => {
      const res = window.appState.analysisResult;
      if (!res || !res.llama || !res.llama.text) return;
      const tr = window.appState.viewingEnglish ? null : res.translation;
      if (tr && tr.text) {
        window.voiceAdvisor.toggle(tr.text, tr.lang, btnVoiceLlama, res.llama.text);
      } else {
        window.voiceAdvisor.toggle(res.llama.text, "en", btnVoiceLlama);
      }
    });
  }

  // Kisan AI answers are chat bubbles with their own Listen button (appendAiChatMessage)

  // Developer mock selector (if testing with query parameter ?example=...)
  const urlParams = new URLSearchParams(window.location.search);
  const mockParam = urlParams.get("example");
  if (mockParam) {
    window.appState.mockExample = mockParam;
  }

  // Spray check: each Yes / No answer updates the result
  document.querySelectorAll(".spray-ans").forEach(btn => {
    btn.addEventListener("click", () => {
      window.sprayCheck.setAnswer(btn.getAttribute("data-q"), btn.getAttribute("data-a"));
      updateWeatherUI();
    });
  });
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
  } else if (status === "retake_photo" || status === "not_tomato") {
    // "not_tomato": the tomato-leaf check rejected the photo; same screen, own title, the message explains it
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

  // Leaf disease and pests are equal results: without a disease name the title is the pest result
  diseaseNameEl.textContent = disease.name || (pestTitle(data) || window.t("diagnosis_result"));

  // Crop detected by the device (Phase 1: tomato from the leaf check; more crops later from the same field)
  const cropBadge = document.getElementById("res-crop-badge");
  if (cropBadge) {
    const crop = data.crop && data.crop.name;
    cropBadge.classList.toggle("hidden", !crop);
    if (crop) cropBadge.textContent = `${window.t("crop_label")}: ${cropName(crop)} (${window.t("crop_detected")})`;
  }

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
    // When the title already is the pest result ("Pest detected: ..."), the badge would repeat it
    pestsBadge.classList.toggle("hidden", !disease.name);
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
  if (data.llama && data.llama.text && data.llama.accepted !== false) {
    llamaTextEl.textContent = data.llama.text;
    llamaContainer.classList.remove("hidden");
  } else {
    llamaContainer.classList.add("hidden");
  }
  renderTranslation(document.getElementById("res-llama-translation"), data.translation, llamaTextEl);
  // A translation was asked for and the AI explanation did not pass the device's safety check: the verified extracts
  // are the advice. The note ("... the verified advice below is in English") is shown only when that is true, i.e.
  // no extract came back in the chosen language; otherwise the farmer just sees the verified advice in their language
  // (whether Llama was rejected stays in the technical details)
  const mtNote = document.getElementById("res-mt-unavailable");
  const llamaRejected = data.llama && (data.llama.accepted === false || !data.llama.text);
  const chunks = (data.advice_blocks || []).flatMap(b => b.chunks || []).filter(c => c.section !== "chemical");
  const anyTranslated = chunks.some(c => c.text_en && c.text && c.text !== c.text_en);
  if (mtNote) mtNote.classList.toggle("hidden", !(window.CONFIG.TRANSLATE_LANG && llamaRejected && !anyTranslated));

  // 5. Advice Blocks (FR-7)
  const btnAdvice = document.getElementById("btn-voice-advice");
  if (btnAdvice) btnAdvice.classList.toggle("hidden", !adviceText(data, false));
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

function formatChatTime() {
  const d = new Date();
  return d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0');
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function appendAiChatMessage(res, topic) {
  const chatContainer = document.getElementById("chat-messages-container");
  if (!chatContainer) return;

  const aiMsg = document.createElement("div");
  aiMsg.className = "chat-message ai-message";

  const bubble = document.createElement("div");
  bubble.className = "chat-bubble ai-bubble";

  // Bubble header
  const header = document.createElement("div");
  header.className = "bubble-header";
  header.innerHTML = `<span class="bubble-badge">${window.t("ai_grounded_badge") || "ICAR / NIPHM / TNAU sources"}</span>`;
  bubble.appendChild(header);

  // Determine speech text and body text
  let speechText = "";
  let englishSpeech = "";

  if (res.answer && res.accepted !== false) {
    const p = document.createElement("p");
    p.className = "bubble-text";
    p.textContent = res.answer;
    bubble.appendChild(p);
    speechText = res.answer;
    englishSpeech = res.answer;

    if (res.translation) {
      const trBlock = document.createElement("div");
      trBlock.className = "translation-block";
      renderTranslation(trBlock, res.translation, p);
      bubble.appendChild(trBlock);

      if (typeof res.translation === "object") {
        if (res.translation.text) speechText = res.translation.text;
        else if (Array.isArray(res.translation.sentences)) speechText = res.translation.sentences.join(" ");
      }
    }
  } else {
    const warning = document.createElement("p");
    warning.className = "table-note";
    warning.style.color = "var(--warn-amber)";
    warning.style.marginBottom = "8px";
    warning.textContent = window.t("llama_rejected_notice") || "A simplified explanation could not be verified safely. Please refer directly to the verified official facts below:";
    bubble.appendChild(warning);
  }

  // Facts list
  if (Array.isArray(res.facts) && res.facts.length > 0) {
    const factsWrapper = document.createElement("div");
    factsWrapper.className = "qa-facts-wrapper";
    factsWrapper.style.marginTop = "8px";
    factsWrapper.innerHTML = `<h4 class="qa-facts-title" style="margin-bottom:6px;">${window.t("verified_facts_title") || "Verified Reference Facts:"}</h4>`;
    
    const factsList = document.createElement("div");
    res.facts.forEach(fact => {
      const factItem = document.createElement("div");
      factItem.className = "fact-item";
      factItem.innerHTML = `<span>${escapeHtml(fact.text)} </span>${fact.source_org ? `<span class="source-badge">[${escapeHtml(fact.source_org)}]</span>` : ""}`;
      factsList.appendChild(factItem);
    });
    factsWrapper.appendChild(factsList);
    bubble.appendChild(factsWrapper);

    if (!speechText) {
      speechText = res.facts.map(f => f.text).join(". ");
      englishSpeech = speechText;
    }
  }

  // Bubble footer with Voice listen button & timestamp
  const footer = document.createElement("div");
  footer.className = "bubble-footer";
  footer.innerHTML = `
    <button class="btn-voice btn-voice-chat" type="button" title="Listen Aloud">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
        <path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>
      </svg>
      <div class="sound-wavebars">
        <span class="sound-bar"></span>
        <span class="sound-bar"></span>
        <span class="sound-bar"></span>
        <span class="sound-bar"></span>
      </div>
      <span>${window.t("listen_voice") || "Listen"}</span>
    </button>
    <span class="bubble-time">${formatChatTime()}</span>
  `;
  bubble.appendChild(footer);

  // Wire up inline voice button
  const voiceBtn = footer.querySelector(".btn-voice-chat");
  if (voiceBtn && window.voiceAdvisor) {
    voiceBtn.addEventListener("click", () => {
      const chosenLang = window.CONFIG.TRANSLATE_LANG || "en";
      window.voiceAdvisor.toggle(speechText, chosenLang, voiceBtn, englishSpeech);
    });
  }

  aiMsg.appendChild(bubble);
  chatContainer.appendChild(aiMsg);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Handle Follow-up Question in Kisan AI Tab (FR-9) - WhatsApp-Style Chat Flow
 */
async function handleAskQuestion() {
  const inputEl = document.getElementById("input-question");
  const question = inputEl.value.trim();
  if (!question) return;

  const chatContainer = document.getElementById("chat-messages-container");
  const typingIndicator = document.getElementById("chat-typing-indicator");

  // 1. Clear input
  inputEl.value = "";

  // 2. Append user bubble
  if (chatContainer) {
    const userMsg = document.createElement("div");
    userMsg.className = "chat-message user-message";
    userMsg.innerHTML = `
      <div class="chat-bubble user-bubble">
        <p class="bubble-text">${escapeHtml(question)}</p>
        <div class="bubble-footer">
          <span class="bubble-time">${formatChatTime()}</span>
        </div>
      </div>
    `;
    chatContainer.appendChild(userMsg);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  // 3. Show typing indicator
  if (typingIndicator) {
    typingIndicator.classList.remove("hidden");
    if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  const topic = window.appState.lastTopic;
  const lang = "en";

  try {
    const res = await window.apiService.askQuestion(question, topic, lang, window.CONFIG.TRANSLATE_LANG || "");
    if (typingIndicator) typingIndicator.classList.add("hidden");
    appendAiChatMessage(res, topic);
  } catch (err) {
    if (typingIndicator) typingIndicator.classList.add("hidden");
    if (chatContainer) {
      const errBubble = document.createElement("div");
      errBubble.className = "chat-message ai-message";
      errBubble.innerHTML = `
        <div class="chat-bubble ai-bubble" style="border-color:var(--urgent-red);background:var(--urgent-bg);">
          <p class="bubble-text" style="color:var(--urgent-red);font-weight:700;">Could not connect to KrishiRakshak device. Please check Wi-Fi hotspot connection.</p>
          <div class="bubble-footer">
            <span class="bubble-time">${formatChatTime()}</span>
          </div>
        </div>
      `;
      chatContainer.appendChild(errBubble);
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }
}

/**
 * Text for the "listen" button of the result header: diagnosis, confidence, urgency and the insects found. For a
 * photo that is not a tomato leaf but shows insects there is no disease name: say that, then the insects.
 * tr: label function (window.t for the chosen language, tEnglish for the English fallback)
 */
// Localised crop name ("crop_tomato" label; the plain name when a new crop has no label yet)
function cropName(name) {
  const key = `crop_${name}`;
  const t = window.t(key);
  return t && t !== key ? t : name;
}

// "Pest detected: Caterpillars (...)" for a result with insects (null when there are none)
function pestTitle(res, tr = window.t) {
  const names = [...new Set((res.pests || []).map(p => p.name).filter(Boolean))].join(", ");
  return names ? `${tr("pest_detected_title")}: ${names}` : null;
}

function spokenResult(res, tr) {
  const d = res.disease || {};
  const pests = [...new Set((res.pests || []).map(p => p.name).filter(Boolean))].join(", ");
  const top = d.top && d.top[0];
  if (d.name) {
    let text = `${tr("diagnosis_result")}: ${d.name}.`;
    if (top && typeof top.probability === "number") text += ` ${tr("confidence")}: ${Math.round(top.probability * 100)}%.`;
    if (d.urgent) text += ` ${tr("urgent_badge")}.`;
    return pests ? `${text} ${pests}.` : text;
  }
  const pt = pestTitle(res, tr);
  return pt ? `${pt}.` : `${d.not_tomato_leaf ? tr("not_tomato_title") : tr("diagnosis_result")}.`;
}

// English label (fallback text when the phone has no voice for the chosen language)
function tEnglish(key) {
  return (window.I18N && window.I18N.en && window.I18N.en[key]) || key;
}

// Verified extracts of all advice blocks as one text, as shown in the advice cards (the chemical spray options
// of the spray table are not read out)
function adviceText(res, english) {
  const parts = [];
  (res.advice_blocks || []).forEach(block => {
    const chunks = (block.chunks || []).filter(c => c.section !== "chemical");
    if (chunks.length === 0) return;
    const enBlock = english && res.en && (res.en.advice_blocks || []).find(b => b.topic === block.topic);
    parts.push(`${english && enBlock ? enBlock.name : block.name}.`);
    chunks.forEach(c => parts.push(english ? (c.text_en || c.text) : (c.text || c.text_en)));
  });
  return parts.filter(Boolean).join(" ");
}

/**
 * Spray check screen: highlight the chosen answers, then "do not spray now" with the reasons (one unsafe answer is
 * enough) or "conditions look suitable" once all four answers are safe
 */
function updateWeatherUI() {
  if (!window.sprayCheck) return;
  const result = window.sprayCheck.evaluate();
  const banner = document.getElementById("spray-status-banner");
  const statusText = document.getElementById("spray-status-text");
  const issuesBox = document.getElementById("spray-issues-box");
  if (!banner || !statusText || !issuesBox) return;

  document.querySelectorAll(".spray-ans").forEach(btn => {
    const chosen = window.sprayCheck.answers[btn.getAttribute("data-q")] === btn.getAttribute("data-a");
    btn.classList.toggle("btn-primary", chosen);
    btn.classList.toggle("btn-secondary", !chosen);
  });

  issuesBox.innerHTML = "";
  if (result.reasons.length > 0) {
    banner.className = "spray-meter-banner unfavorable";
    statusText.textContent = window.t("spray_not_now");
    result.reasons.forEach(key => {
      const p = document.createElement("div");
      p.className = "alert-note";
      p.textContent = window.t(key);
      issuesBox.appendChild(p);
    });
  } else if (result.complete) {
    banner.className = "spray-meter-banner favorable";
    statusText.textContent = window.t("spray_ok");
  } else if (result.answered > 0) {
    banner.className = "spray-meter-banner";
    statusText.textContent = window.t("spray_answer_all");
  } else {
    banner.className = "spray-meter-banner hidden";
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
  const notTomato = data.status === "not_tomato";
  const title = document.querySelector("#view-retake h2");
  const desc = document.querySelector("#view-retake p.muted");
  if (title) {
    title.setAttribute("data-i18n", notTomato ? "not_tomato_title" : "retake_title");  // kept on language change
    title.textContent = window.t(notTomato ? "not_tomato_title" : "retake_title");
  }
  if (desc) desc.classList.toggle("hidden", notTomato);  // "photo quality" text does not apply here
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
  if (!tr || !tr.text) {
    container.classList.add("hidden");
    return;
  }
  const label = document.createElement("div");
  label.className = "translation-label";
  label.textContent = window.t("mt_title");
  const body = document.createElement("p");
  body.className = "translation-text";
  body.lang = tr.lang || "";
  body.textContent = tr.text;
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
 * "Advice also in" picker: shown only when the device reports translation languages (GET /api/info).
 */
async function setupTranslatePicker() {
  const picker = document.getElementById("translate-picker");
  const select = document.getElementById("select-translate");
  if (!picker || !select) return;
  select.value = window.CONFIG.TRANSLATE_LANG || "";
  // One language choice for the whole app: labels, advice and the verified practices in the chosen language
  const applyInterfaceLanguage = () => {
    window.setLanguage(select.value || "en");   // labels in the chosen language (English where one is missing)
    if (typeof updateWeatherUI === "function") updateWeatherUI();
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
    // Device not reachable yet (for example the phone joined the Pi's Wi-Fi after the app opened): keep all languages;
    // a device without the translator simply returns the advice in English
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
