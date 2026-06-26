# Architecture Overview

## Layer Architecture

ospf-python follows a layered architecture:

```
examples/          # Business scenarios (downstream consumers)
framework/         # Domain frameworks (bpp3d, csp1d, gantt)
core/              # Core optimization (MetaModel, Solver)
math/              # Mathematical foundations
quantities/        # Physical quantities
utils/             # Base utilities (Result, Error, etc.)
```

## Key Design Patterns

### Result Pattern (No Exceptions)

All operations return `Result[T, C, E]` instead of raising exceptions:

```python
from ospf_python.utils.functional import Result, Ok, Failed

def risky_operation() -> Result[str, str, Error]:
    if success:
        return Ok("result")
    return Failed(Err(code=ErrorCode.ERROR, message="failed"))
```

### DDD Architecture (framework/)

Each domain follows Domain-Driven Design:

```
framework/<domain>/
├── application/     # Application services (orchestration)
├── domain/          # Domain contexts, models, constraints
└── infrastructure/  # External adapters
```

### Column Generation Lifecycle

All solvers follow the same lifecycle:

1. `register()` — Register problem variables and constraints
2. `add_columns()` — Add new columns (patterns)
3. `refresh_shadow_price()` — Update dual values
4. `finalize()` — Prepare for final solve
5. `extract_solution()` — Extract solution
