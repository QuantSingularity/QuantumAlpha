"""
Data Service for QuantumAlpha
This service is responsible for:
1. Market data collection from various sources
2. Alternative data processing
3. Feature engineering
4. Data storage and retrieval
"""

import logging
import os
import traceback

from backend.common import (
    ServiceError,
    get_config_manager,
    get_db_manager,
    setup_logger,
    validate_schema,
)
from backend.common.validation import MarketDataRequest
from backend.data_service.alternative_data import AlternativeDataService
from backend.data_service.feature_engineering import FeatureEngineeringService
from backend.data_service.market_data import MarketDataService
from flask import Flask, jsonify, request
from flask_cors import CORS

logger = setup_logger("data_service", logging.INFO)
app = Flask(__name__)
CORS(app)
config_manager = get_config_manager(
    env_file=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", ".env"
    )
)
db_manager = get_db_manager(config_manager.get_all())
market_data_service = MarketDataService(config_manager, db_manager)
alternative_data_service = AlternativeDataService(config_manager, db_manager)
feature_engineering_service = FeatureEngineeringService(config_manager, db_manager)


@app.errorhandler(Exception)
def handle_error(error: Exception) -> None:
    """Handle errors"""
    if isinstance(error, ServiceError):
        return (jsonify(error.to_dict()), error.status_code)
    logger.error(f"Unhandled error: {error}")
    logger.error(traceback.format_exc())
    return (
        jsonify(
            {
                "error": "Internal server error",
                "status_code": 500,
                "details": str(error),
            }
        ),
        500,
    )


@app.route("/health", methods=["GET"])
def health_check() -> object:
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "data_service"})


@app.route("/api/market-data/<symbol>", methods=["GET"])
def get_market_data(symbol: object) -> None:
    """Get market data for a symbol"""
    try:
        params = {
            "symbol": symbol,
            "timeframe": request.args.get("timeframe", "1d"),
            "period": request.args.get("period"),
            "start_date": request.args.get("start_date"),
            "end_date": request.args.get("end_date"),
        }
        validated_params = validate_schema(params, MarketDataRequest)
        data = market_data_service.get_market_data(
            symbol=validated_params["symbol"],
            timeframe=validated_params["timeframe"],
            period=validated_params["period"],
            start_date=validated_params["start_date"],
            end_date=validated_params["end_date"],
        )
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/alternative-data/<source>", methods=["GET"])
def get_alternative_data(source: object) -> None:
    """Get alternative data from a source"""
    try:
        symbol = request.args.get("symbol")
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        data = alternative_data_service.get_alternative_data(
            source=source, symbol=symbol, start_date=start_date, end_date=end_date
        )
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting alternative data: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/features/<symbol>", methods=["GET"])
def get_features(symbol: object) -> None:
    """Get engineered features for a symbol"""
    try:
        timeframe = request.args.get("timeframe", "1d")
        features = (
            request.args.get("features", "").split(",")
            if request.args.get("features")
            else None
        )
        data = feature_engineering_service.get_features(
            symbol=symbol, timeframe=timeframe, features=features
        )
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error getting features: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/data-sources", methods=["GET"])
def get_data_sources() -> None:
    """Get all data sources"""
    try:
        data_sources = market_data_service.get_data_sources()
        return jsonify({"data_sources": data_sources})
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


@app.route("/api/data-sources", methods=["POST"])
def create_data_source() -> None:
    """Create a new data source"""
    try:
        data = request.json
        data_source = market_data_service.create_data_source(data)
        return jsonify(data_source)
    except Exception as e:
        logger.error(f"Error creating data source: {e}")
        if isinstance(e, ServiceError):
            raise
        else:
            raise ServiceError(str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
