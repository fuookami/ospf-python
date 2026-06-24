"""异步物品服务 / Async item service.

BPP3D 异步物品服务接口。
Async item service interface for BPP3D.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing import Any

    from ospf_python.framework.bpp3d.domain.item.model.item import Item


@dataclass(frozen=True)
class Bpp3dItemServiceAsync(abc.ABC):
    """异步物品服务 / Async item service.

    BPP3D 物品服务的异步接口。
    Async interface for BPP3D item services.

    Attributes:
        service_id: 服务标识 / Service identifier.
    """

    service_id: str
    """服务标识 / Service identifier."""

    @abc.abstractmethod
    def get_items_async(
        self,
    ) -> Coroutine[Any, Any, tuple[Item, ...]]:
        """异步获取物品列表 / Async get item list.

        Returns:
            物品列表协程 / Item list coroutine.
        """
        ...

    @abc.abstractmethod
    def solve_async(
        self,
        *,
        items: tuple[Item, ...],
    ) -> Coroutine[Any, Any, Any]:
        """异步求解 / Async solve.

        Args:
            items: 物品列表 / Item list.

        Returns:
            求解结果协程 / Solve result coroutine.
        """
        ...
