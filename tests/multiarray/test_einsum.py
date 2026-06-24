"""Einsum 模块测试。

测试 einsum 模块的基本导入和功能。
Tests einsum module basic import and functionality.
"""

from __future__ import annotations


class TestEinsumModule:
    """Einsum 模块测试 / Einsum module tests."""

    def test_module_import(self) -> None:
        """模块可导入。/ Module is importable."""
        import ospf_python.multiarray.einsum

        assert ospf_python.multiarray.einsum is not None
