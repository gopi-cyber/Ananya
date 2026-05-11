import json
from pathlib import Path
from memory.memory_manager import (
    load_memory, save_memory, update_memory,
    format_memory_for_prompt, remember, forget
)


class TestMemoryManager:
    def setup_method(self):
        self.tmp = Path(__file__).resolve().parent.parent / "fixtures"
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.memory_path = self.tmp / "test_memory.json"
        self._orig_path = None

        # Patch MEMORY_PATH
        import memory.memory_manager as mm
        self._orig_path = mm.MEMORY_PATH
        mm.MEMORY_PATH = self.memory_path

    def teardown_method(self):
        import memory.memory_manager as mm
        mm.MEMORY_PATH = self._orig_path
        if self.memory_path.exists():
            self.memory_path.unlink()

    def test_load_empty_memory(self):
        mem = load_memory()
        assert isinstance(mem, dict)
        assert "identity" in mem
        assert "preferences" in mem
        assert "projects" in mem

    def test_update_and_load_memory(self):
        update_memory({
            "identity": {"name": {"value": "Test User"}},
            "preferences": {"color": {"value": "blue"}}
        })
        mem = load_memory()
        assert mem["identity"]["name"]["value"] == "Test User"
        assert mem["preferences"]["color"]["value"] == "blue"

    def test_save_memory(self):
        mem = load_memory()
        mem["notes"] = {"test_key": {"value": "test_value", "updated": "2026-01-01"}}
        save_memory(memory=mem)
        loaded = load_memory()
        assert loaded["notes"]["test_key"]["value"] == "test_value"

    def test_format_memory_for_prompt(self):
        update_memory({
            "identity": {"name": {"value": "Alice"}},
            "preferences": {"food": {"value": "pizza"}},
            "projects": {"app": {"value": "building Ananya"}}
        })
        formatted = format_memory_for_prompt(load_memory())
        assert "Alice" in formatted
        assert "pizza" in formatted
        assert "building Ananya" in formatted

    def test_remember_and_forget(self):
        result = remember("test_key", "test_value", "notes")
        assert "Remembered" in result
        mem = load_memory()
        assert mem["notes"]["test_key"]["value"] == "test_value"

        result = forget("test_key", "notes")
        assert "Forgotten" in result
        mem = load_memory()
        assert "test_key" not in mem.get("notes", {})

    def test_format_empty_memory(self):
        result = format_memory_for_prompt(None)
        assert result == ""

        result = format_memory_for_prompt({})
        assert result == ""

    def test_memory_trimming(self):
        for i in range(100):
            update_memory({
                "notes": {f"key_{i}": {"value": "x" * 100}}
            })
        mem = load_memory()
        total = len(json.dumps(mem, ensure_ascii=False))
        from memory.memory_manager import MEMORY_MAX_CHARS
        assert total <= MEMORY_MAX_CHARS + 500

    def test_track_and_get_mood(self):
        from memory.memory_manager import track_mood, get_recent_mood
        track_mood("happy", "user said something nice")
        assert get_recent_mood() == "happy"

    def test_get_mood_empty(self):
        from memory.memory_manager import get_recent_mood
        import memory.memory_manager as mm
        old = mm.MEMORY_PATH
        test_path = Path(__file__).resolve().parent.parent / "fixtures" / "empty_mood_test.json"
        if test_path.exists():
            test_path.unlink()
        mm.MEMORY_PATH = test_path
        try:
            assert get_recent_mood() is None
        finally:
            mm.MEMORY_PATH = old
            if test_path.exists():
                test_path.unlink()

    def test_mood_in_format(self):
        from memory.memory_manager import track_mood, format_memory_for_prompt, load_memory
        track_mood("frustrated", "something broke")
        formatted = format_memory_for_prompt(load_memory())
        assert "frustrated" in formatted
