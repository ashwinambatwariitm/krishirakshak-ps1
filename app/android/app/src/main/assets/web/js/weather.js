/**
 * KrishiRakshak Field Weather & Agricultural Spray Calculator
 * 
 * Evaluates field weather conditions to advise farmers whether it is safe
 * to spray pesticides/fungicides today (prevents spray drift and chemical wash-off).
 */

class FieldWeather {
  constructor() {
    this.currentData = {
      temp: 28,
      humidity: 65,
      windSpeed: 7, // km/h
      condition: "Clear",
      rainProb: 10
    };
  }

  /**
   * Determine spray suitability based on official agronomy guidelines:
   * - Wind speed: 3 to 12 km/h is safe. > 15 km/h causes dangerous spray drift.
   * - Temperature: < 32°C is safe. > 34°C causes rapid evaporation / leaf scorch.
   * - Rain: Rain probability > 40% will wash away chemicals.
   */
  evaluateSprayConditions(data = this.currentData) {
    const issues = [];
    let isFavorable = true;

    if (data.windSpeed > 15) {
      issues.push({
        type: "wind_high",
        en: `High wind (${data.windSpeed} km/h): Strong risk of chemical drift onto other crops or farmer. Avoid spraying now.`,
        hi: `तेज हवा (${data.windSpeed} किमी/घंटा): दवा उड़ने का खतरा है। अभी छिड़काव न करें।`
      });
      isFavorable = false;
    } else if (data.windSpeed < 3) {
      issues.push({
        type: "wind_calm",
        en: `Very calm air (${data.windSpeed} km/h): Risk of temperature inversion. Morning spray is preferred.`,
        hi: `हवा बहुत शांत है (${data.windSpeed} किमी/घंटा): सुबह के समय छिड़काव बेहतर रहेगा।`
      });
    }

    if (data.temp > 33) {
      issues.push({
        type: "temp_high",
        en: `High temperature (${data.temp}°C): Chemical may evaporate rapidly and cause leaf scorch. Spray in late afternoon (after 4 PM).`,
        hi: `अधिक तापमान (${data.temp}°C): दवा जल्दी वाष्पित हो सकती है। शाम 4 बजे के बाद छिड़काव करें।`
      });
      isFavorable = false;
    }

    if (data.rainProb > 40) {
      issues.push({
        type: "rain_risk",
        en: `Rain expected (${data.rainProb}%): Wash-off risk. Delay spraying until dry weather.`,
        hi: `बारिश की संभावना (${data.rainProb}%): दवा धुलने का खतरा। मौसम साफ होने तक रुकें।`
      });
      isFavorable = false;
    }

    return {
      isFavorable,
      rating: isFavorable ? "FAVORABLE" : "UNFAVORABLE",
      issues
    };
  }

  setManualWeather(temp, humidity, windSpeed, rainProb) {
    this.currentData.temp = Number(temp);
    this.currentData.humidity = Number(humidity);
    this.currentData.windSpeed = Number(windSpeed);
    this.currentData.rainProb = Number(rainProb);
    return this.evaluateSprayConditions();
  }
}

window.fieldWeather = new FieldWeather();
