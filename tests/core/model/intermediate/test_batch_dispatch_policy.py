"""BatchDispatchPolicy 测试。

测试批量调度策略枚举的创建和值。
Tests BatchDispatchPolicy enumeration creation and values.
"""

from __future__ import annotations

import pytest

from ospf_python.core.model.intermediate.batch_dispatch_policy import (
    BatchDispatchPolicy,
)


class TestBatchDispatchPolicy:
    """批量调度策略测试 / BatchDispatchPolicy tests."""

    def test_all_value(self) -> None:
        """ALL 值为 0。/ ALL value is 0."""
        assert BatchDispatchPolicy.ALL.value == 0

    def test_chunked_value(self) -> None:
        """CHUNKED 值为 1。/ CHUNKED value is 1."""
        assert BatchDispatchPolicy.CHUNKED.value == 1

    def test_streaming_value(self) -> None:
        """STREAMING 值为 2。/ STREAMING value is 2."""
        assert BatchDispatchPolicy.STREAMING.value == 2

    def test_member_count(self) -> None:
        """枚举有三个成员。/ Enum has three members."""
        assert len(BatchDispatchPolicy) == 3

    def test_from_value(self) -> None:
        """从值创建枚举成员。/ Create from value."""
        assert BatchDispatchPolicy(0) is BatchDispatchPolicy.ALL
        assert BatchDispatchPolicy(1) is BatchDispatchPolicy.CHUNKED
        assert BatchDispatchPolicy(2) is BatchDispatchPolicy.STREAMING

    def test_invalid_value_raises(self) -> None:
        """无效值抛出异常。/ Invalid value raises error."""
        with pytest.raises(ValueError):
            BatchDispatchPolicy(99)

    def test_iteration(self) -> None:
        """可迭代。/ Iterable."""
        members = list(BatchDispatchPolicy)
        assert len(members) == 3
