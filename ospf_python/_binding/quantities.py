"""固定 Rust 物理量底座及单句柄运行时单位门面。 / Pinned quantity foundation and single-handle runtime unit facade."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal
from fractions import Fraction
from math import isfinite
from typing import Any, cast

from ospf_python import _native
from ospf_python._binding.numeric import Rational
from ospf_python._binding.result import BindingResult, invalid, invoke
from ospf_python._binding.unit_registry import register_runtime_unit
from ospf_python.utils.functional.result import Failed, Ok

type DecimalCoefficient = int | float | Decimal
"""可无损编码为十进制元数据的内置域。 / Builtin domains encodable as decimal metadata."""

type ExactValue = int | Fraction | Decimal | Rational
"""不经 float 的精确输入域。 / Exact input domains without a float conversion."""

type UnitDescriptor = tuple[
    str, str, tuple[int, ...], tuple[int, int], tuple[int, int] | None
]
"""名称、符号、十指数及 coefficient*10**(-scale) 的快照。 / Name, symbol, ten powers and coefficient*10**(-scale) snapshots."""


def _decimal_parts(value: DecimalCoefficient) -> BindingResult[tuple[int, int]]:
    if type(value) is not Decimal:
        return invalid(
            "单位系数需要内置 int/float/Decimal / Unit coefficient requires builtin int/float/Decimal"
        )
    decimal = value
    if not decimal.is_finite():
        return invalid("单位系数必须有限 / Unit coefficient must be finite")
    parts = decimal.as_tuple()
    # 通过 Decimal 构造整数，不触发 Python 十进制字符串位数限制。 / Construct an integer via Decimal, avoiding Python's decimal-string digit limit.
    coefficient = int(Decimal((parts.sign, parts.digits, 0)))
    return Ok((coefficient, -cast("int", parts.exponent)))


def _exact(value: ExactValue) -> BindingResult[Rational]:
    if type(value) is Rational:
        return Ok(value)
    if type(value) not in (int, Fraction, Decimal):
        return invalid(
            "需要内置精确数值域 / A builtin exact numeric domain is required"
        )
    return Rational.from_value(cast("int | Fraction | Decimal", value))


def _coefficient(
    value: DecimalCoefficient,
) -> BindingResult[int | float | tuple[int, int]]:
    if type(value) is int:
        return Ok(value)
    if type(value) is float:
        if not isfinite(value):
            return invalid("单位系数必须有限 / Unit coefficient must be finite")
        return Ok(value)
    return cast("BindingResult[int | float | tuple[int, int]]", _decimal_parts(value))


@register_runtime_unit
@dataclass(frozen=True, slots=True, eq=False)
class Unit:
    """唯一 Rust 运行时单位的薄门面。 / Thin facade over one Rust runtime unit.

    Attributes:
        _handle: 原生单位，不保存 Python 系数镜像。 / Native unit without Python coefficient mirrors.
    """

    _handle: _native._QuantityUnit

    @property
    def name(self) -> str:
        """原生名称，不保存Python镜像。 / Native name without a Python mirror."""
        return self._handle.descriptor()[0]

    @property
    def symbol(self) -> str:
        """原生显示符号，不用于证明量纲。 / Native display symbol, not dimensional evidence."""
        return self._handle.descriptor()[1]

    @property
    def powers(self) -> tuple[int, ...]:
        """真实原生十维指数的独立快照。 / Independent snapshot of the actual native ten powers."""
        return tuple(self._handle.descriptor()[2])

    @property
    def is_affine(self) -> bool:
        """零偏移也保留点身份。 / Retain point identity even at zero offset."""
        return self._handle.descriptor()[4] is not None

    def to_si(self, value: Any) -> BindingResult[Any]:
        """按既有精确/Float64政策导出SI值，显式返回Result。 / Export SI using existing exact/Float64 policies, returning Result explicitly.

        Args:
            value: 原始内置数值域。 / Original builtin numeric domain.

        Returns:
            SI数值或保留来源的失败；Quantity派发不将该Result当作SI数据。
            SI value or original failure; Quantity dispatch does not treat this Result as SI data.
        """
        from ospf_python._binding.unit_conversion import convert_unit_value

        return convert_unit_value(unit=self, value=value, reverse=False)

    def from_si(self, value: Any) -> BindingResult[Any]:
        """将SI值转为此单位，显式返回Result。 / Convert SI into this unit, returning Result explicitly.

        Args:
            value: 原始SI数值。 / Original SI numeric value.

        Returns:
            原数值域输出或保留来源的失败。 / Original-domain output or original failure.
        """
        from ospf_python._binding.unit_conversion import convert_unit_value

        return convert_unit_value(unit=self, value=value, reverse=True)

    @classmethod
    def create(
        cls,
        *,
        name: str,
        symbol: str,
        powers: tuple[int, ...],
        scale: DecimalCoefficient = 1,
        offset: DecimalCoefficient | None = None,
    ) -> BindingResult[Unit]:
        """原子创建带显式量纲的单位。 / Create a unit with explicit dimensions atomically.

        Args:
            name: 元数据名称。 / Metadata name.
            symbol: 显示符号，不用于猜测量纲。 / Display symbol, never dimension inference.
            powers: 质量、长度、时间、电流、温度、物质、发光、信息、平面角、立体角十指数。 / Ten powers: mass, length, time, current, temperature, amount, luminous intensity, information, plane angle, solid angle.
            scale: 有限非零比例，float 按二进制值精确导入。 / Finite nonzero scale; floats import their exact binary values.
            offset: None 为线性，含零的数值为 affine 点。 / None means linear; any value including zero means an affine point.

        Returns:
            原生单位或明确的输入/精度失败。 / Native unit or explicit input/precision failure.
        """
        if type(name) is not str or type(symbol) is not str:
            return invalid(
                "名称和符号必须为内置 str / Name and symbol must be builtin str"
            )
        if (
            type(powers) is not tuple
            or len(powers) != 10
            or any(type(p) is not int for p in powers)
        ):
            return invalid(
                "需要十个内置整数指数 / Ten builtin integer powers are required"
            )

        scale_value = _coefficient(scale)
        if isinstance(scale_value, Failed):
            return scale_value
        offset_value: int | float | tuple[int, int] | None = None
        if offset is not None:
            encoded_offset = _coefficient(offset)
            if isinstance(encoded_offset, Failed):
                return encoded_offset
            offset_value = encoded_offset.unwrap()
        return invoke(
            lambda: _native._create_quantity_unit_encoded(
                name=name,
                symbol=symbol,
                powers=list(powers),
                scale=scale_value.unwrap(),
                offset=offset_value,
            )
        ).map(cls)

    def descriptor(self) -> UnitDescriptor:
        """返回独立元数据快照，无可变内核镜像。 / Return independent metadata, not a mutable kernel mirror."""
        name, symbol, powers, scale, offset = self._handle.descriptor()
        return name, symbol, tuple(powers), scale, offset

    def same_dimension(self, other: Unit) -> BindingResult[bool]:
        """比较 Rust 量纲。 / Compare Rust dimensions.

        Args:
            other: 另一个原生单位。 / Another native unit.

        Returns:
            比较结果或输入失败。 / Comparison or input failure.
        """
        if type(other) is not Unit:
            return invalid("需要原生单位 / A native unit is required")
        return invoke(lambda: (self._handle.same_dimension(other._handle), None))

    def same_unit(self, other: Unit) -> BindingResult[bool]:
        """按 Rust 规则比较单位而非名称/符号。 / Compare Rust rules, not names/symbols.

        Args:
            other: 另一个原生单位。 / Another native unit.

        Returns:
            比较结果或输入失败。 / Comparison or input failure.
        """
        if type(other) is not Unit:
            return invalid("需要原生单位 / A native unit is required")
        return invoke(lambda: (self._handle.same_unit(other._handle), None))

    def convert_exact(
        self, *, value: ExactValue, target: Unit
    ) -> BindingResult[Rational]:
        """用 Rust 物理量执行精确转换，不隐式舍入为 Decimal。 / Convert with Rust quantities exactly, without implicit Decimal rounding.

        Args:
            value: 精确值，Decimal 按其存储值导入。 / Exact value; Decimal imports its stored value.
            target: 显式目标单位。 / Explicit target unit.

        Returns:
            精确 Rational 或 Failed。 / Exact Rational or Failed.
        """
        if type(target) is not Unit:
            return invalid("需要原生目标单位 / A native target unit is required")
        return _exact(value).flat_map(
            lambda exact: invoke(
                lambda: self._handle.convert_exact(
                    value=exact._handle, target=target._handle
                )
            ).map(Rational)
        )

    def convert_float64(self, *, value: float, target: Unit) -> BindingResult[float]:
        """执行显式近似的有限 Float64 转换。 / Perform an explicitly approximate finite Float64 conversion.

        Args:
            value: 内置 float，不调用外部 __float__。 / Builtin float; no external __float__ calls.
            target: 显式目标单位。 / Explicit target unit.

        Returns:
            有限结果或 Failed；结果下溢遵循 Float64。 / Finite result or Failed; result underflow follows Float64.
        """
        if type(value) is not float or type(target) is not Unit:
            return invalid(
                "需要内置 float 和原生目标单位 / Builtin float and native target unit required"
            )
        return invoke(
            lambda: self._handle.convert_float64(value=value, target=target._handle)
        )

    def convert_decimal(
        self,
        *,
        value: ExactValue,
        target: Unit,
        context: Context | None = None,
        exact: bool = True,
    ) -> BindingResult[Decimal]:
        """原生精确换算后显式导出 Decimal。 / Convert exactly in Rust, then export Decimal explicitly.

        Args:
            value: 精确输入值，不读取 Decimal 运算精度。 / Exact input, independent of Decimal arithmetic precision.
            target: 原生目标单位。 / Native target unit.
            context: 仅用于输出舍入的上下文。 / Context used only for output rounding.
            exact: 默认拒绝输出数值损失。 / Reject numeric loss at export by default.

        Returns:
            输出 Decimal 或原始换算/输出失败。 / Decimal or the original conversion/export failure.
        """
        if (context is not None and not issubclass(type(context), Context)) or type(
            exact
        ) is not bool:
            return invalid(
                "需要 Decimal Context 和 bool / Decimal Context and bool required"
            )
        return self.convert_exact(value=value, target=target).flat_map(
            lambda converted: converted.to_decimal(context=context, exact=exact)
        )

    def binary_exact(
        self,
        *,
        value: ExactValue,
        other: ExactValue,
        other_unit: Unit,
        subtract: bool = False,
    ) -> BindingResult[tuple[Rational, Unit]]:
        """执行原生 checked 加减，返回温度点或温差单位。 / Perform native checked addition/subtraction, returning point or difference units.

        Args:
            value: 左精确值。 / Left exact value.
            other: 右精确值。 / Right exact value.
            other_unit: 右单位。 / Right unit.
            subtract: True 为相减。 / True selects subtraction.

        Returns:
            精确值及实际 Rust 输出单位或 Failed。 / Exact value and actual Rust output unit, or Failed.
        """
        if type(other_unit) is not Unit or type(subtract) is not bool:
            return invalid(
                "需要原生单位及 bool 运算选择 / Native unit and bool operation selector required"
            )
        return _exact(value).flat_map(
            lambda left: _exact(other).flat_map(
                lambda right: invoke(
                    lambda: self._handle.binary_exact(
                        value=left._handle,
                        other=right._handle,
                        other_unit=other_unit._handle,
                        subtract=subtract,
                    )
                ).map(lambda result: (Rational(result[0]), Unit(result[1])))
            )
        )

    def to_json(self) -> str:
        """导出版本化 Rust 元数据快照。 / Export versioned Rust metadata."""
        return self._handle.to_json()

    @classmethod
    def from_json(cls, text: str) -> BindingResult[Unit]:
        """恢复并验证版本化单位快照。 / Restore and validate versioned unit metadata.

        Args:
            text: 仅含单位元数据的 JSON。 / JSON containing unit metadata only.

        Returns:
            新单位或 Failed，不恢复 Python callable。 / New unit or Failed; Python callables are not restored.
        """
        if type(text) is not str:
            return invalid("单位快照必须为内置 str / Unit snapshot must be builtin str")
        return invoke(lambda: _native._quantity_unit_from_json(text)).map(cls)
