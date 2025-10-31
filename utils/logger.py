"""Central logging configuration.

Provides a get_logger(name) function that returns a preconfigured logger:
 - Console handler with colored level names (fallback to plain if colorama missing)
 - Optional rotating file handler (disabled by default; enable via env LOG_FILE)
 - Lazy singleton initialization to avoid duplicate handlers

Usage:
    from utils.logger import get_logger
    log = get_logger(__name__)
    log.info("Starting step")

We keep existing print statements in the codebase (as requested) while adding
structured logs for downstream analysis or CI troubleshooting.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional

_BASE_LOGGER_NAME = "cooking_assistant"
_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_LOG_FILE = os.getenv("LOG_FILE")  # If set, we log to file as well
_MAX_BYTES = int(os.getenv("LOG_FILE_MAX_BYTES", 2_000_000))
_BACKUP_COUNT = int(os.getenv("LOG_FILE_BACKUP_COUNT", 3))

_initialized = False

class _ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": "\x1b[36m",   # Cyan
        "INFO": "\x1b[32m",    # Green
        "WARNING": "\x1b[33m", # Yellow
        "ERROR": "\x1b[31m",   # Red
        "CRITICAL": "\x1b[35m" # Magenta
    }
    RESET = "\x1b[0m"

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        level_color = self.COLORS.get(record.levelname, "")
        prefix = f"{level_color}{record.levelname:<8}{self.RESET}"
        message = super().format(record)
        return f"{prefix} {message}"

def _ensure_initialized() -> None:
    global _initialized
    if _initialized:
        return

    root = logging.getLogger(_BASE_LOGGER_NAME)
    root.setLevel(_LEVEL)
    root.propagate = False  # Avoid double logging via root logger

    # Console handler
    ch = logging.StreamHandler()
    fmt = "%(asctime)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    ch.setFormatter(_ColorFormatter(fmt, datefmt=datefmt))
    root.addHandler(ch)

    # Optional file handler
    if _LOG_FILE:
        fh = RotatingFileHandler(_LOG_FILE, maxBytes=_MAX_BYTES, backupCount=_BACKUP_COUNT)
        ffmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt=datefmt)
        fh.setFormatter(ffmt)
        fh.setLevel(_LEVEL)
        root.addHandler(fh)

    _initialized = True

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a child logger under the base namespace.

    Parameters
    ----------
    name: Optional[str]
        Module name; if omitted returns the base logger.
    """
    _ensure_initialized()
    if not name or name == _BASE_LOGGER_NAME:
        return logging.getLogger(_BASE_LOGGER_NAME)
    return logging.getLogger(f"{_BASE_LOGGER_NAME}.{name}")

__all__ = ["get_logger"]
