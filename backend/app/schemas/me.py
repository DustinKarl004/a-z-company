from pydantic import BaseModel, field_validator


class MeOut(BaseModel):
    id: str
    name: str
    email: str
    roles: list[str]
    branch_id: str | None
    branch_name: str | None


class MeBranchUpdate(BaseModel):
    branch_id: str


class MePasswordUpdate(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v
