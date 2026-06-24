"""CSP1D 机器约束管线。

管理机器产能和分配约束。
Machine constraint pipeline for production.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MachineConstraintPipeline:
    """机器约束管线 / Machine constraint pipeline.

    管理机器产能约束和机器-产品兼容性约束。
    在 MILP 中对应机器使用量 <= 产能的约束族。
    Manages machine capacity and machine-product
    compatibility constraints. Corresponds to
    machine usage <= capacity constraint family
    in MILP.

    Attributes:
        enforce_capacity: 是否强制产能约束。
            Whether to enforce capacity constraints.
        enforce_compatibility: 是否强制兼容性约束。
            Whether to enforce compatibility constraints.
    """

    enforce_capacity: bool = True
    """强制产能 / Enforce capacity."""

    enforce_compatibility: bool = True
    """强制兼容性 / Enforce compatibility."""

    def apply[T](self, aggregation: T) -> T:
        """应用机器约束。

        Apply machine constraints.

        Args:
            aggregation: 生产聚合。
                Production aggregation.

        Returns:
            更新后的聚合。
            Updated aggregation.
        """
        return aggregation

    def is_within_capacity(
        self,
        *,
        used: int,
        capacity: int,
    ) -> bool:
        """检查是否在产能范围内。

        Check if within capacity.

        Args:
            used: 已使用量。
                Used quantity.
            capacity: 产能上限。
                Capacity limit.

        Returns:
            在范围内返回 True / True if within range.
        """
        if not self.enforce_capacity:
            return True
        return used <= capacity

    def remaining_capacity(
        self,
        *,
        used: int,
        capacity: int,
    ) -> int:
        """计算剩余产能。

        Compute remaining capacity.

        Args:
            used: 已使用量。
                Used quantity.
            capacity: 产能上限。
                Capacity limit.

        Returns:
            剩余产能（非负）。
            Remaining capacity (non-negative).
        """
        if not self.enforce_capacity:
            return capacity
        return max(0, capacity - used)

    def is_compatible(
        self,
        *,
        machine_key: str,
        product_key: str,
        compatibility: frozenset[tuple[str, str]],
    ) -> bool:
        """检查机器-产品兼容性。

        Check machine-product compatibility.

        Args:
            machine_key: 机器标识。
                Machine key.
            product_key: 产品标识。
                Product key.
            compatibility: 兼容性集合，
                每项为 (机器键, 产品键)。
                Compatibility set, each item
                is (machine_key, product_key).

        Returns:
            兼容返回 True / True if compatible.
        """
        if not self.enforce_compatibility:
            return True
        return (machine_key, product_key) in compatibility
