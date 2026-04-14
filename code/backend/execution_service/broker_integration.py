"""
Broker integration for QuantumAlpha Execution Service.
Handles integration with various brokers via HTTP.
"""

import logging
from typing import Any, Dict, List

import requests
from backend.common import ServiceError, setup_logger

logger = setup_logger("broker_integration", logging.INFO)


class BrokerIntegration:
    """Broker integration"""

    def __init__(self, config_manager: Any, db_manager: Any) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.broker_url = config_manager.get("broker.url", "http://localhost:9000")
        # Use data service URL for real-time market data
        data_host = config_manager.get("services.data_service.host", "localhost")
        data_port = config_manager.get("services.data_service.port", "8081")
        self.data_service_url = f"http://{data_host}:{data_port}"
        logger.info("Broker integration initialized")

    def submit_order_to_broker(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Submit an order to the broker."""
        try:
            response = requests.post(f"{self.broker_url}/orders", json=order)
            if response.status_code != 200:
                raise ServiceError(f"Broker error: {response.text}")
            data = response.json()
            return {
                "order_id": order["id"],
                "broker_order_id": data["broker_order_id"],
                "status": data["status"],
            }
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(f"Error submitting order to broker: {str(e)}")

    def get_order_status_from_broker(self, broker_order_id: str) -> Dict[str, Any]:
        """Get the status of an order from the broker."""
        try:
            response = requests.get(f"{self.broker_url}/orders/{broker_order_id}")
            if response.status_code != 200:
                raise ServiceError(f"Broker error: {response.text}")
            return response.json()
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(f"Error getting order status from broker: {str(e)}")

    def cancel_order_at_broker(self, broker_order_id: str) -> Dict[str, Any]:
        """Cancel an order at the broker."""
        try:
            response = requests.delete(f"{self.broker_url}/orders/{broker_order_id}")
            if response.status_code != 200:
                raise ServiceError(f"Broker error: {response.text}")
            return response.json()
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(f"Error canceling order at broker: {str(e)}")

    def get_account_info(self, account_id: str) -> Dict[str, Any]:
        """Get account information from the broker."""
        try:
            response = requests.get(f"{self.broker_url}/accounts/{account_id}")
            if response.status_code != 200:
                raise ServiceError(f"Broker error: {response.text}")
            return response.json()
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(f"Error getting account info: {str(e)}")

    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get real-time market data for a symbol from data service."""
        try:
            response = requests.get(
                f"{self.data_service_url}/api/market-data/{symbol}",
                params={"timeframe": "1m", "period": "1d"},
            )
            if response.status_code != 200:
                raise ServiceError(f"Data service error: {response.text}")
            return response.json()
        except ServiceError:
            raise
        except Exception as e:
            raise ServiceError(f"Error getting market data: {str(e)}")

    def get_brokers(self) -> List[Dict[str, Any]]:
        """Get list of available brokers."""
        return [{"id": "default", "name": "Default Broker", "status": "active"}]
