#!/usr/bin/env python3
"""
Error Handlers - Circuit breaker pattern and resilience mechanisms

This module provides robust error handling and resilience patterns for pipeline
execution, including circuit breakers, retry mechanisms, and failure recovery.
"""

import time
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Type
from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import threading


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service has recovered


class FailureType(Enum):
    """Types of failures that can occur"""

    SUBPROCESS_ERROR = "subprocess_error"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    VALIDATION_ERROR = "validation_error"
    NETWORK_ERROR = "network_error"
    MEMORY_ERROR = "memory_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class FailureRecord:
    """Record of a failure occurrence"""

    timestamp: datetime
    failure_type: FailureType
    error_message: str
    context: Dict[str, Any]
    retry_count: int = 0
    resolved: bool = False


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout_seconds: int = 60  # Time to wait before trying half-open
    success_threshold: int = 3  # Successful calls needed to close circuit
    timeout_seconds: float = 300.0  # Default timeout for operations
    monitored_exceptions: List[Type[Exception]] = field(
        default_factory=lambda: [
            subprocess.CalledProcessError,
            subprocess.TimeoutExpired,
            FileNotFoundError,
            PermissionError,
            OSError,
        ]
    )


class CircuitBreaker:
    """
    Circuit breaker implementation for preventing cascade failures.

    Based on the circuit breaker pattern research from the PRP, this provides
    automatic failure detection and recovery for subprocess operations.
    """

    def __init__(self, config: CircuitBreakerConfig, name: str = "default"):
        """
        Initialize Circuit Breaker.

        Args:
            config: Circuit breaker configuration
            name: Name for this circuit breaker instance
        """
        self.config = config
        self.name = name
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.failure_records: List[FailureRecord] = []

        # Thread safety
        self.lock = threading.Lock()

        # Logging
        self.logger = logging.getLogger(f"CircuitBreaker.{name}")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result if successful

        Raises:
            CircuitBreakerOpenException: If circuit is open
            Original exception: If function fails
        """
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.logger.info(
                        f"Circuit breaker {self.name}: Attempting reset (HALF_OPEN)"
                    )
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker {self.name} is OPEN. "
                        f"Last failure: {self.last_failure_time}"
                    )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e, {"args": args, "kwargs": kwargs})
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure >= timedelta(
            seconds=self.config.recovery_timeout_seconds
        )

    def _on_success(self):
        """Handle successful operation"""
        with self.lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._reset_circuit()
                    self.logger.info(
                        f"Circuit breaker {self.name}: Reset to CLOSED after {self.success_count} successes"
                    )
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0  # Reset failure count on success

    def _on_failure(self, exception: Exception, context: Dict[str, Any]):
        """Handle failed operation"""
        with self.lock:
            self.failure_count += 1
            self.success_count = 0  # Reset success count on failure
            self.last_failure_time = datetime.now()

            # Record failure
            failure_type = self._classify_failure(exception)
            failure_record = FailureRecord(
                timestamp=self.last_failure_time,
                failure_type=failure_type,
                error_message=str(exception),
                context=context,
            )
            self.failure_records.append(failure_record)

            # Check if we should open the circuit
            if (
                self.state == CircuitState.CLOSED
                and self.failure_count >= self.config.failure_threshold
            ):
                self.state = CircuitState.OPEN
                self.logger.warning(
                    f"Circuit breaker {self.name}: Opened after {self.failure_count} failures. "
                    f"Last error: {exception}"
                )

            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.logger.warning(
                    f"Circuit breaker {self.name}: Re-opened after failure in HALF_OPEN state"
                )

    def _reset_circuit(self):
        """Reset circuit to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def _classify_failure(self, exception: Exception) -> FailureType:
        """Classify the type of failure"""
        if isinstance(exception, subprocess.CalledProcessError):
            return FailureType.SUBPROCESS_ERROR
        elif isinstance(exception, subprocess.TimeoutExpired):
            return FailureType.TIMEOUT_ERROR
        elif isinstance(exception, FileNotFoundError):
            return FailureType.FILE_NOT_FOUND
        elif isinstance(exception, PermissionError):
            return FailureType.PERMISSION_ERROR
        elif isinstance(exception, OSError):
            return FailureType.NETWORK_ERROR
        elif isinstance(exception, MemoryError):
            return FailureType.MEMORY_ERROR
        else:
            return FailureType.UNKNOWN_ERROR

    def get_statistics(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        with self.lock:
            recent_failures = [
                f
                for f in self.failure_records
                if f.timestamp > datetime.now() - timedelta(hours=1)
            ]

            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time.isoformat()
                if self.last_failure_time
                else None,
                "total_failures": len(self.failure_records),
                "recent_failures": len(recent_failures),
                "config": {
                    "failure_threshold": self.config.failure_threshold,
                    "recovery_timeout_seconds": self.config.recovery_timeout_seconds,
                    "success_threshold": self.config.success_threshold,
                    "timeout_seconds": self.config.timeout_seconds,
                },
            }


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""

    pass


@dataclass
class RetryConfig:
    """Configuration for retry mechanism"""

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0
    exponential_backoff: bool = True
    jitter: bool = True
    retryable_exceptions: List[Type[Exception]] = field(
        default_factory=lambda: [subprocess.CalledProcessError, OSError, TimeoutError]
    )


class RetryMechanism:
    """
    Retry mechanism with exponential backoff and jitter.

    Provides configurable retry logic for operations that may fail
    transiently, with intelligent backoff strategies.
    """

    def __init__(self, config: RetryConfig, name: str = "default"):
        """
        Initialize Retry Mechanism.

        Args:
            config: Retry configuration
            name: Name for this retry mechanism instance
        """
        self.config = config
        self.name = name
        self.logger = logging.getLogger(f"RetryMechanism.{name}")

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result if successful

        Raises:
            Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    self.logger.info(
                        f"Retry {self.name}: Succeeded on attempt {attempt + 1}"
                    )
                return result

            except Exception as e:
                last_exception = e

                # Check if this exception is retryable
                if not self._is_retryable(e):
                    self.logger.info(
                        f"Retry {self.name}: Non-retryable exception: {type(e).__name__}"
                    )
                    raise

                # If this is the last attempt, don't delay
                if attempt == self.config.max_attempts - 1:
                    break

                # Calculate delay and sleep
                delay = self._calculate_delay(attempt)
                self.logger.warning(
                    f"Retry {self.name}: Attempt {attempt + 1} failed with {type(e).__name__}: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)

        self.logger.error(
            f"Retry {self.name}: All {self.config.max_attempts} attempts failed"
        )
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"All {self.config.max_attempts} retry attempts failed")

    def _is_retryable(self, exception: Exception) -> bool:
        """Check if exception is retryable"""
        return any(
            isinstance(exception, exc_type)
            for exc_type in self.config.retryable_exceptions
        )

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt"""
        if self.config.exponential_backoff:
            delay = self.config.base_delay_seconds * (2**attempt)
        else:
            delay = self.config.base_delay_seconds

        # Apply maximum delay
        delay = min(delay, self.config.max_delay_seconds)

        # Add jitter if enabled
        if self.config.jitter:
            import random

            jitter = random.uniform(0.0, delay * 0.1)
            delay += jitter

        return delay


class ProcessFailureHandler:
    """
    Comprehensive failure handler for subprocess operations.

    Combines circuit breaker and retry mechanisms for robust subprocess
    execution with intelligent failure handling and recovery.
    """

    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry_mechanism: Optional[RetryMechanism] = None,
        name: str = "default",
    ):
        """
        Initialize Process Failure Handler.

        Args:
            circuit_breaker: Circuit breaker instance (optional)
            retry_mechanism: Retry mechanism instance (optional)
            name: Name for this handler instance
        """
        self.name = name
        self.circuit_breaker = circuit_breaker
        self.retry_mechanism = retry_mechanism
        self.logger = logging.getLogger(f"ProcessFailureHandler.{name}")

        # Statistics
        self.total_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.start_time = datetime.now()

    def execute_subprocess(
        self,
        command: List[str],
        cwd: Optional[Path] = None,
        timeout: Optional[float] = None,
        capture_output: bool = True,
        text: bool = True,
        **subprocess_kwargs,
    ) -> subprocess.CompletedProcess:
        """
        Execute subprocess with failure handling.

        Args:
            command: Command to execute
            cwd: Working directory
            timeout: Timeout in seconds
            capture_output: Whether to capture output
            text: Whether to use text mode
            **subprocess_kwargs: Additional subprocess.run arguments

        Returns:
            CompletedProcess instance

        Raises:
            Various subprocess exceptions if all recovery attempts fail
        """
        self.total_calls += 1

        def run_subprocess():
            return subprocess.run(
                command,
                cwd=cwd,
                timeout=timeout
                or (
                    self.circuit_breaker.config.timeout_seconds
                    if self.circuit_breaker
                    else 300.0
                ),
                capture_output=capture_output,
                text=text,
                **subprocess_kwargs,
            )

        try:
            # Wrap subprocess execution with retry and circuit breaker
            if self.retry_mechanism and self.circuit_breaker:
                # Use both retry and circuit breaker
                result = self.retry_mechanism.execute(
                    lambda: self.circuit_breaker.call(run_subprocess)
                    if self.circuit_breaker
                    else run_subprocess()
                )
            elif self.retry_mechanism:
                # Use only retry mechanism
                result = self.retry_mechanism.execute(run_subprocess)
            elif self.circuit_breaker:
                # Use only circuit breaker
                result = self.circuit_breaker.call(run_subprocess)
            else:
                # Direct execution
                result = run_subprocess()

            # Check return code
            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, command, result.stdout, result.stderr
                )

            self.successful_calls += 1
            self.logger.debug(f"Subprocess succeeded: {' '.join(command)}")
            return result

        except Exception as e:
            self.failed_calls += 1
            self.logger.error(
                f"Subprocess failed after all recovery attempts: {' '.join(command)}. Error: {e}"
            )
            raise

    def get_statistics(self) -> Dict[str, Any]:
        """Get failure handler statistics"""
        uptime = datetime.now() - self.start_time
        success_rate = (
            self.successful_calls / self.total_calls if self.total_calls > 0 else 0.0
        )

        stats = {
            "name": self.name,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "success_rate": success_rate,
            "uptime_seconds": uptime.total_seconds(),
        }

        # Add circuit breaker stats if available
        if self.circuit_breaker:
            stats["circuit_breaker"] = self.circuit_breaker.get_statistics()

        # Add retry mechanism stats if available
        if self.retry_mechanism:
            stats["retry_config"] = {
                "max_attempts": self.retry_mechanism.config.max_attempts,
                "base_delay_seconds": self.retry_mechanism.config.base_delay_seconds,
                "exponential_backoff": self.retry_mechanism.config.exponential_backoff,
            }

        return stats


# Factory functions for creating error handlers


def create_default_circuit_breaker(name: str = "default") -> CircuitBreaker:
    """Create circuit breaker with default configuration"""
    config = CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout_seconds=60,
        success_threshold=3,
        timeout_seconds=300.0,
    )
    return CircuitBreaker(config, name)


def create_default_retry_mechanism(name: str = "default") -> RetryMechanism:
    """Create retry mechanism with default configuration"""
    config = RetryConfig(
        max_attempts=3,
        base_delay_seconds=1.0,
        max_delay_seconds=60.0,
        exponential_backoff=True,
        jitter=True,
    )
    return RetryMechanism(config, name)


def create_process_failure_handler(
    name: str = "default",
    enable_circuit_breaker: bool = True,
    enable_retry: bool = True,
) -> ProcessFailureHandler:
    """Create process failure handler with default components"""
    circuit_breaker = (
        create_default_circuit_breaker(name) if enable_circuit_breaker else None
    )
    retry_mechanism = create_default_retry_mechanism(name) if enable_retry else None

    return ProcessFailureHandler(
        circuit_breaker=circuit_breaker, retry_mechanism=retry_mechanism, name=name
    )
