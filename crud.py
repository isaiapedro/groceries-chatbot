from models import GroceryItem, FamilyMember


def get_or_create_member(db, phone_number: str) -> FamilyMember:
    member = db.query(FamilyMember).filter(FamilyMember.phone_number == phone_number).first()
    if not member:
        member = FamilyMember(phone_number=phone_number, name=f"Member_{phone_number[-4:]}")
        db.add(member)
        db.commit()
        db.refresh(member)
    return member


def add_item(db, item_name: str, quantity: int = 1) -> str:
    existing = db.query(GroceryItem).filter(GroceryItem.item_name == item_name).first()
    if existing:
        return f"'{item_name}' is already on the list (qty: {existing.quantity}). Use 'modify {item_name} <qty>' to update."
    item = GroceryItem(item_name=item_name, quantity=quantity)
    db.add(item)
    db.commit()
    return f"Added {quantity}x {item_name}."


def modify_item(db, item_name: str, quantity: int) -> str:
    item = db.query(GroceryItem).filter(GroceryItem.item_name == item_name).first()
    if not item:
        return f"'{item_name}' not found. Use 'add {item_name} <qty>' to add it first."
    item.quantity = quantity
    db.commit()
    return f"Updated {item_name} to {quantity}."


def delete_item(db, item_name: str) -> str:
    item = db.query(GroceryItem).filter(GroceryItem.item_name == item_name).first()
    if not item:
        return f"'{item_name}' not found on the list."
    db.delete(item)
    db.commit()
    return f"Removed {item_name} from the list."


def list_items(db) -> str:
    items = db.query(GroceryItem).order_by(GroceryItem.id).all()
    if not items:
        return "The grocery list is empty."
    lines = [f"• {item.item_name.capitalize()}: {item.quantity}" for item in items]
    return "Grocery List:\n" + "\n".join(lines)
