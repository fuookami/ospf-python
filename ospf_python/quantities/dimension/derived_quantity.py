"""导出量。/ Derived quantity.

由基本量纲组合而成的物理量。
Physical quantity composed of fundamental dimensions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.quantities.dimension.dimensions import (
        Dimensions,
    )


@dataclass(frozen=True)
class DerivedQuantity:
    """导出量。/ Derived quantity.

    由基本量纲组合定义的物理量。
    Physical quantity defined by combination
    of fundamental dimensions.

    Attributes:
        name: 量名称。/ Quantity name.
        dimensions: 量纲。/ Dimensions.
    """

    name: str
    dimensions: Dimensions
