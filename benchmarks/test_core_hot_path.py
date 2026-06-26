"""Core MetaModel 注册热路径基准 / Core MetaModel registration hot path benchmark.

对齐 Kotlin CoreHotPathBenchmark: MetaModel 变量/约束/目标注册性能。
Aligned to Kotlin CoreHotPathBenchmark: MetaModel variable/constraint/objective
registration performance.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ospf_python.core.model.basic.registration_status import (
    RegistrationStatus,
)
from ospf_python.core.model.mechanism.meta_model import MetaModel

if TYPE_CHECKING:
    from pytest_benchmark.fixture import BenchmarkFixture


@pytest.mark.benchmark
class TestCoreHotPath:
    """Core MetaModel 注册热路径基准。

    Core MetaModel registration hot path benchmarks.
    """

    def test_register_variables(
        self,
        benchmark: BenchmarkFixture,
        core_dataset: dict[str, int],
    ) -> None:
        """变量注册热路径 / Variable registration hot path.

        对齐 Kotlin CoreHotPathBenchmark.registerVariables。
        Aligned to Kotlin CoreHotPathBenchmark.registerVariables.

        Args:
            benchmark: pytest-benchmark fixture.
            core_dataset: 数据集规模 / Dataset scale.
        """
        n_vars = core_dataset["variables"]

        def _run() -> MetaModel:
            model = MetaModel(name="bench")
            for i in range(n_vars):
                result = model.register_variable(
                    name=f"x_{i}",
                    variable=object(),
                )
                assert result is RegistrationStatus.REGISTERED
            return model

        benchmark(_run)

    def test_register_constraints(
        self,
        benchmark: BenchmarkFixture,
        core_dataset: dict[str, int],
    ) -> None:
        """约束注册热路径 / Constraint registration hot path.

        对齐 Kotlin CoreHotPathBenchmark.registerConstraints。
        Aligned to Kotlin CoreHotPathBenchmark.registerConstraints.

        Args:
            benchmark: pytest-benchmark fixture.
            core_dataset: 数据集规模 / Dataset scale.
        """
        n_vars = core_dataset["variables"]
        n_constraints = core_dataset["constraints"]

        def _run() -> MetaModel:
            model = MetaModel(name="bench")
            for i in range(n_vars):
                model.register_variable(name=f"x_{i}", variable=object())
            for i in range(n_constraints):
                model.register_constraint(
                    name=f"c_{i}",
                    constraint=object(),
                )
            return model

        benchmark(_run)

    def test_register_objectives(
        self,
        benchmark: BenchmarkFixture,
        core_dataset: dict[str, int],
    ) -> None:
        """目标函数注册热路径 / Objective registration hot path.

        对齐 Kotlin CoreHotPathBenchmark.registerObjectives。
        Aligned to Kotlin CoreHotPathBenchmark.registerObjectives.

        Args:
            benchmark: pytest-benchmark fixture.
            core_dataset: 数据集规模 / Dataset scale.
        """
        n_objectives = core_dataset["objectives"]

        def _run() -> MetaModel:
            model = MetaModel(name="bench")
            for i in range(n_objectives):
                result = model.register_objective(
                    name=f"obj_{i}",
                    objective=object(),
                )
                assert result is RegistrationStatus.REGISTERED
            return model

        benchmark(_run)
