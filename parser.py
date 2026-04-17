KEYWORDS = {
    'list': [
        'list', 'show', 'what', 'display', 'see', 'all',
        # pt-BR
        'listar', 'mostrar', 'ver', 'lista', 'tudo',
    ],
    'add': [
        'add', 'buy', 'get', 'need', 'put', 'include', 'want', 'purchase',
        # pt-BR
        'adicionar', 'comprar', 'pegar', 'precisar', 'colocar', 'incluir', 'quero', 'querer',
    ],
    'delete': [
        'remove', 'delete', 'bought', 'done', 'got', 'cross', 'check', 'drop', 'cancel',
        # pt-BR
        'remover', 'deletar', 'tirar', 'apagar', 'excluir', 'riscar', 'comprei', 'peguei',
    ],
    'modify': [
        'modify', 'change', 'update', 'set', 'adjust', 'edit',
        # pt-BR
        'modificar', 'mudar', 'atualizar', 'alterar', 'editar', 'trocar',
    ],
}

# Flat map: keyword string → action
_KEYWORD_MAP = {kw: action for action, keywords in KEYWORDS.items() for kw in keywords}


def _extract_quantity_and_item(words: list) -> tuple[int | None, str | None]:
    quantity = None
    item_words = []

    for word in words:
        if quantity is None and word.isdigit():
            quantity = int(word)
        else:
            item_words.append(word)

    item = ' '.join(item_words).strip() or None
    return quantity, item


def parse_command(message: str) -> dict:
    """
    Parse a WhatsApp message into a command dict.

    Returns dict with keys: action, item, quantity
    Possible actions: 'add' | 'delete' | 'modify' | 'list' | 'unknown'

    Implicit add: messages with no keyword (e.g. "2 apples" or "apples") → add
    """
    words = message.strip().lower().split()
    if not words:
        return {'action': 'unknown', 'item': None, 'quantity': None}

    action = _KEYWORD_MAP.get(words[0])

    if action == 'list':
        return {'action': 'list', 'item': None, 'quantity': None}

    if action in ('add', 'delete', 'modify'):
        quantity, item = _extract_quantity_and_item(words[1:])
        return {'action': action, 'item': item, 'quantity': quantity}

    # No keyword found — treat as implicit add ("2 apples", "apples 2", "apples")
    quantity, item = _extract_quantity_and_item(words)
    if item:
        return {'action': 'add', 'item': item, 'quantity': quantity or 1}

    return {'action': 'unknown', 'item': None, 'quantity': None}
