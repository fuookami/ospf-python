"""公开素数筛的完整自然入口合同。 / Natural public prime-sieve contracts."""

from __future__ import annotations

import tomllib

import gc
import json
import math
import os
import subprocess
import sys
import weakref
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import ospf_python
from ospf_python import _native
from ospf_python.math.ordinary.prime import primes_up_to
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed, Ok


def _oracle(limit: int) -> list[int]:
    return [
        number
        for number in range(2, limit + 1)
        if all(number % divisor for divisor in range(2, math.isqrt(number) + 1))
    ]


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
    "limit", [*range(-3, 65), 97, 997, 999, 1000, 1001, 1009, 1024, 1089, 4096]
)
def test_inclusive_prime_list_uses_existing_result_and_builtin_integers(
    limit: int,
) -> None:
    result = primes_up_to(limit)
    assert isinstance(result, Ok)
    output = result.unwrap()
    assert type(output) is list and output == _oracle(limit)
    assert all(type(value) is int for value in output)


@pytest.mark.parametrize(
    ("limit", "count", "last"),
    [(10_000, 1229, 9973), (100_000, 9592, 99991), (1_000_000, 78498, 999983)],
)
def test_larger_sieve_known_counts_and_composite_boundaries(
    *, limit: int, count: int, last: int
) -> None:
    output = primes_up_to(limit).unwrap()
    assert len(output) == count and output[-1] == last
    assert output == sorted(set(output)) and output[0] == 2
    assert all(value <= limit for value in output)
    assert not {square**2 for square in range(2, math.isqrt(limit) + 1)}.intersection(
        output
    )


@pytest.mark.parametrize(
    "limit",
    [-(2**64), -(2**128), -(2**4096), 0, 1, True, False, np.int64(-3), np.uint64(29)],
)
def test_full_negative_integer_domain_bool_and_real_numpy_protocol(limit: Any) -> None:
    expected = _oracle(int(limit))
    assert primes_up_to(limit).unwrap() == expected


def test_index_once_without_numeric_comparison_or_arithmetic() -> None:
    calls: list[str] = []

    class Index:
        def __index__(self) -> int:
            calls.append("index")
            return 29

        def __lt__(self, other: object) -> bool:
            pytest.fail("不比较原始对象 / Do not compare the original object")

        def __add__(self, other: object) -> int:
            pytest.fail("不执行输入算术 / Do not perform input arithmetic")

    assert primes_up_to(Index()).unwrap() == _oracle(29)
    assert calls == ["index"]


def test_real_int_subclass_uses_stored_integer_not_overrides() -> None:
    class Integer(int):
        def __index__(self) -> int:
            pytest.fail("不调用整数子类覆盖 / Do not call the int-subclass override")

        def __lt__(self, other: int) -> bool:
            pytest.fail("不调用整数比较覆盖 / Do not call the int comparison override")

    assert primes_up_to(Integer(29)).unwrap() == _oracle(29)


@pytest.mark.parametrize(
    "error_type",
    [_ValueError, _TypeError, _MemoryError, _KeyboardInterrupt, _SystemExit],
)
def test_external_failure_keeps_instance_traceback_and_never_formats(
    error_type: type[BaseException],
) -> None:
    error = error_type("original")

    class Index:
        def __index__(self) -> int:
            raise error

    if isinstance(error, Exception):
        result = primes_up_to(Index())
        assert isinstance(result, Failed)
        assert result.error.value.callback_exception is error
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
            primes_up_to(Index())
        assert caught.value is error


@pytest.mark.parametrize("value", [None, 1.0, "10", object(), [10]])
def test_non_integer_inputs_fail_without_silent_float_or_string_coercion(
    value: Any,
) -> None:
    result = primes_up_to(value)
    assert (
        isinstance(result, Failed) and result.error.code is ErrorCode.ILLEGAL_ARGUMENT
    )
    assert isinstance(result.error.value.callback_exception, TypeError)


@pytest.mark.parametrize("value", [2**63 - 1, 2**64 - 1, 2**64, 2**4096])
def test_impossible_sieve_capacities_fail_before_upstream_allocation(
    value: int,
) -> None:
    result = primes_up_to(value)
    assert isinstance(result, Failed)
    assert result.error.code is ErrorCode.RESOURCE_EXHAUSTED
    assert result.error.value.source == "ospf-python-native"
    assert result.error.value.callback_exception is None


def test_output_is_detached_and_input_owner_is_not_retained() -> None:
    class Index:
        def __index__(self) -> int:
            return 29

    owner = Index()
    reference = weakref.ref(owner)
    first = primes_up_to(owner).unwrap()
    first[:] = [-1]
    second = primes_up_to(29).unwrap()
    assert second == _oracle(29) and first is not second
    del owner
    gc.collect()
    assert reference() is None


def test_concurrent_cache_queries_publish_independent_correct_lists() -> None:
    limits = [1009, 2111, 4096, 997, 2, 0] * 4
    with ThreadPoolExecutor(max_workers=4) as pool:
        outputs = list(pool.map(lambda limit: primes_up_to(limit).unwrap(), limits))
    for limit, output in zip(limits, outputs, strict=True):
        assert output == _oracle(limit)
    assert len({id(output) for output in outputs}) == len(outputs)


def test_fresh_process_extends_the_actual_pinned_cache() -> None:
    runner = r"""
import json,os,sys
sys.path.insert(0, sys.argv[1])
handles=[os.add_dll_directory(path) for path in os.environ.get('OSPF_NATIVE_DLL_DIRS','').split(os.pathsep) if path] if os.name=='nt' else []
from ospf_python import _native
from ospf_python.math.ordinary.prime import primes_up_to
assert _native.build_info()['rust_revision']==sys.argv[2]
print(json.dumps([primes_up_to(limit).unwrap() for limit in (1001,2000,5000,10000,17)]))
"""
    parent = str(Path(ospf_python.__file__).resolve().parent.parent)
    # 从账本读 baseline revision，而不是硬编码——pin 变更时本用例不应失效。
    # Read the baseline revision from the ledger instead of hardcoding it.
    _baseline = tomllib.loads(
        (Path(parent) / "docs/migration/api-map.toml").read_text(encoding="utf-8")
    )["baseline"]["rust_revision"]
    process = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", "-c", runner, parent, _baseline],
        env=os.environ.copy(),
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert json.loads(process.stdout) == [
        _oracle(limit) for limit in (1001, 2000, 5000, 10000, 17)
    ]


def test_private_boundary_does_not_run_uncollected_protocol() -> None:
    class Index:
        def __index__(self) -> int:
            pytest.fail(
                "私有边界不二次采集 / The private boundary must not collect again"
            )

    function: Any = _native._primes_up_to
    value, error = function(limit=Index())
    assert value is None and error is not None and error.category == "ILLEGAL_ARGUMENT"
