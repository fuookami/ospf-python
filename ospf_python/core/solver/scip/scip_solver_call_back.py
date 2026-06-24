"""SCIP 求解器回调处理器 / SCIP solver callback handler.

管理 SCIP 求解过程中的回调事件。
Manages callback events during SCIP solving.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyscipopt import Model as ScipModel


@dataclass(frozen=True)
class ScipSolverCallBack:
    """SCIP 求解器回调处理器 / SCIP solver callback
    handler.

    冻结数据类，封装 SCIP 回调函数的注册和管理逻辑。
    Frozen dataclass encapsulating callback registration
    and management logic for SCIP.

    Attributes:
        callbacks: 已注册的回调映射 / Registered callback
            mapping.
    """

    callbacks: dict[str, object] = field(
        default_factory=dict,
    )
    """已注册的回调映射 / Registered callback mapping."""

    def register_node_selector(
        self,
        name: str,
        callback: object,
    ) -> ScipSolverCallBack:
        """注册节点选择回调 / Register node selector
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
        return ScipSolverCallBack(
            callbacks=new_callbacks,
        )

    def register_branching_rule(
        self,
        name: str,
        callback: object,
    ) -> ScipSolverCallBack:
        """注册分支规则回调 / Register branching rule
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
        return ScipSolverCallBack(
            callbacks=new_callbacks,
        )

    def register_event_handler(
        self,
        name: str,
        callback: object,
    ) -> ScipSolverCallBack:
        """注册事件处理器回调 / Register event handler
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
        return ScipSolverCallBack(
            callbacks=new_callbacks,
        )

    def apply_to_model(
        self,
        model: ScipModel,
    ) -> None:
        """将回调应用到模型 / Apply callbacks to model.

        Args:
            model: SCIP 模型 / The SCIP model.
        """
        for _name, cb in self.callbacks.items():
            if callable(cb):
                model._callback = cb  # type: ignore[attr-defined]

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
