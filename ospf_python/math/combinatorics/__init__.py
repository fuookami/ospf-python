"""Combinatorics module.

Provides combinatorial functions: factorial, permutation, combination.
"""

from __future__ import annotations

from math import factorial as _factorial


def factorial(n: int) -> int:
    """Compute factorial of n.

    Args:
        n: Non-negative integer.

    Returns:
        n!

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError(f"Factorial requires non-negative integer, got {n}")
    return _factorial(n)


def permutation(n: int, k: int) -> int:
    """Compute permutation P(n, k) = n! / (n-k)!.

    Args:
        n: Total items.
        k: Selected items.

    Returns:
        P(n, k).

    Raises:
        ValueError: If k > n or either is negative.
    """
    if n < 0 or k < 0:
        raise ValueError("Permutation requires non-negative integers")
    if k > n:
        raise ValueError(f"k={k} cannot exceed n={n}")
    return _factorial(n) // _factorial(n - k)


def combination(n: int, k: int) -> int:
    """Compute combination C(n, k) = n! / (k! * (n-k)!).

    Args:
        n: Total items.
        k: Selected items.

    Returns:
        C(n, k).

    Raises:
        ValueError: If k > n or either is negative.
    """
    if n < 0 or k < 0:
        raise ValueError("Combination requires non-negative integers")
    if k > n:
        raise ValueError(f"k={k} cannot exceed n={n}")
    return _factorial(n) // (_factorial(k) * _factorial(n - k))


def combinations_with_replacement(n: int, k: int) -> int:
    """Compute combinations with replacement C(n+k-1, k).

    Args:
        n: Total items.
        k: Selected items (with replacement).

    Returns:
        Number of combinations with replacement.
    """
    return combination(n + k - 1, k)


def catalan_number(n: int) -> int:
    """Compute the nth Catalan number.

    Args:
        n: Non-negative integer.

    Returns:
        C(n) = C(2n, n) / (n+1).
    """
    if n < 0:
        raise ValueError(f"Catalan number requires non-negative integer, got {n}")
    return combination(2 * n, n) // (n + 1)


def stirling_second(n: int, k: int) -> int:
    """Compute Stirling number of the second kind S(n, k).

    Args:
        n: Total items.
        k: Non-empty subsets.

    Returns:
        S(n, k).
    """
    if n < 0 or k < 0:
        raise ValueError("Stirling number requires non-negative integers")
    if k > n:
        return 0
    if k == 0:
        return 1 if n == 0 else 0
    if k == 1 or k == n:
        return 1
    # Recurrence: S(n, k) = k * S(n-1, k) + S(n-1, k-1)
    return k * stirling_second(n - 1, k) + stirling_second(n - 1, k - 1)
