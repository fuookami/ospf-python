"""Tests for AccessOrder, IteratorPosition, MultiIndexIterator."""

from __future__ import annotations

import pytest

from ospf_python.multiarray.access_order import (
    AccessOrder,
    IteratorPosition,
    MultiIndexIterator,
    MultiIndexSequence,
)

# ── AccessOrder enum ──────────────────────────────────────────────


class TestAccessOrderEnum:
    def test_c_order_member_exists(self) -> None:
        assert AccessOrder.C_ORDER is not None

    def test_f_order_member_exists(self) -> None:
        assert AccessOrder.F_ORDER is not None

    def test_default_member_exists(self) -> None:
        assert AccessOrder.DEFAULT is not None

    def test_default_is_not_f_order(self) -> None:
        assert AccessOrder.DEFAULT != AccessOrder.F_ORDER


# ── IteratorPosition ──────────────────────────────────────────────


class TestIteratorPosition:
    def test_creation(self) -> None:
        pos = IteratorPosition(indices=(0, 0, 0))
        assert pos.indices == (0, 0, 0)

    def test_equality(self) -> None:
        a = IteratorPosition(indices=(1, 2, 3))
        b = IteratorPosition(indices=(1, 2, 3))
        assert a == b

    def test_inequality(self) -> None:
        a = IteratorPosition(indices=(1, 2, 3))
        b = IteratorPosition(indices=(1, 2, 4))
        assert a != b

    def test_frozen(self) -> None:
        pos = IteratorPosition(indices=(1, 2))
        with pytest.raises(AttributeError):
            pos.indices = (3, 4)  # type: ignore[misc]


# ── MultiIndexIterator ────────────────────────────────────────────


class TestMultiIndexIterator:
    """Test the multi-dimensional index iterator."""

    def test_2x3_c_order(self) -> None:
        it = MultiIndexIterator((2, 3), access_order=AccessOrder.C_ORDER)
        indices = [pos.indices for pos in it]
        expected = [
            (0, 0),
            (0, 1),
            (0, 2),
            (1, 0),
            (1, 1),
            (1, 2),
        ]
        assert len(indices) == 6
        assert indices == expected

    def test_2x3_f_order(self) -> None:
        it = MultiIndexIterator((2, 3), access_order=AccessOrder.F_ORDER)
        indices = [pos.indices for pos in it]
        expected = [
            (0, 0),
            (1, 0),
            (0, 1),
            (1, 1),
            (0, 2),
            (1, 2),
        ]
        assert len(indices) == 6
        assert indices == expected

    def test_2x2x2_c_order(self) -> None:
        it = MultiIndexIterator((2, 2, 2), access_order=AccessOrder.C_ORDER)
        indices = [pos.indices for pos in it]
        assert len(indices) == 8
        assert indices[0] == (0, 0, 0)
        assert indices[-1] == (1, 1, 1)
        # C-order: last dimension changes fastest
        assert indices[1] == (0, 0, 1)
        assert indices[2] == (0, 1, 0)

    def test_2x2x2_f_order(self) -> None:
        it = MultiIndexIterator((2, 2, 2), access_order=AccessOrder.F_ORDER)
        indices = [pos.indices for pos in it]
        assert len(indices) == 8
        # F-order: first dimension changes fastest
        assert indices[0] == (0, 0, 0)
        assert indices[1] == (1, 0, 0)
        assert indices[2] == (0, 1, 0)

    def test_default_access_order_is_c_order(self) -> None:
        default = [pos.indices for pos in MultiIndexIterator((2, 3))]
        c_order = [
            pos.indices
            for pos in MultiIndexIterator((2, 3), access_order=AccessOrder.C_ORDER)
        ]
        assert default == c_order

    def test_single_element(self) -> None:
        it = MultiIndexIterator((1, 1))
        indices = [pos.indices for pos in it]
        assert len(indices) == 1
        assert indices[0] == (0, 0)

    def test_empty_shape_yields_nothing(self) -> None:
        it = MultiIndexIterator((0,))
        indices = list(it)
        assert indices == []

    def test_len(self) -> None:
        it = MultiIndexIterator((3, 4, 5))
        assert len(it) == 60

    def test_all_indices_unique(self) -> None:
        it = MultiIndexIterator((3, 3, 3))
        indices = [pos.indices for pos in it]
        assert len(set(indices)) == 27

    def test_1d(self) -> None:
        it = MultiIndexIterator((4,))
        indices = [pos.indices for pos in it]
        assert indices == [(0,), (1,), (2,), (3,)]


# ── MultiIndexSequence ────────────────────────────────────────────


class TestMultiIndexSequence:
    def test_to_list(self) -> None:
        seq = MultiIndexSequence((2, 3))
        lst = seq.to_list()
        assert len(lst) == 6
        assert lst[0].indices == (0, 0)

    def test_len(self) -> None:
        seq = MultiIndexSequence((3, 4))
        assert len(seq) == 12
