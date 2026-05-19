from intents.classifier import IntentClassifier

clf = IntentClassifier()

tests = [
    "i want to sell my maize",
    "who is selling corn in yaounde",
    "show me my current listings",
    "delete my tomato listing",
    "what is the weather today",   # should return unknown
]

for text in tests:
    result = clf.classify(text)
    print(f"{text!r:50} → {result}")