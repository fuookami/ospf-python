"""回调模型接口 / Callback model interface.

定义回调模型的协议接口。
Defines the protocol interface for callback models.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class CallBackModelInterface(Protocol):
    """回调模型接口协议 / Callback model interface protocol.

    定义回调模型必须实现的方法。
    Defines the methods that a callback model must implement.
    """

    def register(self, callback: object) -> None:
        """注册回调函数 / Register a callback function.

        Args:
            callback: 要注册的回调 / The callback to register.
        """
        ...

    def clear(self) -> None:
        """清除所有回调 / Clear all callbacks."""
        ...
