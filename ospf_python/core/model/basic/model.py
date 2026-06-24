"""模型抽象基类 / Model abstract base class.

定义所有优化模型的公共接口。
Defines the common interface for all optimization models.
"""

from __future__ import annotations

import abc


class Model(abc.ABC):
    """优化模型抽象基类 / Abstract base class for optimization models.

    所有具体模型类型必须实现名称、添加约束和添加目标函数的接口。
    All concrete model types must implement the interface for
    naming, adding constraints, and adding objectives.

    Attributes:
        name: 模型名称 / The model name.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """获取模型名称 / Get the model name."""
        ...

    @abc.abstractmethod
    def add_constraint(self, constraint: object) -> None:
        """添加约束到模型 / Add a constraint to the model.

        Args:
            constraint: 要添加的约束对象 / The constraint object
                to add.
        """
        ...

    @abc.abstractmethod
    def add_objective(self, objective: object) -> None:
        """添加目标函数到模型 / Add an objective to the model.

        Args:
            objective: 要添加的目标函数对象 / The objective
                object to add.
        """
        ...
