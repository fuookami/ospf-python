"""任意精度比较不可因连分数深度终止进程 / Exact order must not terminate the process on deep continued fractions."""

from __future__ import annotations

import subprocess
import sys

import pytest

from ospf_python import _native


@pytest.mark.parametrize("depth", [8192, 8193, 16384])
def test_exact_rational_order_remains_stack_bounded_in_fresh_process(
    depth: int,
) -> None:
    code = f"""
import os
directories = [os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if p] if os.name == 'nt' else []
from fractions import Fraction
from pathlib import Path
from ospf_python import _native
from ospf_python.math.algebra.number.rational import Rational
from ospf_python._binding.numeric import Rational as StrictRational
from ospf_python.utils.functional.ord import Order
assert Path(_native.__file__).resolve() == Path({_native.__file__!r}).resolve()
a, b = 0, 1
for _ in range({depth}):
    a, b = b, a + b
for n1, d1, n2, d2 in ((a, b, b, a+b), (-a, b, -b, a+b), (a, b, a, b)):
    left, right = Rational(n1, d1), Rational(n2, d2)
    oracle_left, oracle_right = Fraction(n1, d1), Fraction(n2, d2)
    expected = (oracle_left > oracle_right) - (oracle_left < oracle_right)
    assert (left < right) == (expected < 0)
    assert (left <= right) == (expected <= 0)
    assert (left > right) == (expected > 0)
    assert (left >= right) == (expected >= 0)
    assert (left == right) == (expected == 0)
    assert left.cmp(right) is {{-1: Order.LT, 0: Order.EQ, 1: Order.GT}}[expected]
    strict_left = StrictRational.create(numerator=n1, denominator=d1).unwrap()
    strict_right = StrictRational.create(numerator=n2, denominator=d2).unwrap()
    assert strict_left.compare(strict_right).unwrap() == expected
    assert (strict_left == strict_right) == (expected == 0)
    assert strict_left.to_float(exact=True).is_failed()
    assert not strict_left.to_float(exact=False).is_failed()
print('bounded-stack exact comparison passed', flush=True)
"""
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, (result.returncode, result.stdout, result.stderr)
    assert result.stdout.strip() == "bounded-stack exact comparison passed"
