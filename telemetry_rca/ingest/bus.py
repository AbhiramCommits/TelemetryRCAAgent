"""Message bus interface and implementations (KafkaBus and LocalBus)."""

from abc import ABC, abstractmethod
from typing import Iterator, Optional
import queue
import json
from confluent_kafka import Producer, Consumer, KafkaError


class MessageBus(ABC):
    @abstractmethod
    def produce(self, topic: str, key: str, value: dict) -> None:
        pass

    @abstractmethod
    def consume(self, topic: str, group: str) -> Iterator[dict]:
        pass


class LocalBus(MessageBus):
    def __init__(self) -> None:
        self.queues: dict[str, queue.Queue] = {}

    def _get_queue(self, topic: str) -> queue.Queue:
        if topic not in self.queues:
            self.queues[topic] = queue.Queue()
        return self.queues[topic]

    def produce(self, topic: str, key: str, value: dict) -> None:
        q = self._get_queue(topic)
        q.put({"key": key, "value": value})

    def consume(self, topic: str, group: str) -> Iterator[dict]:
        q = self._get_queue(topic)
        while True:
            try:
                item = q.get(timeout=1.0)
                yield item
            except queue.Empty:
                break


class KafkaBus(MessageBus):
    def __init__(self, bootstrap_servers: str) -> None:
        self.bootstrap_servers = bootstrap_servers
        self.producer = Producer({"bootstrap.servers": bootstrap_servers})

    def produce(self, topic: str, key: str, value: dict) -> None:
        def delivery_report(err, msg):
            if err is not None:
                pass
        self.producer.produce(
            topic,
            key=key.encode("utf-8") if key else None,
            value=json.dumps(value).encode("utf-8"),
            callback=delivery_report
        )
        self.producer.poll(0)

    def consume(self, topic: str, group: str) -> Iterator[dict]:
        consumer = Consumer({
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
        })
        consumer.subscribe([topic])
        try:
            while True:
                msg = consumer.poll(1.0)
                if msg is None:
                    break
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        break
                yield {
                    "key": msg.key().decode("utf-8") if msg.key() else None,
                    "value": json.loads(msg.value().decode("utf-8"))
                }
        finally:
            consumer.close()
