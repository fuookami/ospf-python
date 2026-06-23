"""Tests for ospf_python.math.combinatorics module."""

import pytest

from ospf_python.math.combinatorics import (
    catalan_number,
    combination,
    combinations_with_replacement,
    factorial,
    permutation,
    stirling_second,
)


class TestFactorial:
    """Tests for factorial."""

    def test_factorial_zero(self) -> None:
        """Test 0! = 1."""
        assert factorial(0) == 1

    def test_factorial_positive(self) -> None:
        """Test factorial of positive numbers."""
        assert factorial(1) == 1
        assert factorial(5) == 120
        assert factorial(10) == 3628800

    def test_factorial_negative_raises(self) -> None:
        """Test factorial of negative raises."""
        with pytest.raises(ValueError):
            factorial(-1)


class TestPermutation:
    """Tests for permutation."""

    def test_permutation_basic(self) -> None:
        """Test basic permutation."""
        assert permutation(5, 3) == 60
        assert permutation(4, 2) == 12

    def test_permutation_zero(self) -> None:
        """Test permutation with k=0."""
        assert permutation(5, 0) == 1

    def test_permutation_equal(self) -> None:
        """Test permutation with k=n."""
        assert permutation(5, 5) == 120

    def test_permutation_invalid_raises(self) -> None:
        """Test invalid permutation raises."""
        with pytest.raises(ValueError):
            permutation(3, 5)


class TestCombination:
    """Tests for combination."""

    def test_combination_basic(self) -> None:
        """Test basic combination."""
        assert combination(5, 3) == 10
        assert combination(4, 2) == 6

    def test_combination_zero(self) -> None:
        """Test combination with k=0."""
        assert combination(5, 0) == 1

    def test_combination_equal(self) -> None:
        """Test combination with k=n."""
        assert combination(5, 5) == 1

    def test_combination_invalid_raises(self) -> None:
        """Test invalid combination raises."""
        with pytest.raises(ValueError):
            combination(3, 5)


class TestCombinationsWithReplacement:
    """Tests for combinations_with_replacement."""

    def test_basic(self) -> None:
        """Test basic combinations with replacement."""
        assert combinations_with_replacement(3, 2) == 6


class TestCatalanNumber:
    """Tests for Catalan number."""

    def test_catalan_basic(self) -> None:
        """Test Catalan numbers."""
        assert catalan_number(0) == 1
        assert catalan_number(1) == 1
        assert catalan_number(2) == 2
        assert catalan_number(3) == 5
        assert catalan_number(4) == 14

    def test_catalan_negative_raises(self) -> None:
        """Test negative raises."""
        with pytest.raises(ValueError):
            catalan_number(-1)


class TestStirlingSecond:
    """Tests for Stirling number of the second kind."""

    def test_stirling_basic(self) -> None:
        """Test Stirling numbers."""
        assert stirling_second(0, 0) == 1
        assert stirling_second(3, 2) == 3
        assert stirling_second(4, 2) == 7
