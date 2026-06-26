# ospf-python

[English](https://github.com/fuookami/ospf-python) | [中文](https://github.com/fuookami/ospf-python/blob/main/README_ch.md)

Python implementation of the ospf-kotlin optimization framework.

## Overview

ospf-python is a comprehensive optimization modeling framework with support for:

- **Linear Programming (LP)** — continuous variables, linear constraints
- **Mixed-Integer Programming (MILP)** — integer/binary variables
- **Quadratic Programming (QP)** — quadratic objectives
- **Column Generation** — large-scale decomposition
- **Domain frameworks** — bin packing, cutting stock, gantt scheduling

## Quick Start

```python
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.solver.gurobi.gurobi_linear_solver import GurobiLinearSolver

# Create model
model = MetaModel(name="example")

# Create solver
solver = GurobiLinearSolver()

# Build problem, solve, extract solution
```

## Module Structure

| Module | Description |
|--------|-------------|
| `ospf_python.utils` | Result/Error types, functional utilities |
| `ospf_python.multiarray` | N-dimensional arrays with numpy backend |
| `ospf_python.math` | Algebra, geometry, combinatorics, symbolic math |
| `ospf_python.quantities` | Physical quantities with unit system |
| `ospf_python.core` | MetaModel, Solver interfaces, variable types |
| `ospf_python.framework` | Domain frameworks (bpp3d, csp1d, gantt) |

## Documentation

- [Quick Start Guide](guide/quickstart.md)
- [Architecture Overview](guide/architecture.md)
- [Extension Points](guide/extension-points.md)
- [API Reference](api/utils.md)
