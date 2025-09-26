#!/usr/bin/env python3
"""
Basic smoke tests for error_handlers module
"""

import pytest
import time
import subprocess
from unittest.mock import Mock

from orchestrator.error_handlers import (
    CircuitState,
    FailureType,
    CircuitBreakerConfig,
    RetryConfig,
    CircuitBreaker,
    CircuitBreakerOpenException,
    RetryMechanism,
    ProcessFailureHandler,
    create_default_circuit_breaker,
    create_default_retry_mechanism,
    create_process_failure_handler
)


def test_circuit_state_enum():
    """Test CircuitState enum values"""
    assert CircuitState.CLOSED.value == "closed"
    assert CircuitState.OPEN.value == "open"
    assert CircuitState.HALF_OPEN.value == "half_open"


def test_failure_type_enum():
    """Test FailureType enum values"""
    assert FailureType.SUBPROCESS_ERROR.value == "subprocess_error"
    assert FailureType.FILE_NOT_FOUND.value == "file_not_found"
    assert FailureType.TIMEOUT_ERROR.value == "timeout_error"


def test_circuit_breaker_config_creation():
    """Test CircuitBreakerConfig dataclass creation"""
    config = CircuitBreakerConfig()

    assert config.failure_threshold == 5
    assert config.recovery_timeout_seconds == 60
    assert config.success_threshold == 3
    assert config.timeout_seconds == 300.0
    assert len(config.monitored_exceptions) > 0
    assert subprocess.CalledProcessError in config.monitored_exceptions


def test_retry_config_creation():
    """Test RetryConfig dataclass creation"""
    config = RetryConfig()

    assert config.max_attempts == 3
    assert config.base_delay_seconds == 1.0
    assert config.max_delay_seconds == 60.0
    assert config.exponential_backoff == True
    assert config.jitter == True
    assert len(config.retryable_exceptions) > 0


def test_circuit_breaker_creation():
    """Test CircuitBreaker instantiation"""
    config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=30)
    breaker = CircuitBreaker(config, name="test_breaker")

    assert breaker.name == "test_breaker"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0
    assert breaker.success_count == 0
    assert breaker.last_failure_time is None


def test_circuit_breaker_successful_call():
    """Test circuit breaker with successful function call"""
    config = CircuitBreakerConfig(failure_threshold=2)
    breaker = CircuitBreaker(config, name="test")

    def successful_function():
        return "success"

    # Should work normally when circuit is closed
    result = breaker.call(successful_function)
    assert result == "success"
    assert breaker.state == CircuitState.CLOSED
    assert breaker.failure_count == 0


def test_circuit_breaker_failure_handling():
    """Test circuit breaker failure detection"""
    config = CircuitBreakerConfig(failure_threshold=2)
    breaker = CircuitBreaker(config, name="test")

    def failing_function():
        raise subprocess.CalledProcessError(1, ["test"])

    # First failure
    with pytest.raises(subprocess.CalledProcessError):
        breaker.call(failing_function)

    assert breaker.failure_count == 1
    assert breaker.state == CircuitState.CLOSED

    # Second failure should open circuit
    with pytest.raises(subprocess.CalledProcessError):
        breaker.call(failing_function)

    assert breaker.failure_count == 2
    assert breaker.state == CircuitState.OPEN

    # Third call should fail fast
    with pytest.raises(CircuitBreakerOpenException):
        breaker.call(failing_function)


def test_circuit_breaker_statistics():
    """Test circuit breaker statistics"""
    config = CircuitBreakerConfig()
    breaker = CircuitBreaker(config, name="test_stats")

    stats = breaker.get_statistics()

    assert stats["name"] == "test_stats"
    assert stats["state"] == "closed"
    assert stats["failure_count"] == 0
    assert stats["success_count"] == 0
    assert stats["last_failure_time"] is None
    assert "config" in stats
    assert stats["config"]["failure_threshold"] == config.failure_threshold


def test_retry_mechanism_creation():
    """Test RetryMechanism instantiation"""
    config = RetryConfig(max_attempts=2, base_delay_seconds=0.1)
    retry = RetryMechanism(config, name="test_retry")

    assert retry.name == "test_retry"
    assert retry.config.max_attempts == 2
    assert retry.config.base_delay_seconds == 0.1


def test_retry_mechanism_successful_call():
    """Test retry mechanism with successful function"""
    config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
    retry = RetryMechanism(config, name="test")

    def successful_function():
        return "success"

    result = retry.execute(successful_function)
    assert result == "success"


def test_retry_mechanism_eventual_success():
    """Test retry mechanism with eventual success"""
    config = RetryConfig(max_attempts=3, base_delay_seconds=0.01)
    retry = RetryMechanism(config, name="test")

    call_count = 0

    def eventually_successful_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise subprocess.CalledProcessError(1, ["test"])
        return "success"

    result = retry.execute(eventually_successful_function)
    assert result == "success"
    assert call_count == 2


def test_retry_mechanism_all_attempts_fail():
    """Test retry mechanism when all attempts fail"""
    config = RetryConfig(max_attempts=2, base_delay_seconds=0.01)
    retry = RetryMechanism(config, name="test")

    def always_failing_function():
        raise subprocess.CalledProcessError(1, ["test"])

    with pytest.raises(subprocess.CalledProcessError):
        retry.execute(always_failing_function)


def test_process_failure_handler_creation():
    """Test ProcessFailureHandler instantiation"""
    handler = ProcessFailureHandler(name="test_handler")

    assert handler.name == "test_handler"
    assert handler.total_calls == 0
    assert handler.successful_calls == 0
    assert handler.failed_calls == 0


def test_process_failure_handler_statistics():
    """Test ProcessFailureHandler statistics"""
    handler = ProcessFailureHandler(name="test")

    stats = handler.get_statistics()

    assert stats["name"] == "test"
    assert stats["total_calls"] == 0
    assert stats["successful_calls"] == 0
    assert stats["failed_calls"] == 0
    assert stats["success_rate"] == 0.0
    assert "uptime_seconds" in stats


def test_factory_functions():
    """Test factory functions for creating components"""
    # Test circuit breaker factory
    breaker = create_default_circuit_breaker("test_cb")
    assert breaker.name == "test_cb"
    assert isinstance(breaker.config, CircuitBreakerConfig)

    # Test retry mechanism factory
    retry = create_default_retry_mechanism("test_retry")
    assert retry.name == "test_retry"
    assert isinstance(retry.config, RetryConfig)

    # Test process failure handler factory
    handler = create_process_failure_handler("test_handler")
    assert handler.name == "test_handler"
    assert handler.circuit_breaker is not None
    assert handler.retry_mechanism is not None

    # Test with disabled components
    handler_no_components = create_process_failure_handler(
        "test_minimal", enable_circuit_breaker=False, enable_retry=False
    )
    assert handler_no_components.circuit_breaker is None
    assert handler_no_components.retry_mechanism is None


def test_delay_calculation():
    """Test retry delay calculation"""
    config = RetryConfig(
        base_delay_seconds=1.0,
        max_delay_seconds=10.0,
        exponential_backoff=True,
        jitter=False  # Disable jitter for predictable testing
    )
    retry = RetryMechanism(config, name="test")

    # Test exponential backoff
    delay_0 = retry._calculate_delay(0)
    delay_1 = retry._calculate_delay(1)
    delay_2 = retry._calculate_delay(2)

    assert delay_0 == 1.0  # base_delay * 2^0
    assert delay_1 == 2.0  # base_delay * 2^1
    assert delay_2 == 4.0  # base_delay * 2^2

    # Test max delay cap
    delay_large = retry._calculate_delay(10)
    assert delay_large == 10.0  # Should be capped at max_delay_seconds


def test_failure_classification():
    """Test exception classification in circuit breaker"""
    config = CircuitBreakerConfig()
    breaker = CircuitBreaker(config, name="test")

    # Test different exception types
    subprocess_error = subprocess.CalledProcessError(1, ["test"])
    assert breaker._classify_failure(subprocess_error) == FailureType.SUBPROCESS_ERROR

    timeout_error = subprocess.TimeoutExpired(["test"], 30)
    assert breaker._classify_failure(timeout_error) == FailureType.TIMEOUT_ERROR

    file_error = FileNotFoundError("File not found")
    assert breaker._classify_failure(file_error) == FailureType.FILE_NOT_FOUND

    permission_error = PermissionError("Permission denied")
    assert breaker._classify_failure(permission_error) == FailureType.PERMISSION_ERROR

    unknown_error = ValueError("Some other error")
    assert breaker._classify_failure(unknown_error) == FailureType.UNKNOWN_ERROR