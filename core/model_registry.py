from pathlib import Path
from google import genai
from core.key_manager import KeyManager
from core.logging import LOG


class ModelRegistry:
    def __init__(self, config_path: Path):
        self.key_manager = KeyManager(config_path)
        self._logger = LOG.get_logger("ModelRegistry")

        self.models = {
            "CEO": "gemini-2.5-flash-native-audio-latest",
            "CTO": "gemini-2.5-flash",
            "RESEARCHER": "gemini-2.5-flash-lite",
            "ANALYST": "gemini-3.1-flash-lite",
            "CREATIVE": "imagen-4",
            "COMPUTER_USE": "gemini-2.5-flash-lite",
            "EXPERT_CTO": "nvidia/meta/llama-3.3-70b-instruct",
            "REASONER": "nvidia/deepseek-ai/deepseek-r1"
        }

        self.last_used_key = None
        self._clients = {}

    def mark_key_failed(self, api_key: str):
        self.key_manager.mark_key_failed(api_key)

    def get_active_keys(self) -> list:
        return self.key_manager.get_active_keys()

    def get_client(self, model_key="CEO"):
        active_keys = self.get_active_keys()
        if not active_keys:
            return None

        import random
        api_key = random.choice(active_keys)
        self.last_used_key = api_key

        return genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})

    def get_nvidia_client(self):
        nv_key = self.key_manager.get_nvidia_key()
        if not nv_key:
            return None
        try:
            from openai import OpenAI
            return OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=nv_key
            )
        except ImportError:
            self._logger.error("'openai' package not installed. Run pip install openai.")
            return None

    def get_model_name(self, role):
        return self.models.get(role.upper(), self.models["CEO"])


registry = None


def init_registry(config_path: Path):
    global registry
    registry = ModelRegistry(config_path)
    return registry


def get_registry():
    return registry
