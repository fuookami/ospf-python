"""量纲定义。/ Dimensions definition."""

from __future__ import annotations

from dataclasses import dataclass

from ospf_python.quantities.dimension.fundamental_quantity import (
    FundamentalQuantity,
)


@dataclass(frozen=True)
class Dimensions:
    """物理量量纲。/ Physical quantity dimensions.

    用 7 个基本量纲指数表示导出量纲。
    Represented by 7 fundamental dimension exponents.

    Attributes:
        mass: 质量指数。/ Mass exponent.
        length: 长度指数。/ Length exponent.
        time: 时间指数。/ Time exponent.
        current: 电流指数。/ Current exponent.
        temperature: 温度指数。/ Temperature exponent.
        amount: 物质的量指数。/ Amount exponent.
        luminous_intensity: 发光强度指数。
            Luminous intensity exponent.
    """

    mass: float = 0.0
    length: float = 0.0
    time: float = 0.0
    current: float = 0.0
    temperature: float = 0.0
    amount: float = 0.0
    luminous_intensity: float = 0.0

    def __mul__(self, other: Dimensions) -> Dimensions:
        """量纲乘法，指数相加。

        Dimension multiplication by adding exponents.

        Args:
            other: 另一个量纲。/ Another dimension.

        Returns:
            乘积量纲。/ Product dimension.
        """
        return Dimensions(
            mass=self.mass + other.mass,
            length=self.length + other.length,
            time=self.time + other.time,
            current=self.current + other.current,
            temperature=self.temperature + other.temperature,
            amount=self.amount + other.amount,
            luminous_intensity=(self.luminous_intensity + other.luminous_intensity),
        )

    def __truediv__(self, other: Dimensions) -> Dimensions:
        """量纲除法，指数相减。

        Dimension division by subtracting exponents.

        Args:
            other: 另一个量纲。/ Another dimension.

        Returns:
            商量纲。/ Quotient dimension.
        """
        return Dimensions(
            mass=self.mass - other.mass,
            length=self.length - other.length,
            time=self.time - other.time,
            current=self.current - other.current,
            temperature=self.temperature - other.temperature,
            amount=self.amount - other.amount,
            luminous_intensity=(self.luminous_intensity - other.luminous_intensity),
        )

    def __pow__(self, exp: float) -> Dimensions:
        """量纲幂运算，所有指数乘以幂次。

        Dimension power by multiplying all exponents.

        Args:
            exp: 幂次。/ Power exponent.

        Returns:
            幂次量纲。/ Powered dimension.
        """
        return Dimensions(
            mass=self.mass * exp,
            length=self.length * exp,
            time=self.time * exp,
            current=self.current * exp,
            temperature=self.temperature * exp,
            amount=self.amount * exp,
            luminous_intensity=(self.luminous_intensity * exp),
        )

    def is_dimensionless(self) -> bool:
        """是否无量纲。/ Check if dimensionless.

        Returns:
            所有指数为零时返回 True。
            True when all exponents are zero.
        """
        return all(
            v == 0.0
            for v in (
                self.mass,
                self.length,
                self.time,
                self.current,
                self.temperature,
                self.amount,
                self.luminous_intensity,
            )
        )

    def get(self, fq: FundamentalQuantity) -> float:
        """获取指定基本量纲的指数。

        Get exponent for a fundamental quantity.

        Args:
            fq: 基本量纲。/ Fundamental quantity.

        Returns:
            对应指数。/ Corresponding exponent.
        """
        mapping = {
            FundamentalQuantity.MASS: self.mass,
            FundamentalQuantity.LENGTH: self.length,
            FundamentalQuantity.TIME: self.time,
            FundamentalQuantity.CURRENT: self.current,
            FundamentalQuantity.TEMPERATURE: self.temperature,
            FundamentalQuantity.AMOUNT: self.amount,
            FundamentalQuantity.LUMINOUS_INTENSITY: self.luminous_intensity,
        }
        return mapping[fq]
