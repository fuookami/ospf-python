"""安全等级定义 / Security level definition.

定义货物安全检查等级。
Defines the cargo security screening levels.
"""

from __future__ import annotations

from enum import IntEnum


class SecurityLevel(IntEnum):
    """安全等级 / Security level.

    描述货物安全检查的等级，等级越高检查越严格。
    数值越高等级越高，便于直接比较。
    Describes the cargo security screening level; higher
    levels require stricter checks. Numeric values increase
    with severity for easy comparison.

    Attributes:
        NORMAL: 常规等级 / Normal level.
        ELEVATED: 提升等级 / Elevated level.
        HIGH: 高等级 / High level.
        MAXIMUM: 最高等级 / Maximum level.
    """

    NORMAL = 1
    """常规等级，标准安全检查 / Normal, standard screening."""

    ELEVATED = 2
    """提升等级，加强安全检查 / Elevated, enhanced screening."""

    HIGH = 3
    """高等级，严格安全检查 / High, strict screening."""

    MAXIMUM = 4
    """最高等级，全面安全检查 / Maximum, comprehensive screening."""

    @property
    def label_en(self) -> str:
        """英文标签 / English label."""
        labels = {
            SecurityLevel.NORMAL: "Normal",
            SecurityLevel.ELEVATED: "Elevated",
            SecurityLevel.HIGH: "High",
            SecurityLevel.MAXIMUM: "Maximum",
        }
        return labels[self]

    @property
    def label_zh(self) -> str:
        """中文标签 / Chinese label."""
        labels = {
            SecurityLevel.NORMAL: "常规",
            SecurityLevel.ELEVATED: "提升",
            SecurityLevel.HIGH: "高",
            SecurityLevel.MAXIMUM: "最高",
        }
        return labels[self]

    def meets_requirement(self, required: SecurityLevel) -> bool:
        """检查是否满足要求等级。

        Check whether this level meets the required level.

        Args:
            required: 要求的安全等级。/ Required security level.

        Returns:
            若当前等级不低于要求等级则返回 True。
            True if current level is not lower than required.
        """
        return self >= required

    def escalate(self) -> SecurityLevel:
        """提升一级 / Escalate one level.

        Returns:
            提升一级后的安全等级，已达最高则保持不变。
            Security level one step higher; unchanged if
            already max.
        """
        if self == SecurityLevel.MAXIMUM:
            return self
        return SecurityLevel(self.value + 1)

    def de_escalate(self) -> SecurityLevel:
        """降级一级 / De-escalate one level.

        Returns:
            降级一级后的安全等级，已达最低则保持不变。
            Security level one step lower; unchanged if
            already min.
        """
        if self == SecurityLevel.NORMAL:
            return self
        return SecurityLevel(self.value - 1)

    @classmethod
    def from_string(cls, value: str) -> SecurityLevel:
        """从字符串解析 / Parse from string.

        Args:
            value: 等级字符串(normal/elevated/high/maximum)。
                Level string (normal/elevated/high/maximum).

        Returns:
            对应的安全等级。
            Corresponding security level.
        """
        mapping = {
            "normal": cls.NORMAL,
            "elevated": cls.ELEVATED,
            "high": cls.HIGH,
            "maximum": cls.MAXIMUM,
        }
        return mapping[value.lower()]
