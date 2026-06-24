"""CSP1D 问题构建器 / CSP1D problem builder."""

from __future__ import annotations

from ospf_python.framework.csp1d.application.model.csp1d_problem import (
    Csp1dProblem,
)
from ospf_python.framework.csp1d.domain.material.model.machine import (
    Machine,
)
from ospf_python.framework.csp1d.domain.material.model.material import (
    Material,
)
from ospf_python.framework.csp1d.domain.material.model.product import (
    Product,
)
from ospf_python.framework.csp1d.domain.material.model.product_demand import (
    ProductDemand,
)


class Csp1dProblemBuilder:
    """一维切割股问题构建器 / 1D cutting stock problem builder.

    通过逐步添加材料、产品和需求来构建 Csp1dProblem 实例。
    Builds a Csp1dProblem instance by progressively adding
    materials, products, and demands.

    Attributes:
        _materials: 已添加的材料列表 / Added materials list.
        _products: 已添加的产品列表 / Added products list.
        _machines: 已添加的机器列表 / Added machines list.
        _demands: 已添加的需求列表 / Added demands list.
    """

    def __init__(self) -> None:
        """初始化空构建器 / Initialize empty builder."""
        self._materials: list[Material] = []
        self._products: list[Product] = []
        self._machines: list[Machine] = []
        self._demands: list[ProductDemand] = []

    def add_material(
        self,
        *,
        name: str,
        width: float,
        length: float,
        cost: float,
    ) -> Csp1dProblemBuilder:
        """添加原材料 / Add a raw material.

        Args:
            name: 材料名称 / Material name.
            width: 材料宽度 / Material width.
            length: 材料长度 / Material length.
            cost: 材料单价 / Material unit cost.

        Returns:
            构建器自身（链式调用） / Builder itself (chaining).
        """
        self._materials.append(
            Material(
                name=name,
                width=width,
                length=length,
                cost=cost,
            )
        )
        return self

    def add_product(
        self,
        *,
        name: str,
        width: float,
        length: float,
        demand: int,
    ) -> Csp1dProblemBuilder:
        """添加产品规格 / Add a product specification.

        Args:
            name: 产品名称 / Product name.
            width: 产品宽度 / Product width.
            length: 产品长度 / Product length.
            demand: 需求量 / Demand quantity.

        Returns:
            构建器自身（链式调用） / Builder itself (chaining).
        """
        self._products.append(
            Product(
                name=name,
                width=width,
                length=length,
                demand=demand,
            )
        )
        return self

    def add_machine(
        self,
        *,
        name: str,
        max_width: float,
        cut_loss: float,
    ) -> Csp1dProblemBuilder:
        """添加切割机器 / Add a cutting machine.

        Args:
            name: 机器名称 / Machine name.
            max_width: 最大加工宽度 / Maximum processing width.
            cut_loss: 切割损耗 / Width lost per cut.

        Returns:
            构建器自身（链式调用） / Builder itself (chaining).
        """
        self._machines.append(
            Machine(
                name=name,
                max_width=max_width,
                cut_loss=cut_loss,
            )
        )
        return self

    def add_demand(
        self,
        *,
        product: str,
        quantity: int,
    ) -> Csp1dProblemBuilder:
        """添加产品需求 / Add a product demand.

        Args:
            product: 产品名称 / Product name.
            quantity: 需求量 / Demand quantity.

        Returns:
            构建器自身（链式调用） / Builder itself (chaining).
        """
        self._demands.append(
            ProductDemand(
                product=product,
                quantity=quantity,
            )
        )
        return self

    def build(self) -> Csp1dProblem:
        """构建问题实例 / Build the problem instance.

        Returns:
            构建好的问题 / Built problem.
        """
        return Csp1dProblem(
            materials=tuple(self._materials),
            products=tuple(self._products),
            machines=tuple(self._machines),
            demands=tuple(self._demands),
        )
