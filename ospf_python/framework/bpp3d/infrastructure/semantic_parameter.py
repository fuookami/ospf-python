"""语义参数 / Semantic parameter.

BPP3D 中具有业务语义的参数定义。
Business-semantic parameter definition in BPP3D.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticParameter:
    """语义参数 / Semantic parameter.

    描述具有业务含义的模型参数。
    Describes model parameters with business semantics.

    Attributes:
        name: 参数名称 / Parameter name.
        value: 参数值 / Parameter value.
        description: 参数描述 / Parameter description.
    """

    name: str
    """参数名称 / Parameter name."""

    value: float
    """参数值 / Parameter value."""

    description: str
    """参数描述 / Parameter description."""

    @staticmethod
    def create(
        *,
        name: str,
        value: float,
        description: str = "",
    ) -> SemanticParameter:
        """创建语义参数 / Create semantic parameter.

        Args:
            name: 参数名称 / Parameter name.
            value: 参数值 / Parameter value.
            description: 参数描述，默认空 /
                Description, default empty.

        Returns:
            语义参数实例 / SemanticParameter instance.
        """
        return SemanticParameter(
            name=name,
            value=value,
            description=description,
        )
