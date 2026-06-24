"""函数式工具模块测试。

测试 Boolean、Collection、List、Map、MinMax、Nullable、
Predicate、DateTimeRange 子模块的功能。
"""

from __future__ import annotations

from datetime import datetime

from ospf_python.utils.functional.boolean import all_of, any_of, none_of
from ospf_python.utils.functional.collection import (
    chunked,
    distinct_by,
    flatten,
    sum_of,
    zip_with_next,
)
from ospf_python.utils.functional.date_time_range import (
    DateTimeRange,
    contains,
    overlaps,
)
from ospf_python.utils.functional.list import (
    first_or_none,
    last_or_none,
    max_by_or_none,
    min_by_or_none,
    single_or_none,
)
from ospf_python.utils.functional.map import (
    filter_keys,
    filter_values,
    map_keys,
    map_values,
    merge,
)
from ospf_python.utils.functional.min_max import clamp, ensure_max, ensure_min
from ospf_python.utils.functional.nullable import also_not_none, let_not_none
from ospf_python.utils.functional.predicate import and_then, negate, or_else

# ---------------------------------------------------------------------------
# Boolean 测试
# ---------------------------------------------------------------------------


class TestBoolean:
    """Boolean 谓词组合工具测试。"""

    def test_all_of_all_true(self) -> None:
        pred = all_of(lambda x: x > 0, lambda x: x < 10)
        assert pred(5) is True

    def test_all_of_one_false(self) -> None:
        pred = all_of(lambda x: x > 0, lambda x: x < 10)
        assert pred(15) is False

    def test_all_of_no_predicates(self) -> None:
        pred = all_of()
        assert pred(42) is True

    def test_any_of_one_true(self) -> None:
        pred = any_of(lambda x: x > 100, lambda x: x < 0)
        assert pred(-5) is True

    def test_any_of_all_false(self) -> None:
        pred = any_of(lambda x: x > 100, lambda x: x < 0)
        assert pred(50) is False

    def test_any_of_no_predicates(self) -> None:
        pred = any_of()
        assert pred(42) is False

    def test_none_of_all_false(self) -> None:
        pred = none_of(lambda x: x > 100, lambda x: x < 0)
        assert pred(50) is True

    def test_none_of_one_true(self) -> None:
        pred = none_of(lambda x: x > 100, lambda x: x < 0)
        assert pred(-1) is False


# ---------------------------------------------------------------------------
# Collection 测试
# ---------------------------------------------------------------------------


class TestCollection:
    """Collection 集合操作工具测试。"""

    def test_flatten_nested_lists(self) -> None:
        result = flatten([[1, 2], [3], [4, 5]])
        assert result == [1, 2, 3, 4, 5]

    def test_flatten_empty(self) -> None:
        assert flatten([]) == []

    def test_flatten_contains_empty(self) -> None:
        assert flatten([[], [1], []]) == [1]

    def test_distinct_by_keeps_first(self) -> None:
        items = ["apple", "avocado", "banana", "blueberry"]
        result = distinct_by(items, key_func=lambda s: s[0])
        assert result == ["apple", "banana"]

    def test_distinct_by_empty(self) -> None:
        assert distinct_by([], key_func=lambda x: x) == []

    def test_distinct_by_no_duplicates(self) -> None:
        items = [1, 2, 3]
        result = distinct_by(items, key_func=lambda x: x)
        assert result == [1, 2, 3]

    def test_chunked_even_split(self) -> None:
        result = chunked([1, 2, 3, 4], size=2)
        assert result == [[1, 2], [3, 4]]

    def test_chunked_uneven(self) -> None:
        result = chunked([1, 2, 3, 4, 5], size=2)
        assert result == [[1, 2], [3, 4], [5]]

    def test_chunked_size_larger_than_list(self) -> None:
        result = chunked([1, 2], size=10)
        assert result == [[1, 2]]

    def test_zip_with_next(self) -> None:
        result = zip_with_next([1, 2, 3, 4])
        assert result == [(1, 2), (2, 3), (3, 4)]

    def test_zip_with_next_empty(self) -> None:
        assert zip_with_next([]) == []

    def test_zip_with_next_single(self) -> None:
        assert zip_with_next([1]) == []

    def test_sum_of_with_selector(self) -> None:
        items = [{"v": 1}, {"v": 2}, {"v": 3}]
        assert sum_of(items, selector=lambda x: x["v"]) == 6.0

    def test_sum_of_empty(self) -> None:
        assert sum_of([], selector=lambda x: x) == 0.0


# ---------------------------------------------------------------------------
# List 测试
# ---------------------------------------------------------------------------


class TestList:
    """List 列表查询扩展工具测试。"""

    def test_first_or_none_found(self) -> None:
        result = first_or_none([1, 2, 3], predicate=lambda x: x > 1)
        assert result == 2

    def test_first_or_none_not_found(self) -> None:
        result = first_or_none([1, 2, 3], predicate=lambda x: x > 10)
        assert result is None

    def test_first_or_none_empty(self) -> None:
        result = first_or_none([], predicate=lambda x: True)
        assert result is None

    def test_last_or_none_found(self) -> None:
        result = last_or_none([1, 2, 3, 4], predicate=lambda x: x % 2 == 0)
        assert result == 4

    def test_last_or_none_not_found(self) -> None:
        result = last_or_none([1, 3, 5], predicate=lambda x: x % 2 == 0)
        assert result is None

    def test_single_or_none_unique_match(self) -> None:
        result = single_or_none([1, 2, 3], predicate=lambda x: x == 2)
        assert result == 2

    def test_single_or_none_multiple_matches(self) -> None:
        result = single_or_none([1, 2, 2, 3], predicate=lambda x: x == 2)
        assert result is None

    def test_single_or_none_no_match(self) -> None:
        result = single_or_none([1, 2, 3], predicate=lambda x: x > 10)
        assert result is None

    def test_min_by_or_none(self) -> None:
        result = min_by_or_none(
            [{"n": "b", "v": 3}, {"n": "a", "v": 1}],
            selector=lambda x: x["v"],
        )
        assert result == {"n": "a", "v": 1}

    def test_min_by_or_none_empty(self) -> None:
        result = min_by_or_none([], selector=lambda x: x)
        assert result is None

    def test_max_by_or_none(self) -> None:
        result = max_by_or_none(
            [{"v": 1}, {"v": 10}, {"v": 5}],
            selector=lambda x: x["v"],
        )
        assert result == {"v": 10}

    def test_max_by_or_none_empty(self) -> None:
        result = max_by_or_none([], selector=lambda x: x)
        assert result is None


# ---------------------------------------------------------------------------
# Map 测试
# ---------------------------------------------------------------------------


class TestMap:
    """Map 字典操作扩展工具测试。"""

    def test_map_values(self) -> None:
        result = map_values({"a": 1, "b": 2}, f=lambda v: v * 10)
        assert result == {"a": 10, "b": 20}

    def test_map_values_empty(self) -> None:
        assert map_values({}, f=lambda v: v) == {}

    def test_map_keys(self) -> None:
        result = map_keys({"a": 1, "b": 2}, f=str.upper)
        assert result == {"A": 1, "B": 2}

    def test_map_keys_empty(self) -> None:
        assert map_keys({}, f=lambda k: k) == {}

    def test_filter_keys(self) -> None:
        d = {"aa": 1, "b": 2, "ccc": 3}
        result = filter_keys(d, predicate=lambda k: len(k) > 1)
        assert result == {"aa": 1, "ccc": 3}

    def test_filter_values(self) -> None:
        d = {"a": 1, "b": 2, "c": 3}
        result = filter_values(d, predicate=lambda v: v > 1)
        assert result == {"b": 2, "c": 3}

    def test_merge_no_overlap(self) -> None:
        result = merge({"a": 1}, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_merge_later_overrides(self) -> None:
        result = merge({"a": 1}, {"a": 2, "b": 3})
        assert result == {"a": 2, "b": 3}

    def test_merge_empty(self) -> None:
        assert merge() == {}


# ---------------------------------------------------------------------------
# MinMax 测试
# ---------------------------------------------------------------------------


class TestMinMax:
    """MinMax 数值边界裁剪工具测试。"""

    def test_clamp_within_range(self) -> None:
        assert clamp(5, min_val=0, max_val=10) == 5

    def test_clamp_below_min(self) -> None:
        assert clamp(-5, min_val=0, max_val=10) == 0

    def test_clamp_above_max(self) -> None:
        assert clamp(15, min_val=0, max_val=10) == 10

    def test_clamp_at_boundaries(self) -> None:
        assert clamp(0, min_val=0, max_val=10) == 0
        assert clamp(10, min_val=0, max_val=10) == 10

    def test_ensure_min_below(self) -> None:
        assert ensure_min(3, min_val=5) == 5

    def test_ensure_min_above(self) -> None:
        assert ensure_min(8, min_val=5) == 8

    def test_ensure_max_above(self) -> None:
        assert ensure_max(8, max_val=5) == 5

    def test_ensure_max_below(self) -> None:
        assert ensure_max(3, max_val=5) == 3

    def test_clamp_with_floats(self) -> None:
        assert clamp(1.5, min_val=0.0, max_val=1.0) == 1.0


# ---------------------------------------------------------------------------
# Nullable 测试
# ---------------------------------------------------------------------------


class TestNullable:
    """Nullable 可空值安全操作工具测试。"""

    def test_let_not_none_with_value(self) -> None:
        result = let_not_none(5, f=lambda x: x * 2)
        assert result == 10

    def test_let_not_none_with_none(self) -> None:
        result = let_not_none(None, f=lambda x: x * 2)
        assert result is None

    def test_let_not_none_transform_type(self) -> None:
        result = let_not_none(42, f=lambda x: str(x))
        assert result == "42"

    def test_also_not_none_with_value(self) -> None:
        log: list[int] = []
        result = also_not_none(5, f=lambda x: log.append(x))
        assert result == 5
        assert log == [5]

    def test_also_not_none_with_none(self) -> None:
        log: list[int] = []
        result = also_not_none(None, f=lambda x: log.append(x))
        assert result is None
        assert log == []


# ---------------------------------------------------------------------------
# Predicate 测试
# ---------------------------------------------------------------------------


class TestPredicate:
    """Predicate 谓词组合子工具测试。"""

    def test_negate_true_to_false(self) -> None:
        is_even = lambda x: x % 2 == 0
        is_odd = negate(is_even)
        assert is_odd(3) is True
        assert is_odd(4) is False

    def test_and_then_all_pass(self) -> None:
        pred = and_then(lambda x: x > 0, lambda x: x < 10)
        assert pred(5) is True

    def test_and_then_one_fails(self) -> None:
        pred = and_then(lambda x: x > 0, lambda x: x < 10)
        assert pred(-1) is False

    def test_or_else_one_passes(self) -> None:
        pred = or_else(lambda x: x > 100, lambda x: x < 0)
        assert pred(-5) is True

    def test_or_else_none_pass(self) -> None:
        pred = or_else(lambda x: x > 100, lambda x: x < 0)
        assert pred(50) is False


# ---------------------------------------------------------------------------
# DateTimeRange 测试
# ---------------------------------------------------------------------------


class TestDateTimeRange:
    """DateTimeRange 日期时间范围工具测试。"""

    def _make_range(self, start_h: int, end_h: int) -> DateTimeRange:
        return DateTimeRange(
            start=datetime(2026, 1, 1, start_h),
            end=datetime(2026, 1, 1, end_h),
        )

    def test_contains_inside(self) -> None:
        r = self._make_range(8, 17)
        dt = datetime(2026, 1, 1, 12)
        assert contains(r, dt) is True

    def test_contains_at_start(self) -> None:
        r = self._make_range(8, 17)
        dt = datetime(2026, 1, 1, 8)
        assert contains(r, dt) is True

    def test_contains_at_end(self) -> None:
        r = self._make_range(8, 17)
        dt = datetime(2026, 1, 1, 17)
        assert contains(r, dt) is True

    def test_contains_outside_before(self) -> None:
        r = self._make_range(8, 17)
        dt = datetime(2026, 1, 1, 7)
        assert contains(r, dt) is False

    def test_contains_outside_after(self) -> None:
        r = self._make_range(8, 17)
        dt = datetime(2026, 1, 1, 18)
        assert contains(r, dt) is False

    def test_overlaps_partial(self) -> None:
        r1 = self._make_range(8, 12)
        r2 = self._make_range(10, 16)
        assert overlaps(r1, r2) is True

    def test_overlaps_no_overlap(self) -> None:
        r1 = self._make_range(8, 10)
        r2 = self._make_range(14, 16)
        assert overlaps(r1, r2) is False

    def test_overlaps_touching(self) -> None:
        r1 = self._make_range(8, 12)
        r2 = self._make_range(12, 16)
        assert overlaps(r1, r2) is True

    def test_overlaps_symmetric(self) -> None:
        r1 = self._make_range(8, 12)
        r2 = self._make_range(10, 16)
        assert overlaps(r1, r2) is True
        assert overlaps(r2, r1) is True

    def test_range_is_frozen(self) -> None:
        import pytest

        r = self._make_range(8, 17)
        with pytest.raises(AttributeError):
            r.start = datetime(2026, 2, 1)  # type: ignore[misc]
