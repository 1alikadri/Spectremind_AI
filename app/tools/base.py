from abc import ABC, abstractmethod


class BaseTool(ABC):
    name: str

    @abstractmethod
    def run(self, target: str) -> dict:
        raise NotImplementedError