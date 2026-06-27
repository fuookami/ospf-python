"""产品上下文 / Product context.

CSP2D 产品域的注册表，管理形状和需求。
Registry for the CSP2D product domain, managing shapes and demands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok, Result

if TYPE_CHECKING:
    from ospf_python.framework.csp2d.domain.product.model.demand import Demand
    from ospf_python.framework.csp2d.domain.product.model.shape import Shape


class ProductContext:
    """产品上下文 / Product context.

    维护形状和需求注册表，提供注册、查询和管理功能。
    在 CSP2D 中充当产品的中央仓库。
    Maintains shape and demand registries, providing registration,
    query, and management functions. Acts as the central repository
    for products in CSP2D.

    Attributes:
        _shapes: 内部形状字典 / Internal shape dictionary.
        _demands: 内部需求字典 / Internal demand dictionary.
    """

    def __init__(self) -> None:
        """初始化空产品上下文 / Initialize empty product context."""
        self._shapes: dict[str, Shape] = {}
        self._demands: dict[str, Demand] = {}

    def register_shape(
        self,
        shape: Shape,
    ) -> Result[None, str, Err[str]]:
        """注册形状 / Register a shape.

        如果形状键已存在，返回失败结果。
        Returns failure if the shape key already exists.

        Args:
            shape: 要注册的形状 / Shape to register.

        Returns:
            注册结果 / Registration result.
        """
        if shape.shape_key in self._shapes:
            return Failed(
                Err(
                    _code=ErrorCode.ALREADY_EXIST,
                    _message=(
                        f"形状已存在: {shape.shape_key} / "
                        f"Shape already exists: {shape.shape_key}"
                    ),
                )
            )
        self._shapes[shape.shape_key] = shape
        return Ok(None)

    def register_demand(
        self,
        demand: Demand,
    ) -> Result[None, str, Err[str]]:
        """注册需求 / Register a demand.

        如果需求键已存在，返回失败结果。
        Returns failure if the demand key already exists.

        Args:
            demand: 要注册的需求 / Demand to register.

        Returns:
            注册结果 / Registration result.
        """
        if demand.demand_key in self._demands:
            return Failed(
                Err(
                    _code=ErrorCode.ALREADY_EXIST,
                    _message=(
                        f"需求已存在: {demand.demand_key} / "
                        f"Demand already exists: {demand.demand_key}"
                    ),
                )
            )
        self._demands[demand.demand_key] = demand
        return Ok(None)

    def get_shape(self, key: str) -> Shape | None:
        """获取形状 / Get a shape.

        Args:
            key: 形状键 / Shape key.

        Returns:
            形状实例或 None / Shape instance or None.
        """
        return self._shapes.get(key)

    def get_shape_or_error(
        self,
        key: str,
    ) -> Result[Shape, str, Err[str]]:
        """获取形状或返回错误 / Get shape or return error.

        Args:
            key: 形状键 / Shape key.

        Returns:
            包含形状的成功结果或失败结果。
            Success result with shape or failure result.
        """
        shape = self._shapes.get(key)
        if shape is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(f"形状未找到: {key} / Shape not found: {key}"),
                )
            )
        return Ok(shape)

    def get_demand(self, key: str) -> Demand | None:
        """获取需求 / Get a demand.

        Args:
            key: 需求键 / Demand key.

        Returns:
            需求实例或 None / Demand instance or None.
        """
        return self._demands.get(key)

    def get_demand_or_error(
        self,
        key: str,
    ) -> Result[Demand, str, Err[str]]:
        """获取需求或返回错误 / Get demand or return error.

        Args:
            key: 需求键 / Demand key.

        Returns:
            包含需求的成功结果或失败结果。
            Success result with demand or failure result.
        """
        demand = self._demands.get(key)
        if demand is None:
            return Failed(
                Err(
                    _code=ErrorCode.NOT_FOUND,
                    _message=(f"需求未找到: {key} / Demand not found: {key}"),
                )
            )
        return Ok(demand)

    def shapes(self) -> tuple[Shape, ...]:
        """获取所有形状 / Get all shapes.

        Returns:
            形状元组 / Shape tuple.
        """
        return tuple(self._shapes.values())

    def demands(self) -> tuple[Demand, ...]:
        """获取所有需求 / Get all demands.

        Returns:
            需求元组 / Demand tuple.
        """
        return tuple(self._demands.values())

    def demands_for_shape(
        self,
        shape_key: str,
    ) -> tuple[Demand, ...]:
        """获取指定形状的所有需求 / Get all demands for a shape.

        Args:
            shape_key: 形状键 / Shape key.

        Returns:
            该形状的需求元组 / Demand tuple for the shape.
        """
        return tuple(d for d in self._demands.values() if d.shape_key == shape_key)

    def contains_shape(self, key: str) -> bool:
        """检查形状是否存在 / Check if shape exists.

        Args:
            key: 形状键 / Shape key.

        Returns:
            是否存在 / Whether exists.
        """
        return key in self._shapes

    def contains_demand(self, key: str) -> bool:
        """检查需求是否存在 / Check if demand exists.

        Args:
            key: 需求键 / Demand key.

        Returns:
            是否存在 / Whether exists.
        """
        return key in self._demands

    @property
    def shape_count(self) -> int:
        """形状数量 / Shape count.

        Returns:
            已注册形状数量 / Number of registered shapes.
        """
        return len(self._shapes)

    @property
    def demand_count(self) -> int:
        """需求数量 / Demand count.

        Returns:
            已注册需求数量 / Number of registered demands.
        """
        return len(self._demands)

    @property
    def size(self) -> int:
        """产品总数量 / Total product count.

        Returns:
            形状和需求总数 / Total shapes and demands.
        """
        return len(self._shapes) + len(self._demands)

    @property
    def is_empty(self) -> bool:
        """是否为空 / Whether empty.

        Returns:
            无注册产品时返回 True。
            True when no products registered.
        """
        return len(self._shapes) == 0 and len(self._demands) == 0

    def clear(self) -> None:
        """清空所有产品 / Clear all products."""
        self._shapes.clear()
        self._demands.clear()


class ErrorCode:
    """错误码常量 / Error code constants."""

    ALREADY_EXIST = "ALREADY_EXIST"
    NOT_FOUND = "NOT_FOUND"
