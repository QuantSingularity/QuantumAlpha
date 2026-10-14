from ai_models.api.wsgi import app
from ai_models.core.settings import get_settings

__all__ = ["app"]

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=get_settings().port, threaded=True)
