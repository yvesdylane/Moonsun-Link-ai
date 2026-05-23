from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator

# makes detection consistent/reproducible
DetectorFactory.seed = 0

def translate_to_english(text: str) -> tuple[str, str]:
    try:
        lang = detect(text)
        # if not english or french, default to english
        if lang not in ("en", "fr"):
            lang = "en"
        if lang == "en":
            return text, "en"
        translated = GoogleTranslator(source="fr", target="en").translate(text)
        return translated, "fr"
    except Exception:
        return text, "en"

def translate_reply(text: str, target_lang: str) -> str:
    try:
        if target_lang != "fr":
            return text
        return GoogleTranslator(source="en", target="fr").translate(text)
    except Exception:
        return text