from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

STAFF_ROLES = {"staff", "delivery"}


def _validate_roles(v: list[str]) -> list[str]:
    if not v:
        raise ValueError("at least one role is required")
    cleaned = sorted(set(v))
    invalid = [r for r in cleaned if r not in STAFF_ROLES]
    if invalid:
        raise ValueError(f"invalid role(s): {', '.join(invalid)}")
    return cleaned


class StaffCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    branch_id: str | None = None
    roles: list[str] = ["staff"]

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v

    @field_validator("roles")
    @classmethod
    def roles_valid(cls, v: list[str]) -> list[str]:
        return _validate_roles(v)


class StaffUpdate(BaseModel):
    name: str | None = None
    branch_id: str | None = None
    is_active: bool | None = None
    password: str | None = None
    roles: list[str] | None = None

    @field_validator("roles")
    @classmethod
    def roles_valid(cls, v: list[str] | None) -> list[str] | None:
        return _validate_roles(v) if v is not None else v


class StaffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    role: str
    roles: list[str]
    branch_id: str | None
    is_active: bool
    created_at: datetime
