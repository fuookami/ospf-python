"""回调模型 / Callback model.

为求解器回调提供模型访问接口。
Provides model access interface for solver callbacks.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CallBackModel:
    """回调模型 / Callback model.

    在求解过程中允许用户通过回调函数访问和修改模型状态。
    Allows users to access and modify model state during
    solving through callback functions.

    Attributes:
        callbacks: 已注册的回调函数列表 / List of registered
            callback functions.
    """

    callbacks: list[object] = field(default_factory=list)

    def register(self, callback: object) -> None:
        """注册回调函数 / Register a callback function.

        Args:
            callback: 要注册的回调函数 / The callback function
                to register.
        """
        self.callbacks.append(callback)

    def clear(self) -> None:
        """清除所有回调 / Clear all callbacks."""
        self.callbacks.clear()
