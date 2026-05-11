import json
import time
from pathlib import Path
from core.logging import LOG


class KeyManager:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.keys = []
        self.nvidia_key = None
        self.current_index = 0
        self.failed_keys = {}
        self._logger = LOG.get_logger("KeyManager")
        self.load_keys()

    def load_keys(self):
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.keys = config.get("gemini_api_keys", [])
                self.nvidia_key = config.get("nvidia_api_key")
                if not self.keys and "gemini_api_key" in config:
                    self.keys = [config["gemini_api_key"]]
            self._logger.info(f"Loaded {len(self.keys)} API key(s)")
        except Exception as e:
            self._logger.error(f"Error loading keys: {e}")
            self.keys = []

    def get_key(self) -> str:
        if not self.keys:
            self.load_keys()
        if not self.keys:
            return ""
        active = self.get_active_keys()
        if not active:
            return ""
        return active[0]

    def rotate(self):
        if len(self.keys) > 1:
            self.current_index = (self.current_index + 1) % len(self.keys)
            self._logger.info(f"Rotating to key index {self.current_index}")
            return True
        return False

    def get_active_keys(self) -> list:
        now = time.time()
        cooldown = 300
        expired = [k for k, t in self.failed_keys.items() if now - t > cooldown]
        for k in expired:
            del self.failed_keys[k]
            self._logger.info("Key cooled down and restored to pool")
        active = [k for k in self.keys if k not in self.failed_keys]
        if not active and self.keys:
            self._logger.warning("All keys failed. Resetting blacklist.")
            self.failed_keys.clear()
            active = self.keys
        return active

    def mark_key_failed(self, api_key: str):
        if api_key and api_key in self.keys:
            self.failed_keys[api_key] = time.time()
            remaining = len(self.keys) - len(self.failed_keys)
            self._logger.warning(f"Key blacklisted. Remaining active: {remaining}")

    def get_nvidia_key(self) -> str:
        return self.nvidia_key or ""
