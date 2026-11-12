# Natural Logarithm Binding Contract

## Public Surface

`ospf_python.math.ordinary.log.log_base(x, base)` keeps its natural name and two
positional-or-keyword arguments. It now returns the existing three-parameter
`BindingResult[float]`, not a bare float. Existing consumers explicitly unwrap or
propagate that Result. This is a reviewed return-contract upgrade, not an implicit
compatibility fallback.

## Input Domain And Evaluation Order

- Retain the numeric domain accepted by the previous `math.log(x) / math.log(base)`:
  arbitrary-width integers, actual integer subclasses, Float64 values, Decimal,
  Fraction, NumPy scalar numeric protocols, and open `__float__`/`__index__` inputs.
- Actual integers, including bool and int subclasses, use their integer value;
  overridden conversion hooks on an int subclass are not invoked. Other inputs
  use PyFloat_AsDouble, which does not newly accept strings or bytes.
- Collect and validate x before touching base. A conversion error or nonpositive x
  short-circuits the base protocol. Each numeric protocol is called once.
- Nonpositive arguments and base one become explicit ILLEGAL_ARGUMENT failures.
  NaN and positive infinity retain the original IEEE result behavior, including
  signed zero; a NaN x does not bypass validation of base.
- No Float64-only narrowing: an integer too wide to become a finite Float64 is
  passed exactly as a BigInt, never truncated, rejected solely for width, or
  substituted with infinity. The result remains Float64 as before.

## Fixed Rust Computation

The only upstream source is revision
`119854756a0aeb66d2998055f96fa7175c7bfb37`.

- When both inputs are representable, use the fixed
  `ospf_rust_math::ordinary::log::<f64>`.
- For a wider positive integer, pass its exact value to the fixed
  `ordinary::ln_with_precision` with upstream precision parameter 64. Compose the
  two natural logarithms using the upstream `DivRef` operation. Representable
  operands in this mixed path also use the fixed logarithm, with base e.
- The upstream BigDecimal logarithm's normalization and series remain upstream;
  they are not copied or repaired in the binding. Wide operands are positive
  integers greater than one, so its fractional-input branch is not used.
- Finite numeric differential acceptance uses relative tolerance 4e-15, rather
  than claiming cross-libm bit identity. NaN, infinities and zero signs have
  separate assertions. This does not promise arbitrary-precision logarithm output.
- No Python math.log fallback, binding-local logarithm approximation, persistent
  numeric mirror, memoized answer, new dependency, or change to the pinned Rust
  repository is permitted.

## Failure And Lifetime Boundaries

Domain failures carry the existing structured native failure. External conversion
exceptions retain their instance and traceback without formatting them: TypeError
maps to ILLEGAL_ARGUMENT, MemoryError to RESOURCE_EXHAUSTED, other Exception values
to APPLICATION_ERROR. BaseException propagates unchanged. This is the existing
Result family, not a second error model.

Numeric computation detaches from the GIL after input collection, with signal
checks before and after. It does not call Python while detached. Success retains
neither input object, permits reentry during conversion, and creates no native
long-lived owner. Retaining a failure's original traceback intentionally retains
that exception's references.

Wide-integer upstream logarithms normalize iteratively and may be much more
expensive than CPython's integer logarithm. No timely cancellation, recoverable
system OOM, allocation sandbox, no-leak proof, or long-term resource guarantee is
claimed. Measure complete natural Result-plus-unwrap calls, not only raw FFI.

## Acceptance Status

Source candidate only. Default/debug/full identity regression, native tests and
Clippy, typing/lint/scope gates, real SCIP/Gurobi consumers, complete-call budgets,
resources, wheel/sdist isolated installations, and independent evidence freezing
must be recorded in logs. Budget failure remains visible; no formal switched
status or complete migration is implied. Linux, Gurobi 11/12, RG-008/RG-009, all
other numeric/array budgets and remaining P3-P9 requirements remain independent.
