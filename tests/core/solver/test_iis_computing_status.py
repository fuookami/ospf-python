"""IISComputingStatus 测试。

测试 IIS 计算状态枚举的定义和值。
Tests IISComputingStatus enum definition and values.
"""

from __future__ import annotations

import pytest

from ospf_python.core.solver.iis.iis_computing_status import (
    IISComputingStatus,
)
from ospf_python.core.solver.iis.linear import LinearIIS
from ospf_python.core.solver.iis.quadratic import QuadraticIIS


class TestIISComputingStatus:
    """枚举测试 / Enum tests."""

    def test_not_started_value(self) -> None:
        """NOT_STARTED 值为 0。/ NOT_STARTED is 0."""
        assert IISComputingStatus.NOT_STARTED.value == 0

    def test_found_value(self) -> None:
        """FOUND 值为 2。/ FOUND is 2."""
        assert IISComputingStatus.FOUND.value == 2

    def test_member_count(self) -> None:
        """共 6 个成员。/ Has 6 members."""
        assert len(IISComputingStatus) == 6


class TestLinearIIS:
    """LinearIIS 测试 / Tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        iis = LinearIIS()
        with pytest.raises(AttributeError):
            iis.message = "x"  # type: ignore[misc]

    def test_is_found(self) -> None:
        """已找到状态。/ Found status."""
        iis = LinearIIS(
            status=IISComputingStatus.FOUND,
            constraints=("c1",),
        )
        assert iis.is_found is True

    def test_not_found(self) -> None:
        """未找到状态。/ Not found status."""
        iis = LinearIIS()
        assert iis.is_found is False

    def test_size(self) -> None:
        """IIS 大小。/ IIS size."""
        iis = LinearIIS(
            constraints=("c1", "c2"),
            bounds=("x",),
        )
        assert iis.size == 3


class TestQuadraticIIS:
    """QuadraticIIS 测试 / Tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        iis = QuadraticIIS()
        with pytest.raises(AttributeError):
            iis.message = "x"  # type: ignore[misc]

    def test_is_found(self) -> None:
        """已找到状态。/ Found status."""
        iis = QuadraticIIS(
            status=IISComputingStatus.FOUND,
            quadratic_constraints=("qc1",),
        )
        assert iis.is_found is True

    def test_size(self) -> None:
        """IIS 大小。/ IIS size."""
        lin = LinearIIS(
            constraints=("c1",),
            bounds=("x",),
        )
        iis = QuadraticIIS(
            linear_iis=lin,
            quadratic_constraints=("qc1", "qc2"),
        )
        assert iis.size == 4
