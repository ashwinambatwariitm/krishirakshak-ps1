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
   * - Temperature: < 32\u00b0C is safe. > 34\u00b0C causes rapid evaporation / leaf scorch.
   * - Rain: Rain probability > 40% will wash away chemicals.
   */
  evaluateSprayConditions(data = this.currentData) {
    const issues = [];
    let isFavorable = true;

    if (data.windSpeed > 15) {
      issues.push({
        type: "wind_high",
        en: `High wind (${data.windSpeed} km/h): Strong risk of chemical drift onto other crops or farmer. Avoid spraying now.`,
        hi: `\u0924\u0947\u091c \u0939\u0935\u093e (${data.windSpeed} \u0915\u093f\u092e\u0940/\u0918\u0902\u091f\u093e): \u0926\u0935\u093e \u0909\u0921\u093c\u0928\u0947 \u0915\u093e \u0916\u0924\u0930\u093e \u0939\u0948\u0964 \u0905\u092d\u0940 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0928 \u0915\u0930\u0947\u0902\u0964`
      });
      isFavorable = false;
    } else if (data.windSpeed < 3) {
      issues.push({
        type: "wind_calm",
        en: `Very calm air (${data.windSpeed} km/h): Risk of temperature inversion. Morning spray is preferred.`,
        hi: `\u0939\u0935\u093e \u092c\u0939\u0941\u0924 \u0936\u093e\u0902\u0924 \u0939\u0948 (${data.windSpeed} \u0915\u093f\u092e\u0940/\u0918\u0902\u091f\u093e): \u0938\u0941\u092c\u0939 \u0915\u0947 \u0938\u092e\u092f \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u092c\u0947\u0939\u0924\u0930 \u0930\u0939\u0947\u0917\u093e\u0964`
      });
    }

    if (data.temp > 33) {
      issues.push({
        type: "temp_high",
        en: `High temperature (${data.temp}\u00b0C): Chemical may evaporate rapidly and cause leaf scorch. Spray in late afternoon (after 4 PM).`,
        hi: `\u0905\u0927\u093f\u0915 \u0924\u093e\u092a\u092e\u093e\u0928 (${data.temp}\u00b0C): \u0926\u0935\u093e \u091c\u0932\u094d\u0926\u0940 \u0935\u093e\u0937\u094d\u092a\u093f\u0924 \u0939\u094b \u0938\u0915\u0924\u0940 \u0939\u0948\u0964 \u0936\u093e\u092e 4 \u092c\u091c\u0947 \u0915\u0947 \u092c\u093e\u0926 \u091b\u093f\u0921\u093c\u0915\u093e\u0935 \u0915\u0930\u0947\u0902\u0964`
      });
      isFavorable = false;
    }

    if (data.rainProb > 40) {
      issues.push({
        type: "rain_risk",
        en: `Rain expected (${data.rainProb}%): Wash-off risk. Delay spraying until dry weather.`,
        hi: `\u092c\u093e\u0930\u093f\u0936 \u0915\u0940 \u0938\u0902\u092d\u093e\u0935\u0928\u093e (${data.rainProb}%): \u0926\u0935\u093e \u0927\u0941\u0932\u0928\u0947 \u0915\u093e \u0916\u0924\u0930\u093e\u0964 \u092e\u094c\u0938\u092e \u0938\u093e\u092b \u0939\u094b\u0928\u0947 \u0924\u0915 \u0930\u0941\u0915\u0947\u0902\u0964`
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
