"""三维装箱求解器值适配器 / 3D bin packing solver value adapter.

将求解器变量值适配为业务层数据。
Adapts solver variable values to business-layer data.
"""

from __future__ import annotations

import abc


class Bpp3dSolverValueAdapter(abc.ABC):
    """三维装箱求解器值适配器 / 3D bin packing solver value adapter.

    提供求解器值到业务对象的转换接口。
    Provides conversion interface from solver values to
    business objects.
    """

    @abc.abstractmethod
    def adapt_value(self, raw_value: object) -> object:
        """适配原始值 / Adapt raw value.

        Args:
            raw_value: 求解器原始值 / The raw solver value.

        Returns:
            适配后的业务值 / The adapted business value.
        """
        ...

    @abc.abstractmethod
    def reverse_adapt(self, value: object) -> object:
        """反向适配 / Reverse adapt.

        Args:
            value: 业务值 / The business value.

        Returns:
            求解器值 / The solver value.
        """
        ...
