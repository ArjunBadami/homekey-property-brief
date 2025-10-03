# app/routers/refresh.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from ..deps import get_session
from ..models import Property
from ..crud import upsert_source_datum  # you added this for SourceDatum
from ..utils import now_utc

# existing adapters + merge helper
from ..adapters.county import fetch as county_fetch
from ..adapters.listing import fetch as listing_fetch
from ..adapters.hoa import fetch as hoa_fetch
from ..brief import merge_sources_for_property

router = APIRouter(tags=["refresh"])

@router.post("/properties/{property_id}/refresh")
def refresh_property(property_id: int, session: Session = Depends(get_session)):
    prop = session.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    normalized = prop.normalized_address
    sources = {
        "county": county_fetch(normalized),
        "listing": listing_fetch(normalized),
        "hoa": hoa_fetch(normalized),
    }
    for name, payload in sources.items():
        if payload:
            upsert_source_datum(session, property_id, name, payload)

    brief, completeness, flags = merge_sources_for_property(session, property_id)
    return {
        "id": property_id,
        "refreshed_at": now_utc().isoformat(),
        "completeness": completeness,
        "flags_count": len(flags) if isinstance(flags, list) else 0,
    }
