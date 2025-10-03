from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional, Dict, Any
from sqlmodel import SQLModel
from .schemas import ItemCreate, ItemRead
from .models import Item
from .deps import get_session, engine
from .crud import list_items, get_item, create_item, update_item, delete_item

router = APIRouter()

@router.on_event("startup")
def init_db():
    SQLModel.metadata.create_all(engine)

@router.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}

@router.get("/items", response_model=dict)
def list_items_api(
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    session=Depends(get_session),
):
    rows, total = list_items(session, q, page, limit)
    data = [ItemRead.model_validate(r).model_dump() for r in rows]
    return {"data": data, "meta": {"page": page, "limit": limit, "total": total}}

@router.get("/items/{item_id}", response_model=ItemRead)
def get_item_api(item_id: int, session=Depends(get_session)):
    item = get_item(session, item_id)
    if not item:
        raise HTTPException(404, "item not found")
    return ItemRead.model_validate(item)

@router.post("/items", response_model=ItemRead, status_code=201)
def create_item_api(payload: ItemCreate, session=Depends(get_session)):
    item = create_item(session, payload.title, payload.body)
    return ItemRead.model_validate(item)

@router.put("/items/{item_id}", response_model=ItemRead)
def update_item_api(item_id: int, payload: ItemCreate, session=Depends(get_session)):
    item = get_item(session, item_id)
    if not item:
        raise HTTPException(404, "item not found")
    return update_item(session, item, payload.title, payload.body)

@router.delete("/items/{item_id}", status_code=204)
def delete_item_api(item_id: int, session=Depends(get_session)):
    item = get_item(session, item_id)
    if not item:
        raise HTTPException(404, "item not found")
    delete_item(session, item)
    return
