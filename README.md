# ospf-python

[中文版](README_ch.md)

Python implementation of the ospf-kotlin optimization framework.

## Overview

ospf-python is a comprehensive optimization modeling framework with support for:
- Linear Programming (LP)
- Mixed-Integer Programming (MILP)
- Quadratic Programming (QP)
- Domain-specific frameworks for bin packing, cutting stock, and scheduling
- Symbolic math operations with LaTeX rendering
- Persistence plugins (SQLite, Redis)

## Installation

```bash
# Clone and install
git clone <repo-url>
cd ospf-python
uv sync

# Run tests
uv run pytest -q

# Run with coverage
uv run pytest --cov=ospf_python --cov-report=term-missing
```

## Module Structure

| Module | Description |
|--------|-------------|
| `ospf_python.utils` | Error handling (Result pattern), functional utilities, protocols |
| `ospf_python.multiarray` | N-dimensional arrays with numpy backend |
| `ospf_python.math` | Algebra, geometry, combinatorics, chaotic maps, symbolic math |
| `ospf_python.quantities` | Physical quantities with unit system |
| `ospf_python.core` | Optimization core: variables, tokens, models, solvers |
| `ospf_python.framework` | Domain frameworks (see below) |

## Framework Modules

| Module | Description | Example |
|--------|-------------|---------|
| `framework.bpp1d` | 1D bin packing — pack items into bins | `examples/bpp1d_example.py` |
| `framework.bpp2d` | 2D bin packing — place rectangles/circles | `examples/bpp2d_example.py` |
| `framework.bpp3d` | 3D bin packing — column generation algorithm | — |
| `framework.csp1d` | 1D cutting stock — optimize material usage | — |
| `framework.csp2d` | 2D cutting stock — guillotine cutting plans | `examples/csp2d_example.py` |
| `framework.gantt_scheduling` | Gantt chart scheduling — resource-constrained | — |
| `framework.network_scheduling` | Network scheduling — shortest path, max flow | `examples/network_scheduling_example.py` |

## Math Symbol Operations

The `math.symbol.operation` module provides symbolic math capabilities:

```python
from ospf_python.math.symbol.operation.differentiate import Differentiator
from ospf_python.math.symbol.operation.evaluate import PolynomialEvaluator
from ospf_python.math.symbol.operation.latex import LatexRenderer
from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
from ospf_python.math.symbol.polynomial.canonical_polynomial import CanonicalPolynomial

dsl = QuickDsl(factory=CanonicalPolynomial)
ev = PolynomialEvaluator(factory=CanonicalPolynomial)

x = dsl.var("x")
poly = dsl.sum(dsl.product(x, x), dsl.constant(1.0))  # x^2 + 1
val = ev.evaluate(poly, {"x": 3.0})  # 10.0
```

See `examples/math_symbol_example.py` for a full example.

### Available Operations

| Operation | Module | Description |
|-----------|--------|-------------|
| Differentiation | `operation.differentiate` | Symbolic differentiation |
| Evaluation | `operation.evaluate` | Evaluate polynomials at a point |
| LaTeX | `operation.latex` | Render expressions to LaTeX |
| Parsing | `operation.parse` | Parse string expressions |
| Serialization | `operation.serde` | Serialize/deserialize expressions |
| Normalization | `operation.normalize` | Normalize polynomial form |
| Conversion | `operation.convert` | Convert between polynomial types |
| Compilation | `operation.compile` | Compile to callable functions |
| Factorization | `operation.factorization` | Factor polynomial expressions |
| Quick DSL | `operation.quick_dsl` | Fluent DSL for building expressions |
| FLT64 | `operation.flt64_quick_dsl` | Float64-optimized DSL |

## Persistence Plugins

| Backend | Module | Status |
|---------|--------|--------|
| SQLite | `framework.persistence.sqlite_repository` | Implemented |
| Redis | `framework.persistence.redis_repository` | Implemented |
| Base | `framework.persistence.repository` | Abstract base class |

```python
from ospf_python.framework.persistence.sqlite_repository import SQLiteRepository
from ospf_python.framework.persistence.redis_repository import RedisRepository
```

## Solver Plugins

| Solver | Status | License | Notes |
|--------|--------|---------|-------|
| MockSolver | Built-in | N/A | For testing |
| Gurobi | Implemented | Commercial | via gurobipy |
| SCIP | Implemented | Academic | via pyscipopt |
| COPT | Implemented | Commercial | via coptpy |
| MindOPT | Implemented | Commercial | via mindoptpy |

```python
from ospf_python.core.solver.mock_solver import MockSolver
from ospf_python.core.solver.gurobi.gurobi_solver import GurobiSolver
```

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

## Quick Start

```bash
uv sync
uv run pytest -q
```

## License

MIT
