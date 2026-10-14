import logging
import os
import sys
import threading

_lock = threading.Lock()
_configured = False


def _configure() -> None:
    global _configured
    with _lock:
        if _configured:
            return
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
        root = logging.getLogger("ai_models")
        root.setLevel(getattr(logging, level, logging.INFO))
        if not root.handlers:
            root.addHandler(handler)
        root.propagate = False
        _configured = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(
        name if name.startswith("ai_models") else f"ai_models.{name}"
    )
