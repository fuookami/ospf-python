# Extension Points

## Overview

ospf-python provides extension points for downstream business scenarios to inject custom logic without modifying the core framework.

## Extra Context

Add custom variables and constraints to the MetaModel:

```python
from ospf_python.core.model.mechanism.meta_model import MetaModel

model = MetaModel(name="extended")
# Register custom variables
model.register_variable("custom_var", custom_variable)
# Register custom constraints
model.register_constraint("custom_constraint", custom_constraint)
```

## Extra Pipeline

Add custom constraint/objective pipelines:

```python
# Define constraint pipeline
class CustomConstraint:
    def build_constraints(self, aggregation):
        # Build constraints from aggregation
        return constraints

# Inject into solver
solver.register_constraint(CustomConstraint())
```

## Domain Context Pattern

Each domain context follows this pattern:

```python
@dataclass(frozen=True)
class MyContext:
    aggregation: MyAggregation
    # Registration methods (return new instance - immutable)
    def register_item(self, item: MyItem) -> MyContext: ...
    # Query methods
    def get_item(self, key: str) -> MyItem | None: ...
```

## Examples

- **demo2** (3D bin packing aviation): Extended bpp3d with aircraft/stowage/airworthiness contexts
- **demo4** (gantt scheduling): Extended gantt with task/crew/passenger contexts
