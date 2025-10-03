from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import ConfigDict  # <-- add this import

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
