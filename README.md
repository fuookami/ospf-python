# ospf-python

[中文版](README_ch.md)

Python implementation of the ospf-kotlin optimization framework.

## Overview

ospf-python is a comprehensive optimization modeling framework with support for:
- Linear Programming (LP)
- Mixed-Integer Programming (MILP)
- Quadratic Programming (QP)
- Domain-specific frameworks for bin packing, cutting stock, and scheduling

## Module Structure

| Module | Description |
|--------|-------------|
| `ospf_python.utils` | Error handling (Result pattern), functional utilities, protocols |
| `ospf_python.multiarray` | N-dimensional arrays with numpy backend |
| `ospf_python.math` | Algebra, geometry, combinatorics, chaotic maps, symbolic math |
| `ospf_python.quantities` | Physical quantities with unit system |
| `ospf_python.core` | Optimization core: variables, tokens, models, solvers |
| `ospf_python.framework` | Domain frameworks: bpp3d, csp1d, gantt_scheduling |

## Public API

### Core Modeling

```python
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.solver.solver import Solver
from ospf_python.core.solver.mock_solver import MockSolver
```

### Physical Quantities

```python
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER, KILOMETER
from ospf_python.quantities.unit.mass import KILOGRAM
```

### Error Handling (Result Pattern)

```python
from ospf_python.utils.functional import Result, Ok, Failed
from ospf_python.utils.error import ErrorCode
```

## Extension Points

- **Extra Context**: Add custom variables/constraints via `extra context` pattern
- **Extra Pipeline**: Add custom constraints/objectives via `pipeline` pattern
- **Solver Adapters**: gurobi, scip, copt, mindopt (via `core.solver.<vendor>`)

## Generic Numeric Types

- `RealNumber` — abstract numeric type for generic algorithms
- `Quantity[T]` — physical quantity with unit (`.rules §5`)
- Different unit raw values must not mix

## Solvers

| Solver | Status |
|--------|--------|
| MockSolver | Built-in, for testing |
| gurobi | via gurobipy |
| scip | via pyscipopt |
| copt | via coptpy |
| mindopt | via mindoptpy |

## Quick Start

```bash
uv sync
uv run pytest -q
```

## License

MIT
