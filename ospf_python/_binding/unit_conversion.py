"""内置 Rust 单位及开放回调的联合派发候选。 / Joint dispatch candidate for Rust builtin units and open callbacks."""

from __future__ import annotations

import builtins
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Context, Decimal
from fractions import Fraction
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any, cast

from ospf_python import _native
from ospf_python._binding import quantity_conversion as _quantity_conversion
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.result import (
    BindingResult,
    FailureContext,
    invalid,
    unsupported,
)
from ospf_python._binding.unit_registry import Family, native_family
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python.quantities.quantity.numeric_adapter import NumericAdapter

_NATIVE_UNIT_TYPE = _native._QuantityUnit


@dataclass(frozen=True, slots=True)
class _Standard:
    value: Rational | float
    unit: Unit
    domain: type[Any]
    adapter: NumericAdapter[Any] | None = None


def _adapter_result(returned: object) -> BindingResult[Any]:
    mro = type.__getattribute__(type(returned), "__mro__")
    if any(base is Ok for base in mro):
        return Ok(cast("Ok[Any, Any, Any]", returned).value)
    if any(base is Result for base in mro):
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message="数值适配器返回失败或未支持结果 / Numeric adapter returned a failed or unsupported Result",
                value=FailureContext(
                    source="ospf-python",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="QUANTITY_NUMERIC_ADAPTER",
                    callback_result=cast("Result[Any, Any, Any]", returned),
                ),
            )
        )
    return invalid("数值适配器必须返回 Result / Numeric adapter must return Result")


def _import_value(value: Any) -> BindingResult[tuple[Rational | float, type[Any]]]:
    domain = type(value)
    if domain is float:
        return Ok((value, domain))
    if domain is Floating:
        raw = value.value
        if type(raw) is float:
            return Ok((raw, domain))
        if type(raw) is int:
            return (
                Rational.from_value(raw)
                .flat_map(lambda exact: exact.to_float())
                .map(lambda output: (output, domain))
            )
        return invalid(
            "Floating 需要内置 float 或无损整数载荷 / Floating requires builtin float or a lossless integer payload"
        )
    if domain is Rational:
        return Ok((value, domain))
    if domain is PublicRational:
        return Rational.create(
            numerator=value.numerator, denominator=value.denominator
        ).map(lambda result: (result, domain))
    if any(domain is supported for supported in (int, Fraction, Decimal)):
        return Rational.from_value(value).map(lambda result: (result, domain))
    return unsupported(
        "内置单位需要明确数值域，不隐式 float 化 / Builtin units require an explicit numeric domain, without implicit float coercion"
    )


class _Dispatch:
    def __init__(
        self,
        *,
        context: Context | None,
        exact: bool,
        numeric_adapter: NumericAdapter[Any] | None = None,
    ) -> None:
        self.context = context
        self.exact = exact
        self.numeric_adapter = numeric_adapter
        self.failure: BindingResult[Any] | None = None
        self.standard: _Standard | None = None
        # 外部 SI 快照只存活于本次调用，直到工厂完成。
        # External SI snapshots live only within this call, through factory completion.
        self.exports: list[Any] = []

    def checked(self, result: BindingResult[Any]) -> tuple[bool, Any]:
        if isinstance(result, Failed):
            self.failure = result
            return False, None
        return True, result.unwrap()

    def export(self, standard: _Standard) -> BindingResult[Any]:
        value, domain = standard.value, standard.domain
        if standard.adapter is not None:
            fraction = Fraction(*cast("Rational", value).as_integer_ratio())
            return _adapter_result(standard.adapter.from_fraction(fraction))
        if domain in (float, Floating):
            return Ok(Floating(cast("float", value)) if domain is Floating else value)
        rational = cast("Rational", value)
        if domain is Rational:
            return Ok(rational)
        if domain is Decimal:
            return rational.to_decimal(context=self.context, exact=self.exact)
        numerator, denominator = rational.as_integer_ratio()
        if domain is PublicRational:
            return Ok(PublicRational(numerator, denominator))
        if domain is int and denominator == 1:
            return Ok(numerator)
        return Ok(Fraction(numerator, denominator))

    def unit(self, *, unit: Any, family: Family) -> BindingResult[Unit]:
        if family.handle_descriptor is not None:
            if type(unit._handle) is not _NATIVE_UNIT_TYPE:
                return invalid("无效原生单位句柄 / Invalid native unit handle")
            # 仅本次调用保活原生句柄；外部适配器改写原门面不改变已采集的源。
            # Retain this call's native handle; adapter mutation of the input facade cannot rewrite the captured source.
            return Ok(Unit(unit._handle))
        return Unit.create(
            name=family.cls.__name__,
            symbol="",
            powers=family.powers,
            scale=unit._factor,
            offset=unit._offset if family.affine else None,
        )

    def convert(self, *, value: _Standard, target: Unit) -> BindingResult[_Standard]:
        source_descriptor = value.unit._handle.descriptor()
        target_descriptor = target._handle.descriptor()
        if source_descriptor[2] == target_descriptor[2] and (
            (source_descriptor[4] is None) != (target_descriptor[4] is None)
        ):
            return invalid(
                "温度点与线性差不能隐式互换 / Affine points and linear differences cannot be implicitly interchanged"
            )
        if value.adapter is None and value.domain in (float, Floating):
            return value.unit.convert_float64(
                value=cast("float", value.value), target=target
            ).map(lambda output: _Standard(output, target, value.domain))
        return value.unit.convert_exact(
            value=cast("Rational", value.value), target=target
        ).map(lambda output: _Standard(output, target, value.domain, value.adapter))

    def import_value(self, *, value: Any, unit: Unit) -> BindingResult[_Standard]:
        if self.numeric_adapter is None:
            return _import_value(value).map(
                lambda imported: _Standard(imported[0], unit, imported[1])
            )
        imported = _adapter_result(self.numeric_adapter.to_fraction(value))
        if isinstance(imported, Failed):
            return imported
        fraction = imported.unwrap()
        if type(fraction) is not Fraction:
            return invalid(
                "数值适配器必须导出内置 Fraction / Numeric adapter must export builtin Fraction"
            )
        return Rational.from_value(fraction).map(
            lambda result: _Standard(result, unit, type(value), self.numeric_adapter)
        )

    def source(self, *, unit: Any, callback: Any, value: Any) -> BindingResult[Any]:
        family = native_family(unit=unit, callback=callback, direction="source")
        if family is None:
            return Ok(callback(value))

        def publish(standard: _Standard) -> _Standard:
            self.standard = standard
            return standard

        def from_unit(source: Unit) -> BindingResult[Any]:
            descriptor = source._handle.descriptor()
            return Unit.create(
                name="SI",
                symbol="",
                powers=tuple(descriptor[2]),
                offset=0 if descriptor[4] is not None else None,
            ).flat_map(
                lambda standard: self.import_value(value=value, unit=source).flat_map(
                    lambda imported: self.convert(value=imported, target=standard)
                )
            )

        return self.unit(unit=unit, family=family).flat_map(from_unit).map(publish)

    def target(self, *, unit: Any, callback: Any, value: Any) -> BindingResult[Any]:
        family = native_family(unit=unit, callback=callback, direction="target")
        if family is None:
            if self.standard is not None and value is self.standard:
                exported = self.export(value)
                if isinstance(exported, Failed):
                    return exported
                value = exported.unwrap()
                self.exports.append(value)
            return Ok(callback(value))

        def from_unit(target: Unit) -> BindingResult[Any]:
            if self.standard is not None and value is self.standard:
                return self.convert(value=value, target=target).flat_map(self.export)
            # 开放源没有量纲证明；仅按目标的 SI 数值域解释，不伪称维度已验证。
            # An open source has no dimensional proof; interpret target SI without claiming validation.
            descriptor = target._handle.descriptor()
            return Unit.create(
                name="SI",
                symbol="",
                powers=tuple(descriptor[2]),
                offset=0 if descriptor[4] is not None else None,
            ).flat_map(
                lambda standard: self.import_value(value=value, unit=standard).flat_map(
                    lambda imported: self.convert(
                        value=imported,
                        target=target,
                    ).flat_map(self.export)
                )
            )

        return self.unit(unit=unit, family=family).flat_map(from_unit)

    def prepare(
        self, *, unit: Any, callback: Any, direction: str
    ) -> tuple[Callable[[Any], Any], bool]:
        if direction == "source":
            if native_family(unit=unit, callback=callback, direction=direction) is None:
                return cast("Callable[[Any], Any]", callback), False
            return lambda value: self.checked(
                self.source(unit=unit, callback=callback, value=value)
            ), True
        return lambda value: self.checked(
            self.target(unit=unit, callback=callback, value=value)
        ), True


def convert_quantity(
    *,
    owner: object,
    target: object,
    context: Context | None = None,
    exact: bool = True,
    numeric_adapter: NumericAdapter[Any] | None = None,
) -> BindingResult[Any]:
    """联合 Rust 单位数学及开放回调，供公开转换候选使用。 / Combine Rust unit arithmetic and open callbacks for the public conversion candidate.

    Args:
        owner: 提供 unit/value 的物理量。 / Quantity exposing unit/value.
        target: 内置或开放目标单位。 / Builtin or open target unit.
        context: 仅在 Decimal 输出边界使用。 / Used only at Decimal output boundaries.
        exact: 默认拒绝 Decimal 输出损失。 / Reject Decimal export loss by default.
        numeric_adapter: 显式自定义数值导入/输出策略。 / Explicit custom numeric import/export policy.

    Returns:
        工厂结果或保留来源的失败。 / Factory output or failure with provenance.
    """
    if (context is not None and not issubclass(type(context), Context)) or type(
        exact
    ) is not bool:
        return invalid(
            "需要 Decimal Context 和 bool / Decimal Context and bool required"
        )
    dispatch = _Dispatch(context=context, exact=exact, numeric_adapter=numeric_adapter)
    return _execute(
        owner=owner,
        target=target,
        dispatch=dispatch,
        namespace=_quantity_conversion.quantity_module.__dict__,
    )


def _execute(
    *, owner: object, target: object, dispatch: _Dispatch, namespace: dict[str, Any]
) -> BindingResult[Any]:
    completed, output, failure = _native._convert_quantity_dispatched(
        owner=owner,
        target=target,
        namespace=namespace,
        builtins=builtins.__dict__,
        prepare=lambda unit, callback, direction: dispatch.prepare(
            unit=unit, callback=callback, direction=direction
        ),
    )
    if failure is not None:
        stage, error = failure
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message=f"物理量派发协议失败 / Quantity dispatch protocol failed: {stage}",
                value=FailureContext(
                    source="ospf-python-native",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="QUANTITY_DISPATCH",
                    callback_exception=error,
                ),
            )
        )
    if not completed:
        assert dispatch.failure is not None
        return dispatch.failure
    return Ok(output)


def convert_unit_value(*, unit: Unit, value: Any, reverse: bool) -> BindingResult[Any]:
    """原生Unit的直接SI接口共用已受检控制面。 / Direct SI methods on native Unit share the checked control plane.

    Args:
        unit: 唯一真实原生单位。 / One real native unit.
        value: 原数值域输入。 / Original-domain input.
        reverse: True从SI导入，否则导出。 / Import from SI when True, export otherwise.

    Returns:
        数值或保留原异常/原生来源的失败。 / Numeric output or original external/native failure.
    """
    try:
        if type(unit) is not Unit or type(unit._handle) is not _NATIVE_UNIT_TYPE:
            return invalid("需要真实原生单位 / A real native unit is required")
        descriptor = unit._handle.descriptor()
        standard = Unit.create(
            name="SI",
            symbol="",
            powers=tuple(descriptor[2]),
            offset=0 if descriptor[4] is not None else None,
        )
        if isinstance(standard, Failed):
            return standard
        source, target = (
            (standard.unwrap(), unit) if reverse else (unit, standard.unwrap())
        )
        return _execute(
            owner=SimpleNamespace(value=value, unit=source),
            target=target,
            dispatch=_Dispatch(context=None, exact=True),
            namespace={"Quantity": lambda *, value, unit: value},
        )
    except Exception as error:
        return Failed(
            ExErr(
                _code=ErrorCode.APPLICATION_ERROR,
                _message="原生单位SI边界失败 / Native unit SI boundary failed",
                value=FailureContext(
                    source="ospf-python",
                    category="APPLICATION_ERROR",
                    rust_code=None,
                    error_class="QUANTITY_UNIT_VALUE",
                    callback_exception=error,
                ),
            )
        )
