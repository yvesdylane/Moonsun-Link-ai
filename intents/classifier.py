import re
from rapidfuzz import process, fuzz
from intents.patterns import INTENT_PATTERNS


class IntentClassifier:
    def classify(self, text: str) -> dict:
        text = text.lower()

        # Tier 1 — keyword match
        for intent_name, intent_data in INTENT_PATTERNS.items():
            for keyword in intent_data["keywords"]:
                if re.search(rf"\b{re.escape(keyword)}\b", text):
                    return {"intent": intent_name, "confidence": 0.9, "method": "keyword"}

        # Tier 2 — fuzzy match against examples
        return self._fuzzy_match(text)

    def _fuzzy_match(self, text: str) -> dict:
        # flatten all examples into (sentence, intent_name) pairs
        examples = [
            (example, intent_name)
            for intent_name, intent_data in INTENT_PATTERNS.items()
            for example in intent_data["examples"]
        ]

        choices = [e[0] for e in examples]
        match = process.extractOne(text, choices, scorer=fuzz.token_set_ratio)

        if match and match[1] >= 70:
            intent_name = examples[match[2]][1]
            return {"intent": intent_name, "confidence": round(match[1] / 100, 2), "method": "fuzzy"}

        return {"intent": "unknown", "confidence": 0.0}