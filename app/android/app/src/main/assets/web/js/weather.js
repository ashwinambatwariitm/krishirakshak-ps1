/**
 * KrishiRakshak Live Weather & Agricultural Spray Advisory
 * 
 * Powered by Open-Meteo API (100% Free, No API key required).
 * Fetches real live weather data via GPS or city presets and evaluates
 * whether field conditions are safe for spraying pesticides.
 */

class FieldWeather {
  constructor() {
    this.currentData = {
      temp: 29,
      humidity: 55,
      windSpeed: 8, // km/h
      rainProb: 10,
      weatherCode: 0,
      locationName: "Current Field"
    };

    // Major Indian Agricultural Hub presets (fallback if GPS is disabled or offline)
    this.cityPresets = {
      pune: { name: "Maharashtra (Pune / Nashik)", lat: 18.5204, lon: 73.8567 },
      karnal: { name: "Haryana (Karnal / Panipat)", lat: 29.6857, lon: 76.9905 },
      bengaluru: { name: "Karnataka (Kolar / Bengaluru)", lat: 12.9716, lon: 77.5946 },
      varanasi: { name: "Uttar Pradesh (Varanasi / Lucknow)", lat: 25.3176, lon: 82.9739 },
      hyderabad: { name: "Telangana / AP (Warangal / Hyd)", lat: 17.3850, lon: 78.4867 },
      patna: { name: "Bihar (Patna / Muzaffarpur)", lat: 25.5941, lon: 85.1376 },
      anand: { name: "Gujarat (Anand / Vadodara)", lat: 22.5645, lon: 72.9289 }
    };
  }

  /**
   * Fetch live weather from Open-Meteo API (Free, No Key Required)
   */
  async fetchLiveWeather(lat, lon, locationLabel = "Live Field") {
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code&hourly=precipitation_probability&timezone=auto`;
      
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Weather API HTTP ${res.status}`);
      
      const json = await res.json();
      const current = json.current;

      // Extract next 3 hours max rain probability
      let maxRainProb = 0;
      if (json.hourly && Array.isArray(json.hourly.precipitation_probability)) {
        const nextHours = json.hourly.precipitation_probability.slice(0, 6);
        maxRainProb = Math.max(...nextHours, 0);
      }

      this.currentData = {
        temp: Math.round(current.temperature_2m),
        humidity: Math.round(current.relative_humidity_2m),
        windSpeed: Math.round(current.wind_speed_10m),
        rainProb: maxRainProb,
        weatherCode: current.weather_code,
        locationName: locationLabel
      };

      return this.evaluateSprayConditions();
    } catch (err) {
      console.warn("Could not fetch live weather from Open-Meteo, using offline estimates:", err);
      return this.evaluateSprayConditions();
    }
  }

  /**
   * Auto-detect GPS location and fetch live weather
   */
  async fetchByGPS() {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve(this.fetchCityWeather("pune"));
        return;
      }

      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = pos.coords.latitude;
          const lon = pos.coords.longitude;
          const result = await this.fetchLiveWeather(lat, lon, "Your GPS Field");
          resolve(result);
        },
        async (err) => {
          console.warn("GPS location denied or unavailable:", err.message);
          // Fallback to default preset
          const result = await this.fetchCityWeather("pune");
          resolve(result);
        },
        { timeout: 8000 }
      );
    });
  }

  async fetchCityWeather(cityKey) {
    const preset = this.cityPresets[cityKey] || this.cityPresets.pune;
    return await this.fetchLiveWeather(preset.lat, preset.lon, preset.name);
  }

  /**
   * Determine spray suitability based on official agronomy guidelines
   */
  evaluateSprayConditions(data = this.currentData) {
    const issues = [];
    let isFavorable = true;

    // Wind speed: 3 to 12 km/h is safe
    if (data.windSpeed > 14) {
      issues.push({
        type: "wind_high",
        en: `High wind (${data.windSpeed} km/h): Strong risk of chemical drift onto other crops or farmer. Avoid spraying now.`,
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
        en: `Very calm air (${data.windSpeed} km/h): Risk of temperature inversion. Morning spray is preferred.`,
        hi: `हवा बहुत शांत है (${data.windSpeed} किमी/घंटा): सुबह के समय छिड़काव बेहतर रहेगा।`,
        mr: `शांत हवा (${data.windSpeed} किमी/तास): सकाळच्या वेळी फवारणी करणे योग्य राहील.`,
        te: `గాలి చాలా నెమ్మదిగా ఉంది (${data.windSpeed} కి.మీ/గం): ఉదయం పూట పిచికారీ చేయడం మంచిది.`,
        ta: `மிகக் குறைந்த காற்று (${data.windSpeed} கி.மீ/மணி): காலை நேரத்தில் தெளிப்பது நல்லது.`,
        kn: `ಗಾಳಿ ತೀರ ಶಾಂತವಾಗಿದೆ (${data.windSpeed} ಕಿ.ಮೀ/ಗಂ): ಬೆಳಗಿನ ಜಾವ ಸಿಂಪಡಿಸುವುದು ಉತ್ತಮ.`,
        bn: `বাতাস খুব শান্ত (${data.windSpeed} কিমি/ঘণ্টা): সকালে স্প্রে করা ভালো।`,
        gu: `પવન બિલકુલ શાંત છે (${data.windSpeed} કિમી/કલાક): સવારના સમયે છંટકાવ કરવો યોગ્ય રહેશે.`,
        pa: `ਹਵਾ ਬਹੁਤ ਸ਼ਾਂਤ ਹੈ (${data.windSpeed} ਕਿਮੀ/ਘੰਟਾ): ਸਵੇਰ ਵੇਲੇ ਛਿੜਕਾਅ ਕਰਨਾ ਵਧੀਆ ਰਹੇਗਾ।`,
        or: `ପବନ ଖୁବ ଶାନ୍ତ (${data.windSpeed} କିମି/ଘଣ୍ଟା): ସକାଳେ ସ୍ପ୍ରେ କରିବା ଉଚିତ।`
      });
    }

    // Temperature: < 32°C is safe
    if (data.temp > 33) {
      issues.push({
        type: "temp_high",
        en: `High temperature (${data.temp}°C): Chemical may evaporate rapidly and cause leaf scorch. Spray in late afternoon (after 4 PM).`,
        hi: `अधिक तापमान (${data.temp}°C): दवा जल्दी वाष्पित होकर पत्तों को नुकसान पहुंचा सकती है। शाम 4 बजे के बाद छिड़काव करें।`,
        mr: `जास्त तापमान (${data.temp}°C): औषध लवकर बाष्पीभवन होऊन पाने करपू शकतात. दुपारी ४ नंतर फवारणी करा.`,
        te: `అధిక ఉష్ణోగ్రత (${data.temp}°C): మందు త్వరగా ఆవిరై ఆకులు మాడిపోయే ప్రమాదం. సాయంత్రం 4 గంటల తర్వాత పిచికారీ చేయండి.`,
        ta: `அதிக வெப்பநிலை (${data.temp}°C): மருந்து விரைவாக ஆவியாகி இலைகளைக் கருகச் செய்யலாம். மாலை 4 மணிக்கு மேல் தெளிக்கவும்.`,
        kn: `ಹೆಚ್ಚಿನ ತಾಪಮಾನ (${data.temp}°C): ರಾಸಾಯನಿಕ ಆವಿಯಾಗಿ ಎಲೆಗಳು ಸುಡುವ ಅಪಾಯ. ಸಂಜೆ 4 ರ ನಂತರ ಸಿಂಪಡಿಸಿ.`,
        bn: `অতিরিক্ত তাপমাত্রা (${data.temp}°C): ওষুধ দ্রুত বাষ্পীভূত হয়ে পাতা পুড়ে যেতে পারে। বিকেল ৪টার পর স্প্রে করুন।`,
        gu: `વધુ તાપમાન (${data.temp}°C): દવા ઝડપથી બાષ્પીભવન થઈને પાંદડા બાળી શકે છે. સાંજે ૪ વાગ્યા પછી છંટકાવ કરવો.`,
        pa: `ਵੱਧ ਤਾਪਮਾਨ (${data.temp}°C): ਦਵਾਈ ਛੇਤੀ ਭਾਫ਼ ਬਣ ਕੇ ਪੱਤਿਆਂ ਨੂੰ ਨੁਕਸਾਨ ਪਹੁੰਚਾ ਸਕਦੀ ਹੈ। ਸ਼ਾਮ ੪ ਵਜੇ ਤੋਂ ਬਾਅਦ ਛਿੜਕਾਅ ਕਰੋ।`,
        or: `ଅତ୍ୟଧିକ ତାପମାତ୍ରା (${data.temp}°C): ଔଷଧ ବାଷ୍ପୀଭୂତ ହୋଇ ପତ୍ର ପୋଡ଼ିପାରେ। ଅପରାହ୍ନ ୪ଟା ପରେ ସ୍ପ୍ରେ କରନ୍ତୁ।`
      });
      isFavorable = false;
    }

    // Rain: Rain probability > 35%
    if (data.rainProb > 35) {
      issues.push({
        type: "rain_risk",
        en: `Rain expected within hours (${data.rainProb}%): Wash-off risk. Delay spraying until dry weather.`,
        hi: `बारिश की संभावना (${data.rainProb}%): दवा धुलने का खतरा। मौसम साफ होने तक प्रतीक्षा करें।`,
        mr: `पावसाची शक्यता (${data.rainProb}%): औषध धुतले जाण्याचा धोका. पाऊस थांबेपर्यंत फवारणी पुढे ढकला.`,
        te: `వర్షం పడే అవకాశం ఉంది (${data.rainProb}%): మందు కొట్టుకుపోయే ప్రమాదం. పొడి వాతావరణం వచ్చేవరకు ఆగండి.`,
        ta: `மழை பெய்ய வாய்ப்பு உள்ளது (${data.rainProb}%): மருந்து நீரில் அடித்துச் செல்லப்படும். மழை நிற்கும் வரை ஒத்திவைக்கவும்.`,
        kn: `ಮಳೆಯ ಸಂಭವನೀಯತೆ (${data.rainProb}%): ಔಷಧ ತೊಳೆದುಹೋಗುವ ಅಪಾಯ. ಒಣ ಹವೆ ಬರುವವರೆಗೆ ಮುಂದೂಡಿ.`,
        bn: `বৃষ্টির সম্ভাবনা (${data.rainProb}%): ওষুধ ধুয়ে যাওয়ার ঝুঁকি। আবহাওয়া পরিষ্কার না হওয়া পর্যন্ত অপেক্ষা করুন।`,
        gu: `વરસાદની સંભાવના (${data.rainProb}%): દવા ધોવાઈ જવાનું જોખમ. હવામાન સાફ થાય ત્યાં સુધી રાહ જુઓ.`,
        pa: `ਮੀਂਹ ਪੈਣ ਦੀ ਸੰਭਾਵਨਾ (${data.rainProb}%): ਦਵਾਈ ਧੁਲ ਜਾਣ ਦਾ ਖ਼ਤਰਾ। ਮੌਸਮ ਸਾਫ਼ ਹੋਣ ਤੱਕ ਉਡੀਕ ਕਰੋ।`,
        or: `ବର୍ଷା ସମ୍ଭାବନା (${data.rainProb}%): ଔଷଧ ଧୋଇଯିବାର ବିପଦ। ପାଗ ଶୁଖିଲା ହେବା ପର୍ଯ୍ୟନ୍ତ ସ୍ପ୍ରେ ସ୍ଥଗିତ ରଖନ୍ତୁ।`
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
