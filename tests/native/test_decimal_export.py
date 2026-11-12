"""原生精确值的 Decimal 输出合同。 / Decimal export contracts for native exact values."""

from __future__ import annotations

import asyncio
import gc
import sys
from concurrent.futures import ThreadPoolExecutor
from decimal import (
    ROUND_05UP,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
    Clamped,
    Context,
    Decimal,
    Inexact,
    Overflow,
    Rounded,
    Subnormal,
    Underflow,
    getcontext,
    localcontext,
)
from fractions import Fraction
from typing import Any

import pytest

from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

_ROUNDINGS = (
    ROUND_05UP,
    ROUND_CEILING,
    ROUND_DOWN,
    ROUND_FLOOR,
    ROUND_HALF_DOWN,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    ROUND_UP,
)
_LENGTH = (0, 1, 0, 0, 0, 0, 0, 0, 0, 0)


def _context(*, precision: int = 28, rounding: str = ROUND_HALF_EVEN) -> Context:
    context = Context(prec=precision, rounding=rounding)
    context.clear_traps()
    context.clear_flags()
    return context


def _rational(value: int | Fraction | Decimal) -> Rational:
    return Rational.from_value(value).unwrap()


def _unit(scale: int = 1) -> Unit:
    return Unit.create(name="length", symbol="m", powers=_LENGTH, scale=scale).unwrap()


@pytest.mark.parametrize("rounding", _ROUNDINGS)
@pytest.mark.parametrize("precision", (1, 2, 9, 28))
@pytest.mark.parametrize(
    "value",
    (
        Fraction(1, 3),
        Fraction(-1, 3),
        Fraction(1, 8),
        Fraction(-1, 8),
        Fraction(12345, 100),
        Fraction(1200),
        Fraction(0),
    ),
)
def test_every_rounding_mode_matches_decimal_value_flags_and_exactness(
    *, rounding: str, precision: int, value: Fraction
) -> None:
    context = _context(precision=precision, rounding=rounding)
    oracle = context.copy()
    expected = oracle.divide(Decimal(value.numerator), Decimal(value.denominator))
    source = _rational(value)
    before = source.to_json()
    rounded = source.to_decimal(context=context, exact=False).unwrap()
    assert rounded.as_tuple() == expected.as_tuple()
    assert context.flags == oracle.flags
    context.clear_flags()
    exact = source.to_decimal(context=context)
    if Fraction(expected) == value:
        assert exact.unwrap().as_tuple() == expected.as_tuple()
    else:
        assert isinstance(exact, Failed)
        assert exact.error.code is ErrorCode.DATA_LOSS
        assert exact.error.value.callback_exception is None
    assert context.flags == oracle.flags
    assert source.to_json() == before


@pytest.mark.parametrize("precision", (1, 3, 28, 100))
def test_current_context_is_used_without_copy_or_hidden_precision_change(
    precision: int,
) -> None:
    with localcontext(_context(precision=precision)) as context:
        result = _rational(Fraction(1, 3)).to_decimal(exact=False).unwrap()
        assert result == Decimal("0." + "3" * precision)
        assert context is getcontext()
        assert context.flags[Inexact] and context.flags[Rounded]
        assert context.prec == precision


def test_explicit_context_does_not_touch_current_context_or_clear_seeded_flags() -> (
    None
):
    explicit = _context(precision=2)
    explicit.flags[Clamped] = True
    with localcontext(_context(precision=1)) as current:
        assert _rational(Fraction(1, 8)).to_decimal(
            context=explicit, exact=False
        ).unwrap() == Decimal("0.12")
        assert explicit.flags[Clamped]
        assert explicit.flags[Inexact]
        assert not any(current.flags.values())
        assert current.prec == 1


def test_exactness_is_numeric_equality_not_flags_or_decimal_representation() -> None:
    context = _context(precision=2)
    context.flags[Inexact] = True
    context.flags[Underflow] = True
    result = _rational(1200).to_decimal(context=context).unwrap()
    assert result.as_tuple() == Decimal("1.2E3").as_tuple()
    assert context.flags[Inexact] and context.flags[Underflow]
    assert context.flags[Rounded]
    imported = _rational(Decimal("1.23000"))
    assert (
        imported.to_decimal(context=_context()).unwrap().as_tuple()
        == Decimal("1.23").as_tuple()
    )
    assert (
        _rational(Decimal("-0.00")).to_decimal().unwrap().as_tuple()
        == Decimal(0).as_tuple()
    )


@pytest.mark.parametrize("trap", (Inexact, Rounded, Overflow, Underflow))
@pytest.mark.parametrize("exact", (False, True))
def test_traps_retain_exception_type_traceback_and_context_flags(
    *, trap: Any, exact: bool
) -> None:
    context = _context(precision=2)
    context.Emin = -2
    context.Emax = 2
    context.traps[trap] = True
    value = (
        Fraction(10000)
        if trap is Overflow
        else Fraction(1, 100000)
        if trap is Underflow
        else Fraction(1, 3)
    )
    result = _rational(value).to_decimal(context=context, exact=exact)
    assert isinstance(result, Failed)
    error = result.error.value.callback_exception
    assert type(error) is trap
    assert error.__traceback__ is not None
    assert context.flags[trap]
    assert result.error.value.source == "python-decimal"
    assert result.error.value.callback_index is None
    expected = {
        Overflow: ErrorCode.OVERFLOW,
        Underflow: ErrorCode.UNDERFLOW,
        Inexact: ErrorCode.DATA_LOSS,
        Rounded: ErrorCode.DATA_LOSS,
    }
    assert result.error.code is expected[trap]


@pytest.mark.parametrize("exact", (False, True))
def test_untrapped_nonfinite_export_is_not_success(exact: bool) -> None:
    context = _context(precision=2)
    context.Emax = 2
    result = _rational(10000).to_decimal(context=context, exact=exact)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.OVERFLOW
    assert result.error.value.callback_exception is None
    assert context.flags[Overflow] and context.flags[Inexact]


@pytest.mark.parametrize("negative", (False, True))
def test_underflow_zero_requires_explicit_permission_and_preserves_sign(
    negative: bool,
) -> None:
    context = _context(precision=2)
    context.Emin = -2
    source = _rational(Fraction(-1 if negative else 1, 100000))
    result = source.to_decimal(context=context)
    assert isinstance(result, Failed) and result.error.code is ErrorCode.DATA_LOSS
    rounded = source.to_decimal(context=context, exact=False).unwrap()
    assert rounded.is_zero() and rounded.is_signed() is negative
    assert context.flags[Underflow] and context.flags[Subnormal]


@pytest.mark.parametrize("places", (5000, 10000))
def test_huge_values_do_not_use_float_string_digits_or_current_precision(
    places: int,
) -> None:
    value = Decimal((0, (1,) + (0,) * places + (1,), 0))
    source = _rational(value)
    with localcontext(_context(precision=1)) as current:
        output = source.to_decimal(context=_context(precision=places + 2)).unwrap()
        assert output == value
        assert not any(current.flags.values())


@pytest.mark.parametrize("bad", (True, 1, "context", object()))
def test_invalid_context_is_result_without_coercion(bad: Any) -> None:
    assert _rational(1).to_decimal(context=bad).is_failed()
    assert _unit().convert_decimal(value=1, target=_unit(), context=bad).is_failed()


@pytest.mark.parametrize("bad", (None, 0, 1, "exact", object()))
def test_invalid_exact_selector_is_result_without_truth_protocol(bad: Any) -> None:
    assert _rational(1).to_decimal(exact=bad).is_failed()
    assert _unit().convert_decimal(value=1, target=_unit(), exact=bad).is_failed()


def test_context_validation_never_reads_an_untrusted_class_property() -> None:
    def forbidden_class(self: object) -> type[Context]:
        raise AssertionError("context validation must use actual type")

    impostor: Any = type("Impostor", (), {"__class__": property(forbidden_class)})()
    assert _rational(1).to_decimal(context=impostor).is_failed()
    assert (
        _unit().convert_decimal(value=1, target=_unit(), context=impostor).is_failed()
    )


def test_external_exception_identity_handled_state_and_unformattable_error() -> None:
    observations: list[BaseException | None] = []

    class OpaqueError(ValueError):
        def __str__(self) -> str:
            raise AssertionError("exception must not be formatted")

    original = OpaqueError()

    class ExternalContext(Context):
        def divide(self, left: Any, right: Any) -> Decimal:
            observations.append(sys.exception())
            raise original

    outer = RuntimeError("active outer exception")
    try:
        raise outer
    except RuntimeError:
        result = _rational(1).to_decimal(context=ExternalContext())
        assert sys.exception() is outer
    assert isinstance(result, Failed)
    assert result.error.value.callback_exception is original
    assert result.error.code is ErrorCode.APPLICATION_ERROR
    assert observations == [outer]
    assert original.__context__ is outer
    assert original.__traceback__ is not None
    assert original.__traceback__.tb_next is not None
    assert original.__traceback__.tb_next.tb_frame.f_code.co_name == "divide"


@pytest.mark.parametrize(
    "base,code",
    (
        (Exception, ErrorCode.APPLICATION_ERROR),
        (ValueError, ErrorCode.APPLICATION_ERROR),
        (Inexact, ErrorCode.DATA_LOSS),
        (Overflow, ErrorCode.OVERFLOW),
    ),
)
def test_exception_classification_uses_real_type(
    *, base: type[Exception], code: ErrorCode
) -> None:
    def forbidden_class(self: object) -> type[Exception]:
        raise AssertionError("exception classification must not read __class__")

    original = type("OpaqueError", (base,), {"__class__": property(forbidden_class)})()

    class ExternalContext(Context):
        def divide(self, left: Any, right: Any) -> Decimal:
            raise original

    escaped = None
    result = None
    try:
        result = _rational(1).to_decimal(context=ExternalContext())
    except Exception as failure:
        # 先脱离异常链再断言，防止 pytest 报告递归读取恶意属性。 / Assert outside the exception chain to prevent pytest reporting from recursively reading hostile attributes.
        escaped = type(failure).__name__
    assert escaped is None
    assert isinstance(result, Failed)
    assert result.error.code is code
    assert result.error.value.callback_exception is original


@pytest.mark.parametrize("error", (KeyboardInterrupt(), SystemExit(2), GeneratorExit()))
def test_base_exception_propagates_unchanged(error: BaseException) -> None:
    class InterruptingContext(Context):
        def divide(self, left: Any, right: Any) -> Decimal:
            raise error

    with pytest.raises(type(error)) as caught:
        _rational(1).to_decimal(context=InterruptingContext())
    assert caught.value is error
    assert _rational(1).to_decimal().unwrap() == Decimal(1)


def test_reentrant_context_has_no_held_native_lock_or_global_context_override() -> None:
    source = _rational(Fraction(1, 3))

    class ReentrantContext(Context):
        def divide(self, left: Any, right: Any) -> Decimal:
            assert source.to_decimal(context=_context(), exact=False).unwrap() > 0
            assert source.add(_rational(1)).unwrap() == _rational(Fraction(4, 3))
            return super().divide(left, right)

    assert source.to_decimal(
        context=ReentrantContext(prec=2), exact=False
    ).unwrap() == (Decimal("0.33"))


def test_non_decimal_output_is_not_coerced_or_accepted() -> None:
    class BadContext(Context):
        def divide(self, left: Any, right: Any) -> Any:
            return object()

    result = _rational(1).to_decimal(context=BadContext())
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT


@pytest.mark.parametrize("value", (123456789, Fraction(1, 7), Decimal("0.123456789")))
def test_unit_conversion_is_exact_before_one_context_export(value: Any) -> None:
    source, target = _unit(1000), _unit(3)
    expected = Fraction(value) * Fraction(1000, 3)
    context = _context(precision=5)
    oracle = context.copy()
    rounded = oracle.divide(Decimal(expected.numerator), Decimal(expected.denominator))
    with localcontext(_context(precision=1)) as current:
        result = source.convert_decimal(
            value=value, target=target, context=context, exact=False
        ).unwrap()
        assert result.as_tuple() == rounded.as_tuple()
        assert context.flags == oracle.flags
        assert not any(current.flags.values())
    assert source.convert_exact(value=value, target=target).unwrap() == _rational(
        expected
    )


def test_failed_native_conversion_never_runs_context_or_masks_rg008() -> None:
    class UnreachableContext(Context):
        def divide(self, left: Any, right: Any) -> Decimal:
            raise AssertionError("export must not run after native failure")

    mass = Unit.create(name="mass", symbol="kg", powers=(1,) + (0,) * 9).unwrap()
    result = _unit().convert_decimal(value=1, target=mass, context=UnreachableContext())
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    assert result.error.value.source == "ospf-python-native"
    atomic = Unit.create(
        name="atomic mass", symbol="u", powers=(1,) + (0,) * 9, scale=1.6605390666e-27
    )
    assert isinstance(atomic, Failed) and atomic.error.code is ErrorCode.DATA_LOSS


def test_affine_conversion_and_exact_output_do_not_round_intermediate_values() -> None:
    temperature = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
    source = Unit.create(
        name="point", symbol="p", powers=temperature, scale=3, offset=Decimal("0.25")
    ).unwrap()
    target = Unit.create(name="standard", symbol="s", powers=temperature).unwrap()
    assert source.convert_decimal(
        value=Fraction(1, 4), target=target, context=_context(precision=1)
    ).unwrap() == Decimal(1)


def test_context_locality_in_threads_and_no_native_reference_leak() -> None:
    source = _rational(Fraction(1, 3))
    handle = source._handle
    before = sys.getrefcount(handle)

    def worker(precision: int) -> str:
        with localcontext(_context(precision=precision)) as context:
            for _ in range(100):
                result = source.to_decimal(exact=False).unwrap()
                assert context.flags[Inexact]
            return str(result)

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(worker, (2, 4, 6, 8))) == [
            "0.33",
            "0.3333",
            "0.333333",
            "0.33333333",
        ]
    gc.collect()
    after = sys.getrefcount(handle)
    assert after == before


@pytest.mark.asyncio
async def test_current_context_is_task_local_across_await() -> None:
    source = _rational(Fraction(1, 3))

    async def worker(precision: int) -> str:
        with localcontext(_context(precision=precision)):
            await asyncio.sleep(0)
            return str(source.to_decimal(exact=False).unwrap())

    results = await asyncio.gather(worker(2), worker(7))
    assert list(results) == ["0.33", "0.3333333"]
