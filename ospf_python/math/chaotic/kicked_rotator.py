"""混沌映射：受击转子。

Chaotic map: Kicked rotator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class KickedRotator:
    """受击转子映射，描述周期性脉冲力矩下的旋转运动。

    Kicked rotator map describing rotational motion
    under periodic impulsive torque.

    映射规则：
    p_{n+1} = p_n + K * sin(theta_n)
    theta_{n+1} = theta_n + p_{n+1}

    Map rules:
    p_{n+1} = p_n + K * sin(theta_n)
    theta_{n+1} = theta_n + p_{n+1}

    Attributes:
        K: 击打强度。/ Kick strength.
    """

    K: float = 1.0

    def __call__(
        self,
        state: tuple[float, float],
    ) -> tuple[float, float]:
        """执行单步迭代。

        Apply one iteration step.

        Args:
            state: 当前 (theta, p) 状态。
                Current (theta, p) state.

        Returns:
            下一步 (theta, p) 状态。
            Next (theta, p) state.
        """
        theta, p = state
        # 决定 5 / B320：**保留本文件声明的返回顺序 `(theta, p)`**。
        # docstring 声明 `p_{n+1} = p_n + K*sin(theta_n)`、`theta_{n+1} = theta_n + p_{n+1}`，
        # 且 `Returns: 下一步 (theta, p)`。B310 曾按 Kotlin 的 `(l', θ')` 顺序改过，
        # 那与本文件声明冲突，已回退。Kotlin/Rust 的分量顺序是它们自己的偏离。
        # Keep the DECLARED return order `(theta, p)` (B320). The docstring declares the map
        # and states `Returns: Next (theta, p)`; B310 flipped it to kotlin's (l', theta') order,
        # which contradicted this file, and that is reverted. Kotlin/Rust carry their own ordering.
        p_new = p + self.K * math.sin(theta)
        theta_new = theta + p_new
        return (theta_new, p_new)

    def iterate(
        self,
        state: tuple[float, float],
        *,
        n: int = 100,
    ) -> tuple[float, float]:
        """迭代映射 n 次。

        Iterate the map n times.

        Args:
            state: 初始 (theta, p) 状态。
                Initial (theta, p) state.
            n: 迭代次数。/ Number of iterations.

        Returns:
            最终 (theta, p) 状态。
            Final (theta, p) state.
        """
        result = state
        for _ in range(n):
            result = self(result)
        return result
