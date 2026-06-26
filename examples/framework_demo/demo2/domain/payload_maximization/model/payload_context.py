"""载荷最大化上下文 / Payload maximization context.

管理载荷最大化分析的注册与查询。
Manages registration and lookup for payload maximization
analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .payload_aggregation import PayloadAggregation

if TYPE_CHECKING:
    from .payload_result import PayloadResult


@dataclass
class PayloadContext:
    """载荷最大化上下文 / Payload maximization context.

    提供可变的注册接口，收集所有载荷计算结果后
    可生成不可变的聚合对象。
    Provides a mutable registration interface; after
    collecting all payload calculation results, generates
    an immutable aggregation object.

    Attributes:
        _results: 已注册结果 / Registered results.
        _max_structural_weight: 最大结构重量(kg) /
            Maximum structural weight (kg).
        _max_envelope_weight: 最大包线重量(kg) /
            Maximum envelope weight (kg).
        _operating_empty_weight: 使用空重(kg) /
            Operating empty weight (kg).
    """

    _results: list[PayloadResult] = field(
        default_factory=list,
        init=False,
    )
    _max_structural_weight: float = field(
        default=0.0,
        init=False,
    )
    _max_envelope_weight: float = field(
        default=0.0,
        init=False,
    )
    _operating_empty_weight: float = field(
        default=0.0,
        init=False,
    )

    def register_result(self, result: PayloadResult) -> None:
        """注册载荷结果 / Register payload result.

        Args:
            result: 载荷结果 / Payload result.
        """
        self._results.append(result)

    def set_max_structural_weight(
        self,
        weight: float,
    ) -> None:
        """设置最大结构重量 / Set max structural weight.

        Args:
            weight: 最大结构重量(kg) / Max structural weight (kg).
        """
        self._max_structural_weight = weight

    def set_max_envelope_weight(
        self,
        weight: float,
    ) -> None:
        """设置最大包线重量 / Set max envelope weight.

        Args:
            weight: 最大包线重量(kg) / Max envelope weight (kg).
        """
        self._max_envelope_weight = weight

    def set_operating_empty_weight(
        self,
        weight: float,
    ) -> None:
        """设置使用空重 / Set operating empty weight.

        Args:
            weight: 使用空重(kg) / Operating empty weight (kg).
        """
        self._operating_empty_weight = weight

    @property
    def max_structural_weight(self) -> float:
        """最大结构重量(kg) / Max structural weight (kg)."""
        return self._max_structural_weight

    @property
    def max_envelope_weight(self) -> float:
        """最大包线重量(kg) / Max envelope weight (kg)."""
        return self._max_envelope_weight

    @property
    def operating_empty_weight(self) -> float:
        """使用空重(kg) / Operating empty weight (kg)."""
        return self._operating_empty_weight

    @property
    def theoretical_max_payload(self) -> float:
        """理论最大载荷(kg) / Theoretical max payload (kg).

        取结构限制与包线限制中的较小值减去使用空重。
        Takes the minimum of structural and envelope limits
        minus the operating empty weight.
        """
        limit = min(
            self._max_structural_weight,
            self._max_envelope_weight,
        )
        return max(0.0, limit - self._operating_empty_weight)

    @property
    def result_count(self) -> int:
        """已注册结果数 / Registered result count."""
        return len(self._results)

    def build_aggregation(self) -> PayloadAggregation:
        """构建不可变聚合对象。

        Build an immutable aggregation object from
        the currently registered data.

        Returns:
            包含所有已注册结果的聚合对象。
            Aggregation object with all registered results.
        """
        return PayloadAggregation(
            results=tuple(self._results),
        )
