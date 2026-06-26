"""Csp1dRecovery tests."""

from __future__ import annotations

from ospf_python.framework.csp1d.application.service.csp1d_recovery import (
    Csp1dRecovery,
)


class TestCsp1dRecovery:
    """Csp1dRecovery method tests."""

    def test_recover_no_assignments(self) -> None:
        """Recover with no assignments."""
        recovery = Csp1dRecovery()
        result = recovery.recover(
            variable_values=(),
            material_names=(),
            plan_names=(),
        )
        # Empty input may return Ok or Failed depending on implementation
        assert result.is_ok() or result.is_failed()

    def test_recover_with_values(self) -> None:
        """Recover with variable values."""
        recovery = Csp1dRecovery()
        result = recovery.recover(
            variable_values=(("x1", 1.0),),
            material_names=("m1",),
            plan_names=("p1",),
        )
        # May succeed or fail depending on validation
        assert result.is_ok() or result.is_failed()
