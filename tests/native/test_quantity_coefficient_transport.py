"""单位系数原生编码与冻结传输参考差分。 / Native coefficient encoding against a frozen transport reference."""

from __future__ import annotations

import importlib
import math
import random
import struct
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, Inexact, localcontext
from fractions import Fraction
from typing import Any, cast

import pytest

from ospf_python import _native
from ospf_python._binding.quantities import Unit
from ospf_python._binding.unit_registry import _families
from ospf_python.quantities import Quantity
from ospf_python.quantities.unit.length import KILOMETER, METER
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed

_LENGTH = (0, 1, 0, 0, 0, 0, 0, 0, 0, 0)


def _reference_parts(value: int | float | Decimal) -> tuple[int, int]:
    """测试专用旧编码，不实现单位数学。 / Test-only old encoding, never unit arithmetic."""
    if type(value) is int:
        return value, 0
    decimal = (
        Decimal.from_float(value) if type(value) is float else cast("Decimal", value)
    )
    parts = decimal.as_tuple()
    return int(Decimal((parts.sign, parts.digits, 0))), -int(parts.exponent)


def _compare(*, scale: Any, offset: Any, powers: tuple[int, ...] = _LENGTH) -> None:
    old, old_error = _native._create_quantity_unit(
        name="coefficient / 系数",
        symbol="u",
        powers=list(powers),
        scale=_reference_parts(scale),
        offset=None if offset is None else _reference_parts(offset),
    )
    current = Unit.create(
        name="coefficient / 系数", symbol="u", powers=powers, scale=scale, offset=offset
    )
    if old_error is not None:
        assert isinstance(current, Failed)
        assert current.error.code is ErrorCode.__members__[old_error.category]
        assert current.error.message == old_error.message
        context = current.error.value
        assert (context.source, context.rust_code, context.error_class) == (
            old_error.source,
            old_error.rust_code,
            old_error.error_class,
        )
    else:
        assert old is not None
        handle = current.unwrap()._handle
        assert handle.descriptor() == old.descriptor()
        assert handle.to_json() == old.to_json()
        assert handle.same_unit(old)


def _constants() -> list[Any]:
    return [
        pytest.param(unit, family.powers, id=f"{family.cls.__name__}.{name}")
        for family in _families.values()
        for name, unit in sorted(
            vars(importlib.import_module(family.cls.__module__)).items()
        )
        if name.isupper() and type(unit) is family.cls
    ]


@pytest.mark.parametrize(("unit", "powers"), _constants())
def test_all_223_constant_transports_match_exact_old_metadata(
    *, unit: Any, powers: tuple[int, ...]
) -> None:
    _compare(scale=unit._factor, offset=getattr(unit, "_offset", None), powers=powers)


def _float_samples() -> list[float]:
    bits = [
        0,
        1,
        2,
        4,
        8,
        16,
        (1 << 51),
        (1 << 52) - 1,
        1 << 52,
        (1023 << 52),
        (1023 << 52) + 1,
        (2046 << 52),
        (2047 << 52) - 1,
    ]
    generator = random.Random(1198547)
    bits.extend(generator.randrange(2047 << 52) for _ in range(128))
    return [
        struct.unpack("!d", struct.pack("!Q", value | sign))[0]
        for value in bits
        for sign in (0, 1 << 63)
    ]


@pytest.mark.parametrize("value", _float_samples(), ids=lambda value: value.hex())
@pytest.mark.parametrize("field", ("scale", "offset"))
def test_binary64_edge_and_seeded_encodings_match_decimal_from_float(
    *, field: str, value: float
) -> None:
    _compare(
        scale=value if field == "scale" else 1,
        offset=value if field == "offset" else None,
    )


@pytest.mark.parametrize(
    "value",
    (
        1,
        -2,
        1 << 20000,
        Decimal("1.2300"),
        Decimal("-0E-100"),
        Decimal("1E+1000"),
        Decimal("1E-1000"),
    ),
    ids=(
        "one",
        "negative",
        "big-int",
        "decimal-quantum",
        "negative-zero",
        "large-exponent",
        "small-exponent",
    ),
)
@pytest.mark.parametrize("field", ("scale", "offset"))
def test_integer_and_decimal_metadata_keep_original_scale_and_failure_provenance(
    *, field: str, value: Any
) -> None:
    _compare(
        scale=value if field == "scale" else 1,
        offset=value if field == "offset" else None,
    )


@pytest.mark.parametrize("field", ("scale", "offset"))
@pytest.mark.parametrize(
    "value",
    (
        True,
        "1",
        Fraction(1, 3),
        math.inf,
        -math.inf,
        math.nan,
        Decimal("sNaN"),
        Decimal("Infinity"),
    ),
)
def test_invalid_coefficients_keep_python_boundary_provenance(
    *, field: str, value: Any
) -> None:
    result = Unit.create(name="bad", symbol="u", powers=_LENGTH, **{field: value})
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    context = result.error.value
    assert (context.source, context.rust_code, context.error_class) == (
        "ospf-python",
        None,
        "BOUNDARY",
    )


@pytest.mark.parametrize("field", ("scale", "offset"))
def test_native_transport_and_facade_do_not_call_unknown_numeric_protocols(
    field: str,
) -> None:
    class Hostile:
        def __getattribute__(self, name: str) -> Any:
            if name == "__class__":
                pytest.fail("class spoof")
            return object.__getattribute__(self, name)

        def __float__(self) -> Any:
            pytest.fail("float coercion")

        def __index__(self) -> Any:
            pytest.fail("index coercion")

        def __str__(self) -> str:
            pytest.fail("formatting")

    values: list[Any] = [Hostile(), (Hostile(), 0), (1, Hostile()), [1, 0], (True, 0)]
    for value in values:
        result = Unit.create(name="bad", symbol="u", powers=_LENGTH, **{field: value})
        assert isinstance(result, Failed)
        _, error = _native._create_quantity_unit_encoded(
            name="bad",
            symbol="u",
            powers=list(_LENGTH),
            scale=1 if field == "offset" else value,
            offset=value if field == "offset" else None,
        )
        assert error is not None and error.category == "ILLEGAL_ARGUMENT"


def test_context_traps_flags_and_large_metadata_are_not_arithmetic_inputs() -> None:
    with localcontext() as context:
        context.prec = 1
        context.traps[Inexact] = True
        context.clear_flags()
        _compare(scale=0.1, offset=Decimal("1234.50000"))
        _compare(scale=1, offset=(1 << 20000) + 1)
        assert not any(context.flags.values())


def test_actual_generic_quantity_path_uses_new_encoding_without_instance_cache(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        _native,
        "_create_quantity_unit",
        lambda **kw: pytest.fail("old coefficient path"),
    )
    owner = Quantity(value=Fraction(1, 3), unit=KILOMETER)
    assert owner.to(METER).unwrap().value == Fraction(1000, 3)
    assert set(vars(owner)) == {"value", "unit"}


def test_unit_subclass_factory_still_receives_the_native_handle() -> None:
    seen = []

    class Subclass(Unit):
        def __post_init__(self) -> None:
            seen.append(self._handle)

        def __init__(self, handle: _native._QuantityUnit) -> None:
            super().__init__(handle)
            self.__post_init__()

    unit = Subclass.create(
        name="subclass", symbol="u", powers=_LENGTH, scale=1000
    ).unwrap()
    assert type(unit) is Subclass and seen == [unit._handle]


def test_parallel_creations_have_independent_metadata_and_current_values() -> None:
    def create(index: int) -> Any:
        unit = Unit.create(
            name=str(index), symbol="u", powers=_LENGTH, scale=index + 1
        ).unwrap()
        return unit.descriptor()[0], unit.convert_exact(
            value=Fraction(1, 3),
            target=Unit.create(name="SI", symbol="", powers=_LENGTH).unwrap(),
        ).unwrap().as_integer_ratio()

    with ThreadPoolExecutor(max_workers=4) as pool:
        assert list(pool.map(create, range(24))) == [
            (str(index), Fraction(index + 1, 3).as_integer_ratio())
            for index in range(24)
        ]
