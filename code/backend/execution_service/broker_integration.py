import logging
from typing import Any, Dict, List

import requests
from backend.common import ServiceError, setup_logger

logger = setup_logger("broker_integration", logging.INFO)


class BrokerIntegration:

    def __init__(self, config_manager: object, db_manager: object) -> None:
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.broker_url = config_manager.get("broker.url", "http://localhost:9000")
        data_host = config_manager.get("services.data_service.host", "localhost")
        data_port = config_manager.get("services.data_service.port", "8081")
        self.data_service_url = f"http://{data_host}:{data_port}"
        logger.info("Broker integration initialized")

    def submit_order_to_broker(self, order: Dict[str, Any]) -> Dict[str, Any]:
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
        return [{"id": "default", "name": "Default Broker", "status": "active"}]
