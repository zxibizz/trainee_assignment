"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Auth
    jwt_secret: str = "products-cli-challenge-secret-do-not-use-in-prod"
    jwt_algorithm: str = "HS256"

    # Number of authenticated requests allowed per access token before it
    # must be refreshed. The CLI is expected to handle the resulting 401.
    max_requests_per_token: int = 20

    # How long (seconds) an access token stays valid before it expires and the
    # CLI must refresh. Enforced alongside `max_requests_per_token`.
    access_token_ttl_seconds: int = 60

    # How long (seconds) a refresh token stays valid before it must be replaced
    # by logging in again. Refresh tokens are rotated on every use.
    refresh_token_ttl_seconds: int = 3600

    # Latency (seconds) of publishing a mutation to the downstream event bus.
    # Only writes (create, update, delete) publish, so writes pay this cost.
    downstream_event_bus_latency_seconds: float = 0.4

    # Database file (relative to the server working directory).
    database_path: str = "products.db"

    # Minimum level emitted by the application logger (loguru).
    log_level: str = "INFO"


settings = Settings()
