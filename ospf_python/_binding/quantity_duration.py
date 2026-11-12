"""时长单位派发的薄适配，舍入/控制由原生边界负责。 / Thin duration dispatch; native boundary owns rounding/control."""

from __future__ import annotations

import builtins
from decimal import Context, Decimal
from fractions import Fraction
from importlib import import_module
from typing import TYPE_CHECKING, Any

from ospf_python import _native
from ospf_python._binding import unit_conversion as _conversion
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python._binding.result import BindingResult, FailureContext, invalid, invoke
from ospf_python.math.algebra.number.floating import Floating
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

if TYPE_CHECKING:
    from ospf_python.quantities.quantity.numeric_adapter import NumericAdapter

_module = import_module("ospf_python.quantities.quantity.duration_extensions")
_TIME = (0, 0, 1, 0, 0, 0, 0, 0, 0, 0)


class _Duration:
    def __init__(
        self,
        *,
        context: Context | None,
        exact: bool,
        numeric_adapter: NumericAdapter[Any] | None,
    ) -> None:
        self.dispatch = _conversion._Dispatch(
            context=context, exact=exact, numeric_adapter=numeric_adapter
        )
        self.failure: BindingResult[Any] | None = None

    def constructor(self, parts: tuple[Any, int]) -> tuple[bool, bool, Any]:
        value, factor = parts
        if self.dispatch.numeric_adapter is None and not any(
            type(value) is domain
            for domain in (
                int,
                float,
                Fraction,
                Decimal,
                Rational,
                PublicRational,
                Floating,
            )
        ):
            return True, False, value
        result = Unit.create(
            name="duration", symbol="", powers=_TIME, scale=factor
        ).flat_map(
            lambda source: Unit.create(name="SI", symbol="", powers=_TIME).flat_map(
                lambda target: (
                    self.dispatch.import_value(value=value, unit=source)
                    .flat_map(
                        lambda imported: self.dispatch.convert(
                            value=imported, target=target
                        )
                    )
                    .flat_map(self.dispatch.export)
                )
            )
        )
        if isinstance(result, Failed):
            self.failure = result
            return False, True, None
        return True, True, result.unwrap()

    def source(
        self, parts: tuple[Any, Any, Any]
    ) -> tuple[bool, int, Any, tuple[int, ...] | None]:
        unit, callback, value = parts
        self.dispatch.standard = None
        result = self.dispatch.source(unit=unit, callback=callback, value=value)
        if isinstance(result, Failed):
            self.failure = result
            return False, 2, None, None
        value = result.unwrap()
        standard = self.dispatch.standard
        if standard is None or value is not standard:
            return True, 2, value, None
        descriptor = standard.unit._handle.descriptor()
        powers = tuple(descriptor[2])
        if powers == _TIME and descriptor[4] is not None:
            self.failure = invalid(
                "时长需要线性时间差，不接受时间点 / Duration requires a linear time difference, not an affine time point"
            )
            return False, 2, None, None
        if type(standard.value) is Rational:
            return True, 0, standard.value._handle, powers
        return True, 1, standard.value, powers

    @staticmethod
    def export(value: Any) -> Fraction:
        return Fraction(*value.as_integer_ratio())

    def publish(
        self,
        result: tuple[bool, Any, _native.Failure | None, tuple[str, Exception] | None],
    ) -> BindingResult[Any]:
        complete, value, failure, external = result
        if external is not None:
            stage, error = external
            return Failed(
                ExErr(
                    _code=ErrorCode.APPLICATION_ERROR,
                    _message=f"时长协议失败 / Duration protocol failed: {stage}",
                    value=FailureContext(
                        source="ospf-python-native",
                        category="APPLICATION_ERROR",
                        rust_code=None,
                        error_class="QUANTITY_DURATION",
                        callback_exception=error,
                    ),
                )
            )
        if failure is not None:
            return invoke(lambda: (None, failure))
        if not complete:
            assert self.failure is not None
            return self.failure
        return Ok(value)


def from_value(
    *,
    value: Any,
    factor: int,
    context: Context | None,
    exact: bool,
    numeric_adapter: NumericAdapter[Any] | None,
) -> BindingResult[Any]:
    """为自然构造入口复用原生单位转换。 / Reuse native unit conversion for natural constructors.

    Args:
        value: 原始数值或开放乘法输入。 / Original numeric or open multiplication input.
        factor: 固定小时/分钟到秒的比例。 / Fixed hour/minute-to-second scale.
        context: 仅最终 Decimal 出口的上下文。 / Final Decimal export context only.
        exact: 是否拒绝出口损失。 / Whether to reject export loss.
        numeric_adapter: 显式数值导入/输出策略。 / Explicit numeric import/export strategy.

    Returns:
        工厂结果或保留来源的失败。 / Factory output or failure retaining provenance.
    """
    if (context is not None and not issubclass(type(context), Context)) or type(
        exact
    ) is not bool:
        return invalid(
            "需要 Decimal Context 和 bool / Decimal Context and bool required"
        )
    duration = _Duration(context=context, exact=exact, numeric_adapter=numeric_adapter)
    return duration.publish(
        _native._quantity_duration_from(
            value=value,
            factor=factor,
            namespace=_module.__dict__,
            builtins=builtins.__dict__,
            prepare=duration.constructor,
        )
    )


def to_timedelta(
    *, owner: object, numeric_adapter: NumericAdapter[Any] | None
) -> BindingResult[Any]:
    """派发一次 SI 源并交原生时长适配。 / Dispatch one SI source into the native duration adapter.

    Args:
        owner: 提供 unit/value 的数量。 / Quantity exposing unit/value.
        numeric_adapter: 精确导入策略，不重建数值输出。 / Exact import strategy, without numeric reconstruction.

    Returns:
        timedelta 或当前开放工厂输出及原来源失败。 / Timedelta/current factory output or original failure.
    """
    duration = _Duration(context=None, exact=True, numeric_adapter=numeric_adapter)
    return duration.publish(
        _native._quantity_to_timedelta(
            owner=owner,
            namespace=_module.__dict__,
            builtins=builtins.__dict__,
            prepare=duration.source,
            export=duration.export,
        )
    )
