"""取消误差的切换前合同。 / Pre-cutover cancellation contracts.

这些敏感输入不得以普通 allclose 或精确域替换静默批准为已验收。
Sensitive inputs are not accepted through ordinary allclose or silent exact-domain substitution.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from ospf_python import multiarray
from ospf_python.math.multiarray.fast_sum import fast_sum

_DTYPES = ("float16", "float32", "float64", "complex64", "complex128")


def _values(dtype: str) -> np.ndarray[Any, Any]:
    if dtype == "float16":
        sequence = [65504.0] * 512 + [1.0] * 128 + [-65504.0] * 512
    else:
        big = float(2**24) if dtype in ("float32", "complex64") else 1e16
        sequence = [big, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, -big]
    data = np.array(sequence, dtype=dtype)
    if data.dtype.kind == "c":
        data.imag = -data.real
    return data


@pytest.mark.parametrize("dtype", _DTYPES)
@pytest.mark.parametrize("axis", [0, -1, (0,)])
@pytest.mark.parametrize("stride", [1, -1, 2])
def test_cancellation_sensitive_axes_do_not_silently_become_left_fold(
    *, dtype: str, axis: Any, stride: int
) -> None:
    data = _values(dtype)
    if stride == 2:
        backing = np.zeros(data.size * 2, dtype=dtype)
        backing[::2] = data
        data = backing[::2]
    elif stride == -1:
        data = data[::-1]
    source: multiarray.MultiArray[Any, multiarray.DynShape] = multiarray.MultiArray(
        multiarray.DynShape((data.size,)), data
    )
    expected = np.asarray(np.sum(data, axis=axis))
    result = fast_sum(source, axis=axis)
    assert isinstance(result, multiarray.MultiArray)
    assert result.shape.dims == expected.shape and result._data.dtype == expected.dtype
    np.testing.assert_array_equal(result._data, expected.reshape(-1))
    assert not np.shares_memory(result._data, data)
    if stride != -1 and dtype == "float64":
        assert expected == 4.0
