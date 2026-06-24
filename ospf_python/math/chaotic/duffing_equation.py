"""混沌：Duffing 方程。

Chaotic: Duffing equation.

Duffing 方程描述受迫非线性振子的混沌行为。
Duffing equation describes chaotic behavior of a forced nonlinear oscillator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DuffingEquation:
    """Duffing 方程，二维受迫振子系统。

    Duffing equation, a 2D forced oscillator system.

    dx/dt = y
    dy/dt = -delta*y - alpha*x - beta*x³ + gamma*cos(omega*t)

    使用三维状态 (x, y, t) 以跟踪相位。
    Uses 3D state (x, y, t) to track the forcing phase.

    Attributes:
        delta: 阻尼系数。/ Damping coefficient.
        alpha: 线性刚度。/ Linear stiffness.
        beta: 非线性刚度。/ Nonlinear stiffness.
        gamma: 驱动振幅。/ Forcing amplitude.
        omega: 驱动频率。/ Forcing frequency.
        dt: 时间步长。/ Time step.
    """

    delta: float = 0.3
    alpha: float = -1.0
    beta: float = 1.0
    gamma: float = 0.37
    omega: float = 1.2
    dt: float = 0.01

    def __call__(
        self,
        x: float,
        y: float,
        t: float,
    ) -> tuple[float, float, float]:
        """执行单步迭代。

        Perform a single integration step.

        Args:
            x: 当前位移。/ Current displacement.
            y: 当前速度。/ Current velocity.
            t: 当前时间。/ Current time.

        Returns:
            下一步的 (x, y, t)。/ Next (x, y, t).
        """
        dx = y
        dy = (
            -self.delta * y
            - self.alpha * x
            - self.beta * x * x * x
            + self.gamma * math.cos(self.omega * t)
        )
        return (
            x + dx * self.dt,
            y + dy * self.dt,
            t + self.dt,
        )

    def iterate(
        self,
        x: float,
        y: float,
        t: float,
        *,
        n: int,
    ) -> tuple[float, float, float]:
        """执行 n 步迭代。

        Perform n integration steps.

        Args:
            x: 初始位移。/ Initial displacement.
            y: 初始速度。/ Initial velocity.
            t: 初始时间。/ Initial time.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 (x, y, t)。/ (x, y, t) after n steps.
        """
        cx, cy, ct = x, y, t
        for _ in range(n):
            cx, cy, ct = self(cx, cy, ct)
        return cx, cy, ct
