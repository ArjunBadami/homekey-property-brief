from typing import List, Optional, Tuple
from sqlmodel import select
from .models import Item
from sqlalchemy import func


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
