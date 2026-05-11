from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ConfigInterface(ABC):
    """Interface for configuration management."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any):
        pass

    @abstractmethod
    def get_api_keys(self) -> List[str]:
        pass

    @abstractmethod
    def reload(self):
        pass
