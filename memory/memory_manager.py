import json
from datetime import datetime
from threading import Lock
from pathlib import Path
import sys


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR         = get_base_dir()
MEMORY_PATH      = BASE_DIR / "memory" / "long_term.json"
_lock            = Lock()
MAX_VALUE_LENGTH = 380
MEMORY_MAX_CHARS = 2200


def _empty_memory() -> dict:
    return {
        "identity":      {},
        "preferences":   {},
        "projects":      {},
        "relationships": {},
        "wishes":        {},
        "notes":         {},
        "mood_history":  [],
    }


def track_mood(mood: str, context: str = ""):
    memory = load_memory()
    entry = {"mood": mood, "context": context, "time": datetime.now().isoformat()}
    if "mood_history" not in memory:
        memory["mood_history"] = []
    memory["mood_history"].append(entry)
    memory["mood_history"] = memory["mood_history"][-10:]
    save_memory(memory)


def get_recent_mood() -> str | None:
    memory = load_memory()
    history = memory.get("mood_history", [])
    if not history:
        return None
    return history[-1].get("mood")


def load_memory() -> dict:
    if not MEMORY_PATH.exists():
        return _empty_memory()
    with _lock:
        try:
            data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = _empty_memory()
                for key in base:
                    if key not in data:
                        data[key] = [] if key == "mood_history" else {}
                if not isinstance(data.get("mood_history"), list):
                    data["mood_history"] = []
                return data
            return _empty_memory()
        except Exception as e:
            print(f"[Memory] Load error: {e}")
            return _empty_memory()


def _all_entries(memory: dict) -> list[tuple]:
    entries = []
    for cat, items in memory.items():
        if not isinstance(items, dict):
            continue
        for key, entry in items.items():
            if isinstance(entry, dict) and "value" in entry:
                entries.append((cat, key, entry))
    return entries


def _trim_to_limit(memory: dict) -> dict:
    if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
        return memory
    entries = _all_entries(memory)
    entries.sort(key=lambda t: t[2].get("updated", "0000-00-00"))
    for cat, key, _ in entries:
        if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
            break
        del memory[cat][key]
        print(f"[Memory] Trimmed {cat}/{key}")
    return memory


def save_memory(memory: dict) -> None:
    if not isinstance(memory, dict):
        return
    memory = _trim_to_limit(memory)
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        MEMORY_PATH.write_text(
            json.dumps(memory, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _truncate_value(val: str) -> str:
    if isinstance(val, str) and len(val) > MAX_VALUE_LENGTH:
        return val[:MAX_VALUE_LENGTH].rstrip() + "..."
    return val


def _recursive_update(target: dict, updates: dict) -> bool:
    changed = False
    for key, value in updates.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, dict) and "value" not in value:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
                changed = True
            if _recursive_update(target[key], value):
                changed = True
        else:
            new_val  = _truncate_value(str(value["value"] if isinstance(value, dict) else value))
            now_str  = datetime.now().strftime("%Y-%m-%d")
            entry    = {"value": new_val, "updated": now_str}
            existing = target.get(key, {})
            if not isinstance(existing, dict) or existing.get("value") != new_val:
                target[key] = entry
                changed = True
    return changed


def update_memory(memory_update: dict) -> dict:
    if not isinstance(memory_update, dict) or not memory_update:
        return load_memory()
    memory = load_memory()
    if _recursive_update(memory, memory_update):
        save_memory(memory)
        print(f"[Memory] Saved: {list(memory_update.keys())}")
    return memory


def format_memory_for_prompt(memory: dict | None) -> str:
    if not memory:
        return ""

    sections = []

    identity = memory.get("identity", {})
    if identity:
        known = []
        for key, entry in identity.items():
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                known.append(f"- {key.replace('_', ' ').title()}: {val}")
        if known:
            sections.append("I know this person:\n" + "\n".join(known))

    prefs = memory.get("preferences", {})
    if prefs:
        items = []
        for key, entry in list(prefs.items())[:15]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                items.append(f"  - {key.replace('_', ' ').title()}: {val}")
        if items:
            sections.append("Things they like:\n" + "\n".join(items))

    projects = memory.get("projects", {})
    if projects:
        items = []
        for key, entry in list(projects.items())[:10]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                items.append(f"  - {key.replace('_', ' ').title()}: {val}")
        if items:
            sections.append("What they're working on:\n" + "\n".join(items))

    rels = memory.get("relationships", {})
    if rels:
        items = []
        for key, entry in list(rels.items())[:10]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                items.append(f"  - {key.replace('_', ' ').title()}: {val}")
        if items:
            sections.append("People in their life:\n" + "\n".join(items))

    wishes = memory.get("wishes", {})
    if wishes:
        items = []
        for key, entry in list(wishes.items())[:8]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                items.append(f"  - {key.replace('_', ' ').title()}: {val}")
        if items:
            sections.append("Things they want:\n" + "\n".join(items))

    mood_history = memory.get("mood_history", [])
    if mood_history:
        recent = mood_history[-1]
        mood_time = recent.get("time", "")[:10]
        sections.append(
            f"Mood (last interaction): {recent.get('mood', 'neutral')} "
            f"on {mood_time}"
        )

    notes = memory.get("notes", {})
    if notes:
        items = []
        for key, entry in list(notes.items())[:10]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                items.append(f"  - {key}: {val}")
        if items:
            sections.append("Other things to remember:\n" + "\n".join(items))

    if not sections:
        return ""

    result = "[Context about the person I'm talking to — use naturally]\n" + "\n\n".join(sections)
    if len(result) > 2000:
        result = result[:1997] + "..."

    return result + "\n"


def remember(key: str, value: str, category: str = "notes") -> str:
    valid = {"identity", "preferences", "projects", "relationships", "wishes", "notes"}
    if category not in valid:
        category = "notes"
    update_memory({category: {key: {"value": value}}})
    return f"Remembered: {category}/{key} = {value}"


def forget(key: str, category: str = "notes") -> str:
    memory = load_memory()
    cat    = memory.get(category, {})
    if key in cat:
        del cat[key]
        memory[category] = cat
        save_memory(memory)
        return f"Forgotten: {category}/{key}"
    return f"Not found: {category}/{key}"


forget_memory = forget
