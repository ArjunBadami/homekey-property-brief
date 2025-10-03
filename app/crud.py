from typing import List, Optional, Tuple, Dict, Any
from sqlmodel import select
from .models import Item, Property, SourceDatum, Brief, Contribution
from sqlalchemy import func
from .utils import now_utc
import json


def list_items(session, q: Optional[str], page: int, limit: int) -> Tuple[List[Item], int]:
    stmt = select(Item)
    if q:
        q_like = f"%{q.lower()}%"
        # SQLite has no ILIKE; use lower(..) LIKE lower(..)
        stmt = stmt.where(
            func.lower(Item.title).like(q_like) |
            func.lower(Item.body).like(q_like)
        )
    # total count via a subquery
    total = session.exec(
        select(func.count()).select_from(stmt.subquery())
    ).one()

    rows = session.exec(
        stmt.order_by(Item.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
    ).all()
    return rows, total


def get_item(session, item_id: int) -> Optional[Item]:
    return session.get(Item, item_id)

def create_item(session, title: str, body: str) -> Item:
    item = Item(title=title, body=body)
    session.add(item); session.commit(); session.refresh(item)
    return item

def update_item(session, item: Item, title: str, body: str) -> Item:
    item.title, item.body = title, body
    session.add(item); session.commit(); session.refresh(item)
    return item

def delete_item(session, item: Item) -> None:
    session.delete(item); session.commit()

# Property CRUD operations
def get_property_by_address(session, normalized_address: str) -> Optional[Property]:
    stmt = select(Property).where(Property.normalized_address == normalized_address)
    return session.exec(stmt).first()

def create_or_update_property(session, normalized_address: str, raw_address: str) -> Property:
    """Upsert property - create if not exists, update if exists."""
    property = get_property_by_address(session, normalized_address)
    if property:
        property.raw_address = raw_address
        property.updated_at = now_utc()
    else:
        property = Property(normalized_address=normalized_address, raw_address=raw_address)
        session.add(property)
    session.commit()
    session.refresh(property)
    return property

def get_property(session, property_id: int) -> Optional[Property]:
    return session.get(Property, property_id)

# SourceDatum CRUD operations
def create_source_datum(session, property_id: int, source_name: str, data: Dict[str, Any]) -> SourceDatum:
    source_datum = SourceDatum(
        property_id=property_id,
        source_name=source_name,
        data=json.dumps(data)
    )
    session.add(source_datum)
    session.commit()
    session.refresh(source_datum)
    return source_datum

def get_source_data(session, property_id: int) -> List[SourceDatum]:
    stmt = select(SourceDatum).where(SourceDatum.property_id == property_id)
    return session.exec(stmt).all()

# Brief CRUD operations
def create_or_update_brief(session, property_id: int, data: Dict[str, Any], completeness_score: int) -> Brief:
    """Upsert brief - create if not exists, update if exists."""
    stmt = select(Brief).where(Brief.property_id == property_id)
    brief = session.exec(stmt).first()
    
    if brief:
        brief.data = json.dumps(data)
        brief.completeness_score = completeness_score
        brief.updated_at = now_utc()
    else:
        brief = Brief(
            property_id=property_id,
            data=json.dumps(data),
            completeness_score=completeness_score
        )
        session.add(brief)
    
    session.commit()
    session.refresh(brief)
    return brief

def get_brief(session, property_id: int) -> Optional[Brief]:
    stmt = select(Brief).where(Brief.property_id == property_id)
    return session.exec(stmt).first()

# Contribution CRUD operations
def create_contribution(session, property_id: int, field: str, proposed_value: str, reason: str, contributor: str) -> Contribution:
    contribution = Contribution(
        property_id=property_id,
        field=field,
        proposed_value=proposed_value,
        reason=reason,
        contributor=contributor
    )
    session.add(contribution)
    session.commit()
    session.refresh(contribution)
    return contribution

def get_contributions(session, property_id: int) -> List[Contribution]:
    stmt = select(Contribution).where(Contribution.property_id == property_id)
    return session.exec(stmt.order_by(Contribution.created_at.desc())).all()
