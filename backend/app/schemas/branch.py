from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BranchCreate(BaseModel):
    name: str


class BranchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: datetime
