from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import ConfigDict  # <-- add this import
from typing import Optional, Dict, Any

class ItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = ""

class ItemRead(BaseModel):
    # tell Pydantic v2 to read from object attributes (ORM)
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    created_at: datetime

# Property Brief schemas
class PropertyCreate(BaseModel):
    address: str = Field(min_length=1, max_length=500)

class PropertyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    normalized_address: str
    raw_address: str
    created_at: datetime
    updated_at: datetime

class SourceDatumRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    property_id: int
    source_name: str
    data: Dict[str, Any]
    created_at: datetime

class BriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    property_id: int
    data: Dict[str, Any]
    completeness_score: int
    created_at: datetime
    updated_at: datetime

class ContributionCreate(BaseModel):
    field: str = Field(min_length=1, max_length=100)
    proposed_value: str = Field(min_length=1, max_length=1000)
    reason: str = Field(min_length=1, max_length=500)
    contributor: str = Field(min_length=1, max_length=100)

class ContributionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    property_id: int
    field: str
    proposed_value: str
    reason: str
    contributor: str
    status: str
    created_at: datetime

class AISummaryRequest(BaseModel):
    prompt_override: Optional[str] = Field(None, max_length=1000)
