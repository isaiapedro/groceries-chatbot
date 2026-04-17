from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class GroceryItem(Base):
    __tablename__ = 'grocery_list'

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(255), nullable=False, unique=True)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    aisle_category = Column(String(100), default='Uncategorized')


class FamilyMember(Base):
    __tablename__ = 'family_members'

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(50), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ShoppingSession(Base):
    __tablename__ = 'shopping_sessions'

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(50), nullable=False, unique=True)
    session_type = Column(String(50), nullable=False)  # 'bulk_delete' | 'interactive_shopping'
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
