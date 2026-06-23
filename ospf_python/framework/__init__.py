"""Framework module.

Provides shared abstractions for domain frameworks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, unique
from typing import TypeVar

from ospf_python.core.model import MetaModel, Solution
from ospf_python.core.solver import Solver, SolverConfig, SolverOutput
from ospf_python.utils.result import Ok, Result

V = TypeVar("V")


@unique
class LogLevel(Enum):
    """Log level.

    日志级别。
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Logger(ABC):
    """Logger interface.

    日志接口。
    """

    @abstractmethod
    def log(self, level: LogLevel, message: str) -> None:
        """Log a message."""
        ...

    def debug(self, message: str) -> None:
        """Log debug message."""
        self.log(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        """Log info message."""
        self.log(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self.log(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        """Log error message."""
        self.log(LogLevel.ERROR, message)


class ConsoleLogger(Logger):
    """Console logger.

    控制台日志。
    """

    def log(self, level: LogLevel, message: str) -> None:
        """Log to console."""
        print(f"[{level.value.upper()}] {message}")


@dataclass(frozen=True, slots=True)
class FrameworkConfig:
    """Framework configuration.

    框架配置。
    """

    solver_name: str = "mock"
    time_limit: float = 3600.0
    verbose: bool = False


class FrameworkModel(ABC):
    """Framework model interface.

    框架模型接口。
    """

    @abstractmethod
    def build_meta_model(self) -> MetaModel:
        """Build the MetaModel."""
        ...

    @abstractmethod
    def extract_solution(self, solution: Solution) -> object:
        """Extract domain solution from solver solution."""
        ...


class FrameworkSolver(ABC):
    """Framework solver interface.

    框架求解器接口。
    """

    @abstractmethod
    def solve(
        self, model: FrameworkModel, config: FrameworkConfig | None = None
    ) -> Result[V]:
        """Solve the model."""
        ...


class SimpleFrameworkSolver(FrameworkSolver):
    """Simple framework solver.

    简单框架求解器。
    """

    def __init__(self, solver: Solver, logger: Logger | None = None) -> None:
        """Initialize.

        Args:
            solver: Core solver.
            logger: Logger.
        """
        self._solver = solver
        self._logger = logger or ConsoleLogger()

    def solve(
        self, model: FrameworkModel, config: FrameworkConfig | None = None
    ) -> Result[V]:
        """Solve the model.

        Args:
            model: Framework model.
            config: Framework configuration.

        Returns:
            Result with domain solution.
        """
        self._logger.info("Building MetaModel...")
        meta_model = model.build_meta_model()

        self._logger.info("Solving...")
        solver_config = SolverConfig(
            time_limit=config.time_limit if config else 3600.0,
        )
        result = self._solver.solve(meta_model, solver_config)

        if result.is_failed():
            self._logger.error("Solver failed")
            return result  # type: ignore[return-value]

        self._logger.info("Extracting solution...")
        solution = Solution(
            objective_value=result.value.objective_value,  # type: ignore[union-attr]
            variable_values=result.value.variable_values,  # type: ignore[union-attr]
            status=result.value.status.value,  # type: ignore[union-attr]
        )
        domain_solution: object = model.extract_solution(solution)
        return Ok(domain_solution)  # type: ignore[arg-type]


class RemoteSolverClient(ABC):
    """Remote solver client interface.

    远程求解器客户端接口。
    """

    @abstractmethod
    def submit(self, model: MetaModel, config: SolverConfig) -> Result[str]:
        """Submit a model for solving."""
        ...

    @abstractmethod
    def get_status(self, job_id: str) -> Result[str]:
        """Get job status."""
        ...

    @abstractmethod
    def get_result(self, job_id: str) -> Result[SolverOutput]:
        """Get job result."""
        ...


class RemoteSolverPort(ABC):
    """Remote solver port interface.

    远程求解器端口接口。
    """

    @abstractmethod
    def solve_remote(
        self, model: MetaModel, config: SolverConfig
    ) -> Result[SolverOutput]:
        """Solve model remotely."""
        ...


class RemoteSolverAdapter(RemoteSolverPort):
    """Remote solver adapter.

    远程求解器适配器。
    """

    def __init__(self, client: RemoteSolverClient) -> None:
        """Initialize.

        Args:
            client: Remote solver client.
        """
        self._client = client

    def solve_remote(
        self, model: MetaModel, config: SolverConfig
    ) -> Result[SolverOutput]:
        """Solve model remotely.

        Args:
            model: MetaModel.
            config: Solver config.

        Returns:
            Result with solver output.
        """
        # Submit job
        job_result = self._client.submit(model, config)
        if job_result.is_failed():
            return job_result  # type: ignore[return-value]

        job_id = job_result.value  # type: ignore[union-attr]

        # Poll for completion (simplified)
        status_result = self._client.get_status(job_id)
        if status_result.is_failed():
            return status_result  # type: ignore[return-value]

        # Get result
        return self._client.get_result(job_id)
