KEYWORDS = {
    'help': [
        'ajuda', 'socorro', 'como usar', 'comandos'
    ],
    'list': [
        'listar', 'mostrar', 'ver', 'lista', 'tudo', 'mostra', 'exibir', 'ler'
    ],
    'add': [
        'adicionar', 'comprar', 'pegar', 'precisar', 'precisamos',
        'colocar', 'incluir', 'quero', 'querer', 'bota', 'põe', 'poe',
        'adiciona', 'falta', 'coloca', 'inclui', 'pega', 'preciso'
    ],
    'delete': [
        'remover', 'deletar', 'tirar', 'apagar', 'excluir', 'tira',
        'remove', 'apaga', 'exclui', 'corta', 'risca', 'comprei',
        'descartar', 'cancela', 'cancelar', 'peguei'
    ],
    'modify': [
        'modificar', 'mudar', 'atualizar', 'alterar', 'editar', 'trocar',
        'corrige', 'corrigir', 'arrumar', 'arruma', 'conserta',
        'consertar', 'muda', 'altera', 'atualiza'
    ],
    'clear_list': [
        'terminei', 'finalizei', 'acabei', 'zerar', 'zera',
        'limpar', 'limpa', 'fechei', 'encerrar'
    ],
    'start_shopping': [
        'indo', 'fui', 'cheguei', 'iniciar', 'partiu', 'começando',
        'mercado', 'supermercado'
    ],
}

# Flat map: keyword string → action
_KEYWORD_MAP = {kw: action for action, kws in KEYWORDS.items() for kw in kws}

# When multiple action keywords appear in the same phrase, lower number wins
_ACTION_PRIORITY = {'delete': 0, 'modify': 1, 'add': 2, 'list': 3, 'clear_list': 4, 'start_shopping': 5}


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

    Scans all words for action keywords (not just the first), using priority to
    resolve conflicts (e.g. "preciso remover frango" → delete, not add).
    Implicit add: messages with no keyword → treated as add.
    """
    words = message.strip().lower().split()
    if not words:
        return {'action': 'unknown', 'item': None, 'quantity': None}

    # Collect all action keywords found, pick highest-priority one
    found: dict[str, str] = {}  # action → first keyword word that triggered it
    for word in words:
        a = _KEYWORD_MAP.get(word)
        if a and a not in found:
            found[a] = word

    action = min(found, key=lambda a: _ACTION_PRIORITY.get(a, 99)) if found else None

    if action in ('list', 'clear_list', 'start_shopping'):
        return {'action': action, 'item': None, 'quantity': None}

    if action in ('add', 'delete', 'modify'):
        # Strip every action keyword so only the item name + quantity remain
        remaining = [w for w in words if w not in _KEYWORD_MAP]
        quantity, item = _extract_quantity_and_item(remaining)
        return {'action': action, 'item': item, 'quantity': quantity}

    # No keyword — implicit add ("2 maçãs", "maçãs 2", "maçãs")
    quantity, item = _extract_quantity_and_item(words)
    if item:
        return {'action': 'add', 'item': item, 'quantity': quantity or 1}

    return {'action': 'unknown', 'item': None, 'quantity': None}