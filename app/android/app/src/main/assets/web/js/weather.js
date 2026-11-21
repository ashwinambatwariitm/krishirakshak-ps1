/**
 * KrishiRakshak spray check (works offline, no weather data or sensor needed)
 *
 * A farmer cannot measure wind speed or rain probability in the field, so the check asks four questions that can be
 * answered by looking. They follow the NIPHM rule for applying pesticides (AESA based IPM package for Tomato, 2014,
 * p. 89-90; also in the knowledge base, topic pesticide_safety): "Do not apply on hot sunny day or strong windy
 * condition. Do not apply just before the rains and after the rains. Do not apply against the windy direction."
 * No numeric limits are used: the source gives none.
 */

// The answer that makes spraying unsafe, per question
const SPRAY_UNSAFE_ANSWER = { sun: "yes", wind: "yes", rain: "yes", direction: "no" };

class SprayCheck {
  constructor() {
    this.answers = {};
  }

  setAnswer(question, answer) {
    if (question in SPRAY_UNSAFE_ANSWER) this.answers[question] = answer;
    return this.evaluate();
  }

  /**
   * complete: all four questions answered; ok: no unsafe answer; reasons: i18n keys of the rule parts not met
   * (spray_why_sun, spray_why_wind, spray_why_rain, spray_why_direction)
   */
  evaluate() {
    const questions = Object.keys(SPRAY_UNSAFE_ANSWER);
    const reasons = questions.filter(q => this.answers[q] === SPRAY_UNSAFE_ANSWER[q]).map(q => `spray_why_${q}`);
    const complete = questions.every(q => this.answers[q]);
    // One unsafe answer is enough to say "do not spray now", even before the other questions are answered
    return { complete, ok: complete && reasons.length === 0, reasons, answered: Object.keys(this.answers).length };
  }
}

window.sprayCheck = new SprayCheck();
