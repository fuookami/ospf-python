"""量域。/ Quantity domain.

相关物理量的分组。
Grouping of related physical quantities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.quantities.dimension.derived_quantity import (
        DerivedQuantity,
    )


@dataclass(frozen=True)
class QuantityDomain:
    """量域，将相关导出量分组管理。

    Quantity domain grouping related derived quantities.

    Attributes:
        name: 域名称。/ Domain name.
        quantities: 包含的导出量。
            Contained derived quantities.
    """

    name: str
    quantities: tuple[DerivedQuantity, ...] = field(default_factory=tuple)
