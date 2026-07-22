"""Auth routes: login and refresh."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_auth_service, get_token_service
from app.schemas import LoginRequest, RefreshRequest, TokenPair
from app.services.auth_service import AuthService
from app.services.auth_token_service import AuthTokenService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
def login(
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    token_service: AuthTokenService = Depends(get_token_service),
) -> TokenPair:
    if not auth_service.authenticate(body.username, body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid username or password",
        )
    return token_service.issue_token_pair(body.username)


@router.post("/refresh", response_model=TokenPair)
def refresh(
    body: RefreshRequest,
    token_service: AuthTokenService = Depends(get_token_service),
) -> TokenPair:
    return token_service.rotate_refresh_token(body.refresh_token)
