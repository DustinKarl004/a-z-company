from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class StaffCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    branch_id: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class StaffUpdate(BaseModel):
    name: str | None = None
    branch_id: str | None = None
    is_active: bool | None = None
    password: str | None = None


class StaffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: str
    branch_id: str | None
    is_active: bool
    created_at: datetime
