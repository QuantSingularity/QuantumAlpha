from dataclasses import dataclass
from typing import Optional

from ai_models.core.jobs import JobManager
from ai_models.core.settings import Settings, get_settings
from ai_models.data.client import DataServiceClient
from ai_models.inference.ensemble import EnsembleService
from ai_models.inference.predictor import PredictionService
from ai_models.inference.signals import SignalGenerator
from ai_models.monitoring.metrics import MetricsRegistry
from ai_models.monitoring.tracker import PerformanceTracker
from ai_models.persistence.prediction_store import PredictionStore
from ai_models.registry.store import ModelRegistry
from ai_models.rl.service import RLService
from ai_models.training.trainer import Trainer


@dataclass
class Services:
    settings: Settings
    registry: ModelRegistry
    rl_registry: ModelRegistry
    data_client: DataServiceClient
    store: PredictionStore
    predictor: PredictionService
    ensemble: EnsembleService
    signals: SignalGenerator
    tracker: PerformanceTracker
    trainer: Trainer
    rl: RLService
    jobs: JobManager
    metrics: MetricsRegistry


def build_services(
    settings: Optional[Settings] = None,
    data_client: Optional[DataServiceClient] = None,
    store: Optional[PredictionStore] = None,
) -> Services:
    settings = settings or get_settings()
    registry = ModelRegistry(settings.model_dir, "model")
    rl_registry = ModelRegistry(settings.rl_model_dir, "rl_model")
    registry.recover_stuck()
    rl_registry.recover_stuck()
    data_client = data_client or DataServiceClient(
        settings.data_service_url,
        settings.request_timeout,
        settings.request_retries,
        settings.cache_ttl,
        settings.cache_size,
    )
    store = store or PredictionStore(settings.database_url)
    predictor = PredictionService(registry, data_client, store, settings)
    return Services(
        settings=settings,
        registry=registry,
        rl_registry=rl_registry,
        data_client=data_client,
        store=store,
        predictor=predictor,
        ensemble=EnsembleService(predictor),
        signals=SignalGenerator(predictor, data_client, store),
        tracker=PerformanceTracker(registry, data_client, store, predictor),
        trainer=Trainer(registry, data_client, on_trained=predictor.invalidate),
        rl=RLService(rl_registry, data_client, settings),
        jobs=JobManager(settings.max_workers, settings.job_history),
        metrics=MetricsRegistry(),
    )
