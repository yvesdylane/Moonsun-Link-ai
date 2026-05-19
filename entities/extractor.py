from rapidfuzz import process, fuzz
from entities.vocabulary import PRODUCTS, LOCATIONS

class EntityExtractor:
    def extract(self, text: str) -> dict:
        text = text.lower()
        return {
            "product": self._match(text, PRODUCTS),
            "location": self._match(text, LOCATIONS),
        }

    def _match(self, text: str, vocabulary: list) -> str | None:
        match = process.extractOne(text, vocabulary, scorer=fuzz.partial_ratio)
        if match and match[1] >= 80:
            return match[0]
        return None