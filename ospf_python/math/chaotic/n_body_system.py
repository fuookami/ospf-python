"""混沌系统：N 体引力系统。

Chaotic system: N-body gravitational system.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class NBodySystem:
    """N 体引力系统，模拟多个天体在引力作用下的运动。

    N-body gravitational system simulating the motion
    of multiple bodies under gravitational attraction.

    状态向量为 [x0, y0, vx0, vy0, x1, y1, vx1,
    vy1, ...]，其中每个物体有位置 (x, y) 和速度
    (vx, vy)。

    State vector is [x0, y0, vx0, vy0, x1, y1, vx1,
    vy1, ...] where each body has position (x, y) and
    velocity (vx, vy).

    Attributes:
        n_bodies: 天体数量。/ Number of bodies.
        G: 引力常数。/ Gravitational constant.
        softening: 软化长度，防止奇异性。
            Softening length to prevent singularities.
        dt: 时间步长。/ Time step.
    """

    n_bodies: int = 3
    G: float = 1.0
    softening: float = 0.01
    dt: float = 0.001

    def __call__(
        self,
        state: tuple[float, ...],
    ) -> tuple[float, ...]:
        """执行单步积分。

        Apply one integration step.

        Args:
            state: 当前状态向量，长度为 4 * n_bodies。
                Current state vector of length 4*n_bodies.

        Returns:
            下一步状态向量。/ Next state vector.
        """
        n = self.n_bodies
        grav_const = self.G
        eps2 = self.softening * self.softening
        dt = self.dt
        ax = [0.0] * n
        ay = [0.0] * n
        for i in range(n):
            xi = state[4 * i]
            yi = state[4 * i + 1]
            for j in range(n):
                if i == j:
                    continue
                xj = state[4 * j]
                yj = state[4 * j + 1]
                dx = xj - xi
                dy = yj - yi
                r2 = dx * dx + dy * dy + eps2
                r3 = r2 * math.sqrt(r2)
                ax[i] += grav_const * dx / r3
                ay[i] += grav_const * dy / r3
        result = []
        for i in range(n):
            px = state[4 * i]
            py = state[4 * i + 1]
            vx = state[4 * i + 2]
            vy = state[4 * i + 3]
            result.append(px + vx * dt)
            result.append(py + vy * dt)
            result.append(vx + ax[i] * dt)
            result.append(vy + ay[i] * dt)
        return tuple(result)

    def iterate(
        self,
        state: tuple[float, ...],
        *,
        n: int = 1000,
    ) -> tuple[float, ...]:
        """迭代系统 n 步。

        Iterate the system n steps.

        Args:
            state: 初始状态向量。
                Initial state vector.
            n: 迭代步数。/ Number of steps.

        Returns:
            最终状态向量。/ Final state vector.
        """
        result = state
        for _ in range(n):
            result = self(result)
        return result
