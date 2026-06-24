"""COPT 求解器回调处理器 / COPT solver callback handler.

管理 COPT 求解过程中的回调事件。
Manages callback events during COPT solving.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import coptpy


@dataclass(frozen=True)
class CoptSolverCallBack:
    """COPT 求解器回调处理器 / COPT solver callback
    handler.

    冻结数据类，封装 COPT 回调函数的注册和管理逻辑。
    Frozen dataclass encapsulating callback registration
    and management logic for COPT.

    Attributes:
        callbacks: 已注册的回调映射 / Registered callback
            mapping.
    """

    callbacks: dict[str, object] = field(
        default_factory=dict,
    )
    """已注册的回调映射 / Registered callback mapping."""

    def register_lazy_constraint(
        self,
        name: str,
        callback: object,
    ) -> CoptSolverCallBack:
        """注册惰性约束回调 / Register lazy constraint
        callback.

        Args:
            name: 回调名称 / Callback name.
            callback: 回调函数 / Callback function.

        Returns:
            包含新回调的新实例 / New instance with the
            added callback.
        """
        new_callbacks = {
            **self.callbacks,
            name: callback,
        }
        return CoptSolverCallBack(
            callbacks=new_callbacks,
        )

    def register_heuristic(
        self,
        name: str,
        callback: object,
    ) -> CoptSolverCallBack:
        """注册启发式回调 / Register heuristic callback.

        Args:
            name: 回调名称 / Callback name.
            callback: 回调函数 / Callback function.

        Returns:
            包含新回调的新实例 / New instance with the
            added callback.
        """
        new_callbacks = {
            **self.callbacks,
            name: callback,
        }
        return CoptSolverCallBack(
            callbacks=new_callbacks,
        )

    def register_cutting_plane(
        self,
        name: str,
        callback: object,
    ) -> CoptSolverCallBack:
        """注册割平面回调 / Register cutting plane
        callback.

        Args:
            name: 回调名称 / Callback name.
            callback: 回调函数 / Callback function.

        Returns:
            包含新回调的新实例 / New instance with the
            added callback.
        """
        new_callbacks = {
            **self.callbacks,
            name: callback,
        }
        return CoptSolverCallBack(
            callbacks=new_callbacks,
        )

    def apply_to_model(
        self,
        model: coptpy.Model,
    ) -> None:
        """将回调应用到模型 / Apply callbacks to model.

        Args:
            model: coptpy 模型 / The coptpy model.
        """
        for _name, cb in self.callbacks.items():
            if callable(cb):
                model._callback = cb

    @property
    def has_callbacks(self) -> bool:
        """是否有已注册的回调 / Whether callbacks are
        registered.

        Returns:
            有回调时返回 True / True when callbacks exist.
        """
        return len(self.callbacks) > 0

    @property
    def callback_count(self) -> int:
        """已注册回调数量 / Number of registered callbacks.

        Returns:
            回调数量 / Callback count.
        """
        return len(self.callbacks)
