"""快递上下文模型。

Express context for registering and retrieving delivery components.
"""

from __future__ import annotations

from typing import Any


class ExpressContext:
    """快递上下文。

    Central registry for express delivery-related components such
    as constraints, objectives, and routing strategies.

    Attributes:
        _registry: 内部注册表 / Internal component registry
    """

    def __init__(self) -> None:
        self._registry: dict[str, Any] = {}

    def register(self, name: str, component: Any) -> None:
        """注册组件。

        Registers a component under the given name.

        Args:
            name: 组件名称 / Component name
            component: 组件实例 / Component instance
        """
        self._registry[name] = component

    def lookup(self, name: str) -> Any | None:
        """按名称查找组件。

        Args:
            name: 组件名称 / Component name

        Returns:
            Any | None: 组件实例或None / Component or None
        """
        return self._registry.get(name)

    def has(self, name: str) -> bool:
        """检查组件是否已注册。

        Args:
            name: 组件名称 / Component name

        Returns:
            bool: 是否已注册 / Whether registered
        """
        return name in self._registry

    def registered_names(self) -> tuple[str, ...]:
        """获取所有已注册组件名称。

        Returns:
            tuple: 已注册名称列表 / Registered names
        """
        return tuple(self._registry.keys())

    def remove(self, name: str) -> None:
        """移除已注册组件。

        Args:
            name: 组件名称 / Component name to remove
        """
        self._registry.pop(name, None)

    def clear(self) -> None:
        """清空所有注册组件。

        Removes all registered components.
        """
        self._registry.clear()
