# Quantity Duration / 数量时长

## Status And Scope / 状态与范围

Natural `from_hours`, `from_minutes` and `to_timedelta` now use the Rust-backed
source candidate and explicitly return the existing three-parameter BindingResult.
This is not formal `switched` acceptance of duration, Quantity, P3 or the migration.
Full-call/resource budgets, distributions, all framework consumers/platforms,
Gurobi11/12 and every existing RG-008 requirement remain mandatory. Execution
evidence and progress are kept in ignored `logs/`.

三个自然时长入口已接通原生 Result 源码候选，不能据此宣布 helpers/Quantity 或整体切换。
旧八项原子质量精度门禁继续真实失败，所有223单位、旧性能缺口及 P3-P9 均不缩减。

## Natural API / 自然接口

- `from_hours[V](hours, *, context=None, exact=True, numeric_adapter=None)`.
- `from_minutes[V](minutes, *, context=None, exact=True, numeric_adapter=None)`.
- `to_timedelta[V](qty, *, numeric_adapter=None)`.

Each returns BindingResult[Any]. Normal outputs are a second-denominated Quantity
or datetime.timedelta; a replaced module factory can intentionally return another
object, including None or a Result as data. No false generic promise is made for
those open factories. Consume Result explicitly before using the value. In
particular, use `to_timedelta(from_hours(1).unwrap()).unwrap()`, not a nested call
passing the outer Result as if it were a Quantity.

Quantity remains a frozen two-field DTO. No native instance field, coefficient
cache, second authoritative duration state, selectable old kernel or Python unit
formula is added. The separate `ospf_python.math.duration.Duration` API is not this
module and is not rewritten by matching method names.

## Constructors / 小时和分钟构造

Builtin int/Fraction/finite Decimal/private-public Rational and finite
float/Floating use the existing fixed-revision Unit/quantity conversion with
integer scales 3600/60 and SI seconds. The original numeric import/export policy
retains domains, promotes nonintegral integers when needed, and never silently
coerces exact values to float. Decimal context participates only at the final
canonical export; exact=True rejects loss, exact=False permits the explicit output
rounding policy. Float64 signed zero follows pinned Rust operation order.

An explicit NumericAdapter imports custom values and reconstructs the constructor
output through from_fraction. Without an adapter, other representations retain
their Python multiplication protocol `value * 3600` / `value * 60`, invoked by Rust.
The returned value stays opaque; this is an open numeric extension, not a fallback
to old Python builtin-unit mathematics and not a claim that arbitrary arithmetic is
native, finite or exact. The integer factor and original operand are not float-cast.

Rust captures the current module `Quantity` factory before conversion/arithmetic,
then reads the current `SECOND` after arithmetic and calls that captured factory
with `value`/`unit`. Rebinding Quantity during arithmetic does not replace the
already-captured callable; rebinding SECOND does affect the output label, as before.
The literal hour/minute conversion does not read HOUR/MINUTE or infer mathematics
from that label. Module globals have priority over builtins fallbacks; missing
names or factory failures follow the external-error Result boundary.

构造器先捕获工厂、运算后再读 SECOND；不能把工厂读取挪到回调之后，也不能将当前
输出标签当作已验证的时间单位。自定义数值可显式 adapter，也可保留开放乘法协议。

## SI Import And Dimensions / SI 导入与量纲

to_timedelta reads owner.unit, captures unit.to_si, reads owner.value, and invokes
the existing source dispatch once. Builtin family guards select the pinned Unit/SI
lane; native provenance requires identity with this call's published SI token,
after clearing any preceding token. The actual native SI descriptor supplies the
dimension proof. Private token type or an old token returned by an open callback
does not prove provenance. All known builtin nontime dimensions fail, regardless
of symbol. Existing Scale/data-loss guards still run and preserve original failure.

Subclasses, replaced methods and dynamic fields remain open. Unknown units do not
trigger speculative symbol/factor/dimension reads. Their captured callback receives
the **original value**, not the old mandatory float(value); its result stays opaque
and is supplied to the current timedelta factory as `seconds=result`. An open unit
cannot prove it is time-dimensional. It is not labeled dimensionally verified.

The old implicit float, accepted nontime dimensions and exception-based public
return were deliberately upgraded. Migration-before probes and frozen source are
references, not a selectable production implementation or a claim of unchanged
old semantics.

## Exact And Float64 Microseconds / 精确域与 Float64 微秒

For a native exact SI value and the actual builtin datetime.timedelta type, Rust
quantizes exact seconds to microseconds, ties to even, without Decimal arithmetic
or float. It checks the **rounded** value against the asymmetric Python bounds:
`-999999999 days` through `999999999 days, 23:59:59.999999`. Out-of-range exact
values return native OVERFLOW. The builtin object is constructed from the resulting
signed integer microseconds; Python performs its normal normalized DTO construction.

For native Float64/Floating SI outputs, pass the already-converted builtin float to
datetime.timedelta(seconds=...). Its CPython rounding is retained rather than
substituting exact binary-rational rounding. For example, 2.5e-6 gives 2 microseconds;
rounding its exact binary fraction after multiplying by 1000000 would give 3.
The negative and nextafter-neighbor cases must also retain this distinction.

An open timedelta factory receives `seconds=`: native exact SI exports canonical
Fraction, native Float64 remains float, and open SI remains the original object.
NumericAdapter is import-only for to_timedelta: no custom numeric output is created,
so from_fraction is not called. Replaced factories are not forced to accept integer
`microseconds=` or reconstructed outputs; their own seconds protocol remains open.
The canonical builtin check uses the Python datetime C API type, not a cached
replaceable module attribute or a same-name/type guess.

Float64/open factory errors, including stdlib range/type errors, retain their
original exception object in APPLICATION_ERROR FailureContext; native exact range
failures use structured OVERFLOW. No error text is parsed to invent categories.

精确域按精确 SI 秒进行微秒 ties-to-even，保留正负与完整非对称范围；Float64 则保留
CPython 的浮点舍入，不统一改为精确二进制分数舍入。开放工厂仍接收 seconds 关键字；
其原始异常保留，不以字符串猜测错误类别。to_timedelta 无数值重建，不调用 adapter 出口。

## Why Not IntoDuration / 不能直接别名的原因

Fixed Rust IntoDuration targets unsigned std::time::Duration, rejects negative
values and finer-than-nanosecond values, and accepts a u64-second range. Python
timedelta is signed, rounds submicrosecond values and has a different range.
Aliasing the trait would both narrow and widen the Python contract incorrectly.
This binding reuses the real pinned unit mathematics and adds only the required
Python representation/quantization boundary; it does not implement another unit
kernel or decorate a Python calculation with an unused trait call.

Ordinary external Exception identities, traceback, cause/context and handled state
are retained under the QUANTITY_DURATION failure class, without formatting errors.
BaseException propagates. Typed native/adapter failures stop before output factories
and keep provenance. Success/failed output release remains outside storage locks;
the call keeps no persistent owner, value, unit or adapter cache.

Checked operators, temperature differences, fractional dimensions, all previous
performance gaps, complete framework domains, Linux/Gurobi11/12 and final old-kernel
removal remain separate required work. See the master plan, not local green tests,
for migration completion criteria.
