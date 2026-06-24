"""WidthRange tests.

Test width range model creation and immutability.
测试宽度范围模型创建和不可变性。
"""

from __future__ import annotations

import pytest

from ospf_python.framework.csp1d.domain.material.model.width_range import (
    WidthRange,
)


class TestWidthRange:
    """WidthRange frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        r = WidthRange(min_width=10.0, max_width=100.0)
        assert r.min_width == 10.0
        assert r.max_width == 100.0

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        r = WidthRange(min_width=10.0, max_width=100.0)
        with pytest.raises(AttributeError):
            r.min_width = 5.0  # type: ignore[misc]

    def test_equality(self) -> None:
        """Same field values yield equality. / 相同字段值相等。"""
        a = WidthRange(min_width=10.0, max_width=100.0)
        b = WidthRange(min_width=10.0, max_width=100.0)
        assert a == b

    def test_inequality(self) -> None:
        """Different values yield inequality. / 不同值不等。"""
        a = WidthRange(min_width=10.0, max_width=100.0)
        b = WidthRange(min_width=20.0, max_width=100.0)
        assert a != b

    def test_hash(self) -> None:
        """Instances are hashable. / 实例可哈希。"""
        r = WidthRange(min_width=10.0, max_width=100.0)
        assert hash(r) is not None

    def test_is_dataclass(self) -> None:
        """Instance is a dataclass. / 实例是数据类。"""
        import dataclasses

        r = WidthRange(min_width=0.0, max_width=1.0)
        assert dataclasses.is_dataclass(r)
