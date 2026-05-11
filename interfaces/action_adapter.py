from typing import Any, Dict, Optional
from interfaces.action import BaseAction, ActionResult


class ActionAdapter(BaseAction):
    """Adapter that wraps existing action modules with the BaseAction interface.
    This allows backward-compatible standardization without rewriting all modules.
    """

    def __init__(self, action_func, action_name: str, action_desc: str):
        super().__init__()
        self._action_func = action_func
        self._action_name = action_name
        self._action_desc = action_desc

    def execute(self, parameters: Dict[str, Any]) -> str:
        result = self._action_func(parameters)
        if isinstance(result, str):
            return result
        return str(result) if result else "Done."

    @classmethod
    def name(cls) -> str:
        return cls._action_name if hasattr(cls, '_action_name') else "unknown"

    @classmethod
    def description(cls) -> str:
        return cls._action_desc if hasattr(cls, '_action_desc') else ""


class ActionRegistry:
    """Registry for all available actions."""

    def __init__(self):
        self._actions: Dict[str, ActionAdapter] = {}

    def register(self, action: ActionAdapter):
        self._actions[action.name()] = action

    def get(self, name: str) -> Optional[ActionAdapter]:
        return self._actions.get(name)

    def has(self, name: str) -> bool:
        return name in self._actions

    def all(self) -> Dict[str, ActionAdapter]:
        return dict(self._actions)

    def execute(self, name: str, parameters: Dict[str, Any]) -> ActionResult:
        action = self.get(name)
        if not action:
            return ActionResult.error(f"Unknown action: {name}")
        try:
            result = action.execute(parameters)
            return ActionResult.ok(result)
        except Exception as e:
            return ActionResult.error(f"{name} failed: {e}")
