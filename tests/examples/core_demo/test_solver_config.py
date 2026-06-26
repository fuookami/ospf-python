"""Test solver configuration — 测试求解器配置。"""

from __future__ import annotations

from ospf_python.core.solver.solve_options import SolveOptions


def test_solve_options_defaults() -> None:
    """Test default solve options."""
    options = SolveOptions()
    assert options.time_limit > 0
    assert isinstance(options.verbose, bool)


def test_solve_options_custom() -> None:
    """Test custom solve options."""
    options = SolveOptions(time_limit=60.0, verbose=True, seed=42)
    assert options.time_limit == 60.0
    assert options.verbose is True
    assert options.seed == 42
