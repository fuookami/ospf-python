"""混沌：Van der Pol 振荡器。

Chaotic: Van der Pol oscillator.

Van der Pol 振荡器是一种非线性阻尼振荡系统。
Van der Pol oscillator is a nonlinear damped oscillation system.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VanDerPolSystem:
    """Van der Pol 振荡器，二维非线性系统。

    Van der Pol oscillator, a 2D nonlinear system.

    dx/dt = y
    dy/dt = mu * (1 - x^2) * y - x

    Attributes:
        mu: 非线性阻尼参数。/ Nonlinear damping parameter.
        dt: 时间步长。/ Time step.
    """

    mu: float = 1.0
    dt: float = 0.01

    def __call__(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:
        """执行单步迭代。

        Perform a single integration step.

        Args:
            x: 当前 x 值。/ Current x value.
            y: 当前 y 值。/ Current y value.

        Returns:
            下一步的 (x, y)。/ Next (x, y).
        """
        # 决定 5 / B320：**保留本文件 docstring 声明的标准 Van der Pol 形式**
        # `dx/dt = y`、`dy/dt = mu*(1 - x²)*y - x`。
        # B310 曾按 Kotlin 的 Liénard 缩放形式 `dx = a(x−x³/3) − y`、`dy = x/a` 改过，
        # 那与本文件声明冲突，已回退。Kotlin/Rust 的 Liénard 形式是它们自己的表示。
        # Keep the STANDARD Van der Pol form declared in this file's docstring (B320).
        # B310 switched to Kotlin's scaled Lienard form, which contradicted the declaration,
        # and that is reverted.
        dx = y
        dy = self.mu * (1 - x * x) * y - x
        return (
            x + dx * self.dt,
            y + dy * self.dt,
        )

    def iterate(
        self,
        x: float,
        y: float,
        *,
        n: int,
    ) -> tuple[float, float]:
        """执行 n 步迭代。

        Perform n integration steps.

        Args:
            x: 初始 x 值。/ Initial x value.
            y: 初始 y 值。/ Initial y value.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 (x, y)。/ (x, y) after n steps.
        """
        cx, cy = x, y
        for _ in range(n):
            cx, cy = self(cx, cy)
        return cx, cy
