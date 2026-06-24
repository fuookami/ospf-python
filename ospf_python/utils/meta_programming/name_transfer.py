"""名称转换工具 / Name transfer utilities.

对应 Kotlin 端 NameTransfer。
Mirrors the Kotlin NameTransfer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ospf_python.utils.meta_programming.naming_system import NamingSystem


@dataclass(frozen=True)
class NameTransferCacheKey:
    """名称转换缓存键 / Name transfer cache key.

    用于缓存名称转换结果的不可变键。
    Immutable key for caching name transfer results.

    Attributes:
        name: 原始名称 / The original name.
        system: 目标命名系统 / The target naming system.
    """

    name: str
    system: NamingSystem


class NameTransfer:
    """名称转换器 / Name transfer converter.

    在 camelCase、snake_case、PascalCase 之间转换名称。
    转换结果通过缓存避免重复计算。
    Converts names between camelCase, snake_case, and PascalCase.
    Results are cached to avoid redundant computation.

    Attributes:
        _cache: 转换结果缓存 / The conversion result cache.
    """

    def __init__(self) -> None:
        """初始化名称转换器 / Initialize the name transfer."""
        self._cache: dict[NameTransferCacheKey, str] = {}

    def to_snake(self, name: str) -> str:
        """转换为 snake_case / Convert to snake_case.

        Args:
            name: 原始名称 / The original name.

        Returns:
            snake_case 格式的名称 / The name in snake_case.
        """
        return self._convert(name, NamingSystem.SNAKE_CASE)

    def to_camel(self, name: str) -> str:
        """转换为 camelCase / Convert to camelCase.

        Args:
            name: 原始名称 / The original name.

        Returns:
            camelCase 格式的名称 / The name in camelCase.
        """
        return self._convert(name, NamingSystem.CAMEL_CASE)

    def to_pascal(self, name: str) -> str:
        """转换为 PascalCase / Convert to PascalCase.

        Args:
            name: 原始名称 / The original name.

        Returns:
            PascalCase 格式的名称 / The name in PascalCase.
        """
        return self._convert(name, NamingSystem.PASCAL_CASE)

    def _convert(self, name: str, system: NamingSystem) -> str:
        """执行带缓存的转换 / Perform cached conversion.

        Args:
            name: 原始名称 / The original name.
            system: 目标命名系统 / The target naming system.

        Returns:
            转换后的名称 / The converted name.
        """
        key = NameTransferCacheKey(name=name, system=system)
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        result = self._do_convert(name, system)
        self._cache[key] = result
        return result

    @staticmethod
    def _do_convert(name: str, system: NamingSystem) -> str:
        """实际转换逻辑 / Actual conversion logic.

        先将名称拆分为单词列表，再按目标系统重新组合。
        Splits the name into words first, then reassembles
        according to the target system.

        Args:
            name: 原始名称 / The original name.
            system: 目标命名系统 / The target naming system.

        Returns:
            转换后的名称 / The converted name.
        """
        words = NameTransfer._split_words(name)

        if system is NamingSystem.SNAKE_CASE:
            return "_".join(words)
        if system is NamingSystem.CAMEL_CASE:
            if not words:
                return ""
            return words[0] + "".join(w.capitalize() for w in words[1:])
        if system is NamingSystem.PASCAL_CASE:
            return "".join(w.capitalize() for w in words)
        return name

    @staticmethod
    def _split_words(name: str) -> list[str]:
        """将名称拆分为单词 / Split a name into words.

        支持 snake_case、camelCase、PascalCase 的混合格式。
        Supports mixed formats of snake_case, camelCase, and
        PascalCase.

        Args:
            name: 待拆分的名称 / The name to split.

        Returns:
            小写单词列表 / List of lowercase words.
        """
        # 按下划线拆分 / Split by underscores
        parts = name.split("_")
        words: list[str] = []
        for part in parts:
            # 按大小写边界拆分 / Split by case boundaries
            tokens = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", part)
            words.extend(tokens)
        return [w.lower() for w in words if w]
