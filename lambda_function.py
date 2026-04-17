import base64
import json
import os
import secrets
from urllib.parse import parse_qs

from db import SessionLocal
from crud import (
    add_item, modify_item, delete_item, delete_item_by_id, find_items_fuzzy,
    list_items, get_all_items, delete_items_by_ids, clear_all_items,
    get_or_create_member,
    get_active_session, create_session, get_session_by_token,
    update_session_payload, delete_session,
)
from categories import categorize_item
from parser import parse_command

HELP_DICT = {
    "lista": "mostra todos os itens",
    "adicionar <item> <qtd>": "adiciona um item",
    "remover <item>": "remove um item",
    "modificar <item> <qtd>": "atualiza a quantidade",
    "vou fazer compras": "inicia a sessão de compras interativa",
    "terminei as compras": "limpa os itens comprados",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_help_text() -> str:
    """Gera a mensagem de ajuda formatada a partir do dicionário."""
    linhas = ["Comandos:"]
    for comando, descricao in HELP_DICT.items():
        linhas.append(f"• {comando} — {descricao}")
    linhas.append("Ou apenas envie '2 maçãs' para adicionar diretamente.")
    return "\n".join(linhas)


def _base_url(event: dict) -> str:
    host = event.get("headers", {}).get("Host", "")
    stage = event.get("requestContext", {}).get("stage", "prod")
    return f"https://{host}/{stage}"


def _twiml(message: str) -> dict:
    safe = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/xml"},
        "body": f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe}</Message></Response>',
    }


def _html(body: str, status: int = 200) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "text/html; charset=utf-8"},
        "body": body,
    }


def _json_resp(data: dict, status: int = 200) -> dict:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(data),
    }


# ---------------------------------------------------------------------------
# Session handlers (WhatsApp side)
# ---------------------------------------------------------------------------

def _handle_confirm_add_response(db, session, message: str, from_number: str, base_url: str) -> str:
    """Handle the user's reply to an '❓ Itens Especiais' confirmation prompt."""
    text = message.strip().lower()
    item = session.payload.get("item")
    qty = session.payload.get("qty", 1)

    delete_session(db, session)

    # 1. Explicit confirmation → add to ❓ Itens Especiais
    if text in ("sim", "s", "confirmar", "confirma", "ok"):
        return add_item(db, item, qty)

    # 2. Recognised command → execute it directly
    command = parse_command(message)
    if command["action"] not in ("unknown",):
        return _dispatch(db, command, from_number, base_url)

    # 3. Unrecognised input → inform and show commands
    return (
        f"Ok, '*{item}*' não foi adicionado.\n\n"
        + get_help_text()
    )


def _handle_bulk_delete_response(db, session, message: str) -> str:
    """Handle the user's reply to a 'finished shopping' prompt."""
    text = message.strip().lower()
    items: list[dict] = session.payload.get("items", [])

    if text in ("tudo", "todos", "confirmar"):
        clear_all_items(db)
        delete_session(db, session)
        return f"Tudo limpo! Todos os {len(items)} itens foram removidos da lista. 🚀"

    # Parse item names from the reply
    keep_names = {w.strip() for w in text.replace(",", " ").split() if w.strip()}
    ids_to_delete = [i["id"] for i in items if i["name"] not in keep_names]
    kept = [i["name"] for i in items if i["name"] in keep_names]

    if ids_to_delete:
        delete_items_by_ids(db, ids_to_delete)

    delete_session(db, session)

    if kept:
        return f"Feito! Foram removidos {len(ids_to_delete)} itens. Mantidos na lista: {', '.join(kept)}. ✨"
    return f"Pronto! Todos os {len(ids_to_delete)} itens marcados foram removidos. 🗑️"


def _handle_confirm_delete_response(db, session, message: str) -> str:
    """Handle the user's reply when multiple items matched a delete search."""
    candidates: list[dict] = session.payload.get("candidates", [])
    text = message.strip().lower()

    delete_session(db, session)

    if text in ("cancelar", "nao", "não", "n", "na", "para"):
        return "Ok, nenhum item foi removido."

    # Match by index ("1", "2", ...)
    if text.isdigit():
        idx = int(text) - 1
        if 0 <= idx < len(candidates):
            return delete_item_by_id(db, candidates[idx]["id"])
        return "Número inválido. Nenhum item removido."

    # Match by partial name
    matches = [c for c in candidates if text in c["name"].lower()]
    if len(matches) == 1:
        return delete_item_by_id(db, matches[0]["id"])
    if len(matches) > 1:
        return "Ainda ambíguo. Tente novamente com um nome mais específico."

    return "Não entendi. Nenhum item removido."


# ---------------------------------------------------------------------------
# Normal command dispatch
# ---------------------------------------------------------------------------

def _dispatch(db, command: dict, from_number: str, base_url: str) -> str:
    action = command["action"]
    item = command["item"]
    qty = command["quantity"]
    if action == "help":
        # Se o usuário digitou "ajuda adicionar", procuramos a palavra "adicionar" no dicionário
        if item:
            for comando, descricao in HELP_DICT.items():
                if item in comando:
                    return f"Como usar o '{item}':\n• {comando} — {descricao}"
            return f"Não encontrei ajuda específica para '{item}'.\n\n{get_help_text()}"
        
        # Se digitou apenas "ajuda"
        return get_help_text()
        
    if action == "list":
        return list_items(db)

    if action == "add":
        if not item:
            return "Por favor, informe o item que deseja adicionar! 🤔 Exemplo: 'adicionar leite 2'"
        if categorize_item(item) == "❓ Itens Especiais":
            create_session(db, from_number, "confirm_add", {"item": item, "qty": qty or 1})
            return (
                f"Não reconheci a categoria de '*{item}*'. "
                f"Deseja adicionar mesmo assim em *❓ Itens Especiais*? "
                f"Responda *sim* para confirmar, ou envie o nome correto do item."
            )
        return add_item(db, item, qty or 1)

    if action == "delete":
        if not item:
            return "O que você deseja remover? Exemplo: 'remover leite'"
        matches = find_items_fuzzy(db, item)
        if not matches:
            return f"Nenhum item com '{item}' encontrado na lista."
        if len(matches) == 1:
            return delete_item_by_id(db, matches[0].id)
        # Multiple matches — ask user to pick
        candidates = [{"id": m.id, "name": m.item_name} for m in matches]
        create_session(db, from_number, "confirm_delete", {"candidates": candidates})
        options = "\n".join(f"{i+1}. {c['name']}" for i, c in enumerate(candidates))
        return f"Encontrei mais de um item com '{item}':\n{options}\n\nQual devo remover? Responda com o número ou nome."

    if action == "modify":
        if not item or not qty:
            return "Uso: 'modificar leite 3'"
        return modify_item(db, item, qty)

    if action == "clear_list":
        all_items = get_all_items(db)
        if not all_items:
            return "A lista de compras já está vazia! ✨"
        names = ", ".join(i["name"].capitalize() for i in all_items)
        create_session(db, from_number, "bulk_delete", {"items": all_items})
        return (
            f"Os seguintes itens serão excluídos:\n{names}\n\n"
            "Responda com os itens que você deseja manter, "
            "ou digite 'tudo' para limpar a lista inteira! 🧹"
        )

    if action == "start_shopping":
        all_items = get_all_items(db)
        if not all_items:
            return "Sua lista está vazia! Adicione alguns itens antes de ir às compras. 🛑"
        token = secrets.token_urlsafe(12)
        create_session(db, from_number, "interactive_shopping", {"items": all_items, "token": token})
        shop_url = f"{base_url}/shop?s={token}"
        return f"Sessão de compras iniciada! 🛒\n{shop_url}\n\nMarque os itens conforme for comprando. Ao finalizar, pressione 'Compras Finalizadas' no site!"
    texto_ajuda = get_help_text()
    return f"Não entendi o comando.\n\n{texto_ajuda}"


# ---------------------------------------------------------------------------
# Route: POST /webhook  (Twilio)
# ---------------------------------------------------------------------------

def _handle_webhook(event: dict) -> dict:
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    params = parse_qs(body)
    incoming_msg = params.get("Body", [""])[0].strip()
    from_number = params.get("From", ["unknown"])[0]
    base_url = _base_url(event)

    db = SessionLocal()
    try:
        get_or_create_member(db, from_number)

        # Check for active session first
        session = get_active_session(db, from_number)
        if session and session.session_type == "bulk_delete":
            reply = _handle_bulk_delete_response(db, session, incoming_msg)
        elif session and session.session_type == "confirm_add":
            reply = _handle_confirm_add_response(db, session, incoming_msg, from_number, base_url)
        elif session and session.session_type == "confirm_delete":
            reply = _handle_confirm_delete_response(db, session, incoming_msg)
        else:
            command = parse_command(incoming_msg)
            reply = _dispatch(db, command, from_number, base_url)
    finally:
        db.close()

    return _twiml(reply)


# ---------------------------------------------------------------------------
# Route: GET /shop?s=<token>  (web to-do page)
# ---------------------------------------------------------------------------

def _handle_shop_page(event: dict) -> dict:
    token = (event.get("queryStringParameters") or {}).get("s", "")
    if not token:
        return _html("<h2>Link inválido.</h2>", 400)

    db = SessionLocal()
    try:
        session = get_session_by_token(db, token)
        if not session:
            return _html("<h2>Esta sessão de compras expirou ou não existe.</h2>", 404)
        items: list[dict] = session.payload.get("items", [])
    finally:
        db.close()

    # Build grouped item rows
    from categories import CATEGORY_ORDER
    grouped: dict[str, list[dict]] = {}
    for it in items:
        grouped.setdefault(it["category"], []).append(it)

    rows_html = ""
    for cat in CATEGORY_ORDER:
        cat_items = grouped.get(cat)
        if not cat_items:
            continue
        rows_html += f'<div class="category"><h3>{cat}</h3>'
        for it in cat_items:
            rows_html += (
                f'<label class="item">'
                f'<input type="checkbox" name="item" value="{it["id"]}">'
                f' {it["name"].capitalize()} <span class="qty">x{it["qty"]}</span>'
                f'</label>'
            )
        rows_html += "</div>"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lista de Compras</title>
</head>
<body>
<h1>🛒 Lista de Compras</h1>
<form id="shopForm">
  <input type="hidden" name="token" value="{token}">
  {rows_html}
  <button type="submit">Compras Finalizadas ✓</button>
</form>
<p id="msg"></p>
<script>
  document.querySelectorAll('.item').forEach(label => {{
    label.addEventListener('change', () => label.classList.toggle('checked', label.querySelector('input').checked));
  }});
  document.getElementById('shopForm').addEventListener('submit', async e => {{
    e.preventDefault();
    const form = e.target;
    const checked = [...form.querySelectorAll('input[name=item]:checked')].map(i => parseInt(i.value));
    const token = form.querySelector('input[name=token]').value;
    const res = await fetch(window.location.href.replace('/shop', '/shop/finish').split('?')[0], {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{ token, purchased_ids: checked }})
    }});
    const data = await res.json();
    document.getElementById('msg').textContent = data.message || 'Pronto!';
    form.querySelector('button').disabled = true;
  }});
</script>
</body>
</html>"""
    return _html(html)


# ---------------------------------------------------------------------------
# Route: POST /shop/finish
# ---------------------------------------------------------------------------

def _handle_shop_finish(event: dict) -> dict:
    try:
        body = event.get("body", "{}")
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        data = json.loads(body)
        token = data.get("token", "")
        purchased_ids: list[int] = data.get("purchased_ids", [])
    except Exception:
        return _json_resp({"message": "Requisição inválida."}, 400)

    db = SessionLocal()
    try:
        session = get_session_by_token(db, token)
        if not session:
            return _json_resp({"message": "Sessão expirada ou não encontrada."}, 404)

        if purchased_ids:
            deleted = delete_items_by_ids(db, purchased_ids)
        else:
            deleted = 0

        delete_session(db, session)
    finally:
        db.close()

    if deleted:
        return _json_resp({"message": f"Removido(s) {deleted} item(ns). Boas compras!"})
    return _json_resp({"message": "Nenhum item marcado — lista inalterada."})
    
# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def handler(event, context):
    path = event.get("path", "/webhook")
    method = event.get("httpMethod", "POST").upper()

    try:
        if path == "/shop/finish" and method == "POST":
            return _handle_shop_finish(event)
        if path == "/shop" and method == "GET":
            return _handle_shop_page(event)
        # Default: Twilio webhook
        return _handle_webhook(event)
    except Exception as e:
        return _twiml(f"Internal error: {e}")
