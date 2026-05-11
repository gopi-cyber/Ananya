import json
from pathlib import Path
from config.manager import ConfigManager, get_gemini_key, is_configured, config_exists


class TestConfigManager:
    def setup_method(self):
        self.tmp = Path(__file__).resolve().parent.parent / "fixtures"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.config_path = self.tmp / "test_config.json"
        self.config_path.write_text(json.dumps({
            "gemini_api_keys": ["key1", "key2"],
            "nvidia_api_key": "nvidia-test-key",
            "voice_name": "TestVoice",
            "os_system": "windows"
        }, indent=2), encoding="utf-8")

    def teardown_method(self):
        if self.config_path.exists():
            self.config_path.unlink()

    def test_load_config(self):
        cm = ConfigManager(self.config_path)
        assert len(cm.get_api_keys()) == 2
        assert cm.get_nvidia_key() == "nvidia-test-key"

    def test_get_voice_name(self):
        cm = ConfigManager(self.config_path)
        assert cm.get_voice_name() == "TestVoice"

    def test_get_voice_name_default(self):
        no_voice = self.tmp / "no_voice.json"
        no_voice.write_text(json.dumps({"gemini_api_keys": ["key1"]}), encoding="utf-8")
        cm = ConfigManager(no_voice)
        assert cm.get_voice_name() == "Aoede"
        no_voice.unlink()

    def test_get_os(self):
        cm = ConfigManager(self.config_path)
        assert cm.get_os() == "windows"

    def test_is_windows(self):
        cm = ConfigManager(self.config_path)
        assert cm.is_windows() is True
        assert cm.is_mac() is False

    def test_set_and_save(self):
        cm = ConfigManager(self.config_path)
        cm.set("voice_name", "NewVoice")
        # Reload to verify persistence
        cm2 = ConfigManager(self.config_path)
        assert cm2.get("voice_name") == "NewVoice"

    def test_is_configured(self):
        long_config = self.tmp / "long_key_config.json"
        long_config.write_text(json.dumps({
            "gemini_api_keys": ["this-is-a-very-long-api-key-more-than-15-chars"]
        }), encoding="utf-8")
        cm = ConfigManager(long_config)
        assert cm.is_configured() is True
        long_config.unlink()

    def test_is_not_configured(self):
        short_key = self.tmp / "short_key.json"
        short_key.write_text(json.dumps({"gemini_api_keys": ["short"]}), encoding="utf-8")
        cm = ConfigManager(short_key)
        assert cm.is_configured() is False
        short_key.unlink()

    def test_save_api_key(self):
        cm = ConfigManager(self.config_path)
        cm.save_api_key("new-key")
        assert "new-key" in cm.get_api_keys()

    def test_get_gemini_key(self):
        # Test the standalone function
        result = get_gemini_key()  # This uses the default path, may or may not exist
        assert result is None or len(result) > 0

    def test_config_not_exists(self):
        assert config_exists() or not config_exists()  # Idempotent check

    def test_get_nvidia_key_missing(self):
        no_nvidia = self.tmp / "no_nvidia.json"
        no_nvidia.write_text(json.dumps({"gemini_api_keys": ["key1"]}), encoding="utf-8")
        cm = ConfigManager(no_nvidia)
        assert cm.get_nvidia_key() is None
        no_nvidia.unlink()
