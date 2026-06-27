"""材料上下文 / Material context.

CSP2D 材料域的注册表，管理板材和卷材。
Registry for the CSP2D material domain, managing sheets and strips.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python.framework.csp2d.domain.material.model.sheet import (
        Sheet,
    )
    from ospf_python.framework.csp2d.domain.material.model.strip import (
        Strip,
    )


class MaterialContext:
    """材料上下文 / Material context.

    维护板材和卷材注册表，提供注册、查询和管理功能。
    在 CSP2D 中充当材料的中央仓库。
    Maintains sheet and strip registries, providing registration,
    query, and management functions. Acts as the central repository
    for materials in CSP2D.

    Attributes:
        _sheets: 内部板材字典 / Internal sheet dictionary.
        _strips: 内部卷材字典 / Internal strip dictionary.
    """

    def __init__(self) -> None:
        """初始化空材料上下文 / Initialize empty material context."""
        self._sheets: dict[str, Sheet] = {}
        self._strips: dict[str, Strip] = {}

    def register_sheet(
        self,
        sheet: Sheet,
    ) -> Result[None, str, Err[str]]:
        """注册板材 / Register a sheet.

        如果板材名称已存在，返回失败结果。
        Returns failure if the sheet name already exists.

        Args:
            sheet: 要注册的板材 / Sheet to register.

        Returns:
            注册结果 / Registration result.
        """
        if sheet.name in self._sheets:
            return Failed(
                Err(
                    _code=ErrorCode.ALREADY_EXIST,
                    _message=(
                        f"板材已存在: {sheet.name} / Sheet already exists: {sheet.name}"
                    ),
                )
            )
        self._sheets[sheet.name] = sheet
        return Ok(None)

    def register_strip(
        self,
        strip: Strip,
    ) -> Result[None, str, Err[str]]:
        """注册卷材 / Register a strip.

        如果卷材名称已存在，返回失败结果。
        Returns failure if the strip name already exists.

        Args:
            strip: 要注册的卷材 / Strip to register.

        Returns:
            注册结果 / Registration result.
        """
        if strip.name in self._strips:
            return Failed(
                Err(
                    _code=ErrorCode.ALREADY_EXIST,
                    _message=(
                        f"卷材已存在: {strip.name} / Strip already exists: {strip.name}"
                    ),
                )
            )
        self._strips[strip.name] = strip
        return Ok(None)

    def get_sheet(self, name: str) -> Sheet | None:
        """获取板材 / Get a sheet.

        Args:
            name: 板材名称 / Sheet name.

        Returns:
            板材实例或 None / Sheet instance or None.
        """
        return self._sheets.get(name)

    def get_sheet_or_error(
        self,
        name: str,
    ) -> Result[Sheet, str, Err[str]]:
        """获取板材或返回错误 / Get sheet or return error.

        Args:
            name: 板材名称 / Sheet name.

        Returns:
            包含板材的成功结果或失败结果。
            Success result with sheet or failure result.
        """
        sheet = self._sheets.get(name)
        if sheet is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(f"板材未找到: {name} / Sheet not found: {name}"),
                )
            )
        return Ok(sheet)

    def get_strip(self, name: str) -> Strip | None:
        """获取卷材 / Get a strip.

        Args:
            name: 卷材名称 / Strip name.

        Returns:
            卷材实例或 None / Strip instance or None.
        """
        return self._strips.get(name)

    def get_strip_or_error(
        self,
        name: str,
    ) -> Result[Strip, str, Err[str]]:
        """获取卷材或返回错误 / Get strip or return error.

        Args:
            name: 卷材名称 / Strip name.

        Returns:
            包含卷材的成功结果或失败结果。
            Success result with strip or failure result.
        """
        strip = self._strips.get(name)
        if strip is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(f"卷材未找到: {name} / Strip not found: {name}"),
                )
            )
        return Ok(strip)

    def sheets(self) -> tuple[Sheet, ...]:
        """获取所有板材 / Get all sheets.

        Returns:
            板材元组 / Sheet tuple.
        """
        return tuple(self._sheets.values())

    def strips(self) -> tuple[Strip, ...]:
        """获取所有卷材 / Get all strips.

        Returns:
            卷材元组 / Strip tuple.
        """
        return tuple(self._strips.values())

    def items(self) -> tuple[Sheet | Strip, ...]:
        """获取所有材料 / Get all materials.

        Returns:
            板材和卷材的合并元组 / Combined tuple of sheets and strips.
        """
        return (*self._sheets.values(), *self._strips.values())

    def contains_sheet(self, name: str) -> bool:
        """检查板材是否存在 / Check if sheet exists.

        Args:
            name: 板材名称 / Sheet name.

        Returns:
            是否存在 / Whether exists.
        """
        return name in self._sheets

    def contains_strip(self, name: str) -> bool:
        """检查卷材是否存在 / Check if strip exists.

        Args:
            name: 卷材名称 / Strip name.

        Returns:
            是否存在 / Whether exists.
        """
        return name in self._strips

    @property
    def sheet_count(self) -> int:
        """板材数量 / Sheet count.

        Returns:
            已注册板材数量 / Number of registered sheets.
        """
        return len(self._sheets)

    @property
    def strip_count(self) -> int:
        """卷材数量 / Strip count.

        Returns:
            已注册卷材数量 / Number of registered strips.
        """
        return len(self._strips)

    @property
    def size(self) -> int:
        """材料总数量 / Total material count.

        Returns:
            板材和卷材总数 / Total sheets and strips.
        """
        return len(self._sheets) + len(self._strips)

    @property
    def is_empty(self) -> bool:
        """是否为空 / Whether empty.

        Returns:
            无注册材料时返回 True。
            True when no materials registered.
        """
        return len(self._sheets) == 0 and len(self._strips) == 0

    def clear(self) -> None:
        """清空所有材料 / Clear all materials."""
        self._sheets.clear()
        self._strips.clear()


# ErrorCode 内联常量 / Inline error code constants
# 避免循环导入，直接使用字符串错误码。
# Avoid circular imports, use string error codes directly.
class ErrorCode:
    """错误码常量 / Error code constants."""

    ALREADY_EXIST = "ALREADY_EXIST"
    NOT_FOUND = "NOT_FOUND"
