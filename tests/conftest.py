import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class MockUI:
    def __init__(self):
        self.muted = False
        self.current_file = None
        self.dashboard = MagicMock()
        self._logs = []

    def set_state(self, state):
        pass

    def write_log(self, msg, style="plain"):
        self._logs.append((msg, style))

    def update_amplitude(self, amp, is_mic=False):
        pass

    def refresh_memory_ui(self):
        pass


def create_mock_config(tmp_path) -> Path:
    config_path = tmp_path / "api_keys.json"
    config_data = {
        "gemini_api_keys": ["test-key-1", "test-key-2"],
        "nvidia_api_key": "test-nvidia-key",
        "voice_name": "Aoede"
    }
    config_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
    return config_path
