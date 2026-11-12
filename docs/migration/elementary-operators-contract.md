# Elementary Operators Binding Contract

## Public Surface

The twelve public unary entries keep their natural names and positional-or-keyword
argument names:

- exponential: `exp_op`, `exp2_op`, `exp10_op`;
- logarithm: `log_op`, `log2_op`, `log10_op`;
- trigonometry: `sin_op`, `cos_op`, `tan_op`, `asin_op`, `acos_op`, `atan_op`.

Each now returns the existing three-parameter `BindingResult[float]`. Existing
consumers explicitly unwrap or propagate that Result. This is a reviewed return
contract upgrade, not an implicit bare-float compatibility fallback.

## Input Domains

- `exp`, `exp2`, and the six trigonometric entries retain the previous
  `PyFloat_AsDouble` protocol: open `__float__` and `__index__` values are
  supported, strings and bytes are not newly accepted, and an int subclass may
  provide `__float__`. An exact integer too wide for a finite Float64 and a finite
  input whose result overflows become explicit `OVERFLOW` failures.
- `log`, `log2`, and `log10` read the actual payload of every `int`, including
  bool and int subclasses, without invoking an overridden `__float__`. Other
  inputs use `PyFloat_AsDouble`. Positive arbitrary-width integers are passed
  exactly as BigInt rather than narrowed to infinity. Nonpositive values and
  negative infinity fail with `ILLEGAL_ARGUMENT`; NaN and positive infinity retain
  their IEEE behavior.
- `exp10` retains the legacy real-power split: integer payloads, including int
  subclasses, bypass `__float__`; Fraction, NumPy real scalars, bool, and open
  values registered as `numbers.Real` are accepted. Decimal and float-only
  unregistered objects remain rejected before the native boundary. Every
  successful output is Float64; NumPy scalar intermediate-dtype rounding is not
  promised as a Python Result representation.
- Trigonometric NaN behavior follows the old math functions. `sin`, `cos`, and
  `tan` reject both infinities. `asin` and `acos` accept NaN but reject values
  outside `[-1, 1]`. `atan` accepts every IEEE Float64 value.

Each natural call collects its one numeric protocol once and immediately reaches
the native boundary. No input or result cache is retained.

## Fixed Rust Computation

The only upstream source is revision
`119854756a0aeb66d2998055f96fa7175c7bfb37`.

- `exp` calls the pinned `operator::exp`.
- The three logarithms call pinned `operator::ln`, `lg`, and `lg2`.
- Representable wide logarithms use the pinned BigDecimal operations with
  precision parameter 64 and then export Float64. Upstream normalization and
  series remain upstream.
- No dedicated upstream binary-exponential export exists for `exp2` or `exp10`,
  so both call pinned `operator::powf` with base 2 or 10. The binding never falls
  back to Python `math.exp2` or `10.0**x`.
- The six trigonometric operations call pinned `sin`, `cos`, `tan`, `asin`,
  `acos`, and `atan`. Upstream `Option` failures are mapped to
  `ILLEGAL_ARGUMENT`; they are not retained as exception control flow.

Plain-Float64 differential contracts cover signed zero, subnormal values,
nonfinite values, finite overflow, and the domain boundaries. Wide-integer
logarithms use relative tolerance 4e-15 rather than claiming cross-libm or
arbitrary-precision bit identity.

## Failure And Lifetime Boundaries

Structured native failures reuse `Failure`, `ErrorCode`, `ExErr`, and
`FailureContext`. External conversion exceptions retain their original instance
and traceback without formatting: TypeError maps to `ILLEGAL_ARGUMENT`,
OverflowError to `OVERFLOW`, MemoryError to `RESOURCE_EXHAUSTED`, and other
ordinary Exception values to `APPLICATION_ERROR`. BaseException propagates
unchanged. A missing native payload is never interpreted as a successful unit
value.

Numeric computation detaches from the GIL after input collection, with signal
checks before and after. It does not call Python while detached. Success retains
neither the input object nor a long-lived native owner. A retained failure
traceback intentionally retains the references reachable from that exception.

## Acceptance Status

The Windows CPython 3.13 source and distribution candidates have passed:

- default, `scip,gurobi10`, and release Rust tests (127 each), plus strict Clippy
  in both default and dual-backend configurations;
- strict mypy for the four production modules, Ruff/format for all affected
  Python files, 42 migration gates, scope inventory, and 12 benchmark correctness
  contracts;
- the complete `tests + examples` identity audit: 31,017 passed, 8 existing
  failures, 594 skipped, and 29 xfailed, with all 31,072 prior case identities
  and results preserved;
- real SCIP/Gurobi 10 models for all 12 coefficient paths, and four isolated
  wheel/same-sdist installations built outside the checkout.

The API status remains `specified`, not `switched`. Both complete natural-call
rounds failed the 1.15 budget on all 52 cold/warm configurations. Wide-integer
logarithms remain the dominant cost (about 885-955 times the former Python
batch in the warm measurements), and this is part of the preserved input
contract rather than a benchmark exclusion.

Linux, Gurobi 11/12, long-term resource and allocation-failure behavior,
RG-008/RG-009, the remaining elementary/numeric domains, array and symbol work,
all P3-P9 requirements, and final legacy-kernel removal remain independent.
