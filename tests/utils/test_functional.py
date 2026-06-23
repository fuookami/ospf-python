"""Tests for ospf_python.utils.functional module."""

from ospf_python.utils.functional import (
    compose,
    constant,
    curry,
    flip,
    identity,
    ignore,
    tap,
)


class TestIdentity:
    """Tests for identity function."""

    def test_identity_returns_value(self) -> None:
        """Test identity returns the input value."""
        assert identity(42) == 42
        assert identity("hello") == "hello"
        assert identity(None) is None
        assert identity([1, 2, 3]) == [1, 2, 3]

    def test_identity_preserves_reference(self) -> None:
        """Test identity preserves object reference."""
        obj = {"key": "value"}
        assert identity(obj) is obj


class TestConstant:
    """Tests for constant function."""

    def test_constant_returns_function(self) -> None:
        """Test constant returns a function."""
        fn = constant(42)
        assert callable(fn)

    def test_constant_function_returns_value(self) -> None:
        """Test constant function returns the value."""
        fn = constant(42)
        assert fn() == 42
        assert fn() == 42  # Can be called multiple times

    def test_constant_with_none(self) -> None:
        """Test constant with None value."""
        fn = constant(None)
        assert fn() is None


class TestCompose:
    """Tests for compose function."""

    def test_compose_two_functions(self) -> None:
        """Test composing two functions."""
        add_one = lambda x: x + 1
        double = lambda x: x * 2
        composed = compose(double, add_one)
        assert composed(3) == 8  # (3 + 1) * 2

    def test_compose_multiple_functions(self) -> None:
        """Test composing multiple functions."""
        add_one = lambda x: x + 1
        double = lambda x: x * 2
        square = lambda x: x**2
        composed = compose(square, double, add_one)
        assert composed(2) == 36  # ((2 + 1) * 2) ^ 2

    def test_compose_single_function(self) -> None:
        """Test composing a single function."""
        add_one = lambda x: x + 1
        composed = compose(add_one)
        assert composed(3) == 4

    def test_compose_identity(self) -> None:
        """Test composing with identity."""
        add_one = lambda x: x + 1
        composed = compose(identity, add_one)
        assert composed(3) == 4


class TestCurry:
    """Tests for curry function."""

    def test_curry_add(self) -> None:
        """Test currying an add function."""
        add = lambda a, b: a + b
        curried = curry(add)
        assert curried(1)(2) == 3

    def test_curry_partial_application(self) -> None:
        """Test partial application with curry."""
        multiply = lambda a, b: a * b
        curried = curry(multiply)
        double = curried(2)
        assert double(5) == 10
        assert double(10) == 20


class TestFlip:
    """Tests for flip function."""

    def test_flip_subtract(self) -> None:
        """Test flipping a subtract function."""
        subtract = lambda a, b: a - b
        flipped = flip(subtract)
        assert subtract(5, 3) == 2
        assert flipped(5, 3) == -2

    def test_flip_divide(self) -> None:
        """Test flipping a divide function."""
        divide = lambda a, b: a / b
        flipped = flip(divide)
        assert divide(10, 2) == 5.0
        assert flipped(10, 2) == 0.2


class TestTap:
    """Tests for tap function."""

    def test_tap_calls_side_effect(self) -> None:
        """Test tap calls the side effect function."""
        called_with = []

        def side_effect(value):
            called_with.append(value)

        tapper = tap(side_effect)
        result = tapper(42)
        assert called_with == [42]
        assert result == 42

    def test_tap_returns_original_value(self) -> None:
        """Test tap returns the original value."""
        tapper = tap(lambda x: None)
        assert tapper(42) == 42
        assert tapper("hello") == "hello"

    def test_tap_ignores_side_effect_return(self) -> None:
        """Test tap ignores the return value of side effect."""
        tapper = tap(lambda x: "ignored")
        assert tapper(42) == 42


class TestIgnore:
    """Tests for ignore function."""

    def test_ignore_returns_none(self) -> None:
        """Test ignore returns None."""
        assert ignore(42) is None
        assert ignore("hello") is None
        assert ignore([1, 2, 3]) is None

    def test_ignore_accepts_any_value(self) -> None:
        """Test ignore accepts any value."""
        ignore(None)
        ignore(0)
        ignore("")
        ignore([])
