/**
 * Bilingual UI Dictionary (English & Hindi)
 * Meets FR-11, FR-15, and Section 8 Content & Safety Rules.
 */

const I18N = {
  en: {
    app_title: "KrishiRakshak",
    app_subtitle: "On-Device Plant Health Advisor",
    tagline: "Runs 100% offline on Raspberry Pi \u2022 Zero internet required",
    
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
    waiting_desc: "On-device AI is checking for disease, insects and severity. This takes about 5-10 seconds.",
    device_error: "Cannot connect to KrishiRakshak device. Please ensure you are connected to the device Wi-Fi hotspot.",
    timeout_error: "Analysis took longer than 60 seconds. Please check the device and try again.",
    
    // Result Screen
    diagnosis_result: "Diagnosis Result",
    confidence: "Model confidence",
    urgent_badge: "Urgent - act today",
    healthy: "Healthy leaf",
    early_blight: "Early blight",
    late_blight: "Late blight",
    septoria_leaf_spot: "Septoria leaf spot",
    bacterial_spot: "Bacterial spot",
    yellow_leaf_curl_virus: "Tomato yellow leaf curl virus",
    topic_healthy: "Healthy leaf",
    topic_early_blight: "Early blight",
    topic_late_blight: "Late blight",
    topic_septoria_leaf_spot: "Septoria leaf spot",
    topic_bacterial_spot: "Bacterial spot",
    topic_yellow_leaf_curl_virus: "Tomato yellow leaf curl virus",
    spread_level: "Estimated spread on leaf",
    spread_high: "High",
    spread_medium: "Medium",
    spread_low: "Low",
    spread_moderate: "Moderate",
    spread_not_applicable: "Not measured (virus)",
    sev_title: "Disease severity (this leaf)",
    sev_share: "about {pct}% of the leaf shows disease",
    sev_scale: "Low: under 10% of the leaf - Moderate: 10-25% - High: over 25%.",
    sev_note: "Estimate from this photo, measured on the device. Check other leaves and plants too.",
    sev_not_applicable: "No severity level for virus diseases: the symptoms are curling and mottling of the whole plant, not spots. Follow the advice below.",
    insect_found: "Insect detected",
    translate_label: "Advice also in",
    translate_none: "English only",
    mt_title: "Machine translation on this device - not yet checked by a speaker of this language",
    mt_withheld: "Some sentences failed the translation check and are shown in English.",
    mt_show_english: "Show the English original",
    tts_no_voice: "No {lang} voice on this phone, so the English is read. To install it: Settings > Text-to-speech > Speech Services by Google > Install voice data.",
    tts_not_started: "Speech did not start. Check that a text-to-speech voice for this language is installed and downloaded for offline use.",
    tts_unsupported: "Text-to-speech is not supported on this browser.",
    kb_mt_note: "Text from ICAR, NIPHM and TNAU publications, machine-translated (not yet checked by a speaker of this language). Spray products and doses are as published.",
    mt_unavailable: "The AI explanation did not pass the safety check, so there is no translation for this photo. The verified advice below is in English.",
    pest_sev_title: "Insects in this photo",
    pest_sev_photo_only: "Level for this photo only - check the field before spraying.",
    pest_sev_uncertain: "Species not certain.",
    pest_threshold: "Published action level",
    pest_scouting: "How to check your field",
    level_low: "Low",
    level_moderate: "Moderate",
    level_high: "High",
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
    section_resistant_varieties: "Resistant Varieties",
    section_nutrition: "Nutrition",
    section_natural_enemies: "Natural Enemies (Friendly Insects)",
    section_chemical: "Spray Options",
    
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
    ask_placeholder: "Type or speak your question...",
    ask_waiting: "Finding verified answer on device...",
    mic_btn: "Speak question",
    mic_listening: "Listening... Speak now",
    mic_error: "Voice not recognized. Please try again or type.",
    mic_not_supported: "Voice input is not supported on this browser/device.",
    verified_facts_title: "Verified Reference Facts:",
    llama_rejected_notice: "A simplified explanation could not be verified safely. Please refer directly to the verified official facts below:",
    chip_q1: "When can I harvest after spraying?",
    chip_q2: "How to prevent disease spread?",
    chip_q3: "What are organic bio-control options?",
    chip_q4: "Water management tips during blight?",
    tip_daylight: "Bright Daylight",
    tip_sharp: "Close-up & Sharp",
    tip_single_leaf: "Single Leaf",
    leaf_alignment_hint: "Center a single affected leaf inside the frame",
    llama_online: "On-Device Llama \u2022 100% Offline",
    ai_grounded_badge: "ICAR / NIPHM Grounded",
    chat_welcome: "Namaste! I am your Kisan AI advisor running on this device. Ask any question about tomato crop diseases, safe spray practices, waiting intervals (PHI), or organic control.",
    chat_now: "Now",
    speaking_label: "Speaking advice in {lang}...",
    
    // Field Conditions & Spray Prediction
    weather_title: "Field Conditions & Spray Advisory",
    weather_desc: "Select field wind, temperature, and rain conditions to calculate offline spray suitability.",
    spray_favorable: "GOOD CONDITIONS FOR SPRAYING",
    spray_unfavorable: "SPRAYING NOT RECOMMENDED RIGHT NOW",
    temp_label: "Temperature",
    humidity_label: "Humidity",
    wind_label: "Wind Speed",
    rain_label: "Rain Chance",
    spray_tip_title: "Agronomy Spray Tip:",
    spray_tip_text: "Ideal spray hours: 7:00 AM \u2013 10:00 AM or 4:00 PM \u2013 6:30 PM. Never spray directly against strong wind (>12 km/h) or under scorching mid-day sun.",
    weather_q_section_title: "Field Condition Questions",
    weather_q_section_desc: "Answer 3 quick questions about your field to calculate spray suitability:",
    q_wind_label: "1. How is the wind in your field right now?",
    opt_wind_calm: "Calm (< 6 km/h)",
    opt_wind_breeze: "Gentle Breeze (7-12 km/h)",
    opt_wind_strong: "Strong Wind (> 15 km/h)",
    q_temp_label: "2. What is the time and heat condition?",
    opt_temp_morning: "Morning / Cool (25\u00b0C)",
    opt_temp_afternoon: "Warm Afternoon (29\u00b0C)",
    opt_temp_scorching: "Hot Midday (> 34\u00b0C)",
    q_rain_label: "3. What is the sky and rain forecast?",
    opt_rain_clear: "Clear Sky (No rain)",
    opt_rain_cloudy: "Cloudy / Overcast",
    opt_rain_expected: "Rain Expected / Raining",
    faq_title: "Spray & Weather Frequently Asked Questions",
    faq_q1: "What are the best hours of the day to spray?",
    faq_a1: "Early morning (7:00 AM \u2013 10:00 AM) or late afternoon (4:00 PM \u2013 6:30 PM). Avoid scorching midday heat (above 33\u00b0C) to prevent rapid evaporation and foliar burn.",
    faq_q2: "Why is spraying dangerous in strong winds (>15 km/h)?",
    faq_a2: "High winds blow fine chemical mist away from the target tomato plants onto nearby crops, water canals, or the applicator (chemical drift), wasting money and causing contamination.",
    faq_q3: "What if rain falls within 2 to 4 hours after spraying?",
    faq_a3: "Rain will wash off contact fungicides before they can adhere to the leaf cuticle. Most sprays require at least 2 to 4 hours of dry weather to achieve rainfastness.",
    faq_q4: "Why should I check the harvest waiting period (PHI)?",
    faq_a4: "The Pre-Harvest Interval (PHI) is the mandatory number of days between the last pesticide spray and picking tomatoes. Strictly observe PHI to ensure produce is free from chemical residues.",
    
    // Kisan Guide
    guide_title: "Farmer Safety & Knowledge Guide",
    helpline_title: "Government Farmer Helplines",
    kisan_call_center: "Kisan Call Center: 1800-180-1551 (Toll Free, 6 AM - 10 PM)",
    kvk_contact: "Contact your local District Krishi Vigyan Kendra (KVK) for on-field soil & leaf tests.",
    cibrc_title: "CIB&RC Official Toxicity Label Codes",
    toxic_red: "Red Triangle: Extremely Toxic (Class I) \u2014 Highest hazard, use maximum protective gear.",
    toxic_yellow: "Yellow Triangle: Highly Toxic (Class II) \u2014 Strict precautions needed.",
    toxic_blue: "Blue Triangle: Moderately Toxic (Class III) \u2014 Follow label safety rules.",
    toxic_green: "Green Triangle: Slightly Toxic (Class IV) \u2014 Safer bio-rational or organic choice.",
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
    issue_too_dark: "Photo is too dark \u2014 take photo in bright daylight.",
    issue_too_bright: "Photo is overexposed/too bright \u2014 avoid direct sun glare.",
    issue_too_blurred: "Photo is blurred \u2014 hold camera steady and tap to focus on leaf.",
    issue_too_small: "Leaf is too far away \u2014 move closer so leaf fills the frame.",
    
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
    app_title: "\u0915\u0943\u0937\u093f\u0930\u0915\u094d\u0937\u0915",
    app_subtitle: "\u0921\u093f\u0935\u093e\u0907\u0938 \u092a\u0930 \u091a\u0932\u0928\u0947 \u0935\u093e\u0932\u093e \u092b\u0938\u0932 \u0938\u094d\u0935\u093e\u0938\u094d\u0925\u094d\u092f \u0938\u0932\u093e\u0939\u0915\u093e\u0930",
    tagline: "\u0930\u093e\u0938\u094d\u092a\u092c\u0947\u0930\u0940 \u092a\u093e\u0908 \u092a\u0930 100% \u0911\u092b\u0932\u093e\u0907\u0928 \u2022 \u092c\u093f\u0928\u093e \u0907\u0902\u091f\u0930\u0928\u0947\u091f \u091a\u0932\u0924\u093e \u0939\u0948",
    
    // Bottom Navigation
    nav_scan: "\u091c\u093e\u0902\u091a",
    nav_ai: "\u0915\u093f\u0938\u093e\u0928 AI",
    nav_weather: "\u092e\u094c\u0938\u092e \u0935 \u091b\u093f\u0921\u093c\u0915\u093e\u0935",
    nav_guide: "\u092e\u093e\u0930\u094d\u0917\u0926\u0930\u094d\u0936\u093f\u0915\u093e",
    
    // Actions & Navigation
    take_photo: "\u092b\u094b\u091f\u094b \u0932\u0947\u0902",
    choose_gallery: "\u0917\u0948\u0932\u0930\u0940 \u0938\u0947 \u091a\u0941\u0928\u0947\u0902",
    check_plant: "\u092a\u094c\u0927\u0947 \u0915\u0940 \u091c\u093e\u0902\u091a \u0915\u0930\u0947\u0902",
    take_another_photo: "\u0926\u0942\u0938\u0930\u0940 \u092b\u094b\u091f\u094b \u0932\u0947\u0902",
    back_to_home: "\u092e\u0941\u0916\u094d\u092f \u092a\u0943\u0937\u094d\u0920",
    try_again: "\u092a\u0941\u0928\u0903 \u092a\u094d\u0930\u092f\u093e\u0938 \u0915\u0930\u0947\u0902",
    ask: "AI \u0938\u0947 \u092a\u0942\u091b\u0947\u0902",
    close: "\u092c\u0902\u0926 \u0915\u0930\u0947\u0902",
    about_btn: "\u091c\u093e\u0928\u0915\u093e\u0930\u0940",
    history_btn: "\u0939\u093e\u0932 \u0915\u0940 \u091c\u093e\u0902\u091a",
    clear_history: "\u0907\u0924\u093f\u0939\u093e\u0938 \u092e\u093f\u091f\u093e\u090f\u0902",
    no_history: "\u0915\u094b\u0908 \u0939\u093e\u0932\u093f\u092f\u093e \u091c\u093e\u0902\u091a \u0938\u0939\u0947\u091c\u0940 \u0928\u0939\u0940\u0902 \u0917\u0908 \u0939\u0948\u0964",
    listen_voice: "\u092c\u094b\u0932\u0915\u0930 \u0938\u0941\u0928\u0947\u0902 (Voice)",
    stop_voice: "\u0906\u0935\u093e\u091c \u092c\u0902\u0926 \u0915\u0930\u0947\u0902",
    
    // Waiting Screen
    checking_plant: "\u0906\u092a\u0915\u0947 \u092a\u094c\u0927\u0947 \u0915\u0940 \u091c\u093e\u0902\u091a \u0939\u094b \u0930\u0939\u0940 \u0939\u0948...",
    waiting_desc: "\u0921\u093f\u0935\u093e\u0907\u0938 \u092a\u0930 AI \u0930\u094b\u0917, \u0915\u0940\u091f \u0914\u0930 \u0917\u0902\u092d\u0940\u0930\u0924\u093e \u0915\u0940 \u091c\u093e\u0901\u091a \u0915\u0930 \u0930\u0939\u093e \u0939\u0948\u0964 \u0907\u0938\u092e\u0947\u0902 \u0932\u0917\u092d\u0917 5-10 \u0938\u0947\u0915\u0902\u0921 \u0932\u0917\u0924\u0947 \u0939\u0948\u0902\u0964",
    device_error: "\u0915\u0943\u0937\u093f\u0930\u0915\u094d\u0937\u0915 \u0921\u093f\u0935\u093e\u0907\u0938 \u0938\u0947 \u0938\u0902\u092a\u0930\u094d\u0915 \u0928\u0939\u0940\u0902 \u0939\u094b \u0938\u0915\u093e\u0964 \u0915\u0943\u092a\u092f\u093e \u091c\u093e\u0902\u091a\u0947\u0902 \u0915\u093f \u092b\u094b\u0928 \u0915\u0943\u0937\u093f\u0930\u0915\u094d\u0937\u0915 \u0935\u093e\u0908-\u092b\u093c\u093e\u0908 \u0939\u0949\u091f\u0938\u094d\u092a\u0949\u091f \u0938\u0947 \u091c\u0941\u0921\u093c\u093e \u0939\u0948\u0964",
    timeout_error: "\u091c\u093e\u0902\u091a \u092e\u0947\u0902 60 \u0938\u0947\u0915\u0902\u0921 \u0938\u0947 \u0905\u0927\u093f\u0915 \u0938\u092e\u092f \u0932\u0917\u093e\u0964 \u0915\u0943\u092a\u092f\u093e \u092a\u0941\u0928\u0903 \u092a\u094d\u0930\u092f\u093e\u0938 \u0915\u0930\u0947\u0902\u0964",
    
    // Result Screen
    diagnosis_result: "\u0928\u093f\u0926\u093e\u0928 \u092a\u0930\u093f\u0923\u093e\u092e",
    confidence: "\u092e\u0949\u0921\u0932 \u0938\u091f\u0940\u0915\u0924\u093e",
    urgent_badge: "\u0924\u0924\u094d\u0915\u093e\u0932 \u0915\u093e\u0930\u094d\u0930\u0935\u093e\u0908 \u0915\u0930\u0947\u0902",
    healthy: "\u0938\u094d\u0935\u0938\u094d\u0925 \u092a\u0924\u094d\u0924\u093e",
    early_blight: "\u0905\u0917\u0947\u0924\u0940 \u091d\u0941\u0932\u0938\u093e",
    late_blight: "\u092a\u091b\u0947\u0924\u0940 \u091d\u0941\u0932\u0938\u093e",
    septoria_leaf_spot: "\u0938\u0947\u092a\u094d\u091f\u094b\u0930\u093f\u092f\u093e \u092a\u0924\u094d\u0924\u0940 \u0927\u092c\u094d\u092c\u093e",
    bacterial_spot: "\u091c\u0940\u0935\u093e\u0923\u0941 \u092a\u0924\u094d\u0924\u0940 \u0927\u092c\u094d\u092c\u093e",
    yellow_leaf_curl_virus: "\u092a\u0930\u094d\u0923 \u0915\u0941\u0902\u091a\u0928 \u0935\u093f\u0937\u093e\u0923\u0941",
    topic_healthy: "\u0938\u094d\u0935\u0938\u094d\u0925 \u092a\u0924\u094d\u0924\u093e",
    topic_early_blight: "\u0905\u0917\u0947\u0924\u0940 \u091d\u0941\u0932\u0938\u093e",
    topic_late_blight: "\u092a\u091b\u0947\u0924\u0940 \u091d\u0941\u0932\u0938\u093e",
    topic_septoria_leaf_spot: "\u0938\u0947\u092a\u094d\u091f\u094b\u0930\u093f\u092f\u093e \u092a\u0924\u094d\u0924\u0940 \u0927\u092c\u094d\u092c\u093e",
    topic_bacterial_spot: "\u091c\u0940\u0935\u093e\u0923\u0941 \u092a\u0924\u094d\u0924\u0940 \u0927\u092c\u094d\u092c\u093e",
    topic_yellow_leaf_curl_virus: "\u092a\u0930\u094d\u0923 \u0915\u0941\u0902\u091a\u0928 \u0935\u093f\u0937\u093e\u0923\u0941",
    spread_level: "\u092a\u0924\u094d\u0924\u0940 \u092a\u0930 \u0905\u0928\u0941\u092e\u093e\u0928\u093f\u0924 \u092b\u0948\u0932\u093e\u0935",
    spread_high: "\u0905\u0927\u093f\u0915 (High)",
    spread_medium: "\u092e\u0927\u094d\u092f\u092e (Medium)",
    spread_low: "\u0915\u092e (Low)",
    spread_moderate: "\u092e\u0927\u094d\u092f\u092e",
    spread_not_applicable: "\u092e\u093e\u092a\u093e \u0928\u0939\u0940\u0902 \u0917\u092f\u093e (\u0935\u093e\u092f\u0930\u0938)",
    sev_title: "\u0930\u094b\u0917 \u0915\u0940 \u0917\u0902\u092d\u0940\u0930\u0924\u093e (\u0907\u0938 \u092a\u0924\u094d\u0924\u0940 \u092a\u0930)",
    sev_share: "\u092a\u0924\u094d\u0924\u0940 \u0915\u0947 \u0932\u0917\u092d\u0917 {pct}% \u0939\u093f\u0938\u094d\u0938\u0947 \u092a\u0930 \u0930\u094b\u0917",
    sev_scale: "\u0915\u092e: \u092a\u0924\u094d\u0924\u0940 \u0915\u093e 10% \u0938\u0947 \u0915\u092e - \u092e\u0927\u094d\u092f\u092e: 10-25% - \u0905\u0927\u093f\u0915: 25% \u0938\u0947 \u0905\u0927\u093f\u0915\u0964",
    sev_note: "\u092f\u0939 \u0907\u0938 \u092b\u094b\u091f\u094b \u0938\u0947 \u0921\u093f\u0935\u093e\u0907\u0938 \u092a\u0930 \u0932\u0917\u093e\u092f\u093e \u0917\u092f\u093e \u0905\u0928\u0941\u092e\u093e\u0928 \u0939\u0948\u0964 \u0926\u0942\u0938\u0930\u0940 \u092a\u0924\u094d\u0924\u093f\u092f\u094b\u0902 \u0914\u0930 \u092a\u094c\u0927\u094b\u0902 \u0915\u094b \u092d\u0940 \u0926\u0947\u0916\u0947\u0902\u0964",
    sev_not_applicable: "\u0935\u093e\u092f\u0930\u0938 \u0930\u094b\u0917\u094b\u0902 \u0915\u0947 \u0932\u093f\u090f \u0917\u0902\u092d\u0940\u0930\u0924\u093e \u0938\u094d\u0924\u0930 \u0928\u0939\u0940\u0902 \u0926\u093f\u092f\u093e \u091c\u093e\u0924\u093e: \u0907\u0928\u092e\u0947\u0902 \u0927\u092c\u094d\u092c\u0947 \u0928\u0939\u0940\u0902, \u092a\u0942\u0930\u0947 \u092a\u094c\u0927\u0947 \u092e\u0947\u0902 \u092e\u0941\u0921\u093c\u0928\u093e \u0914\u0930 \u091a\u093f\u0924\u0915\u092c\u0930\u0947 \u0939\u094b\u0924\u0947 \u0939\u0948\u0902\u0964 \u0928\u0940\u091a\u0947 \u0926\u0940 \u0917\u0908 \u0938\u0932\u093e\u0939 \u092e\u093e\u0928\u0947\u0902\u0964",
    insect_found: "\u0915\u0940\u091f \u092a\u093e\u092f\u093e \u0917\u092f\u093e",
    translate_label: "\u0938\u0932\u093e\u0939 \u0907\u0938 \u092d\u093e\u0937\u093e \u092e\u0947\u0902 \u092d\u0940",
    translate_none: "\u0915\u0947\u0935\u0932 \u0905\u0902\u0917\u094d\u0930\u0947\u091c\u093c\u0940",
    mt_title: "\u0907\u0938 \u0921\u093f\u0935\u093e\u0907\u0938 \u092a\u0930 \u092e\u0936\u0940\u0928 \u0905\u0928\u0941\u0935\u093e\u0926 - \u0905\u092d\u0940 \u091c\u093e\u0901\u091a\u093e \u0928\u0939\u0940\u0902 \u0917\u092f\u093e",
    mt_withheld: "\u0915\u0941\u091b \u0935\u093e\u0915\u094d\u092f \u0905\u0928\u0941\u0935\u093e\u0926 \u091c\u093e\u0901\u091a \u092e\u0947\u0902 \u0935\u093f\u092b\u0932 \u0930\u0939\u0947, \u0935\u0947 \u0905\u0902\u0917\u094d\u0930\u0947\u091c\u093c\u0940 \u092e\u0947\u0902 \u0926\u093f\u0916\u093e\u090f \u0917\u090f \u0939\u0948\u0902\u0964",
    mt_show_english: "\u0905\u0902\u0917\u094d\u0930\u0947\u091c\u093c\u0940 \u092e\u0942\u0932 \u092a\u093e\u0920 \u0926\u093f\u0916\u093e\u090f\u0901",
    tts_no_voice: "\u0907\u0938 \u092b\u094b\u0928 \u092e\u0947\u0902 {lang} \u0906\u0935\u093e\u091c\u093c \u0928\u0939\u0940\u0902 \u0939\u0948, \u0907\u0938\u0932\u093f\u090f \u0905\u0902\u0917\u094d\u0930\u0947\u091c\u093c\u0940 \u092a\u0922\u093c\u0940 \u091c\u093e \u0930\u0939\u0940 \u0939\u0948\u0964 \u0907\u0902\u0938\u094d\u091f\u0949\u0932 \u0915\u0930\u0947\u0902: Settings > Text-to-speech > Speech Services by Google > Install voice data\u0964",
    tts_not_started: "\u0906\u0935\u093e\u091c\u093c \u0936\u0941\u0930\u0942 \u0928\u0939\u0940\u0902 \u0939\u0941\u0908\u0964 \u091c\u093e\u0901\u091a\u0947\u0902 \u0915\u093f \u0907\u0938 \u092d\u093e\u0937\u093e \u0915\u0940 \u0906\u0935\u093e\u091c\u093c \u0907\u0902\u0938\u094d\u091f\u0949\u0932 \u0939\u0948 \u0914\u0930 \u0911\u092b\u093c\u0932\u093e\u0907\u0928 \u0909\u092a\u092f\u094b\u0917 \u0915\u0947 \u0932\u093f\u090f \u0921\u093e\u0909\u0928\u0932\u094b\u0921 \u0939\u0948\u0964",
    tts_unsupported: "\u0907\u0938 \u092c\u094d\u0930\u093e\u0909\u091c\u093c\u0930 \u092e\u0947\u0902 \u0906\u0935\u093e\u091c\u093c \u092a\u0922\u093c\u0928\u0947 \u0915\u0940 \u0938\u0941\u0935\u093f\u0927\u093e \u0928\u0939\u0940\u0902 \u0939\u0948\u0964",
    kb_mt_note: "ICAR, NIPHM \u0914\u0930 TNAU \u0915\u0947 \u092a\u094d\u0930\u0915\u093e\u0936\u0928\u094b\u0902 \u0938\u0947 \u0932\u093f\u092f\u093e \u0917\u092f\u093e \u092a\u093e\u0920, \u092e\u0936\u0940\u0928 \u0905\u0928\u0941\u0935\u093e\u0926 (\u0905\u092d\u0940 \u091c\u093e\u0901\u091a\u093e \u0928\u0939\u0940\u0902 \u0917\u092f\u093e)\u0964 \u0926\u0935\u093e\u0913\u0902 \u0915\u0947 \u0928\u093e\u092e \u0914\u0930 \u092e\u093e\u0924\u094d\u0930\u093e \u092a\u094d\u0930\u0915\u093e\u0936\u093f\u0924 \u0930\u0942\u092a \u092e\u0947\u0902 \u0939\u0948\u0902\u0964",
    mt_unavailable: "AI \u0935\u094d\u092f\u093e\u0916\u094d\u092f\u093e \u0938\u0941\u0930\u0915\u094d\u0937\u093e \u091c\u093e\u0901\u091a \u092e\u0947\u0902 \u092a\u093e\u0938 \u0928\u0939\u0940\u0902 \u0939\u0941\u0908, \u0907\u0938\u0932\u093f\u090f \u0907\u0938 \u092b\u094b\u091f\u094b \u0915\u093e \u0905\u0928\u0941\u0935\u093e\u0926 \u0928\u0939\u0940\u0902 \u0939\u0948\u0964 \u0928\u0940\u091a\u0947 \u0926\u0940 \u0917\u0908 \u0938\u0924\u094d\u092f\u093e\u092a\u093f\u0924 \u0938\u0932\u093e\u0939 \u0905\u0902\u0917\u094d\u0930\u0947\u091c\u093c\u0940 \u092e\u0947\u0902 \u0939\u0948\u0964",
    pest_sev_title: "\u0907\u0938 \u092b\u094b\u091f\u094b \u092e\u0947\u0902 \u0915\u0940\u091f",
    pest_sev_photo_only: "\u092f\u0939 \u0938\u094d\u0924\u0930 \u0915\u0947\u0935\u0932 \u0907\u0938 \u092b\u094b\u091f\u094b \u0915\u093e \u0939\u0948 - \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0938\u0947 \u092a\u0939\u0932\u0947 \u0916\u0947\u0924 \u0915\u0940 \u091c\u093e\u0901\u091a \u0915\u0930\u0947\u0902\u0964",
    pest_sev_uncertain: "\u0915\u0940\u091f \u0915\u0940 \u092a\u094d\u0930\u091c\u093e\u0924\u093f \u0928\u093f\u0936\u094d\u091a\u093f\u0924 \u0928\u0939\u0940\u0902\u0964",
    pest_threshold: "\u092a\u094d\u0930\u0915\u093e\u0936\u093f\u0924 \u0915\u093e\u0930\u094d\u0930\u0935\u093e\u0908 \u0938\u094d\u0924\u0930",
    pest_scouting: "\u0905\u092a\u0928\u0947 \u0916\u0947\u0924 \u0915\u0940 \u091c\u093e\u0901\u091a \u0915\u0948\u0938\u0947 \u0915\u0930\u0947\u0902",
    level_low: "\u0915\u092e",
    level_moderate: "\u092e\u0927\u094d\u092f\u092e",
    level_high: "\u0905\u0927\u093f\u0915",
    species_label: "\u092a\u094d\u0930\u091c\u093e\u0924\u093f",
    important_notes: "\u092e\u0939\u0924\u094d\u0935\u092a\u0942\u0930\u094d\u0923 \u0906\u0927\u093f\u0915\u093e\u0930\u093f\u0915 \u0938\u0942\u091a\u0928\u093e\u090f\u0902",
    
    // Llama & Advice
    llama_card_title: "\u0938\u0932\u093e\u0939 (\u0907\u0938 \u0921\u093f\u0935\u093e\u0907\u0938 \u092a\u0930 Llama \u0926\u094d\u0935\u093e\u0930\u093e \u0938\u092e\u091d\u093e\u0908 \u0917\u0908)",
    llama_badge: "AI \u0938\u0930\u0932 \u092d\u093e\u0937\u093e",
    advice_title: "\u092a\u094d\u0930\u092e\u093e\u0923\u093f\u0924 \u0930\u094b\u0915\u0925\u093e\u092e \u090f\u0935\u0902 \u092a\u094d\u0930\u092c\u0902\u0927\u0928 \u0915\u0947 \u0909\u092a\u093e\u092f",
    source_label: "\u0938\u094d\u0930\u094b\u0924",
    
    // Advice Sections
    section_symptoms: "\u0930\u094b\u0917 \u0915\u0947 \u0932\u0915\u094d\u0937\u0923 \u090f\u0935\u0902 \u092a\u0939\u091a\u093e\u0928",
    section_spread: "\u092b\u0948\u0932\u093e\u0935 \u090f\u0935\u0902 \u091c\u0940\u0935\u093f\u0924 \u0930\u0939\u0928\u0947 \u0915\u0947 \u0915\u093e\u0930\u0923",
    section_cultural: "\u0916\u0947\u0924 \u0915\u0940 \u0938\u094d\u0935\u091a\u094d\u091b\u0924\u093e \u090f\u0935\u0902 \u0915\u0943\u0937\u093f \u092a\u094d\u0930\u092c\u0902\u0927\u0928",
    section_mechanical: "\u092d\u094c\u0924\u093f\u0915 \u090f\u0935\u0902 \u092f\u093e\u0902\u0924\u094d\u0930\u093f\u0915 \u0928\u093f\u092f\u0902\u0924\u094d\u0930\u0923",
    section_biological: "\u091c\u0948\u0935\u093f\u0915 \u090f\u0935\u0902 \u092c\u093e\u092f\u094b-\u092a\u0947\u0938\u094d\u091f\u093f\u0938\u093e\u0907\u0921 \u0928\u093f\u092f\u0902\u0924\u094d\u0930\u0923",
    section_monitoring: "\u0928\u093f\u0917\u0930\u093e\u0928\u0940 \u090f\u0935\u0902 \u091f\u094d\u0930\u0948\u092a\u093f\u0902\u0917 (\u0906\u0930\u094d\u0925\u093f\u0915 \u0938\u0940\u092e\u093e)",
    section_safety: "\u0938\u0941\u0930\u0915\u094d\u0937\u093e \u090f\u0935\u0902 \u0938\u093e\u0935\u0927\u093e\u0928\u0940",
    section_general: "\u0938\u093e\u092e\u093e\u0928\u094d\u092f \u0938\u093f\u092b\u093e\u0930\u093f\u0936\u0947\u0902",
    section_resistant_varieties: "\u0930\u094b\u0917 \u092a\u094d\u0930\u0924\u093f\u0930\u094b\u0927\u0940 \u0915\u093f\u0938\u094d\u092e\u0947\u0902",
    section_nutrition: "\u092a\u094b\u0937\u0923",
    section_natural_enemies: "\u092a\u094d\u0930\u093e\u0915\u0943\u0924\u093f\u0915 \u0936\u0924\u094d\u0930\u0941 (\u092e\u093f\u0924\u094d\u0930 \u0915\u0940\u091f)",
    section_chemical: "\u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u0947 \u0935\u093f\u0915\u0932\u094d\u092a",
    
    // Spray Table
    spray_title: "\u0915\u0940\u091f\u0928\u093e\u0936\u0915 / \u0915\u0935\u0915\u0928\u093e\u0936\u0940 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0935\u093f\u0915\u0932\u094d\u092a (\u0906\u0927\u093f\u0915\u093e\u0930\u093f\u0915)",
    spray_notice: "\u0928\u0940\u091a\u0947 \u0926\u093f\u090f \u0917\u090f \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0935\u093f\u0915\u0932\u094d\u092a ICAR, NIPHM \u0914\u0930 TNAU \u0915\u0947 \u092a\u094d\u0930\u0915\u093e\u0936\u0928\u094b\u0902 \u0938\u0947 \u0939\u0942\u092c\u0939\u0942 \u0932\u093f\u090f \u0917\u090f \u0939\u0948\u0902\u0964 \u0938\u0941\u0930\u0915\u094d\u0937\u093e\u0924\u094d\u092e\u0915 \u0915\u092a\u0921\u093c\u0947 \u092a\u0939\u0928\u0947\u0902 \u0914\u0930 \u0924\u0941\u0921\u093c\u093e\u0908 \u092a\u094d\u0930\u0924\u0940\u0915\u094d\u0937\u093e \u0905\u0935\u0927\u093f \u0915\u093e \u092a\u093e\u0932\u0928 \u0915\u0930\u0947\u0902\u0964",
    col_product: "\u0909\u0924\u094d\u092a\u093e\u0926 \u0915\u093e \u0928\u093e\u092e",
    col_dose: "\u092e\u093e\u0924\u094d\u0930\u093e",
    col_note: "\u0932\u0947\u092c\u0932 / \u0924\u0941\u0921\u093c\u093e\u0908 \u092a\u094d\u0930\u0924\u0940\u0915\u094d\u0937\u093e \u091f\u093f\u092a\u094d\u092a\u0923\u0940",
    col_source: "\u0906\u0927\u093f\u0915\u093e\u0930\u093f\u0915 \u0938\u094d\u0930\u094b\u0924",
    
    // Q&A & Kisan AI
    ask_title: "\u0915\u093f\u0938\u093e\u0928 AI \u092e\u093f\u0924\u094d\u0930 (\u0921\u093f\u0935\u093e\u0907\u0938 \u092a\u0930 Llama \u092e\u0949\u0921\u0932)",
    ask_desc: "\u091f\u092e\u093e\u091f\u0930 \u0915\u0947 \u0930\u094b\u0917, \u0915\u0940\u091f \u0928\u093f\u092f\u0902\u0924\u094d\u0930\u0923 \u092f\u093e \u0924\u0941\u0921\u093c\u093e\u0908 \u0938\u092e\u092f \u0915\u0947 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902 \u0915\u094b\u0908 \u092d\u0940 \u092a\u094d\u0930\u0936\u094d\u0928 \u092a\u0942\u091b\u0947\u0902\u0964",
    ask_placeholder: "\u0905\u092a\u0928\u093e \u0938\u0935\u093e\u0932 \u0932\u093f\u0916\u0947\u0902 \u092f\u093e \u092c\u094b\u0932\u0947\u0902...",
    ask_waiting: "\u0921\u093f\u0935\u093e\u0907\u0938 \u0938\u0947 \u092a\u094d\u0930\u092e\u093e\u0923\u093f\u0924 \u0909\u0924\u094d\u0924\u0930 \u0916\u094b\u091c\u093e \u091c\u093e \u0930\u0939\u093e \u0939\u0948...",
    mic_btn: "\u092c\u094b\u0932 \u0915\u0930 \u092a\u0942\u091b\u0947\u0902",
    mic_listening: "\u0938\u0941\u0928 \u0930\u0939\u093e \u0939\u0948... \u092c\u094b\u0932\u0947\u0902",
    mic_error: "\u0906\u0935\u093e\u091c\u093c \u092a\u0939\u091a\u093e\u0928 \u0928\u0939\u0940\u0902 \u0938\u0915\u0947\u0964 \u092b\u093f\u0930 \u092a\u094d\u0930\u092f\u093e\u0938 \u0915\u0930\u0947\u0902\u0964",
    mic_not_supported: "\u0907\u0938 \u0921\u093f\u0935\u093e\u0907\u0938 \u092a\u0930 \u0935\u0949\u092f\u0938 \u0907\u0928\u092a\u0941\u091f \u0909\u092a\u0932\u092c\u094d\u0927 \u0928\u0939\u0940\u0902 \u0939\u0948\u0964",
    verified_facts_title: "\u092a\u094d\u0930\u092e\u093e\u0923\u093f\u0924 \u0938\u0902\u0926\u0930\u094d\u092d \u0924\u0925\u094d\u092f:",
    llama_rejected_notice: "\u0938\u0930\u0932 \u092d\u093e\u0937\u093e \u092e\u0947\u0902 \u0935\u094d\u092f\u093e\u0916\u094d\u092f\u093e \u0938\u0924\u094d\u092f\u093e\u092a\u093f\u0924 \u0928\u0939\u0940\u0902 \u0939\u094b \u0938\u0915\u0940\u0964 \u0915\u0943\u092a\u092f\u093e \u0928\u0940\u091a\u0947 \u0926\u093f\u090f \u0917\u090f \u092a\u094d\u0930\u092e\u093e\u0923\u093f\u0924 \u0906\u0927\u093f\u0915\u093e\u0930\u093f\u0915 \u0924\u0925\u094d\u092f\u094b\u0902 \u0915\u094b \u092a\u0922\u093c\u0947\u0902:",
    chip_q1: "\u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u0947 \u0915\u093f\u0924\u0928\u0947 \u0926\u093f\u0928 \u092c\u093e\u0926 \u0924\u0941\u0921\u093c\u093e\u0908 \u0915\u0930\u0947\u0902?",
    chip_q2: "\u0930\u094b\u0917 \u0915\u094b \u0906\u0917\u0947 \u092b\u0948\u0932\u0928\u0947 \u0938\u0947 \u0915\u0948\u0938\u0947 \u0930\u094b\u0915\u0947\u0902?",
    chip_q3: "\u091c\u0948\u0935\u093f\u0915 \u0935 \u0926\u0947\u0938\u0940 \u0928\u093f\u092f\u0902\u0924\u094d\u0930\u0923 \u0915\u0947 \u0915\u094d\u092f\u093e \u0909\u092a\u093e\u092f \u0939\u0948\u0902?",
    chip_q4: "\u091d\u0941\u0932\u0938\u093e \u0930\u094b\u0917 \u092e\u0947\u0902 \u0938\u093f\u0902\u091a\u093e\u0908 \u0915\u0948\u0938\u0947 \u0915\u0930\u0947\u0902?",
    tip_daylight: "\u092a\u094d\u0930\u093e\u0915\u0943\u0924\u093f\u0915 \u0930\u094b\u0936\u0928\u0940",
    tip_sharp: "\u0928\u091c\u093c\u0926\u0940\u0915 \u0935 \u0938\u093e\u092b\u093c \u092b\u094b\u091f\u094b",
    tip_single_leaf: "\u090f\u0915 \u0939\u0940 \u092a\u0924\u094d\u0924\u0940",
    leaf_alignment_hint: "\u092a\u094d\u0930\u092d\u093e\u0935\u093f\u0924 \u092a\u0924\u094d\u0924\u0940 \u0915\u094b \u092b\u094d\u0930\u0947\u092e \u0915\u0947 \u092c\u0940\u091a \u092e\u0947\u0902 \u0930\u0916\u0947\u0902",
    llama_online: "\u0921\u093f\u0935\u093e\u0907\u0938 \u092a\u0930 Llama \u2022 \u092c\u093f\u0928\u093e \u0907\u0902\u091f\u0930\u0928\u0947\u091f",
    ai_grounded_badge: "\u092a\u094d\u0930\u092e\u093e\u0923\u093f\u0924 ICAR / NIPHM",
    chat_welcome: "\u0928\u092e\u0938\u094d\u0924\u0947! \u092e\u0948\u0902 \u0906\u092a\u0915\u093e \u0915\u093f\u0938\u093e\u0928 AI \u092e\u093f\u0924\u094d\u0930 \u0939\u0942\u0902\u0964 \u091f\u092e\u093e\u091f\u0930 \u0915\u0947 \u0930\u094b\u0917, \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u092f\u093e \u0924\u0941\u0921\u093c\u093e\u0908 \u0938\u092e\u092f \u0915\u0947 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902 \u0915\u094b\u0908 \u092d\u0940 \u0938\u0935\u093e\u0932 \u092a\u0942\u091b\u0947\u0902\u0964",
    chat_now: "\u0905\u092d\u0940",
    speaking_label: "{lang} \u092e\u0947\u0902 \u092c\u094b\u0932 \u0930\u0939\u093e \u0939\u0948...",
    
    // Field Conditions & Spray Prediction
    weather_title: "\u0916\u0947\u0924 \u0915\u0940 \u0938\u094d\u0925\u093f\u0924\u093f \u090f\u0935\u0902 \u0938\u094d\u092a\u094d\u0930\u0947 \u0938\u0932\u093e\u0939",
    weather_desc: "\u0916\u0947\u0924 \u092e\u0947\u0902 \u0939\u0935\u093e, \u0924\u093e\u092a\u092e\u093e\u0928 \u0914\u0930 \u092c\u093e\u0930\u093f\u0936 \u0915\u0940 \u0938\u094d\u0925\u093f\u0924\u093f \u091a\u0941\u0928\u0947\u0902 \u0914\u0930 \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u093e \u092a\u0942\u0930\u094d\u0935\u093e\u0928\u0941\u092e\u093e\u0928 \u092a\u093e\u090f\u0902\u0964",
    spray_favorable: "\u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u0947 \u0932\u093f\u090f \u092e\u094c\u0938\u092e \u0905\u0928\u0941\u0915\u0942\u0932 \u0939\u0948",
    spray_unfavorable: "\u0935\u0930\u094d\u0924\u092e\u093e\u0928 \u0938\u092e\u092f \u092e\u0947\u0902 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0928 \u0915\u0930\u0947\u0902",
    temp_label: "\u0924\u093e\u092a\u092e\u093e\u0928",
    humidity_label: "\u0928\u092e\u0940 (\u0906\u0930\u094d\u0926\u094d\u0930\u0924\u093e)",
    wind_label: "\u0939\u0935\u093e \u0915\u0940 \u0917\u0924\u093f",
    rain_label: "\u092c\u093e\u0930\u093f\u0936 \u0915\u0940 \u0938\u0902\u092d\u093e\u0935\u0928\u093e",
    spray_tip_title: "\u0915\u0943\u0937\u093f \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0938\u0932\u093e\u0939:",
    spray_tip_text: "\u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u093e \u0938\u092c\u0938\u0947 \u0909\u0924\u094d\u0924\u092e \u0938\u092e\u092f: \u0938\u0941\u092c\u0939 7:00 \u0938\u0947 10:00 \u092c\u091c\u0947 \u092f\u093e \u0936\u093e\u092e 4:00 \u0938\u0947 6:30 \u092c\u091c\u0947\u0964 \u0924\u0947\u091c \u0939\u0935\u093e (>12 \u0915\u093f\u092e\u0940/\u0918\u0902\u091f\u093e) \u092f\u093e \u0924\u0947\u091c \u0926\u094b\u092a\u0939\u0930 \u0915\u0940 \u0927\u0942\u092a \u092e\u0947\u0902 \u0915\u092d\u0940 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0928 \u0915\u0930\u0947\u0902\u0964",
    weather_q_section_title: "\u0916\u0947\u0924 \u0915\u0947 \u092e\u094c\u0938\u092e \u0915\u0947 \u0938\u0935\u093e\u0932",
    weather_q_section_desc: "\u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u0940 \u0938\u0941\u0930\u0915\u094d\u0937\u093e \u091c\u093e\u0902\u091a\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f 3 \u0938\u0935\u093e\u0932\u094b\u0902 \u0915\u093e \u091a\u092f\u0928 \u0915\u0930\u0947\u0902:",
    q_wind_label: "1. \u0906\u092a\u0915\u0947 \u0916\u0947\u0924 \u092e\u0947\u0902 \u0939\u0935\u093e \u0915\u0948\u0938\u0940 \u091a\u0932 \u0930\u0939\u0940 \u0939\u0948?",
    opt_wind_calm: "\u0936\u093e\u0902\u0924 \u0939\u0935\u093e (< 6 km/h)",
    opt_wind_breeze: "\u0939\u0932\u094d\u0915\u0940 \u0939\u0935\u093e (7-12 km/h)",
    opt_wind_strong: "\u0924\u0947\u091c\u093c \u0939\u0935\u093e (> 15 km/h)",
    q_temp_label: "2. \u0907\u0938 \u0938\u092e\u092f \u0927\u0942\u092a \u0935 \u0917\u0930\u094d\u092e\u0940 \u0915\u0948\u0938\u0940 \u0939\u0948?",
    opt_temp_morning: "\u0938\u0941\u092c\u0939 / \u0920\u0902\u0921\u0915 (25\u00b0C)",
    opt_temp_afternoon: "\u0936\u093e\u092e \u0915\u093e \u0938\u092e\u092f (29\u00b0C)",
    opt_temp_scorching: "\u0926\u094b\u092a\u0939\u0930 \u0915\u0940 \u0924\u0947\u091c\u093c \u0927\u0942\u092a (> 34\u00b0C)",
    q_rain_label: "3. \u0906\u0938\u092e\u093e\u0928 \u0914\u0930 \u092c\u093e\u0930\u093f\u0936 \u0915\u0940 \u0915\u094d\u092f\u093e \u0938\u094d\u0925\u093f\u0924\u093f \u0939\u0948?",
    opt_rain_clear: "\u0938\u093e\u092b\u093c \u0906\u0938\u092e\u093e\u0928 (\u092c\u093e\u0930\u093f\u0936 \u0928\u0939\u0940\u0902)",
    opt_rain_cloudy: "\u092c\u093e\u0926\u0932 \u091b\u093e\u090f \u0939\u0948\u0902",
    opt_rain_expected: "\u092c\u093e\u0930\u093f\u0936 \u0939\u094b \u0930\u0939\u0940 \u0939\u0948 / \u0938\u0902\u092d\u093e\u0935\u0928\u093e",
    faq_title: "\u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0935 \u092e\u094c\u0938\u092e \u0938\u0902\u092c\u0902\u0927\u0940 \u092e\u0941\u0916\u094d\u092f \u0938\u0935\u093e\u0932",
    faq_q1: "\u0915\u0940\u091f\u0928\u093e\u0936\u0915 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u093e \u0938\u092c\u0938\u0947 \u0905\u091a\u094d\u091b\u093e \u0938\u092e\u092f \u0915\u094c\u0928 \u0938\u093e \u0939\u0948?",
    faq_a1: "\u0938\u0941\u092c\u0939 7 \u0938\u0947 10 \u092c\u091c\u0947 \u092f\u093e \u0936\u093e\u092e 4 \u0938\u0947 6:30 \u092c\u091c\u0947\u0964 \u0926\u094b\u092a\u0939\u0930 \u0915\u0940 \u0915\u0921\u093c\u0915 \u0927\u0942\u092a \u092e\u0947\u0902 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0928 \u0915\u0930\u0947\u0902\u0964",
    faq_q2: "\u0924\u0947\u091c\u093c \u0939\u0935\u093e (>15 km/h) \u092e\u0947\u0902 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u094d\u092f\u094b\u0902 \u0928\u0939\u0940\u0902 \u0915\u0930\u0928\u093e \u091a\u093e\u0939\u093f\u090f?",
    faq_a2: "\u0924\u0947\u091c\u093c \u0939\u0935\u093e \u0938\u0947 \u0926\u0935\u093e \u0909\u0921\u093c\u0915\u0930 \u0926\u0942\u0938\u0930\u0940 \u092b\u093c\u0938\u0932\u094b\u0902 \u092f\u093e \u0915\u093f\u0938\u093e\u0928 \u092a\u0930 \u0917\u093f\u0930\u0924\u0940 \u0939\u0948, \u091c\u093f\u0938\u0938\u0947 \u0926\u0935\u093e \u092c\u0930\u094d\u092c\u093e\u0926 \u0939\u094b\u0924\u0940 \u0939\u0948\u0964",
    faq_q3: "\u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u0947 \u0924\u0941\u0930\u0902\u0924 \u092c\u093e\u0926 \u092c\u093e\u0930\u093f\u0936 \u0939\u094b \u091c\u093e\u090f \u0924\u094b \u0915\u094d\u092f\u093e \u0939\u094b\u0917\u093e?",
    faq_a3: "\u092c\u093e\u0930\u093f\u0936 \u0938\u0947 \u0926\u0935\u093e \u092a\u0924\u094d\u0924\u094b\u0902 \u0938\u0947 \u0927\u0941\u0932 \u091c\u093e\u0924\u0940 \u0939\u0948\u0964 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u0947 \u092c\u093e\u0926 \u0915\u092e \u0938\u0947 \u0915\u092e 2 \u0938\u0947 4 \u0918\u0902\u091f\u0947 \u092e\u094c\u0938\u092e \u0938\u0942\u0916\u093e \u0930\u0939\u0928\u093e \u091a\u093e\u0939\u093f\u090f\u0964",
    faq_q4: "\u0924\u0941\u0921\u093c\u093e\u0908 \u0938\u092e\u092f (PHI) \u0915\u093e \u0927\u094d\u092f\u093e\u0928 \u0930\u0916\u0928\u093e \u0915\u094d\u092f\u094b\u0902 \u091c\u093c\u0930\u0942\u0930\u0940 \u0939\u0948?",
    faq_a4: "\u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0914\u0930 \u092b\u093c\u0938\u0932 \u0924\u094b\u0921\u093c\u0928\u0947 \u0915\u0947 \u092c\u0940\u091a \u0928\u093f\u0930\u094d\u0927\u093e\u0930\u093f\u0924 \u0926\u093f\u0928\u094b\u0902 \u0915\u093e \u0905\u0902\u0924\u0930 \u0930\u0916\u0947\u0902, \u0924\u093e\u0915\u093f \u091f\u092e\u093e\u091f\u0930 \u092e\u0947\u0902 \u0915\u0940\u091f\u0928\u093e\u0936\u0915 \u0915\u093e \u0905\u0902\u0936 \u0928 \u0930\u0939\u0947\u0964",
    
    // Kisan Guide
    guide_title: "\u0915\u093f\u0938\u093e\u0928 \u0938\u0941\u0930\u0915\u094d\u0937\u093e \u090f\u0935\u0902 \u092e\u093e\u0930\u094d\u0917\u0926\u0930\u094d\u0936\u093f\u0915\u093e",
    helpline_title: "\u0938\u0930\u0915\u093e\u0930\u0940 \u0915\u093f\u0938\u093e\u0928 \u0939\u0947\u0932\u094d\u092a\u0932\u093e\u0907\u0928",
    kisan_call_center: "\u0915\u093f\u0938\u093e\u0928 \u0915\u0949\u0932 \u0938\u0947\u0902\u091f\u0930: 1800-180-1551 (\u091f\u094b\u0932 \u092b\u094d\u0930\u0940, \u0938\u0941\u092c\u0939 6 \u0938\u0947 \u0930\u093e\u0924 10)",
    kvk_contact: "\u0916\u0947\u0924 \u0915\u0940 \u092e\u093f\u091f\u094d\u091f\u0940 \u0935 \u0930\u094b\u0917 \u091c\u093e\u0902\u091a \u0915\u0947 \u0932\u093f\u090f \u0905\u092a\u0928\u0947 \u091c\u093f\u0932\u093e \u0915\u0943\u0937\u093f \u0935\u093f\u091c\u094d\u091e\u093e\u0928 \u0915\u0947\u0902\u0926\u094d\u0930 (KVK) \u0938\u0947 \u0938\u0902\u092a\u0930\u094d\u0915 \u0915\u0930\u0947\u0902\u0964",
    cibrc_title: "\u0915\u0947\u0902\u0926\u094d\u0930\u0940\u092f \u0915\u0940\u091f\u0928\u093e\u0936\u0940 \u092c\u094b\u0930\u094d\u0921 (CIB&RC) \u0935\u093f\u0937\u093e\u0915\u094d\u0924\u0924\u093e \u0930\u0902\u0917 \u0938\u0902\u0915\u0947\u0924",
    toxic_red: "\u0932\u093e\u0932 \u0924\u094d\u0930\u093f\u0915\u094b\u0923: \u0905\u0924\u094d\u092f\u0927\u093f\u0915 \u0935\u093f\u0937\u093e\u0915\u094d\u0924 (Class I) \u2014 \u0905\u0924\u094d\u092f\u0902\u0924 \u0916\u0924\u0930\u0928\u093e\u0915, \u092a\u0942\u0930\u094d\u0923 \u0938\u0941\u0930\u0915\u094d\u0937\u093e \u0909\u092a\u0915\u0930\u0923 \u092a\u0939\u0928\u0947\u0902\u0964",
    toxic_yellow: "\u092a\u0940\u0932\u093e \u0924\u094d\u0930\u093f\u0915\u094b\u0923: \u0905\u0924\u093f \u0935\u093f\u0937\u093e\u0915\u094d\u0924 (Class II) \u2014 \u0935\u093f\u0936\u0947\u0937 \u0938\u093e\u0935\u0927\u093e\u0928\u0940 \u0906\u0935\u0936\u094d\u092f\u0915\u0964",
    toxic_blue: "\u0928\u0940\u0932\u093e \u0924\u094d\u0930\u093f\u0915\u094b\u0923: \u092e\u0927\u094d\u092f\u092e \u0935\u093f\u0937\u093e\u0915\u094d\u0924 (Class III) \u2014 \u0932\u0947\u092c\u0932 \u0928\u093f\u0930\u094d\u0926\u0947\u0936 \u0905\u0928\u0941\u0938\u093e\u0930 \u0909\u092a\u092f\u094b\u0917 \u0915\u0930\u0947\u0902\u0964",
    toxic_green: "\u0939\u0930\u093e \u0924\u094d\u0930\u093f\u0915\u094b\u0923: \u0915\u092e \u0935\u093f\u0937\u093e\u0915\u094d\u0924 (Class IV) \u2014 \u091c\u0948\u0935\u093f\u0915 \u0935 \u0905\u092a\u0947\u0915\u094d\u0937\u093e\u0915\u0943\u0924 \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0935\u093f\u0915\u0932\u094d\u092a\u0964",
    golden_rules_title: "\u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u0947 5 \u0938\u0941\u0928\u0939\u0930\u0947 \u0928\u093f\u092f\u092e",
    rule_1: "1. \u0938\u0941\u0930\u0915\u094d\u0937\u093e\u0924\u094d\u092e\u0915 \u0915\u092a\u0921\u093c\u0947: \u092e\u093e\u0938\u094d\u0915, \u0926\u0938\u094d\u0924\u093e\u0928\u0947 \u0914\u0930 \u091c\u0942\u0924\u0947 \u091c\u0930\u0942\u0930 \u092a\u0939\u0928\u0947\u0902\u0964",
    rule_2: "2. \u092c\u0902\u0926 \u0928\u094b\u091c\u0932 \u0915\u094b \u0915\u092d\u0940 \u092e\u0941\u0902\u0939 \u0938\u0947 \u0928 \u092b\u0942\u0902\u0915\u0947\u0902; \u0938\u093e\u092b \u092a\u093e\u0928\u0940 \u0914\u0930 \u092c\u094d\u0930\u0936 \u0915\u093e \u0909\u092a\u092f\u094b\u0917 \u0915\u0930\u0947\u0902\u0964",
    rule_3: "3. \u0939\u0935\u093e \u0915\u0940 \u0926\u093f\u0936\u093e \u092e\u0947\u0902 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u0930\u0947\u0902, \u0926\u0935\u093e \u0915\u0947 \u092b\u0941\u0939\u093e\u0930 \u0915\u0940 \u0909\u0932\u094d\u091f\u0940 \u0926\u093f\u0936\u093e \u092e\u0947\u0902 \u0928 \u091a\u0932\u0947\u0902\u0964",
    rule_4: "4. \u092b\u0938\u0932 \u0924\u0941\u0921\u093c\u093e\u0908 \u0938\u0947 \u092a\u0939\u0932\u0947 \u0932\u0947\u092c\u0932 \u092a\u0930 \u0926\u0940 \u0917\u0908 \u092a\u094d\u0930\u0924\u0940\u0915\u094d\u0937\u093e \u0905\u0935\u0927\u093f (PHI) \u0915\u093e \u0915\u0921\u093c\u093e\u0908 \u0938\u0947 \u092a\u093e\u0932\u0928 \u0915\u0930\u0947\u0902\u0964",
    rule_5: "5. \u0916\u093e\u0932\u0940 \u0921\u093f\u092c\u094d\u092c\u094b\u0902 \u0915\u094b \u0924\u0940\u0928 \u092c\u093e\u0930 \u0927\u094b\u0915\u0930 \u0928\u0937\u094d\u091f \u0915\u0930\u0947\u0902; \u092a\u093e\u0928\u0940 \u092f\u093e \u091a\u093e\u0930\u0947 \u0915\u0947 \u0932\u093f\u090f \u092a\u094d\u0930\u092f\u094b\u0917 \u0928 \u0915\u0930\u0947\u0902\u0964",
    
    // Uncertain & Retake
    uncertain_title: "\u0928\u093f\u0926\u093e\u0928 \u0905\u0928\u093f\u0936\u094d\u091a\u093f\u0924 \u0939\u0948",
    uncertain_desc: "\u092e\u0949\u0921\u0932 \u0907\u0938 \u092a\u0924\u094d\u0924\u0947 \u0915\u0947 \u0930\u094b\u0917 \u0915\u0947 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902 \u092a\u0930\u094d\u092f\u093e\u092a\u094d\u0924 \u0906\u0936\u094d\u0935\u0938\u094d\u0924 \u0928\u0939\u0940\u0902 \u0939\u0948\u0964",
    uncertain_tips_title: "\u0938\u0941\u091d\u093e\u090f \u0917\u090f \u0915\u0926\u092e:",
    uncertain_tip_1: "\u0926\u093f\u0928 \u0915\u0940 \u092a\u094d\u0930\u093e\u0915\u0943\u0924\u093f\u0915 \u0927\u0942\u092a \u092e\u0947\u0902 \u090f\u0915 \u092a\u094d\u0930\u092d\u093e\u0935\u093f\u0924 \u092a\u0924\u094d\u0924\u0947 \u0915\u0940 \u0938\u093e\u092b \u0914\u0930 \u0938\u094d\u092a\u0937\u094d\u091f \u092b\u094b\u091f\u094b \u0932\u0947\u0902\u0964",
    uncertain_tip_2: "\u092a\u094c\u0927\u0947 \u0915\u094b \u0905\u092a\u0928\u0947 \u0928\u091c\u0926\u0940\u0915\u0940 \u0915\u0943\u0937\u093f \u0935\u093f\u091c\u094d\u091e\u093e\u0928 \u0915\u0947\u0902\u0926\u094d\u0930 (KVK) \u092f\u093e \u0915\u0943\u0937\u093f \u0905\u0927\u093f\u0915\u093e\u0930\u0940 \u0915\u094b \u0926\u093f\u0916\u093e\u090f\u0902\u0964",
    retake_title: "\u0915\u0943\u092a\u092f\u093e \u0926\u094b\u092c\u093e\u0930\u093e \u092b\u094b\u091f\u094b \u0932\u0947\u0902",
    retake_desc: "\u092b\u094b\u091f\u094b \u0915\u0940 \u0917\u0941\u0923\u0935\u0924\u094d\u0924\u093e \u0930\u094b\u0917 \u092a\u0939\u091a\u093e\u0928\u0928\u0947 \u092f\u094b\u0917\u094d\u092f \u0928\u0939\u0940\u0902 \u0939\u0948\u0964",
    quality_issues: "\u092b\u094b\u091f\u094b \u092e\u0947\u0902 \u092a\u093e\u0908 \u0917\u0908 \u0915\u092e\u093f\u092f\u093e\u0902:",
    issue_too_dark: "\u092b\u094b\u091f\u094b \u092c\u0939\u0941\u0924 \u0905\u0902\u0927\u0947\u0930\u0940 \u0939\u0948 \u2014 \u092a\u094d\u0930\u093e\u0915\u0943\u0924\u093f\u0915 \u0930\u094b\u0936\u0928\u0940 \u092e\u0947\u0902 \u092b\u094b\u091f\u094b \u0916\u0940\u0902\u091a\u0947\u0902\u0964",
    issue_too_bright: "\u092b\u094b\u091f\u094b \u092c\u0939\u0941\u0924 \u0905\u0927\u093f\u0915 \u091a\u092e\u0915\u0926\u093e\u0930 \u0939\u0948 \u2014 \u0938\u0940\u0927\u0940 \u0927\u0942\u092a \u0915\u0940 \u091a\u092e\u0915 \u0938\u0947 \u092c\u091a\u0947\u0902\u0964",
    issue_too_blurred: "\u092b\u094b\u091f\u094b \u0927\u0941\u0902\u0927\u0932\u0940 \u0939\u0948 \u2014 \u0915\u0948\u092e\u0930\u093e \u0938\u094d\u0925\u093f\u0930 \u0930\u0916\u0947\u0902 \u0914\u0930 \u092a\u0924\u094d\u0924\u0947 \u092a\u0930 \u092b\u094b\u0915\u0938 \u0915\u0930\u0947\u0902\u0964",
    issue_too_small: "\u092a\u0924\u094d\u0924\u093e \u092c\u0939\u0941\u0924 \u0926\u0942\u0930 \u0939\u0948 \u2014 \u092a\u093e\u0938 \u091c\u093e\u0915\u0930 \u092a\u0924\u094d\u0924\u0947 \u0915\u094b \u0938\u094d\u0915\u094d\u0930\u0940\u0928 \u092e\u0947\u0902 \u092d\u0930\u0947\u0902\u0964",
    
    // About
    about_title: "\u0915\u0943\u0937\u093f\u0930\u0915\u094d\u0937\u0915 \u0915\u0947 \u092c\u093e\u0930\u0947 \u092e\u0947\u0902",
    about_desc: "\u0915\u0943\u0937\u093f\u0930\u0915\u094d\u0937\u0915 \u092d\u093e\u0930\u0924 AI-SoC \u091a\u0948\u0932\u0947\u0902\u091c \u0915\u0947 \u0924\u0939\u0924 \u092d\u093e\u0930\u0924\u0940\u092f \u0915\u093f\u0938\u093e\u0928\u094b\u0902 \u0915\u0947 \u0932\u093f\u090f \u092c\u0928\u093e\u092f\u093e \u0917\u092f\u093e \u0911\u0928-\u0921\u093f\u0935\u093e\u0907\u0938, \u092c\u093f\u0928\u093e \u0907\u0902\u091f\u0930\u0928\u0947\u091f \u091a\u0932\u0928\u0947 \u0935\u093e\u0932\u093e \u092b\u0938\u0932 \u0930\u094b\u0917 \u090f\u0935\u0902 \u0915\u0940\u091f \u0938\u0932\u093e\u0939\u0915\u093e\u0930 \u0939\u0948\u0964",
    about_req_icar: "Advice from ICAR, NIPHM and TNAU publications",
    about_req_llama: "Built with Llama",
    sys_details: "\u0938\u093f\u0938\u094d\u091f\u092e \u090f\u0935\u0902 \u092e\u0949\u0921\u0932 \u0935\u093f\u0935\u0930\u0923",
    disease_model: "\u0930\u094b\u0917 \u092a\u0939\u091a\u093e\u0928 \u092e\u0949\u0921\u0932",
    pest_model: "\u0915\u0940\u091f \u092a\u0939\u091a\u093e\u0928 \u092e\u0949\u0921\u0932",
    llama_model: "\u0911\u0928-\u0921\u093f\u0935\u093e\u0907\u0938 \u092d\u093e\u0937\u093e \u092e\u0949\u0921\u0932",
    kb_version: "\u091c\u094d\u091e\u093e\u0928 \u092d\u0902\u0921\u093e\u0930 (KB) \u0938\u0902\u0938\u094d\u0915\u0930\u0923",
    kb_draft: "\u092a\u094d\u0930\u093e\u0930\u0942\u092a (\u0935\u093f\u0936\u0947\u0937\u091c\u094d\u091e \u0938\u092e\u0940\u0915\u094d\u0937\u093e\u0927\u0940\u0928)",
    kb_reviewed: "\u0938\u0924\u094d\u092f\u093e\u092a\u093f\u0924",
    runtime_env: "\u0930\u0928\u091f\u093e\u0907\u092e",
    api_server_setting: "API \u0938\u0930\u094d\u0935\u0930 \u092a\u0924\u093e",
    api_server_hint: "\u092a\u093e\u0908 \u0938\u0930\u094d\u0935\u0930 \u0915\u0947 \u0932\u093f\u090f \u0916\u093e\u0932\u0940 \u091b\u094b\u0921\u093c\u0947\u0902, \u092f\u093e \u092e\u0949\u0915 \u0938\u0930\u094d\u0935\u0930 \u0939\u0947\u0924\u0941 http://localhost:8080 \u0926\u0930\u094d\u091c \u0915\u0930\u0947\u0902\u0964",
    save_setting: "\u0938\u0939\u0947\u091c\u0947\u0902 \u0914\u0930 \u092a\u0941\u0928\u0903 \u0932\u094b\u0921 \u0915\u0930\u0947\u0902",
    
    // Technical
    tech_details: "\u0924\u0915\u0928\u0940\u0915\u0940 \u0935\u093f\u0935\u0930\u0923 \u090f\u0935\u0902 \u0938\u092e\u092f (Timings)",
    total_time: "\u0915\u0941\u0932 \u0928\u093f\u0937\u094d\u0915\u0930\u094d\u0937 \u0938\u092e\u092f",
    vision_time: "\u0935\u093f\u091c\u093c\u0928 \u092e\u0949\u0921\u0932 (\u0930\u094b\u0917 + \u0915\u0940\u091f)",
    llama_time: "Llama \u090f\u0932\u090f\u0932\u090f\u092e \u0938\u092e\u092f",
    tokens_sec: "\u091f\u094b\u0915\u0928 \u092a\u094d\u0930\u0924\u093f \u0938\u0947\u0915\u0902\u0921"
  }
};

let currentLanguage = window.CONFIG ? window.CONFIG.DEFAULT_LANG : "en";

function setLanguage(lang) {
  if (!I18N[lang]) lang = "en";
  currentLanguage = lang;
  localStorage.setItem("KR_LANG", lang);
  updateStaticDOMText();
  document.documentElement.lang = lang;
  
  window.dispatchEvent(new CustomEvent("kr-lang-changed", { detail: { lang } }));
}

function getLanguage() {
  return currentLanguage;
}

// Interface labels in the regional languages (te mr kn ta bn gu or pa): machine translations generated by
// tools/translate_kb.py into i18n_regional.js. A label missing there is shown in English.
if (window.I18N_REGIONAL) {
  Object.keys(window.I18N_REGIONAL).forEach(lang => { if (!I18N[lang]) I18N[lang] = window.I18N_REGIONAL[lang]; });
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
    langToggleBtn.textContent = currentLanguage === "en" ? "\u0939\u093f\u0928\u094d\u0926\u0940" : "English";
    langToggleBtn.setAttribute("aria-label", currentLanguage === "en" ? "Switch to Hindi" : "Switch to English");
  }
}

window.I18N = I18N;
window.t = t;
window.setLanguage = setLanguage;
window.getLanguage = getLanguage;
window.updateStaticDOMText = updateStaticDOMText;
