"""混沌：Hindmarsh-Rose 神经元模型。

Chaotic: Hindmarsh-Rose neuron model.

Hindmarsh-Rose 模型描述神经元的放电动力学行为。
Hindmarsh-Rose model describes neuronal firing dynamics.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HindmarshRoseModel:
    """Hindmarsh-Rose 神经元模型，三维混沌系统。

    Hindmarsh-Rose neuron model, a 3D chaotic system.

    dx/dt = y - a*x³ + b*x² - z + I
    dy/dt = c - d*x² - y
    dz/dt = r*(s*(x - x0) - z)

    Attributes:
        a: 立方项系数。/ Cubic term coefficient.
        b: 二次项系数。/ Quadratic term coefficient.
        c: 恢复变量偏移。/ Recovery variable offset.
        d: 恢复变量系数。/ Recovery variable coefficient.
        r: 慢适应时间常数倒数。/ Slow adaptation rate.
        s: 慢适应耦合强度。/ Slow adaptation coupling.
        x0: 静息电位。/ Resting potential.
        I: 外部驱动电流。/ External driving current.
        dt: 时间步长。/ Time step.
    """

    a: float = 1.0
    b: float = 3.0
    c: float = 1.0
    d: float = 5.0
    r: float = 0.001
    s: float = 4.0
    x0: float = -1.6
    I: float = 3.0  # noqa: E741
    dt: float = 0.01

    def __call__(
        self,
        x: float,
        y: float,
        z: float,
    ) -> tuple[float, float, float]:
        """执行单步迭代。

        Perform a single integration step.

        Args:
            x: 当前膜电位。/ Current membrane potential.
            y: 当前恢复变量。/ Current recovery variable.
            z: 当前慢适应电流。/ Current slow adaptation current.

        Returns:
            下一步的 (x, y, z)。/ Next (x, y, z).
        """
        dx = y - self.a * x * x * x + self.b * x * x - z + self.I
        dy = self.c - self.d * x * x - y
        dz = self.r * (self.s * (x - self.x0) - z)
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
            x: 初始膜电位。/ Initial membrane potential.
            y: 初始恢复变量。/ Initial recovery variable.
            z: 初始慢适应电流。/ Initial slow adaptation current.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的 (x, y, z)。/ (x, y, z) after n steps.
        """
        cx, cy, cz = x, y, z
        for _ in range(n):
            cx, cy, cz = self(cx, cy, cz)
        return cx, cy, cz
