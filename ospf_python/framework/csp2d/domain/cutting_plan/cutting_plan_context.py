"""切割方案上下文 / Cutting plan context.

CSP2D 切割方案域的注册表，管理切割方案。
Registry for the CSP2D cutting plan domain, managing cutting plans.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python.framework.csp2d.domain.cutting_plan.model.cutting_plan import (
        CuttingPlan,
    )


class CuttingPlanContext:
    """切割方案上下文 / Cutting plan context.

    维护切割方案注册表，提供注册、查询和管理功能。
    在 CSP2D 中充当切割方案的中央仓库。
    Maintains the cutting plan registry, providing registration,
    query, and management functions. Acts as the central repository
    for cutting plans in CSP2D.

    Attributes:
        _plans: 内部方案字典 / Internal plan dictionary.
    """

    def __init__(self) -> None:
        """初始化空切割方案上下文 / Initialize empty cutting plan context."""
        self._plans: dict[str, CuttingPlan] = {}

    def register(
        self,
        plan: CuttingPlan,
    ) -> Result[None, str, Err[str]]:
        """注册切割方案 / Register a cutting plan.

        如果方案键已存在，返回失败结果。
        Returns failure if the plan key already exists.

        Args:
            plan: 要注册的方案 / Plan to register.

        Returns:
            注册结果 / Registration result.
        """
        if plan.plan_key in self._plans:
            return Failed(
                Err(
                    _code=ErrorCode.ALREADY_EXIST,
                    _message=(
                        f"方案已存在: {plan.plan_key} / "
                        f"Plan already exists: {plan.plan_key}"
                    ),
                )
            )
        self._plans[plan.plan_key] = plan
        return Ok(None)

    def unregister(
        self,
        plan_key: str,
    ) -> Result[None, str, Err[str]]:
        """注销切割方案 / Unregister a cutting plan.

        Args:
            plan_key: 方案键 / Plan key.

        Returns:
            注销结果 / Unregistration result.
        """
        if plan_key not in self._plans:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(f"方案未找到: {plan_key} / Plan not found: {plan_key}"),
                )
            )
        del self._plans[plan_key]
        return Ok(None)

    def get(self, key: str) -> CuttingPlan | None:
        """获取切割方案 / Get a cutting plan.

        Args:
            key: 方案键 / Plan key.

        Returns:
            方案实例或 None / Plan instance or None.
        """
        return self._plans.get(key)

    def get_or_error(
        self,
        key: str,
    ) -> Result[CuttingPlan, str, Err[str]]:
        """获取方案或返回错误 / Get plan or return error.

        Args:
            key: 方案键 / Plan key.

        Returns:
            包含方案的成功结果或失败结果。
            Success result with plan or failure result.
        """
        plan = self._plans.get(key)
        if plan is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(f"方案未找到: {key} / Plan not found: {key}"),
                )
            )
        return Ok(plan)

    def items(self) -> tuple[CuttingPlan, ...]:
        """获取所有方案 / Get all plans.

        Returns:
            方案元组 / Plan tuple.
        """
        return tuple(self._plans.values())

    def plans_for_material(
        self,
        material_key: str,
    ) -> tuple[CuttingPlan, ...]:
        """获取指定材料的所有方案 / Get all plans for a material.

        Args:
            material_key: 材料键 / Material key.

        Returns:
            该材料的方案元组 / Plan tuple for the material.
        """
        return tuple(p for p in self._plans.values() if p.material_key == material_key)

    def contains(self, key: str) -> bool:
        """检查方案是否存在 / Check if plan exists.

        Args:
            key: 方案键 / Plan key.

        Returns:
            是否存在 / Whether exists.
        """
        return key in self._plans

    @property
    def size(self) -> int:
        """方案数量 / Plan count.

        Returns:
            已注册方案数量 / Number of registered plans.
        """
        return len(self._plans)

    @property
    def is_empty(self) -> bool:
        """是否为空 / Whether empty.

        Returns:
            无注册方案时返回 True。
            True when no plans registered.
        """
        return len(self._plans) == 0

    def clear(self) -> None:
        """清空所有方案 / Clear all plans."""
        self._plans.clear()


class ErrorCode:
    """错误码常量 / Error code constants."""

    ALREADY_EXIST = "ALREADY_EXIST"
    NOT_FOUND = "NOT_FOUND"
