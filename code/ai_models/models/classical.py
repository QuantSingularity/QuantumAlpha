import os
from typing import Any, Dict

import joblib
import numpy as np
from ai_models.core.exceptions import ValidationError
from ai_models.data.preprocessing import PreparedData, to_tabular
from ai_models.models.base import ForecastModel
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.multioutput import MultiOutputRegressor

_ESTIMATOR_FILE = "estimator.joblib"


class ClassicalForecaster(ForecastModel):
    family = "classical"

    def _build(self) -> Any:
        raise NotImplementedError

    def fit(self, data: PreparedData) -> Dict[str, Any]:
        self.estimator = self._build()
        self.estimator.fit(to_tabular(data.X_train), data.y_train)
        self.fitted = True
        return {"train_samples": int(len(data.X_train))}

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._ensure_2d(self.estimator.predict(to_tabular(X)))

    def save(self, directory: str) -> None:
        joblib.dump(self.estimator, self.artifact_path(directory, _ESTIMATOR_FILE))

    @classmethod
    def load(cls, directory, params, n_features, sequence_length, horizon):
        model = cls(params, n_features, sequence_length, horizon)
        path = os.path.join(directory, _ESTIMATOR_FILE)
        if not os.path.exists(path):
            raise ValidationError(f"Model artifact missing: {path}")
        model.estimator = joblib.load(path)
        model.fitted = True
        return model


class RidgeForecaster(ClassicalForecaster):
    kind = "ridge"

    def _build(self) -> Any:
        return Ridge(alpha=float(self.params.get("alpha", 1.0)))


class RandomForestForecaster(ClassicalForecaster):
    kind = "random_forest"

    def _build(self) -> Any:
        return RandomForestRegressor(
            n_estimators=int(self.params.get("n_estimators", 200)),
            max_depth=self.params.get("max_depth", 8),
            min_samples_leaf=int(self.params.get("min_samples_leaf", 3)),
            n_jobs=int(self.params.get("n_jobs", 1)),
            random_state=int(self.params.get("seed", 42)),
        )


class GradientBoostingForecaster(ClassicalForecaster):
    kind = "gradient_boosting"

    def _build(self) -> Any:
        base = GradientBoostingRegressor(
            n_estimators=int(self.params.get("n_estimators", 150)),
            learning_rate=float(self.params.get("learning_rate", 0.05)),
            max_depth=int(self.params.get("max_depth", 3)),
            subsample=float(self.params.get("subsample", 0.8)),
            random_state=int(self.params.get("seed", 42)),
        )
        return MultiOutputRegressor(base)
