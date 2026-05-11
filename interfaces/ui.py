from abc import ABC, abstractmethod
from typing import Any


class UIInterface(ABC):
    """Interface for UI interaction."""

    @abstractmethod
    def set_state(self, state: str):
        pass

    @abstractmethod
    def write_log(self, msg: str, style: str = "plain"):
        pass

    @abstractmethod
    def update_amplitude(self, amp: float, is_mic: bool = False):
        pass
