"""Gantt scheduling task compilation model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TaskCompilationModel:
    """Gantt scheduling task compilation model."""

    name: str = "task_compilation_model"
    model_name: str = ""
    aggregation: Any = None
    _variables: tuple[Any, ...] = ()
    _constraints: tuple[Any, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)

    def with_config(self, config: Any) -> TaskCompilationModel:
        """创建不同配置的模型副本。/ Create copy with config."""
        return TaskCompilationModel(
            name=self.name,
            model_name=self.model_name,
            aggregation=self.aggregation,
            _variables=self._variables,
            _constraints=self._constraints,
        )

    def add_variable(
        self,
        variable: Any,
    ) -> TaskCompilationModel:
        """添加决策变量。/ Add decision variable."""
        return TaskCompilationModel(
            name=self.name,
            model_name=self.model_name,
            aggregation=self.aggregation,
            _variables=(*self._variables, variable),
            _constraints=self._constraints,
        )

    def add_constraint(
        self,
        constraint: Any,
    ) -> TaskCompilationModel:
        """添加约束。/ Add constraint."""
        return TaskCompilationModel(
            name=self.name,
            model_name=self.model_name,
            aggregation=self.aggregation,
            _variables=self._variables,
            _constraints=(*self._constraints, constraint),
        )
