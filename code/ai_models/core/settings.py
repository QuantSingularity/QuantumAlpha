import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional


def _service_url(url_env: str, host_env: str, port_env: str, default_port: str) -> str:
    url = os.getenv(url_env)
    if url:
        return url.rstrip("/")
    host = os.getenv(host_env, "localhost")
    port = os.getenv(port_env, default_port)
    return f"http://{host}:{port}"


def _database_url() -> Optional[str]:
    url = os.getenv("DATABASE_URL")
    if url:
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        return url
    host = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST")
    if not host:
        return None
    user = os.getenv("POSTGRES_USER") or os.getenv("DB_USERNAME", "postgres")
    password = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD", "postgres")
    port = os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT", "5432")
    name = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME", "quantumalpha")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


@dataclass(frozen=True)
class Settings:
    model_dir: str
    rl_model_dir: str
    data_service_url: str
    database_url: Optional[str]
    api_key: Optional[str]
    request_timeout: float
    request_retries: int
    max_workers: int
    job_history: int
    cache_ttl: int
    cache_size: int
    port: int
    min_history_rows: int
    cors_origins: tuple
    max_training_epochs: int
    max_rl_timesteps: int

    @classmethod
    def from_env(cls) -> "Settings":
        model_dir = (
            os.getenv("AI_MODEL_DIR") or os.getenv("MODEL_REGISTRY_PATH") or "models"
        )
        if model_dir.startswith("/path/to"):
            model_dir = "models"
        origins = tuple(
            o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
        )
        return cls(
            model_dir=model_dir,
            rl_model_dir=os.getenv("AI_RL_MODEL_DIR", os.path.join(model_dir, "rl")),
            data_service_url=_service_url(
                "DATA_SERVICE_URL", "DATA_SERVICE_HOST", "DATA_SERVICE_PORT", "8081"
            ),
            database_url=_database_url(),
            api_key=os.getenv("AI_ENGINE_API_KEY") or None,
            request_timeout=float(os.getenv("AI_REQUEST_TIMEOUT", "30")),
            request_retries=int(os.getenv("AI_REQUEST_RETRIES", "2")),
            max_workers=int(os.getenv("AI_MAX_WORKERS", "2")),
            job_history=int(os.getenv("AI_JOB_HISTORY", "200")),
            cache_ttl=int(os.getenv("AI_CACHE_TTL", "60")),
            cache_size=int(os.getenv("AI_CACHE_SIZE", "256")),
            port=int(os.getenv("PORT") or os.getenv("AI_ENGINE_PORT", "8082")),
            min_history_rows=int(os.getenv("AI_MIN_HISTORY_ROWS", "80")),
            cors_origins=origins or ("*",),
            max_training_epochs=int(os.getenv("AI_MAX_EPOCHS", "500")),
            max_rl_timesteps=int(os.getenv("AI_MAX_RL_TIMESTEPS", "2000000")),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()


def reset_settings() -> None:
    get_settings.cache_clear()
