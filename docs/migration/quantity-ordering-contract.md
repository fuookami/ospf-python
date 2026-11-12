# Quantity Extrema And Ranges / 数量极值与范围

## Status And Scope / 状态与范围

Natural `min_quantity`, `max_quantity` and `QuantityValueRange.contains` use a pinned
Rust-backed source candidate and explicitly return the existing three-parameter
Result. This is not formal `switched` acceptance or completion of Quantity, helpers,
P3 or the migration. RG-008, full-call budgets, all domains/platforms and the complete
plan remain required. Execution evidence and progress live under ignored `logs/`.

自然极值/范围入口默认接通固定 Rust 源码候选，显式返回既有三参 Result。不能据此
宣布完整 Quantity/helpers/P3 切换；RG-008、完整调用预算、领域/平台及总计划仍须验收。

## Public Contract / 公开合同

- `min_quantity[V](items, *, numeric_adapter=None) -> BindingResult[Quantity[V]]`.
- `max_quantity[V](items, *, numeric_adapter=None) -> BindingResult[Quantity[V]]`.
- `QuantityValueRange[V]` remains a frozen two-field DTO (`min_qty`, `max_qty`), with
  default `Any` generic parameter for existing unparameterized use.
- `contains(qty, *, numeric_adapter=None) -> BindingResult[bool]` checks a closed range.

All calls can fail; consume Result explicitly. `bool(Result)` is not a containment
test. Extrema return the original winning object, never a normalized/reconstructed
Quantity, and retain the first object on ties. Empty extrema return ILLEGAL_ARGUMENT.
Reversed range bounds give `Ok(False)` rather than swapping endpoints. No user-visible
backend flag, instance coefficient cache, normalized owner mirror or silent old
Python arithmetic fallback is introduced.

所有入口须显式消费 Result；不能以 Result 对象的 truth 值代替 contains 的布尔结果。
极值保留原输入对象及首个平局，不重建数量。空极值为 ILLEGAL_ARGUMENT；反向闭区间
返回 Ok(False)，不擅自交换端点。范围 DTO 的字段、序列化及不可变性保留。

## Rust Mathematics And Domains / Rust 数学与数值域

Builtin family detection uses the existing definition-time identity/descriptor
guards, not symbol inference. Each live source coefficient and value enters the
existing fixed-revision Unit/SI conversion lane, including its Scale/data-loss
guards. This reuses the same pinned unit mathematics consumed by natural `to()`;
there is no independent Python SI formula, implicit float conversion or Decimal
precision override.

Integers, Fraction, finite Decimal and private/public Rational normalize losslessly.
Finite float/Floating values retain the pinned Float64 conversion order; their
already-converted binary values are compared exactly against other numeric SI keys.
Thus a precise `Fraction(1, 10)` is less than binary `0.1`, and huge integers never
become float for comparison. Decimal contexts/flags/traps are not numerical inputs
to this comparison and no final Decimal output is needed.

显式 NumericAdapter 对内置单位的自定义表示只调用 to_fraction 并要求 Ok 中为内置
Fraction；失败/未支持 Result 对象保存在 callback_result，不格式化 error。极值与范围
不创建数值输出，所以不调用 from_fraction。原始数值对象始终保留在原 Quantity 中。

The Rust binding performs streaming selection/range control and reuses the existing
safe native rational-comparison boundary (OSPF math arbitrary-precision operations),
rather than recursively ordering arbitrary continued fractions or rounding them to
float. It does not alias upstream `functional::quantity_min/max`: those return cloned
quantities of one value representation and do not express Python object identity,
heterogeneous exact domains or open comparison protocols. The adapter does not
replace the upstream unit-conversion core.

已登记内置单位的所有已知十维量纲必须一致，包括中间穿插未知开放单位而当前获胜者
恰为 opaque 的情况。所有 33 家族/223 常量保持范围；原子质量仍受 RG-008 DATA_LOSS
防护，原八项强制切换测试继续真实失败，不能将“拒绝损失成功”说成全部单位切换成功。

## Open Protocol And Evaluation Order / 开放协议与求值顺序

For each owner, read `unit`, capture `unit.to_si`, then read `value`. For guarded
builtins the existing native source strategy runs; subclasses, changed methods and
dynamic descriptors remain open callbacks, without speculative `_factor`/`symbol`
reads or `float(value)`. An open callback's returned object stays opaque, including
None or Result data. Its arithmetic/comparison is not claimed to be native, finite,
totally ordered or dimensionally proved.

Each key uses the existing source dispatch once, without a speculative duplicate
family guard. Native provenance requires object identity with the SI token published
by that dispatch call, after clearing the preceding key's token. Dimensions come
from that actual native SI unit descriptor. An open callback returning a previous
token or an object of the private token type remains opaque, not a dimensional proof.

每个 key 仅执行一次既有 source 派发，不以提前的重复家族判断代替实际派发结果。
原生来源必须与本次派发发布的 SI token 身份一致，每次先清除上一 key 的 token；
量纲取自实际原生 SI 单位。开放回调返回旧 token 或同类型对象仍是不透明数据。

If both keys are native numeric SI keys, compare in Rust. Otherwise invoke Python
rich comparison/truth protocols. At an actual mixed boundary only, export a native
exact SI key as canonical builtin Fraction, or retain its Float64 value; opaque keys
are not coerced or reconstructed. No Decimal rounding or adapter output is inserted.
Metadata-free open units cannot prove dimensional compatibility. Known builtin
dimensions are still checked wherever available.

Extrema consume one iterator, do not request length/length hints and retain only the
winner/current keys (plus normal input references). A new candidate is compared
`candidate < best` for minimum or `candidate > best` for maximum. No later input is
consumed after failure. Range reads/imports lower, then the current upper, then the
candidate; callback changes to later bounds remain visible. All three SI keys are
obtained before inclusive comparisons, then `lower <= value` short-circuits the
second `value <= upper` comparison. Native dimension mismatch fails before rich
comparison. Native typed failures preserve their Result/provenance identity.

`contains` truth-tests both rich-comparison results and publishes a builtin bool in
Ok. The old chained Python expression could return the final comparison's opaque
object without truth-testing it; the new Result[bool] contract deliberately does not
retain that accidental return type. Any additional final truth protocol is explicit
and its errors follow the same Exception/BaseException boundary.

普通外部 Exception 以原异常对象、traceback 和零基输入位置保存在 FailureContext；
错误消息只包含固定 stage，不触发异常的 str/repr。BaseException 原样传播。比较策略、
真值协议、adapter、迭代器以及重入皆为显式边界；不以捕获所有错误或返回部分极值替代。

## Compatibility And Remaining Work / 兼容与剩余工作

The old helper policy coerced values to float, allowed cross-dimensional comparisons
and raised on empty inputs. These are deliberate Result/exact-domain/dimension
upgrades, not unchanged production semantics. Ordinary existing tests consume Result;
the one migration-before helper-policy test uses test-only frozen functions with the
real module globals and retains its old assertions. These references are never used
by production helpers and are not a selectable fallback backend.

Existing production sources contain no direct consumers of these three helper
functions; matching CSP1D fields named min_quantity/max_quantity are unrelated and
must not be rewritten by name. New resource-solver tests exercise actual native
registration and post-solve checks, not a claim that complete framework domains have
already migrated. The solver registration boundary alone exports bare float.

Duration helpers and checked operators remain separate required work. Fixed Rust
`IntoDuration` targets unsigned std::time::Duration with nanosecond precision and
rejects negatives, whereas Python timedelta supports negative values, microsecond
rounding and a different range. They cannot be directly aliased or silently narrowed.
The current from_hours/from_minutes/to_timedelta implementation is unchanged in this
workpack; its full signed/exact/rounding/open-protocol integration must still migrate.
Temperature-point/difference and fractional-dimension contracts also remain pending.

时长/checked 四则、完整量纲扩展、全部预算、领域、平台、Gurobi11/12、旧内核删除等
仍属于完整目标。本包不能因新增测试或 Windows 安装通过就取消这些要求。
