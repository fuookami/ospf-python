"""Extra tests for DataFrameBuilder, null handling.

DataFrameBuilder、空值处理的额外测试。
"""

from __future__ import annotations

import pytest

from ospf_python.multiarray.data_frame import (
    DataFrame,
    DataFrameBuilder,
    NullableValue,
)

# -- DataFrameBuilder edge cases -------------------------------------


class TestDataFrameBuilderEdgeCases:
    """Test DataFrameBuilder boundary conditions."""

    def test_builder_multiple_columns(self) -> None:
        """多列构建 / Multi-column build."""
        df = (
            DataFrameBuilder()
            .add_column("a", [1, 2, 3])
            .add_column("b", [4, 5, 6])
            .add_column("c", [7, 8, 9])
            .build()
        )
        assert df.columns() == ["a", "b", "c"]
        assert df.rows() == 3

    def test_builder_empty(self) -> None:
        """空构建器 / Empty builder."""
        df = DataFrameBuilder().build()
        assert df.rows() == 0
        assert df.columns() == []

    def test_builder_single_row(self) -> None:
        """单行构建 / Single row build."""
        df = DataFrameBuilder().add_column("x", [42]).build()
        assert df.rows() == 1
        assert df.get("x", 0) == 42

    def test_builder_with_all_nulls(self) -> None:
        """全空列 / All null column."""
        df = DataFrameBuilder().add_column("a", [None, None, None]).build()
        assert df.rows() == 3
        assert df.get("a", 0) is None
        assert df.get("a", 1) is None
        assert df.get("a", 2) is None

    def test_builder_chaining_returns_self(self) -> None:
        """链式调用返回自身 / Chaining returns self."""
        builder = DataFrameBuilder()
        result = builder.add_column("a", [1])
        assert result is builder


# -- NullableValue edge cases ----------------------------------------


class TestNullableValueEdgeCases:
    """Test NullableValue boundary conditions."""

    def test_nullable_zero(self) -> None:
        """零值非空 / Zero value is not null."""
        nv = NullableValue(0)
        assert nv.is_present is True
        assert nv.is_null is False
        assert nv.value == 0

    def test_nullable_empty_string(self) -> None:
        """空字符串非空 / Empty string is not null."""
        nv = NullableValue("")
        assert nv.is_present is True
        assert nv.is_null is False

    def test_nullable_false(self) -> None:
        """False 非空 / False is not null."""
        nv = NullableValue(False)
        assert nv.is_present is True
        assert nv.is_null is False

    def test_or_else_with_zero(self) -> None:
        """零值返回零 / Zero returns zero."""
        nv = NullableValue(0)
        assert nv.or_else(99) == 0

    def test_or_else_with_empty_string(self) -> None:
        """空字符串返回空 / Empty string returns empty."""
        nv = NullableValue("")
        assert nv.or_else("default") == ""

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        nv = NullableValue(42)
        with pytest.raises(AttributeError):
            nv.value = 99  # type: ignore[misc]


# -- DataFrame null handling -----------------------------------------


class TestDataFrameNullHandling:
    """Test DataFrame null value handling."""

    def test_all_null_column(self) -> None:
        """全空列 / All null column."""
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [None, None])
        assert df.get("a", 0) is None
        assert df.get("a", 1) is None

    def test_mixed_null_column(self) -> None:
        """混合空列 / Mixed null column."""
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, None, 3, None])
        assert df.get("a", 0) == 1
        assert df.get("a", 1) is None
        assert df.get("a", 2) == 3
        assert df.get("a", 3) is None

    def test_to_list_with_nulls(self) -> None:
        """带空值转列表 / To list with nulls."""
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, None, 3])
        rows = df.to_list()
        assert rows[0]["a"] == 1
        assert rows[1]["a"] is None
        assert rows[2]["a"] == 3

    def test_add_shorter_column_pads_null(self) -> None:
        """短列补齐空值 / Shorter column pads with null."""
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, 2, 3, 4, 5])
        df.add_column("b", [10, 20])
        assert df.get("b", 0) == 10
        assert df.get("b", 1) == 20
        assert df.get("b", 2) is None
        assert df.get("b", 3) is None
        assert df.get("b", 4) is None


# -- DataFrame edge cases --------------------------------------------


class TestDataFrameEdgeCasesExtra:
    """Test DataFrame extra edge cases."""

    def test_get_nonexistent_column(self) -> None:
        """获取不存在列 / Get nonexistent column."""
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, 2])
        assert df.get("missing", 0) is None

    def test_get_out_of_bounds(self) -> None:
        """越界获取 / Out of bounds get."""
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, 2])
        assert df.get("a", 100) is None

    def test_get_negative_index(self) -> None:
        """负索引获取 / Negative index get."""
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, 2])
        assert df.get("a", -1) is None

    def test_row_count_consistency(self) -> None:
        """行数一致性 / Row count consistency."""
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, 2, 3])
        assert df.row_count == df.rows()

    def test_to_list_empty(self) -> None:
        """空 DataFrame 转列表 / Empty DataFrame to list."""
        df: DataFrame[int] = DataFrame()
        assert df.to_list() == []
