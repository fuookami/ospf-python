"""公开形状切换前的值对象合同 / Public shape value-object contracts before cutover."""

from __future__ import annotations

import copy
import inspect
import itertools
import pickle
from dataclasses import FrozenInstanceError, asdict, astuple, dataclass, fields, replace
from typing import Any

import pytest

import ospf_python.multiarray as public
from ospf_python.multiarray.block_multi_array import BlockMultiArray
from ospf_python.multiarray.shape import (
    DynShape,
    Shape,
    Shape1,
    Shape2,
    Shape3,
    Shape4,
    StorageOrder,
)

_CASES = [
    (Shape1, (2,), (2,)),
    (Shape2, (2, 3), (2, 3)),
    (Shape3, (2, 3, 4), (2, 3, 4)),
    (Shape4, (2, 3, 4, 5), (2, 3, 4, 5)),
    (DynShape, ((2, 3, 4, 5, 6),), (2, 3, 4, 5, 6)),
]


class DerivedShape2(Shape2):
    """普通子类的额外状态 / Additional state on an ordinary subclass."""

    label = "derived"


@dataclass(frozen=True)
class LabeledShape2(Shape2):
    """下游 dataclass 字段扩展 / Downstream dataclass field extension."""

    label: str = "labeled"


@pytest.mark.parametrize(("cls", "args", "dims"), _CASES)
def test_public_identity_constructor_dataclass_and_hash(
    cls: type[Any], args: tuple[Any, ...], dims: tuple[int, ...]
) -> None:
    value = cls(*args, StorageOrder.COLUMN_MAJOR)
    names = (
        [f"d{i}" for i in range(len(dims))] if cls is not DynShape else ["dims"]
    ) + ["storage_order"]
    assert getattr(public, cls.__name__) is cls
    signature = inspect.signature(cls)
    assert list(signature.parameters) == names
    assert all(
        p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for p in signature.parameters.values()
    )
    assert [f.name for f in fields(cls)] == names
    assert cls.__match_args__ == tuple(names)
    assert value.dims == dims
    assert isinstance(value, Shape)
    assert astuple(value) == (*args, StorageOrder.COLUMN_MAJOR)
    assert asdict(value) == dict(
        zip(names, (*args, StorageOrder.COLUMN_MAJOR), strict=True)
    )
    assert hash(value) == hash((*args, StorageOrder.COLUMN_MAJOR))
    assert value == cls(*args, StorageOrder.COLUMN_MAJOR)
    assert value != cls(*args)
    assert repr(value).startswith(cls.__name__ + "(")
    assert "COLUMN_MAJOR" in repr(value)
    replaced = replace(value, storage_order=StorageOrder.ROW_MAJOR)
    assert type(replaced) is cls
    assert replaced == cls(*args)
    with pytest.raises(FrozenInstanceError):
        value.storage_order = StorageOrder.ROW_MAJOR


@pytest.mark.parametrize(("cls", "args", "dims"), _CASES)
@pytest.mark.parametrize("protocol", range(pickle.HIGHEST_PROTOCOL + 1))
def test_serialization_and_copy_preserve_fields_and_behavior(
    *, cls: type[Any], args: tuple[Any, ...], dims: tuple[int, ...], protocol: int
) -> None:
    value = cls(*args, StorageOrder.COLUMN_MAJOR)
    for restored in (
        pickle.loads(pickle.dumps(value, protocol)),
        copy.copy(value),
        copy.deepcopy(value),
    ):
        assert type(restored) is cls
        assert restored == value
        assert asdict(restored) == asdict(value)
        assert restored.dims == dims
        assert restored.strides() == value.strides()
        assert restored.flat_index(*(d - 1 for d in dims)) == value.size - 1


def test_pattern_matching_and_factory_self_for_subclasses() -> None:
    value = DerivedShape2.of(2, 3)
    assert type(value) is DerivedShape2
    assert value != Shape2.of(2, 3)
    match value:
        case Shape2(2, 3, StorageOrder.ROW_MAJOR):
            pass
        case _:
            pytest.fail("Public positional shape pattern changed")
    for cls, args, _ in _CASES[:-1]:
        assert cls.of(*args) == cls(*args)
    labeled = LabeledShape2(2, 3, label="extra")
    assert [f.name for f in fields(labeled)] == ["d0", "d1", "storage_order", "label"]
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        restored = pickle.loads(pickle.dumps(labeled, protocol))
        assert type(restored) is LabeledShape2
        assert restored.label == "extra"
        assert restored.flat_index(1, 2) == 5
    ordinary = DerivedShape2(2, 3)
    object.__setattr__(ordinary, "payload", {"tag": [1, 2]})
    for restored in (
        copy.copy(ordinary),
        copy.deepcopy(ordinary),
        pickle.loads(pickle.dumps(ordinary)),
    ):
        assert type(restored) is DerivedShape2
        assert restored.payload == {"tag": [1, 2]}
        assert restored.flat_index(1, 2) == 5


def test_legacy_field_only_pickles_remain_loadable() -> None:
    # 固定的迁移前 protocol-0 数据，不载入外部 pickle。 / Fixed pre-migration protocol-0 data, never external pickle input.
    payloads = [
        b"ccopy_reg\n_reconstructor\np0\n(cospf_python.multiarray.shape\nShape2\np1\nc__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nVd0\np6\nI2\nsVd1\np7\nI3\nsVstorage_order\np8\ncospf_python.multiarray.shape\nStorageOrder\np9\n(I2\ntp10\nRp11\nsb.",
        b"ccopy_reg\n_reconstructor\np0\n(cospf_python.multiarray.shape\nDynShape\np1\nc__builtin__\nobject\np2\nNtp3\nRp4\n(dp5\nVdims\np6\n(I2\nI3\ntp7\nsVstorage_order\np8\ncospf_python.multiarray.shape\nStorageOrder\np9\n(I2\ntp10\nRp11\nsb.",
    ]
    for payload, cls, args in zip(
        payloads, [Shape2, DynShape], [(2, 3), ((2, 3),)], strict=True
    ):
        restored = pickle.loads(payload)
        assert type(restored) is cls
        assert restored == cls(*args, StorageOrder.COLUMN_MAJOR)
        assert restored.flat_index(1, 2) == 5


@pytest.mark.parametrize("order", [StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR])
def test_valid_coordinate_mapping_is_a_bijection(order: StorageOrder) -> None:
    for cls, args, dims in _CASES:
        shape = cls(*args, order)
        offsets = [
            shape.flat_index(*vector)
            for vector in itertools.product(*(range(d) for d in dims))
        ]
        assert sorted(offsets) == list(range(shape.size))
    scalar = DynShape((), order)
    assert scalar.size == 1
    assert scalar.ndim == 0
    assert scalar.strides() == ()
    assert scalar.flat_index() == 0


def test_public_unbounded_shape_metadata_supports_sparse_use() -> None:
    dims = (1 << 128, 3)
    shape = DynShape(dims)
    assert shape.size == (1 << 128) * 3
    assert shape.strides() == (3, 1)
    sparse = BlockMultiArray(shape, default=-1)
    sparse.set((1 << 128) - 1, 2, 7)
    assert sparse.block_count() == 1
    assert sparse.get((1 << 128) - 1, 2) == 7
    assert sparse.get(0, 0) == -1
