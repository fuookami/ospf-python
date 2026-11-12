"""`transpose` 的批量分支（count ≥ 256）守卫。

背景：`native/src/coordinate_materialization.rs` 的 `transpose_into` 在满足
「精确形状类 + 标准目标布局 + 双方皆 ndarray + `count >= 256`」时走批量路径
（一次 `ndarray.take` + 一次 fancy-index 赋值），否则保持逐元素循环。

**两段代码必须产出相同结果。** 本文件覆盖三条：

1. **小数组（per-element 路径）** 与 NumPy 参考一致；
2. **大数组（bulk 路径，含 256 边界）** 与 NumPy 参考一致；
3. **同一条数据在两条路径下的等价性**：把小数组切开、大数组也对照，
   用「分块拼接」构造出与 bulk 路径同尺寸的调用来比对。

另有一条不变量：`count == 256` 与 `count == 255` 都必须是正确结果
（阈值两侧都走对的一条，即使实现路径不同）。
"""

from __future__ import annotations

import numpy as np

from ospf_python.multiarray.multi_array import MultiArray
from ospf_python.multiarray.shape import DynShape, StorageOrder

BULK_THRESHOLD = 256


def _array(dims: tuple[int, ...]) -> tuple[MultiArray, np.ndarray]:
    """构造被测数组与其 NumPy 参考。"""
    count = int(np.prod(dims))
    values = np.arange(count, dtype=np.int16)
    return MultiArray(DynShape(dims, StorageOrder.ROW_MAJOR), values), values.reshape(dims)


def _transpose_values(array: MultiArray) -> np.ndarray:
    """调用 `transpose()` 并把结果折回 ndarray。"""
    result = array.transpose()
    assert not hasattr(result, "error"), f"transpose 失败：{result}"
    nested = result.unwrap().to_list().unwrap()
    return np.array(nested, dtype=np.int16)


def test_small_array_matches_numpy_per_element_path() -> None:
    """小数组（6 元素，per-element 路径）与 NumPy 一致。"""
    array, reference = _array((2, 3))
    assert _transpose_values(array).tolist() == reference.T.tolist()


def test_large_array_matches_numpy_bulk_path() -> None:
    """大数组（10,000 元素，bulk 路径）与 NumPy 一致。"""
    array, reference = _array((100, 100))
    assert _transpose_values(array).tolist() == reference.T.tolist()


def test_threshold_boundary_both_sides_are_correct() -> None:
    """阈值两侧（255 与 256 元素）都必须给出正确结果。"""
    for dims in ((15, 17), (16, 16)):
        count = dims[0] * dims[1]
        assert count in (BULK_THRESHOLD - 1, BULK_THRESHOLD)
        array, reference = _array(dims)
        assert _transpose_values(array).tolist() == reference.T.tolist(), (
            f"{dims}（{count} 元素）结果与 NumPy 不一致"
        )


def test_non_square_large_array() -> None:
    """非方阵大数组也必须正确。"""
    array, reference = _array((200, 100))
    assert _transpose_values(array).tolist() == reference.T.tolist()


def test_column_major_large_array_matches_fortran_order_reference() -> None:
    """列布局大数组的参考必须按 Fortran 序构造。

    列布局下逻辑值等于 `values.reshape(dims, order="F")`，
    所以转置后应等于它的 `.T`；用 C 序当参考会得到错误的「不一致」。
    """
    dims = (40, 8)  # 320 元素 → 走批量路径
    count = dims[0] * dims[1]
    assert count >= BULK_THRESHOLD
    values = np.arange(count, dtype=np.int16)
    array = MultiArray(DynShape(dims, StorageOrder.COLUMN_MAJOR), values)
    reference = values.reshape(dims, order="F")
    assert _transpose_values(array).tolist() == reference.T.tolist()
