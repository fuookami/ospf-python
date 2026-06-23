"""Tests for ospf_python.multiarray.array module."""

import numpy as np

from ospf_python.multiarray.array import MultiArray, einsum


class TestMultiArrayCreation:
    """Tests for MultiArray creation."""

    def test_from_list_1d(self) -> None:
        """Test creating 1D array from list."""
        arr = MultiArray.from_list([1, 2, 3])
        assert arr.shape == (3,)
        assert arr.ndim == 1
        assert arr.size == 3

    def test_from_list_2d(self) -> None:
        """Test creating 2D array from list."""
        arr = MultiArray.from_list([[1, 2], [3, 4]])
        assert arr.shape == (2, 2)
        assert arr.ndim == 2
        assert arr.size == 4

    def test_zeros(self) -> None:
        """Test creating array of zeros."""
        arr = MultiArray.zeros((2, 3))
        assert arr.shape == (2, 3)
        assert arr.size == 6
        np.testing.assert_array_equal(arr.data, np.zeros((2, 3)))

    def test_ones(self) -> None:
        """Test creating array of ones."""
        arr = MultiArray.ones((2, 2))
        assert arr.shape == (2, 2)
        np.testing.assert_array_equal(arr.data, np.ones((2, 2)))

    def test_full(self) -> None:
        """Test creating array filled with value."""
        arr = MultiArray.full((2, 2), 5)
        np.testing.assert_array_equal(arr.data, np.full((2, 2), 5))

    def test_arange(self) -> None:
        """Test creating array with range."""
        arr = MultiArray.arange(5)
        assert arr.shape == (5,)
        np.testing.assert_array_equal(arr.data, np.arange(5))

    def test_eye(self) -> None:
        """Test creating identity matrix."""
        arr = MultiArray.eye(3)
        assert arr.shape == (3, 3)
        np.testing.assert_array_equal(arr.data, np.eye(3))


class TestMultiArrayProperties:
    """Tests for MultiArray properties."""

    def test_shape(self) -> None:
        """Test shape property."""
        arr = MultiArray.from_list([[1, 2, 3], [4, 5, 6]])
        assert arr.shape == (2, 3)

    def test_ndim(self) -> None:
        """Test ndim property."""
        arr = MultiArray.from_list([[1, 2], [3, 4]])
        assert arr.ndim == 2

    def test_size(self) -> None:
        """Test size property."""
        arr = MultiArray.from_list([[1, 2], [3, 4]])
        assert arr.size == 4

    def test_dtype(self) -> None:
        """Test dtype property."""
        arr = MultiArray.from_list([1, 2, 3])
        assert arr.dtype == np.int64 or arr.dtype == np.int32


class TestMultiArrayIndexing:
    """Tests for MultiArray indexing and slicing."""

    def test_getitem_scalar(self) -> None:
        """Test getting scalar value."""
        arr = MultiArray.from_list([1, 2, 3])
        assert arr[0] == 1
        assert arr[1] == 2
        assert arr[2] == 3

    def test_getitem_slice(self) -> None:
        """Test getting slice."""
        arr = MultiArray.from_list([1, 2, 3, 4, 5])
        sliced = arr[1:3]
        assert isinstance(sliced, MultiArray)
        np.testing.assert_array_equal(sliced.data, np.array([2, 3]))

    def test_getitem_2d(self) -> None:
        """Test 2D indexing."""
        arr = MultiArray.from_list([[1, 2], [3, 4]])
        assert arr[0, 0] == 1
        assert arr[0, 1] == 2
        assert arr[1, 0] == 3
        assert arr[1, 1] == 4

    def test_setitem(self) -> None:
        """Test setting value."""
        arr = MultiArray.from_list([1, 2, 3])
        arr[0] = 10
        assert arr[0] == 10

    def test_len(self) -> None:
        """Test length."""
        arr = MultiArray.from_list([1, 2, 3])
        assert len(arr) == 3


class TestMultiArrayArithmetic:
    """Tests for MultiArray arithmetic operations."""

    def test_add_arrays(self) -> None:
        """Test adding two arrays."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([4, 5, 6])
        result = a + b
        np.testing.assert_array_equal(result.data, np.array([5, 7, 9]))

    def test_add_scalar(self) -> None:
        """Test adding scalar."""
        a = MultiArray.from_list([1, 2, 3])
        result = a + 10
        np.testing.assert_array_equal(result.data, np.array([11, 12, 13]))

    def test_radd_scalar(self) -> None:
        """Test reverse add scalar."""
        a = MultiArray.from_list([1, 2, 3])
        result = 10 + a
        np.testing.assert_array_equal(result.data, np.array([11, 12, 13]))

    def test_sub_arrays(self) -> None:
        """Test subtracting two arrays."""
        a = MultiArray.from_list([4, 5, 6])
        b = MultiArray.from_list([1, 2, 3])
        result = a - b
        np.testing.assert_array_equal(result.data, np.array([3, 3, 3]))

    def test_mul_arrays(self) -> None:
        """Test multiplying two arrays."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([4, 5, 6])
        result = a * b
        np.testing.assert_array_equal(result.data, np.array([4, 10, 18]))

    def test_div_arrays(self) -> None:
        """Test dividing two arrays."""
        a = MultiArray.from_list([4.0, 6.0, 8.0])
        b = MultiArray.from_list([2.0, 3.0, 4.0])
        result = a / b
        np.testing.assert_array_equal(result.data, np.array([2.0, 2.0, 2.0]))

    def test_neg(self) -> None:
        """Test negation."""
        a = MultiArray.from_list([1, -2, 3])
        result = -a
        np.testing.assert_array_equal(result.data, np.array([-1, 2, -3]))


class TestMultiArrayComparison:
    """Tests for MultiArray comparison operations."""

    def test_eq(self) -> None:
        """Test equality."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([1, 2, 4])
        result = a == b
        np.testing.assert_array_equal(result.data, np.array([True, True, False]))

    def test_ne(self) -> None:
        """Test inequality."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([1, 2, 4])
        result = a != b
        np.testing.assert_array_equal(result.data, np.array([False, False, True]))

    def test_lt(self) -> None:
        """Test less than."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([2, 2, 2])
        result = a < b
        np.testing.assert_array_equal(result.data, np.array([True, False, False]))

    def test_le(self) -> None:
        """Test less than or equal."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([2, 2, 2])
        result = a <= b
        np.testing.assert_array_equal(result.data, np.array([True, True, False]))

    def test_gt(self) -> None:
        """Test greater than."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([2, 2, 2])
        result = a > b
        np.testing.assert_array_equal(result.data, np.array([False, False, True]))

    def test_ge(self) -> None:
        """Test greater than or equal."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([2, 2, 2])
        result = a >= b
        np.testing.assert_array_equal(result.data, np.array([False, True, True]))


class TestMultiArrayReduction:
    """Tests for MultiArray reduction operations."""

    def test_sum_all(self) -> None:
        """Test sum of all elements."""
        arr = MultiArray.from_list([[1, 2], [3, 4]])
        assert arr.sum() == 10

    def test_sum_axis(self) -> None:
        """Test sum along axis."""
        arr = MultiArray.from_list([[1, 2], [3, 4]])
        result = arr.sum(axis=0)
        assert isinstance(result, MultiArray)
        np.testing.assert_array_equal(result.data, np.array([4, 6]))

    def test_mean_all(self) -> None:
        """Test mean of all elements."""
        arr = MultiArray.from_list([[1, 2], [3, 4]])
        assert arr.mean() == 2.5

    def test_mean_axis(self) -> None:
        """Test mean along axis."""
        arr = MultiArray.from_list([[1, 2], [3, 4]])
        result = arr.mean(axis=1)
        assert isinstance(result, MultiArray)
        np.testing.assert_array_equal(result.data, np.array([1.5, 3.5]))

    def test_min_all(self) -> None:
        """Test min of all elements."""
        arr = MultiArray.from_list([[3, 1], [4, 2]])
        assert arr.min() == 1

    def test_max_all(self) -> None:
        """Test max of all elements."""
        arr = MultiArray.from_list([[3, 1], [4, 2]])
        assert arr.max() == 4


class TestMultiArrayTransform:
    """Tests for MultiArray transform operations."""

    def test_reshape(self) -> None:
        """Test reshape."""
        arr = MultiArray.from_list([1, 2, 3, 4, 5, 6])
        reshaped = arr.reshape((2, 3))
        assert reshaped.shape == (2, 3)
        np.testing.assert_array_equal(reshaped.data, np.array([[1, 2, 3], [4, 5, 6]]))

    def test_transpose(self) -> None:
        """Test transpose."""
        arr = MultiArray.from_list([[1, 2, 3], [4, 5, 6]])
        transposed = arr.transpose()
        assert transposed.shape == (3, 2)
        np.testing.assert_array_equal(
            transposed.data, np.array([[1, 4], [2, 5], [3, 6]])
        )

    def test_flatten(self) -> None:
        """Test flatten."""
        arr = MultiArray.from_list([[1, 2], [3, 4]])
        flat = arr.flatten()
        assert flat.shape == (4,)
        np.testing.assert_array_equal(flat.data, np.array([1, 2, 3, 4]))

    def test_copy(self) -> None:
        """Test copy."""
        arr = MultiArray.from_list([1, 2, 3])
        copied = arr.copy()
        copied[0] = 10
        assert arr[0] == 1  # Original unchanged
        assert copied[0] == 10


class TestMultiArrayDot:
    """Tests for MultiArray dot product and matmul."""

    def test_dot(self) -> None:
        """Test dot product."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([4, 5, 6])
        result = a.dot(b)
        assert result == 32  # 1*4 + 2*5 + 3*6

    def test_matmul(self) -> None:
        """Test matrix multiplication."""
        a = MultiArray.from_list([[1, 2], [3, 4]])
        b = MultiArray.from_list([[5, 6], [7, 8]])
        result = a.matmul(b)
        assert isinstance(result, MultiArray)
        np.testing.assert_array_equal(result.data, np.array([[19, 22], [43, 50]]))


class TestEinsum:
    """Tests for einsum function."""

    def test_matrix_multiply(self) -> None:
        """Test matrix multiplication via einsum."""
        a = MultiArray.from_list([[1, 2], [3, 4]])
        b = MultiArray.from_list([[5, 6], [7, 8]])
        result = einsum("ij,jk->ik", a, b)
        assert isinstance(result, MultiArray)
        np.testing.assert_array_equal(result.data, np.array([[19, 22], [43, 50]]))

    def test_trace(self) -> None:
        """Test trace via einsum."""
        a = MultiArray.from_list([[1, 2], [3, 4]])
        result = einsum("ii->", a)
        assert result == 5  # 1 + 4

    def test_element_wise_multiply(self) -> None:
        """Test element-wise multiply via einsum."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([4, 5, 6])
        result = einsum("i,i->i", a, b)
        np.testing.assert_array_equal(result.data, np.array([4, 10, 18]))

    def test_sum(self) -> None:
        """Test sum via einsum."""
        a = MultiArray.from_list([1, 2, 3])
        result = einsum("i->", a)
        assert result == 6

    def test_outer_product(self) -> None:
        """Test outer product via einsum."""
        a = MultiArray.from_list([1, 2, 3])
        b = MultiArray.from_list([4, 5, 6])
        result = einsum("i,j->ij", a, b)
        assert result.shape == (3, 3)
        np.testing.assert_array_equal(
            result.data, np.array([[4, 5, 6], [8, 10, 12], [12, 15, 18]])
        )


class TestMultiArrayRepr:
    """Tests for MultiArray string representation."""

    def test_repr(self) -> None:
        """Test repr."""
        arr = MultiArray.from_list([1, 2, 3])
        assert "MultiArray" in repr(arr)

    def test_str(self) -> None:
        """Test str."""
        arr = MultiArray.from_list([1, 2, 3])
        assert "[1 2 3]" in str(arr)
