import json
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from confluent_kafka import Consumer, KafkaError, KafkaException, Producer

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KafkaProducer:

    def __init__(self, bootstrap_servers: str, client_id: str) -> None:
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "client.id": client_id,
            "acks": "all",
        }
        self.producer = Producer(self.config)
        logger.info(f"Kafka producer initialized with client ID: {client_id}")

    def publish(
        self, topic: str, message: Dict[str, Any], key: Optional[str] = None
    ) -> None:
        try:
            message_json = json.dumps(message).encode("utf-8")
            self.producer.produce(
                topic=topic,
                value=message_json,
                key=key.encode("utf-8") if key else None,
                callback=self._delivery_callback,
            )
            self.producer.flush()
            logger.debug(f"Published message to topic {topic}")
        except Exception as e:
            logger.error(f"Error publishing message to topic {topic}: {e}")
            raise

    def _delivery_callback(self, err: object, msg: object) -> object:
        if err:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}"
            )

    def close(self) -> None:
        self.producer.flush()
        logger.info("Kafka producer closed")


class KafkaConsumer:

    def __init__(
        self,
        bootstrap_servers: str,
        group_id: str,
        topics: List[str],
        auto_offset_reset: str = "earliest",
    ) -> None:
        self.config = {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": True,
        }
        self.topics = topics
        self.consumer = Consumer(self.config)
        self.running = False
        self.consumer_thread = None
        logger.info(f"Kafka consumer initialized with group ID: {group_id}")

    def start(
        self, message_handler: Callable[[Dict[str, Any], str, int, int], None]
    ) -> None:
        if self.running:
            logger.warning("Consumer is already running")
            return
        self.running = True
        self.consumer.subscribe(self.topics)
        self.consumer_thread = threading.Thread(
            target=self._consume_loop, args=(message_handler,), daemon=True
        )
        self.consumer_thread.start()
        logger.info(f"Started consuming from topics: {', '.join(self.topics)}")

    def _consume_loop(
        self, message_handler: Callable[[Dict[str, Any], str, int, int], None]
    ) -> None:
        try:
            while self.running:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition {msg.partition()}")
                    else:
                        logger.error(f"Error while consuming: {msg.error()}")
                else:
                    try:
                        value = json.loads(msg.value().decode("utf-8"))
                        message_handler(
                            value, msg.topic(), msg.partition(), msg.offset()
                        )
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse message as JSON: {msg.value()}")
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")
        except KafkaException as e:
            logger.error(f"Kafka exception: {e}")
        finally:
            logger.info("Exiting consumer loop")

    def stop(self) -> None:
        self.running = False
        if self.consumer_thread:
            self.consumer_thread.join(timeout=5.0)
            if self.consumer_thread.is_alive():
                logger.warning("Consumer thread did not terminate gracefully")
        self.consumer.close()
        logger.info("Kafka consumer closed")


class MessageBus:

    def __init__(self, bootstrap_servers: str, service_name: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.service_name = service_name
        self.producer = KafkaProducer(bootstrap_servers, f"{service_name}-producer")
        self.consumers = {}
        logger.info(f"Message bus initialized for service: {service_name}")

    def publish(
        self, topic: str, message: Dict[str, Any], key: Optional[str] = None
    ) -> None:
        message["metadata"] = {
            "service": self.service_name,
            "timestamp": int(time.time() * 1000),
        }
        self.producer.publish(topic, message, key)

    def subscribe(
        self,
        topics: List[str],
        group_id: str,
        message_handler: Callable[[Dict[str, Any], str, int, int], None],
    ) -> None:
        consumer_key = f"{group_id}-{'-'.join(topics)}"
        if consumer_key in self.consumers:
            logger.warning(
                f"Consumer already exists for group {group_id} and topics {topics}"
            )
            return
        consumer = KafkaConsumer(self.bootstrap_servers, group_id, topics)
        consumer.start(message_handler)
        self.consumers[consumer_key] = consumer

    def close(self) -> None:
        self.producer.close()
        for consumer in self.consumers.values():
            consumer.stop()
        logger.info("Message bus closed")
