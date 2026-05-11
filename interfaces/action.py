from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAction(ABC):
    """Standardized interface for all action modules."""

    def __init__(self):
        self._logger = None

    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> str:
        """Execute the action with given parameters and return a result string."""
        pass

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        """Return the unique name of this action."""
        pass

    @classmethod
    @abstractmethod
    def description(cls) -> str:
        """Return a description of what this action does."""
        pass

    def validate(self, parameters: Dict[str, Any]) -> Optional[str]:
        """Validate parameters. Return error message or None if valid."""
        return None

    def cleanup(self):
        """Cleanup resources if needed."""
        pass


class ActionResult:
    def __init__(self, success: bool, message: str, data: Any = None):
        self.success = success
        self.message = message
        self.data = data

    def __str__(self) -> str:
        return self.message

    @classmethod
    def ok(cls, message: str = "Done.", data: Any = None) -> "ActionResult":
        return cls(True, message, data)

    @classmethod
    def error(cls, message: str, data: Any = None) -> "ActionResult":
        return cls(False, message, data)
