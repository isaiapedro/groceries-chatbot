import base64
from urllib.parse import parse_qs

from db import SessionLocal
from crud import add_item, modify_item, delete_item, list_items, get_or_create_member
from parser import parse_command

HELP_TEXT = (
    "Commands:\n"
    "• list — show all items\n"
    "• add <item> <qty> — add item\n"
    "• remove <item> — remove item\n"
    "• modify <item> <qty> — update qty\n"
    "Or just send '2 apples' to add directly."
)


def _twiml(message: str) -> str:
    safe = message.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'<Message>{safe}</Message>'
        '</Response>'
    )


def _dispatch(db, command: dict) -> str:
    action = command['action']
    item = command['item']
    qty = command['quantity']

    if action == 'list':
        return list_items(db)

    if action == 'add':
        if not item:
            return "What do you want to add? Example: 'add milk 2'"
        return add_item(db, item, qty or 1)

    if action == 'delete':
        if not item:
            return "What do you want to remove? Example: 'remove milk'"
        return delete_item(db, item)

    if action == 'modify':
        if not item or not qty:
            return "Usage: 'modify milk 3'"
        return modify_item(db, item, qty)

    return f"I didn't understand that.\n\n{HELP_TEXT}"


def handler(event, context):
    try:
        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            body = base64.b64decode(body).decode('utf-8')

        params = parse_qs(body)
        incoming_msg = params.get('Body', [''])[0].strip()
        from_number = params.get('From', ['unknown'])[0]

        db = SessionLocal()
        try:
            get_or_create_member(db, from_number)
            command = parse_command(incoming_msg)
            reply = _dispatch(db, command)
        finally:
            db.close()

    except Exception as e:
        reply = f"Internal error: {e}"

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'text/xml'},
        'body': _twiml(reply),
    }
