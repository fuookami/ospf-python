"""公开形状 raw 字段的权威与恢复合同 / Authority and restoration of public raw shape fields."""

from __future__ import annotations

import copy
import pickle
from dataclasses import FrozenInstanceError
from typing import Any

import numpy as np
import pytest

from ospf_python._binding.multiarray import Shape as NativeShape
from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import (
    DynShape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
    StorageOrder,
)
from ospf_python.utils.functional.result import Failed

_CASES = [
    (Shape1, (2,)),
    (Shape2, (2, 3)),
    (Shape3, (2, 3, 4)),
    (Shape4, (2, 3, 4, 5)),
    (DynShape, ((2, 3),)),
]
_ORDERS = list(StorageOrder)


def _changed_state(shape: Any) -> dict[str, Any]:
    state = dict(vars(shape))
    if type(shape) is DynShape:
        state.update(dims=(3, 2))
    else:
        state.update(d0=3)
    return state


@pytest.mark.parametrize(("cls", "args"), _CASES)
@pytest.mark.parametrize("order", _ORDERS)
def test_raw_dictionary_is_live_despite_frozen_assignment(
    *, cls: type[Any], args: tuple[Any, ...], order: StorageOrder
) -> None:
    shape = cls(*args, order)
    alias = vars(shape)
    field = "dims" if cls is DynShape else "d0"
    replacement = _changed_state(shape)
    with pytest.raises(FrozenInstanceError):
        setattr(shape, field, replacement[field])

    alias.update(replacement)
    expected = cls(**replacement)
    assert vars(shape) is alias
    assert shape == expected and hash(shape) == hash(expected)
    assert shape.dims == expected.dims and shape.size == expected.size
    assert shape.strides() == expected.strides()
    assert shape.flat_index(*(dim - 1 for dim in shape.dims)) == shape.size - 1


@pytest.mark.parametrize(("cls", "args"), _CASES)
@pytest.mark.parametrize("order", _ORDERS)
def test_dictionary_replacement_detaches_old_alias_and_changes_live_metadata(
    *, cls: type[Any], args: tuple[Any, ...], order: StorageOrder
) -> None:
    shape = cls(*args, order)
    old_alias = vars(shape)
    replacement = _changed_state(shape)
    object.__setattr__(shape, "__dict__", replacement)
    assert vars(shape) is replacement and old_alias is not replacement
    old_alias.clear()
    expected = cls(**replacement)
    assert shape == expected and hash(shape) == hash(expected)
    assert shape.size == expected.size and shape.strides() == expected.strides()
    replacement["storage_order"] = StorageOrder.COLUMN_MAJOR
    assert shape.storage_order is StorageOrder.COLUMN_MAJOR
    assert shape.strides() == cls(**replacement).strides()


@pytest.mark.parametrize(("cls", "args"), _CASES)
@pytest.mark.parametrize("mode", ["deepcopy", *range(pickle.HIGHEST_PROTOCOL + 1)])
def test_field_only_restore_does_not_require_constructor_or_native_layout(
    *,
    cls: type[Any],
    args: tuple[Any, ...],
    mode: str | int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = cls(*args, StorageOrder.COLUMN_MAJOR)
    raw = object.__new__(cls)
    raw.__dict__.update(vars(expected))

    def forbidden(*args: Any, **kwargs: Any) -> None:
        pytest.fail("恢复不得重新调用构造器 / Restoration must not rerun constructors")

    monkeypatch.setattr(cls, "__init__", forbidden)
    if mode == "deepcopy":
        restored = copy.deepcopy(raw)
    else:
        assert isinstance(mode, int)
        restored = pickle.loads(pickle.dumps(raw, protocol=mode))
    assert type(restored) is cls and restored == expected
    assert vars(restored) == vars(raw)
    assert restored.size == expected.size and restored.strides() == expected.strides()
    assert restored.flat_index(*(dim - 1 for dim in restored.dims)) == restored.size - 1


@pytest.mark.parametrize(("cls", "args"), _CASES)
@pytest.mark.parametrize("order", _ORDERS)
def test_native_snapshot_revalidates_current_dictionary_and_is_not_mirrored_state(
    *, cls: type[Any], args: tuple[Any, ...], order: StorageOrder
) -> None:
    shape = cls(*args, order)
    snapshot = NativeShape.from_shape(shape).unwrap()
    original_dims = shape.dims
    vars(shape).update(_changed_state(shape))
    fresh = NativeShape.from_shape(shape).unwrap()
    assert snapshot.dims == original_dims and fresh.dims == shape.dims
    assert fresh.dims != snapshot.dims
    if cls is DynShape:
        vars(shape).update(dims=(0,))
    else:
        vars(shape).update(d0=0)
    assert isinstance(NativeShape.from_shape(shape), Failed)
    assert snapshot.dims == original_dims
    vars(shape).update(_changed_state(cls(*args, order)))
    assert NativeShape.from_shape(shape).unwrap().dims == fresh.dims


@pytest.mark.parametrize("cls", [MultiArray, MutableMultiArray])
@pytest.mark.parametrize("order", _ORDERS)
def test_arrays_observe_shared_shape_dictionary_changes_at_checked_boundary(
    *, cls: type[Any], order: StorageOrder
) -> None:
    shape = Shape2(2, 3, order)
    first = cls(shape, np.arange(6))
    second = cls(shape, np.arange(6) + 10)
    assert first.shape is second.shape is shape
    state = vars(shape)
    state.update(d0=3, d1=2)
    assert first.at(indices=(2, 1)).unwrap() == 5
    assert second.at(indices=(2, 1)).unwrap() == 15
    assert isinstance(first.at(indices=(1, 2)), Failed)
    state.update(d0=2, d1=3)
    assert first.at(indices=(1, 2)).unwrap() == 5
    assert second.at(indices=(1, 2)).unwrap() == 15


@pytest.mark.parametrize(("cls", "args"), _CASES)
def test_shallow_shape_copy_has_independent_dictionary_rebinding(
    cls: type[Any], args: tuple[Any, ...]
) -> None:
    original = cls(*args)
    shallow = copy.copy(original)
    assert shallow == original and shallow is not original
    assert vars(shallow) is not vars(original)
    for field, value in vars(original).items():
        assert vars(shallow)[field] is value
    vars(shallow).update(_changed_state(shallow))
    assert original == cls(*args) and shallow != original


@pytest.mark.parametrize(("cls", "args"), _CASES)
@pytest.mark.parametrize("order", _ORDERS)
def test_prior_arithmetic_use_does_not_freeze_later_raw_metadata(
    *, cls: type[Any], args: tuple[Any, ...], order: StorageOrder
) -> None:
    shape = cls(*args, order)
    original_state = dict(vars(shape))

    def observed(value: Any) -> tuple[Any, ...]:
        return (
            value.dims,
            value.size,
            value.strides(),
            value.flat_index(*(dim - 1 for dim in value.dims)),
            hash(value),
            repr(value),
        )

    assert observed(shape) == observed(cls(*args, order))
    changed = _changed_state(shape)
    vars(shape).update(changed)
    assert observed(shape) == observed(cls(**changed))
    object.__setattr__(shape, "__dict__", original_state)
    assert observed(shape) == observed(cls(*args, order))
