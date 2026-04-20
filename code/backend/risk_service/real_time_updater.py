"""
Real-time data updater for QuantumAlpha Risk Service.
Handles continuous data ingestion and model updates.
"""

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from queue import Empty, Queue
from typing import Any, Callable, Dict, List

from backend.common import ServiceError, setup_logger
from backend.data_service.market_data import MarketDataService
from backend.risk_service.online_learning import OnlineLearningEngine

logger = setup_logger("real_time_updater", logging.INFO)


class RealTimeUpdater:
    """Real-time data updater and model adapter"""

    def __init__(self, config_manager: object, db_manager: object) -> None:
        """Initialize real-time updater

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.online_learning_engine = OnlineLearningEngine(config_manager, db_manager)
        self.market_data_service = MarketDataService(config_manager, db_manager)
        self.data_sources = {
            "websocket_feeds": [],
            "polling_feeds": [],
            "event_streams": [],
        }
        self.data_queue = Queue(maxsize=10000)
        self.update_queue = Queue(maxsize=1000)
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running = False
        self.threads = []
        self.model_update_interval = 300
        self.data_fetch_interval = 60
        self.anomaly_check_interval = 120
        self.tracked_symbols = set()
        self.metrics = {
            "data_points_processed": 0,
            "model_updates": 0,
            "anomalies_detected": 0,
            "last_update": None,
            "processing_errors": 0,
        }
        self.callbacks = {
            "data_received": [],
            "model_updated": [],
            "anomaly_detected": [],
            "error_occurred": [],
        }
        logger.info("Real-time updater initialized")

    def start(self, symbols: List[str]) -> None:
        """Start real-time data processing

        Args:
            symbols: List of symbols to track
        """
        try:
            logger.info(f"Starting real-time updater for {len(symbols)} symbols")
            self.tracked_symbols = set(symbols)
            self.running = True
            self.online_learning_engine.load_models()
            self._start_data_processor()
            self._start_model_updater()
            self._start_anomaly_detector()
            self._start_data_fetcher()
            self._initialize_feeds()
            logger.info("Real-time updater started successfully")
        except Exception as e:
            logger.error(f"Error starting real-time updater: {e}")
            self.stop()
            raise ServiceError(f"Error starting real-time updater: {str(e)}")

    def stop(self) -> None:
        """Stop real-time data processing"""
        try:
            logger.info("Stopping real-time updater")
            self.running = False
            for thread in self.threads:
                if thread.is_alive():
                    thread.join(timeout=5)
            self.executor.shutdown(wait=True)
            self._close_feeds()
            logger.info("Real-time updater stopped")
        except Exception as e:
            logger.error(f"Error stopping real-time updater: {e}")

    def add_symbol(self, symbol: str) -> None:
        """Add a symbol to real-time tracking

        Args:
            symbol: Symbol to add
        """
        self.tracked_symbols.add(symbol)
        logger.info(f"Added symbol {symbol} to real-time tracking")

    def remove_symbol(self, symbol: str) -> None:
        """Remove a symbol from real-time tracking

        Args:
            symbol: Symbol to remove
        """
        self.tracked_symbols.discard(symbol)
        logger.info(f"Removed symbol {symbol} from real-time tracking")

    def register_callback(self, event_type: str, callback: Callable) -> None:
        """Register a callback for real-time events

        Args:
            event_type: Type of event ('data_received', 'model_updated', 'anomaly_detected', 'error_occurred')
            callback: Callback function
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
            logger.info(f"Registered callback for {event_type}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get real-time processing metrics

        Returns:
            Processing metrics
        """
        return {
            "metrics": self.metrics.copy(),
            "tracked_symbols": list(self.tracked_symbols),
            "queue_sizes": {
                "data_queue": self.data_queue.qsize(),
                "update_queue": self.update_queue.qsize(),
            },
            "running": self.running,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }

    def force_model_update(self) -> Dict[str, Any]:
        """Force an immediate model update

        Returns:
            Update results
        """
        try:
            logger.info("Forcing immediate model update")
            market_data = {}
            for symbol in self.tracked_symbols:
                try:
                    data = self.market_data_service.get_market_data(
                        symbol=symbol, timeframe="1m", period="1h"
                    )
                    market_data[symbol] = data["data"]
                except Exception as e:
                    logger.warning(f"Could not get data for {symbol}: {e}")
            if market_data:
                result = self.online_learning_engine.update_models(market_data)
                self.metrics["model_updates"] += 1
                self.metrics["last_update"] = datetime.now(timezone.utc).isoformat()
                self._trigger_callbacks("model_updated", result)
                return result
            else:
                return {"status": "no_update", "reason": "no_data_available"}
        except Exception as e:
            logger.error(f"Error forcing model update: {e}")
            raise ServiceError(f"Error forcing model update: {str(e)}")

    def _start_data_processor(self) -> None:
        """Start data processing thread"""

        def process_data():
            while self.running:
                try:
                    data = self.data_queue.get(timeout=1)
                    self._process_data_point(data)
                    self.metrics["data_points_processed"] += 1
                    self.data_queue.task_done()
                except Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error processing data: {e}")
                    self.metrics["processing_errors"] += 1
                    self._trigger_callbacks(
                        "error_occurred",
                        {"error": str(e), "context": "data_processing"},
                    )

        thread = threading.Thread(target=process_data, daemon=True)
        thread.start()
        self.threads.append(thread)
        logger.info("Data processor thread started")

    def _start_model_updater(self) -> None:
        """Start model update thread"""

        def update_models():
            while self.running:
                try:
                    time.sleep(self.model_update_interval)
                    if not self.running:
                        break
                    market_data = {}
                    for symbol in self.tracked_symbols:
                        try:
                            data = self.market_data_service.get_market_data(
                                symbol=symbol, timeframe="1m", period="1h"
                            )
                            market_data[symbol] = data["data"]
                        except Exception as e:
                            logger.warning(f"Could not get data for {symbol}: {e}")
                    if market_data:
                        result = self.online_learning_engine.update_models(market_data)
                        self.metrics["model_updates"] += 1
                        self.metrics["last_update"] = datetime.now(
                            timezone.utc
                        ).isoformat()
                        self._trigger_callbacks("model_updated", result)
                        logger.info(
                            f"Models updated: {result.get('models_updated', [])}"
                        )
                except Exception as e:
                    logger.error(f"Error in model updater: {e}")
                    self.metrics["processing_errors"] += 1
                    self._trigger_callbacks(
                        "error_occurred", {"error": str(e), "context": "model_updating"}
                    )

        thread = threading.Thread(target=update_models, daemon=True)
        thread.start()
        self.threads.append(thread)
        logger.info("Model updater thread started")

    def _start_anomaly_detector(self) -> None:
        """Start anomaly detection thread"""

        def detect_anomalies():
            while self.running:
                try:
                    time.sleep(self.anomaly_check_interval)
                    if not self.running:
                        break
                    market_data = {}
                    for symbol in self.tracked_symbols:
                        try:
                            data = self.market_data_service.get_market_data(
                                symbol=symbol, timeframe="1m", period="30m"
                            )
                            market_data[symbol] = data["data"]
                        except Exception as e:
                            logger.warning(f"Could not get data for {symbol}: {e}")
                    if market_data:
                        result = self.online_learning_engine.detect_market_anomalies(
                            market_data
                        )
                        if result.get("anomalies_detected", False):
                            self.metrics["anomalies_detected"] += len(
                                result.get("anomalous_symbols", [])
                            )
                            self._trigger_callbacks("anomaly_detected", result)
                            logger.warning(
                                f"Anomalies detected: {result.get('anomalous_symbols', [])}"
                            )
                except Exception as e:
                    logger.error(f"Error in anomaly detector: {e}")
                    self.metrics["processing_errors"] += 1
                    self._trigger_callbacks(
                        "error_occurred",
                        {"error": str(e), "context": "anomaly_detection"},
                    )

        thread = threading.Thread(target=detect_anomalies, daemon=True)
        thread.start()
        self.threads.append(thread)
        logger.info("Anomaly detector thread started")

    def _start_data_fetcher(self) -> None:
        """Start periodic data fetching thread"""

        def fetch_data():
            while self.running:
                try:
                    time.sleep(self.data_fetch_interval)
                    if not self.running:
                        break
                    for symbol in self.tracked_symbols:
                        try:
                            data = self.market_data_service.get_market_data(
                                symbol=symbol, timeframe="1m", period="5m"
                            )
                            if data["data"]:
                                latest_data = data["data"][-1]
                                data_point = {
                                    "symbol": symbol,
                                    "data": latest_data,
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                    "source": "polling",
                                }
                                if not self.data_queue.full():
                                    self.data_queue.put(data_point)
                        except Exception as e:
                            logger.warning(f"Error fetching data for {symbol}: {e}")
                except Exception as e:
                    logger.error(f"Error in data fetcher: {e}")
                    self.metrics["processing_errors"] += 1
                    self._trigger_callbacks(
                        "error_occurred", {"error": str(e), "context": "data_fetching"}
                    )

        thread = threading.Thread(target=fetch_data, daemon=True)
        thread.start()
        self.threads.append(thread)
        logger.info("Data fetcher thread started")

    def _process_data_point(self, data_point: Dict[str, Any]) -> None:
        """Process a single data point

        Args:
            data_point: Data point to process
        """
        try:
            data_point["symbol"]
            data_point["data"]
            self._trigger_callbacks("data_received", data_point)
            if not self.update_queue.full():
                self.update_queue.put(data_point)
        except Exception as e:
            logger.error(f"Error processing data point: {e}")
            raise

    def _initialize_feeds(self) -> None:
        """Initialize real-time data feeds"""
        try:
            logger.info("Real-time feeds initialized (polling mode)")
        except Exception as e:
            logger.error(f"Error initializing feeds: {e}")

    def _close_feeds(self) -> None:
        """Close real-time data feeds"""
        try:
            logger.info("Real-time feeds closed")
        except Exception as e:
            logger.error(f"Error closing feeds: {e}")

    def _trigger_callbacks(self, event_type: str, data: object) -> None:
        """Trigger callbacks for an event type

        Args:
            event_type: Type of event
            data: Event data
        """
        try:
            for callback in self.callbacks.get(event_type, []):
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in callback for {event_type}: {e}")
        except Exception as e:
            logger.error(f"Error triggering callbacks: {e}")


class StreamingDataProcessor:
    """Handles streaming data processing for high-frequency updates"""

    def __init__(self, config_manager: object, db_manager: object) -> None:
        """Initialize streaming data processor

        Args:
            config_manager: Configuration manager
            db_manager: Database manager
        """
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.price_buffer = {}
        self.volume_buffer = {}
        self.trade_buffer = {}
        self.buffer_size = 1000
        self.flush_interval = 30
        self.stats = {
            "messages_processed": 0,
            "trades_processed": 0,
            "quotes_processed": 0,
            "errors": 0,
            "last_flush": None,
        }
        logger.info("Streaming data processor initialized")

    def process_trade(self, trade_data: Dict[str, Any]) -> None:
        """Process a trade message

        Args:
            trade_data: Trade data
        """
        try:
            symbol = trade_data.get("symbol")
            if not symbol:
                return
            if symbol not in self.trade_buffer:
                self.trade_buffer[symbol] = []
            self.trade_buffer[symbol].append(
                {
                    "timestamp": trade_data.get(
                        "timestamp", datetime.now(timezone.utc).isoformat()
                    ),
                    "price": trade_data.get("price"),
                    "size": trade_data.get("size"),
                    "side": trade_data.get("side"),
                }
            )
            if len(self.trade_buffer[symbol]) >= self.buffer_size:
                self._flush_trade_buffer(symbol)
            self.stats["trades_processed"] += 1
            self.stats["messages_processed"] += 1
        except Exception as e:
            logger.error(f"Error processing trade: {e}")
            self.stats["errors"] += 1

    def process_quote(self, quote_data: Dict[str, Any]) -> None:
        """Process a quote message

        Args:
            quote_data: Quote data
        """
        try:
            symbol = quote_data.get("symbol")
            if not symbol:
                return
            self.price_buffer[symbol] = {
                "timestamp": quote_data.get(
                    "timestamp", datetime.now(timezone.utc).isoformat()
                ),
                "bid": quote_data.get("bid"),
                "ask": quote_data.get("ask"),
                "bid_size": quote_data.get("bid_size"),
                "ask_size": quote_data.get("ask_size"),
            }
            self.stats["quotes_processed"] += 1
            self.stats["messages_processed"] += 1
        except Exception as e:
            logger.error(f"Error processing quote: {e}")
            self.stats["errors"] += 1

    def _flush_trade_buffer(self, symbol: str) -> None:
        """Flush trade buffer for a symbol

        Args:
            symbol: Symbol to flush
        """
        try:
            if symbol in self.trade_buffer and self.trade_buffer[symbol]:
                trades = self.trade_buffer[symbol]
                logger.debug(f"Flushing {len(trades)} trades for {symbol}")
                self.trade_buffer[symbol] = []
                self.stats["last_flush"] = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            logger.error(f"Error flushing trade buffer: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics

        Returns:
            Processing statistics
        """
        return {
            "stats": self.stats.copy(),
            "buffer_sizes": {
                "price_buffer": len(self.price_buffer),
                "volume_buffer": len(self.volume_buffer),
                "trade_buffer": sum(
                    (len(trades) for trades in self.trade_buffer.values())
                ),
            },
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }
