"""Centralised loguru logging configuration.

Loguru is the single sink for the whole application. The standard library
``logging`` module (used by uvicorn, starlette, passlib, ...) is intercepted and
forwarded to loguru so every log line shares one format and destination.
"""

import logging
import sys
from types import FrameType

from loguru import logger

from app.config import settings

# stdlib loggers whose records should be routed through loguru.
_INTERCEPTED_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "fastapi",
)


class InterceptHandler(logging.Handler):
    """Forward standard-library logging records to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        # Map the stdlib level name onto loguru's, falling back to the number.
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Walk back to the frame that issued the log so loguru reports the real
        # call site rather than this handler.
        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame is not None and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """Make loguru the sole sink and route stdlib logging through it.

    Idempotent: safe to call more than once (e.g. under the test client).
    """
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        backtrace=False,
        diagnose=False,
    )

    # Route the root logger and the noisy third-party loggers into loguru.
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in _INTERCEPTED_LOGGERS:
        intercepted = logging.getLogger(name)
        intercepted.handlers = [InterceptHandler()]
        intercepted.propagate = False
