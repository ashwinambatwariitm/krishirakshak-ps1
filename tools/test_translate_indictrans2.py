"""Offline safety regressions; no models or optional dependencies required."""
import unittest
from translate_indictrans2 import Grounding, LANGUAGES, number_check, protect, repeated_output, translate_answers


class TranslationTests(unittest.TestCase):
    def test_number_identity(self):
        for source, target, passed in [("10 days", "100", False), ("1.0", "10", False),
                                        ("5 and 5", "5", False), ("5", "5 6", False),
                                        ("15-18", "15 - 18", True), ("1,000", "1000", False),
                                        ("-5", "5", False), ("15-18", "18-15", False)]:
            self.assertEqual(number_check(source, target, "hi")["passed"], passed)

    def test_target_digits(self):
        self.assertTrue(number_check("15.5", "\u0967\u096b.\u096b", "hi")["passed"])
        self.assertEqual(number_check("15", "\u0967\u096b", "hi")["digit_scripts"], ["Deva"])
        self.assertFalse(number_check("15", "\u0967\u096b", "ta")["passed"])

    def test_split_matches_grounding(self):
        self.assertEqual(Grounding.split_sentences("Use 1.0 g. Check leaves; do not spray!"),
                         ["Use 1.0 g.", "Check leaves;", "do not spray!"])

    def test_repetition(self):
        self.assertTrue(repeated_output("white white white white leaves"))
        self.assertTrue(repeated_output("a b a b a b a b"))
        self.assertFalse(repeated_output("Check leaves and stems."))

    def test_protect(self):
        text = "Trichoderma asperellum @ 4 g/kg seeds."
        masked, mapping = protect(text, [])
        self.assertNotIn("Trichoderma", masked)
        self.assertNotIn("4 g", masked)
        for marker, original in mapping.items():
            masked = masked.replace(marker, original)
        self.assertEqual(masked, text)
        masked, mapping = protect("Use 5% or 10% W/W.", [])
        self.assertIn("@keep.invalid or ", masked)
        self.assertEqual(list(mapping.values()), ["5%", "10% W/W"])

    def test_fail_closed_and_chemical_bypass(self):
        class BadEngine:
            def translate(self, *args):
                return "999", True, 0.01
        answers = [{"id": "a", "text": "Wait 7 days."},
                   {"id": "b", "text": "Product 5 g.", "section": "chemical"},
                   {"id": "c", "text": "Rejected text.", "accepted": False}]
        rows = translate_answers(BadEngine(), answers, list(LANGUAGES))
        self.assertEqual(len(rows), 27)
        for row in rows:
            if row["id"] == "a":
                self.assertEqual(row["display_text"], "")
                self.assertEqual(row["sentences"][0]["status"], "withheld")
            elif row["id"] == "b":
                self.assertEqual(row["display_text"], "Product 5 g.")
            else:
                self.assertEqual(row["display_text"], "")

    def test_entity_and_runtime_failure(self):
        class MissingEntity:
            def translate(self, *args):
                return "Candidate without the product", False, 0.01
        row = translate_answers(MissingEntity(), [{"id": "a", "text": "Product."}], ["hi"])[0]
        self.assertEqual(row["display_text"], "")
        self.assertFalse(row["sentences"][0]["protected_text_check"])

        class FailingEngine:
            def translate(self, *args):
                raise ValueError("fixture generation error")
        row = translate_answers(FailingEngine(), [{"id": "a", "text": "One. Two."}], ["hi"])[0]
        self.assertEqual(row["display_text"], "")
        self.assertEqual(len(row["sentences"]), 2)
        self.assertTrue(all(s["error"] == "ValueError: fixture generation error" for s in row["sentences"]))


if __name__ == "__main__":
    unittest.main()
