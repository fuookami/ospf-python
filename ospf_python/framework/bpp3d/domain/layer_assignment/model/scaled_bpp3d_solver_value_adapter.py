"""缩放求解器值适配器 / Scaled solver value adapter.

在适配过程中应用缩放因子。
Applies scaling factors during value adaptation.
"""

from __future__ import annotations

import abc


class ScaledBpp3dSolverValueAdapter(abc.ABC):
    """缩放求解器值适配器 / Scaled solver value adapter.

    在求解器值与业务值之间应用缩放转换。
    Applies scaling conversion between solver values and
    business values.
    """

    @abc.abstractmethod
    def adapt_value(
        self,
        raw_value: object,
        scale_factor: float,
    ) -> object:
        """适配原始值（带缩放） / Adapt raw value (scaled).

        Args:
            raw_value: 求解器原始值 / The raw solver value.
            scale_factor: 缩放因子 / The scale factor.

        Returns:
            缩放后的业务值 / The scaled business value.
        """
        ...

    @abc.abstractmethod
    def reverse_adapt(
        self,
        value: object,
        scale_factor: float,
    ) -> object:
        """反向适配（带缩放） / Reverse adapt (scaled).

        Args:
            value: 业务值 / The business value.
            scale_factor: 缩放因子 / The scale factor.

        Returns:
            缩放后的求解器值 / The scaled solver value.
        """
        ...
