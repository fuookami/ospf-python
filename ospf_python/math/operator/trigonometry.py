"""三角函数运算符。

Trigonometric function operators.
"""

from __future__ import annotations

import math


def sin_op(x: float) -> float:
    """计算正弦值（弧度）。

    Compute sine (radians).

    Args:
        x: 弧度值。/ Angle in radians.

    Returns:
        正弦值。/ Sine value.
    """
    return math.sin(x)


def cos_op(x: float) -> float:
    """计算余弦值（弧度）。

    Compute cosine (radians).

    Args:
        x: 弧度值。/ Angle in radians.

    Returns:
        余弦值。/ Cosine value.
    """
    return math.cos(x)


def tan_op(x: float) -> float:
    """计算正切值（弧度）。

    Compute tangent (radians).

    Args:
        x: 弧度值。/ Angle in radians.

    Returns:
        正切值。/ Tangent value.
    """
    return math.tan(x)


def asin_op(x: float) -> float:
    """计算反正弦值（返回弧度）。

    Compute arcsine (returns radians).

    Args:
        x: 输入值 [-1, 1]。/ Input in [-1, 1].

    Returns:
        反正弦弧度值。/ Arcsine in radians.
    """
    return math.asin(x)


def acos_op(x: float) -> float:
    """计算反余弦值（返回弧度）。

    Compute arccosine (returns radians).

    Args:
        x: 输入值 [-1, 1]。/ Input in [-1, 1].

    Returns:
        反余弦弧度值。/ Arccosine in radians.
    """
    return math.acos(x)


def atan_op(x: float) -> float:
    """计算反正切值（返回弧度）。

    Compute arctangent (returns radians).

    Args:
        x: 输入值。/ Input value.

    Returns:
        反正切弧度值。/ Arctangent in radians.
    """
    return math.atan(x)
