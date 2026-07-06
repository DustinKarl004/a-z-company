from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, verify_password, verify_totp_code
from app.crud.users import get_user_by_email
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = get_user_by_email(db, payload.email)
    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise _INVALID_CREDENTIALS

    if user.totp_secret:
        if not payload.totp_code or not verify_totp_code(user.totp_secret, payload.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Valid authenticator code required",
            )

    token = create_access_token(user_id=user.id, role=user.role, branch_id=user.branch_id)
    return TokenResponse(access_token=token)
