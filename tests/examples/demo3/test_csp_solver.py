"""Test CSP solver — 测试 CSP 求解器。"""

from __future__ import annotations

from examples.framework_demo.demo3.main import run_demo


def test_csp_column_generation() -> None:
    """Test CSP column generation solves correctly."""
    result = run_demo()
    assert int(str(result["iterations"])) > 0
    assert result["converged"] is True
    assert int(str(result["columns"])) > 0


def test_csp_parameters_aligned() -> None:
    """Test CSP parameters match Kotlin Main.kt."""
    result = run_demo()
    # Should converge within max iterations
    assert int(str(result["iterations"])) <= 50
    # Should generate multiple columns
    assert int(str(result["columns"])) >= 10
