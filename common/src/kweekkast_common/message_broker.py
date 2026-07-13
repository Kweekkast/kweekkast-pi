from __future__ import annotations

from kweekkast_common.communication_component.subscriber import Subscriber
from kweekkast_common.communication_component.connection import ConnectionDevice
from kweekkast_common.logger_component import file_logger
from kweekkast_common.logger_component.logger_enum import MessageSeverity
from kweekkast_common.reading import Reading


class MessageBroker:
    """
    Centrale broker die berichten doorstuurt op basis van ConnectionDevice topic.
    Subscribers registreren zich op een specifiek topic (ConnectionDevice.ESP of ConnectionDevice.PI).
    """

    def __init__(self):
        self.subscribers: dict[ConnectionDevice, list[Subscriber]] = {}

    def Subscribe(self, topic: ConnectionDevice, subscriber: Subscriber) -> None:
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(subscriber)
        file_logger.logger.log(MessageSeverity.INFO, self.__class__.__name__,
                               f"gesubscribed op {topic.name}")

    def Unsubscribe(self, topic: ConnectionDevice, subscriber: Subscriber) -> None:
        if topic in self.subscribers:
            self.subscribers[topic].remove(subscriber)

    def Publish(self, topic: ConnectionDevice, reading: Reading) -> None:
        for subscriber in self.subscribers.get(topic, []):
            subscriber.Notify(reading)