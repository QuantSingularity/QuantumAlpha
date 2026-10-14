import json
import os
from typing import Any, Dict

import numpy as np
from ai_models.core.exceptions import DependencyError, ValidationError
from ai_models.data.preprocessing import PreparedData
from ai_models.models.base import ForecastModel

_MODEL_FILE = "model.keras"


def load_tensorflow() -> Any:
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise DependencyError(
            "TensorFlow is required for deep learning models", {"install": "tensorflow"}
        ) from exc
    return tf


def _lstm(tf: Any, p: Dict[str, Any], length: int, features: int, horizon: int) -> Any:
    layers = tf.keras.layers
    units = int(p.get("units", 64))
    dropout = float(p.get("dropout", 0.2))
    inputs = tf.keras.Input(shape=(length, features))
    x = layers.LSTM(units, return_sequences=True)(inputs)
    x = layers.Dropout(dropout)(x)
    x = layers.LSTM(max(8, units // 2))(x)
    x = layers.Dropout(dropout)(x)
    x = layers.Dense(32, activation="relu")(x)
    outputs = layers.Dense(horizon)(x)
    return tf.keras.Model(inputs, outputs)


def _gru(tf: Any, p: Dict[str, Any], length: int, features: int, horizon: int) -> Any:
    layers = tf.keras.layers
    units = int(p.get("units", 64))
    dropout = float(p.get("dropout", 0.2))
    inputs = tf.keras.Input(shape=(length, features))
    x = layers.GRU(units, return_sequences=True)(inputs)
    x = layers.Dropout(dropout)(x)
    x = layers.GRU(max(8, units // 2))(x)
    x = layers.Dropout(dropout)(x)
    x = layers.Dense(32, activation="relu")(x)
    outputs = layers.Dense(horizon)(x)
    return tf.keras.Model(inputs, outputs)


def _cnn(tf: Any, p: Dict[str, Any], length: int, features: int, horizon: int) -> Any:
    layers = tf.keras.layers
    filters = int(p.get("filters", 64))
    dropout = float(p.get("dropout", 0.2))
    kernel = max(2, min(int(p.get("kernel_size", 3)), length))
    inputs = tf.keras.Input(shape=(length, features))
    x = layers.Conv1D(filters, kernel, padding="causal", activation="relu")(inputs)
    x = layers.Conv1D(
        filters, kernel, padding="causal", activation="relu", dilation_rate=2
    )(x)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dropout(dropout)(x)
    x = layers.Dense(32, activation="relu")(x)
    outputs = layers.Dense(horizon)(x)
    return tf.keras.Model(inputs, outputs)


def _transformer(
    tf: Any, p: Dict[str, Any], length: int, features: int, horizon: int
) -> Any:
    layers = tf.keras.layers
    d_model = int(p.get("d_model", 64))
    heads = int(p.get("num_heads", 4))
    blocks = int(p.get("num_blocks", 2))
    ff_dim = int(p.get("ff_dim", 128))
    dropout = float(p.get("dropout", 0.1))
    if d_model % heads:
        raise ValidationError("d_model must be divisible by num_heads")
    inputs = tf.keras.Input(shape=(length, features))
    x = layers.Conv1D(d_model, min(3, length), padding="causal", activation="relu")(
        inputs
    )
    for _ in range(blocks):
        attn = layers.MultiHeadAttention(
            num_heads=heads, key_dim=d_model // heads, dropout=dropout
        )(x, x)
        x = layers.LayerNormalization(epsilon=1e-6)(x + layers.Dropout(dropout)(attn))
        ff = layers.Dense(ff_dim, activation="relu")(x)
        ff = layers.Dense(d_model)(layers.Dropout(dropout)(ff))
        x = layers.LayerNormalization(epsilon=1e-6)(x + ff)
    x = layers.GlobalAveragePooling1D()(x)
    x = layers.Dense(32, activation="relu")(x)
    outputs = layers.Dense(horizon)(x)
    return tf.keras.Model(inputs, outputs)


_BUILDERS = {"lstm": _lstm, "gru": _gru, "cnn": _cnn, "transformer": _transformer}


class KerasForecaster(ForecastModel):
    family = "deep"
    arch = ""

    def _compile(self, tf: Any) -> None:
        learning_rate = float(self.params.get("learning_rate", 1e-3))
        optimizer = tf.keras.optimizers.Adam(learning_rate=learning_rate, clipnorm=1.0)
        self.network.compile(
            optimizer=optimizer, loss=tf.keras.losses.Huber(delta=0.05)
        )

    def fit(self, data: PreparedData) -> Dict[str, Any]:
        tf = load_tensorflow()
        seed = int(self.params.get("seed", 42))
        tf.keras.utils.set_random_seed(seed)
        self.network = _BUILDERS[self.arch](
            tf, self.params, data.sequence_length, data.n_features, data.horizon
        )
        self._compile(tf)
        epochs = int(self.params.get("epochs", 50))
        batch_size = int(self.params.get("batch_size", 32))
        patience = int(self.params.get("patience", 8))
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss" if len(data.X_val) else "loss",
                patience=patience,
                restore_best_weights=True,
            ),
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss" if len(data.X_val) else "loss",
                factor=0.5,
                patience=max(2, patience // 2),
            ),
        ]
        validation = (data.X_val, data.y_val) if len(data.X_val) else None
        history = self.network.fit(
            data.X_train,
            data.y_train,
            validation_data=validation,
            epochs=epochs,
            batch_size=batch_size,
            shuffle=False,
            callbacks=callbacks,
            verbose=0,
        )
        self.fitted = True
        losses = history.history.get("loss", [])
        val_losses = history.history.get("val_loss", [])
        return {
            "epochs_run": len(losses),
            "final_loss": float(losses[-1]) if losses else None,
            "final_val_loss": float(val_losses[-1]) if val_losses else None,
            "best_val_loss": float(min(val_losses)) if val_losses else None,
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._ensure_2d(self.network(X, training=False).numpy())

    def mc_predict(self, X: np.ndarray, samples: int = 20) -> np.ndarray:
        runs = [
            self._ensure_2d(self.network(X, training=True).numpy())
            for _ in range(samples)
        ]
        return np.stack(runs)

    def save(self, directory: str) -> None:
        self.network.save(self.artifact_path(directory, _MODEL_FILE))
        with open(self.artifact_path(directory, "network.json"), "w") as handle:
            json.dump({"arch": self.arch}, handle)

    @classmethod
    def load(cls, directory, params, n_features, sequence_length, horizon):
        tf = load_tensorflow()
        path = os.path.join(directory, _MODEL_FILE)
        if not os.path.exists(path):
            raise ValidationError(f"Model artifact missing: {path}")
        model = cls(params, n_features, sequence_length, horizon)
        model.network = tf.keras.models.load_model(path, compile=False)
        model.fitted = True
        return model


class LSTMForecaster(KerasForecaster):
    kind = "lstm"
    arch = "lstm"


class GRUForecaster(KerasForecaster):
    kind = "gru"
    arch = "gru"


class CNNForecaster(KerasForecaster):
    kind = "cnn"
    arch = "cnn"


class TransformerForecaster(KerasForecaster):
    kind = "transformer"
    arch = "transformer"
