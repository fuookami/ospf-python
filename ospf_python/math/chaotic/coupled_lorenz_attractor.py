"""混沌：耦合 Lorenz 吸引子。

Chaotic: Coupled Lorenz attractor.

两个 Lorenz 系统通过耦合项相互作用。
Two Lorenz systems interacting through coupling terms.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoupledLorenzAttractor:
    """耦合 Lorenz 吸引子，六维混沌系统。

    Coupled Lorenz attractor, a 6D chaotic system.

    System 1:
      dx1/dt = sigma * (y1 - x1)
      dy1/dt = r * x1 - y1 - x1 * z1
      dz1/dt = -b * z1 + x1 * y1

    System 2:
      dx2/dt = sigma * (y2 - x2) + k * (x1 - x2)
      dy2/dt = r * x2 - y2 - x2 * z2
      dz2/dt = -b * z2 + x2 * y2

    Attributes:
        sigma: Prandtl 数。/ Prandtl number.
        r: Rayleigh 数。/ Rayleigh number.
        b: 几何参数。/ Geometric parameter.
        k: 耦合强度。/ Coupling strength.
        dt: 时间步长。/ Time step.
    """

    sigma: float = 10.0
    r: float = 28.0
    b: float = 8.0 / 3.0
    k: float = 1.0
    dt: float = 0.001

    def __call__(
        self,
        x1: float,
        y1: float,
        z1: float,
        x2: float,
        y2: float,
        z2: float,
    ) -> tuple[float, float, float, float, float, float]:
        """执行单步迭代。

        Perform a single integration step.

        Args:
            x1: 系统 1 当前 x 坐标。/ System 1 current x.
            y1: 系统 1 当前 y 坐标。/ System 1 current y.
            z1: 系统 1 当前 z 坐标。/ System 1 current z.
            x2: 系统 2 当前 x 坐标。/ System 2 current x.
            y2: 系统 2 当前 y 坐标。/ System 2 current y.
            z2: 系统 2 当前 z 坐标。/ System 2 current z.

        Returns:
            下一步的 (x1, y1, z1, x2, y2, z2)。
            Next (x1, y1, z1, x2, y2, z2).
        """
        dx1 = self.sigma * (y1 - x1)
        dy1 = self.r * x1 - y1 - x1 * z1
        dz1 = -self.b * z1 + x1 * y1

        dx2 = self.sigma * (y2 - x2) + self.k * (x1 - x2)
        dy2 = self.r * x2 - y2 - x2 * z2
        dz2 = -self.b * z2 + x2 * y2

        return (
            x1 + dx1 * self.dt,
            y1 + dy1 * self.dt,
            z1 + dz1 * self.dt,
            x2 + dx2 * self.dt,
            y2 + dy2 * self.dt,
            z2 + dz2 * self.dt,
        )

    def iterate(
        self,
        x1: float,
        y1: float,
        z1: float,
        x2: float,
        y2: float,
        z2: float,
        *,
        n: int,
    ) -> tuple[float, float, float, float, float, float]:
        """执行 n 步迭代。

        Perform n integration steps.

        Args:
            x1: 系统 1 初始 x 坐标。/ System 1 initial x.
            y1: 系统 1 初始 y 坐标。/ System 1 initial y.
            z1: 系统 1 初始 z 坐标。/ System 1 initial z.
            x2: 系统 2 初始 x 坐标。/ System 2 initial x.
            y2: 系统 2 初始 y 坐标。/ System 2 initial y.
            z2: 系统 2 初始 z 坐标。/ System 2 initial z.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 (x1, y1, z1, x2, y2, z2)。
            (x1, y1, z1, x2, y2, z2) after n steps.
        """
        cx1, cy1, cz1 = x1, y1, z1
        cx2, cy2, cz2 = x2, y2, z2
        for _ in range(n):
            cx1, cy1, cz1, cx2, cy2, cz2 = self(
                cx1,
                cy1,
                cz1,
                cx2,
                cy2,
                cz2,
            )
        return cx1, cy1, cz1, cx2, cy2, cz2
