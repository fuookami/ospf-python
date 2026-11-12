"""精确数值域的薄门面 / Thin facade for the Rust exact-number domain."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Context, Decimal, Inexact, Overflow, Rounded, Underflow, getcontext
from fractions import Fraction
from typing import TYPE_CHECKING

from ospf_python import _native
from ospf_python._binding.result import BindingResult, FailureContext, invalid, invoke
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import ExErr
from ospf_python.utils.functional.result import Failed, Ok

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = ["Rational", "RationalArray"]


@dataclass(frozen=True, slots=True, eq=False)
class Rational:
    """不可变的 Rust 任意精度有理数 / Immutable Rust arbitrary-precision rational.

    使用工厂创建；Python 不缓存分子、分母或运算结果。
    Use factories; Python does not cache components or arithmetic results.
    """

    _handle: _native.Rational

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Rational):
            return NotImplemented
        return self._handle.compare(other._handle) == 0

    def __hash__(self) -> int:
        return hash(self.as_integer_ratio())

    @classmethod
    def create(cls, *, numerator: int, denominator: int = 1) -> BindingResult[Rational]:
        """创建并规范化精确分数 / Create and normalize an exact fraction.

        Args:
            numerator: 任意精度整数分子，不接受 bool / Arbitrary-precision numerator, not bool.
            denominator: 非零整数分母，不接受 bool / Nonzero integer denominator, not bool.

        Returns:
            Rust 有理数或 Failed / Rust rational or Failed.
        """
        if (
            not isinstance(numerator, int)
            or isinstance(numerator, bool)
            or not isinstance(denominator, int)
            or isinstance(denominator, bool)
        ):
            return invalid(
                "分子和分母必须为整数 / Numerator and denominator must be integers"
            )
        return invoke(
            lambda: _native._create_rational(
                numerator=numerator, denominator=denominator
            )
        ).map(cls)

    @classmethod
    def from_value(cls, value: int | Fraction | Decimal) -> BindingResult[Rational]:
        """无损接入 Python 精确数值 / Import an exact Python number losslessly.

        Args:
            value: int、Fraction 或有限 Decimal；float 必须走显式入口 / int, Fraction or finite Decimal; floats require the explicit factory.

        Returns:
            精确有理数或 Failed / Exact rational or Failed.
        """
        if isinstance(value, int) and not isinstance(value, bool):
            return cls.create(numerator=value)
        if not isinstance(value, Fraction | Decimal):
            return invalid("需要精确数值域 / An exact numeric domain is required")
        try:
            numerator, denominator = value.as_integer_ratio()
        except (ArithmeticError, ValueError, TypeError) as error:
            return invalid(
                f"精确数值转换失败 / Exact numeric conversion failed: {error}"
            )
        return cls.create(numerator=numerator, denominator=denominator)

    @classmethod
    def from_float(cls, value: float) -> BindingResult[Rational]:
        """显式接入 IEEE 浮点值，不猜测十进制意图 / Import the exact IEEE value without guessing decimal intent.

        Args:
            value: 有限 Python float / Finite Python float.

        Returns:
            该二进制值的精确分数或 Failed / Exact binary-value fraction or Failed.
        """
        if not isinstance(value, float):
            return invalid("需要 float 值 / A float value is required")
        try:
            numerator, denominator = value.as_integer_ratio()
        except (ArithmeticError, ValueError) as error:
            return invalid(f"浮点值无效 / Invalid floating value: {error}")
        return cls.create(numerator=numerator, denominator=denominator)

    @classmethod
    def from_json(cls, text: str) -> BindingResult[Rational]:
        """恢复版本化精确快照 / Restore a versioned exact snapshot.

        Args:
            text: JSON 快照，整数用十进制字符串编码 / JSON snapshot with decimal-string integers.

        Returns:
            规范化有理数或 Failed / Normalized rational or Failed.
        """
        return invoke(lambda: _native._rational_from_json(text)).map(cls)

    def as_integer_ratio(self) -> tuple[int, int]:
        """返回分子和正分母快照 / Return a numerator and positive-denominator snapshot."""
        return self._handle.as_integer_ratio()

    def to_json(self) -> str:
        """输出不经浮点的版本化快照 / Export a versioned snapshot without floating conversion."""
        return self._handle.to_json()

    def to_float(self, *, exact: bool = True) -> BindingResult[float]:
        """显式检查 Float64 精度边界 / Check the Float64 precision boundary explicitly.

        Args:
            exact: 默认拒绝任何损失，False 显式允许舍入/下溢 / Reject all loss by default; False explicitly permits rounding/underflow.

        Returns:
            有限 float 或 DATA_LOSS/OVERFLOW 失败 / Finite float or DATA_LOSS/OVERFLOW failure.
        """
        if not isinstance(exact, bool):
            return invalid("exact 必须为 bool / exact must be bool")
        return invoke(lambda: self._handle.to_float(exact=exact))

    def to_decimal(
        self, *, context: Context | None = None, exact: bool = True
    ) -> BindingResult[Decimal]:
        """按指定 context 导出，不隐式接受数值损失。 / Export in a context without implicitly accepting numeric loss.

        Args:
            context: 输出上下文，None 使用当前上下文；flags 原位更新。 / Output context, or the current context; flags update in place.
            exact: 默认拒绝舍入损失；False 显式允许有限结果舍入。 / Reject rounding loss by default; False explicitly permits finite rounded results.

        Returns:
            Decimal 或保留外部异常的 Failed，不修改原生分数。 / Decimal or Failed retaining external exceptions, without changing the native fraction.
        """
        if (context is not None and not issubclass(type(context), Context)) or type(
            exact
        ) is not bool:
            return invalid(
                "需要 Decimal Context 和 bool / Decimal Context and bool required"
            )

        def failure(
            code: ErrorCode, error: Exception | None = None
        ) -> BindingResult[Decimal]:
            return Failed(
                ExErr(
                    _code=code,
                    _message="Decimal 导出失败 / Decimal export failed",
                    value=FailureContext(
                        source="python-decimal",
                        category=code.name,
                        rust_code=None,
                        error_class="BOUNDARY",
                        callback_exception=error,
                    ),
                )
            )

        numerator, denominator = self.as_integer_ratio()
        try:
            selected = getcontext() if context is None else context
            # 仅在输出边界调用 Python 的舍入协议；精确算术与单位换算仍在 Rust。 / Invoke Python rounding only at export; exact arithmetic and unit conversion remain in Rust.
            exported = selected.divide(Decimal(numerator), Decimal(denominator))
        except Exception as error:
            if issubclass(type(error), Overflow):
                code = ErrorCode.OVERFLOW
            elif issubclass(type(error), Underflow):
                code = ErrorCode.UNDERFLOW
            elif issubclass(type(error), (Inexact, Rounded)):
                code = ErrorCode.DATA_LOSS
            else:
                code = ErrorCode.APPLICATION_ERROR
            return failure(code, error)
        if type(exported) is not Decimal:
            return invalid(
                "Decimal context 必须返回内置 Decimal / Decimal context must return builtin Decimal"
            )
        if not exported.is_finite():
            return failure(ErrorCode.OVERFLOW)
        if not exact:
            return Ok(exported)
        return Rational.from_value(exported).flat_map(
            lambda restored: self.compare(restored).flat_map(
                lambda ordering: (
                    Ok(exported) if ordering == 0 else failure(ErrorCode.DATA_LOSS)
                )
            )
        )

    def _binary(
        self,
        *,
        other: Rational,
        operation: Callable[[_native.Rational], _native.Rational],
    ) -> BindingResult[Rational]:
        if not isinstance(other, Rational):
            return invalid(
                "操作数必须属于有理数域 / Operand must belong to the rational domain"
            )
        return invoke(lambda: (operation(other._handle), None)).map(Rational)

    def add(self, other: Rational) -> BindingResult[Rational]:
        """精确相加 / Add exactly.

        Args:
            other: 右操作数 / Right operand.

        Returns:
            新的 Rust 值或 Failed / New Rust value or Failed.
        """
        return self._binary(other=other, operation=self._handle.add)

    def subtract(self, other: Rational) -> BindingResult[Rational]:
        """精确相减 / Subtract exactly.

        Args:
            other: 右操作数 / Right operand.

        Returns:
            新的 Rust 值或 Failed / New Rust value or Failed.
        """
        return self._binary(other=other, operation=self._handle.subtract)

    def multiply(self, other: Rational) -> BindingResult[Rational]:
        """精确相乘 / Multiply exactly.

        Args:
            other: 右操作数 / Right operand.

        Returns:
            新的 Rust 值或 Failed / New Rust value or Failed.
        """
        return self._binary(other=other, operation=self._handle.multiply)

    def divide(self, other: Rational) -> BindingResult[Rational]:
        """精确相除，零除数返回 Failed / Divide exactly; zero divisor returns Failed.

        Args:
            other: 右操作数 / Right operand.

        Returns:
            新的 Rust 值或 Failed / New Rust value or Failed.
        """
        if not isinstance(other, Rational):
            return invalid(
                "操作数必须属于有理数域 / Operand must belong to the rational domain"
            )
        return invoke(lambda: self._handle.divide(other._handle)).map(Rational)

    def reciprocal(self) -> BindingResult[Rational]:
        """返回精确倒数，零返回 Failed / Return the exact reciprocal, or Failed for zero."""
        return invoke(self._handle.reciprocal).map(Rational)

    def negated(self) -> Rational:
        """返回 Rust 计算的相反数 / Return the Rust-computed additive inverse."""
        return Rational(self._handle.negated())

    def compare(self, other: Rational) -> BindingResult[int]:
        """精确全序比较 / Compare in the exact total order.

        Args:
            other: 右操作数 / Right operand.

        Returns:
            -1/0/1 或 Failed / -1/0/1 or Failed.
        """
        if not isinstance(other, Rational):
            return invalid(
                "操作数必须属于有理数域 / Operand must belong to the rational domain"
            )
        return invoke(lambda: (self._handle.compare(other._handle), None))


@dataclass(frozen=True, slots=True, eq=False)
class RationalArray:
    """Rust 持有的一维精确值批次 / Rust-owned one-dimensional exact batch.

    批量归约不创建逐元素 Python 有理数；不是 NumPy view 或通用多维数组。
    Reductions avoid per-element Python rationals; this is not a NumPy view or general multiarray.
    """

    _handle: _native.RationalArray

    @classmethod
    def create(cls, inputs: list[tuple[int, int]]) -> BindingResult[RationalArray]:
        """原子创建精确值批次 / Create an exact batch atomically.

        Args:
            inputs: 分子/分母对的 list；不接受 bool 或浮点 / List of numerator/denominator pairs, not bool or floats.

        Returns:
            唯一 Rust 批次或 Failed，不返回部分结果 / One Rust batch or Failed, never partial output.
        """
        if not isinstance(inputs, list):
            return invalid("批量输入必须为 list / Batch input must be a list")
        owned: list[tuple[int, int]] = []
        for index, pair in enumerate(inputs):
            if not isinstance(pair, tuple) or len(pair) != 2:
                return invalid(
                    f"需要整数对 / Integer pair required; 索引 / index: {index}"
                )
            numerator, denominator = pair
            if (
                not isinstance(numerator, int)
                or isinstance(numerator, bool)
                or not isinstance(denominator, int)
                or isinstance(denominator, bool)
            ):
                return invalid(
                    f"需要整数域 / Integer domain required; 索引 / index: {index}"
                )
            owned.append((numerator, denominator))
        return invoke(lambda: _native._create_rational_array(owned)).map(cls)

    def __len__(self) -> int:
        return len(self._handle)

    def as_integer_ratios(self) -> list[tuple[int, int]]:
        """返回独立整数对快照 / Return an independent integer-pair snapshot."""
        return self._handle.as_integer_ratios()

    def at(self, index: int) -> BindingResult[Rational]:
        """按零基索引取独立值 / Get an independent value by zero-based index.

        Args:
            index: 非负整数，不接受 bool；无 Python 负索引语义 / Nonnegative integer, not bool; no Python negative indexing.

        Returns:
            独立有理数或 OUT_OF_RANGE/输入失败 / Independent rational or OUT_OF_RANGE/input failure.
        """
        if not isinstance(index, int) or isinstance(index, bool):
            return invalid("索引必须为整数 / Index must be an integer")
        return invoke(lambda: self._handle.at(index)).map(Rational)

    def sum(self) -> Rational:
        """单次 FFI 精确求和，空批次为 0 / Exact sum in one FFI call; empty batch yields zero."""
        return Rational(self._handle.sum())

    def dot(self, other: RationalArray) -> BindingResult[Rational]:
        """单次 FFI 精确点积 / Exact dot product in one FFI call.

        Args:
            other: 等长批次，无广播/截断 / Equal-length batch; no broadcasting/truncation.

        Returns:
            精确值或 Failed / Exact value or Failed.
        """
        if not isinstance(other, RationalArray):
            return invalid("操作数必须为精确批次 / Operand must be an exact batch")
        return invoke(lambda: self._handle.dot(other._handle)).map(Rational)

    def _binary(
        self,
        *,
        other: RationalArray,
        operation: Callable[
            [_native.RationalArray],
            tuple[_native.RationalArray | None, _native.Failure | None],
        ],
    ) -> BindingResult[RationalArray]:
        if not isinstance(other, RationalArray):
            return invalid("操作数必须为精确批次 / Operand must be an exact batch")
        return invoke(lambda: operation(other._handle)).map(RationalArray)

    def add(self, other: RationalArray) -> BindingResult[RationalArray]:
        """逐项精确相加 / Add elementwise exactly.

        Args:
            other: 等长批次 / Equal-length batch.

        Returns:
            新批次或 Failed / New batch or Failed.
        """
        return self._binary(other=other, operation=self._handle.add)

    def subtract(self, other: RationalArray) -> BindingResult[RationalArray]:
        """逐项精确相减 / Subtract elementwise exactly.

        Args:
            other: 等长批次 / Equal-length batch.

        Returns:
            新批次或 Failed / New batch or Failed.
        """
        return self._binary(other=other, operation=self._handle.subtract)

    def multiply(self, other: RationalArray) -> BindingResult[RationalArray]:
        """逐项精确相乘 / Multiply elementwise exactly.

        Args:
            other: 等长批次 / Equal-length batch.

        Returns:
            新批次或 Failed / New batch or Failed.
        """
        return self._binary(other=other, operation=self._handle.multiply)

    def divide(self, other: RationalArray) -> BindingResult[RationalArray]:
        """逐项精确相除，不发布部分结果 / Divide elementwise exactly without partial output.

        Args:
            other: 等长且各项非零的批次 / Equal-length batch with nonzero values.

        Returns:
            新批次或 Failed / New batch or Failed.
        """
        return self._binary(other=other, operation=self._handle.divide)
