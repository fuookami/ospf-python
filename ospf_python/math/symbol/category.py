"""符号类别枚举。

Symbol category enumeration.
"""

from __future__ import annotations

import enum


class Category(enum.Enum):
    """符号多项式类别。

    Symbol polynomial category.

    Attributes:
        LINEAR: 线性类别。/ Linear category.
        QUADRATIC: 二次类别。/ Quadratic category.
        CANONICAL: 标准（通用）类别。/ Canonical (general) category.
    """

    LINEAR = "linear"
    QUADRATIC = "quadratic"
    CANONICAL = "canonical"

    @property
    def is_linear(self) -> bool:
        """是否为线性类别。/ Whether linear."""
        return self == Category.LINEAR

    @property
    def is_quadratic(self) -> bool:
        """是否为二次类别。/ Whether quadratic."""
        return self == Category.QUADRATIC

    @property
    def is_canonical(self) -> bool:
        """是否为标准类别。/ Whether canonical."""
        return self == Category.CANONICAL
