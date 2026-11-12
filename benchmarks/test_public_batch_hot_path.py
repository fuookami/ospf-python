"""公开受检单点/批量及实际旧字段导入基准 / Public checked scalar/batch and actual legacy-state import benchmarks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from ospf_python._binding.multiarray import MultiArray as RustArray
from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import Shape2, StorageOrder

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture

_SIZES = {"small": 100, "medium": 10_000, "large": 100_000}


@pytest.mark.benchmark
@pytest.mark.parametrize("size", list(_SIZES))
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("dtype", [np.int64, object])
@pytest.mark.parametrize(
    "path", ["unchecked", "checked-scalar", "checked-batch", "legacy-import"]
)
def test_public_batch_hot_path(
    *,
    benchmark: BenchmarkFixture,
    size: str,
    order: StorageOrder,
    dtype: Any,
    path: str,
) -> None:
    """独立验证同一输入，区分有检查与无检查语义 / Independently verify identical inputs while distinguishing checked and unchecked semantics.

    Args:
        benchmark: 计时器 / Timer.
        size: 输入大小档位 / Input size tier.
        order: 源物理布局 / Source physical layout.
        dtype: 数值或对象存储 / Numeric or object storage.
        path: 公共读取或实际导入路径 / Public read or actual import path.
    """
    count = _SIZES[size]
    data = np.arange(count, dtype=dtype)
    shape = Shape2(10, count // 10, order)
    source: MultiArray[Any, Shape2] = MultiArray(shape, data)
    coordinates: list[tuple[int, ...]] = [
        (i, j) for i in range(10) for j in range(count // 10)
    ]
    offsets = np.ravel_multi_index(
        tuple(zip(*coordinates, strict=True)),
        shape.dims,
        order="C" if order is StorageOrder.ROW_MAJOR else "F",
    )
    expected = data[offsets].tolist()
    benchmark.extra_info.update(
        count=count,
        storage_order=order.name,
        dtype=data.dtype.name,
        checked=path != "unchecked",
        source_construction_timed=False,
    )
    if path == "legacy-import":
        payload = vars(source)
        imported = benchmark(
            lambda: RustArray.from_legacy_state(payload=payload, copy=True).unwrap()
        )
        assert imported.flatten(access_order=order).unwrap() == list(data)
    elif path == "checked-batch":
        assert (
            benchmark(lambda: source.at_many(indices=coordinates).unwrap()) == expected
        )
    elif path == "checked-scalar":
        assert (
            benchmark(
                lambda: [source.at(indices=value).unwrap() for value in coordinates]
            )
            == expected
        )
    else:
        assert (
            benchmark(lambda: [source.get(*value) for value in coordinates]) == expected
        )


@pytest.mark.benchmark
@pytest.mark.parametrize("size", list(_SIZES))
@pytest.mark.parametrize("order", list(StorageOrder))
@pytest.mark.parametrize("dtype", [np.int64, object])
@pytest.mark.parametrize("path", ["legacy-set", "checked-set"])
def test_public_set_hot_path(
    *,
    benchmark: BenchmarkFixture,
    size: str,
    order: StorageOrder,
    dtype: Any,
    path: str,
) -> None:
    """Compare complete legacy and checked single-slot write calls.

    Args:
        benchmark: Timer.
        size: Input size tier.
        order: Source physical layout.
        dtype: Numeric or object storage.
        path: Legacy or checked write path.
    """
    count = _SIZES[size]
    data = np.arange(count, dtype=dtype)
    source: MutableMultiArray[Any, Shape2] = MutableMultiArray(
        Shape2(10, count // 10, order), data
    )
    coordinates: list[tuple[int, ...]] = [
        (i, j) for i in range(10) for j in range(count // 10)
    ]
    benchmark.extra_info.update(
        count=count,
        storage_order=order.name,
        dtype=data.dtype.name,
        checked=path == "checked-set",
        source_construction_timed=False,
    )
    if path == "checked-set":
        benchmark(
            lambda: [
                source.set_at(indices=value, value=0).unwrap() for value in coordinates
            ]
        )
    else:
        benchmark(lambda: [source.set(*value, 0) for value in coordinates])
    np.testing.assert_array_equal(data, np.zeros(count, dtype=dtype))
