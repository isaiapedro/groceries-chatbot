CATEGORY_ORDER = [
    "Hortifruti",
    "Açougue & Peixaria",
    "Laticínios & Ovos",
    "Padaria",
    "Despensa & Mercearia",
    "Produtos Internacionais",
    "Biscoitos & Doces",
    "Bebidas",
    "Congelados",
    "Limpeza",
    "Higiene Pessoal",
    "Pet Shop",
    "Itens Especiais",
]

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Hortifruti": [
        "alface", "tomate", "batata", "cebola", "cenoura", "pimentão", "abobrinha", 
        "pepino", "beterraba", "cogumelo", "ervas", "couve", "espinafre", "maçã", 
        "banana", "laranja", "limão", "uva", "morango", "mirtilo", "manga", 
        "abacaxi", "melancia", "melão", "pêssego", "pera", "cereja", "abacate", 
        "alho", "aipo", "berinjela", "milho", "gengibre", "salsinha", "coentro", 
        "manjericão", "hortelã", "alecrim", "tomilho", "cebolinha", "repolho", 
        "brócolis", "couve-flor", "batata-doce", "mandioca", "aipim", "macaxeira", 
        "mamão", "maracujá", "kiwi", "tangerina", "mexerica", "ponkan", "goiaba",
        "rúcula", "agrião", "alho-poró", "inhame", "chuchu", "quiabo", "vagem"
    ],
    "Açougue & Peixaria": [
        "carne", "frango", "porco", "peixe", "camarão", "atum", "salmão", 
        "linguiça", "calabresa", "costela", "filé", "picanha", "alcatra", 
        "maminha", "fraldinha", "contrafilé", "patinho", "coxão mole", "coxão duro", 
        "peito de frango", "coxa", "sobrecoxa", "asa", "coração", "bacon", 
        "presunto", "mortadela", "salame", "salsicha", "lombo", "pernil", 
        "tilápia", "bacalhau", "sardinha", "lula", "polvo", "ostra", "carne moída",
        "peito de peru", "copa", "merluza", "pescada", "pintado", "tambaqui"
    ],
    "Laticínios & Ovos": [
        "leite", "manteiga", "queijo", "iogurte", "creme de leite", "ovo", "ovos", 
        "requeijão", "nata", "muçarela", "mussarela", "prato", "provolone", 
        "parmesão", "gorgonzola", "minas", "coalho", "cheddar", "ricota", 
        "leite condensado", "doce de leite", "margarina", "yakult", 
        "leite fermentado", "coalhada", "petit suisse", "danoninho", "catupiry"
    ],
    "Padaria": [
        "pão", "bolo", "torta", "rosca", "coxinha", "pãozinho", "pão francês", 
        "pão de forma", "pão integral", "pão de queijo", "bisnaguinha", "baguete", 
        "croissant", "sonho", "empada", "pastel", "esfiha", "pão doce", "sírio",
        "broa", "panetone", "chocotone", "ciabatta"
    ],
    "Despensa & Mercearia": [
        "arroz", "feijão", "macarrão", "farinha", "açúcar", "sal", "azeite", 
        "molho", "óleo", "vinagre", "mostarda", "maionese", "lentilha", 
        "grão-de-bico", "aveia", "mel", "geleia", "ketchup", "extrato de tomate", 
        "massa", "farofa", "farinha de mandioca", "farinha de trigo", "fubá", 
        "polvilho", "tapioca", "amido de milho", "pimenta", "orégano", "canela", 
        "colorau", "cominho", "louro", "caldo", "sopa", "enlatado", "milho em lata", 
        "ervilha", "atum em lata", "sardinha em lata", "creme de avelã", "nutella",
        "azeitona", "palmito", "champignon", "leite em pó", "fermento", "achocolatado"
    ],
    "Produtos Internacionais": [
        "shoyu", "missô", "leite de coco", "lamen", "lámen", "miojo", "curry", 
        "taco", "tortilha", "wasabi", "tofu", "tahine", "molho inglês", 
        "molho de ostra", "alga", "nori", "kimchi", "sriracha", "óleo de gergelim",
        "guacamole", "hummus", "homus"
    ],
    "Biscoitos & Doces": [
        "salgadinho", "biscoito", "bolacha", "amendoim", "castanha", "nozes", 
        "pipoca", "bala", "doce", "chocolate", "bombom", "chiclete", "marshmallow", 
        "pirulito", "paçoca", "pé de moleque", "goiabada", "bananinha", 
        "barra de cereal", "chips", "doritos", "ruffles", "wafer", "cookies",
        "torrada", "suspiro", "gelatina", "pudim", "leite moça"
    ],
    "Bebidas": [
        "água", "suco", "refrigerante", "café", "chá", "cerveja", "vinho", 
        "cachaça", "vodka", "energético", "gin", "rum", "espumante", "champanhe", 
        "licor", "mate", "guaraná", "água com gás", "água de coco", "toddy", 
        "nescau", "ice", "kombucha", "cápsula de café", "refrigerante zero"
    ],
    "Congelados": [
        "sorvete", "picolé", "pizza congelada", "nuggets", "hambúrguer", 
        "batata frita", "lasanha congelada", "prato pronto", "pão de queijo congelado", 
        "polpa de fruta", "açaí", "legumes congelados", "empanado", "kibe congelado",
        "torta congelada", "hambúrguer vegetal"
    ],
    "Limpeza": [
        "detergente", "sabão", "desinfetante", "esponja", "papel toalha", 
        "saco de lixo", "guardanapo", "sabão em pó", "sabão líquido", "amaciante", 
        "água sanitária", "cândida", "álcool", "limpador multiuso", "lustra-móveis", 
        "limpa-vidros", "vassoura", "rodo", "pá", "pano de chão", "flanela", 
        "palha de aço", "bombril", "tira-manchas", "desengordurante", "inseticida",
        "repelente", "purificador de ar", "naftalina"
    ],
    "Higiene Pessoal": [
        "sabonete", "creme", "protetor solar", "curativo", "remédio", "vitamina", 
        "desodorante", "shampoo", "xampu", "condicionador", "pasta de dente", 
        "creme dental", "escova de dente", "fio dental", "enxaguante bucal", 
        "lâmina de barbear", "prestobarba", "espuma de barbear", "hidratante", 
        "loção", "absorvente", "algodão", "cotonete", "band-aid", "papel higiênico",
        "lenço umedecido", "fralda", "talco", "gel de cabelo", "creme de pentear"
    ],
    "Pet Shop": [
        "ração", "areia para gato", "petisco", "tapete higiênico", "sachê", 
        "patê", "osso", "coleira", "brinquedo pet", "shampoo pet", "antipulgas",
        "comedouro", "bebedouro", "bifinho"
    ],
}

# Flat map: keyword → category (longest keywords matched first to handle multi-word)
_KEYWORD_TO_CATEGORY: dict[str, str] = {}
for _cat, _kws in _CATEGORY_KEYWORDS.items():
    for _kw in _kws:
        _KEYWORD_TO_CATEGORY[_kw] = _cat


def categorize_item(item_name: str) -> str:
    name_lower = item_name.strip().lower()

    # Exact full-name match
    if name_lower in _KEYWORD_TO_CATEGORY:
        return _KEYWORD_TO_CATEGORY[name_lower]

    # Multi-word keywords as substrings (longest first to prefer specific matches)
    for keyword in sorted(_KEYWORD_TO_CATEGORY, key=len, reverse=True):
        if " " in keyword and keyword in name_lower:
            return _KEYWORD_TO_CATEGORY[keyword]

    # Single-word match on each token
    for word in name_lower.split():
        if word in _KEYWORD_TO_CATEGORY:
            return _KEYWORD_TO_CATEGORY[word]

    return "Itens Especiais"