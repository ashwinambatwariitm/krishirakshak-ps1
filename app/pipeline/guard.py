"""Output check for text written by Llama, applied before anything is shown to the farmer.

Llama only rephrases retrieved extracts. The check rejects an answer (and the application falls back to showing the
verified extracts directly) when it:

- names a pesticide/chemical that does not appear in the retrieved extracts,
- gives a dose or quantity (number + unit) that does not appear in the retrieved extracts,
- is empty, far too long, or not mainly in the requested language,
- names a different disease than the one diagnosed (English only).
"""
import re

# Active ingredients and product words that must never appear unless they are in the retrieved extracts.
# Includes ingredients that are NOT in the knowledge base, to catch invented advice.
CHEMICAL_WORDS = """
acephate azadirachtin azoxystrobin bifenthrin captan carbaryl carbendazim carbofuran chlorantraniliprole
chlorothalonil chlorpyrifos copper cyantraniliprole cyazofamid cymoxanil cypermethrin dazomet deltamethrin
difenoconazole dimethoate emamectin endosulfan famoxadone fenazaquin fenvalerate flubendiamide fluxapyroxad
glyphosate hexaconazole imidacloprid indoxacarb iprodione kitazin malathion mancozeb metalaxyl methomyl metiram
monocrotophos novaluron oxychloride oxydemeton paraquat phorate phosalone profenofos propiconazole propineb
pyraclostrobin quinalphos spinosad spiromesifen streptocycline streptomycin sulphur sulfur tebuconazole tetracycline
thiamethoxam thiophanate trichlorfon trifloxystrobin zineb ziram
""".split()

UNIT = r"(?:ml|mL|g|gm|gram|grams|kg|l|lit|litre|litres|liter|liters|ppm|%|" \
       r"\u092e\u093f\u0932\u0940|\u0917\u094d\u0930\u093e\u092e|\u0915\u093f\u0932\u094b|\u0932\u0940\u091f\u0930)"
DOSE_RE = re.compile(r"(\d+(?:[.,]\d+)?(?:\s*-\s*\d+(?:[.,]\d+)?)?)\s*" + UNIT + r"(?![A-Za-z])")
DEVANAGARI_RE = re.compile(r"[\u0900-\u097f]")
LATIN_RE = re.compile(r"[A-Za-z]")

DISEASE_WORDS = {"early_blight": "early blight", "late_blight": "late blight", "septoria_leaf_spot": "septoria",
                 "bacterial_spot": "bacterial", "yellow_leaf_curl_virus": "leaf curl"}


def _norm(text):
    """Lower case, Devanagari digits -> ASCII digits, collapse spaces (so '2.5 g' and '2.5g' compare equal)."""
    text = text.translate(str.maketrans("\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f",
                                        "0123456789"))
    return re.sub(r"\s+", "", text.lower())


def check_output(text, facts, lang, diagnosed_topic=None, max_chars=1200):
    """Return (ok, reasons). facts: the list of retrieved chunk dicts given to Llama."""
    reasons = []
    allowed = _norm(" ".join(f"{c['text_en']} {c['text']} {c.get('product') or ''} {c.get('dose') or ''}"
                             for c in facts))
    stripped = text.strip()
    if len(stripped) < 20:
        reasons.append("empty_or_too_short")
    if len(stripped) > max_chars:
        reasons.append("too_long")

    low = stripped.lower()
    for word in CHEMICAL_WORDS:
        if re.search(rf"\b{word}\b", low) and word not in allowed:
            reasons.append(f"chemical_not_in_sources:{word}")
    for match in DOSE_RE.finditer(_norm_keep_spaces(stripped)):
        if _norm(match.group(0)) not in allowed:
            reasons.append(f"dose_not_in_sources:{match.group(0)}")

    letters = len(DEVANAGARI_RE.findall(stripped)) + len(LATIN_RE.findall(stripped))
    if letters:
        share_hi = len(DEVANAGARI_RE.findall(stripped)) / letters
        if lang == "hi" and share_hi < 0.6:
            reasons.append("not_hindi")
        if lang == "en" and share_hi > 0.1:
            reasons.append("not_english")

    if lang == "en" and diagnosed_topic in DISEASE_WORDS:
        for topic, word in DISEASE_WORDS.items():
            if topic != diagnosed_topic and word in low and word not in DISEASE_WORDS[diagnosed_topic]:
                reasons.append(f"other_disease_named:{word}")
    return not reasons, reasons


def _norm_keep_spaces(text):
    """Devanagari digits -> ASCII digits, keeping the text otherwise unchanged (for dose matching)."""
    return text.translate(str.maketrans("\u0966\u0967\u0968\u0969\u096a\u096b\u096c\u096d\u096e\u096f",
                                        "0123456789"))
