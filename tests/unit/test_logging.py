from core.logging import Logger, LogLevel


class TestLogger:
    def setup_method(self):
        # Reset singleton for each test
        Logger._instance = None

    def test_singleton(self):
        logger1 = Logger()
        logger2 = Logger()
        assert logger1 is logger2

    def test_get_logger(self):
        log = Logger()
        component_logger = log.get_logger("TestComponent")
        assert component_logger.name.endswith("TestComponent")

    def test_log_levels(self):
        assert LogLevel.DEBUG.value == 10
        assert LogLevel.INFO.value == 20
        assert LogLevel.ERROR.value == 40

    def test_initialization(self):
        log = Logger()
        assert log._initialized is True
        assert log._log_dir.exists()

    def test_set_ui_callback(self):
        log = Logger()
        callback = lambda msg, style: None
        log.set_ui_callback(callback)
        assert log._ui_callback is not None

    def test_multiple_components(self):
        log = Logger()
        comp1 = log.get_logger("Component1")
        comp2 = log.get_logger("Component2")
        assert comp1 is not comp2
