"""数量极值与范围的薄适配，不实现另一套单位数学。 / Thin quantity ordering adapter, not a second unit kernel."""

from __future__ import annotations

from fractions import Fraction
from typing import TYPE_CHECKING, Any

from ospf_python import _native
from ospf_python._binding import unit_conversion as _conversion
from ospf_python._binding.numeric import Rational
from ospf_python._binding.result import BindingResult, FailureContext, invalid, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ospf_python.quantities.quantity.numeric_adapter import NumericAdapter


class _Keys:
    def __init__(self, numeric_adapter: NumericAdapter[Any] | None) -> None:
        self.dispatch = _conversion._Dispatch(
            context=None, exact=True, numeric_adapter=numeric_adapter
        )
        self.failure: BindingResult[Any] | None = None
        self.affine: tuple[tuple[int, ...], bool] | None = None

    def prepare(
        self, parts: tuple[Any, Any, Any]
    ) -> tuple[bool, int, Any, tuple[int, ...] | None]:
        unit, callback, value = parts
        # 每个 key 只派发一次，以本次发布的 SI token 证明原生来源。
        # Dispatch once per key; only this call's published SI token proves native provenance.
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
        affine = descriptor[4] is not None
        if self.affine is None:
            self.affine = (powers, affine)
        elif self.affine[0] == powers and self.affine[1] != affine:
            self.failure = invalid(
                "数量比较不能混合点与线性差 / Quantity comparison cannot mix points and linear differences"
            )
            return False, 2, None, None
        if type(standard.value) is Rational:
            return True, 0, standard.value._handle, powers
        return True, 1, standard.value, powers

    @staticmethod
    def export(kind: int, value: Any) -> Any:
        # 只在混合开放比较边界导出规范 Fraction，不调用 Decimal context 或 adapter 输出。
        # Export canonical Fraction only for mixed open comparisons, without Decimal context or adapter output.
        return Fraction(*value.as_integer_ratio()) if kind == 0 else value

    def publish(
        self,
        result: tuple[
            bool,
            Any,
            _native.Failure | None,
            tuple[str, Exception, int | None] | None,
        ],
    ) -> BindingResult[Any]:
        complete, value, failure, external = result
        if external is not None:
            stage, error, index = external
            return Failed(
                ExErr(
                    _code=ErrorCode.APPLICATION_ERROR,
                    _message=f"数量比较协议失败 / Quantity ordering protocol failed: {stage}",
                    value=FailureContext(
                        source="ospf-python-native",
                        category="APPLICATION_ERROR",
                        rust_code=None,
                        error_class="QUANTITY_ORDERING",
                        callback_exception=error,
                        callback_index=index,
                    ),
                )
            )
        if failure is not None:
            return invoke(lambda: (None, failure))
        if not complete:
            assert self.failure is not None
            return self.failure
        return Ok(value)


def select(
    *,
    items: Iterable[Any],
    maximum: bool,
    numeric_adapter: NumericAdapter[Any] | None,
) -> BindingResult[Any]:
    """原生流式选择，返回原输入对象。 / Select in native streaming order, returning the original item.

    Args:
        items: 单次迭代的数量。 / Quantities consumed in one pass.
        maximum: True 选最大，否则选最小。 / Select maximum when True, minimum otherwise.
        numeric_adapter: 内置单位的显式数值导入策略。 / Explicit numeric import policy for builtin units.

    Returns:
        保留首个平局对象或原始来源的失败。 / First tied item or failure retaining its provenance.
    """
    keys = _Keys(numeric_adapter)
    return keys.publish(
        _native._quantity_extreme(
            items=items, maximum=maximum, prepare=keys.prepare, export=keys.export
        )
    )


def contains(
    *, bounds: object, quantity: object, numeric_adapter: NumericAdapter[Any] | None
) -> BindingResult[bool]:
    """原生闭区间判断，按 min/max/value 顺序取 SI。 / Check an inclusive range, importing SI in min/max/value order.

    Args:
        bounds: 提供 min_qty/max_qty 的范围。 / Range exposing min_qty/max_qty.
        quantity: 待检查数量。 / Candidate quantity.
        numeric_adapter: 内置单位的显式数值导入策略。 / Explicit numeric import policy for builtin units.

    Returns:
        包含判断或保留来源的失败。 / Containment or failure retaining its provenance.
    """
    keys = _Keys(numeric_adapter)
    return keys.publish(
        _native._quantity_contains(
            bounds=bounds, quantity=quantity, prepare=keys.prepare, export=keys.export
        )
    )
