# ospf-python

[中文版](README_ch.md)

Python interface for OSPF, migrating from an independent implementation to Rust bindings.

## Rust Binding Migration

The package now uses a Maturin/PyO3 mixed build with a private
`ospf_python._native` extension linked to a pinned `ospf-rust` revision.
The current public modeling and domain APIs still use their existing Python
implementations; a successful native import does not mean the core replacement
or a Rust solver has been completed.

Source builds require Rustup, the toolchain in `rust-toolchain.toml`, a platform
linker, and network access to the pinned Rust source and dependencies. A sibling
`ospf-rust` checkout is not required. The base package does not require a solver
SDK or license. Gurobi native support follows Rust's 10/11/12 features, not 13.
The optional Python SDK extras support not-yet-migrated Python adapters; they do
not enable compiled Rust features.

The local documentation links and examples are in the source checkout and source
distribution, not the installed wheel. On a package index, start from the
[source repository](https://github.com/fuookami/ospf-python). To run an example
from a source tree, first build its extension as described in the native
development guide.

See the [binding decisions](docs/migration/decisions/0001-binding-boundaries.md)
and [capability map](docs/migration/api-map.toml) for the migration boundaries.

The private BPP1D `PackingContext` accepts a Python candidate policy during the
pinned Rust search and bounded integer solve. The policy receives a detached
pattern and returns `bool` or `Ok(bool)`. The private solve also accepts a
declarative exact linear extension with detached registration and indicator
snapshots; failures remain explicit Results. This does not switch the public
FFD entry points. A private rebuildable column pool can solve a pinned-revision LP
and a separate final integer model for a captured generation, with independent
exact-source solution checks. It does not yet provide complete column generation,
trusted dual prices or a global optimality proof. See the
[BPP1D contract](docs/migration/bpp1d-contract.md) and
`examples/bpp1d_pattern_policy_example.py` and
`examples/bpp1d_model_extension_example.py`, and
`examples/bpp1d_column_pool_example.py`.

The ordinary mathematical `clamp` has a pinned Rust ordering candidate and now
returns the existing Result; consume it before using the selected original object.
The separate utilities `clamp` is unchanged. See the
[clamp contract](docs/migration/clamp-contract.md) and
`examples/clamp_binding_example.py`; performance and cross-platform acceptance remain pending.

Ordinary `min_of`, `max_of` and `min_max_of` also return `Result` and delegate
ordering to pinned Rust. The current candidate is slower than the previous builtins;
see the [extrema contract](docs/migration/ordinary-extrema-contract.md) before upgrading.

Public array iteration now delegates shared/live slot reads to a native protocol
adapter while retaining the Python generator interface and existing ndarray
sharing. Only actual NumPy scalars use implicit `.item()` conversion; ordinary
objects and ndarray leaves retain identity. This is not a complete array-kernel
cutover. See the [iteration migration notes](docs/migration/public-iteration-cutover.md).

Public arrays also offer checked `at(indices=...)` and mutable `set_at(indices=..., value=...)`
returning the existing Result, with pinned Rust coordinate checks and the original shared
ndarray. Legacy `get/set` signatures are unchanged; custom shapes require explicit
standard-layout consent. See [checked access](docs/migration/public-array-access.md).
`at_many(indices=[...])` checks a whole coordinate batch before collecting shared slots,
preserving request order and duplicates; it is not a concurrent atomic snapshot.

Both public array `to_list()` methods now have a native source candidate returning the
existing Result. Consume it explicitly, for example `array.to_list().unwrap()`.
Pinned Rust plans the standard logical nested layout, fixing column-major C-order export;
NumPy only adapts dtype serialization and custom hooks retain their own protocols.
Complete-call performance/distribution acceptance and authoritative storage remain pending.
See the [nested-export contract](docs/migration/public-nested-export.md).

Public `fast_sum` is still NumPy-backed. Its [replacement contract](docs/migration/fast-sum-contract.md)
records dtype/layout/error boundaries and known precision defects; compatibility tests and
pure Rust timing probes do not certify a reduction-kernel cutover.

`combinations(items, k)` / `permutations(items, k)` and their async variants return
the existing Result through the same pinned Rust selection kernel. Consume success
before iterating; positional order, opaque leaf identity and live indexed protocols
are retained. The [caller upgrade guide](docs/migration/selection-contract.md)
explains failure provenance and executor cancellation. Run
`python -m examples.selection_example` for all four entry points with exact
`Quantity[Fraction]` values; use `await main_async()` inside an existing event loop.
Windows CPython 3.13 operation checks do not certify Linux, Gurobi 11/12, or the
remaining math/array migration and full-domain resource budgets.

Public `cross(*iterables)` now returns the existing Result and delegates Cartesian
enumeration to the pinned Rust kernels. Consume the successful list before iterating;
arbitrary iterable inputs, ordering, duplicates and opaque leaf identities are retained.
See the [upgrade contract](docs/migration/cross-contract.md) and
`examples/cartesian_product_example.py` for exact quantities without float coercion.

Public `MultiArray.reduce(f)` and `MutableMultiArray.reduce(f)` now return the
existing Result: consume it before using the final value. The native boundary uses
pinned Rust indices while preserving a live physical-order left fold and Python
callbacks, exact quantities and opaque result identity. This is not `fast_sum` or
full array-storage migration. See the [reduction contract](docs/migration/public-reduction-cutover.md)
and `examples/array_reduction_example.py`.

Public eager `map(f)` and `flat_map(f)` on both array classes also return the
existing Result. Native physical traversal keeps live storage reads and arbitrary
Python callbacks; NumPy still owns output dtype/broadcast/array protocols. Expanded
data retains the final source shape, including historical size mismatches; this is
not lazy view mapping or complete array storage migration. See the
[mapping contract](docs/migration/public-mapping-cutover.md) and
`examples/array_mapping_example.py`.

Public `MappedMultiArrayView.materialize()` now returns the existing Result and
uses native live coordinate sampling and pinned Rust output-layout publication.
This fixes column-layout coordinate mismatch while preserving C-order callbacks
and NumPy output probing. Plain view materialization and public reshape/flatten
remain separate migration gates. See the
[materialization contract](docs/migration/public-mapped-materialization.md) and
`examples/mapped_materialization_example.py`.

Plain `MultiArrayView.materialize()` has a native source candidate returning the
existing Result: `view.materialize().unwrap()`. Pinned Rust validates the remaining
offset region and plans storage indices; copying preserves dtype, object leaves
and trailing storage axes. Nonzero offsets no longer copy the incorrect full source.
Full-call performance/distribution gates and the view's shape/get authority remain
pending. See the [plain view contract](docs/migration/public-view-materialization.md)
and `examples/view_materialization_example.py`.
The standard storage path copies a checked pinned-stride descriptor once instead
of allocating an index per slot. Native view and storage-transform publication
reuse the existing Result factories without retaining call owners; zero-offset
views still validate live metadata but skip unused dense-shape construction.
Custom storage and ndarray subclasses retain
their actual copy/take protocols. NumPy remains the dtype-aware storage boundary.

Public `MultiArray.transpose()` and `MutableMultiArray.transpose()` also return
the existing Result. Pinned Rust coordinates and standard-layout indexing replace
the Python coordinate loop while preserving immutable live reads, mutable input
precopy, NumPy dtype/assignment and custom shape/integer-stride protocols. This
does not by itself switch full shared storage. See the
[transpose contract](docs/migration/public-transpose-cutover.md).

Public `reshape/flatten` use native storage/shape orchestration and return the
existing Result. A prior candidate passed the local reshape budget against the
complete old implementation, while flatten exceeded it. The current shape-size
candidate does not consistently pass the local reshape budget and still exceeds
the flatten budget; solver and distribution validation also remain pending.
The binding honors
DynShape allocation/initialization and Ok construction hooks, including replacements
before binding import. NumPy remains the dtype-aware copying boundary; full storage,
cross-platform and long-term resource acceptance remain separate. See the
[storage transform contract](docs/migration/storage-transform-contract.md).

Array iteration, mapping, reduction and transpose also read the changed shape size;
their prior local validation must be repeated for the current candidate.

Public Shape dataclasses now use a native arithmetic candidate for size, strides
and permissive flat indices, while preserving their fields, pickle paths and sparse
integer metadata. Package exports load lazily to remove shape/binding import cycles.
Exact machine-integer metadata avoids eager BigInt conversion and repeated layout
probing. Complete-call budgets, distributions and public storage authority remain
separate acceptance gates; this is not a complete shape/storage cutover. See the
[public shape contract](docs/migration/public-shape-contract.md).

Public `Rational` has a source candidate that delegates normalization, arithmetic
and exact ordering to pinned Rust BigRational/OSPF traits. It retains the frozen
two-field dataclass, legacy zero sentinel and Python copy/pickle graph protocols;
strict Result operations remain separate. Subclass constructors receive canonical
result pairs rather than unreduced intermediates. A scoped native identity proof
avoids normalizing those same result objects twice, while still executing subclass
constructors and post-init hooks; it stores no persistent value cache. Complete-call
performance and cross-platform distribution remain acceptance gates, not certified by private batch
speed. See the [public rational contract](docs/migration/public-rational-contract.md).
The four public integer classes also use a source candidate with pinned Rust
arithmetic/comparison and temporary arbitrary-precision values. Their distinct
unbounded, clamped and negative-rejecting policies, Python subclass hooks,
constructor order and dataclass/pickle protocols remain explicit. External numeric
objects keep their Python slots, without a legacy integer backend or cached value
mirror. Complete-call performance, domain/resource budgets and distribution are
still acceptance gates; see the [integer contract](docs/migration/public-integer-contract.md)
and [example](examples/integer_binding_example.py).

Public `Quantity.to(target, *, context=None, exact=True, numeric_adapter=None)` now
has a default source candidate returning the existing Result; explicitly consume
success/failure instead of accessing the return value as a Quantity. Ordinary builtin
units use pinned Rust unit arithmetic with checked dimensions, exact int/Fraction/
Rational/Decimal domains, and explicit finite Float64/Floating. Nonintegral integer
outputs promote to Fraction; Decimal export is canonical (no original trailing zeros,
quantum or negative zero), with rounding allowed only by `exact=False`. Open unit
callbacks remain extensible, and public `NumericAdapter[V]` provides explicit custom
representation import/export without implicit float coercion. Signed zero follows the
pinned Rust operation order. This is not formal quantity cutover: RG-008, helpers,
temperature differences, fractional dimensions, complete-call budgets and full domain/
platform acceptance remain pending. See the [quantity contract](docs/migration/quantity-unit-contract.md)
and run `python -m examples.quantity_conversion_example` for a solver-free example.

Quantity `min_quantity`/`max_quantity` and `QuantityValueRange.contains` also return
Result in their default source candidate. Extrema preserve the original first tied
item; builtin keys use Rust exact SI ordering and checked dimensions without float
coercion or Decimal-context rounding. `NumericAdapter` supplies explicit custom
imports; open unit keys retain Python rich comparisons (mixed native exact keys
export canonical Fraction only at that boundary). Use `.unwrap()` for successful
containment rather than testing the Result object itself. This is not full helper
cutover: duration, checked operators, RG-008, full budgets and domain/platform
acceptance remain pending. See the [ordering contract](docs/migration/quantity-ordering-contract.md)
and `python -m examples.quantity_ordering_example`.

`from_hours`, `from_minutes` and `to_timedelta` now return Result in their source
candidate too. For example, `to_timedelta(from_hours(1).unwrap()).unwrap()` yields
a signed Python timedelta. Builtin conversion uses the same pinned Rust unit lane;
exact SI values quantize to microseconds without float, while Float64 preserves
CPython timedelta rounding. Known nontime dimensions fail; open numeric/unit/factory
protocols retain explicit boundaries. This is not formal duration/Quantity cutover.
See the [duration contract](docs/migration/quantity-duration-contract.md) and
`python -m examples.quantity_duration_example`; complete budgets, distributions,
checked operators, RG-008, domains and platforms remain required.

Solver-enabled Windows wheels require SDK DLL directories to be registered before
native imports; `tests/conftest.py` registers explicitly configured
`OSPF_NATIVE_DLL_DIRS` before test collection, independent of test order.

Solver-enabled Linux wheels keep SCIP/Gurobi runtime libraries external and use
the native `linux` wheel tag. These wheels are intentionally not PyPI-compatible.
The pinned SCIP crate also embeds its build-time `SCIPOPTDIR/lib` as an RPATH, so
the current artifact expects the matching runtime at that path; otherwise rebuild
with the deployment `SCIPOPTDIR`. Solver-enabled sdist rebuilds select this policy
through `scripts/verify_binding_distribution.py`.

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
uv sync --extra dev

# Run tests
uv run pytest -q

# Run with coverage
uv run pytest --cov=ospf_python --cov-report=term-missing
```

For the existing Python SCIP adapter, install `--extra scip` as well. This does
not enable a Rust SCIP backend. Private source-build and test commands
are documented in the [native development guide](docs/migration/native-development.md);
they do not switch the public core. Review [upstream semantic gaps](docs/migration/rust-gaps.md)
before treating the prototype as a complete solver interface.

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

`ospf_python.quantities.Unit` (also `ospf_python.quantities.unit.Unit`) exposes
the existing single-handle Rust runtime unit facade. `Unit.create(...)`, direct
`to_si`/`from_si`, and `Quantity.to(...)` return explicit `Result` values; numeric
domains and `NumericAdapter` policies are preserved instead of forcing floats.
Real native point-subtraction output units can now flow through conversion,
min/max, ranges and duration validation. Known affine points and linear
differences are not interchangeable, including points with a zero offset.
See [the runtime-unit contract](docs/migration/runtime-unit-contract.md) and
`examples/runtime_unit_example.py`.

The natural `Quantity.add/subtract/multiply/divide` methods and their default
operators now share a checked Rust source candidate and return explicit `Result`.
Same-dimensional addition/subtraction converts actual units; integer division is
exact, affine point subtraction publishes a real difference unit, and exact
point/difference operations retain recurring scale ratios such as 1/3. Mixed
builtin domains follow an explicit promotion policy, with lossless exact-to-float
import by default and `exact=False` for explicit approximation. Open numeric
protocols and `NumericAdapter` remain extension points. See
[the arithmetic contract](docs/migration/quantity-arithmetic-contract.md) and
`examples/quantity_arithmetic_example.py`. Consume each operation's Result before
using its output in an array callback or the next arithmetic operation.

This source integration is not full cutover acceptance. Complete native-output
DTO/pickle/deepcopy support, RG-008,
all 223 predefined units, performance budgets and platform/domain validation
remain required; untested Gurobi 11/12 and Linux combinations are not accepted.

### Error Handling (Result Pattern)

```python
from ospf_python.utils.functional import Result, Ok, Failed
from ospf_python.utils.error import ErrorCode
```

## Quantity Snapshots

`Quantity.to_dict()` / `.to_json()` and `Quantity.from_dict()` / `.from_json()`
return Result with an explicit versioned DTO. Numeric domains, signed Float64
zero, Decimal representation, registered unit fields and actual native output
metadata are preserved without implicit float conversion or wire-supplied class
imports. Generic `SnapshotAdapter` policies handle open values and units.
Native Unit/Rational copy, deepcopy and trusted pickle now have source candidates;
Unit keeps its existing identity equality, not a hidden interning cache.
`dataclasses.asdict` remains a Python object graph, not the pure-data DTO.
A legacy unit affected by a proven Rust precision gap is archived with
`native=null`; its arithmetic still returns DATA_LOSS, not a Python fallback.
See the [snapshot contract](docs/migration/quantity-snapshot-contract.md) and
`examples/quantity_snapshot_example.py`. Full acceptance, performance gaps,
RG-008 and platform/domain migration remain pending.

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
