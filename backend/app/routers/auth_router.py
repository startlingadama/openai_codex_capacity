from fastapi import APIRouter, Depends, Header

from backend.app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from backend.app.services.auth_service import current_user, login_user, logout_user, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest):
    return register_user(payload.username, payload.password, payload.role)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, authorization: str | None = Header(default=None)):
    rotate_token = None
    if authorization and authorization.startswith("Bearer "):
        rotate_token = authorization.split(" ", 1)[1].strip()
    return login_user(payload.username, payload.password, rotate_token)


@router.post("/logout")
def logout(user=Depends(current_user)):
    logout_user(user["token"])
    return {"status": "logged_out"}
