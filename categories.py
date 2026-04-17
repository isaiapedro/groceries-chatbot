CATEGORY_ORDER = [
    "Produce",
    "Meat & Seafood",
    "Dairy & Eggs",
    "Bakery",
    "Pantry & Dry Goods",
    "International & Global",
    "Snacks & Sweets",
    "Beverages",
    "Frozen Foods",
    "Household & Cleaning",
    "Personal Care",
    "Pet Care",
    "Uncategorized",
]

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Produce": [
        "apple", "apples", "banana", "bananas", "orange", "oranges", "lemon", "lemons",
        "lime", "limes", "grape", "grapes", "strawberry", "strawberries", "blueberry",
        "blueberries", "mango", "mangoes", "pineapple", "watermelon", "melon", "peach",
        "pear", "cherry", "cherries", "avocado", "avocados",
        "lettuce", "spinach", "kale", "arugula", "cabbage", "broccoli", "cauliflower",
        "carrot", "carrots", "potato", "potatoes", "sweet potato", "onion", "onions",
        "garlic", "tomato", "tomatoes", "pepper", "peppers", "cucumber", "celery",
        "zucchini", "eggplant", "beetroot", "beet", "corn", "mushroom", "mushrooms",
        "ginger", "herb", "herbs", "parsley", "cilantro", "basil", "mint", "rosemary",
        "thyme", "alface", "tomate", "batata", "cebola", "cenoura", "pimentão",
        "abobrinha", "pepino", "beterraba", "cogumelo", "ervas", "couve", "espinafre",
    ],
    "Meat & Seafood": [
        "beef", "chicken", "pork", "lamb", "turkey", "veal", "duck",
        "steak", "ground beef", "mince", "sausage", "sausages", "bacon", "ham",
        "salami", "pepperoni", "chorizo", "ribs",
        "fish", "salmon", "tuna", "tilapia", "cod", "shrimp", "prawns", "crab",
        "lobster", "oyster", "squid", "octopus", "sardine", "sardines",
        "carne", "frango", "porco", "peixe", "camarão", "atum", "salmão",
        "linguiça", "calabresa", "costela", "filé", "picanha",
    ],
    "Dairy & Eggs": [
        "milk", "butter", "cheese", "yogurt", "yoghurt", "cream", "sour cream",
        "cream cheese", "mozzarella", "cheddar", "parmesan", "brie", "gouda",
        "egg", "eggs", "whipped cream", "condensed milk", "evaporated milk",
        "leite", "manteiga", "queijo", "iogurte", "creme", "ovo", "ovos",
        "requeijão", "nata",
    ],
    "Bakery": [
        "bread", "bun", "buns", "roll", "rolls", "baguette", "croissant",
        "muffin", "muffins", "cake", "pastry", "pastries", "donut", "donuts",
        "bagel", "bagels", "tortilla", "tortillas", "pita", "flatbread",
        "sourdough", "brioche",
        "pão", "bolo", "torta", "rosca", "coxinha", "pãozinho",
    ],
    "Pantry & Dry Goods": [
        "rice", "pasta", "noodle", "noodles", "spaghetti", "penne", "flour",
        "sugar", "salt", "pepper", "oil", "olive oil", "vinegar", "sauce",
        "tomato sauce", "ketchup", "mustard", "mayonnaise", "soy sauce",
        "bean", "beans", "lentil", "lentils", "chickpea", "chickpeas",
        "oat", "oats", "cereal", "granola", "honey", "jam", "peanut butter",
        "canned", "can", "soup", "broth", "stock", "spice", "spices",
        "cinnamon", "paprika", "cumin", "oregano", "bay leaf",
        "arroz", "feijão", "macarrão", "farinha", "açúcar", "sal", "azeite",
        "molho", "óleo", "vinagre", "mostarda", "maionese", "lentilha",
        "grão de bico", "aveia", "mel", "geleia",
    ],
    "International & Global": [
        "lamen", "ramen", "soy", "curry", "taco", "tortilla chip", "salsa",
        "wasabi", "miso", "tofu", "kimchi", "sriracha", "tahini", "hummus",
        "coconut milk", "fish sauce", "oyster sauce", "hoisin", "pad thai",
        "nori", "sake", "mirin", "panko",
        "shoyu", "missô", "leite de coco",
    ],
    "Snacks & Sweets": [
        "chip", "chips", "crisp", "crisps", "popcorn", "pretzel", "cracker",
        "crackers", "cookie", "cookies", "biscuit", "biscuits", "chocolate",
        "candy", "candies", "gummy", "gummies", "lollipop", "marshmallow",
        "brownie", "bar", "granola bar", "nut", "nuts", "almond", "almonds",
        "cashew", "cashews", "peanut", "peanuts", "pistachio", "walnut",
        "salgadinho", "biscoito", "bolacha", "amendoim", "castanha", "nozes",
        "pipoca", "bala", "doce",
    ],
    "Beverages": [
        "water", "juice", "soda", "cola", "coffee", "tea", "milk tea",
        "energy drink", "sports drink", "beer", "wine", "vodka", "whiskey",
        "rum", "gin", "champagne", "sparkling water", "coconut water",
        "smoothie", "lemonade",
        "água", "suco", "refrigerante", "café", "chá", "cerveja", "vinho",
        "cachaça", "vodka", "energético",
    ],
    "Frozen Foods": [
        "frozen", "ice cream", "gelato", "sorbet", "popsicle",
        "frozen pizza", "frozen meal", "frozen vegetable", "frozen fruit",
        "frozen fish", "nugget", "nuggets", "fries", "french fries",
        "sorvete", "picolé", "pizza congelada", "nuggets",
    ],
    "Household & Cleaning": [
        "detergent", "dish soap", "laundry", "bleach", "disinfectant",
        "sponge", "sponges", "paper towel", "trash bag", "garbage bag",
        "cleaning", "cleaner", "mop", "broom", "toilet paper", "tissue",
        "napkin", "napkins", "foil", "aluminum foil", "plastic wrap",
        "zip bag", "zip bags",
        "detergente", "sabão", "desinfetante", "esponja", "papel toalha",
        "saco de lixo", "papel higiênico", "guardanapo",
    ],
    "Personal Care": [
        "shampoo", "conditioner", "soap", "body wash", "shower gel",
        "toothpaste", "toothbrush", "floss", "deodorant", "razor",
        "shaving cream", "moisturizer", "lotion", "sunscreen",
        "cotton", "band aid", "bandage", "medicine", "vitamin", "vitamins",
        "ibuprofen", "paracetamol", "aspirin",
        "sabonete", "creme", "protetor solar", "curativo", "remédio",
        "vitamina", "desodorante",
    ],
    "Pet Care": [
        "dog food", "cat food", "pet food", "kibble", "treat", "treats",
        "litter", "cat litter", "pet toy", "leash", "collar",
        "ração", "areia para gato", "petisco",
    ],
}

# Flat map: keyword → category (longest keywords matched first to handle multi-word)
_KEYWORD_TO_CATEGORY: dict[str, str] = {}
for _cat, _kws in _CATEGORY_KEYWORDS.items():
    for _kw in _kws:
        _KEYWORD_TO_CATEGORY[_kw] = _cat


def categorize_item(item_name: str) -> str:
    name_lower = item_name.strip().lower()

    # Try full name match first (handles multi-word like "olive oil")
    if name_lower in _KEYWORD_TO_CATEGORY:
        return _KEYWORD_TO_CATEGORY[name_lower]

    # Try each word in the item name
    for word in name_lower.split():
        if word in _KEYWORD_TO_CATEGORY:
            return _KEYWORD_TO_CATEGORY[word]

    return "Uncategorized"
