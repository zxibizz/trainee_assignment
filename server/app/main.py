"""FastAPI application entrypoint."""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.controllers import auth_controller, products_controller
from app.db import init_db, reset_db_file
from app.gateways.event_bus_gateway import ProductEventBusGateway
from app.logging_config import setup_logging
from app.repositories.products_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthorizationError, AuthService
from app.services.auth_token_service import AuthTokenService
from app.services.products_service import ProductService

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting up: resetting and seeding the database")
    reset_db_file()
    init_db()

    # Build the object graph once, at startup. Instances live on app.state and
    # are handed to routes via app.dependencies — no module-level singletons.
    user_repository = UserRepository()
    auth_service = AuthService(user_repository)
    token_service = AuthTokenService()
    product_repository = ProductRepository()
    event_bus = ProductEventBusGateway()
    product_service = ProductService(product_repository, auth_service, event_bus)

    app.state.auth_service = auth_service
    app.state.token_service = token_service
    app.state.product_service = product_service
    logger.info("startup complete")
    yield
    logger.info("shutting down")


app = FastAPI(
    title="Products CLI API",
    description="Reference product service for the CLI assignment.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth_controller.router)
app.include_router(products_controller.router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log every request with its method, path, status, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "{method} {path} -> {status} ({elapsed:.1f} ms)",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        elapsed=elapsed_ms,
    )
    return response


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(
    request: Request, exc: AuthorizationError
) -> JSONResponse:
    """Map a local authorization denial to an HTTP 403 response."""
    logger.warning("authorization denied: {}", exc)
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc) or "not authorized"},
    )


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
