"""混沌：双摆系统。

Chaotic: Double pendulum system.

双摆系统是经典的混沌力学系统。
Double pendulum is a classical chaotic mechanical system.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class DoublePendulumSystem:
    """双摆系统，四维混沌力学系统。

    Double pendulum system, a 4D chaotic mechanical system.

    dθ1/dt = ω1
    dω1/dt = [-g*(2*m1+m2)*sin(θ1)
              - m2*g*sin(θ1-2*θ2)
              - 2*sin(θ1-θ2)*m2
              *(ω2²*l2+ω1²*l1*cos(θ1-θ2))]
             / [l1*(2*m1+m2-m2*cos(2*(θ1-θ2)))]
    dθ2/dt = ω2
    dω2/dt = [2*sin(θ1-θ2)
              *(ω1²*l1*(m1+m2)
              + g*(m1+m2)*cos(θ1)
              + ω2²*l2*m2*cos(θ1-θ2))]
             / [l2*(2*m1+m2-m2*cos(2*(θ1-θ2)))]

    Attributes:
        m1: 上摆质量。/ Upper pendulum mass.
        m2: 下摆质量。/ Lower pendulum mass.
        l1: 上摆长度。/ Upper pendulum length.
        l2: 下摆长度。/ Lower pendulum length.
        g: 重力加速度。/ Gravitational acceleration.
        dt: 时间步长。/ Time step.
    """

    m1: float = 1.0
    m2: float = 1.0
    l1: float = 1.0
    l2: float = 1.0
    g: float = 9.81
    dt: float = 0.01

    def __call__(
        self,
        theta1: float,
        omega1: float,
        theta2: float,
        omega2: float,
    ) -> tuple[float, float, float, float]:
        """执行单步迭代。

        Perform a single integration step.

        Args:
            theta1: 上摆角度（弧度）。/ Upper angle (rad).
            omega1: 上摆角速度。/ Upper angular velocity.
            theta2: 下摆角度（弧度）。/ Lower angle (rad).
            omega2: 下摆角速度。/ Lower angular velocity.

        Returns:
            下一步的状态。/ Next state.
        """
        m1 = self.m1
        m2 = self.m2
        l1 = self.l1
        l2 = self.l2
        g = self.g

        delta = theta1 - theta2
        sin_d = math.sin(delta)
        cos_d = math.cos(delta)

        den1 = l1 * (2 * m1 + m2 - m2 * math.cos(2 * delta))
        den2 = l2 * den1 / l1

        d_omega1 = (
            -g * (2 * m1 + m2) * math.sin(theta1)
            - m2 * g * math.sin(theta1 - 2 * theta2)
            - 2 * sin_d * m2 * (omega2 * omega2 * l2 + omega1 * omega1 * l1 * cos_d)
        ) / den1

        d_omega2 = (
            2
            * sin_d
            * (
                omega1 * omega1 * l1 * (m1 + m2)
                + g * (m1 + m2) * math.cos(theta1)
                + omega2 * omega2 * l2 * m2 * cos_d
            )
        ) / den2

        return (
            theta1 + omega1 * self.dt,
            omega1 + d_omega1 * self.dt,
            theta2 + omega2 * self.dt,
            omega2 + d_omega2 * self.dt,
        )

    def iterate(
        self,
        theta1: float,
        omega1: float,
        theta2: float,
        omega2: float,
        *,
        n: int,
    ) -> tuple[float, float, float, float]:
        """执行 n 步迭代。

        Perform n integration steps.

        Args:
            theta1: 初始上摆角度。/ Initial upper angle.
            omega1: 初始上摆角速度。/ Initial upper velocity.
            theta2: 初始下摆角度。/ Initial lower angle.
            omega2: 初始下摆角速度。/ Initial lower velocity.
            n: 迭代步数。/ Number of steps.

        Returns:
            n 步后的状态。/ State after n steps.
        """
        ct1, co1, ct2, co2 = theta1, omega1, theta2, omega2
        for _ in range(n):
            ct1, co1, ct2, co2 = self(ct1, co1, ct2, co2)
        return ct1, co1, ct2, co2
