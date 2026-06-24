"""Extra tests for AccessOrder, reverse iteration, edge cases.

访问顺序的额外测试：逆序、边界情况。
"""

from __future__ import annotations

from ospf_python.multiarray.access_order import (
    AccessOrder,
    IteratorPosition,
    MultiIndexIterator,
    MultiIndexSequence,
)

# -- AccessOrder reverse / edge cases --------------------------------


class TestAccessOrderReverse:
    """Test reverse iteration and boundary conditions."""

    def test_reverse_c_order_2x3(self) -> None:
        """C 阶段逆序迭代 / Reverse C-order iteration."""
        it = MultiIndexIterator((2, 3), access_order=AccessOrder.C_ORDER)
        indices = [pos.indices for pos in it]
        reversed_indices = list(reversed(indices))
        assert reversed_indices[0] == (1, 2)
        assert reversed_indices[-1] == (0, 0)

    def test_reverse_f_order_2x3(self) -> None:
        """F 阶段逆序迭代 / Reverse F-order iteration."""
        it = MultiIndexIterator((2, 3), access_order=AccessOrder.F_ORDER)
        indices = [pos.indices for pos in it]
        reversed_indices = list(reversed(indices))
        assert reversed_indices[0] == (1, 2)
        assert reversed_indices[-1] == (0, 0)

    def test_3x1x2_c_order(self) -> None:
        """3x1x2 C 阶段迭代 / 3x1x2 C-order iteration."""
        it = MultiIndexIterator((3, 1, 2), access_order=AccessOrder.C_ORDER)
        indices = [pos.indices for pos in it]
        assert len(indices) == 6
        assert indices[0] == (0, 0, 0)
        assert indices[1] == (0, 0, 1)
        assert indices[2] == (1, 0, 0)
        assert indices[3] == (1, 0, 1)
        assert indices[4] == (2, 0, 0)
        assert indices[5] == (2, 0, 1)

    def test_3x1x2_f_order(self) -> None:
        """3x1x2 F 阶段迭代 / 3x1x2 F-order iteration."""
        it = MultiIndexIterator((3, 1, 2), access_order=AccessOrder.F_ORDER)
        indices = [pos.indices for pos in it]
        assert len(indices) == 6
        assert indices[0] == (0, 0, 0)
        assert indices[1] == (1, 0, 0)
        assert indices[2] == (2, 0, 0)
        assert indices[3] == (0, 0, 1)
        assert indices[4] == (1, 0, 1)
        assert indices[5] == (2, 0, 1)

    def test_1x1_shape(self) -> None:
        """1x1 形状迭代 / 1x1 shape iteration."""
        it = MultiIndexIterator((1, 1))
        indices = [pos.indices for pos in it]
        assert indices == [(0, 0)]

    def test_5x1_shape(self) -> None:
        """5x1 形状迭代 / 5x1 shape iteration."""
        it = MultiIndexIterator((5, 1))
        indices = [pos.indices for pos in it]
        assert len(indices) == 5
        assert indices[0] == (0, 0)
        assert indices[4] == (4, 0)

    def test_1x5_shape(self) -> None:
        """1x5 形状迭代 / 1x5 shape iteration."""
        it = MultiIndexIterator((1, 5))
        indices = [pos.indices for pos in it]
        assert len(indices) == 5
        assert indices[0] == (0, 0)
        assert indices[4] == (0, 4)

    def test_empty_shape_with_zero_dim(self) -> None:
        """零维度形状返回空迭代 / Zero-dim shape yields nothing."""
        it = MultiIndexIterator((0, 5))
        assert list(it) == []

    def test_multiple_zero_dims(self) -> None:
        """多维零形状返回空迭代 / Multi-zero-dim yields nothing."""
        it = MultiIndexIterator((0, 0, 0))
        assert list(it) == []

    def test_iterator_consumed_after_iteration(self) -> None:
        """迭代器消耗后为空 / Iterator empty after consumption."""
        it = MultiIndexIterator((2, 2))
        first_pass = list(it)
        second_pass = list(it)
        assert len(first_pass) == 4
        assert len(second_pass) == 0


# -- IteratorPosition edge cases -------------------------------------


class TestIteratorPositionEdgeCases:
    """Test IteratorPosition boundary conditions."""

    def test_single_element_tuple(self) -> None:
        """单元素元组 / Single element tuple."""
        pos = IteratorPosition(indices=(42,))
        assert pos.indices == (42,)

    def test_large_tuple(self) -> None:
        """大元组 / Large tuple."""
        indices = tuple(range(100))
        pos = IteratorPosition(indices=indices)
        assert pos.indices == indices

    def test_hash_consistency(self) -> None:
        """相同位置哈希一致 / Same position hash consistency."""
        a = IteratorPosition(indices=(1, 2, 3))
        b = IteratorPosition(indices=(1, 2, 3))
        assert hash(a) == hash(b)


# -- MultiIndexSequence edge cases -----------------------------------


class TestMultiIndexSequenceEdgeCases:
    """Test MultiIndexSequence boundary conditions."""

    def test_f_order_sequence(self) -> None:
        """F 阶段序列 / F-order sequence."""
        seq = MultiIndexSequence((2, 3), access_order=AccessOrder.F_ORDER)
        lst = seq.to_list()
        assert len(lst) == 6
        assert lst[0].indices == (0, 0)
        assert lst[1].indices == (1, 0)

    def test_len_matches_iteration(self) -> None:
        """长度与迭代一致 / Length matches iteration count."""
        seq = MultiIndexSequence((3, 4, 5))
        assert len(seq) == 60
        assert len(list(seq)) == 60

    def test_single_dim_sequence(self) -> None:
        """单维序列 / Single dimension sequence."""
        seq = MultiIndexSequence((5,))
        lst = seq.to_list()
        assert len(lst) == 5
        assert lst[0].indices == (0,)
        assert lst[4].indices == (4,)
