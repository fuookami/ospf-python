"""库元信息 / Library metadata.

对应 Kotlin 端 Library data object。
Mirrors the Kotlin ``Library`` data object.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Library:
    """库元信息单例 / Library metadata singleton.

    以不可变数据类形式暴露库名称和版本号。
    Exposes library name and version as an immutable data class.

    Attributes:
        name: 库名称 / The library name.
        version: 语义化版本号 / Semantic version string.
    """

    name: str = "ospf-python"
    version: str = "0.1.0"
