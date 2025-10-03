from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
import json

class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    body: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Property(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    normalized_address: str = Field(index=True, unique=True)
    raw_address: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    source_data: list["SourceDatum"] = Relationship(back_populates="property")
    brief: Optional["Brief"] = Relationship(back_populates="property")
    contributions: list["Contribution"] = Relationship(back_populates="property")

class SourceDatum(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    property_id: int = Field(foreign_key="property.id")
    source_name: str  # "county", "listing", "hoa"
    data: str  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    property: Property = Relationship(back_populates="source_data")

class Brief(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    property_id: int = Field(foreign_key="property.id")
    data: str  # JSON string containing the canonical brief
    completeness_score: int = Field(ge=0, le=100)  # 0-100 completeness percentage
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    property: Property = Relationship(back_populates="brief")

class FieldIssue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    brief_id: int = Field(foreign_key="brief.id")
    field_name: str
    conflicting_values: str  # JSON string of conflicting values
    confidence_scores: str  # JSON string of confidence scores per source
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Contribution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    property_id: int = Field(foreign_key="property.id")
    field: str
    proposed_value: str
    reason: str
    contributor: str
    status: str = Field(default="pending")  # "pending", "accepted", "rejected"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    property: Property = Relationship(back_populates="contributions")
