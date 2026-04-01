"""
WSGI entry point for production deployment via gunicorn.
"""

from common.database import cleanup_database, initialize_database
from main import QuantumAlphaApp
from services.trading_engine import trading_engine

_app_instance = QuantumAlphaApp()
application = _app_instance.create_app()

with application.app_context():
    try:
        initialize_database()
        trading_engine.start()
    except Exception as exc:
        import logging

        logging.getLogger(__name__).error("Startup error: %s", exc)

# gunicorn atexit cleanup
import atexit


@atexit.register
def _shutdown():
    trading_engine.stop()
    cleanup_database()
