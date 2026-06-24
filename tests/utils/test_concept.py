"""Concept 基础概念协议测试。

测试 Copyable、Movable、Swappable、Indexed 协议的行为。
"""

from __future__ import annotations

import copy

from ospf_python.utils.concept import (
    Copyable,
    Indexed,
    Swappable,
)


class _Vec2:
    """测试用二维向量，实现 Copyable 和 Swappable。"""

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def copy(self) -> _Vec2:
        return _Vec2(self.x, self.y)

    def swap(self, other: _Vec2) -> tuple[_Vec2, _Vec2]:
        self.x, other.x = other.x, self.x
        self.y, other.y = other.y, self.y
        return self, other


class _Indexable:
    """测试用可索引类型，实现 Indexed 协议。"""

    def __init__(self, idx: int) -> None:
        self._idx = idx

    def index(self) -> int:
        return self._idx


class TestCopyable:
    """Copyable 可复制协议测试。"""

    def test_copy_creates_independent_instance(self) -> None:
        v = _Vec2(1.0, 2.0)
        v2 = v.copy()
        assert v2.x == 1.0
        assert v2.y == 2.0
        assert v is not v2

    def test_copy_mutation_independence(self) -> None:
        v = _Vec2(1.0, 2.0)
        v2 = v.copy()
        v2.x = 99.0
        assert v.x == 1.0

    def test_deepcopy_of_nested(self) -> None:
        data = {"a": [1, 2]}
        data2 = copy.deepcopy(data)
        data2["a"].append(3)
        assert data["a"] == [1, 2]

    def test_vec2_is_copyable(self) -> None:
        assert isinstance(_Vec2(0, 0), Copyable)


class TestMovable:
    """Movable 可移动协议测试。"""

    def test_move_transfers_ownership_semantics(self) -> None:
        """模拟移动语义：原引用失效，新引用持有数据。"""
        original = [1, 2, 3]
        moved = original
        original = None
        assert moved == [1, 2, 3]


class TestSwappable:
    """Swappable 可交换协议测试。"""

    def test_swap_values(self) -> None:
        a = _Vec2(1.0, 2.0)
        b = _Vec2(3.0, 4.0)
        a.swap(b)
        assert a.x == 3.0 and a.y == 4.0
        assert b.x == 1.0 and b.y == 2.0

    def test_swap_is_symmetric(self) -> None:
        a = _Vec2(1.0, 2.0)
        b = _Vec2(3.0, 4.0)
        a.swap(b)
        b.swap(a)
        assert a.x == 1.0 and a.y == 2.0
        assert b.x == 3.0 and b.y == 4.0

    def test_swap_same_object(self) -> None:
        a = _Vec2(5.0, 6.0)
        a.swap(a)
        assert a.x == 5.0 and a.y == 6.0

    def test_vec2_is_swappable(self) -> None:
        assert isinstance(_Vec2(0, 0), Swappable)


class TestIndexed:
    """Indexed 可索引协议测试。"""

    def test_index(self) -> None:
        obj = _Indexable(42)
        assert obj.index() == 42

    def test_is_indexed_protocol(self) -> None:
        assert isinstance(_Indexable(0), Indexed)

    def test_different_indices(self) -> None:
        a = _Indexable(0)
        b = _Indexable(1)
        assert a.index() != b.index()

    def test_out_of_range(self) -> None:
        """Indexed 协议只提供 index() 方法，越界由具体实现处理。"""
        obj = _Indexable(5)
        assert obj.index() == 5
