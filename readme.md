# Ananya AI
### The Ultimate Cross-Platform Personal AI Assistant

A real-time voice AI that can hear, see, understand, and control your computer * on any OS. Local execution. Zero subscriptions.

---

## Capabilities

| Feature | Description |
|---|---|
| Real-time Voice | Ultra-low latency conversation in any language |
| System Control | Launch apps, manage files, execute terminal commands |
| Autonomous Tasks | High-level planning for complex, multi-step goals |
| Visual Awareness | Real-time screen processing and webcam vision |
| Persistent Memory | Deeply remembers your projects, preferences, and personal context |
| Hybrid Input | Seamlessly switch between keyboard typing and voice commands |

---

## Quick Start

```bash
pip install -r requirements.txt
playwright install
python main.py
```

---

## Requirements

| Requirement | Details |
|---|---|
| **OS** | Windows 10/11, macOS, or Linux |
| **Python** | 3.11 or 3.12 |
| **Microphone** | Required for voice interaction |
| **API Key** | Free Gemini API key |

---

## Project Structure

```
Ananya/
  main.py                  Entry point (orchestrates all components)
  core/
    logging.py             Centralized structured logging system
    key_manager.py         API key management with rotation and failure tracking
    audio_manager.py       Audio I/O (mic input, speaker output, VAD)
    session_manager.py     AI session lifecycle and message handling
    tool_executor.py       Executes tool calls from the AI model (22 tools)
    ue_relay.py            Unreal Engine 5 TCP socket relay for lipsync
    orchestrator.py        Multi-model task delegation with retry and fallback
    model_registry.py      Model definitions and client factory
    error_handler.py       Error handling utilities with retry/backoff
    prompt.txt             System prompt defining AI behavior
  actions/                 18+ capability modules (browser, files, code, etc.)
  agent/                   Autonomous task planning and execution
  config/
    __init__.py            OS detection helpers
    manager.py             Configuration management with persistence
    api_keys.json          API key storage (gitignored)
  interfaces/
    action.py              Base action interface and ActionResult
    action_adapter.py      Backward-compatible action wrapping
    memory.py              Memory storage interface
    config.py              Configuration interface
    ui.py                  UI callback interface
  memory/                  Long-term memory storage and retrieval
  UI/                      PyQt6-based user interface
    dashboard.py           Main window with tactical HUD design
    widget.py              UI widgets (Chat, Memory, Settings, Camera)
    orc_reactor.py         Visual audio reactor
    button.py              Custom UI buttons
  tests/
    conftest.py            Shared test fixtures and mocks
    unit/                  Unit tests for core modules
    integration/           Integration tests for memory/actions
```

---

## Architecture

The system follows a layered architecture:

```
main.py (Entry Point)
  |
  SessionManager (AI session lifecycle)
    |-- AudioManager (Mic/Speaker I/O)
    |-- ToolExecutor (Tool call dispatch)
    |-- KeyManager (API key rotation)
    |-- UERelay (Unreal Engine integration)
    |-- Orchestrator (Multi-model delegation)
        |-- ModelRegistry (Model selection)
```

All components use the centralized logging system (`core/logging.py`) for structured, file + console output.

## Running Tests

```bash
python -m pytest tests/ -v
```

## Configuration

Edit `config/api_keys.json`:
```json
{
  "gemini_api_keys": ["key1", "key2"],
  "nvidia_api_key": "optional-nvidia-key",
  "voice_name": "Aoede"
}
```
