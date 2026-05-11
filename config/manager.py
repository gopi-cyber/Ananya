import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from interfaces.config import ConfigInterface


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR = get_base_dir()
CONFIG_DIR = BASE_DIR / "config"
CONFIG_FILE = CONFIG_DIR / "api_keys.json"


class ConfigManager(ConfigInterface):
    def __init__(self, config_path: Optional[Path] = None):
        self._config_path = config_path or CONFIG_FILE
        self._data: Dict[str, Any] = {}
        self.reload()

    def reload(self):
        try:
            if self._config_path.exists():
                self._data = json.loads(self._config_path.read_text(encoding="utf-8"))
            else:
                self._data = {}
        except Exception as e:
            print(f"[ConfigManager] Error loading config: {e}")
            self._data = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self._save()

    def get_api_keys(self) -> List[str]:
        keys = self._data.get("gemini_api_keys", [])
        if not keys and "gemini_api_key" in self._data:
            keys = [self._data["gemini_api_key"]]
        return keys

    def get_nvidia_key(self) -> Optional[str]:
        return self._data.get("nvidia_api_key")

    def get_voice_name(self) -> str:
        return self._data.get("voice_name", "Aoede")

    def get_os(self) -> str:
        return self._data.get("os_system", "windows").lower()

    def is_windows(self) -> bool:
        return self.get_os() == "windows"

    def is_mac(self) -> bool:
        return self.get_os() == "mac"

    def is_linux(self) -> bool:
        return self.get_os() == "linux"

    def save_api_key(self, gemini_api_key: str):
        keys = self.get_api_keys()
        if gemini_api_key.strip() not in keys:
            keys.insert(0, gemini_api_key.strip())
        self._data["gemini_api_keys"] = keys
        self._save()

    def is_configured(self) -> bool:
        keys = self.get_api_keys()
        return bool(keys and len(keys[0]) > 15)

    def _save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self._config_path.write_text(
            json.dumps(self._data, indent=2),
            encoding="utf-8"
        )


def ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def config_exists() -> bool:
    return CONFIG_FILE.exists()


def save_api_keys(gemini_api_key: str):
    cm = ConfigManager()
    cm.save_api_key(gemini_api_key)


def load_api_keys() -> dict:
    cm = ConfigManager()
    return cm._data


def get_gemini_key() -> Optional[str]:
    keys = ConfigManager().get_api_keys()
    return keys[0] if keys else None


def is_configured() -> bool:
    return ConfigManager().is_configured()
