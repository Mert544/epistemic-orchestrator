from __future__ import annotations

import time

import pytest

from app.utils.error_handling import (
    ApexError,
    ApexTimeoutError,
    ErrorCollector,
    PatchError,
    SafetyError,
    ValidationError,
    safe_execute,
    with_error_handling,
    with_timeout,
)


def test_with_error_handling_success():
    @with_error_handling(default_return="fallback")
    def success():
        return "ok"

    assert success() == "ok"


def test_with_error_handling_failure():
    @with_error_handling(default_return="fallback")
    def fail():
        raise ValueError("boom")

    assert fail() == "fallback"


def test_with_error_handling_reraise():
    @with_error_handling(reraise=True)
    def fail():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        fail()


def test_with_timeout_success():
    @with_timeout(1.0)
    def fast():
        return 42

    assert fast() == 42


def test_with_timeout_raises():
    @with_timeout(0.1)
    def slow():
        time.sleep(1)
        return 42

    with pytest.raises(TimeoutError):
        slow()


def test_safe_execute_success():
    assert safe_execute(lambda: 42) == 42


def test_safe_execute_failure():
    def fail():
        raise ValueError("boom")

    assert safe_execute(fail, default="fallback") == "fallback"


def test_error_collector():
    ec = ErrorCollector()
    assert not ec.has_errors()
    ec.add_error("test", "something broke")
    assert ec.has_errors()
    s = ec.summary()
    assert s["error_count"] == 1
    assert s["warning_count"] == 0


def test_error_collector_warnings():
    ec = ErrorCollector()
    ec.add_warning("test", "careful")
    s = ec.summary()
    assert s["warning_count"] == 1


def test_exception_hierarchy():
    assert issubclass(SafetyError, ApexError)
    assert issubclass(PatchError, ApexError)
    assert issubclass(ValidationError, ApexError)
    assert issubclass(ApexTimeoutError, ApexError)
