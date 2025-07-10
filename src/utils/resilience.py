"""Resilience utilities for enhanced error handling and recovery"""

import functools
import time
from enum import Enum
from typing import Any, Callable, Optional, Type, Union

from loguru import logger
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern implementation"""

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.debug("Circuit breaker: Attempting reset (HALF_OPEN)")
            else:
                raise Exception("Circuit breaker is OPEN - too many failures")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.timeout

    def _on_success(self) -> None:
        """Handle successful call"""
        if self.state == CircuitState.HALF_OPEN:
            logger.success("Circuit breaker: Reset successful (CLOSED)")
            self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None

    def _on_failure(self) -> None:
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker: Opening due to {self.failure_count} failures"
                )
                self.state = CircuitState.OPEN


# Global circuit breakers for different operations
browser_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=120.0)
element_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60.0)
move_circuit_breaker = CircuitBreaker(failure_threshold=7, timeout=30.0)


def retry_on_exception(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], tuple] = (Exception,),
    circuit_breaker: Optional[CircuitBreaker] = None,
    fallback_func: Optional[Callable] = None,
) -> Callable:
    """
    Decorator for retrying functions on specific exceptions

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff_factor: Exponential backoff multiplier
        exceptions: Exception types to retry on
        circuit_breaker: Optional circuit breaker to use
        fallback_func: Optional fallback function to call if all retries fail
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    if circuit_breaker:
                        return circuit_breaker.call(func, *args, **kwargs)
                    else:
                        return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__}: {str(e)}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff_factor
                    else:
                        logger.error(
                            f"All {max_retries} retries failed for {func.__name__}: {str(e)}"
                        )

                        # Try fallback if available
                        if fallback_func:
                            logger.info(f"Attempting fallback for {func.__name__}")
                            try:
                                return fallback_func(*args, **kwargs)
                            except Exception as fallback_error:
                                logger.error(f"Fallback also failed: {fallback_error}")

                        raise last_exception

            raise last_exception

        return wrapper

    return decorator


def browser_retry(max_retries: int = 3, delay: float = 2.0) -> Callable:
    """Specialized retry decorator for browser operations"""
    return retry_on_exception(
        max_retries=max_retries,
        delay=delay,
        backoff_factor=1.5,
        exceptions=(
            WebDriverException,
            TimeoutException,
            NoSuchElementException,
            StaleElementReferenceException,
            ElementNotInteractableException,
        ),
        circuit_breaker=browser_circuit_breaker,
    )


def element_retry(max_retries: int = 2, delay: float = 0.5) -> Callable:
    """Specialized retry decorator for element operations"""
    return retry_on_exception(
        max_retries=max_retries,
        delay=delay,
        backoff_factor=2.0,
        exceptions=(
            NoSuchElementException,
            StaleElementReferenceException,
            ElementNotInteractableException,
        ),
        circuit_breaker=element_circuit_breaker,
    )


def move_retry(max_retries: int = 5, delay: float = 0.3) -> Callable:
    """Specialized retry decorator for move operations"""
    return retry_on_exception(
        max_retries=max_retries,
        delay=delay,
        backoff_factor=1.2,
        exceptions=(
            NoSuchElementException,
            StaleElementReferenceException,
            ElementNotInteractableException,
            TimeoutException,
        ),
        circuit_breaker=move_circuit_breaker,
    )


class BrowserRecoveryManager:
    """Manages browser crash detection and recovery"""

    def __init__(self, browser_manager):
        self.browser_manager = browser_manager
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        self.last_recovery_time = None
        self.recovery_cooldown = 300  # 5 minutes

    def is_browser_healthy(self) -> bool:
        """Check if browser is healthy and responsive"""
        try:
            if not self.browser_manager.driver:
                return False

            # Try to get current URL as a health check
            _ = self.browser_manager.driver.current_url
            return True
        except Exception as e:
            logger.warning(f"Browser health check failed: {e}")
            return False

    def can_attempt_recovery(self) -> bool:
        """Check if we can attempt browser recovery"""
        if self.recovery_attempts >= self.max_recovery_attempts:
            logger.error(
                f"Max recovery attempts ({self.max_recovery_attempts}) exceeded"
            )
            return False

        if self.last_recovery_time:
            time_since_last = time.time() - self.last_recovery_time
            if time_since_last < self.recovery_cooldown:
                logger.warning(
                    f"Recovery cooldown active ({time_since_last:.0f}s/{self.recovery_cooldown}s)"
                )
                return False

        return True

    def attempt_browser_recovery(self) -> bool:
        """Attempt to recover from browser crash"""
        if not self.can_attempt_recovery():
            return False

        logger.warning("Attempting browser recovery...")
        self.recovery_attempts += 1
        self.last_recovery_time = time.time()

        try:
            # Close existing driver if possible
            if self.browser_manager.driver:
                try:
                    self.browser_manager.driver.quit()
                except:
                    pass
                self.browser_manager.driver = None

            # Reinitialize browser
            self.browser_manager._setup_driver()

            # Basic health check
            if self.is_browser_healthy():
                logger.success("Browser recovery successful")
                return True
            else:
                logger.error("Browser recovery failed - health check failed")
                return False

        except Exception as e:
            logger.error(f"Browser recovery failed: {e}")
            return False

    def reset_recovery_state(self) -> None:
        """Reset recovery state after successful operation"""
        if self.recovery_attempts > 0:
            logger.debug("Resetting browser recovery state")
            self.recovery_attempts = 0
            self.last_recovery_time = None


def with_browser_recovery(recovery_manager: BrowserRecoveryManager) -> Callable:
    """Decorator that attempts browser recovery on failure"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                recovery_manager.reset_recovery_state()
                return result
            except (WebDriverException, TimeoutException) as e:
                logger.warning(f"Browser operation failed: {e}")

                if recovery_manager.attempt_browser_recovery():
                    logger.info("Retrying operation after browser recovery")
                    try:
                        return func(*args, **kwargs)
                    except Exception as retry_error:
                        logger.error(
                            f"Operation failed even after recovery: {retry_error}"
                        )
                        raise retry_error
                else:
                    logger.error("Browser recovery failed, propagating original error")
                    raise e

        return wrapper

    return decorator


def safe_execute(
    func: Callable, *args, default_return=None, log_errors: bool = True, **kwargs
) -> Any:
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.error(f"Safe execution failed for {func.__name__}: {e}")
        return default_return


def validate_game_state(board, move_number: int, expected_moves: int = None) -> bool:
    """Validate current game state consistency"""
    try:
        # Basic board state validation
        if not board:
            logger.warning("Board state is None")
            return False

        # Check if board is in valid state
        if board.is_game_over():
            logger.debug("Game is over according to board state")
            return True

        # Check move number consistency
        actual_moves = len(board.move_stack)
        if expected_moves and abs(actual_moves - expected_moves) > 1:
            logger.warning(
                f"Move count mismatch: expected {expected_moves}, got {actual_moves}"
            )
            return False

        # Check for illegal positions
        if board.is_check() and board.is_checkmate():
            logger.debug("Valid checkmate position")
            return True

        if board.is_stalemate():
            logger.debug("Valid stalemate position")
            return True

        # Check if we have legal moves
        if not list(board.legal_moves):
            logger.warning("No legal moves available but game not over")
            return False

        return True

    except Exception as e:
        logger.error(f"Game state validation failed: {e}")
        return False
