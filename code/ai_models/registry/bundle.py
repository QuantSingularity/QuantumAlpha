import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List

from ai_models.core.exceptions import NotFoundError
from ai_models.data.preprocessing import FeatureScaler
from ai_models.models.base import ForecastModel
from ai_models.models.factory import load_model


@dataclass
class LoadedBundle:
    model: ForecastModel
    scaler: FeatureScaler
    meta: Dict[str, Any]

    @property
    def columns(self) -> List[str]:
        return self.meta["columns"]

    @property
    def sequence_length(self) -> int:
        return int(self.meta["sequence_length"])

    @property
    def horizon(self) -> int:
        return int(self.meta["horizon"])


def save_bundle(
    directory: str, model: ForecastModel, scaler: FeatureScaler, meta: Dict[str, Any]
) -> None:
    os.makedirs(directory, exist_ok=True)
    model.save(directory)
    with open(os.path.join(directory, "scaler.json"), "w") as handle:
        json.dump(scaler.to_dict(), handle)
    with open(os.path.join(directory, "meta.json"), "w") as handle:
        json.dump(meta, handle, indent=2, default=float)


def load_bundle(directory: str, kind: str) -> LoadedBundle:
    meta_path = os.path.join(directory, "meta.json")
    scaler_path = os.path.join(directory, "scaler.json")
    if not (os.path.exists(meta_path) and os.path.exists(scaler_path)):
        raise NotFoundError(f"Model artifacts not found: {directory}")
    with open(meta_path) as handle:
        meta = json.load(handle)
    with open(scaler_path) as handle:
        scaler = FeatureScaler.from_dict(json.load(handle))
    model = load_model(
        kind,
        directory,
        meta.get("params", {}),
        len(meta["columns"]),
        int(meta["sequence_length"]),
        int(meta["horizon"]),
    )
    return LoadedBundle(model=model, scaler=scaler, meta=meta)
