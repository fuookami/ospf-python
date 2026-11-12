"""混沌：Dadras 吸引子。

Chaotic: Dadras attractor.

Dadras 系统是一种三维混沌吸引子 (Dadras & Momeni, 2010)。
Dadras system is a 3D chaotic attractor (Dadras & Momeni, 2010).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DadrasAttractor:
    """Dadras 吸引子，三维混沌系统。

    Dadras attractor, a 3D chaotic system.

    dx/dt = y - a*x + b*y*z
    dy/dt = c*y + z*(1 - x)
    dz/dt = d*x*y - h*z

    Attributes:
        a: 控制参数 a。/ Control parameter a.
        b: 控制参数 b。/ Control parameter b.
        c: 控制参数 c。/ Control parameter c.
        d: 控制参数 d。/ Control parameter d.
        h: 控制参数 h。/ Control parameter h.
        dt: 时间步长。/ Time step.
    """

    a: float = 3.0
    b: float = 2.7
    c: float = 1.7
    d: float = 2.0
    h: float = 9.0
    dt: float = 0.001

    def __call__(
        self,
        x: float,
        y: float,
        z: float,
    ) -> tuple[float, float, float]:
        """执行单步迭代。

        Perform a single integration step.

        Args:
            x: 当前 x 坐标。/ Current x coordinate.
            y: 当前 y 坐标。/ Current y coordinate.
            z: 当前 z 坐标。/ Current z coordinate.

        Returns:
            下一步的 (x, y, z)。/ Next (x, y, z).
        """
        # 决定 5 / B315（2026-11-11）：**按线上权威与 `ospf-kotlin`/上游 Rust 统一**。
        # 标准 Dadras 系统（Dadras & Momeni 2009）：
        #   ẋ = y − a·x + b·y·z ,  ẏ = c·y + z(1 − x) ,  ż = d·x·y − e·z
        # 本文件字段的角色对应：`a↔ρ`、`b↔σ`、`c↔γ`、`d↔ζ`、`h↔ε`
        # （默认值逐一对上：3.0 / 2.7 / 1.7 / 2.0 / 9.0）。
        # 原实现的 `dx`/`dy` 是完全不同的系统，`dz` 结构本来就对。
        # Unified with the standard Dadras system and with `ospf-kotlin` / upstream Rust (B315).
        # Field roles: a↔rho, b↔sigma, c↔gamma, d↔zeta, h↔epsilon (defaults match one for one).
        dx = y - self.a * x + self.b * y * z
        dy = self.c * y + z * (1.0 - x)
        dz = self.d * x * y - self.h * z
        return (
            x + dx * self.dt,
            y + dy * self.dt,
            z + dz * self.dt,
        )

    def iterate(
        self,
        x: float,
        y: float,
        z: float,
        *,
        n: int,
    ) -> tuple[float, float, float]:
        """执行 n 步迭代。

        Perform n integration steps.

        Args:
            x: 初始 x 坐标。/ Initial x coordinate.
            y: 初始 y 坐标。/ Initial y coordinate.
            z: 初始 z 坐标。/ Initial z coordinate.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 (x, y, z)。/ (x, y, z) after n steps.
        """
        cx, cy, cz = x, y, z
        for _ in range(n):
            cx, cy, cz = self(cx, cy, cz)
        return cx, cy, cz
