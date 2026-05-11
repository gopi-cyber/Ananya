import asyncio
from core.error_handler import ErrorHandler, RetryConfig, retry_async


class TestErrorHandler:
    def setup_method(self):
        self.handler = ErrorHandler("TestComponent")

    def test_safe_call_success(self):
        result = self.handler.safe_call(lambda x: x * 2, default=0, x=5)
        assert result == 10

    def test_safe_call_failure(self):
        def failing():
            raise ValueError("test error")
        result = self.handler.safe_call(failing, default="fallback")
        assert result == "fallback"

    def test_safe_call_async_success(self):
        async def success():
            return "ok"

        result = asyncio.run(self.handler.safe_call_async(success, default="fail"))
        assert result == "ok"

    def test_safe_call_async_failure(self):
        async def failing():
            raise ValueError("test error")

        result = asyncio.run(self.handler.safe_call_async(failing, default="fallback"))
        assert result == "fallback"

    def test_format_error(self):
        error = ValueError("something went wrong")
        formatted = self.handler.format_error(error)
        assert "something went wrong" in formatted
        assert len(formatted) <= 200

    def test_format_error_with_traceback(self):
        try:
            raise ValueError("detailed error")
        except ValueError as e:
            formatted = self.handler.format_error(e, include_traceback=True)
            assert "detailed error" in formatted
            assert "Traceback" in formatted

    def test_retry_config_defaults(self):
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.backoff_factor == 2.0


class TestRetryAsync:
    def test_retry_success(self):
        async def succeed():
            return "success"

        result = asyncio.run(retry_async(succeed))
        assert result == (True, "success")

    def test_retry_eventually_fails(self):
        call_count = 0

        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"attempt {call_count}")

        config = RetryConfig(max_retries=3, base_delay=0.01)
        success, last_error = asyncio.run(retry_async(always_fail, config))
        assert success is False
        assert call_count == 3
        assert isinstance(last_error, ValueError)

    def test_retry_succeeds_on_last_attempt(self):
        call_count = 0

        async def fail_then_succeed():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"attempt {call_count}")
            return "finally success"

        config = RetryConfig(max_retries=5, base_delay=0.01)
        success, result = asyncio.run(retry_async(fail_then_succeed, config))
        assert success is True
        assert result == "finally success"
        assert call_count == 3

    def test_retry_custom_error_types(self):
        class CustomError(Exception):
            pass

        async def raise_custom():
            raise CustomError("custom")

        config = RetryConfig(max_retries=2, base_delay=0.01,
                             retryable_errors=(CustomError,))
        success, error = asyncio.run(retry_async(raise_custom, config))
        assert success is False
        assert isinstance(error, CustomError)
