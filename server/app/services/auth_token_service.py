"""Access/refresh token lifecycle: issuing, rotation, validation, and the
per-token request budget.

Split out of :class:`app.services.auth_service.AuthService` so that user
credentials and the token machinery are separate concerns.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock

import jwt
from fastapi import HTTPException, status
from loguru import logger

from app.config import settings
from app.schemas import TokenPair


@dataclass
class _AccessTokenState:
    requests: int  # number of authed requests made with this token
    expires_at: datetime  # wall-clock expiry (UTC)


class AuthTokenService:
    """Owns the full access/refresh token lifecycle and request budgeting."""

    def __init__(self) -> None:
        # In-memory state. Resets whenever the server restarts. A single lock
        # guards all of it because sync routes run on uvicorn's threadpool, so
        # these structures are mutated from multiple threads concurrently.
        self._lock = Lock()
        self._access_state: dict[str, _AccessTokenState] = {}  # access jti -> state
        self._active_refresh: dict[str, datetime] = {}  # refresh jti -> expiry (UTC)

    def issue_token_pair(self, username: str) -> TokenPair:
        """Create a fresh access/refresh pair and register their state."""
        access_jti = uuid.uuid4().hex
        refresh_jti = uuid.uuid4().hex

        now = datetime.now(timezone.utc)
        access_expires_at = now + timedelta(seconds=settings.access_token_ttl_seconds)
        refresh_expires_at = now + timedelta(seconds=settings.refresh_token_ttl_seconds)

        access = self._encode(
            {
                "sub": username,
                "jti": access_jti,
                "type": "access",
                "exp": access_expires_at,
            }
        )
        refresh = self._encode(
            {
                "sub": username,
                "jti": refresh_jti,
                "type": "refresh",
                "exp": refresh_expires_at,
            }
        )

        with self._lock:
            self._prune_expired()
            self._access_state[access_jti] = _AccessTokenState(
                requests=0, expires_at=access_expires_at
            )
            self._active_refresh[refresh_jti] = refresh_expires_at
        logger.info("issued token pair for {!r}", username)
        return TokenPair(access_token=access, refresh_token=refresh)

    def rotate_refresh_token(self, refresh_token: str) -> TokenPair:
        """Validate a refresh token and issue a new pair, rotating the jti."""
        try:
            payload = jwt.decode(
                refresh_token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid refresh token",
            )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="not a refresh token",
            )

        jti = payload.get("jti", "")
        with self._lock:
            # Rotate: the old refresh token can no longer be used.
            if self._active_refresh.pop(jti, None) is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="refresh token expired",
                )
        logger.info("rotated refresh token for {!r}", payload["sub"])
        return self.issue_token_pair(payload["sub"])

    def validate_access_token(self, token: str) -> tuple[str, dict[str, str]]:
        """Validate an access token and enforce the request/expiry budget.

        Returns the subject and the ``X-Token-*`` usage headers so the caller
        can surface the remaining budget on the response. Raises
        :class:`HTTPException` (401) when the token is invalid, expired, or has
        exceeded its request budget.
        """
        try:
            payload = jwt.decode(
                token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="access token expired",
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid access token",
            )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="not an access token",
            )

        jti = payload.get("jti", "")
        with self._lock:
            state = self._access_state.get(jti)
            if state is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="access token expired",
                )

            state.requests += 1
            requests_used = state.requests
            expires_at = state.expires_at

        usage_headers = {
            "X-Token-Requests-Used": str(requests_used),
            "X-Token-Requests-Limit": str(settings.max_requests_per_token),
            "X-Token-Expires-At": expires_at.isoformat(),
        }

        if requests_used > settings.max_requests_per_token:
            # Force the client to refresh after too many requests.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="token request limit exceeded, please refresh",
                headers=usage_headers,
            )

        return payload["sub"], usage_headers

    # ---- Internals ----
    def _encode(self, payload: dict) -> str:
        return jwt.encode(
            payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
        )

    def _prune_expired(self) -> None:
        """Drop bookkeeping for access and refresh tokens that have expired.

        Must be called while holding ``self._lock``.
        """
        now = datetime.now(timezone.utc)
        for jti in [j for j, st in self._access_state.items() if st.expires_at <= now]:
            del self._access_state[jti]
        for jti in [j for j, exp in self._active_refresh.items() if exp <= now]:
            del self._active_refresh[jti]
