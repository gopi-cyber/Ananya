import os
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.text.font.db.warning=false;qt.qpa.window.warning=false"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

import warnings
warnings.filterwarnings("ignore")

import sys
import asyncio
import threading
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from UI.dashboard import DashboardUI
from core.logging import LOG
from core.key_manager import KeyManager
from core.ue_relay import UnrealEngineRelay
from core.audio_manager import AudioManager
from core.tool_executor import ToolExecutor
from core.session_manager import SessionManager
from core.orchestrator import Orchestrator


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
API_CONFIG_PATH = BASE_DIR / "config" / "api_keys.json"
PROMPT_PATH = BASE_DIR / "core" / "prompt.txt"

SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHANNELS = 1
CHUNK_SIZE = 1024


class TerminalUI:
    def __init__(self):
        self.muted = False
        self.current_file = None
        self.on_text_command = None
        self.on_file_selected_callback = None
        self.dashboard = None
        self.app = None

    def init_gui(self):
        self.dashboard = DashboardUI()
        if self.on_text_command:
            self.dashboard.chat_widget.command_entered.connect(self.on_text_command)
            self.dashboard.memory_widget.command_entered.connect(self.on_text_command)

        if self.on_file_selected_callback:
            self.dashboard.chat_widget.file_selected.connect(self.on_file_selected_callback)

        self.dashboard.show()

    def set_state(self, state):
        LOG.info("UI", f"State: {state}")
        if self.dashboard:
            self.dashboard.set_status(state)

    def write_log(self, msg, style="plain"):
        LOG.info("UI", msg)
        if self.dashboard:
            from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
            QMetaObject.invokeMethod(self.dashboard, "add_terminal_log",
                                   Qt.ConnectionType.QueuedConnection,
                                   Q_ARG(str, msg),
                                   Q_ARG(str, style))

    def update_amplitude(self, amp, is_mic=False):
        if self.dashboard:
            from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
            QMetaObject.invokeMethod(self.dashboard, "update_audio_amplitude",
                                   Qt.ConnectionType.QueuedConnection,
                                   Q_ARG(float, amp),
                                   Q_ARG(bool, is_mic))

    def wait_for_api_key(self):
        pass

    def start_input_loop(self):
        def _loop():
            while True:
                try:
                    cmd = input()
                    if cmd and self.on_text_command:
                        self.on_text_command(cmd)
                except EOFError:
                    break
        threading.Thread(target=_loop, daemon=True).start()

    def refresh_memory_ui(self):
        if self.dashboard:
            from memory.memory_manager import load_memory
            memory = load_memory()
            from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
            QMetaObject.invokeMethod(self.dashboard, "refresh_memory_ui",
                                   Qt.ConnectionType.QueuedConnection,
                                   Q_ARG(dict, memory))


def init_components(ui):
    key_manager = KeyManager(API_CONFIG_PATH)
    ue_relay = UnrealEngineRelay(host="0.0.0.0", port=8080)
    audio_manager = AudioManager(
        send_sample_rate=SEND_SAMPLE_RATE,
        receive_sample_rate=RECEIVE_SAMPLE_RATE,
        channels=CHANNELS,
        chunk_size=CHUNK_SIZE
    )
    audio_manager.set_amplitude_callback(ui.update_amplitude)
    audio_manager.set_ue_broadcast_callback(ue_relay.broadcast)

    from core.model_registry import init_registry
    registry = init_registry(API_CONFIG_PATH)
    orchestrator = Orchestrator(ui)

    tool_executor = ToolExecutor(ui, orchestrator, speak_callback=None)

    session_manager = SessionManager(
        ui=ui,
        key_manager=key_manager,
        audio_manager=audio_manager,
        tool_executor=tool_executor,
        ue_relay=ue_relay,
        config_path=API_CONFIG_PATH,
        prompt_path=PROMPT_PATH
    )

    # Wire up speak callback now that we have session_manager
    tool_executor.speak = session_manager.send_text

    # Wire up UI callbacks
    ui.on_text_command = session_manager.on_text_command
    ui.on_file_selected_callback = session_manager.on_file_selected

    # Set logging UI callback
    LOG.set_ui_callback(ui.dashboard)

    # Hot-reload connection for API Settings saved
    def reload_config():
        LOG.info("Main", "Settings changed! Hot-reloading API keys...")
        key_manager.load_keys()
        registry.key_manager.load_keys()
        ui.write_log("SYS: Settings updated successfully. Real-time keys reloaded.")

    ui.dashboard.settings_widget.settings_saved.connect(reload_config)

    return {
        "key_manager": key_manager,
        "ue_relay": ue_relay,
        "audio_manager": audio_manager,
        "orchestrator": orchestrator,
        "tool_executor": tool_executor,
        "session_manager": session_manager,
    }


def main():
    LOG.info("Main", "Starting Ananya AI...")

    app = QApplication(sys.argv)
    ui = TerminalUI()
    ui.app = app
    ui.init_gui()
    ui.start_input_loop()

    components = init_components(ui)
    session_manager = components["session_manager"]
    ue_relay = components["ue_relay"]

    # Start UE5 relay
    ue_relay.start()

    def start_ai():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(session_manager.run())
        except Exception as e:
            LOG.error("Main", f"AI Logic Error: {e}", exc_info=True)

    ai_thread = threading.Thread(target=start_ai, daemon=True)
    ai_thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
