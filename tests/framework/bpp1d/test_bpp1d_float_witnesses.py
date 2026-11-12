"""BPP1D 浮点反例的精确算术基线 / Exact arithmetic witnesses for BPP1D floats.

这些测试只验证数学证据，不代表原生领域绑定已接通。
These check the witnesses only, not a native domain cutover.
"""

from __future__ import annotations

from fractions import Fraction


def test_one_bin_witness_is_exact_despite_ordered_rounding() -> None:
    """相同输入顺序不应消除可行解 / Input order must not erase a feasible solution."""
    a, b, c, capacity = 0.1, 0.03, 0.2, 0.33
    f = Fraction.from_float
    assert (a + c) + b > capacity
    assert (a + b) + c == capacity
    assert f(a) + f(b) + f(c) == f(capacity)
    end = Fraction(0)
    for start, length in ((0.0, a), (0.1, b), (0.13, c)):
        assert f(start) == end
        end = f(start) + f(length)
    assert end == f(capacity)


def test_rounded_capacity_can_hide_a_whole_unit() -> None:
    """大尺度累计不得丢失一单位 / Large-scale accumulation must not lose one unit."""
    capacity, piece = 1e16, 1.0
    assert capacity + piece == capacity
    assert Fraction.from_float(capacity) + Fraction.from_float(piece) > (
        Fraction.from_float(capacity)
    )
    assert Fraction.from_float(capacity) + Fraction.from_float(piece) == (
        Fraction.from_float(capacity) + 1
    )


def test_decimal_rounding_can_hide_overlap_and_capacity_excess() -> None:
    """精确比较揭示舍入误差 / Exact comparisons reveal rounding error."""
    f = Fraction.from_float
    assert (0.4 + 0.1) + 0.1 == 0.6
    assert f(0.4) + f(0.1) - f(0.5) == Fraction(1, 2**55)
    assert f(0.5) + f(0.1) - f(0.6) == Fraction(1, 2**55)


def test_exact_placement_may_not_fit_in_a_float() -> None:
    """精确坐标不可静默舍入 / An exact coordinate cannot be silently rounded."""
    f = Fraction.from_float
    start = f(0.1) + f(0.2)
    assert f(float(start)) != start
    assert start + f(0.03) == f(0.33)


def test_exact_coefficient_does_not_make_a_float_sum_exact() -> None:
    """严格输入转换不保证求和精确 / Strict input conversion does not ensure exact sums."""
    exact_cost = Fraction.from_float(0.1)
    reported_cost = Fraction.from_float(0.1 * 3)
    assert reported_cost - exact_cost * 3 == Fraction(1, 2**55)
    assert Fraction.from_float(float(Fraction(1, 10))) != Fraction(1, 10)
