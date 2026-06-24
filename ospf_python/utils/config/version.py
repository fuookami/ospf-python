"""版本信息 / Version information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Version:
    """版本信息 / Version information."""

    MAJOR: int = 0
    MINOR: int = 1
    PATCH: int = 0

    @property
    def version_string(self) -> str:
        """版本字符串 / Version string."""
        return f"{self.MAJOR}.{self.MINOR}.{self.PATCH}"

    def __str__(self) -> str:
        return self.version_string


# 模块级单例 / Module-level singleton
VERSION = Version()
