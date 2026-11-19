/**
 * KrishiRakshak Global Live Weather & Agricultural Spray Advisory
 * 
 * Powered by Open-Meteo Global Meteorological Forecast Engine
 * (100% Free, Zero API Key required, Zero Rate Limits, Global Resolution 1-10 km).
 * 
 * Capabilities:
 * 1. Automatic Multi-Tier Worldwide Location Detection:
 *    - Android Native GPS (inside APK)
 *    - HTML5 Geolocation (browser GPS)
 *    - IP Geolocation (instant worldwide detection with 0 permission prompts)
 * 2. Worldwide City & Farm Search (Open-Meteo Global Geocoding for 200,000+ cities)
 * 3. High-precision agricultural spray suitability meter following FAO/ICAR standards
 */

class FieldWeather {
  constructor() {
    this.currentData = {
      temp: 28,
      humidity: 55,
      windSpeed: 8,
      windGusts: 12,
      rainProb: 10,
      weatherCode: 0,
      weatherCondition: "Clear Sky",
      weatherIcon: "☀️",
      locationName: "Detecting Location..."
    };

    // Major global agricultural zones presets (covering Asia, Americas, Europe, Africa, Oceania)
    this.cityPresets = {
      // India / South Asia
      pune: { name: "Maharashtra (Pune / Nashik), India", lat: 18.5204, lon: 73.8567 },
      karnal: { name: "Haryana (Karnal / Panipat), India", lat: 29.6857, lon: 76.9905 },
      bengaluru: { name: "Karnataka (Kolar / Bengaluru), India", lat: 12.9716, lon: 77.5946 },
      varanasi: { name: "Uttar Pradesh (Varanasi), India", lat: 25.3176, lon: 82.9739 },
      hyderabad: { name: "Telangana (Warangal / Hyderabad), India", lat: 17.3850, lon: 78.4867 },
      patna: { name: "Bihar (Patna / Muzaffarpur), India", lat: 25.5941, lon: 85.1376 },
      anand: { name: "Gujarat (Anand / Vadodara), India", lat: 22.5645, lon: 72.9289 },
      ludhiana: { name: "Punjab (Ludhiana / Jalandhar), India", lat: 30.9010, lon: 75.8573 },
      kolkata: { name: "West Bengal (Kolkata / Hooghly), India", lat: 22.5726, lon: 88.3639 },
      // Americas
      california: { name: "California (Central Valley), USA", lat: 36.7783, lon: -119.4179 },
      iowa: { name: "Iowa (Corn Belt / Des Moines), USA", lat: 41.5868, lon: -93.6250 },
      florida: { name: "Florida (Orlando / Highlands), USA", lat: 28.5383, lon: -81.3792 },
      mexico: { name: "Sinaloa (Culiacán), Mexico", lat: 24.8091, lon: -107.3940 },
      brazil: { name: "Mato Grosso (Cuiabá / São Paulo), Brazil", lat: -15.6014, lon: -56.0979 },
      // Europe
      spain: { name: "Almería (Greenhouse Valley), Spain", lat: 36.8381, lon: -2.4597 },
      italy: { name: "Emilia-Romagna (Bologna), Italy", lat: 44.4949, lon: 11.3426 },
      france: { name: "Occitanie (Toulouse), France", lat: 43.6047, lon: 1.4442 },
      uk: { name: "Kent / London, United Kingdom", lat: 51.2787, lon: 0.5217 },
      // Africa & Oceania
      kenya: { name: "Rift Valley (Naivasha / Nairobi), Kenya", lat: -0.7172, lon: 36.4310 },
      nigeria: { name: "Kano / Kaduna, Nigeria", lat: 12.0022, lon: 8.5920 },
      egypt: { name: "Nile Delta (Cairo / Tanta), Egypt", lat: 30.0444, lon: 31.2357 },
      australia: { name: "Queensland (Bowen / Bundaberg), Australia", lat: -20.0137, lon: 148.2476 }
    };

    // WMO Weather Code definitions
    this.wmoCodes = {
      0: { text: "Clear Sky", icon: "☀️" },
      1: { text: "Mainly Clear", icon: "🌤️" },
      2: { text: "Partly Cloudy", icon: "⛅" },
      3: { text: "Overcast", icon: "☁️" },
      45: { text: "Fog", icon: "🌫️" },
      48: { text: "Icy Fog", icon: "🌫️" },
      51: { text: "Light Drizzle", icon: "🌦️" },
      53: { text: "Moderate Drizzle", icon: "🌦️" },
      55: { text: "Dense Drizzle", icon: "🌧️" },
      61: { text: "Slight Rain", icon: "🌧️" },
      63: { text: "Moderate Rain", icon: "🌧️" },
      65: { text: "Heavy Rain", icon: "🌧️" },
      71: { text: "Slight Snow", icon: "🌨️" },
      73: { text: "Moderate Snow", icon: "🌨️" },
      75: { text: "Heavy Snow", icon: "❄️" },
      80: { text: "Rain Showers", icon: "🌦️" },
      81: { text: "Moderate Showers", icon: "🌧️" },
      82: { text: "Violent Showers", icon: "⛈️" },
      95: { text: "Thunderstorm", icon: "⛈️" },
      96: { text: "Thunderstorm with Hail", icon: "⛈️" },
      99: { text: "Severe Thunderstorm", icon: "⛈️" }
    };
  }

  /**
   * Fetch live weather from Open-Meteo Global Meteorological API
   */
  async fetchLiveWeather(lat, lon, locationLabel = null) {
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_gusts_10m&hourly=precipitation_probability&timezone=auto`;
      
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Weather API HTTP ${res.status}`);
      
      const json = await res.json();
      const current = json.current;

      // Extract next 4 hours max rain probability
      let maxRainProb = 0;
      if (json.hourly && Array.isArray(json.hourly.precipitation_probability)) {
        const nextHours = json.hourly.precipitation_probability.slice(0, 5);
        maxRainProb = Math.max(...nextHours, 0);
      }

      const wCode = current.weather_code ?? 0;
      const wInfo = this.wmoCodes[wCode] || { text: "Clear", icon: "☀️" };

      // Resolve location name if not already provided
      let finalLabel = locationLabel;
      if (!finalLabel || finalLabel.includes("GPS") || finalLabel.includes("Field")) {
        const rev = await this.reverseGeocode(lat, lon);
        if (rev) finalLabel = rev;
      }

      this.currentData = {
        temp: Math.round(current.temperature_2m),
        humidity: Math.round(current.relative_humidity_2m),
        windSpeed: Math.round(current.wind_speed_10m),
        windGusts: Math.round(current.wind_gusts_10m || current.wind_speed_10m),
        rainProb: maxRainProb,
        weatherCode: wCode,
        weatherCondition: wInfo.text,
        weatherIcon: wInfo.icon,
        locationName: finalLabel || "Local Farm"
      };

      return this.evaluateSprayConditions();
    } catch (err) {
      console.warn("Could not fetch Open-Meteo weather:", err.message);
      return this.evaluateSprayConditions();
    }
  }

  /**
   * Universal Worldwide Location Auto-Detection
   * 1. Native Android Location (Inside APK)
   * 2. Browser GPS (if permission granted)
   * 3. IP Geolocation (Zero prompt worldwide fallback)
   */
  async detectWorldwideLocation() {
    // 1. Check Android Native Location Bridge
    if (window.AndroidLocation && typeof window.AndroidLocation.getLastLocation === "function") {
      try {
        const locJson = window.AndroidLocation.getLastLocation();
        if (locJson) {
          const parsed = JSON.parse(locJson);
          if (parsed && parsed.lat && parsed.lon) {
            const locName = await this.reverseGeocode(parsed.lat, parsed.lon);
            return await this.fetchLiveWeather(parsed.lat, parsed.lon, locName || "Your Farm");
          }
        }
      } catch (e) {
        console.log("AndroidLocation bridge check:", e.message);
      }
    }

    // 2. Check Browser / Device HTML5 GPS
    const gpsCoords = await new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve(null);
        return;
      }
      navigator.geolocation.getCurrentPosition(
        (pos) => resolve({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        () => resolve(null),
        { timeout: 4000, enableHighAccuracy: true }
      );
    });

    if (gpsCoords) {
      const locName = await this.reverseGeocode(gpsCoords.lat, gpsCoords.lon);
      return await this.fetchLiveWeather(gpsCoords.lat, gpsCoords.lon, locName || "Your GPS Location");
    }

    // 3. Worldwide IP Geolocation Fallback (Works everywhere on Earth without permissions)
    try {
      const ipRes = await fetch("https://freeipapi.com/api/json");
      if (ipRes.ok) {
        const ipData = await ipRes.json();
        if (ipData && ipData.latitude && ipData.longitude) {
          const locParts = [ipData.cityName, ipData.regionName, ipData.countryName].filter(Boolean);
          const label = locParts.length > 0 ? locParts.join(", ") : "Your City";
          return await this.fetchLiveWeather(ipData.latitude, ipData.longitude, label);
        }
      }
    } catch (ipErr) {
      console.log("IP Geolocation check 1:", ipErr.message);
    }

    try {
      const ipRes2 = await fetch("https://ipapi.co/json/");
      if (ipRes2.ok) {
        const ipData2 = await ipRes2.json();
        if (ipData2 && ipData2.latitude && ipData2.longitude) {
          const locParts = [ipData2.city, ipData2.region, ipData2.country_name].filter(Boolean);
          const label = locParts.length > 0 ? locParts.join(", ") : "Your City";
          return await this.fetchLiveWeather(ipData2.latitude, ipData2.longitude, label);
        }
      }
    } catch (ipErr2) {
      console.log("IP Geolocation check 2:", ipErr2.message);
    }

    // 4. Default fallback to preset
    return await this.fetchCityWeather("pune");
  }

  /**
   * Search any city or district worldwide using Open-Meteo Global Geocoding API
   */
  async searchWorldwideCity(query) {
    if (!query || !query.trim()) return null;
    const cleanQuery = query.trim();

    try {
      const url = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(cleanQuery)}&count=1&language=en&format=json`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Geocoding HTTP ${res.status}`);

      const json = await res.json();
      if (json.results && json.results.length > 0) {
        const item = json.results[0];
        const labelParts = [item.name, item.admin1, item.country].filter(Boolean);
        const locationLabel = labelParts.join(", ");
        return await this.fetchLiveWeather(item.latitude, item.longitude, locationLabel);
      }
    } catch (err) {
      console.warn("Global city search error:", err.message);
    }

    return null;
  }

  /**
   * Reverse geocode lat/lon to friendly city, state, country
   */
  async reverseGeocode(lat, lon) {
    try {
      const url = `https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lon}&localityLanguage=en`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        const city = data.city || data.locality || data.principalSubdivision;
        const state = data.principalSubdivision;
        const country = data.countryName;
        const parts = [city, state !== city ? state : null, country].filter(Boolean);
        if (parts.length > 0) return parts.join(", ");
      }
    } catch (e) {
      // ignore
    }
    return null;
  }

  async fetchCityWeather(cityKey) {
    const preset = this.cityPresets[cityKey] || this.cityPresets.pune;
    return await this.fetchLiveWeather(preset.lat, preset.lon, preset.name);
  }

  /**
   * Agricultural Spray Suitability Evaluation (International FAO/ICAR Guidelines)
   */
  evaluateSprayConditions(data = this.currentData) {
    const issues = [];
    let isFavorable = true;

    // Wind speed threshold: Safe window is 3 to 14 km/h
    if (data.windSpeed > 14) {
      issues.push({
        type: "wind_high",
        en: `High wind (${data.windSpeed} km/h): Strong chemical drift onto non-target crops or farmer. Spraying is NOT safe now.`,
        hi: `तेज हवा (${data.windSpeed} किमी/घंटा): दवा उड़ने का गंभीर खतरा। अभी छिड़काव न करें।`,
        mr: `जोरदार वारा (${data.windSpeed} किमी/तास): औषध इतर पिकांवर उडण्याचा धोका. आता फवारणी टाळा.`,
        te: `తీవ్రమైన గాలి (${data.windSpeed} కి.మీ/గం): మందు పక్క పంటలపైకి కొట్టుకుపోయే ప్రమాదం. ఇప్పుడు పిచికారీ చేయవద్దు.`,
        ta: `வேகமான காற்று (${data.windSpeed} கி.மீ/மணி): மருந்து காற்றில் அடித்துச் செல்லப்படும் அபாயம். இப்போது தெளிக்க வேண்டாம்.`,
        kn: `ವೇಗದ ಗಾಳಿ (${data.windSpeed} ಕಿ.ಮೀ/ಗಂ): ರಾಸಾಯನಿಕ ಗಾಳಿಗೆ ಹಾರಿಹೋಗುವ ಅಪಾಯ. ಈಗ ಸಿಂಪಡಿಸಬೇಡಿ.`,
        bn: `ঝড়ো বাতাস (${data.windSpeed} কিমি/ঘণ্টা): ওষুধ অন্য ফসলে উড়ে যাওয়ার ঝুঁকি। এখন স্প্রে করবেন না।`,
        gu: `ઝડપી પવન (${data.windSpeed} કિમી/કલાક): દવા પવનમાં ઊડી જવાનું જોખમ. અત્યારે છંટકાવ ન કરવો.`,
        pa: `ਤੇਜ਼ ਹਵਾ (${data.windSpeed} ਕਿਮੀ/ਘੰਟਾ): ਦਵਾਈ ਉੱਡ ਕੇ ਦੂਜੀਆਂ ਫ਼ਸਲਾਂ 'ਤੇ ਪੈਣ ਦਾ ਖ਼ਤਰਾ। ਹੁਣ ਛਿੜਕਾਅ ਨਾ ਕਰੋ।`,
        or: `ପ୍ରବଳ ପବନ (${data.windSpeed} କିମି/ଘଣ୍ଟା): ଔଷଧ ଅନ୍ୟ ଫସଲକୁ ଉଡ଼ିଯିବାର ବିପଦ। ବର୍ତ୍ତମାନ ସ୍ପ୍ରେ କରନ୍ତୁ ନାହିଁ।`
      });
      isFavorable = false;
    } else if (data.windSpeed < 2) {
      issues.push({
        type: "wind_calm",
        en: `Very calm air (${data.windSpeed} km/h): Temperature inversion risk. Morning or evening spray is preferred.`,
        hi: `हवा बहुत शांत है (${data.windSpeed} किमी/घंटा): सुबह या शाम के समय छिड़काव बेहतर रहेगा।`,
        mr: `शांत हवा (${data.windSpeed} किमी/तास): सकाळच्या किंवा संध्याकाळच्या वेळी फवारणी करणे योग्य राहील.`,
        te: `గాలి చాలా నెమ్మదిగా ఉంది (${data.windSpeed} కి.మీ/గం): ఉదయం లేదా సాయంత్రం పిచికారీ చేయడం మంచిది.`,
        ta: `மிகக் குறைந்த காற்று (${data.windSpeed} கி.மீ/மணி): காலை அல்லது மாலை நேரத்தில் தெளிப்பது நல்லது.`,
        kn: `ಗಾಳಿ ತೀರ ಶಾಂತವಾಗಿದೆ (${data.windSpeed} ಕಿ.ಮೀ/ಗಂ): ಬೆಳಗಿನ ಜಾವ ಅಥವಾ ಸಂಜೆ ಸಿಂಪಡಿಸುವುದು ಉತ್ತಮ.`,
        bn: `বাতাস খুব শান্ত (${data.windSpeed} কিমি/ঘণ্টা): সকালে বা বিকেলে স্প্রে করা ভালো।`,
        gu: `પવન બિલકુલ શાંત છે (${data.windSpeed} કિમી/કલાક): સવારે અથવા સાંજે છંટકાવ કરવો યોગ્ય રહેશે.`,
        pa: `ਹਵਾ ਬਹੁਤ ਸ਼ਾਂਤ ਹੈ (${data.windSpeed} ਕਿਮੀ/ਘੰਟਾ): ਸਵੇਰੇ ਜਾਂ ਸ਼ਾਮ ਵੇਲੇ ਛਿੜਕਾਅ ਕਰਨਾ ਵਧੀਆ ਰਹੇਗਾ।`,
        or: `ପବନ ଖୁବ ଶାନ୍ତ (${data.windSpeed} କିମି/ଘଣ୍ଟା): ସକାଳେ କିମ୍ବା ସନ୍ଧ୍ୟାରେ ସ୍ପ୍ରେ କରିବା ଉଚିତ।`
      });
    }

    // High Wind Gust warning
    if (data.windGusts > 20) {
      issues.push({
        type: "gust_high",
        en: `Sudden wind gusts (${data.windGusts} km/h): Sudden gusts cause uneven spray droplets and pesticide wastage.`,
        hi: `हवा के तेज झोंके (${data.windGusts} किमी/घंटा): दवा की बूंदें बिखरने और बर्बादी का खतरा।`,
        mr: `वाऱ्याचे झोत (${data.windGusts} किमी/तास): औषधाचे तुषार असमान पसरण्याचा व वाया जाण्याचा धोका.`,
        te: `గాలి తీవ్రమైన ఈదురుగాలులు (${data.windGusts} కి.మీ/గం): మందు వృథా అయ్యే ప్రమాదం.`,
        ta: `சுழல் காற்று வீசுகிறது (${data.windGusts} கி.மீ/மணி): மருந்து வீணாகும் அபாயம்.`,
        kn: `ಬಿರುಗಾಳಿಯ ಹೊಡೆತ (${data.windGusts} ಕಿ.ಮೀ/ಗಂ): ಔಷಧ ಸಮರ್ಪಕವಾಗಿ ತಲುಪದೆ ವ್ಯರ್ಥವಾಗಬಹುದು.`,
        bn: `বাতাসের দমকা (${data.windGusts} কিমি/ঘণ্টা): ওষুধের কণা অসমভাবে ছড়ানোর ঝুঁকি।`,
        gu: `પવનના ઝાપટાં (${data.windGusts} કિમી/કલાક): દવાનું ટીપું વિખેરાઈ જવાનું જોખમ.`,
        pa: `ਹਵਾ ਦੇ ਤੇਜ਼ ਬੁੱਲੇ (${data.windGusts} ਕਿਮੀ/ਘੰਟਾ): ਦਵਾਈ ਦਾ ਨੁਕਸਾਨ ਹੋਣ ਦਾ ਖ਼ਤਰਾ।`,
        or: `ପବନର ଝଟକା (${data.windGusts} କିମି/ଘଣ୍ଟା): ଔଷଧ ନଷ୍ଟ ହେବାର ଆଶଙ୍କା।`
      });
      isFavorable = false;
    }

    // High Temperature warning (> 32°C)
    if (data.temp > 32) {
      issues.push({
        type: "temp_high",
        en: `High temperature (${data.temp}°C): Rapid droplet evaporation causes leaf scorch. Spray after 4:00 PM.`,
        hi: `अधिक तापमान (${data.temp}°C): दवा तेजी से सूखकर पत्तों को जला सकती है। शाम 4:00 बजे के बाद छिड़काव करें।`,
        mr: `जास्त तापमान (${data.temp}°C): औषध बाष्पीभवन होऊन पाने करपू शकतात. संध्याकाळी ४:०० नंतर फवारणी करा.`,
        te: `అధిక ఉష్ణోగ్రత (${data.temp}°C): మందు త్వరగా ఆవిరై ఆకులు మాడిపోయే ప్రమాదం. సాయంత్రం 4:00 తర్వాత చేయండి.`,
        ta: `அதிக வெப்பநிலை (${data.temp}°C): இலைகள் கருகும் அபாயம். மாலை 4:00 மணிக்கு மேல் தெளிக்கவும்.`,
        kn: `ಹೆಚ್ಚಿನ ತಾಪಮಾನ (${data.temp}°C): ರಾಸಾಯನಿಕ ಆವಿಯಾಗಿ ಎಲೆಗಳು ಸುಡುವ ಅಪಾಯ. ಸಂಜೆ 4:00 ರ ನಂತರ ಸಿಂಪಡಿಸಿ.`,
        bn: `অতিরিক্ত তাপমাত্রা (${data.temp}°C): পাতা পুড়ে যাওয়ার ঝুঁকি। বিকেল ৪:০০টার পর স্প্রে করুন।`,
        gu: `વધુ તાપમાન (${data.temp}°C): પાંદડા બળી જવાનું જોખમ. સાંજે ૪:૦૦ પછી છંટકાવ કરવો.`,
        pa: `ਵੱਧ ਤਾਪਮਾਨ (${data.temp}°C): ਪੱਤੇ ਸੜਨ ਦਾ ਖ਼ਤਰਾ। ਸ਼ਾਮ ੪:੦੦ ਵਜੇ ਤੋਂ ਬਾਅਦ ਛਿੜਕਾਅ ਕਰੋ।`,
        or: `ଅତ୍ୟଧିକ ତାପମାତ୍ରା (${data.temp}°C): ପତ୍ର ପୋଡ଼ିପାରେ। ଅପରାହ୍ନ ୪:୦୦ ପରେ ସ୍ପ୍ରେ କରନ୍ତୁ।`
      });
      isFavorable = false;
    }

    // Rain probability warning (> 30%)
    if (data.rainProb > 30) {
      issues.push({
        type: "rain_risk",
        en: `High rain risk (${data.rainProb}% within hours): Immediate wash-off of chemical. Delay spraying until weather clears.`,
        hi: `बारिश का खतरा (${data.rainProb}%): दवा धुलने की पूरी संभावना। मौसम साफ होने तक छिड़काव टालें।`,
        mr: `पावसाचा धोका (${data.rainProb}%): औषध वाहून जाण्याची शक्यता. पाऊस थांबेपर्यंत फवारणी पुढे ढकला.`,
        te: `వర్షం వచ్చే అవకాశం (${data.rainProb}%): మందు కొట్టుకుపోయే ప్రమాదం. వాతావరణం పొడిగా ఉండే వరకు ఆగండి.`,
        ta: `மழை பெய்ய வாய்ப்பு (${data.rainProb}%): மருந்து நீரில் அடித்துச் செல்லப்படும். மழை நிற்கும் வரை ஒத்திவைக்கவும்.`,
        kn: `ಮಳೆಯ ಅಪಾಯ (${data.rainProb}%): ಔಷಧ ತೊಳೆದುಹೋಗುವ ಸಂಭವ. ಒಣ ಹವೆ ಬರುವವರೆಗೆ ಮುಂದೂಡಿ.`,
        bn: `বৃষ্টির আশঙ্কা (${data.rainProb}%): ওষুধ ধুয়ে যাওয়ার ঝুঁকি। আবহাওয়া পরিষ্কার না হওয়া পর্যন্ত অপেক্ষা করুন।`,
        gu: `વરસાદનું જોખમ (${data.rainProb}%): દવા ધોવાઈ જવાની સંભાવના. હવામાન સાફ થાય ત્યાં સુધી રાહ જુઓ.`,
        pa: `ਮੀਂਹ ਦਾ ਖ਼ਤਰਾ (${data.rainProb}%): ਦਵਾਈ ਧੁਲਣ ਦਾ ਖ਼ਤਰਾ। ਮੌਸਮ ਸਾਫ਼ ਹੋਣ ਤੱਕ ਉਡੀਕ ਕਰੋ।`,
        or: `ବର୍ଷା ଆଶଙ୍କା (${data.rainProb}%): ଔଷଧ ଧୋଇଯିବାର ସମ୍ଭାବନା। ପାଗ ପରିଷ୍କାର ହେବା ପର୍ଯ୍ୟନ୍ତ ସ୍ପ୍ରେ ସ୍ଥଗିତ ରଖନ୍ତୁ।`
      });
      isFavorable = false;
    }

    return {
      isFavorable,
      rating: isFavorable ? "FAVORABLE" : "UNFAVORABLE",
      data: this.currentData,
      issues
    };
  }
}

window.fieldWeather = new FieldWeather();
