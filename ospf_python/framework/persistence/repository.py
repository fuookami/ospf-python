"""Repository pattern for persistence / 持久化仓储模式.

Provides abstract repository interface for data persistence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Abstract repository for data persistence.

    数据持久化的抽象仓储接口。
    """

    @abstractmethod
    def find_by_id(self, id: str) -> T | None:
        """Find entity by ID / 按 ID 查找实体."""
        ...

    @abstractmethod
    def save(self, entity: T) -> None:
        """Save entity / 保存实体."""
        ...

    @abstractmethod
    def delete(self, id: str) -> None:
        """Delete entity / 删除实体."""
        ...

    @abstractmethod
    def find_all(self) -> list[T]:
        """Find all entities / 查找所有实体."""
        ...
