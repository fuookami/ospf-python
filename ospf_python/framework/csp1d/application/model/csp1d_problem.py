"""CSP1D 问题模型 / CSP1D problem model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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


@dataclass(frozen=True)
class Csp1dProblem:
    """一维切割股问题定义 / 1D cutting stock problem definition.

    聚合求解一维切割股问题所需的全部输入数据。
    Aggregates all input data required to solve a
    1D cutting stock problem.

    Attributes:
        materials: 可用原材料元组 / Tuple of available materials.
        products: 产品规格元组 / Tuple of product specifications.
        machines: 可用机器元组 / Tuple of available machines.
        demands: 产品需求元组 / Tuple of product demands.
    """

    materials: tuple[Material, ...]
    products: tuple[Product, ...]
    machines: tuple[Machine, ...]
    demands: tuple[ProductDemand, ...]
