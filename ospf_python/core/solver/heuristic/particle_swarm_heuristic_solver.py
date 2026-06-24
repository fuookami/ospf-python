"""粒子群启发式求解器 / Particle swarm heuristic solver.

实现粒子群优化 (PSO) 算法的求解器。
Implements a solver using Particle Swarm Optimization
(PSO) algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ospf_python.core.solver.heuristic.iteration import (
    Iteration,
)
from ospf_python.core.solver.heuristic.population import (
    Population,
)
from ospf_python.core.solver.output.solver_output import (
    SolverOutput,
)
from ospf_python.core.solver.output.solver_status import (
    SolverStatus,
)
from ospf_python.core.solver.solver import Solver

if TYPE_CHECKING:
    from ospf_python.core.solver.solve_options import (
        SolveOptions,
    )


@dataclass
class ParticleSwarmHeuristicSolver(Solver):
    """粒子群启发式求解器 / Particle swarm heuristic solver.

    使用粒子群优化算法求解连续优化问题。
    Uses PSO to solve continuous optimization problems.

    Attributes:
        iteration: 迭代控制 / Iteration control.
        population: 种群 / Population.
        inertia: 惯性权重 / Inertia weight.
        cognitive: 认知系数 / Cognitive coefficient.
        social: 社会系数 / Social coefficient.
    """

    iteration: Iteration = field(
        default_factory=lambda: Iteration(
            max_iterations=100,
        ),
    )
    """迭代控制 / Iteration control."""

    population: Population = field(
        default_factory=Population,
    )
    """种群 / Population."""

    inertia: float = 0.7
    """惯性权重 / Inertia weight."""

    cognitive: float = 1.5
    """认知系数 / Cognitive coefficient."""

    social: float = 1.5
    """社会系数 / Social coefficient."""

    @property
    def name(self) -> str:
        """求解器名称 / Solver name.

        Returns:
            'particle_swarm' / 'particle_swarm'.
        """
        return "particle_swarm"

    def solve(
        self,
        model: object,
        *,
        options: SolveOptions | None = None,
    ) -> SolverOutput:
        """求解模型 / Solve the model.

        Args:
            model: 优化模型 / The optimization model.
            options: 求解选项 / Solve options.

        Returns:
            求解输出 / Solver output.
        """
        return SolverOutput(status=SolverStatus.UNKNOWN)
