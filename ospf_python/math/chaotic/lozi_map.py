"""混沌映射：Lozi 映射。

Chaotic map: Lozi map.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LoziMap:
    """Lozi 映射，一个二维分段线性混沌映射。

    Lozi map, a 2D piecewise-linear chaotic map.

    映射规则（以 `ospf-kotlin` 的 `LoziMap.kt` 为准，B309 已统一）：
    x_{n+1} = 1 + y_n - a * |x_n|
    y_{n+1} = b * x_n

    Map rules (unified with `LoziMap.kt` in ospf-kotlin, B309):
    x_{n+1} = 1 + y_n - a * |x_n|
    y_{n+1} = b * x_n

    Attributes:
        a: 非线性参数。/ Nonlinearity parameter.
        b: 线性耦合参数。
            Linear coupling parameter.
    """

    a: float = 1.7
    b: float = 0.5

    def __call__(
        self,
        state: tuple[float, float],
    ) -> tuple[float, float]:
        """执行单步迭代。

        Apply one iteration step.

        Args:
            state: 当前 (x, y) 状态。
                Current (x, y) state.

        Returns:
            下一步 (x, y) 状态。
            Next (x, y) state.
        """
        x, y = state
        # 决定 5 / B309（2026-11-11）：以 `ospf-kotlin` 为准。`LoziMap.kt` 与上游 `lozi.rs`
        # 同为 `(1 + y - a·|x|, b·x)`，而本文件原式 `(1 - a|x| + b·y, x)` 与之不同。
        # docstring 已同步更新——否则实现与自己的文档不符，那比「与上游不一致」更严重。
        # Unified with `ospf-kotlin` (B309): `LoziMap.kt` and `lozi.rs` are both
        # `(1 + y - a*|x|, b*x)`; this file shipped `(1 - a|x| + b*y, x)`. The docstring is
        # updated too, since implementation/doc mismatch is worse than upstream mismatch.
        x_new = 1.0 + y - self.a * abs(x)
        y_new = self.b * x
        return (x_new, y_new)

    def iterate(
        self,
        state: tuple[float, float],
        *,
        n: int = 100,
    ) -> tuple[float, float]:
        """迭代映射 n 次。

        Iterate the map n times.

        Args:
            state: 初始 (x, y) 状态。
                Initial (x, y) state.
            n: 迭代次数。/ Number of iterations.

        Returns:
            最终 (x, y) 状态。
            Final (x, y) state.
        """
        result = state
        for _ in range(n):
            result = self(result)
        return result
