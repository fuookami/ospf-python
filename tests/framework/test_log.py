"""Tests for logging framework.

日志框架测试。
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ospf_python.framework.log.log_context import LogContext
from ospf_python.framework.log.log_record import LogRecord

# -- LogContext -------------------------------------------------------


class TestLogContextExtra:
    """Test LogContext edge cases."""

    def test_create_minimal(self) -> None:
        """最小创建 / Minimal creation."""
        ctx = LogContext(module="core")
        assert ctx.module == "core"
        assert ctx.request_id == ""
        assert ctx.user_id == ""

    def test_create_full(self) -> None:
        """全字段创建 / Full creation."""
        ctx = LogContext(
            module="solver",
            request_id="req-001",
            user_id="user-002",
        )
        assert ctx.module == "solver"
        assert ctx.request_id == "req-001"
        assert ctx.user_id == "user-002"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ctx = LogContext(module="test")
        with pytest.raises(AttributeError):
            ctx.module = "other"  # type: ignore[misc]

    def test_equality(self) -> None:
        """相等性 / Equality."""
        a = LogContext(module="m", request_id="r", user_id="u")
        b = LogContext(module="m", request_id="r", user_id="u")
        assert a == b

    def test_inequality(self) -> None:
        """不相等 / Inequality."""
        a = LogContext(module="m1")
        b = LogContext(module="m2")
        assert a != b


# -- LogRecord -------------------------------------------------------


class TestLogRecordExtra:
    """Test LogRecord edge cases."""

    def test_info_level(self) -> None:
        """INFO 级别 / INFO level."""
        ts = datetime(2026, 1, 1, tzinfo=UTC)
        rec = LogRecord(level="INFO", message="ok", timestamp=ts)
        assert rec.level == "INFO"

    def test_error_level(self) -> None:
        """ERROR 级别 / ERROR level."""
        ts = datetime(2026, 1, 1, tzinfo=UTC)
        rec = LogRecord(level="ERROR", message="fail", timestamp=ts)
        assert rec.level == "ERROR"

    def test_warning_level(self) -> None:
        """WARNING 级别 / WARNING level."""
        ts = datetime(2026, 1, 1, tzinfo=UTC)
        rec = LogRecord(level="WARNING", message="warn", timestamp=ts)
        assert rec.level == "WARNING"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ts = datetime(2026, 1, 1, tzinfo=UTC)
        rec = LogRecord(level="INFO", message="ok", timestamp=ts)
        with pytest.raises(AttributeError):
            rec.level = "ERROR"  # type: ignore[misc]

    def test_empty_message(self) -> None:
        """空消息 / Empty message."""
        ts = datetime(2026, 1, 1, tzinfo=UTC)
        rec = LogRecord(level="INFO", message="", timestamp=ts)
        assert rec.message == ""

    def test_long_message(self) -> None:
        """长消息 / Long message."""
        ts = datetime(2026, 1, 1, tzinfo=UTC)
        msg = "x" * 10000
        rec = LogRecord(level="INFO", message=msg, timestamp=ts)
        assert len(rec.message) == 10000
