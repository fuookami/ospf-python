"""Either 类型测试。

测试 Either、Left、Right 的 map、fold 等操作。
"""

from __future__ import annotations

from ospf_python.utils.functional import Either, Left, Right


class TestLeft:
    """Left 左值测试。"""

    def test_left_is_either(self) -> None:
        assert isinstance(Left("error"), Either)

    def test_left_value(self) -> None:
        assert Left("err").value == "err"

    def test_left_is_left(self) -> None:
        assert Left(1).is_left() is True

    def test_left_is_not_right(self) -> None:
        assert Left(1).is_right() is False


class TestRight:
    """Right 右值测试。"""

    def test_right_is_either(self) -> None:
        assert isinstance(Right(42), Either)

    def test_right_value(self) -> None:
        assert Right(42).value == 42

    def test_right_is_right(self) -> None:
        assert Right(1).is_right() is True

    def test_right_is_not_left(self) -> None:
        assert Right(1).is_left() is False


class TestEitherMap:
    """Either 的 map 操作测试。"""

    def test_map_on_right(self) -> None:
        result = Right(5).map(lambda x: x * 2)
        assert isinstance(result, Right)
        assert result.value == 10

    def test_map_on_left(self) -> None:
        result = Left("err").map(lambda x: x * 2)
        assert isinstance(result, Left)
        assert result.value == "err"


class TestEitherFold:
    """Either 的 fold 操作测试。"""

    def test_fold_on_right(self) -> None:
        result = Right(10).fold(
            lambda e: f"error: {e}",
            lambda v: f"value: {v}",
        )
        assert result == "value: 10"

    def test_fold_on_left(self) -> None:
        result = Left("oops").fold(
            lambda e: f"error: {e}",
            lambda v: f"value: {v}",
        )
        assert result == "error: oops"
