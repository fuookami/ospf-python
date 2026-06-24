"""Tests for DataFrame creation, columns, rows, builder."""

from __future__ import annotations

from ospf_python.multiarray.data_frame import DataFrame, DataFrameBuilder, NullableValue

# ── NullableValue ─────────────────────────────────────────────────


class TestNullableValue:
    def test_with_value(self) -> None:
        nv = NullableValue(42)
        assert nv.value == 42
        assert nv.is_present is True
        assert nv.is_null is False

    def test_with_none(self) -> None:
        nv = NullableValue(None)
        assert nv.value is None
        assert nv.is_present is False
        assert nv.is_null is True

    def test_or_else_with_value(self) -> None:
        nv = NullableValue(42)
        assert nv.or_else(0) == 42

    def test_or_else_with_none(self) -> None:
        nv = NullableValue(None)
        assert nv.or_else(0) == 0


# ── DataFrame creation ────────────────────────────────────────────


class TestDataFrameCreation:
    def test_create_empty(self) -> None:
        df: DataFrame[int] = DataFrame()
        assert df.row_count == 0
        assert df.rows() == 0
        assert df.columns() == []

    def test_add_column(self) -> None:
        df: DataFrame[int] = DataFrame()
        df.add_column("name", ["Alice", "Bob", "Charlie"])
        assert df.columns() == ["name"]
        assert df.rows() == 3

    def test_add_multiple_columns(self) -> None:
        df: DataFrame[int] = DataFrame()
        df.add_column("name", ["Alice", "Bob"])
        df.add_column("age", [25, 30])
        assert df.columns() == ["name", "age"]
        assert df.rows() == 2


# ── DataFrame get ─────────────────────────────────────────────────


class TestDataFrameGet:
    def test_get_by_column_and_row(self) -> None:
        df: DataFrame[int] = DataFrame()
        df.add_column("name", ["Alice", "Bob"])
        df.add_column("age", [25, 30])
        assert df.get("name", 0) == "Alice"
        assert df.get("age", 1) == 30

    def test_get_nonexistent_column(self) -> None:
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, 2])
        assert df.get("nonexistent", 0) is None

    def test_get_out_of_bounds_row(self) -> None:
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, 2])
        assert df.get("a", 5) is None

    def test_get_negative_row(self) -> None:
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, 2])
        assert df.get("a", -1) is None


# ── DataFrameBuilder ──────────────────────────────────────────────


class TestDataFrameBuilder:
    def test_builder_chaining(self) -> None:
        df = (
            DataFrameBuilder()
            .add_column("name", ["Alice", "Bob"])
            .add_column("age", [25, 30])
            .build()
        )
        assert df.columns() == ["name", "age"]
        assert df.rows() == 2

    def test_builder_single_column(self) -> None:
        df = DataFrameBuilder().add_column("x", [1, 2, 3]).build()
        assert df.rows() == 3
        assert df.get("x", 0) == 1

    def test_builder_with_nulls(self) -> None:
        df = DataFrameBuilder().add_column("a", [1, None, 3]).build()
        assert df.get("a", 0) == 1
        assert df.get("a", 1) is None
        assert df.get("a", 2) == 3


# ── to_list ───────────────────────────────────────────────────────


class TestDataFrameToList:
    def test_to_list(self) -> None:
        df: DataFrame[int] = DataFrame()
        df.add_column("name", ["Alice", "Bob"])
        df.add_column("age", [25, 30])
        rows = df.to_list()
        assert len(rows) == 2
        assert rows[0] == {"name": "Alice", "age": 25}
        assert rows[1] == {"name": "Bob", "age": 30}

    def test_to_list_empty(self) -> None:
        df: DataFrame[int] = DataFrame()
        assert df.to_list() == []


# ── Nullable values ───────────────────────────────────────────────


class TestDataFrameNullable:
    def test_null_values(self) -> None:
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, None, 3])
        assert df.get("a", 0) == 1
        assert df.get("a", 1) is None
        assert df.get("a", 2) == 3


# ── Edge cases ────────────────────────────────────────────────────


class TestDataFrameEdgeCases:
    def test_column_padding(self) -> None:
        """Adding shorter column after longer one should pad with None."""
        df: DataFrame[int] = DataFrame()
        df.add_column("a", [1, 2, 3])
        df.add_column("b", [4])
        # Column b should be padded
        assert df.get("b", 0) == 4
        assert df.get("b", 1) is None
        assert df.get("b", 2) is None
