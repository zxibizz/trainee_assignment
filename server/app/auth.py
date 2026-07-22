"""FastAPI authentication dependency.

The token lifecycle lives in
:class:`app.services.auth_token_service.AuthTokenService`. This module only
wires that logic into FastAPI's request/response cycle.
"""

from fastapi import Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.dependencies import get_token_service
from app.services.auth_token_service import AuthTokenService


def get_current_user(
    response: Response,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        HTTPBearer(auto_error=False)
    ),
    token_service: AuthTokenService = Depends(get_token_service),
) -> str:
    """Validate the access token and surface the remaining request budget on
    every response via ``X-Token-*`` headers."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated"
        )

    subject, usage_headers = token_service.validate_access_token(
        credentials.credentials
    )
    # Expose the budget on the outgoing response so clients can pre-empt refresh.
    response.headers.update(usage_headers)
    return subject
