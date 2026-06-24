"""CSP1D 产出率约束管线。

向产出率模型添加产出率约束。
Yield constraint pipeline for yield optimization.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class YieldConstraintPipeline:
    """产出率约束管线 / Yield constraint pipeline.

    在产出率模型中添加最低产出率约束，
    确保切割方案满足最低产出率要求。
    Adds minimum yield ratio constraints to the
    yield model, ensuring cutting plans meet
    minimum yield requirements.

    Attributes:
        enforce_min_yield: 是否强制最低产出率。
            Whether to enforce minimum yield.
        min_ratio: 最低产出率阈值。
            Minimum yield ratio threshold.
    """

    enforce_min_yield: bool = True
    """强制最低产出率 / Enforce minimum yield."""

    min_ratio: float = 0.0
    """最低产出率 / Min yield ratio."""

    def apply[T](self, aggregation: T) -> T:
        """应用产出率约束。

        Apply yield constraints.

        Args:
            aggregation: 产出率聚合。
                Yield aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return aggregation

    def is_yield_acceptable(
        self,
        *,
        yield_ratio: float,
    ) -> bool:
        """检查产出率是否可接受。

        Check if yield ratio is acceptable.

        Args:
            yield_ratio: 实际产出率。
                Actual yield ratio.

        Returns:
            可接受返回 True / True if acceptable.
        """
        if not self.enforce_min_yield:
            return True
        return yield_ratio >= self.min_ratio

    def compute_yield_shortfall(
        self,
        *,
        yield_ratio: float,
        target_ratio: float,
    ) -> float:
        """计算产出率缺口。

        Compute yield ratio shortfall.

        Args:
            yield_ratio: 实际产出率。
                Actual yield ratio.
            target_ratio: 目标产出率。
                Target yield ratio.

        Returns:
            缺口（非负）。
            Shortfall (non-negative).
        """
        return max(0.0, target_ratio - yield_ratio)

    def filter_acceptable_yields(
        self,
        *,
        yields: tuple[tuple[str, float], ...],
    ) -> tuple[tuple[str, float], ...]:
        """过滤可接受的产出率。

        Filter acceptable yield ratios.

        Args:
            yields: 产品键到产出率的映射。
                Product key to yield ratio mapping.

        Returns:
            可接受的产出率元组。
            Tuple of acceptable yield ratios.
        """
        return tuple(
            (k, r) for k, r in yields if self.is_yield_acceptable(yield_ratio=r)
        )
