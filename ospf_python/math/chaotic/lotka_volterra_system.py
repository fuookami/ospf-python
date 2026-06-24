"""混沌系统：Lotka-Volterra 捕食者-猎物系统。

Chaotic system: Lotka-Volterra predator-prey system.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LotkaVolterraSystem:
    """Lotka-Volterra 捕食者-猎物模型。

    Lotka-Volterra predator-prey model.

    微分方程：
    dx/dt = a * x - b * x * y
    dy/dt = d * x * y - c * y

    其中 x 为猎物种群，y 为捕食者种群。

    where x is prey population and y is predator
    population.

    Differential equations:
    dx/dt = a * x - b * x * y
    dy/dt = d * x * y - c * y

    Attributes:
        a: 猎物增长率。/ Prey growth rate.
        b: 捕食率。/ Predation rate.
        c: 捕食者死亡率。/ Predator death rate.
        d: 捕食者增长效率。
            Predator growth efficiency.
        dt: 时间步长。/ Time step.
    """

    a: float = 1.0
    b: float = 0.1
    c: float = 1.5
    d: float = 0.075
    dt: float = 0.01

    def __call__(
        self,
        state: tuple[float, float],
    ) -> tuple[float, float]:
        """执行单步积分。

        Apply one integration step.

        Args:
            state: 当前 (x, y) 状态。
                Current (x, y) state.

        Returns:
            下一步 (x, y) 状态。
            Next (x, y) state.
        """
        x, y = state
        dx = self.a * x - self.b * x * y
        dy = self.d * x * y - self.c * y
        return (
            x + dx * self.dt,
            y + dy * self.dt,
        )

    def iterate(
        self,
        state: tuple[float, float],
        *,
        n: int = 1000,
    ) -> tuple[float, float]:
        """迭代系统 n 步。

        Iterate the system n steps.

        Args:
            state: 初始 (x, y) 状态。
                Initial (x, y) state.
            n: 迭代步数。/ Number of steps.

        Returns:
            最终 (x, y) 状态。
            Final (x, y) state.
        """
        result = state
        for _ in range(n):
            result = self(result)
        return result
