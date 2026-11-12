"""Frozen pre-native `to_list` comparison baseline.

The body is copied verbatim from the implementation frozen before the native
`to_list` orchestration (`logs/p3/public-nested-performance-current-20261031/legacy-multi_array.py`).
Benchmark-only reference code; production modules must not import it.

已知限制 / Known limitation: this baseline always exports row-major nesting, so it is
NOT a valid oracle for column-major layouts (the native path fixes that export).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray


class LegacyMultiArray(MultiArray[Any, Any]):
    """Frozen immutable `to_list` reference."""

    def to_list(self) -> list[Any]:
        """转换为嵌套 Python 列表（冻结实现原文）。 / Nested list via the frozen implementation."""
        reshaped = self._data.reshape(self._shape.dims)
        return reshaped.tolist()  # type: ignore[no-any-return]


class LegacyMutableMultiArray(MutableMultiArray[Any, Any]):
    """Frozen mutable `to_list` reference."""

    def to_list(self) -> list[Any]:
        """转换为嵌套 Python 列表（冻结实现原文）。 / Nested list via the frozen implementation."""
        reshaped = self._data.reshape(self._shape.dims)
        return reshaped.tolist()  # type: ignore[no-any-return]


_ = np  # keep numpy import explicit for type checkers
