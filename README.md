# ospf-python

Python implementation of the ospf-kotlin optimization framework.

[中文文档](README_ch.md)

## Overview

ospf-python is a comprehensive optimization modeling framework that provides:

- **Core modeling**: MetaModel-based optimization with variable/constraint/objective registration
- **Solver abstraction**: Unified interface for multiple solvers (Gurobi, SCIP, COPT, MindOpt)
- **Domain frameworks**: Pre-built frameworks for:
  - 3D Bin Packing (BPP3D)
  - 1D Cutting Stock (CSP1D)
  - Gantt Scheduling
- **Math library**: Algebra, geometry, symbolic computation, and chaos theory
- **Physical quantities**: Type-safe unit system with dimensional analysis

## Installation

```bash
# Basic installation
uv pip install -e .

# With solver support
uv pip install -e ".[gurobi,scip]"

# Development
uv pip install -e ".[dev]"
```

## Quick Start

```python
from ospf_python.core.model import MetaModel
from ospf_python.core.variable import LinearVariable

# Create a model
model = MetaModel("my_model")

# Add variables
x = model.add_variable("x", lower_bound=0)
y = model.add_variable("y", lower_bound=0)

# Add objective
model.set_objective(x + y, minimize=True)

# Add constraints
model.add_constraint(x + 2 * y >= 10)

# Solve
result = model.solve()
print(f"Optimal value: {result.objective_value}")
```

## Project Structure

```
ospf_python/
├── utils/          # Error handling, Result pattern, functional utilities
├── multiarray/     # Multi-dimensional array abstraction (numpy backend)
├── math/           # Algebra, geometry, symbolic computation, chaos
├── quantities/     # Physical quantities and unit system
├── core/           # Core modeling framework
│   ├── variable/   # Variable types
│   ├── token/      # Token system
│   ├── symbol/     # Symbolic functions
│   ├── model/      # MetaModel and model variants
│   ├── solver/     # Solver abstraction and mock
│   └── plugin/     # Solver adapters (gurobi, scip, copt, mindopt)
└── framework/      # Domain-specific frameworks
    ├── bpp3d/      # 3D Bin Packing
    ├── csp1d/      # 1D Cutting Stock
    └── gantt_scheduling/  # Gantt Scheduling
```

## Requirements

- Python 3.13+
- NumPy 1.26+
- Pydantic 2.0+
- Returns 0.22+

## License

MIT
