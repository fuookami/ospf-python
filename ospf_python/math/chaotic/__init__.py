"""Chaotic dynamics module.

Provides chaotic maps and functions: logistic, tent, sine, etc.
"""

from __future__ import annotations

import math
from collections.abc import Callable


def logistic_map(x: float, r: float) -> float:
    """Logistic map: x_{n+1} = r * x_n * (1 - x_n).

    Args:
        x: Current value (0..1).
        r: Growth parameter.

    Returns:
        Next value.
    """
    return r * x * (1 - x)


def tent_map(x: float, mu: float) -> float:
    """Tent map.

    Args:
        x: Current value (0..1).
        mu: Slope parameter.

    Returns:
        Next value.
    """
    if x < 0.5:
        return mu * x
    return mu * (1 - x)


def sine_map(x: float, r: float) -> float:
    """Sine map: x_{n+1} = r * sin(pi * x_n).

    Args:
        x: Current value (0..1).
        r: Growth parameter.

    Returns:
        Next value.
    """
    return r * math.sin(math.pi * x)


def gauss_map(x: float, beta: float) -> float:
    """Gauss map (mouse map).

    Args:
        x: Current value.
        beta: Parameter.

    Returns:
        Next value.
    """
    if x == 0:
        return 0
    return math.exp(-beta * x**2)


def circle_map(x: float, omega: float, k: float) -> float:
    """Circle map.

    Args:
        x: Current value.
        omega: Frequency.
        k: Coupling strength.

    Returns:
        Next value.
    """
    return (x + omega - k / (2 * math.pi) * math.sin(2 * math.pi * x)) % 1


def henon_map(
    x: float, y: float, a: float = 1.4, b: float = 0.3
) -> tuple[float, float]:
    """Henon map.

    Args:
        x: Current x value.
        y: Current y value.
        a: Parameter a.
        b: Parameter b.

    Returns:
        Next (x, y) values.
    """
    new_x = 1 - a * x**2 + y
    new_y = b * x
    return new_x, new_y


def ikeda_map(x: float, y: float, u: float = 0.9) -> tuple[float, float]:
    """Ikeda map.

    Args:
        x: Current x value.
        y: Current y value.
        u: Parameter.

    Returns:
        Next (x, y) values.
    """
    t = 0.4 - 6.0 / (1 + x**2 + y**2)
    new_x = 1 + u * (x * math.cos(t) - y * math.sin(t))
    new_y = u * (x * math.sin(t) + y * math.cos(t))
    return new_x, new_y


def standard_map(
    theta: float,
    p: float,
    k: float = 1.0,
) -> tuple[float, float]:
    """Standard (Chirikov) map.

    Args:
        theta: Current angle.
        p: Current momentum.
        k: Stochasticity parameter.

    Returns:
        Next (theta, p) values.
    """
    new_p = (p + k * math.sin(theta)) % (2 * math.pi)
    new_theta = (theta + new_p) % (2 * math.pi)
    return new_theta, new_p


def lorenz_step(
    x: float,
    y: float,
    z: float,
    dt: float = 0.01,
    sigma: float = 10.0,
    rho: float = 28.0,
    beta: float = 8.0 / 3.0,
) -> tuple[float, float, float]:
    """One step of Lorenz system (Euler method).

    Args:
        x, y, z: Current state.
        dt: Time step.
        sigma, rho, beta: Lorenz parameters.

    Returns:
        Next (x, y, z) values.
    """
    dx = sigma * (y - x)
    dy = x * (rho - z) - y
    dz = x * y - beta * z
    return x + dx * dt, y + dy * dt, z + dz * dt


def rossler_step(
    x: float,
    y: float,
    z: float,
    dt: float = 0.01,
    a: float = 0.2,
    b: float = 0.2,
    c: float = 5.7,
) -> tuple[float, float, float]:
    """One step of Rossler system (Euler method).

    Args:
        x, y, z: Current state.
        dt: Time step.
        a, b, c: Rossler parameters.

    Returns:
        Next (x, y, z) values.
    """
    dx = -y - z
    dy = x + a * y
    dz = b + z * (x - c)
    return x + dx * dt, y + dy * dt, z + dz * dt


def bifurcation_diagram(
    map_fn: Callable[[float, float], float],
    param_range: tuple[float, float],
    x0: float = 0.5,
    n_transient: int = 100,
    n_iter: int = 100,
    n_points: int = 100,
) -> list[tuple[float, list[float]]]:
    """Compute bifurcation diagram.

    Args:
        map_fn: Map function f(x, r) -> x_next.
        param_range: Range of parameter values.
        x0: Initial value.
        n_transient: Number of transient iterations to skip.
        n_iter: Number of iterations to collect.
        n_points: Number of parameter points.

    Returns:
        List of (parameter, [values]) pairs.
    """
    r_min, r_max = param_range
    results = []
    for i in range(n_points):
        r = r_min + (r_max - r_min) * i / (n_points - 1)
        x = x0
        # Skip transient
        for _ in range(n_transient):
            x = map_fn(x, r)
        # Collect values
        values = []
        for _ in range(n_iter):
            x = map_fn(x, r)
            values.append(x)
        results.append((r, values))
    return results


def lyapunov_exponent(
    map_fn: Callable[[float, float], float],
    x0: float,
    r: float,
    n_iter: int = 1000,
) -> float:
    """Compute Lyapunov exponent for a 1D map.

    Args:
        map_fn: Map function f(x, r) -> x_next.
        x0: Initial value.
        r: Parameter.
        n_iter: Number of iterations.

    Returns:
        Lyapunov exponent.
    """
    x = x0
    total = 0.0
    for _ in range(n_iter):
        # Numerical derivative
        eps = 1e-10
        df = (map_fn(x + eps, r) - map_fn(x - eps, r)) / (2 * eps)
        if df == 0:
            return float("-inf")
        total += math.log(abs(df))
        x = map_fn(x, r)
    return total / n_iter
