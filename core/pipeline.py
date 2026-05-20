from intents.classifier import IntentClassifier
from entities.extractor import EntityExtractor
from db.controller.logController import log_message

class AssistantPipeline:
    def __init__(self):
        self.classifier = IntentClassifier()
        self.extractor = EntityExtractor()

    def process(self, text: str) -> dict:
        intent = self.classifier.classify(text)
        entities = self.extractor.extract(text)

        log_message(text, intent, entities)

        return {
            "input": text,
            "intent": intent,
            "entities": entities
        }