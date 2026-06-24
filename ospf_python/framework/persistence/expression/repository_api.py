"""仓储 API / Repository API.

定义数据仓储的抽象接口。
Defines the abstract interface for data repositories.
"""

from __future__ import annotations

import abc
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class RepositoryApi(abc.ABC, Generic[T]):
    """仓储 API / Repository API.

    提供通用的数据仓储操作接口。
    Provides a common interface for data repository operations.

    Type Parameters:
        T: 实体类型 / The entity type.
    """

    @abc.abstractmethod
    def find_by_id(self, entity_id: Any) -> T | None:
        """按 ID 查找 / Find by ID.

        Args:
            entity_id: 实体标识 / The entity identifier.

        Returns:
            查找到的实体或 None / The found entity or None.
        """
        ...

    @abc.abstractmethod
    def save(self, entity: T) -> T:
        """保存实体 / Save entity.

        Args:
            entity: 要保存的实体 / The entity to save.

        Returns:
            保存后的实体 / The saved entity.
        """
        ...

    @abc.abstractmethod
    def delete(self, entity_id: Any) -> bool:
        """删除实体 / Delete entity.

        Args:
            entity_id: 实体标识 / The entity identifier.

        Returns:
            删除成功返回 True / True if deletion succeeded.
        """
        ...

    @abc.abstractmethod
    def find_all(self) -> list[T]:
        """查找全部 / Find all.

        Returns:
            所有实体列表 / List of all entities.
        """
        ...
