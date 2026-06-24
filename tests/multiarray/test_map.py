"""Tests for map extension functions."""

from __future__ import annotations

import numpy as np

from ospf_python.multiarray.map import group_by_to_array, map_to_matrix

# ── map_to_matrix ─────────────────────────────────────────────────


class TestMapToMatrix:
    def test_basic_conversion(self) -> None:
        d = {
            ("a", "x"): 1,
            ("a", "y"): 2,
            ("b", "x"): 3,
            ("b", "y"): 4,
        }
        matrix = map_to_matrix(d, rows=["a", "b"], cols=["x", "y"])
        assert matrix.shape == (2, 2)
        assert matrix[0, 0] == 1
        assert matrix[0, 1] == 2
        assert matrix[1, 0] == 3
        assert matrix[1, 1] == 4

    def test_missing_keys_use_default(self) -> None:
        d = {("a", "x"): 1}
        matrix = map_to_matrix(d, rows=["a", "b"], cols=["x", "y"], default=0)
        assert matrix[0, 0] == 1
        assert matrix[0, 1] == 0
        assert matrix[1, 0] == 0
        assert matrix[1, 1] == 0

    def test_custom_default(self) -> None:
        d: dict[tuple[str, str], int] = {}
        matrix = map_to_matrix(d, rows=["a"], cols=["b"], default=-1)
        assert matrix[0, 0] == -1

    def test_single_element(self) -> None:
        d = {("a", "x"): 42}
        matrix = map_to_matrix(d, rows=["a"], cols=["x"])
        assert matrix[0, 0] == 42

    def test_non_tuple_keys_ignored(self) -> None:
        d = {
            ("a", "x"): 1,
            "invalid": 2,
            ("a", "y"): 3,
        }
        matrix = map_to_matrix(d, rows=["a"], cols=["x", "y"], default=0)
        assert matrix[0, 0] == 1
        assert matrix[0, 1] == 3


# ── group_by_to_array ─────────────────────────────────────────────


class TestGroupByToArray:
    def test_basic_grouping(self) -> None:
        items = [("a", 1), ("b", 2), ("a", 3), ("b", 4)]
        groups = group_by_to_array(items, key_func=lambda x: x[0])
        assert "a" in groups
        assert "b" in groups
        assert len(groups["a"]) == 2
        assert len(groups["b"]) == 2

    def test_single_group(self) -> None:
        items = [1, 2, 3]
        groups = group_by_to_array(items, key_func=lambda x: "all")
        assert len(groups) == 1
        assert len(groups["all"]) == 3

    def test_empty_input(self) -> None:
        groups = group_by_to_array([], key_func=lambda x: x)
        assert groups == {}

    def test_values_are_numpy_arrays(self) -> None:
        items = [("a", 1), ("a", 2)]
        groups = group_by_to_array(items, key_func=lambda x: x[0])
        assert isinstance(groups["a"], np.ndarray)
