"""公共计算与原生形状共用的容量合同 / Capacity contract shared by public arithmetic and native shapes."""

from __future__ import annotations

import sys

import pytest

from ospf_python._binding.multiarray import Shape
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.functional.result import Failed


@pytest.mark.parametrize(
    ("dims", "code"),
    [
        ((sys.maxsize, 2, 0), ErrorCode.OVERFLOW),
        ((sys.maxsize, 0, 2), ErrorCode.ILLEGAL_ARGUMENT),
        ((-1, sys.maxsize, 2), ErrorCode.ILLEGAL_ARGUMENT),
        ((sys.maxsize + 1, 0), ErrorCode.OVERFLOW),
    ],
)
def test_shared_dense_validation_keeps_first_failure_category(
    dims: tuple[int, ...], code: ErrorCode
) -> None:
    result = Shape.create(dims=dims)
    assert isinstance(result, Failed)
    assert result.error.code is code
