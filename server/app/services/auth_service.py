"""Auth service: authentication and the local authorization check.

The user credential store lives in
:class:`app.repositories.user_repository.UserRepository`. Token issuing/refresh
and the per-token request budget live in
:class:`app.services.auth_token_service.AuthTokenService`. This class stays
focused on *who the user is* and *whether they may act*.
"""

from loguru import logger
from passlib.context import CryptContext

from app.repositories.user_repository import UserRepository
from app.schemas import UserRole

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Privileged actions that only users holding the ADMIN role may perform.
_ADMIN_ONLY_ACTIONS = frozenset({"products:delete"})


class AuthorizationError(Exception):
    """Raised when a subject is not entitled to perform an action."""


class AuthService:
    """Authenticates users and performs the local authorization check."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    # ---- Authentication ----
    def authenticate(self, username: str, password: str) -> bool:
        hashed = self._users.get_password_hash(username)
        ok = bool(hashed and _pwd.verify(password, hashed))
        if ok:
            logger.info("authentication succeeded for {!r}", username)
        else:
            logger.warning("authentication failed for {!r}", username)
        return ok

    # ---- Authorization ----
    def authorize(self, subject: str, action: str) -> None:
        """Confirm that ``subject`` may perform ``action``."""
        if action in _ADMIN_ONLY_ACTIONS:
            user = self._users.get_user(subject)
            if user is None or user.role != UserRole.ADMIN:
                logger.warning(
                    "authorization denied: {!r} may not perform {!r}", subject, action
                )
                raise AuthorizationError(
                    f"'{subject}' is not entitled to perform '{action}'"
                )
