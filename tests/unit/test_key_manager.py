import json
import time
from pathlib import Path
from core.key_manager import KeyManager


class TestKeyManager:
    def setup_method(self):
        self.tmp = Path(__file__).resolve().parent.parent / "fixtures"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.config_path = self.tmp / "test_keys.json"
        self.config_path.write_text(json.dumps({
            "gemini_api_keys": ["key1", "key2", "key3"],
            "nvidia_api_key": "nvidia-key"
        }, indent=2), encoding="utf-8")

    def teardown_method(self):
        if self.config_path.exists():
            self.config_path.unlink()

    def test_load_keys(self):
        km = KeyManager(self.config_path)
        assert len(km.keys) == 3
        assert km.nvidia_key == "nvidia-key"

    def test_load_keys_fallback_single_key(self):
        single_path = self.tmp / "single_key.json"
        single_path.write_text(json.dumps({"gemini_api_key": "single-key"}, indent=2), encoding="utf-8")
        km = KeyManager(single_path)
        assert len(km.keys) == 1
        assert km.keys[0] == "single-key"
        single_path.unlink()

    def test_get_key(self):
        km = KeyManager(self.config_path)
        key = km.get_key()
        assert key in km.keys

    def test_get_key_no_keys(self):
        empty_path = self.tmp / "empty.json"
        empty_path.write_text(json.dumps({}), encoding="utf-8")
        km = KeyManager(empty_path)
        assert km.get_key() == ""
        empty_path.unlink()

    def test_rotate(self):
        km = KeyManager(self.config_path)
        initial_index = km.current_index
        km.rotate()
        assert km.current_index == (initial_index + 1) % len(km.keys)

    def test_rotate_single_key(self):
        single_path = self.tmp / "single.json"
        single_path.write_text(json.dumps({"gemini_api_keys": ["only-key"]}), encoding="utf-8")
        km = KeyManager(single_path)
        assert km.rotate() is False
        single_path.unlink()

    def test_mark_key_failed(self):
        km = KeyManager(self.config_path)
        km.mark_key_failed("key1")
        assert "key1" in km.failed_keys

    def test_get_active_keys_excludes_failed(self):
        km = KeyManager(self.config_path)
        km.mark_key_failed("key1")
        active = km.get_active_keys()
        assert "key1" not in active
        assert len(active) == 2

    def test_get_active_keys_all_failed_resets(self):
        km = KeyManager(self.config_path)
        for k in km.keys:
            km.mark_key_failed(k)
        active = km.get_active_keys()
        assert len(active) == 3  # Should reset when all failed

    def test_get_active_keys_with_cooldown(self):
        km = KeyManager(self.config_path)
        km.failed_keys["key1"] = time.time() - 400  # 400 seconds ago (cooldown is 300)
        active = km.get_active_keys()
        assert "key1" in active  # Should be restored after cooldown

    def test_mark_key_failed_nonexistent(self):
        km = KeyManager(self.config_path)
        km.mark_key_failed("nonexistent-key")
        assert "nonexistent-key" not in km.failed_keys

    def test_get_nvidia_key(self):
        km = KeyManager(self.config_path)
        assert km.get_nvidia_key() == "nvidia-key"

    def test_get_nvidia_key_missing(self):
        no_nvidia = self.tmp / "no_nvidia.json"
        no_nvidia.write_text(json.dumps({"gemini_api_keys": ["key1"]}), encoding="utf-8")
        km = KeyManager(no_nvidia)
        assert km.get_nvidia_key() == ""
        no_nvidia.unlink()
