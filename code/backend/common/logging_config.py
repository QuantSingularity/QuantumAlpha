import logging
import sys


def setup_logging(level: object = logging.INFO) -> None:
    """Set up the root logger."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
