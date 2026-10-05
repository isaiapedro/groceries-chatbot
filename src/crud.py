import json
import secrets
from datetime import datetime, timezone, timedelta

from models import GroceryItem, FamilyMember, ShoppingSession
from categories import categorize_item, CATEGORY_ORDER


# ---------------------------------------------------------------------------
# Family members
# ---------------------------------------------------------------------------

def get_or_create_member(db, phone_number: str) -> FamilyMember:
    member = db.query(FamilyMember).filter(FamilyMember.phone_number == phone_number).first()
    if not member:
        member = FamilyMember(phone_number=phone_number, name=f"Member_{phone_number[-4:]}")
        db.add(member)
        db.commit()
        db.refresh(member)
    return member


# ---------------------------------------------------------------------------
# Grocery CRUD
# ---------------------------------------------------------------------------

def add_item(db, item_name: str, quantity: int = 1) -> str:
    existing = db.query(GroceryItem).filter(GroceryItem.item_name == item_name).first()
    if existing:
        return f"'{item_name}' já está na lista (qtd: {existing.quantity}). Use 'modificar {item_name} <qtd>' para atualizar."
    category = categorize_item(item_name)
    item = GroceryItem(item_name=item_name, quantity=quantity, aisle_category=category)
    db.add(item)
    db.commit()
    return f"Adicionado {quantity}x {item_name}."


def modify_item(db, item_name: str, quantity: int) -> str:
    item = db.query(GroceryItem).filter(GroceryItem.item_name == item_name).first()
    if not item:
        return f"'{item_name}' não encontrado. Use 'adicionar {item_name} <qtd>' primeiro."
    item.quantity = quantity
    db.commit()
    return f"Atualizado {item_name} para {quantity}."


def delete_item(db, item_name: str) -> str:
    item = db.query(GroceryItem).filter(GroceryItem.item_name == item_name).first()
    if not item:
        return f"'{item_name}' não encontrado na lista."
    db.delete(item)
    db.commit()
    return f"Removido {item_name} da lista."


def delete_item_by_id(db, item_id: int) -> str:
    item = db.query(GroceryItem).filter(GroceryItem.id == item_id).first()
    if not item:
        return "Item não encontrado."
    name = item.item_name
    db.delete(item)
    db.commit()
    return f"Removido {name} da lista."


def find_items_fuzzy(db, search_term: str) -> list:
    return db.query(GroceryItem).filter(GroceryItem.item_name.ilike(f"%{search_term}%")).all()


def list_items(db) -> str:
    items = db.query(GroceryItem).all()
    if not items:
        return "A lista de compras está vazia."

    grouped: dict[str, list[GroceryItem]] = {}
    for item in items:
        cat = item.aisle_category or "❓ Itens Especiais"
        grouped.setdefault(cat, []).append(item)

    lines = []
    for cat in CATEGORY_ORDER:
        cat_items = grouped.get(cat)
        if not cat_items:
            continue
        lines.append(f"*{cat}*")
        for it in sorted(cat_items, key=lambda x: x.item_name):
            lines.append(f"  • {it.item_name.capitalize()}: {it.quantity}")

    return "\n".join(lines)


def get_all_items(db) -> list[dict]:
    """Return all items as dicts, ordered by category then name."""
    items = db.query(GroceryItem).all()
    result = []
    for cat in CATEGORY_ORDER:
        for item in sorted(
            [i for i in items if (i.aisle_category or "❓ Itens Especiais") == cat],
            key=lambda x: x.item_name,
        ):
            result.append({"id": item.id, "name": item.item_name, "qty": item.quantity, "category": cat})
    return result


def delete_items_by_ids(db, item_ids: list[int]) -> int:
    deleted = db.query(GroceryItem).filter(GroceryItem.id.in_(item_ids)).delete(synchronize_session=False)
    db.commit()
    return deleted


def clear_all_items(db) -> int:
    deleted = db.query(GroceryItem).delete()
    db.commit()
    return deleted


# ---------------------------------------------------------------------------
# Shopping sessions
# ---------------------------------------------------------------------------

def get_active_session(db, phone_number: str) -> ShoppingSession | None:
    now = datetime.now(timezone.utc)
    return (
        db.query(ShoppingSession)
        .filter(
            ShoppingSession.phone_number == phone_number,
            ShoppingSession.expires_at > now,
        )
        .first()
    )


def create_session(db, phone_number: str, session_type: str, payload: dict) -> ShoppingSession:
    # Remove any existing session for this phone
    db.query(ShoppingSession).filter(ShoppingSession.phone_number == phone_number).delete()
    session = ShoppingSession(
        phone_number=phone_number,
        session_type=session_type,
        payload=payload,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=6),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session_by_token(db, token: str) -> ShoppingSession | None:
    now = datetime.now(timezone.utc)
    sessions = (
        db.query(ShoppingSession)
        .filter(ShoppingSession.expires_at > now)
        .all()
    )
    for s in sessions:
        if s.payload.get("token") == token:
            return s
    return None


def update_session_payload(db, session: ShoppingSession, payload: dict):
    session.payload = payload
    db.commit()


def delete_session(db, session: ShoppingSession):
    db.delete(session)
    db.commit()
