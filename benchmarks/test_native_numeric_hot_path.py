"""分离创建、逐项 FFI 与批量归约成本 / Separate construction, per-item FFI and batch reduction costs."""

from __future__ import annotations

import random
from fractions import Fraction
from typing import TYPE_CHECKING

import pytest

from ospf_python._binding.numeric import Rational, RationalArray
from ospf_python.math.algebra.number.rational import Rational as PublicRational

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture

# 每项为数目与整数位宽，不将 solver 波动混入 FFI 成本。 / Count and integer bit width, excluding solver variation.
_SIZES = {"small": (32, 32), "medium": (256, 128), "large": (2048, 256)}


@pytest.fixture(params=["small", "medium", "large"])
def numeric_dataset(
    request: pytest.FixtureRequest,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    """固定种子的精确有理数输入 / Seeded exact rational inputs.

    Args:
        request: pytest 数据集参数 / Pytest dataset parameter.

    Returns:
        左右整数对列表 / Left and right integer-pair lists.
    """
    count, bits = _SIZES[request.param]
    rng = random.Random(20261029)
    left = [(rng.getrandbits(bits) - (1 << (bits - 1)), 17) for _ in range(count)]
    right = [(rng.getrandbits(bits) + 1, 19) for _ in range(count)]
    return left, right


@pytest.mark.benchmark
@pytest.mark.parametrize(
    "path",
    [
        "create-scalar",
        "create-batch",
        "dot-public",
        "dot-scalar",
        "dot-batch",
        "pipeline-public",
        "pipeline-scalar",
        "pipeline-batch",
    ],
)
def test_numeric_hot_path(
    *,
    benchmark: BenchmarkFixture,
    numeric_dataset: tuple[list[tuple[int, int]], list[tuple[int, int]]],
    path: str,
) -> None:
    """同数据分别测各条路径，验证精确结果 / Measure each path on identical data and verify exact results.

    Args:
        benchmark: pytest-benchmark 计时器 / Pytest-benchmark timer.
        numeric_dataset: 左右整数对 / Left and right integer pairs.
        path: 创建、已有值点积或含创建完整流程 / Construction, resident dot or construction-inclusive pipeline.
    """
    left, right = numeric_dataset
    expected = sum(
        Fraction(*a) * Fraction(*b) for a, b in zip(left, right, strict=True)
    )

    def scalar_create(inputs: list[tuple[int, int]]) -> list[Rational]:
        return [Rational.create(numerator=n, denominator=d).unwrap() for n, d in inputs]

    def public_create(inputs: list[tuple[int, int]]) -> list[PublicRational]:
        return [PublicRational(n, d) for n, d in inputs]

    def scalar_dot(a: list[Rational], b: list[Rational]) -> tuple[int, int]:
        total = Rational.create(numerator=0).unwrap()
        for x, y in zip(a, b, strict=True):
            total = total.add(x.multiply(y).unwrap()).unwrap()
        return total.as_integer_ratio()

    def public_dot(a: list[PublicRational], b: list[PublicRational]) -> tuple[int, int]:
        total = PublicRational(0)
        for x, y in zip(a, b, strict=True):
            total = total + x * y
        return total.numerator, total.denominator

    if path == "create-scalar":
        assert len(benchmark(lambda: scalar_create(left))) == len(left)
        return
    if path == "create-batch":
        assert len(benchmark(lambda: RationalArray.create(left).unwrap())) == len(left)
        return
    if path == "dot-public":
        a_public, b_public = public_create(left), public_create(right)
        result = benchmark(lambda: public_dot(a_public, b_public))
    elif path == "dot-scalar":
        a_scalar, b_scalar = scalar_create(left), scalar_create(right)
        result = benchmark(lambda: scalar_dot(a_scalar, b_scalar))
    elif path == "dot-batch":
        a_batch, b_batch = (
            RationalArray.create(left).unwrap(),
            RationalArray.create(right).unwrap(),
        )
        result = benchmark(lambda: a_batch.dot(b_batch).unwrap().as_integer_ratio())
    elif path == "pipeline-public":
        result = benchmark(
            lambda: public_dot(public_create(left), public_create(right))
        )
    elif path == "pipeline-scalar":
        result = benchmark(
            lambda: scalar_dot(scalar_create(left), scalar_create(right))
        )
    else:
        result = benchmark(
            lambda: (
                RationalArray.create(left)
                .unwrap()
                .dot(RationalArray.create(right).unwrap())
                .unwrap()
                .as_integer_ratio()
            )
        )
    assert result == (expected.numerator, expected.denominator)
