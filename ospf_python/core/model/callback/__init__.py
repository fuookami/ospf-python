"""ospf_python.core.model.callback

回调模型组件 / Callback model components.

提供求解器回调模型和接口定义。
Provides solver callback model and interface definitions.
"""

from ospf_python.core.model.callback.call_back_model import (
    CallBackModel,
)
from ospf_python.core.model.callback.call_back_model_interface import (
    CallBackModelInterface,
)

__all__ = [
    "CallBackModel",
    "CallBackModelInterface",
]
