"""物理量。/ Physical quantity.

值 + 单位；受检四则与转换显式返回 Result。
Value + unit; checked arithmetic and conversion return Result explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from ospf_python._binding import quantity_arithmetic as _arithmetic
from ospf_python._binding import quantity_snapshot as _snapshot
from ospf_python._binding import unit_conversion as _unit_conversion

if TYPE_CHECKING:
    from decimal import Context

    from ospf_python._binding.result import BindingResult
    from ospf_python.quantities.quantity.numeric_adapter import NumericAdapter
    from ospf_python.quantities.quantity.snapshot_adapter import SnapshotAdapter
    from ospf_python.quantities.unit.physical_unit import (
        PhysicalUnit,
    )

T = TypeVar("T")


@dataclass(frozen=True)
class Quantity(Generic[T]):
    """物理量，包含数值和单位。

    Physical quantity with numeric value and unit.

    同量纲四则由固定 Rust 检查单位与点差语义。
    Pinned Rust checks dimensions, units and point/difference arithmetic.

    Attributes:
        value: 数值。/ Numeric value.
        unit: 物理单位。/ Physical unit.
    """

    value: T
    unit: PhysicalUnit

    def to_dict(
        self,
        *,
        value_adapter: SnapshotAdapter[T] | None = None,
        unit_adapter: SnapshotAdapter[Any] | None = None,
    ) -> BindingResult[dict[str, Any]]:
        """导出版本化纯数据，保留数值域及原生单位元数据。 / Export versioned data preserving numeric domains and native unit metadata.

        Args:
            value_adapter: 开放值的显式快照策略。 / Explicit snapshot policy for open values.
            unit_adapter: 开放单位的显式快照策略。 / Explicit snapshot policy for open units.

        Returns:
            独立字典或保留原来源的失败。 / Independent dictionary or provenance-retaining failure.
        """
        return _snapshot.encode(
            owner=self,
            value_adapter=value_adapter,
            unit_adapter=unit_adapter,
            as_json=False,
        )

    def to_json(
        self,
        *,
        value_adapter: SnapshotAdapter[T] | None = None,
        unit_adapter: SnapshotAdapter[Any] | None = None,
    ) -> BindingResult[str]:
        """导出同一版本化 DTO 的 JSON，不执行隐式 float 转换。 / Export the same versioned DTO as JSON without implicit float conversion.

        Args:
            value_adapter: 开放值的显式快照策略。 / Explicit snapshot policy for open values.
            unit_adapter: 开放单位的显式快照策略。 / Explicit snapshot policy for open units.

        Returns:
            JSON 字符串或保留原来源的失败。 / JSON string or provenance-retaining failure.
        """
        return _snapshot.encode(
            owner=self,
            value_adapter=value_adapter,
            unit_adapter=unit_adapter,
            as_json=True,
        )

    @classmethod
    def from_dict(
        cls,
        payload: object,
        *,
        value_adapter: SnapshotAdapter[Any] | None = None,
        unit_adapter: SnapshotAdapter[Any] | None = None,
    ) -> BindingResult[Any]:
        """验证并恢复 DTO，不自动导入快照提供的类。 / Validate and restore a DTO without importing snapshot-supplied classes.

        Args:
            payload: 版本化纯数据字典。 / Versioned pure-data dictionary.
            value_adapter: 开放值的显式恢复策略。 / Explicit restoration policy for open values.
            unit_adapter: 开放单位的显式恢复策略。 / Explicit restoration policy for open units.

        Returns:
            当前类工厂输出或 Failed，中断继续传播。 / Current class factory output or Failed; interrupts propagate.
        """
        return _snapshot.decode(
            payload=payload,
            factory=cls,
            value_adapter=value_adapter,
            unit_adapter=unit_adapter,
            as_json=False,
        )

    @classmethod
    def from_json(
        cls,
        text: str,
        *,
        value_adapter: SnapshotAdapter[Any] | None = None,
        unit_adapter: SnapshotAdapter[Any] | None = None,
    ) -> BindingResult[Any]:
        """验证并恢复 JSON，拒绝重复字段及未知版本。 / Validate and restore JSON, rejecting duplicate keys and unknown versions.

        Args:
            text: 版本化 JSON 字符串。 / Versioned JSON string.
            value_adapter: 开放值的显式恢复策略。 / Explicit restoration policy for open values.
            unit_adapter: 开放单位的显式恢复策略。 / Explicit restoration policy for open units.

        Returns:
            当前类工厂输出或保留来源的失败。 / Current class factory output or provenance-retaining failure.
        """
        return _snapshot.decode(
            payload=text,
            factory=cls,
            value_adapter=value_adapter,
            unit_adapter=unit_adapter,
            as_json=True,
        )

    def to(
        self,
        target_unit: PhysicalUnit,
        *,
        context: Context | None = None,
        exact: bool = True,
        numeric_adapter: NumericAdapter[T] | None = None,
    ) -> BindingResult[Any]:
        """通过 Rust 单位内核及开放回调转换，显式返回 Result。 / Convert through the Rust unit kernel and open callbacks, returning Result explicitly.

        不隐式转换 float。内置整数除不尽提升 Fraction；Decimal 仅最终出口舍入。
        No implicit float conversion. Nonintegral int results promote to Fraction;
        Decimal rounding occurs only at final export.

        Args:
            target_unit: 目标单位。/ Target unit.
            context: 仅用于 Decimal 输出的上下文。 / Context for Decimal export only.
            exact: 默认拒绝 Decimal 输出损失。 / Reject Decimal export loss by default.
            numeric_adapter: 自定义精确数值的显式策略。 / Explicit policy for custom exact values.

        Returns:
            Ok 中的 Quantity 或当前开放工厂输出；失败保留原生错误或外部异常。
            Quantity or current open factory output in Ok; failures retain native
            provenance or external exceptions. The open output is intentionally Any,
            not a false promise that every callback preserves T.
        """
        return _unit_conversion.convert_quantity(
            owner=self,
            target=target_unit,
            context=context,
            exact=exact,
            numeric_adapter=numeric_adapter,
        )

    def add(
        self,
        other: Any,
        *,
        context: Context | None = None,
        exact: bool = True,
        numeric_adapter: NumericAdapter[Any] | None = None,
    ) -> BindingResult[Any]:
        """受检相加，显式返回 Result。 / Checked addition, returning Result explicitly.

        Args:
            other: 右数量或标量。 / Right quantity or scalar.
            context: 最终 Decimal 出口上下文。 / Final Decimal export context.
            exact: 拒绝出口或 Float64 混合导入损失。 / Reject export or mixed Float64 import loss.
            numeric_adapter: 双方数值导入及单次输出策略。 / Import both operands and export once.

        Returns:
            工厂输出或保留来源的失败。 / Factory output or failure retaining provenance.
        """
        return _arithmetic.calculate(
            owner=self,
            other=other,
            operation="add",
            context=context,
            exact=exact,
            numeric_adapter=numeric_adapter,
        )

    def __add__(self, other: Any) -> BindingResult[Any]:
        """默认受检相加，与自然方法共用 Result 路径。 / Default checked addition shares the natural Result path.

        Args:
            other: 右数量或标量。 / Right quantity or scalar.

        Returns:
            显式 Result，不是未受检数量。 / Explicit Result, not an unchecked quantity.
        """
        return self.add(other)

    def subtract(
        self,
        other: Any,
        *,
        context: Context | None = None,
        exact: bool = True,
        numeric_adapter: NumericAdapter[Any] | None = None,
    ) -> BindingResult[Any]:
        """受检相减，显式返回 Result。 / Checked subtraction, returning Result explicitly.

        Args:
            other: 右数量或标量。 / Right quantity or scalar.
            context: 最终 Decimal 出口上下文。 / Final Decimal export context.
            exact: 拒绝出口或 Float64 混合导入损失。 / Reject export or mixed Float64 import loss.
            numeric_adapter: 双方数值导入及单次输出策略。 / Import both operands and export once.

        Returns:
            工厂输出或保留来源的失败。 / Factory output or failure retaining provenance.
        """
        return _arithmetic.calculate(
            owner=self,
            other=other,
            operation="subtract",
            context=context,
            exact=exact,
            numeric_adapter=numeric_adapter,
        )

    def __sub__(self, other: Any) -> BindingResult[Any]:
        """默认受检相减，与自然方法共用 Result 路径。 / Default checked subtraction shares the natural Result path.

        Args:
            other: 右数量或标量。 / Right quantity or scalar.

        Returns:
            显式 Result，不是未受检数量。 / Explicit Result, not an unchecked quantity.
        """
        return self.subtract(other)

    def multiply(
        self,
        scalar: Any,
        *,
        context: Context | None = None,
        exact: bool = True,
        numeric_adapter: NumericAdapter[Any] | None = None,
    ) -> BindingResult[Any]:
        """受检标量乘法，显式返回 Result。 / Checked scalar multiplication, returning Result explicitly.

        Args:
            scalar: 右数量或标量。 / Right quantity or scalar.
            context: 最终 Decimal 出口上下文。 / Final Decimal export context.
            exact: 拒绝出口或 Float64 混合导入损失。 / Reject export or mixed Float64 import loss.
            numeric_adapter: 双方数值导入及单次输出策略。 / Import both operands and export once.

        Returns:
            工厂输出或保留来源的失败。 / Factory output or failure retaining provenance.
        """
        return _arithmetic.calculate(
            owner=self,
            other=scalar,
            operation="multiply",
            context=context,
            exact=exact,
            numeric_adapter=numeric_adapter,
        )

    def __mul__(self, scalar: Any) -> BindingResult[Any]:
        """默认受检标量乘法，与自然方法共用 Result 路径。 / Default checked scalar multiplication shares the natural Result path.

        Args:
            scalar: 右数量或标量。 / Right quantity or scalar.

        Returns:
            显式 Result，不是未受检数量。 / Explicit Result, not an unchecked quantity.
        """
        return self.multiply(scalar)

    def divide(
        self,
        scalar: Any,
        *,
        context: Context | None = None,
        exact: bool = True,
        numeric_adapter: NumericAdapter[Any] | None = None,
    ) -> BindingResult[Any]:
        """受检标量除法，显式返回 Result。 / Checked scalar division, returning Result explicitly.

        Args:
            scalar: 右数量或标量。 / Right quantity or scalar.
            context: 最终 Decimal 出口上下文。 / Final Decimal export context.
            exact: 拒绝出口或 Float64 混合导入损失。 / Reject export or mixed Float64 import loss.
            numeric_adapter: 双方数值导入及单次输出策略。 / Import both operands and export once.

        Returns:
            工厂输出或保留来源的失败。 / Factory output or failure retaining provenance.
        """
        return _arithmetic.calculate(
            owner=self,
            other=scalar,
            operation="divide",
            context=context,
            exact=exact,
            numeric_adapter=numeric_adapter,
        )

    def __truediv__(self, scalar: Any) -> BindingResult[Any]:
        """默认受检标量除法，与自然方法共用 Result 路径。 / Default checked scalar division shares the natural Result path.

        Args:
            scalar: 右数量或标量。 / Right quantity or scalar.

        Returns:
            显式 Result，不是未受检数量。 / Explicit Result, not an unchecked quantity.
        """
        return self.divide(scalar)

    def __str__(self) -> str:
        """字符串表示。/ String representation."""
        return f"{self.value} {self.unit.symbol}"
