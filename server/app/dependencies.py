"""FastAPI dependency providers.

The object graph is built once at startup (see :func:`app.main.lifespan`) and
stored on ``app.state``. These providers expose those instances to routes, so
nothing depends on a module-level singleton.
"""

from fastapi import Request

from app.services.auth_service import AuthService
from app.services.auth_token_service import AuthTokenService
from app.services.products_service import ProductService


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_token_service(request: Request) -> AuthTokenService:
    return request.app.state.token_service


def get_product_service(request: Request) -> ProductService:
    return request.app.state.product_service
