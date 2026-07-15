"""Logging configuration.

Call configure_logging() once, at application startup, before any other
module logs anything. Individual modules should just use
logging.getLogger(__name__) as usual.
"""

import logging
import sys

from app.core.config import get_settings


def configure_logging() -> None:
    """Configure the root logger with a single structured stream handler."""
    settings = get_settings()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quiet down noisy third-party loggers without hiding real problems.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
