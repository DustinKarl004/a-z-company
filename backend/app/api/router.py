from fastapi import APIRouter

from app.api.routes import auth, branches, staff

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(branches.router)
api_router.include_router(staff.router)
