"""框架数值类型别名 / Framework number type aliases.

定义框架层常用的数值类型别名。
Defines common number type aliases for the framework layer.
"""

from __future__ import annotations

from typing import Any

import numpy as np

# 标量类型 / Scalar types
type Float = float
"""浮点数 / Floating point number."""

type Integer = int
"""整数 / Integer."""

# NumPy 类型 / NumPy types
type NpFloat64 = np.float64
"""NumPy 64位浮点数 / NumPy 64-bit float."""

type NpInt64 = np.int64
"""NumPy 64位整数 / NumPy 64-bit integer."""

# 容器类型 / Container types
type FloatArray = np.ndarray[Any, np.dtype[np.float64]]
"""浮点数组 / Float array."""

type IntArray = np.ndarray[Any, np.dtype[np.int64]]
"""整数数组 / Integer array."""
