"""Loading effectiveness 测试 / Loading effectiveness tests.

覆盖 LoadingPattern、空间利用率、重量分布和
装载效果管线。
Covers LoadingPattern, space utilization, weight
distribution, and effectiveness pipeline.
"""

from __future__ import annotations

import pytest

from examples.framework_demo.demo2.domain.loading_effectiveness.model.loading_pattern import (
    LoadingPattern,
)
from examples.framework_demo.demo2.domain.loading_effectiveness.model.space_utilization import (
    SpaceUtilization,
)
from examples.framework_demo.demo2.domain.loading_effectiveness.model.weight_distribution import (
    WeightDistribution,
)


class TestLoadingPattern:
    """LoadingPattern 测试 / Loading pattern tests."""

    def test_item_count(self) -> None:
        """物品数量 / Item count."""
        pattern = LoadingPattern(
            pattern_id="LP1",
            items=("A", "B", "C"),
            positions={
                "A": (0.0, 0.0, 0.0),
                "B": (1.0, 0.0, 0.0),
                "C": (2.0, 0.0, 0.0),
            },
            efficiency=0.85,
        )
        assert pattern.item_count() == 3

    def test_is_valid(self) -> None:
        """方案有效性 / Pattern validity."""
        valid = LoadingPattern(
            pattern_id="LP1",
            items=("A", "B"),
            positions={"A": (0.0, 0.0, 0.0), "B": (1.0, 0.0, 0.0)},
            efficiency=0.9,
        )
        invalid = LoadingPattern(
            pattern_id="LP2",
            items=("A", "B", "C"),
            positions={"A": (0.0, 0.0, 0.0)},
            efficiency=0.5,
        )
        assert valid.is_valid() is True
        assert invalid.is_valid() is False

    def test_bounding_box(self) -> None:
        """包围盒计算 / Bounding box calculation."""
        pattern = LoadingPattern(
            pattern_id="LP1",
            items=("A", "B"),
            positions={"A": (1.0, 2.0, 3.0), "B": (4.0, 5.0, 6.0)},
            efficiency=0.8,
        )
        min_c, max_c = pattern.bounding_box()
        assert min_c == (1.0, 2.0, 3.0)
        assert max_c == (4.0, 5.0, 6.0)

    def test_empty_bounding_box(self) -> None:
        """空方案包围盒 / Empty pattern bounding box."""
        pattern = LoadingPattern(
            pattern_id="LP_EMPTY",
            items=(),
            positions={},
            efficiency=0.0,
        )
        min_c, max_c = pattern.bounding_box()
        assert min_c == (0.0, 0.0, 0.0)
        assert max_c == (0.0, 0.0, 0.0)


class TestSpaceUtilization:
    """SpaceUtilization 测试 / Space utilization tests."""

    def test_compute_ratio(self) -> None:
        """计算利用率 / Compute ratio."""
        su = SpaceUtilization.compute(
            total_volume=100.0,
            used_volume=75.0,
        )
        assert su.ratio == pytest.approx(0.75)

    def test_clamp_used_volume(self) -> None:
        """使用量超限截断 / Clamp used volume."""
        su = SpaceUtilization.compute(
            total_volume=100.0,
            used_volume=150.0,
        )
        assert su.used_volume == pytest.approx(100.0)
        assert su.ratio == pytest.approx(1.0)

    def test_zero_total_volume(self) -> None:
        """零总体积安全处理 / Zero total volume safe."""
        su = SpaceUtilization.compute(
            total_volume=0.0,
            used_volume=0.0,
        )
        assert su.ratio == pytest.approx(0.0)

    def test_remaining_volume(self) -> None:
        """剩余体积 / Remaining volume."""
        su = SpaceUtilization.compute(
            total_volume=200.0,
            used_volume=80.0,
        )
        assert su.remaining_volume() == pytest.approx(120.0)

    def test_is_fully_utilized(self) -> None:
        """是否充分装载 / Fully utilized check."""
        su = SpaceUtilization.compute(
            total_volume=100.0,
            used_volume=96.0,
        )
        assert su.is_fully_utilized(0.95) is True
        assert su.is_fully_utilized(0.99) is False


class TestWeightDistribution:
    """WeightDistribution 测试 / Weight distribution tests."""

    def test_from_compartment_weights(self) -> None:
        """从舱室重量计算分布 / Compute from weights."""
        wd = WeightDistribution.from_compartment_weights(
            weights={"left": 1_000.0, "right": 1_000.0},
            lateral_groups=(
                frozenset({"left"}),
                frozenset({"right"}),
            ),
            longitudinal_groups=(
                frozenset({"left"}),
                frozenset({"right"}),
            ),
        )
        assert wd.lateral_balance == pytest.approx(1.0)
        assert wd.longitudinal_balance == pytest.approx(1.0)

    def test_imbalanced(self) -> None:
        """不平衡分布 / Imbalanced distribution."""
        wd = WeightDistribution.from_compartment_weights(
            weights={"front": 2_000.0, "rear": 500.0},
            lateral_groups=(
                frozenset({"front"}),
                frozenset({"rear"}),
            ),
            longitudinal_groups=(
                frozenset({"front"}),
                frozenset({"rear"}),
            ),
        )
        # 2*500/2500 = 0.4
        assert wd.lateral_balance < 0.5

    def test_total_weight(self) -> None:
        """总重量 / Total weight."""
        wd = WeightDistribution(
            compartments={"A": 1_000.0, "B": 2_000.0},
            lateral_balance=0.8,
            longitudinal_balance=0.9,
        )
        assert wd.total_weight() == pytest.approx(3_000.0)

    def test_is_balanced(self) -> None:
        """是否平衡 / Balanced check."""
        balanced = WeightDistribution(
            compartments={"A": 1_000.0, "B": 1_000.0},
            lateral_balance=0.95,
            longitudinal_balance=0.92,
        )
        unbalanced = WeightDistribution(
            compartments={"A": 2_000.0, "B": 500.0},
            lateral_balance=0.5,
            longitudinal_balance=0.8,
        )
        assert balanced.is_balanced(0.1) is True
        assert unbalanced.is_balanced(0.1) is False
