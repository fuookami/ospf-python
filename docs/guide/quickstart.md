# Quick Start Guide

## Installation

```bash
git clone https://github.com/fuookami/ospf-python.git
cd ospf-python
uv sync
```

## Basic Usage

### Creating a Model

```python
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.variable.any_variable import AnyVariable
from ospf_python.core.variable.type import VariableType

# Create model
model = MetaModel(name="example")

# Register variables
x = AnyVariable(name="x", index=0, type=VariableType.CONTINUOUS)
y = AnyVariable(name="y", index=1, type=VariableType.CONTINUOUS)
model.register_variable("x", x)
model.register_variable("y", y)
```

### Using Solvers

```python
from ospf_python.core.solver.gurobi.gurobi_linear_solver import GurobiLinearSolver

solver = GurobiLinearSolver()
# Build problem, solve, extract solution
```

### Running Tests

```bash
uv run pytest -q
uv run ruff check .
uv run mypy ospf_python
```
