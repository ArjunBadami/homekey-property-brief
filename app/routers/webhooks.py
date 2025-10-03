# app/routers/webhooks.py
import hmac, hashlib
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from sqlmodel import Session
from ..deps import get_session, engine
from ..models import Property
from ..crud import upsert_source_datum
from ..adapters.county import fetch as county_fetch
from ..adapters.listing import fetch as listing_fetch
from ..adapters.hoa import fetch as hoa_fetch
from ..brief import merge_sources_for_property

router = APIRouter(tags=["webhooks"])
WEBHOOK_SECRET = b"dev-secret"  # document: replace with env var in prod

def _verify_hmac(raw: bytes, sig_hex: str) -> bool:
    mac = hmac.new(WEBHOOK_SECRET, raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, sig_hex or "")

def _refresh_in_background(property_id: int):
    from sqlmodel import Session as _Session  # local import to avoid cycles
    with _Session(engine) as s:
        prop = s.get(Property, property_id)
        if not prop:
            return
        normalized = prop.normalized_address
        for name, fetch in {"county": county_fetch, "listing": listing_fetch, "hoa": hoa_fetch}.items():
            payload = fetch(normalized)
            if payload:
                upsert_source_datum(s, property_id, name, payload)
        merge_sources_for_property(s, property_id)

@router.post("/webhooks/source-update")
async def source_update(request: Request, background: BackgroundTasks, session: Session = Depends(get_session)):
    raw = await request.body()
    sig = request.headers.get("X-Signature", "")
    if not _verify_hmac(raw, sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    property_id = data.get("property_id")
    if not property_id:
        raise HTTPException(status_code=400, detail="Missing property_id")

    background.add_task(_refresh_in_background, int(property_id))
    return {"status": "accepted", "property_id": int(property_id)}
