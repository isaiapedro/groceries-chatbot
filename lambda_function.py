import base64
import json
import os
import secrets
from urllib.parse import parse_qs

from db import SessionLocal
from crud import (
    add_item, modify_item, delete_item, list_items, get_all_items,
    delete_items_by_ids, clear_all_items,
    get_or_create_member,
    get_active_session, create_session, get_session_by_token,
    update_session_payload, delete_session,
)
from parser import parse_command

HELP_TEXT = (
    "Commands:\n"
    "• list — show all items\n"
    "• add <item> <qty> — add item\n"
    "• remove <item> — remove item\n"
    "• modify <item> <qty> — update qty\n"
    "• going shopping — start shopping session\n"
    "• finished shopping — bulk clear list\n"
    "Or just send '2 apples' to add directly."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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

def _handle_bulk_delete_response(db, session, message: str) -> str:
    """Handle the user's reply to a 'finished shopping' prompt."""
    text = message.strip().lower()
    items: list[dict] = session.payload.get("items", [])

    if text in ("all", "tudo", "everything", "confirm"):
        clear_all_items(db)
        delete_session(db, session)
        return f"Done! Cleared all {len(items)} items from the list."

    # Parse item names from the reply
    keep_names = {w.strip() for w in text.replace(",", " ").split() if w.strip()}
    ids_to_delete = [i["id"] for i in items if i["name"] not in keep_names]
    kept = [i["name"] for i in items if i["name"] in keep_names]

    if ids_to_delete:
        delete_items_by_ids(db, ids_to_delete)

    delete_session(db, session)

    if kept:
        return f"Done! Removed {len(ids_to_delete)} items. Kept: {', '.join(kept)}."
    return f"Done! Removed all {len(ids_to_delete)} items."


# ---------------------------------------------------------------------------
# Normal command dispatch
# ---------------------------------------------------------------------------

def _dispatch(db, command: dict, from_number: str, base_url: str) -> str:
    action = command["action"]
    item = command["item"]
    qty = command["quantity"]

    if action == "list":
        return list_items(db)

    if action == "add":
        if not item:
            return "What do you want to add? Example: 'add milk 2'"
        return add_item(db, item, qty or 1)

    if action == "delete":
        if not item:
            return "What do you want to remove? Example: 'remove milk'"
        return delete_item(db, item)

    if action == "modify":
        if not item or not qty:
            return "Usage: 'modify milk 3'"
        return modify_item(db, item, qty)

    if action == "clear_list":
        all_items = get_all_items(db)
        if not all_items:
            return "The grocery list is already empty."
        names = ", ".join(i["name"].capitalize() for i in all_items)
        create_session(db, from_number, "bulk_delete", {"items": all_items})
        return (
            f"About to delete:\n{names}\n\n"
            "Reply with items you *didn't* get to keep them, "
            "or 'all' to clear everything."
        )

    if action == "start_shopping":
        all_items = get_all_items(db)
        if not all_items:
            return "Your grocery list is empty — nothing to shop for!"
        token = secrets.token_urlsafe(12)
        create_session(db, from_number, "interactive_shopping", {"items": all_items, "token": token})
        shop_url = f"{base_url}/shop?s={token}"
        return f"Here's your shopping list:\n{shop_url}\n\nTick items as you go. When done, press 'Done Shopping'."

    return f"I didn't understand that.\n\n{HELP_TEXT}"


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
        return _html("<h2>Invalid link.</h2>", 400)

    db = SessionLocal()
    try:
        session = get_session_by_token(db, token)
        if not session:
            return _html("<h2>This shopping session has expired or doesn't exist.</h2>", 404)
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
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Shopping List</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; padding: 16px; background: #f9f9f9; }}
  h1 {{ font-size: 1.4rem; margin-bottom: 8px; }}
  .category {{ background: white; border-radius: 10px; padding: 12px 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  h3 {{ font-size: .85rem; text-transform: uppercase; color: #888; margin: 0 0 8px; letter-spacing: .05em; }}
  .item {{ display: flex; align-items: center; gap: 10px; padding: 8px 0; border-bottom: 1px solid #f0f0f0; font-size: 1rem; cursor: pointer; }}
  .item:last-child {{ border-bottom: none; }}
  input[type=checkbox] {{ width: 20px; height: 20px; accent-color: #4caf50; flex-shrink: 0; }}
  .qty {{ color: #aaa; font-size: .85rem; margin-left: auto; }}
  .item.checked {{ text-decoration: line-through; color: #bbb; }}
  button {{ width: 100%; padding: 14px; background: #4caf50; color: white; border: none; border-radius: 10px; font-size: 1.1rem; font-weight: 600; margin-top: 16px; cursor: pointer; }}
  button:active {{ background: #388e3c; }}
  #msg {{ text-align: center; margin-top: 16px; font-size: 1rem; color: #555; }}
</style>
</head>
<body>
<h1>🛒 Shopping List</h1>
<form id="shopForm">
  <input type="hidden" name="token" value="{token}">
  {rows_html}
  <button type="submit">Done Shopping ✓</button>
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
    document.getElementById('msg').textContent = data.message || 'Done!';
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
        return _json_resp({"message": "Bad request."}, 400)

    db = SessionLocal()
    try:
        session = get_session_by_token(db, token)
        if not session:
            return _json_resp({"message": "Session expired or not found."}, 404)

        if purchased_ids:
            deleted = delete_items_by_ids(db, purchased_ids)
        else:
            deleted = 0

        delete_session(db, session)
    finally:
        db.close()

    if deleted:
        return _json_resp({"message": f"Removed {deleted} item(s). Happy shopping!"})
    return _json_resp({"message": "No items marked — list unchanged."})


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
