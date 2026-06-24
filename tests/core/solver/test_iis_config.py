"""IISConfig 测试。

测试 IIS 配置的创建和默认值。
Tests IISConfig creation and defaults.
"""

from __future__ import annotations

import pytest

from ospf_python.core.solver.iis.iis_config import IISConfig


class TestIISConfig:
    """IIS 配置测试 / IIS config tests."""

    def test_frozen(self) -> None:
        """实例不可变。/ Instance is frozen."""
        cfg = IISConfig()
        with pytest.raises(AttributeError):
            cfg.time_limit = 1.0  # type: ignore[misc]

    def test_defaults(self) -> None:
        """默认值正确。/ Default values correct."""
        cfg = IISConfig()
        assert cfg.time_limit == 300.0
        assert cfg.max_iterations == 1000
        assert cfg.verbose is False
