from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class MemoryInterface(ABC):
    """Interface for memory storage backends."""

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def save(self, memory: Dict[str, Any]):
        pass

    @abstractmethod
    def update(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def format_for_prompt(self, memory: Optional[Dict[str, Any]] = None) -> str:
        pass
