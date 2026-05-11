import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Optional


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class Logger:
    _instance = None
    _ui_callback = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._log_dir = Path(__file__).resolve().parent.parent / "logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        
        self._logger = logging.getLogger("Ananya")
        self._logger.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        log_file = self._log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
        
        self._component_loggers = {}

    def set_ui_callback(self, callback):
        self._ui_callback = callback

    def get_logger(self, component: str) -> logging.Logger:
        if component not in self._component_loggers:
            self._component_loggers[component] = self._logger.getChild(component)
        return self._component_loggers[component]

    def debug(self, component: str, msg: str):
        self.get_logger(component).debug(msg)
        self._write_ui(f"[{component}] {msg}")

    def info(self, component: str, msg: str):
        self.get_logger(component).info(msg)
        self._write_ui(f"[{component}] {msg}")

    def warning(self, component: str, msg: str):
        self.get_logger(component).warning(msg)
        self._write_ui(f"[{component}] ⚠️ {msg}")

    def error(self, component: str, msg: str, exc_info: bool = False):
        self.get_logger(component).error(msg, exc_info=exc_info)
        self._write_ui(f"[{component}] ❌ {msg}")
        if exc_info:
            tb = traceback.format_exc()
            self.get_logger(component).debug(tb)

    def _write_ui(self, msg: str):
        if self._ui_callback:
            from PyQt6.QtCore import QMetaObject, Q_ARG, Qt
            try:
                QMetaObject.invokeMethod(
                    self._ui_callback, "add_terminal_log",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, msg),
                    Q_ARG(str, "plain")
                )
            except Exception:
                pass

    def cleanup_old_logs(self, keep_days: int = 7):
        import time
        cutoff = time.time() - (keep_days * 86400)
        for f in self._log_dir.glob("session_*.log"):
            if f.stat().st_mtime < cutoff:
                f.unlink()


LOG = Logger()
