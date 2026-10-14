import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import numpy as np
from ai_models.data.preprocessing import PreparedData


class ForecastModel(ABC):
    kind: str = ""
    family: str = ""

    def __init__(
        self,
        params: Optional[Dict[str, Any]] = None,
        n_features: int = 0,
        sequence_length: int = 0,
        horizon: int = 1,
    ) -> None:
        self.params = dict(params or {})
        self.n_features = n_features
        self.sequence_length = sequence_length
        self.horizon = horizon
        self.fitted = False

    @abstractmethod
    def fit(self, data: PreparedData) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    @abstractmethod
    def save(self, directory: str) -> None:
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def load(
        cls,
        directory: str,
        params: Dict[str, Any],
        n_features: int,
        sequence_length: int,
        horizon: int,
    ) -> "ForecastModel":
        raise NotImplementedError

    def artifact_path(self, directory: str, name: str) -> str:
        os.makedirs(directory, exist_ok=True)
        return os.path.join(directory, name)

    def _ensure_2d(self, predictions: np.ndarray) -> np.ndarray:
        predictions = np.asarray(predictions, dtype=np.float64)
        if predictions.ndim == 1:
            predictions = predictions.reshape(-1, 1)
        return predictions
