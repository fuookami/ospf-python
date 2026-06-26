"""Demo 15 — 求解器配置 / Solver Configuration.

演示不同求解器的配置选项和参数设置。
Demonstrates solver configuration options and parameter settings.
"""

from __future__ import annotations

from ospf_python.core.solver.solve_options import (
    SolveOptions,
)


def run() -> None:
    """运行 Demo 15 / Run Demo 15."""
    options = SolveOptions()
    print(f"Time limit: {options.time_limit}s")
    print(f"Verbose: {options.verbose}")
    print(f"Seed: {options.seed}")
    print(f"Threads: {options.threads}")
    print("Demo 15 completed: solver configuration demonstrated")


if __name__ == "__main__":
    run()
