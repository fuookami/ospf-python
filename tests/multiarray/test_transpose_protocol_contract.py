"""锁住 `transpose_into` 的两条契约，防止将来加 native 快路径时静默吞掉自定义协议。

对应 `native/src/coordinate_materialization.rs` 的两条 Rust 单测
（`:226` `transpose_uses_pinned_target_and_keeps_final_keys`、
`:249` `transpose_preserves_signed_external_stride_and_live_reads`）。
本文件是它们的 **Python 侧等价版本**——从 Python 调用 `CoordinatePlan.transpose_into`，
所以任何「按 strides 或按类名猜 flat_index」的快路径都会让它变红。

两条契约：
1. **自定义 `flat_index` 必须被真正调用**（不能被 native 推算替代）；
2. **每次读值前必须重新取 `_data`**（`flat_index` 回调可以替换存储）。
"""

from __future__ import annotations

from typing import Any, Final

from ospf_python import _native

TWO_BY_TWO: Final = [2, 2]
TWO_BY_THREE: Final = [2, 3]


class _CountingShape:
    """`flat_index` 用自己的公式，并计数——证明它真的被调用。"""

    __slots__ = ("calls", "downstream", "dims", "swap")

    def __init__(self, *, dims: int, swap: bool = False) -> None:
        self.calls = 0
        self.downstream: _Source | None = None
        self.swap = swap
        self.dims = dims

    def flat_index(self, *indices: int) -> int:
        """自定义扁平索引 + 可选的回调副作用。"""
        self.calls += 1
        if self.swap and self.downstream is not None:
            self.downstream._data = [5, 4, 3, 2, 1, 0]
        return sum(index * (self.dims ** (len(indices) - position - 1))
                   for position, index in enumerate(indices))


class _Source:
    """带自定义 `_shape` 的源。"""

    __slots__ = ("_data", "_shape")

    def __init__(self, shape: _CountingShape, data: list[int]) -> None:
        self._shape = shape
        self._data = data
        shape.downstream = self


def test_transpose_calls_custom_flat_index() -> None:
    """契约 1：自定义 `flat_index` 被调用恰 4 次，结果由它决定。"""
    shape = _CountingShape(dims=2)
    source = _Source(shape, [1, 2, 3, 4])
    output: list[Any] = [None] * 4
    plan = _native._create_coordinate_plan(TWO_BY_TWO)[0]
    plan.transpose_into(owner=source, strides=(1, 2), destination=output)
    assert shape.calls == 4, f"flat_index 应被调用 4 次，实际 {shape.calls}"
    assert output == [1, 2, 3, 4]


def test_transpose_rereads_data_after_flat_index_side_effects() -> None:
    """契约 2：`flat_index` 回调替换 `_data` 后，读值必须取到新存储。"""
    shape = _CountingShape(dims=3, swap=True)
    source = _Source(shape, [0] * 6)
    output: list[Any] = [None] * 6
    plan = _native._create_coordinate_plan(TWO_BY_THREE)[0]
    # 与 Rust 单测同参数：有符号外部步长 (-1, 3)，目标偏移落在 0–5。
    plan.transpose_into(owner=source, strides=(-1, 3), destination=output)
    assert shape.calls == 6, f"flat_index 应被调用 6 次，实际 {shape.calls}"
    assert output == [5, 0, 1, 2, 3, 4], f"与 Rust 单测应一致，实际 {output}"
