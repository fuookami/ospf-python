"""框架模型模块 / Framework model module.

提供管道和影子价格等通用模型组件。
Provides common model components such as pipelines
and shadow prices.
"""

from ospf_python.framework.model.pipeline import Pipeline
from ospf_python.framework.model.shadow_price import ShadowPrice

__all__ = [
    "Pipeline",
    "ShadowPrice",
]
