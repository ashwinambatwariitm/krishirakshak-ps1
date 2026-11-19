/**
 * Bilingual UI Dictionary (English & Hindi)
 * Meets FR-11, FR-15, and Section 8 Content & Safety Rules.
 */

const I18N = {
  en: {
    app_title: "KrishiRakshak",
    app_subtitle: "On-Device Plant Health Advisor",
    tagline: "Runs 100% offline on Raspberry Pi • Zero internet required",
    
    // Bottom Navigation
    nav_scan: "Scan",
    nav_ai: "Kisan AI",
    nav_weather: "Spray & Weather",
    nav_guide: "Kisan Guide",
    
    // Actions & Navigation
    take_photo: "Take Photo",
    choose_gallery: "Choose from Gallery",
    check_plant: "Check Plant",
    take_another_photo: "Take Another Photo",
    back_to_home: "Back to Home",
    try_again: "Try Again",
    ask: "Ask AI",
    close: "Close",
    about_btn: "About",
    history_btn: "Recent Scans",
    clear_history: "Clear History",
    no_history: "No recent scans saved yet.",
    listen_voice: "Listen Aloud",
    stop_voice: "Stop Voice",
    
    // Waiting Screen
    checking_plant: "Checking your plant...",
    waiting_desc: "On-device AI is analyzing disease, insects, and severity. This may take 15–45 seconds.",
    device_error: "Cannot connect to KrishiRakshak device. Please ensure you are connected to the device Wi-Fi hotspot.",
    timeout_error: "Analysis took longer than 60 seconds. Please check the device and try again.",
    
    // Result Screen
    diagnosis_result: "Diagnosis Result",
    confidence: "Model confidence",
    urgent_badge: "Urgent - act today",
    spread_level: "Estimated spread on leaf",
    spread_high: "High",
    spread_medium: "Medium",
    spread_low: "Low",
    insect_found: "Insect detected",
    species_label: "Species",
    important_notes: "Important Official Notices",
    
    // Llama & Advice
    llama_card_title: "Advice (explained by Llama on this device)",
    llama_badge: "AI Simplified",
    advice_title: "Verified Management Practices",
    source_label: "Source",
    
    // Advice Sections
    section_symptoms: "Symptoms & Identification",
    section_spread: "Spread & Survival",
    section_cultural: "Cultural & Field Sanitation",
    section_mechanical: "Physical & Mechanical Control",
    section_biological: "Biological & Bio-Pesticide Control",
    section_monitoring: "Monitoring & Trapping (ETL)",
    section_safety: "Safety & Handling Precautions",
    section_general: "General Recommendations",
    
    // Spray Table
    spray_title: "Spray Options (Official Recommendations)",
    spray_notice: "The spray options below are copied exactly from ICAR, NIPHM and TNAU publications. Always wear protective equipment and observe harvest waiting periods.",
    col_product: "Product",
    col_dose: "Dose",
    col_note: "Label / Waiting Note",
    col_source: "Official Source",
    
    // Q&A & Kisan AI
    ask_title: "Kisan AI Assistant (On-Device Llama)",
    ask_desc: "Ask any follow-up question about tomato diseases, pest control, or harvest intervals.",
    ask_placeholder: "Type or tap a suggestion below...",
    ask_waiting: "Finding verified answer on device...",
    verified_facts_title: "Verified Reference Facts:",
    llama_rejected_notice: "A simplified explanation could not be verified safely. Please refer directly to the verified official facts below:",
    chip_q1: "When can I harvest after spraying?",
    chip_q2: "How to prevent disease spread?",
    chip_q3: "What are organic bio-control options?",
    chip_q4: "Water management tips during blight?",
    
    // Weather & Spray Meter
    weather_title: "Weather & Spray Suitability Meter",
    weather_desc: "Check if wind, temperature, and rain conditions are safe for spraying today to avoid drift and wash-off.",
    spray_favorable: "GOOD CONDITIONS FOR SPRAYING",
    spray_unfavorable: "SPRAYING NOT RECOMMENDED RIGHT NOW",
    temp_label: "Temperature",
    humidity_label: "Humidity",
    wind_label: "Wind Speed",
    rain_label: "Rain Chance",
    spray_tip_title: "Agronomy Spray Tip:",
    spray_tip_text: "Ideal spray hours: 7:00 AM – 10:00 AM or 4:00 PM – 6:30 PM. Never spray directly against strong wind (>12 km/h) or under scorching mid-day sun.",
    
    // Kisan Guide
    guide_title: "Farmer Safety & Knowledge Guide",
    helpline_title: "Government Farmer Helplines",
    kisan_call_center: "Kisan Call Center: 1800-180-1551 (Toll Free, 6 AM - 10 PM)",
    kvk_contact: "Contact your local District Krishi Vigyan Kendra (KVK) for on-field soil & leaf tests.",
    cibrc_title: "CIB&RC Official Toxicity Label Codes",
    toxic_red: "Red Triangle: Extremely Toxic (Class I) — Highest hazard, use maximum protective gear.",
    toxic_yellow: "Yellow Triangle: Highly Toxic (Class II) — Strict precautions needed.",
    toxic_blue: "Blue Triangle: Moderately Toxic (Class III) — Follow label safety rules.",
    toxic_green: "Green Triangle: Slightly Toxic (Class IV) — Safer bio-rational or organic choice.",
    golden_rules_title: "5 Golden Rules of Safe Spraying",
    rule_1: "1. Wear protective gear: mask, gloves, and boots.",
    rule_2: "2. Never blow blocked nozzles with your mouth; use clean water and a soft brush.",
    rule_3: "3. Spray with the wind at your back, never walking into the spray mist.",
    rule_4: "4. Strictly observe the harvest waiting period (PHI) before picking produce.",
    rule_5: "5. Triple rinse empty pesticide containers and puncture them; never reuse for water or feed.",
    
    // Uncertain & Retake
    uncertain_title: "Diagnosis Uncertain",
    uncertain_desc: "The AI model is not confident enough to diagnose this leaf safely.",
    uncertain_tips_title: "Recommended next steps:",
    uncertain_tip_1: "Take a clear, sharp photo of a single affected leaf in bright, natural daylight.",
    uncertain_tip_2: "Consult your local Krishi Vigyan Kendra (KVK) or Block Agriculture Officer.",
    retake_title: "Please Retake Photo",
    retake_desc: "The photo quality is not suitable for accurate diagnosis.",
    quality_issues: "Detected photo issues:",
    issue_too_dark: "Photo is too dark — take photo in bright daylight.",
    issue_too_bright: "Photo is overexposed/too bright — avoid direct sun glare.",
    issue_too_blurred: "Photo is blurred — hold camera steady and tap to focus on leaf.",
    issue_too_small: "Leaf is too far away — move closer so leaf fills the frame.",
    
    // About
    about_title: "About KrishiRakshak",
    about_desc: "KrishiRakshak is an offline, on-device crop disease and insect pest advisory system built for Indian farmers as part of the Bharat AI-SoC Challenge.",
    about_req_icar: "Advice from ICAR, NIPHM and TNAU publications",
    about_req_llama: "Built with Llama",
    sys_details: "System & Model Details",
    disease_model: "Disease Classifier",
    pest_model: "Insect Pest Detector",
    llama_model: "On-device LLM",
    kb_version: "Knowledge Base Version",
    kb_draft: "Draft (Under Expert Review)",
    kb_reviewed: "Verified",
    runtime_env: "Runtime",
    api_server_setting: "API Server Address",
    api_server_hint: "Leave empty for same Pi server, or set http://localhost:8080 for mock server.",
    save_setting: "Save & Reload",
    
    // Technical
    tech_details: "Technical Details & Timings",
    total_time: "Total Inference Time",
    vision_time: "Vision Models (Disease + Pest)",
    llama_time: "Llama LLM Inference",
    tokens_sec: "Tokens per second"
  },
  
  hi: {
    app_title: "कृषिरक्षक",
    app_subtitle: "डिवाइस पर चलने वाला फसल स्वास्थ्य सलाहकार",
    tagline: "रास्पबेरी पाई पर 100% ऑफलाइन • बिना इंटरनेट चलता है",
    
    // Bottom Navigation
    nav_scan: "जांच",
    nav_ai: "किसान AI",
    nav_weather: "मौसम व छिड़काव",
    nav_guide: "मार्गदर्शिका",
    
    // Actions & Navigation
    take_photo: "फोटो लें",
    choose_gallery: "गैलरी से चुनें",
    check_plant: "पौधे की जांच करें",
    take_another_photo: "दूसरी फोटो लें",
    back_to_home: "मुख्य पृष्ठ",
    try_again: "पुनः प्रयास करें",
    ask: "AI से पूछें",
    close: "बंद करें",
    about_btn: "जानकारी",
    history_btn: "हाल की जांच",
    clear_history: "इतिहास मिटाएं",
    no_history: "कोई हालिया जांच सहेजी नहीं गई है।",
    listen_voice: "बोलकर सुनें (Voice)",
    stop_voice: "आवाज बंद करें",
    
    // Waiting Screen
    checking_plant: "आपके पौधे की जांच हो रही है...",
    waiting_desc: "डिवाइस पर AI मॉडल रोग, कीट और गंभीरता की जांच कर रहा है। कृपया 15–45 सेकंड प्रतीक्षा करें।",
    device_error: "कृषिरक्षक डिवाइस से संपर्क नहीं हो सका। कृपया जांचें कि फोन कृषिरक्षक वाई-फ़ाई हॉटस्पॉट से जुड़ा है।",
    timeout_error: "जांच में 60 सेकंड से अधिक समय लगा। कृपया पुनः प्रयास करें।",
    
    // Result Screen
    diagnosis_result: "निदान परिणाम",
    confidence: "मॉडल सटीकता",
    urgent_badge: "तत्काल कार्रवाई करें",
    spread_level: "पत्ती पर अनुमानित फैलाव",
    spread_high: "अधिक (High)",
    spread_medium: "मध्यम (Medium)",
    spread_low: "कम (Low)",
    insect_found: "कीट पाया गया",
    species_label: "प्रजाति",
    important_notes: "महत्वपूर्ण आधिकारिक सूचनाएं",
    
    // Llama & Advice
    llama_card_title: "सलाह (इस डिवाइस पर Llama द्वारा समझाई गई)",
    llama_badge: "AI सरल भाषा",
    advice_title: "प्रमाणित रोकथाम एवं प्रबंधन के उपाय",
    source_label: "स्रोत",
    
    // Advice Sections
    section_symptoms: "रोग के लक्षण एवं पहचान",
    section_spread: "फैलाव एवं जीवित रहने के कारण",
    section_cultural: "खेत की स्वच्छता एवं कृषि प्रबंधन",
    section_mechanical: "भौतिक एवं यांत्रिक नियंत्रण",
    section_biological: "जैविक एवं बायो-पेस्टिसाइड नियंत्रण",
    section_monitoring: "निगरानी एवं ट्रैपिंग (आर्थिक सीमा)",
    section_safety: "सुरक्षा एवं सावधानी",
    section_general: "सामान्य सिफारिशें",
    
    // Spray Table
    spray_title: "कीटनाशक / कवकनाशी छिड़काव विकल्प (आधिकारिक)",
    spray_notice: "नीचे दिए गए छिड़काव विकल्प ICAR, NIPHM और TNAU के प्रकाशनों से हूबहू लिए गए हैं। सुरक्षात्मक कपड़े पहनें और तुड़ाई प्रतीक्षा अवधि का पालन करें।",
    col_product: "उत्पाद का नाम",
    col_dose: "मात्रा",
    col_note: "लेबल / तुड़ाई प्रतीक्षा टिप्पणी",
    col_source: "आधिकारिक स्रोत",
    
    // Q&A & Kisan AI
    ask_title: "किसान AI मित्र (डिवाइस पर Llama मॉडल)",
    ask_desc: "टमाटर के रोग, कीट नियंत्रण या तुड़ाई समय के बारे में कोई भी प्रश्न पूछें।",
    ask_placeholder: "लिखें या नीचे दिए गए सुझाव पर टैप करें...",
    ask_waiting: "डिवाइस से प्रमाणित उत्तर खोजा जा रहा है...",
    verified_facts_title: "प्रमाणित संदर्भ तथ्य:",
    llama_rejected_notice: "सरल भाषा में व्याख्या सत्यापित नहीं हो सकी। कृपया नीचे दिए गए प्रमाणित आधिकारिक तथ्यों को पढ़ें:",
    chip_q1: "छिड़काव के कितने दिन बाद तुड़ाई करें?",
    chip_q2: "रोग को आगे फैलने से कैसे रोकें?",
    chip_q3: "जैविक व देसी नियंत्रण के क्या उपाय हैं?",
    chip_q4: "झुलसा रोग में सिंचाई कैसे करें?",
    
    // Weather & Spray Meter
    weather_title: "मौसम एवं सुरक्षित छिड़काव मीटर",
    weather_desc: "जांचें कि आज खेत में दवा छिड़कने के लिए हवा, तापमान और बारिश के हालात अनुकूल हैं या नहीं।",
    spray_favorable: "छिड़काव के लिए मौसम अनुकूल है",
    spray_unfavorable: "वर्तमान समय में छिड़काव न करें",
    temp_label: "तापमान",
    humidity_label: "नमी (आर्द्रता)",
    wind_label: "हवा की गति",
    rain_label: "बारिश की संभावना",
    spray_tip_title: "कृषि छिड़काव सलाह:",
    spray_tip_text: "छिड़काव का सबसे उत्तम समय: सुबह 7:00 से 10:00 बजे या शाम 4:00 से 6:30 बजे। तेज हवा (>12 किमी/घंटा) या तेज दोपहर की धूप में कभी छिड़काव न करें।",
    
    // Kisan Guide
    guide_title: "किसान सुरक्षा एवं मार्गदर्शिका",
    helpline_title: "सरकारी किसान हेल्पलाइन",
    kisan_call_center: "किसान कॉल सेंटर: 1800-180-1551 (टोल फ्री, सुबह 6 से रात 10)",
    kvk_contact: "खेत की मिट्टी व रोग जांच के लिए अपने जिला कृषि विज्ञान केंद्र (KVK) से संपर्क करें।",
    cibrc_title: "केंद्रीय कीटनाशी बोर्ड (CIB&RC) विषाक्तता रंग संकेत",
    toxic_red: "लाल त्रिकोण: अत्यधिक विषाक्त (Class I) — अत्यंत खतरनाक, पूर्ण सुरक्षा उपकरण पहनें।",
    toxic_yellow: "पीला त्रिकोण: अति विषाक्त (Class II) — विशेष सावधानी आवश्यक।",
    toxic_blue: "नीला त्रिकोण: मध्यम विषाक्त (Class III) — लेबल निर्देश अनुसार उपयोग करें।",
    toxic_green: "हरा त्रिकोण: कम विषाक्त (Class IV) — जैविक व अपेक्षाकृत सुरक्षित विकल्प।",
    golden_rules_title: "सुरक्षित छिड़काव के 5 सुनहरे नियम",
    rule_1: "1. सुरक्षात्मक कपड़े: मास्क, दस्ताने और जूते जरूर पहनें।",
    rule_2: "2. बंद नोजल को कभी मुंह से न फूंकें; साफ पानी और ब्रश का उपयोग करें।",
    rule_3: "3. हवा की दिशा में छिड़काव करें, दवा के फुहार की उल्टी दिशा में न चलें।",
    rule_4: "4. फसल तुड़ाई से पहले लेबल पर दी गई प्रतीक्षा अवधि (PHI) का कड़ाई से पालन करें।",
    rule_5: "5. खाली डिब्बों को तीन बार धोकर नष्ट करें; पानी या चारे के लिए प्रयोग न करें।",
    
    // Uncertain & Retake
    uncertain_title: "निदान अनिश्चित है",
    uncertain_desc: "मॉडल इस पत्ते के रोग के बारे में पर्याप्त आश्वस्त नहीं है।",
    uncertain_tips_title: "सुझाए गए कदम:",
    uncertain_tip_1: "दिन की प्राकृतिक धूप में एक प्रभावित पत्ते की साफ और स्पष्ट फोटो लें।",
    uncertain_tip_2: "पौधे को अपने नजदीकी कृषि विज्ञान केंद्र (KVK) या कृषि अधिकारी को दिखाएं।",
    retake_title: "कृपया दोबारा फोटो लें",
    retake_desc: "फोटो की गुणवत्ता रोग पहचानने योग्य नहीं है।",
    quality_issues: "फोटो में पाई गई कमियां:",
    issue_too_dark: "फोटो बहुत अंधेरी है — प्राकृतिक रोशनी में फोटो खींचें।",
    issue_too_bright: "फोटो बहुत अधिक चमकदार है — सीधी धूप की चमक से बचें।",
    issue_too_blurred: "फोटो धुंधली है — कैमरा स्थिर रखें और पत्ते पर फोकस करें।",
    issue_too_small: "पत्ता बहुत दूर है — पास जाकर पत्ते को स्क्रीन में भरें।",
    
    // About
    about_title: "कृषिरक्षक के बारे में",
    about_desc: "कृषिरक्षक भारत AI-SoC चैलेंज के तहत भारतीय किसानों के लिए बनाया गया ऑन-डिवाइस, बिना इंटरनेट चलने वाला फसल रोग एवं कीट सलाहकार है।",
    about_req_icar: "Advice from ICAR, NIPHM and TNAU publications",
    about_req_llama: "Built with Llama",
    sys_details: "सिस्टम एवं मॉडल विवरण",
    disease_model: "रोग पहचान मॉडल",
    pest_model: "कीट पहचान मॉडल",
    llama_model: "ऑन-डिवाइस भाषा मॉडल",
    kb_version: "ज्ञान भंडार (KB) संस्करण",
    kb_draft: "प्रारूप (विशेषज्ञ समीक्षाधीन)",
    kb_reviewed: "सत्यापित",
    runtime_env: "रनटाइम",
    api_server_setting: "API सर्वर पता",
    api_server_hint: "पाई सर्वर के लिए खाली छोड़ें, या मॉक सर्वर हेतु http://localhost:8080 दर्ज करें।",
    save_setting: "सहेजें और पुनः लोड करें",
    
    // Technical
    tech_details: "तकनीकी विवरण एवं समय (Timings)",
    total_time: "कुल निष्कर्ष समय",
    vision_time: "विज़न मॉडल (रोग + कीट)",
    llama_time: "Llama एलएलएम समय",
    tokens_sec: "टोकन प्रति सेकंड"
  }
};

let currentLanguage = window.CONFIG ? window.CONFIG.DEFAULT_LANG : "en";

function setLanguage(lang) {
  if (lang !== "en" && lang !== "hi") lang = "en";
  currentLanguage = lang;
  localStorage.setItem("KR_LANG", lang);
  updateStaticDOMText();
  document.documentElement.lang = lang;
  
  window.dispatchEvent(new CustomEvent("kr-lang-changed", { detail: { lang } }));
}

function getLanguage() {
  return currentLanguage;
}

function t(key) {
  const dict = I18N[currentLanguage] || I18N.en;
  return dict[key] || I18N.en[key] || key;
}

function updateStaticDOMText() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (key) {
      el.textContent = t(key);
    }
  });
  document.querySelectorAll("[data-i18n-ph]").forEach(el => {
    const key = el.getAttribute("data-i18n-ph");
    if (key) {
      el.setAttribute("placeholder", t(key));
    }
  });
  document.querySelectorAll("[data-i18n-title]").forEach(el => {
    const key = el.getAttribute("data-i18n-title");
    if (key) {
      el.setAttribute("title", t(key));
    }
  });
  
  const langToggleBtn = document.getElementById("btn-lang-toggle");
  if (langToggleBtn) {
    langToggleBtn.textContent = currentLanguage === "en" ? "हिन्दी" : "English";
    langToggleBtn.setAttribute("aria-label", currentLanguage === "en" ? "Switch to Hindi" : "Switch to English");
  }
}

window.I18N = I18N;
window.t = t;
window.setLanguage = setLanguage;
window.getLanguage = getLanguage;
window.updateStaticDOMText = updateStaticDOMText;
