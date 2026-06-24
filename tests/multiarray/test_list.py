"""Tests for list extension functions (flatten, transpose, chunk)."""

from __future__ import annotations

from ospf_python.multiarray.list import chunk_list, flatten_list, transpose_list

# ── flatten_list ──────────────────────────────────────────────────


class TestFlattenList:
    def test_flatten_simple(self) -> None:
        nested = [[1, 2], [3, 4]]
        assert flatten_list(nested) == [1, 2, 3, 4]

    def test_flatten_deep(self) -> None:
        nested = [1, [2, [3, [4, 5]]]]
        assert flatten_list(nested) == [1, 2, 3, 4, 5]

    def test_flatten_empty(self) -> None:
        assert flatten_list([]) == []

    def test_flatten_already_flat(self) -> None:
        lst = [1, 2, 3]
        assert flatten_list(lst) == [1, 2, 3]

    def test_flatten_mixed(self) -> None:
        nested = [[1, 2], 3, [4, [5, 6]]]
        assert flatten_list(nested) == [1, 2, 3, 4, 5, 6]

    def test_flatten_3d(self) -> None:
        cube = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
        assert flatten_list(cube) == [1, 2, 3, 4, 5, 6, 7, 8]


# ── transpose_list ────────────────────────────────────────────────


class TestTransposeList:
    def test_transpose_2x3(self) -> None:
        matrix = [[1, 2, 3], [4, 5, 6]]
        transposed = transpose_list(matrix)
        assert transposed == [[1, 4], [2, 5], [3, 6]]

    def test_transpose_3x2(self) -> None:
        matrix = [[1, 4], [2, 5], [3, 6]]
        transposed = transpose_list(matrix)
        assert transposed == [[1, 2, 3], [4, 5, 6]]

    def test_transpose_empty(self) -> None:
        assert transpose_list([]) == []

    def test_transpose_single_row(self) -> None:
        matrix = [[1, 2, 3]]
        assert transpose_list(matrix) == [[1], [2], [3]]

    def test_transpose_single_col(self) -> None:
        matrix = [[1], [2], [3]]
        assert transpose_list(matrix) == [[1, 2, 3]]

    def test_transpose_square(self) -> None:
        matrix = [[1, 2], [3, 4]]
        assert transpose_list(matrix) == [[1, 3], [2, 4]]

    def test_transpose_1x1(self) -> None:
        matrix = [[42]]
        assert transpose_list(matrix) == [[42]]


# ── chunk_list ────────────────────────────────────────────────────


class TestChunkList:
    def test_chunk_even(self) -> None:
        lst = [1, 2, 3, 4, 5, 6]
        assert chunk_list(lst, size=2) == [[1, 2], [3, 4], [5, 6]]

    def test_chunk_uneven(self) -> None:
        lst = [1, 2, 3, 4, 5]
        result = chunk_list(lst, size=2)
        assert result[0] == [1, 2]
        assert result[1] == [3, 4]
        assert result[2] == [5]

    def test_chunk_size_one(self) -> None:
        lst = [1, 2, 3]
        assert chunk_list(lst, size=1) == [[1], [2], [3]]

    def test_chunk_size_larger_than_list(self) -> None:
        lst = [1, 2]
        result = chunk_list(lst, size=5)
        assert len(result) == 1
        assert list(result[0]) == [1, 2]

    def test_chunk_empty(self) -> None:
        assert chunk_list([], size=3) == []

    def test_chunk_size_zero_returns_empty(self) -> None:
        assert chunk_list([1, 2, 3], size=0) == []

    def test_chunk_size_negative_returns_empty(self) -> None:
        assert chunk_list([1, 2, 3], size=-1) == []
