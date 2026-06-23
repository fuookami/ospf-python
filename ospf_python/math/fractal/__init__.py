"""Fractal module.

Provides fractal dimension calculations and fractal generators.
"""

from __future__ import annotations

import math


def fractal_dimension_box(count: int, scale: float) -> float:
    """Compute fractal dimension using box-counting method.

    Args:
        count: Number of boxes covering the fractal.
        scale: Scale factor.

    Returns:
        Fractal dimension D = log(count) / log(1/scale).
    """
    if count <= 0:
        raise ValueError(f"Count must be positive, got {count}")
    if scale <= 0 or scale >= 1:
        raise ValueError(f"Scale must be in (0, 1), got {scale}")
    return math.log(count) / math.log(1.0 / scale)


def sierpinski_triangle_area(order: int, initial_area: float = 1.0) -> float:
    """Compute area of Sierpinski triangle at given order.

    Args:
        order: Iteration order (0 = full triangle).
        initial_area: Area of initial triangle.

    Returns:
        Area at given order.
    """
    if order < 0:
        raise ValueError(f"Order must be non-negative, got {order}")
    return initial_area * (3.0 / 4.0) ** order


def sierpinski_triangle_count(order: int) -> int:
    """Compute number of triangles in Sierpinski triangle.

    Args:
        order: Iteration order.

    Returns:
        Number of triangles.
    """
    if order < 0:
        raise ValueError(f"Order must be non-negative, got {order}")
    result: int = 3**order
    return result


def koch_curve_length(order: int, initial_length: float = 1.0) -> float:
    """Compute length of Koch curve at given order.

    Args:
        order: Iteration order.
        initial_length: Length of initial segment.

    Returns:
        Length at given order.
    """
    if order < 0:
        raise ValueError(f"Order must be non-negative, got {order}")
    return initial_length * (4.0 / 3.0) ** order


def cantor_set_count(order: int) -> int:
    """Compute number of intervals in Cantor set.

    Args:
        order: Iteration order.

    Returns:
        Number of intervals.
    """
    if order < 0:
        raise ValueError(f"Order must be non-negative, got {order}")
    result: int = 2**order
    return result


def cantor_set_length(order: int, initial_length: float = 1.0) -> float:
    """Compute total length of Cantor set intervals.

    Args:
        order: Iteration order.
        initial_length: Length of initial interval.

    Returns:
        Total length at given order.
    """
    if order < 0:
        raise ValueError(f"Order must be non-negative, got {order}")
    return initial_length * (2.0 / 3.0) ** order


def mandelbrot_iteration(c: complex, max_iter: int = 100) -> int:
    """Compute Mandelbrot set iteration count.

    Args:
        c: Complex number to test.
        max_iter: Maximum iterations.

    Returns:
        Number of iterations before escape (0 if in set).
    """
    z: complex = 0 + 0j
    for i in range(max_iter):
        z = z * z + c
        if abs(z) > 2:
            return i
    return max_iter


def julia_iteration(
    z: complex,
    c: complex,
    max_iter: int = 100,
) -> int:
    """Compute Julia set iteration count.

    Args:
        z: Initial complex number.
        c: Julia set parameter.
        max_iter: Maximum iterations.

    Returns:
        Number of iterations before escape (0 if in set).
    """
    current: complex = z
    for i in range(max_iter):
        current = current * current + c
        if abs(current) > 2:
            return i
    return max_iter
