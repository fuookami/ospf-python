"""自然四则的数值域适配；固定 Rust 负责单位数学与协议控制。 / Numeric adaptation for natural arithmetic; pinned Rust owns unit math and protocol control."""

from __future__ import annotations

import builtins
from decimal import Context, Decimal
from fractions import Fraction
from importlib import import_module
from typing import TYPE_CHECKING, Any, cast

from ospf_python import _native
from ospf_python._binding import unit_conversion as _conversion
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.result import (
    BindingResult,
    FailureContext,
    invalid,
    invoke,
    unsupported,
)
from ospf_python._binding.unit_registry import arithmetic_family
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

if TYPE_CHECKING:
    from ospf_python.quantities.quantity.numeric_adapter import NumericAdapter

_DOMAINS = (int, Fraction, PublicRational, Rational, Decimal, float, Floating)


class _Arithmetic:
    def __init__(
        self,
        *,
        operation: str,
        context: Context | None,
        exact: bool,
        numeric_adapter: NumericAdapter[Any] | None,
    ) -> None:
        self.operation = operation
        self.dispatch = _conversion._Dispatch(
            context=context, exact=exact, numeric_adapter=numeric_adapter
        )
        self.left: Unit | None = None
        self.right: Unit | None = None
        self.failure: BindingResult[Any] | None = None
        self.originals: list[tuple[Any, object]] = []

    def native_unit(self, unit: Any) -> BindingResult[Unit | None]:
        family = arithmetic_family(unit)
        if family is None:
            return Ok(None)
        if family.handle_descriptor is not None:
            return self.dispatch.unit(unit=unit, family=family).map(lambda value: value)
        return Unit.create(
            name=family.cls.__name__,
            symbol=object.__getattribute__(unit, "_symbol"),
            powers=family.powers,
            scale=object.__getattribute__(unit, "_factor"),
            offset=object.__getattribute__(unit, "_offset") if family.affine else None,
        ).map(lambda value: value)

    def units(self, parts: tuple[Any, Any]) -> bool:
        left, right = parts
        self.originals.append(
            (left, vars(type(left)).get("symbol") if type(type(left)) is type else None)
        )
        source = self.native_unit(left)
        if isinstance(source, Failed):
            self.failure = source
            return False
        self.left = source.unwrap()
        if self.operation in ("add", "subtract"):
            self.originals.append(
                (
                    right,
                    vars(type(right)).get("symbol")
                    if type(type(right)) is type
                    else None,
                )
            )
            target = self.native_unit(right)
            if isinstance(target, Failed):
                self.failure = target
                return False
            self.right = target.unwrap()
            if (self.left is None or self.right is None) and left is not right:
                self.failure = unsupported(
                    "开放四则需要相同单位对象或明确的原生元数据 / Open arithmetic requires the same unit object or explicit native metadata"
                )
                return False
        return True

    def publish_unit(self, unit: Unit | None) -> Any:
        if unit is not None:
            descriptor = unit._handle.descriptor()
            for original, symbol in self.originals:
                if (
                    type(type(original)) is not type
                    or vars(type(original)).get("symbol") is not symbol
                ):
                    continue
                current = self.native_unit(original)
                if not isinstance(current, Failed) and current.unwrap() is not None:
                    candidate = current.unwrap()
                    assert candidate is not None
                    if candidate._handle.descriptor() == descriptor:
                        return original
        return unit

    def import_value(
        self, value: Any
    ) -> BindingResult[tuple[Rational | float, type[Any]]]:
        adapter = self.dispatch.numeric_adapter
        if adapter is None:
            return _conversion._import_value(value)
        imported = _conversion._adapter_result(adapter.to_fraction(value))
        if isinstance(imported, Failed):
            return imported
        fraction = imported.unwrap()
        if type(fraction) is not Fraction:
            return invalid(
                "数值适配器必须导出内置 Fraction / Numeric adapter must export builtin Fraction"
            )
        return Rational.from_value(fraction).map(lambda exact: (exact, type(value)))

    def math(
        self, *, left: Rational | float, right: Rational | float
    ) -> BindingResult[tuple[Rational | float, Unit | None]]:
        scalar = self.operation in ("multiply", "divide")
        if self.left is None:
            # 外部同一单位仅承诺数值策略，不制造虚假量纲；adapter 的数学仍走 Rust Rational。
            # One opaque unit proves no dimension; adapter arithmetic still uses Rust Rational without a fake unit.
            result = getattr(cast("Rational", left), self.operation)(right)
            return cast("BindingResult[Rational]", result).map(
                lambda value: (value, None)
            )
        source = self.left._handle
        if type(left) is float:
            output = (
                invoke(
                    lambda: source.scalar_float64(
                        value=left,
                        scalar=cast("float", right),
                        divide=self.operation == "divide",
                    )
                )
                if scalar
                else invoke(
                    lambda: source.binary_float64(
                        value=left,
                        other=cast("float", right),
                        other_unit=cast("Unit", self.right)._handle,
                        subtract=self.operation == "subtract",
                    )
                )
            )
            return output.map(lambda pair: (pair[0], Unit(pair[1])))
        output_exact = (
            invoke(
                lambda: source.scalar_exact(
                    value=cast("Rational", left)._handle,
                    scalar=cast("Rational", right)._handle,
                    divide=self.operation == "divide",
                )
            )
            if scalar
            else invoke(
                lambda: source.binary_exact(
                    value=cast("Rational", left)._handle,
                    other=cast("Rational", right)._handle,
                    other_unit=cast("Unit", self.right)._handle,
                    subtract=self.operation == "subtract",
                )
            )
        )
        return output_exact.map(lambda pair: (Rational(pair[0]), Unit(pair[1])))

    def execute(
        self, *, left: Any, right: Any
    ) -> BindingResult[tuple[Any, Unit | None]]:
        imported_left = self.import_value(left)
        if isinstance(imported_left, Failed):
            return imported_left
        imported_right = self.import_value(right)
        if isinstance(imported_right, Failed):
            return imported_right
        a, left_domain = imported_left.unwrap()
        b, right_domain = imported_right.unwrap()
        adapter = self.dispatch.numeric_adapter
        domain = (
            left_domain
            if adapter is not None
            else next(
                kind
                for kind in reversed(_DOMAINS)
                if kind is left_domain or kind is right_domain
            )
        )
        if adapter is None and domain in (float, Floating):
            # 混合域仅在这里显式接入 Float64；默认必须证明精确输入未损失。
            # Mixed domains enter Float64 only here; exact inputs must be lossless by default.
            if type(a) is Rational:
                converted = a.to_float(exact=self.dispatch.exact)
                if isinstance(converted, Failed):
                    return converted
                a = converted.unwrap()
            if type(b) is Rational:
                converted = b.to_float(exact=self.dispatch.exact)
                if isinstance(converted, Failed):
                    return converted
                b = converted.unwrap()
        output = self.math(left=a, right=b)
        if isinstance(output, Failed):
            return output
        value, unit = output.unwrap()
        if unit is None:
            assert adapter is not None and type(value) is Rational
            exported = _conversion._adapter_result(
                adapter.from_fraction(Fraction(*value.as_integer_ratio()))
            )
        else:
            exported = self.dispatch.export(
                _conversion._Standard(value, unit, domain, adapter)
            )
        return exported.map(lambda value: (value, unit))

    def compute(self, parts: tuple[Any, Any]) -> tuple[bool, bool, Any, Any]:
        left, right = parts
        if self.dispatch.numeric_adapter is None and (
            self.left is None
            or not all(
                any(type(value) is domain for domain in _DOMAINS) for value in parts
            )
        ):
            if self.left is not None and (
                self.left._handle.descriptor()[4] is not None
                or (
                    self.right is not None
                    and not self.left._handle.same_unit(self.right._handle)
                )
            ):
                self.failure = unsupported(
                    "开放数值需要相同线性单位或显式 NumericAdapter / Open numeric operands require identical linear units or an explicit NumericAdapter"
                )
                return False, False, None, None
            return True, False, None, self.left
        result = self.execute(left=left, right=right)
        if isinstance(result, Failed):
            self.failure = result
            return False, True, None, None
        value, unit = result.unwrap()
        return True, True, value, self.publish_unit(unit)


_QUANTITY_NAMESPACE: dict[str, Any] | None = None


def _quantity_namespace() -> dict[str, Any]:
    """取 `ospf_python.quantities.quantity.quantity` 的模块字典，**只解析一次**。

    该模块已经由调用方导入，但 `import_module` 每次仍会走
    `_find_and_load` → `_gcd_import` 的检查链；实测每次算术调用因此多花 2–5 µs
    （`Quantity.multiply` 11,364 ns 的约 18%）。
    这里缓存结果，语义不变（同一个模块字典对象）。

    Cache the target module's `__dict__`. The module is already imported by the caller, yet
    `import_module` still walks `_find_and_load` -> `_gcd_import` on every call, costing
    2-5 us (about 18% of `Quantity.multiply`'s 11,364 ns).

    Returns:
        目标模块的 `__dict__`。 / The target module's namespace.
    """
    global _QUANTITY_NAMESPACE
    namespace = _QUANTITY_NAMESPACE
    if namespace is None:
        namespace = import_module("ospf_python.quantities.quantity.quantity").__dict__
        _QUANTITY_NAMESPACE = namespace
    return namespace


def calculate(
    *,
    owner: object,
    other: object,
    operation: str,
    context: Context | None,
    exact: bool,
    numeric_adapter: NumericAdapter[Any] | None,
) -> BindingResult[Any]:
    """执行自然四则的唯一默认路径。 / Execute the sole default path for natural arithmetic.

    Args:
        owner: 左数量。 / Left quantity.
        other: 右数量或标量。 / Right quantity or scalar.
        operation: 已知四则名称。 / Known operation name.
        context: 仅 Decimal 最终出口上下文。 / Final Decimal export context only.
        exact: 拒绝 Decimal 出口/混合 Float64 导入损失。 / Reject Decimal export/mixed Float64 import loss.
        numeric_adapter: 显式导入双方并重建一次输出。 / Explicit import of both operands and one output reconstruction.

    Returns:
        工厂输出或保留原来源的失败，中断不捕获。 / Factory output or failure retaining provenance; interrupts propagate.
    """
    if (context is not None and not issubclass(type(context), Context)) or type(
        exact
    ) is not bool:
        return invalid(
            "需要 Decimal Context 和 bool / Decimal Context and bool required"
        )
    arithmetic = _Arithmetic(
        operation=operation,
        context=context,
        exact=exact,
        numeric_adapter=numeric_adapter,
    )
    complete, value, external = _native._quantity_arithmetic(
        owner=owner,
        other=other,
        operation=operation,
        namespace=_quantity_namespace(),
        builtins=builtins.__dict__,
        protocols=(arithmetic.units, arithmetic.compute),
    )
    if external is not None:
        stage, error = external
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message=f"物理量四则协议失败 / Quantity arithmetic protocol failed: {stage}",
                value=FailureContext(
                    source="ospf-python-native",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="QUANTITY_ARITHMETIC",
                    callback_exception=error,
                ),
            )
        )
    if not complete:
        assert arithmetic.failure is not None
        return arithmetic.failure
    return Ok(value)
