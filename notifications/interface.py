from abc import ABC, abstractmethod


class NotificationHandler(ABC):
    @abstractmethod
    async def send(self, message: str) -> None:
        pass
