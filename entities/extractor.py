import re
from rapidfuzz import process, fuzz
from entities.vocabulary import PRODUCTS, LOCATIONS, MEASUREMENT_KEYWORDS
from utils.region_resolver import resolve_region


class EntityExtractor:
    def extract(self, text: str) -> dict:
        text_lower = text.lower()
        return {
            "product": self._match(text_lower, PRODUCTS),
            "location": self._match(text_lower, LOCATIONS),
            "quantity": self._extract_quantity(text_lower),
            "measurement": self._extract_measurement(text_lower),
            "price": self._extract_price(text_lower),
            "region": self._extract_region(text),
            "origin": self._extract_origin(text),
        }

    def _extract_region(self, text: str) -> str | None:
        match = re.search(r"\b(selling in|in|au|dans)\s+([a-zA-Z\-]+)", text, re.IGNORECASE)
        if match:
            return resolve_region(match.group(2))
        return None

    def _extract_origin(self, text: str) -> str | None:
        match = re.search(r"\b(from|de|depuis|origin|origine)\s+([a-zA-Z\-]+)", text, re.IGNORECASE)
        if match:
            return resolve_region(match.group(2))
        return None

    def _match(self, text: str, vocabulary: list) -> str | None:
        match = process.extractOne(text, vocabulary, scorer=fuzz.partial_ratio)
        if match and match[1] >= 80:
            return match[0]
        return None

    def _extract_quantity(self, text: str) -> int | None:
        # "200kg", "200 kg", "200k", "200 kilo"
        match = re.search(r"(\d+)\s*(kg|kilo|k)\b", text)
        if match:
            return int(match.group(1))
        # "5 bags", "10 gallons", "2 hours" — with measurement but no kg
        match = re.search(r"(\d+)\s*(bag|bags|gallon|gallons|liter|liters|litre|litres|hour|hours|day|days|piece|pieces|head|heads|bunch|bunches|crate|crates|sack|sacks|tin|tins|bottle|bottles|carton|cartons|ton|tonnes|dozen|dozens|session|sessions|unit|units|pair|pairs|box|boxes|basket|baskets|task|tasks|job|jobs)\b", text)
        if match:
            return int(match.group(1))
        return None

    def _extract_measurement(self, text: str) -> str | None:
        # "200kg", "200 kg"
        match = re.search(r"(\d+)\s*(kg|kilo|k)\b", text)
        if match:
            return "kg"
        # "5 bags", "10 gallons", "2 hours"
        match = re.search(r"(\d+)\s*(bag|bags|gallon|gallons|liter|liters|litre|litres|hour|hours|day|days|piece|pieces|head|heads|bunch|bunches|crate|crates|sack|sacks|tin|tins|bottle|bottles|carton|cartons|ton|tonnes|dozen|dozens|session|sessions|unit|units|pair|pairs|box|boxes|basket|baskets|task|tasks|job|jobs)\b", text)
        if match:
            raw = match.group(2).lower()
            # Normalize plural/singular
            singular_map = {
                "bags": "bag", "gallons": "gallon", "liters": "liter", "litres": "liter",
                "hours": "hour", "days": "day", "pieces": "piece", "heads": "head",
                "bunches": "bunch", "crates": "crate", "sacks": "sack", "tins": "tin",
                "bottles": "bottle", "cartons": "carton", "tonnes": "ton",
                "dozens": "dozen", "sessions": "session", "units": "unit",
                "pairs": "pair", "boxes": "box", "baskets": "basket",
                "tasks": "task", "jobs": "job",
            }
            return singular_map.get(raw, raw)
        # "mecanicien", "veterinary" — service mentions with no explicit unit → task
        service_keywords = [
            "mecanicien", "mechanic", "veterinary", "vet", "ploughing", "plowing",
            "tilling", "harvesting", "spraying", "irrigation", "transport",
            "delivery", "consulting", "training", "land clearing", "pruning",
            "grafting", "sowing", "weeding", "fencing", "installation",
        ]
        if any(kw in text for kw in service_keywords):
            return "task"
        return None

    def _extract_price(self, text: str) -> int | None:
        match = re.search(r"(\d+)\s*(fcfa|xaf|fcf|cfa)\b", text)
        if match:
            return int(match.group(1))
        return None
