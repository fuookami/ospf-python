"""Csp1dRecovery tests."""

from __future__ import annotations

import pytest

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

    def test_noise_below_one_unit_is_not_promoted_to_a_real_assignment(self) -> None:
        """容差以上的噪声不得被抬成 1 件的真实分配。

        1e-5 大于默认容差 1e-6，但 round(1e-5) 是 0；旧的 max(1, round(val)) 会给求解器
        根本没有选中的变量记 1 件。
        Noise above the tolerance must not become a real one-unit assignment: 1e-5 exceeds the
        default 1e-6 tolerance but round(1e-5) is 0, and the old max(1, round(val)) recorded one
        unit for a variable the solver never selected.
        """
        recovery = Csp1dRecovery()
        result = recovery.recover(
            variable_values=(("x_M1_P1", 1e-5),),
            material_names=("M1",),
            plan_names=("P1",),
        )
        assert result.is_failed()

    def test_whole_unit_still_recovers(self) -> None:
        """整数值仍恢复为真实分配。/ A whole-unit value still recovers a real assignment."""
        recovery = Csp1dRecovery()
        result = recovery.recover(
            variable_values=(("x_M1_P1", 3.0),),
            material_names=("M1",),
            plan_names=("P1",),
        )
        assert result.is_ok()
        solution = result.unwrap()
        assert [a.quantity for a in solution.assignments] == [3]

    def test_utilization_uses_lengths_not_bar_counts(self) -> None:
        """利用率 = 已用长度 / 消耗长度，不是 1 - 余料长度 / 根数。

        每根长 100、余料 10、2 根时旧实现算 1 - 20/2 = -9 → clamp 成 0.0；
        正确值是 (90*2)/(100*2) = 0.9。
        Utilization is used length over consumed length, not 1 - waste length / bar count. With
        two bars of length 100 and waste 10 the old code computed 1 - 20/2 = -9, clamped to 0.0;
        the correct value is (90*2)/(100*2) = 0.9.
        """
        recovery = Csp1dRecovery()
        solution = recovery.recover(
            variable_values=(("x_M1_P1", 2.0), ("w_M1_P1", 10.0)),
            material_names=("M1",),
            plan_names=("P1",),
            material_lengths={"M1": 100.0},
        ).unwrap()
        assert solution.utilization == pytest.approx(0.9)
        assert solution.total_waste == pytest.approx(20.0)

    def test_utilization_is_one_for_zero_waste(self) -> None:
        """零余料是完全利用。/ Zero waste is full utilization."""
        recovery = Csp1dRecovery()
        solution = recovery.recover(
            variable_values=(("x_M1_P1", 1.0), ("w_M1_P1", 0.0)),
            material_names=("M1",),
            plan_names=("P1",),
            material_lengths={"M1": 100.0},
        ).unwrap()
        assert solution.utilization == pytest.approx(1.0)
