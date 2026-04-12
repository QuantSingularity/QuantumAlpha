"""
Prediction service for QuantumAlpha AI Engine.
Handles predictions and signal generation.
"""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common import NotFoundError, ServiceError, ValidationError, setup_logger

logger = setup_logger("prediction_service", logging.INFO)


class PredictionService:
    """Prediction service"""

    def __init__(
        self, config_manager: Any, db_manager: Any, model_manager: Any
    ) -> None:
        """Initialize prediction service

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
            model_manager: Model manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.model_manager = model_manager
        self.data_service_url = f"http://{config_manager.get('services.data_service.host')}:{config_manager.get('services.data_service.port')}"
        logger.info("Prediction service initialized")

    def generate_prediction(
        self,
        model_id: str,
        symbol: str,
        timeframe: str = "1d",
        period: str = "1mo",
        horizon: int = 5,
    ) -> Dict[str, Any]:
        """Generate prediction

        Args:
            model_id: Model ID
            symbol: Symbol
            timeframe: Timeframe
            period: Period
            horizon: Prediction horizon

        Returns:
            Prediction result

        Raises:
            NotFoundError: If model is not found
            ValidationError: If parameters are invalid
            ServiceError: If there is an error generating prediction
        """
        try:
            logger.info(f"Generating prediction for {symbol} using model {model_id}")
            if not model_id:
                raise ValidationError("Model ID is required")
            if not symbol:
                raise ValidationError("Symbol is required")
            prediction = self.model_manager.predict(
                model_id=model_id,
                data={"symbol": symbol, "timeframe": timeframe, "period": period},
            )
            latest_predictions = prediction["predictions"][-horizon:]
            market_data = self._get_market_data(
                symbol=symbol, timeframe=timeframe, period="1d"
            )
            latest_price = market_data[-1]["close"]
            prediction_values = [p["value"] for p in latest_predictions]
            avg_prediction = sum(prediction_values) / len(prediction_values)
            min_prediction = min(prediction_values)
            max_prediction = max(prediction_values)
            change = avg_prediction - latest_price
            change_percent = change / latest_price * 100
            if change_percent > 1:
                direction = "bullish"
            elif change_percent < -1:
                direction = "bearish"
            else:
                direction = "neutral"
            response = {
                "symbol": symbol,
                "model_id": model_id,
                "latest_price": latest_price,
                "prediction": {
                    "average": avg_prediction,
                    "minimum": min_prediction,
                    "maximum": max_prediction,
                    "change": change,
                    "change_percent": change_percent,
                    "direction": direction,
                },
                "horizon": horizon,
                "timeframe": timeframe,
                "predictions": latest_predictions,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }
            return response
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error generating prediction: {e}")
            raise ServiceError(f"Error generating prediction: {str(e)}")

    def generate_signals(
        self,
        symbols: List[str],
        model_id: Optional[str] = None,
        timeframe: str = "1d",
        period: str = "1mo",
        strategy: str = "prediction",
    ) -> Dict[str, Any]:
        """Generate trading signals

        Args:
            symbols: List of symbols
            model_id: Model ID (optional)
            timeframe: Timeframe
            period: Period
            strategy: Signal generation strategy

        Returns:
            Trading signals

        Raises:
            ValidationError: If parameters are invalid
            ServiceError: If there is an error generating signals
        """
        try:
            logger.info(f"Generating signals for {len(symbols)} symbols")
            if not symbols:
                raise ValidationError("Symbols are required")
            if strategy == "prediction":
                return self._generate_prediction_signals(
                    symbols, model_id, timeframe, period
                )
            elif strategy == "technical":
                return self._generate_technical_signals(symbols, timeframe, period)
            elif strategy == "ensemble":
                return self._generate_ensemble_signals(
                    symbols, model_id, timeframe, period
                )
            else:
                raise ValidationError(f"Unsupported strategy: {strategy}")
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error generating signals: {e}")
            raise ServiceError(f"Error generating signals: {str(e)}")

    def _generate_prediction_signals(
        self, symbols: List[str], model_id: Optional[str], timeframe: str, period: str
    ) -> Dict[str, Any]:
        """Generate signals based on predictions

        Args:
            symbols: List of symbols
            model_id: Model ID
            timeframe: Timeframe
            period: Period

        Returns:
            Trading signals

        Raises:
            ValidationError: If parameters are invalid
        """
        if not model_id:
            raise ValidationError("Model ID is required for prediction signals")
        signals = []
        for symbol in symbols:
            try:
                prediction = self.generate_prediction(
                    model_id=model_id, symbol=symbol, timeframe=timeframe, period=period
                )
                change_percent = prediction["prediction"]["change_percent"]
                if change_percent > 5:
                    strength = 1.0
                elif change_percent > 3:
                    strength = 0.8
                elif change_percent > 1:
                    strength = 0.6
                elif change_percent > 0:
                    strength = 0.4
                elif change_percent > -1:
                    strength = 0.2
                elif change_percent > -3:
                    strength = 0.0
                else:
                    strength = 0.0
                if change_percent > 1:
                    signal_type = "buy"
                elif change_percent < -1:
                    signal_type = "sell"
                else:
                    signal_type = "hold"
                signal = {
                    "symbol": symbol,
                    "type": signal_type,
                    "strength": strength,
                    "price": prediction["latest_price"],
                    "prediction": prediction["prediction"],
                    "model_id": model_id,
                    "strategy": "prediction",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }
                signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        response = {
            "signals": signals,
            "count": len(signals),
            "strategy": "prediction",
            "model_id": model_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        return response

    def _generate_technical_signals(
        self, symbols: List[str], timeframe: str, period: str
    ) -> Dict[str, Any]:
        """Generate signals based on technical analysis

        Args:
            symbols: List of symbols
            timeframe: Timeframe
            period: Period

        Returns:
            Trading signals
        """
        signals = []
        for symbol in symbols:
            try:
                market_data = self._get_market_data(
                    symbol=symbol, timeframe=timeframe, period=period
                )
                df = pd.DataFrame(market_data)
                from data_service.data_processor import DataProcessor

                data_processor = DataProcessor(self.config_manager, self.db_manager)
                df = data_processor.generate_signals(df, strategy="sma_crossover")
                latest_signal = df["signal"].iloc[-1]
                if latest_signal > 0:
                    signal_type = "buy"
                    strength = 0.8
                elif latest_signal < 0:
                    signal_type = "sell"
                    strength = 0.8
                else:
                    signal_type = "hold"
                    strength = 0.0
                signal = {
                    "symbol": symbol,
                    "type": signal_type,
                    "strength": strength,
                    "price": market_data[-1]["close"],
                    "strategy": "technical",
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                }
                signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                continue
        response = {
            "signals": signals,
            "count": len(signals),
            "strategy": "technical",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        return response

    def _generate_ensemble_signals(
        self, symbols: List[str], model_id: Optional[str], timeframe: str, period: str
    ) -> Dict[str, Any]:
        """Generate signals based on ensemble of strategies

        Args:
            symbols: List of symbols
            model_id: Model ID
            timeframe: Timeframe
            period: Period

        Returns:
            Trading signals

        Raises:
            ValidationError: If parameters are invalid
        """
        if not model_id:
            raise ValidationError("Model ID is required for ensemble signals")
        prediction_signals = self._generate_prediction_signals(
            symbols=symbols, model_id=model_id, timeframe=timeframe, period=period
        )
        technical_signals = self._generate_technical_signals(
            symbols=symbols, timeframe=timeframe, period=period
        )
        signals = []
        for symbol in symbols:
            try:
                prediction_signal = next(
                    (s for s in prediction_signals["signals"] if s["symbol"] == symbol),
                    None,
                )
                technical_signal = next(
                    (s for s in technical_signals["signals"] if s["symbol"] == symbol),
                    None,
                )
                if prediction_signal and technical_signal:
                    if prediction_signal["type"] == technical_signal["type"] == "buy":
                        signal_type = "buy"
                        strength = (
                            prediction_signal["strength"] + technical_signal["strength"]
                        ) / 2
                    elif (
                        prediction_signal["type"] == technical_signal["type"] == "sell"
                    ):
                        signal_type = "sell"
                        strength = (
                            prediction_signal["strength"] + technical_signal["strength"]
                        ) / 2
                    elif (
                        prediction_signal["type"] == "buy"
                        and technical_signal["type"] == "sell"
                    ):
                        signal_type = "hold"
                        strength = 0.0
                    elif (
                        prediction_signal["type"] == "sell"
                        and technical_signal["type"] == "buy"
                    ):
                        signal_type = "hold"
                        strength = 0.0
                    else:
                        signal_type = "hold"
                        strength = 0.0
                    signal = {
                        "symbol": symbol,
                        "type": signal_type,
                        "strength": strength,
                        "price": prediction_signal["price"],
                        "prediction": prediction_signal.get("prediction"),
                        "model_id": model_id,
                        "strategy": "ensemble",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                    }
                    signals.append(signal)
            except Exception as e:
                logger.error(f"Error generating ensemble signal for {symbol}: {e}")
                continue
        response = {
            "signals": signals,
            "count": len(signals),
            "strategy": "ensemble",
            "model_id": model_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        return response

    def _get_market_data(
        self, symbol: str, timeframe: str, period: str
    ) -> List[Dict[str, Any]]:
        """Get market data from data service

        Args:
            symbol: Symbol
            timeframe: Timeframe
            period: Period

        Returns:
            Market data

        Raises:
            ServiceError: If there is an error getting market data
        """
        try:
            response = requests.get(
                f"{self.data_service_url}/api/market-data/{symbol}",
                params={"timeframe": timeframe, "period": period},
            )
            if response.status_code != 200:
                raise ServiceError(f"Error getting market data: {response.text}")
            data = response.json()
            return data["data"]
        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            raise ServiceError(f"Error getting market data: {str(e)}")

    def get_prediction_history(
        self,
        model_id: str,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get prediction history

        Args:
            model_id: Model ID
            symbol: Symbol
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            Prediction history

        Raises:
            NotFoundError: If model is not found
            ValidationError: If parameters are invalid
            ServiceError: If there is an error getting prediction history
        """
        try:
            logger.info(
                f"Getting prediction history for {symbol} using model {model_id}"
            )
            if not model_id:
                raise ValidationError("Model ID is required")
            if not symbol:
                raise ValidationError("Symbol is required")
            session = self.db_manager.get_postgres_session()
            query = "\n                SELECT *\n                FROM prediction_history\n                WHERE model_id = %s AND symbol = %s\n            "
            params = [model_id, symbol]
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)
            query += " ORDER BY timestamp ASC"
            result = session.execute(query, params)
            predictions = []
            for row in result:
                predictions.append(
                    {
                        "id": row["id"],
                        "model_id": row["model_id"],
                        "symbol": row["symbol"],
                        "timestamp": row["timestamp"].isoformat(),
                        "prediction": row["prediction"],
                        "actual": row["actual"],
                        "error": row["error"],
                    }
                )
            response = {
                "model_id": model_id,
                "symbol": symbol,
                "predictions": predictions,
                "count": len(predictions),
            }
            return response
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error getting prediction history: {e}")
            raise ServiceError(f"Error getting prediction history: {str(e)}")
        finally:
            session.close()

    def save_prediction(
        self,
        model_id: str,
        symbol: str,
        timestamp: str,
        prediction: float,
        actual: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Save prediction to history

        Args:
            model_id: Model ID
            symbol: Symbol
            timestamp: Timestamp
            prediction: Prediction value
            actual: Actual value (optional)

        Returns:
            Saved prediction

        Raises:
            ValidationError: If parameters are invalid
            ServiceError: If there is an error saving prediction
        """
        try:
            logger.info(f"Saving prediction for {symbol} using model {model_id}")
            if not model_id:
                raise ValidationError("Model ID is required")
            if not symbol:
                raise ValidationError("Symbol is required")
            if not timestamp:
                raise ValidationError("Timestamp is required")
            error = None
            if actual is not None:
                error = actual - prediction
            session = self.db_manager.get_postgres_session()
            query = "\n                INSERT INTO prediction_history\n                (model_id, symbol, timestamp, prediction, actual, error)\n                VALUES (%s, %s, %s, %s, %s, %s)\n                RETURNING id\n            "
            result = session.execute(
                query, [model_id, symbol, timestamp, prediction, actual, error]
            )
            prediction_id = result.fetchone()[0]
            session.commit()
            response = {
                "id": prediction_id,
                "model_id": model_id,
                "symbol": symbol,
                "timestamp": timestamp,
                "prediction": prediction,
                "actual": actual,
                "error": error,
            }
            return response
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            raise ServiceError(f"Error saving prediction: {str(e)}")
        finally:
            session.close()

    def update_prediction(self, prediction_id: str, actual: float) -> Dict[str, Any]:
        """Update prediction with actual value

        Args:
            prediction_id: Prediction ID
            actual: Actual value

        Returns:
            Updated prediction

        Raises:
            NotFoundError: If prediction is not found
            ValidationError: If parameters are invalid
            ServiceError: If there is an error updating prediction
        """
        try:
            logger.info(f"Updating prediction {prediction_id}")
            if not prediction_id:
                raise ValidationError("Prediction ID is required")
            session = self.db_manager.get_postgres_session()
            query = "\n                SELECT *\n                FROM prediction_history\n                WHERE id = %s\n            "
            result = session.execute(query, [prediction_id])
            row = result.fetchone()
            if not row:
                raise NotFoundError(f"Prediction not found: {prediction_id}")
            error = actual - row["prediction"]
            query = "\n                UPDATE prediction_history\n                SET actual = %s, error = %s\n                WHERE id = %s\n            "
            session.execute(query, [actual, error, prediction_id])
            session.commit()
            response = {
                "id": prediction_id,
                "model_id": row["model_id"],
                "symbol": row["symbol"],
                "timestamp": row["timestamp"].isoformat(),
                "prediction": row["prediction"],
                "actual": actual,
                "error": error,
            }
            return response
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error updating prediction: {e}")
            raise ServiceError(f"Error updating prediction: {str(e)}")
        finally:
            session.close()

    def get_model_performance(
        self,
        model_id: str,
        symbol: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get model performance metrics

        Args:
            model_id: Model ID
            symbol: Symbol (optional)
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            Model performance metrics

        Raises:
            NotFoundError: If model is not found
            ValidationError: If parameters are invalid
            ServiceError: If there is an error getting model performance
        """
        try:
            logger.info(f"Getting performance metrics for model {model_id}")
            if not model_id:
                raise ValidationError("Model ID is required")
            session = self.db_manager.get_postgres_session()
            query = "\n                SELECT\n                    model_id,\n                    symbol,\n                    COUNT(*) as count,\n                    AVG(error) as avg_error,\n                    AVG(ABS(error)) as avg_abs_error,\n                    STDDEV(error) as std_error,\n                    MIN(error) as min_error,\n                    MAX(error) as max_error\n                FROM prediction_history\n                WHERE model_id = %s AND actual IS NOT NULL\n            "
            params = [model_id]
            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)
            if start_date:
                query += " AND timestamp >= %s"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= %s"
                params.append(end_date)
            if symbol:
                query += " GROUP BY model_id, symbol"
            else:
                query += " GROUP BY model_id"
            result = session.execute(query, params)
            metrics = []
            for row in result:
                metrics.append(
                    {
                        "model_id": row["model_id"],
                        "symbol": row["symbol"] if symbol else None,
                        "count": row["count"],
                        "avg_error": (
                            float(row["avg_error"]) if row["avg_error"] else None
                        ),
                        "avg_abs_error": (
                            float(row["avg_abs_error"])
                            if row["avg_abs_error"]
                            else None
                        ),
                        "std_error": (
                            float(row["std_error"]) if row["std_error"] else None
                        ),
                        "min_error": (
                            float(row["min_error"]) if row["min_error"] else None
                        ),
                        "max_error": (
                            float(row["max_error"]) if row["max_error"] else None
                        ),
                    }
                )
            response = {
                "model_id": model_id,
                "symbol": symbol,
                "metrics": metrics[0] if metrics else None,
            }
            return response
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            raise ServiceError(f"Error getting model performance: {str(e)}")
        finally:
            session.close()
