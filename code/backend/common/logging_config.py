import logging
import sys
from typing import Any


def setup_logging(level: Any = logging.INFO) -> Any:
    """Set up the root logger."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
