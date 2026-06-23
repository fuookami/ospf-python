"""Ordinary mathematical functions.

Provides common mathematical functions.
"""

from __future__ import annotations

import math
from typing import TypeVar

from ospf_python.math.algebra.number import Float64, RealNumber

V = TypeVar("V", bound=RealNumber)


def clamp(value: RealNumber, lower: RealNumber, upper: RealNumber) -> RealNumber:
    """Clamp value to range [lower, upper].

    Args:
        value: Value to clamp.
        lower: Lower bound.
        upper: Upper bound.

    Returns:
        Clamped value.
    """
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def lerp(a: RealNumber, b: RealNumber, t: float) -> RealNumber:
    """Linear interpolation between a and b.

    Args:
        a: Start value.
        b: End value.
        t: Interpolation factor (0..1).

    Returns:
        Interpolated value.
    """
    return Float64(a.to_float() + t * (b.to_float() - a.to_float()))


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Smoothstep interpolation.

    Args:
        edge0: Lower edge.
        edge1: Upper edge.
        x: Input value.

    Returns:
        Smoothstep result.
    """
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3 - 2 * t)


def sign(x: RealNumber) -> int:
    """Sign function.

    Args:
        x: Input value.

    Returns:
        -1, 0, or 1.
    """
    if x.to_float() < 0:
        return -1
    if x.to_float() > 0:
        return 1
    return 0


def gcd(a: int, b: int) -> int:
    """Greatest common divisor.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        GCD of a and b.
    """
    return math.gcd(a, b)


def lcm(a: int, b: int) -> int:
    """Least common multiple.

    Args:
        a: First integer.
        b: Second integer.

    Returns:
        LCM of a and b.
    """
    return abs(a * b) // math.gcd(a, b)


def is_prime(n: int) -> bool:
    """Check if number is prime.

    Args:
        n: Integer to check.

    Returns:
        True if prime.
    """
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def primes_up_to(n: int) -> list[int]:
    """Generate primes up to n using sieve of Eratosthenes.

    Args:
        n: Upper bound.

    Returns:
        List of primes.
    """
    if n < 2:
        return []
    sieve = [True] * (n + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(n**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, n + 1, i):
                sieve[j] = False
    return [i for i in range(2, n + 1) if sieve[i]]
