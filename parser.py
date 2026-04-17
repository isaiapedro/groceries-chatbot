KEYWORDS = {
    'list': [
        'list', 'show', 'what', 'display', 'see', 'all',
        'listar', 'mostrar', 'ver', 'lista', 'tudo',
    ],
    'add': [
        'add', 'buy', 'get', 'need', 'put', 'include', 'want', 'purchase',
        'adicionar', 'comprar', 'pegar', 'precisar', 'colocar', 'incluir', 'quero', 'querer',
    ],
    'delete': [
        'remove', 'delete', 'drop', 'cancel',
        'remover', 'deletar', 'tirar', 'apagar', 'excluir',
    ],
    'modify': [
        'modify', 'change', 'update', 'set', 'adjust', 'edit',
        'modificar', 'mudar', 'atualizar', 'alterar', 'editar', 'trocar',
    ],
    'clear_list': [
        'finished shopping', 'done shopping', 'bought everything', 'all done', 'shopping done',
        'compras feitas', 'terminei as compras', 'finalizei as compras', 'comprei tudo',
        'terminei', 'finalizei',
    ],
    'start_shopping': [
        'going shopping', 'at the store', 'starting shopping', 'im at the store',
        "i'm at the store", 'heading to store', 'at supermarket',
        'vou às compras', 'vou fazer compras', 'vou ao mercado', 'vou ao supermercado',
        'indo fazer compras', 'indo ao mercado', 'fui fazer compras',
    ],
}

# Multi-word phrases must be checked before single-word keywords
_MULTI_WORD = {phrase: action for action, phrases in KEYWORDS.items() for phrase in phrases if ' ' in phrase}
_SINGLE_WORD = {kw: action for action, kws in KEYWORDS.items() for kw in kws if ' ' not in kw}


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
    Actions: 'add' | 'delete' | 'modify' | 'list' | 'clear_list' | 'start_shopping' | 'unknown'

    Implicit add: messages with no keyword → treated as add.
    """
    text = message.strip().lower()
    words = text.split()

    if not words:
        return {'action': 'unknown', 'item': None, 'quantity': None}

    # Check multi-word phrases first (longer match wins)
    for phrase in sorted(_MULTI_WORD, key=len, reverse=True):
        if text.startswith(phrase):
            action = _MULTI_WORD[phrase]
            return {'action': action, 'item': None, 'quantity': None}

    # Single-word keyword at position 0
    action = _SINGLE_WORD.get(words[0])

    if action in ('list', 'clear_list', 'start_shopping'):
        return {'action': action, 'item': None, 'quantity': None}

    if action in ('add', 'delete', 'modify'):
        quantity, item = _extract_quantity_and_item(words[1:])
        return {'action': action, 'item': item, 'quantity': quantity}

    # No keyword — implicit add ("2 apples", "apples 2", "apples")
    quantity, item = _extract_quantity_and_item(words)
    if item:
        return {'action': 'add', 'item': item, 'quantity': quantity or 1}

    return {'action': 'unknown', 'item': None, 'quantity': None}
