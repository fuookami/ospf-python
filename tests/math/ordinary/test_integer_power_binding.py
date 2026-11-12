"""公开整数幂的完整整数与外部协议合同。 / Full integer and external-protocol contracts for public integer power."""

from __future__ import annotations

import gc
import random
import weakref
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from typing import Any, SupportsIndex, get_type_hints

import numpy as np
import pytest

from ospf_python import _native
from ospf_python.math.ordinary.pow import pow_int
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok

_BASES = (
    -(2**2048) + 1,
    -(2**127),
    -(2**63),
    -17,
    -3,
    -2,
    -1,
    0,
    1,
    2,
    3,
    17,
    2**63,
    2**127,
    2**2048 + 1,
)
_EXPONENTS = (0, 1, 2, 3, 7, 16, 65)
_HUGE = (
    0,
    1,
    2,
    3,
    2**32 - 1,
    2**32,
    2**64 - 1,
    2**64,
    2**127 + 1,
    2**4096,
    2**4096 + 1,
)


@pytest.mark.parametrize(
    "base", _BASES, ids=[f"base-{index}" for index in range(len(_BASES))]
)
@pytest.mark.parametrize("exp", _EXPONENTS)
def test_signed_arbitrary_precision_bases_and_nonnegative_integer_powers(
    *, base: int, exp: int
) -> None:
    result = pow_int(base, exp)
    assert isinstance(result, Ok)
    output = result.unwrap()
    assert type(output) is int and output == pow(base, exp)


def _pairs() -> list[tuple[int, int]]:
    generator = random.Random(20261027)
    return [
        (
            generator.getrandbits(bits) * (-1 if index % 2 else 1),
            generator.randrange(33),
        )
        for bits in (8, 64, 256, 2048)
        for index in range(4)
    ]


@pytest.mark.parametrize(
    ("base", "exp"), _pairs(), ids=[f"seed-{index}" for index in range(16)]
)
def test_seeded_integer_domain_differential(*, base: int, exp: int) -> None:
    assert pow_int(base, exp).unwrap() == pow(base, exp)


@pytest.mark.parametrize("base", (-1, 0, 1))
@pytest.mark.parametrize(
    "exp", _HUGE, ids=[f"exponent-{index}" for index in range(len(_HUGE))]
)
def test_trivial_bases_accept_arbitrary_width_exponents(*, base: int, exp: int) -> None:
    output = pow_int(base, exp).unwrap()
    assert type(output) is int and output == pow(base, exp)


@pytest.mark.parametrize(
    ("base", "exp"),
    [(2, 1_000_000), (-3, 65535), (3, 65536), (2**257 + 13, 513)],
    ids=("million-bit", "negative-dense", "positive-dense", "large-base"),
)
def test_large_realizable_results_are_exact_not_machine_word_values(
    *, base: int, exp: int
) -> None:
    output = pow_int(base, exp).unwrap()
    assert output == pow(base, exp) and type(output) is int


@pytest.mark.parametrize("base", (-2, -1, 0, 1, 2))
@pytest.mark.parametrize(
    "exp", (-1, -2, -(2**4096)), ids=("minus-one", "minus-two", "wide-negative")
)
def test_negative_exponents_fail_instead_of_float_truncation(
    *, base: int, exp: int
) -> None:
    result = pow_int(base, exp)
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )
    assert result.error.value.callback_exception is None


@pytest.mark.parametrize("base", (0, 1, -1, 27))
@pytest.mark.parametrize("exp", (0, 2, 3, 64))
def test_each_index_is_collected_once_in_order_even_for_identities(
    *, base: int, exp: int
) -> None:
    events: list[str] = []

    class Index:
        def __init__(self, *, name: str, value: int) -> None:
            self.name, self.value = name, value

        def __index__(self) -> int:
            events.append(self.name)
            return self.value

        def __int__(self) -> int:
            pytest.fail("不调用int转换 / Do not call int conversion")

        def __pow__(self, other: object) -> int:
            pytest.fail("不回退Python幂协议 / Do not fall back to Python power")

    output = pow_int(
        Index(name="base", value=base), Index(name="exp", value=exp)
    ).unwrap()
    assert output == pow(base, exp) and events == ["base", "exp"]


class _Unformattable:
    def __str__(self) -> str:
        pytest.fail("不格式化外部异常 / Do not format an external exception")


class _ValueError(_Unformattable, ValueError):
    pass


class _TypeError(_Unformattable, TypeError):
    pass


class _MemoryError(_Unformattable, MemoryError):
    pass


class _KeyboardInterrupt(_Unformattable, KeyboardInterrupt):
    pass


class _SystemExit(_Unformattable, SystemExit):
    pass


@pytest.mark.parametrize(
    "error_type",
    (_ValueError, _TypeError, _MemoryError, _KeyboardInterrupt, _SystemExit),
)
@pytest.mark.parametrize("side", ("base", "exp"))
def test_first_failure_stops_and_preserves_original_error_without_formatting(
    *, error_type: type[BaseException], side: str
) -> None:
    events: list[str] = []
    error = error_type("original")

    class Index:
        def __init__(self, name: str) -> None:
            self.name = name

        def __index__(self) -> int:
            events.append(self.name)
            if self.name == side:
                raise error
            return 0

    if isinstance(error, Exception):
        result = pow_int(Index("base"), Index("exp"))
        assert (
            isinstance(result, Failed)
            and result.error.value.callback_exception is error
        )
        expected = (
            ErrorCode.RESOURCE_EXHAUSTED
            if isinstance(error, MemoryError)
            else ErrorCode.ILLEGAL_ARGUMENT
            if isinstance(error, TypeError)
            else ErrorCode.APPLICATION_ERROR
        )
        assert result.error.code is expected
        traceback = error.__traceback__
        assert traceback is not None
        while traceback.tb_next is not None:
            traceback = traceback.tb_next
        assert traceback.tb_frame.f_code.co_name == "__index__"
    else:
        with pytest.raises(error_type) as caught:
            pow_int(Index("base"), Index("exp"))
        assert caught.value is error
    assert events == (["base"] if side == "base" else ["base", "exp"])


@pytest.mark.parametrize(
    ("base", "exp"),
    [
        (1.0, 2),
        (2, 1.0),
        (None, 3),
        (3, None),
        (Fraction(2), 3),
        (2, Fraction(2)),
        ("2", 3),
        (2, "3"),
    ],
)
def test_non_integer_coercions_are_not_silently_accepted(
    *, base: Any, exp: Any
) -> None:
    result = pow_int(base, exp)
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )
    assert isinstance(result.error.value.callback_exception, TypeError)


@pytest.mark.parametrize(
    ("base", "exp"),
    [(2, 2**64), (3, 2**4096), (-2, 2**64 + 1), (2**2048, 2**64 - 1), (2**2048, 2**63)],
    ids=[f"capacity-{index}" for index in range(5)],
)
def test_impossible_nontrivial_results_fail_before_unbounded_allocation(
    *, base: int, exp: int
) -> None:
    result = pow_int(base, exp)
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.RESOURCE_EXHAUSTED
    )
    assert result.error.value.source == "ospf-python-native"
    assert result.error.value.callback_exception is None


@pytest.mark.parametrize(
    ("base", "exp"),
    [
        (True, False),
        (False, True),
        (np.int64(-7), np.int64(19)),
        (np.uint64(2**64 - 1), np.uint64(3)),
        (-1, np.uint64(2**64 - 1)),
    ],
)
def test_bool_and_numpy_integer_inputs_use_exact_integer_domain(
    *, base: Any, exp: Any
) -> None:
    output = pow_int(base, exp).unwrap()
    assert output == pow(int(base), int(exp)) and type(output) is int


def test_real_int_subclasses_do_not_replace_stored_integer_by_overrides() -> None:
    class Integer(int):
        def __index__(self) -> int:
            pytest.fail("不调用整数index覆盖 / Do not call int index overrides")

        def __int__(self) -> int:
            pytest.fail("不调用整数int覆盖 / Do not call int conversion overrides")

    assert pow_int(Integer(3), Integer(7)).unwrap() == 2187


def test_completed_result_does_not_retain_input_owners() -> None:
    class Index:
        def __index__(self) -> int:
            return 19

    base, exp = Index(), Index()
    references = weakref.ref(base), weakref.ref(exp)
    assert pow_int(base, exp).unwrap() == 19**19
    del base, exp
    gc.collect()
    assert all(reference() is None for reference in references)


def test_concurrent_calls_keep_their_own_exact_values() -> None:
    pairs = [
        (base, exp) for base in (-7, -2, 0, 1, 3, 2**256 + 13) for exp in (0, 1, 7, 65)
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(lambda pair: pow_int(*pair).unwrap(), pairs))
    assert outputs == [pow(base, exp) for base, exp in pairs]


@pytest.mark.parametrize("side", ("base", "exponent"))
def test_private_boundary_refuses_uncollected_index_objects(side: str) -> None:
    class Index:
        def __index__(self) -> int:
            pytest.fail("私有边界不重复采集 / Private boundary does not collect again")

    function: Any = _native._pow_int
    arguments: dict[str, Any] = {"base": 2, "exponent": 3}
    arguments[side] = Index()
    value, error = function(**arguments)
    assert value is None and error is not None and error.category == "ILLEGAL_ARGUMENT"


def test_public_annotations_resolve_the_actual_integer_protocol() -> None:
    hints = get_type_hints(pow_int)
    assert hints["base"] is SupportsIndex and hints["exp"] is SupportsIndex
