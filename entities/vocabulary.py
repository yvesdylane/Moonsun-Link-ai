PRODUCTS = [
    # crops
    "maize", "corn", "cassava", "tomato", "onion",
    "plantain", "yam", "cocoyam", "groundnut", "pepper",
    "beans", "rice", "sorghum", "palm oil", "banana",
    "mango", "sweet potato", "potato", "cabbage", "carrot",
    "pineapple", "papaya", "avocado", "garlic", "ginger",
    "okra", "spinach", "lettuce", "cucumber", "pumpkin",
    "coffee", "cocoa", "cotton", "sugarcane",
    # animals
    "chicken", "goat", "sheep", "cattle", "cow",
    "pig", "horse", "donkey", "duck", "turkey",
    "rabbit", "fish", "snail", "grasscutter",
    # tools
    "hoe", "machete", "shovel", "rake", "wheelbarrow",
    "watering can", "sprayer", "pump", "tractor",
    "plough", "harvester", "irrigation pipe",
    "cutlass", "axe", "sickle", "net", "cage",
    # services
    "ploughing", "plowing", "tilling", "harvesting",
    "spraying", "irrigation", "transport", "delivery",
    "mechanic", "veterinary", "consulting", "training",
    "land clearing", "pruning", "grafting", "sowing",
    "weeding", "fencing", "installation",
]

LOCATIONS = [
    "yaounde", "douala", "bafoussam", "bamenda",
    "garoua", "maroua", "bertoua", "ebolowa",
    "nkongsamba", "kumba", "limbe", "buea",
    "dschang", "mbouda", "foumban", "kousseri",
]

PRODUCT_SYNONYMS = {
    "corn": "maize",
    "manioc": "cassava",
    "yuca": "cassava",
    "groundnuts": "groundnut",
    "peanut": "groundnut",
    "peanuts": "groundnut",
    "hot pepper": "pepper",
    "plantains": "plantain",
    "mangoes": "mango",
    "cocoyams": "cocoyam",
    "sweet potatoes": "sweet potato",
    "yam tuber": "yam",
    "palm oil": "palm oil",
    "red oil": "palm oil",
    "palm nut": "palm oil",
    "cows": "cattle",
    "bull": "cattle",
    "bulls": "cattle",
    "fishes": "fish",
    "chickens": "chicken",
    "goats": "goat",
    "pigs": "pig",
    "sheeps": "sheep",
    "ducks": "duck",
    "turkeys": "turkey",
    "rabbits": "rabbit",
    "hens": "chicken",
    "cockerel": "chicken",
    "rooster": "chicken",
    "shovels": "shovel",
    "machetes": "machete",
    "hoes": "hoe",
    "tractors": "tractor",
    "ploughing service": "ploughing",
    "plowing service": "plowing",
    "spraying service": "spraying",
    "transport service": "transport",
    "delivery service": "delivery",
    "land clearing service": "land clearing",
    "land preparation": "land clearing",
    "mechanical work": "mechanic",
    "vet": "veterinary",
}

REGIONS = [
    "Adamaoua", "Centre", "Est", "Extreme-Nord",
    "Littoral", "Nord", "Nord-Ouest",
    "Ouest", "Sud", "Sud-Ouest", "General"
]

PRODUCT_TYPES = {
    # crops
    "maize": "crop", "corn": "crop", "cassava": "crop",
    "tomato": "crop", "onion": "crop", "plantain": "crop",
    "yam": "crop", "cocoyam": "crop", "groundnut": "crop",
    "pepper": "crop", "beans": "crop", "rice": "crop",
    "sorghum": "crop", "palm oil": "crop", "banana": "crop",
    "mango": "crop", "sweet potato": "crop", "potato": "crop",
    "cabbage": "crop", "carrot": "crop", "pineapple": "crop",
    "papaya": "crop", "avocado": "crop", "garlic": "crop",
    "ginger": "crop", "okra": "crop", "spinach": "crop",
    "lettuce": "crop", "cucumber": "crop", "pumpkin": "crop",
    "coffee": "crop", "cocoa": "crop", "cotton": "crop",
    "sugarcane": "crop",
    # animals
    "chicken": "animal", "goat": "animal", "sheep": "animal",
    "cattle": "animal", "cow": "animal", "pig": "animal",
    "horse": "animal", "donkey": "animal", "duck": "animal",
    "turkey": "animal", "rabbit": "animal", "fish": "animal",
    "snail": "animal", "grasscutter": "animal",
    # tools
    "hoe": "tool", "machete": "tool", "shovel": "tool",
    "rake": "tool", "wheelbarrow": "tool", "watering can": "tool",
    "sprayer": "tool", "pump": "tool", "tractor": "tool",
    "plough": "tool", "harvester": "tool", "irrigation pipe": "tool",
    "cutlass": "tool", "axe": "tool", "sickle": "tool",
    "net": "tool", "cage": "tool",
    # services
    "ploughing": "service", "plowing": "service", "tilling": "service",
    "harvesting": "service", "spraying": "service", "irrigation": "service",
    "transport": "service", "delivery": "service", "mechanic": "service",
    "veterinary": "service", "consulting": "service", "training": "service",
    "land clearing": "service", "pruning": "service", "grafting": "service",
    "sowing": "service", "weeding": "service", "fencing": "service",
    "installation": "service",
}

# Default measurements by product type
TYPE_DEFAULT_MEASUREMENTS = {
    "crop": "kg",
    "animal": "head",
    "tool": "piece",
    "service": "task",
}

# For auto-detection of measurement from user text
MEASUREMENT_KEYWORDS = [
    "kg", "kilo", "kilos", "kilogram", "kilograms",
    "bag", "bags", "sack", "sacks",
    "gallon", "gallons",
    "liter", "liters", "litre", "litres",
    "bottle", "bottles",
    "crate", "crates",
    "carton", "cartons",
    "tin", "tins",
    "piece", "pieces",
    "head", "heads",
    "bunch", "bunches",
    "dozen", "dozens",
    "ton", "tonnes",
    "hour", "hours",
    "day", "days",
    "week", "weeks",
    "month", "months",
    "task", "tasks",
    "job", "jobs",
    "session", "sessions",
    "unit", "units",
    "pair", "pairs",
    "box", "boxes",
    "basket", "baskets",
    "bowl", "bowls",
]
