"""异步物品模型 / Async item model.

BPP3D 异步物品模型接口。
Async item model interface for BPP3D.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Coroutine
    from typing import Any


@dataclass(frozen=True)
class Bpp3dItemModelAsync(abc.ABC):
    """异步物品模型 / Async item model.

    BPP3D 物品模型的异步接口。
    Async interface for BPP3D item models.

    Attributes:
        model_id: 模型标识 / Model identifier.
    """

    model_id: str
    """模型标识 / Model identifier."""

    @abc.abstractmethod
    def solve_async(
        self,
    ) -> Coroutine[Any, Any, Any]:
        """异步求解 / Async solve.

        Returns:
            求解结果协程 / Solve result coroutine.
        """
        ...

    @abc.abstractmethod
    def get_status_async(
        self,
    ) -> Coroutine[Any, Any, str]:
        """异步获取状态 / Async get status.

        Returns:
            模型状态协程 / Model status coroutine.
        """
        ...
