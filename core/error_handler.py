import traceback
from typing import Callable, Optional, Tuple
from core.logging import LOG


class ErrorHandler:
    def __init__(self, component: str):
        self.component = component
        self._logger = LOG.get_logger(component)

    def wrap(self, func: Callable, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self._logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise

    async def wrap_async(self, func: Callable, *args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            self._logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            raise

    def safe_call(self, func: Callable, default=None, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self._logger.warning(f"Safe call failed for {func.__name__}: {e}")
            return default

    async def safe_call_async(self, func: Callable, default=None, *args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            self._logger.warning(f"Safe async call failed for {func.__name__}: {e}")
            return default

    def format_error(self, error: Exception, include_traceback: bool = False) -> str:
        if include_traceback:
            return f"{error}\n{traceback.format_exc()}"
        return str(error)[:200]


class RetryConfig:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0,
                 max_delay: float = 30.0, backoff_factor: float = 2.0,
                 retryable_errors: Optional[Tuple[Exception, ...]] = None):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.retryable_errors = retryable_errors or (Exception,)


async def retry_async(func: Callable, config: RetryConfig = None,
                      *args, **kwargs) -> Tuple[bool, any]:
    """Retry an async function with exponential backoff."""
    if config is None:
        config = RetryConfig()

    import asyncio
    last_error = None

    for attempt in range(config.max_retries):
        try:
            result = await func(*args, **kwargs)
            return True, result
        except config.retryable_errors as e:
            last_error = e
            if attempt < config.max_retries - 1:
                delay = min(config.base_delay * (config.backoff_factor ** attempt),
                           config.max_delay)
                LOG.get_logger("Retry").warning(
                    f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)

    return False, last_error
