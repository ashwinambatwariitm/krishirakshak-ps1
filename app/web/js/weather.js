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
        hi: `तेज हवा (${data.windSpeed} किमी/घंटा): दवा उड़ने का गंभीर खतरा। अभी छिड़काव न करें।`
      });
      isFavorable = false;
    } else if (data.windSpeed < 2) {
      issues.push({
        type: "wind_calm",
        en: `Very calm air (${data.windSpeed} km/h): Risk of temperature inversion. Morning spray is preferred.`,
        hi: `हवा बहुत शांत है (${data.windSpeed} किमी/घंटा): सुबह के समय छिड़काव बेहतर रहेगा।`
      });
    }

    // Temperature: < 32°C is safe
    if (data.temp > 33) {
      issues.push({
        type: "temp_high",
        en: `High temperature (${data.temp}°C): Chemical may evaporate rapidly and cause leaf scorch. Spray in late afternoon (after 4 PM).`,
        hi: `अधिक तापमान (${data.temp}°C): दवा जल्दी वाष्पित होकर पत्तों को नुकसान पहुंचा सकती है। शाम 4 बजे के बाद छिड़काव करें।`
      });
      isFavorable = false;
    }

    // Rain: Rain probability > 35%
    if (data.rainProb > 35) {
      issues.push({
        type: "rain_risk",
        en: `Rain expected within hours (${data.rainProb}%): Wash-off risk. Delay spraying until dry weather.`,
        hi: `बारिश की संभावना (${data.rainProb}%): दवा धुलने का खतरा। मौसम साफ होने तक प्रतीक्षा करें।`
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
