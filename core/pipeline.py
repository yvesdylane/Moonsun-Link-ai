from intents.classifier import IntentClassifier
from entities.extractor import EntityExtractor
from db.controller.logController import log_message
from utils.translator import translate_to_english

class AssistantPipeline:
    def __init__(self):
        self.classifier = IntentClassifier()
        self.extractor = EntityExtractor()

    def process(self, text: str) -> dict:
        translated_text, detected_lang = translate_to_english(text)

        intent = self.classifier.classify(translated_text)
        entities = self.extractor.extract(translated_text)

        log_message(text, intent, entities)

        return {
            "input": text,
            "translated": translated_text,
            "language": detected_lang,
            "intent": intent,
            "entities": entities
        }