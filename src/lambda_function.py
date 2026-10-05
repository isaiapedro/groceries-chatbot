import base64
import hashlib
import hmac
import json
import os
import secrets
from difflib import SequenceMatcher
from urllib.request import urlopen, Request
from urllib.error import HTTPError

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
    "apagar tudo": "limpa a lista inteira de uma vez",
    "terminei": "remove itens selecionados (você escolhe o que manter)",
    "vou fazer compras": "inicia a sessão de compras interativa",
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


def find_similar_keyword(item_name: str, threshold: float = 0.8) -> str | None:
    from categories import _KEYWORD_TO_CATEGORY
    name_lower = item_name.strip().lower()
    best_match = None
    best_ratio = threshold
    for keyword in _KEYWORD_TO_CATEGORY:
        ratio = SequenceMatcher(None, name_lower, keyword).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = keyword
    return best_match


def _base_url(event: dict) -> str:
    host = event.get("headers", {}).get("Host", "")
    stage = event.get("requestContext", {}).get("stage", "prod")
    return f"https://{host}/{stage}"


WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("META_PHONE_NUMBER_ID", "")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "")
META_APP_SECRET = os.environ.get("META_APP_SECRET", "")


def _send_whatsapp(to: str, message: str) -> None:
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    payload = json.dumps({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    }).encode()
    req = Request(url, data=payload, headers={
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    })
    try:
        urlopen(req)
    except HTTPError as e:
        raise RuntimeError(f"Meta API error {e.code}: {e.read().decode()}") from e


def _ok() -> dict:
    return {"statusCode": 200, "headers": {"Content-Type": "text/plain"}, "body": "OK"}


def _text(body: str, status: int) -> dict:
    return {"statusCode": status, "headers": {"Content-Type": "text/plain"}, "body": body}


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
    """Handle the user's reply to a confirmation prompt (similar word or ❓ Itens Especiais)."""
    text = message.strip().lower()
    item = session.payload.get("item")
    qty = session.payload.get("qty", 1)
    similar = session.payload.get("similar")  # present when a similar known word was found

    delete_session(db, session)

    if text in ("sim", "s", "confirmar", "confirma", "ok"):
        # If we suggested a similar word, "sim" → use the known word
        target = similar if similar else item
        return add_item(db, target, qty)

    # Explicit negative: show help
    if text in ("não", "nao", "n", "cancelar", "nope"):
        if similar:
            # User rejected the suggestion → add original to ❓ Itens Especiais
            return add_item(db, item, qty)
        return (
            f"Ok, '*{item}*' não foi adicionado.\n\n"
            + get_help_text()
        )

    # Recognised command → execute it directly
    command = parse_command(message)
    if command["action"] not in ("unknown",):
        return _dispatch(db, command, from_number, base_url)

    # Unrecognised input → inform and show commands
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
            similar = find_similar_keyword(item)
            if similar:
                create_session(db, from_number, "confirm_add", {"item": item, "qty": qty or 1, "similar": similar})
                return (
                    f"Você quis dizer '*{similar}*'?\n"
                    f"Responda *sim* para adicionar _{similar}_ ou *não* para adicionar _{item}_ em Itens Especiais."
                )
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

    if action == "delete_all":
        all_items = get_all_items(db)
        if not all_items:
            return "A lista já está vazia! ✨"
        clear_all_items(db)
        return f"Pronto! {len(all_items)} item(ns) removido(s). Lista limpa! 🗑️"

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
# Route: GET /webhook  (Meta verification challenge)
# ---------------------------------------------------------------------------

def _handle_webhook_verify(event: dict) -> dict:
    params = event.get("queryStringParameters") or {}
    mode = params.get("hub.mode", "")
    token = params.get("hub.verify_token", "")
    challenge = params.get("hub.challenge", "")

    if VERIFY_TOKEN and mode == "subscribe" and hmac.compare_digest(token, VERIFY_TOKEN):
        return {"statusCode": 200, "headers": {"Content-Type": "text/plain"}, "body": challenge}
    return {"statusCode": 403, "headers": {"Content-Type": "text/plain"}, "body": "Forbidden"}


# ---------------------------------------------------------------------------
# Route: POST /webhook  (Meta incoming messages)
# ---------------------------------------------------------------------------

def _get_request_body(event: dict) -> bytes | None:
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        try:
            return base64.b64decode(body, validate=True)
        except (TypeError, ValueError):
            return None
    if not isinstance(body, str):
        return None
    return body.encode("utf-8")


def _has_valid_meta_signature(event: dict, raw_body: bytes) -> bool:
    """Validate Meta's SHA-256 webhook signature before parsing any payload."""
    headers = event.get("headers") or {}
    signature = next(
        (value for key, value in headers.items() if key.lower() == "x-hub-signature-256"),
        "",
    )
    if not META_APP_SECRET or not isinstance(signature, str):
        return False
    expected = "sha256=" + hmac.new(
        META_APP_SECRET.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


def _handle_webhook(event: dict) -> dict:
    raw_body = _get_request_body(event)
    if raw_body is None:
        print("webhook_rejected reason=invalid_body_encoding")
        return _text("Bad Request", 400)
    if not _has_valid_meta_signature(event, raw_body):
        print("webhook_rejected reason=invalid_signature")
        return _text("Unauthorized", 401)

    try:
        data = json.loads(raw_body)
    except (TypeError, ValueError, UnicodeDecodeError):
        print("webhook_rejected reason=invalid_json")
        return _text("Bad Request", 400)

    # Navigate Meta's payload structure
    try:
        entry = data["entry"][0]
        change = entry["changes"][0]["value"]
        msg_obj = change["messages"][0]
        incoming_msg = msg_obj["text"]["body"].strip()
        from_number = msg_obj["from"]  # e.g. "5511999999999"
    except (KeyError, IndexError):
        # Status updates, read receipts, etc. — acknowledge and ignore
        print("webhook_ignored reason=no_supported_message")
        return _ok()

    base_url = _base_url(event)

    db = SessionLocal()
    try:
        get_or_create_member(db, from_number)

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

    _send_whatsapp(from_number, reply)
    return _ok()


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
                f'<span>{it["name"].capitalize()}</span>'
                f'<span class="qty">x{it["qty"]}</span>'
                f'</label>'
            )
        rows_html += "</div>"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lista de Compras</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f2f5;padding:16px;max-width:600px;margin:0 auto}}
  h1{{font-size:1.4rem;margin-bottom:16px;color:#222}}
  .category{{background:#fff;border-radius:12px;padding:12px 16px;margin-bottom:12px;box-shadow:0 1px 4px rgba(0,0,0,.08)}}
  .category h3{{font-size:.95rem;color:#555;margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #eee}}
  .item{{display:flex;align-items:center;gap:10px;padding:9px 4px;cursor:pointer;font-size:1rem;color:#333;border-radius:6px;transition:background .12s;width:100%}}
  .item:hover{{background:#f7f7f7}}
  .item input[type=checkbox]{{width:18px;height:18px;cursor:pointer;accent-color:#4caf50;flex-shrink:0}}
  .item.checked span:first-of-type{{text-decoration:line-through;color:#aaa}}
  .qty{{margin-left:auto;font-size:.8rem;color:#999;white-space:nowrap}}
  button[type=submit]{{display:block;width:100%;padding:14px;background:#4caf50;color:#fff;border:none;border-radius:10px;font-size:1rem;font-weight:600;cursor:pointer;margin-top:16px}}
  button[type=submit]:hover{{background:#43a047}}
  button[type=submit]:disabled{{background:#bbb;cursor:not-allowed}}
  #msg{{text-align:center;margin-top:12px;color:#555;font-size:.9rem}}
</style>
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
    print(f"request path={path!r} method={method!r}")

    try:
        if path == "/shop/finish" and method == "POST":
            return _handle_shop_finish(event)
        if path == "/shop" and method == "GET":
            return _handle_shop_page(event)
        if path == "/webhook" and method == "GET":
            return _handle_webhook_verify(event)
        if path == "/webhook" and method == "POST":
            return _handle_webhook(event)
        return {"statusCode": 404, "body": "Not found"}
    except Exception as error:
        # Do not expose event bodies, phone numbers, tokens, or exception details.
        print(f"request_failed path={path!r} error_type={type(error).__name__}")
        return _text("Internal Server Error", 500)
