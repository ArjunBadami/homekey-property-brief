from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional, Dict, Any
from sqlmodel import SQLModel
from .schemas import (
    ItemCreate, ItemRead, PropertyCreate, PropertyRead, SourceDatumRead, 
    BriefRead, ContributionCreate, ContributionRead, AISummaryRequest
)
from .models import Item
from .deps import get_session, engine
from .crud import (
    list_items, get_item, create_item, update_item, delete_item,
    get_property_by_address, create_or_update_property, get_property,
    upsert_source_datum, get_source_data, create_or_update_brief, get_brief,
    create_contribution, get_contributions
)
from .utils import normalize_address, merge_source_data, calculate_completeness_score, call_llm_topics
from .adapters.county import get_county_data
from .adapters.listing import get_listing_data
from .adapters.hoa import get_hoa_data
import json

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

# Property Brief endpoints

@router.post("/properties/ingest", response_model=PropertyRead, status_code=201)
def ingest_property(payload: PropertyCreate, session=Depends(get_session)):
    """
    Ingest property data from all sources and create/update brief.
    """
    # Normalize address
    normalized_addr = normalize_address(payload.address)
    
    # Upsert property
    property = create_or_update_property(session, normalized_addr, payload.address)
    
    # Fetch data from all adapters
    sources = {}
    adapters = [
        ("county", get_county_data),
        ("listing", get_listing_data), 
        ("hoa", get_hoa_data)
    ]
    
    for source_name, adapter_func in adapters:
        data = adapter_func(normalized_addr)
        if data:
            sources[source_name] = data
            # Upsert source datum (update if exists, create if not)
            upsert_source_datum(session, property.id, source_name, data)
    
    # Merge data and create brief
    if sources:
        merged_data = merge_source_data(sources)
        completeness_score = calculate_completeness_score(merged_data)
        create_or_update_brief(session, property.id, merged_data, completeness_score)
    
    return PropertyRead.model_validate(property)

@router.get("/properties/{property_id}/sources", response_model=list[SourceDatumRead])
def get_property_sources(property_id: int, session=Depends(get_session)):
    """Get all source data for a property."""
    property = get_property(session, property_id)
    if not property:
        raise HTTPException(404, "Property not found")
    
    source_data = get_source_data(session, property_id)
    result = []
    for datum in source_data:
        # Parse JSON data before validation
        datum_dict = datum.model_dump()
        datum_dict['data'] = json.loads(datum.data)
        parsed_data = SourceDatumRead.model_validate(datum_dict)
        result.append(parsed_data)
    
    return result

@router.get("/properties/{property_id}/brief", response_model=BriefRead)
def get_property_brief(property_id: int, session=Depends(get_session)):
    """Get the property brief."""
    property = get_property(session, property_id)
    if not property:
        raise HTTPException(404, "Property not found")
    
    brief = get_brief(session, property_id)
    if not brief:
        raise HTTPException(404, "Brief not found for this property")
    
    # Parse JSON data before validation
    brief_dict = brief.model_dump()
    brief_dict['data'] = json.loads(brief.data)
    result = BriefRead.model_validate(brief_dict)
    return result

@router.post("/properties/{property_id}/contributions", response_model=ContributionRead, status_code=201)
def create_property_contribution(
    property_id: int, 
    payload: ContributionCreate, 
    session=Depends(get_session)
):
    """Create a contribution for a property."""
    property = get_property(session, property_id)
    if not property:
        raise HTTPException(404, "Property not found")
    
    contribution = create_contribution(
        session, property_id, payload.field, payload.proposed_value, 
        payload.reason, payload.contributor
    )
    return ContributionRead.model_validate(contribution)

@router.get("/properties/{property_id}/contributions", response_model=list[ContributionRead])
def get_property_contributions(property_id: int, session=Depends(get_session)):
    """Get all contributions for a property."""
    property = get_property(session, property_id)
    if not property:
        raise HTTPException(404, "Property not found")
    
    contributions = get_contributions(session, property_id)
    return [ContributionRead.model_validate(c) for c in contributions]

@router.post("/properties/{property_id}/ai_summary")
def get_ai_summary(
    property_id: int,
    payload: AISummaryRequest,
    session=Depends(get_session)
):
    """Generate AI summary for property using call_llm_topics function."""
    property = get_property(session, property_id)
    if not property:
        raise HTTPException(404, "Property not found")
    
    brief = get_brief(session, property_id)
    if not brief:
        raise HTTPException(404, "Brief not found for this property")
    
    brief_data = json.loads(brief.data)
    
    # Get contributions for this property
    contributions = get_contributions(session, property_id)
    
    # Build the prompt with brief data and contributions
    prompt_parts = ["Property Brief Data:"]
    prompt_parts.append(json.dumps(brief_data, indent=2))
    
    if contributions:
        prompt_parts.append("\nUser Contributions:")
        for contrib in contributions:
            prompt_parts.append(f"- Field: {contrib.field}, Proposed Value: {contrib.proposed_value}, Reason: {contrib.reason}, Contributor: {contrib.contributor}")
    
    prompt = payload.prompt_override or "\n".join(prompt_parts)
    
    try:
        # Use the call_llm_topics function
        summary = call_llm_topics(prompt)
        
        return {
            "summary": summary,
            "source": "openai",
            "completeness_score": brief.completeness_score
        }
        
    except requests.exceptions.RequestException as e:
        # Network/HTTP related errors
        error_details = {
            "error_type": "request_exception",
            "error_message": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None,
            "response_text": getattr(e.response, 'text', None) if hasattr(e, 'response') else None
        }
        
        return _generate_fallback_summary(brief_data, contributions, error_details)
        
    except KeyError as e:
        # Missing key in response
        error_details = {
            "error_type": "key_error",
            "error_message": f"Missing key in OpenAI response: {str(e)}",
            "expected_keys": ["choices", "message", "content"]
        }
        
        return _generate_fallback_summary(brief_data, contributions, error_details)
        
    except json.JSONDecodeError as e:
        # JSON parsing error
        error_details = {
            "error_type": "json_decode_error",
            "error_message": f"Failed to parse OpenAI response JSON: {str(e)}"
        }
        
        return _generate_fallback_summary(brief_data, contributions, error_details)
        
    except Exception as e:
        # Any other unexpected errors
        error_details = {
            "error_type": "unexpected_error",
            "error_message": str(e),
            "error_class": type(e).__name__
        }
        
        return _generate_fallback_summary(brief_data, contributions, error_details)

def _generate_fallback_summary(brief_data: dict, contributions: list, error_details: dict) -> dict:
    """Generate rule-based fallback summary with error details"""
    summary_parts = []
    
    if brief_data.get('address'):
        summary_parts.append(f"This {brief_data.get('property_type', 'property')} at {brief_data['address']}")
    
    if brief_data.get('square_feet') and brief_data.get('bedrooms') and brief_data.get('bathrooms'):
        summary_parts.append(f"features {brief_data['square_feet']} sq ft with {brief_data['bedrooms']} bedrooms and {brief_data['bathrooms']} bathrooms")
    
    if brief_data.get('year_built'):
        summary_parts.append(f"built in {brief_data['year_built']}")
    
    if brief_data.get('hoa_fee'):
        summary_parts.append(f"with ${brief_data['hoa_fee']} monthly HOA fee")
    
    # Add contributions if any
    if contributions:
        contrib_text = "User contributions: " + ", ".join([f"{c.field}={c.proposed_value}" for c in contributions])
        summary_parts.append(contrib_text)
    
    summary = ". ".join(summary_parts) + "."
    
    return {
        "summary": summary,
        "source": "rule_based_fallback",
        "error_details": error_details,
        "completeness_score": brief.completeness_score
    }
