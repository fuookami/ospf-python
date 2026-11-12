"""基础形状与绑定层的独立导入合同 / Independent shape and binding import-order contracts."""

from __future__ import annotations

import subprocess
import sys

import pytest

_ENTRIES = [
    "ospf_python.math.algebra.number.rational",
    "ospf_python.multiarray",
    "ospf_python.multiarray.shape",
    "ospf_python._binding.storage_transform",
    "ospf_python._binding.shared_transpose",
    "ospf_python._binding.multiarray",
]


@pytest.mark.parametrize("entry", _ENTRIES)
@pytest.mark.parametrize("reverse", [False, True])
def test_binding_and_shape_import_order_in_fresh_interpreter(
    entry: str, reverse: bool
) -> None:
    script = f"""
import importlib
import os
directories = [os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if p] if os.name == 'nt' else []
entries = {_ENTRIES!r}
importlib.import_module({entry!r})
for name in entries[::{"-1" if reverse else "1"}]:
    importlib.import_module(name)
import ospf_python.multiarray as public
from ospf_python.multiarray import shape, multi_array
from ospf_python.math.algebra.number import Rational
from ospf_python.math.algebra.number.rational import Rational as DeepRational
assert Rational is DeepRational
assert Rational(1, 2) + Rational(1, 2) == Rational(1)
assert set(vars(Rational(1))) == {{'numerator', 'denominator'}}
assert public.DynShape is shape.DynShape
assert public.MultiArray is multi_array.MultiArray
assert public.MutableMultiArray is multi_array.MutableMultiArray
namespace = {{}}
exec('from ospf_python.multiarray import *', namespace)
assert set(public.__all__) <= set(dir(public))
for name in public.__all__:
    assert namespace[name] is getattr(public, name)
try:
    getattr(public, '_missing_shape_export')
except AttributeError:
    pass
else:
    raise AssertionError('未知导出必须失败 / Unknown export must fail')
"""
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_package_facade_does_not_eagerly_import_array_consumers() -> None:
    script = """
import sys
import ospf_python.multiarray as public
assert 'ospf_python.multiarray.multi_array' not in sys.modules
assert 'ospf_python._binding.storage_transform' not in sys.modules
assert 'Shape2' in dir(public) and 'MultiArray' in dir(public)
"""
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_flatten_honors_shape_init_replaced_before_binding_import() -> None:
    script = """
import os
directories = [os.add_dll_directory(p) for p in os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if p] if os.name == 'nt' else []
import numpy as np
from ospf_python.multiarray import shape

original = shape.DynShape.__init__
calls = []

def construct(self, dims, storage_order=shape.StorageOrder.ROW_MAJOR):
    calls.append(dims)
    original(self, dims, storage_order)

shape.DynShape.__init__ = construct
from ospf_python.multiarray import MultiArray

source = MultiArray(shape.Shape1(6), np.arange(6))
assert source.flatten().unwrap()._data.tolist() == list(range(6))
assert calls == [(6,)]
"""
    completed = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, timeout=30
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
