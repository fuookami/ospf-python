"""谓词注解 / Predicate annotations.

定义持久化查询谓词的注解类型。
Defines annotation types for persistence query predicates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PredicateAnnotations:
    """谓词注解 / Predicate annotations.

    为持久化查询谓词提供附加上下文信息。
    Provides附加 context information for persistence
    query predicates.

    Attributes:
        description: 谓词描述 / The predicate description.
        category: 谓词分类 / The predicate category.
        metadata: 附加元数据 / Additional metadata.
    """

    description: str = ""
    category: str = ""
    metadata: dict[str, Any] | None = None
