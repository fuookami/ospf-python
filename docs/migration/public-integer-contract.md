# 四类公开整数的绑定合同 / Public integer binding contracts

## 范围与当前状态 / Scope and current state

本合同覆盖 `Integer`、`UInteger`、`NumericInteger`、`NumericUInteger` 的完整
公开行为，而不是把它们合并为一个 i64/u64 包装器。四个自然名保持 `specified`。
公共源码默认已接通 Rust 计算候选，但完整调用预算、领域和跨平台发行尚未验收，
不登记为已验收的 `switched`。永久基线与绑定验证分别位于
`tests/math/algebra/number/test_integer_migration_contracts.py` 和
`tests/math/algebra/number/test_integer_binding.py`。

The four public classes remain distinct, with status `specified`. Source defaults
use the native arithmetic candidate, but complete-call budgets, domains, and
cross-platform distribution are not accepted. Baselines and binding tests do not
by themselves certify a full migration or release.

Rust 依赖固定为 `119854756a0aeb66d2998055f96fa7175c7bfb37`，不修改相邻
Rust/WASM 工作区，不使用本地 path/patch，不为实现绑定升级依赖。

## 数值域与运算 / Domains and operations

| 自然类型 / Public class | 持久字段 / Persistent field | 数值域与结果 / Domain and result |
| --- | --- | --- |
| `Integer` | frozen `value` | 任意精度有符号；加、减、乘、负、除法结果调用 `self.__class__`。 / Unbounded signed arithmetic; results use the dynamic self constructor. |
| `UInteger` | frozen `value` | 任意精度非负，构造负数钳零，减法结果钳零；取负直接构造零。 / Unbounded nonnegative, with construction/subtraction clamping and unconditional zero negation. |
| `NumericInteger` | frozen `_value` | 默认 signed64 边界，但 `MIN_VALUE`/`MAX_VALUE` 可由子类覆盖为任意精度值；仅有 `safe_add`/`safe_mul`，不新增普通 `+`/`*`。 / Default signed64 bounds are overridable; only the existing safe methods are promised. |
| `NumericUInteger` | frozen `_value` | 任意精度非负，无 u64 上限；负构造抛现有 `ValueError`，有 `safe_add`/`safe_mul` 和 `+`/`*`，不新增除法或负号。 / Unbounded nonnegative, rejecting negative construction, without additional division/negation APIs. |

三个无上限域必须保留超过 64 位及十进制字符串长度限制的整数；桥接不能把
i64/u64 当作公共域上限，或使用中间 float、十进制字符串往返。绑定使用临时 `BigInt` 和固定
`ospf_rust_math::operator::{AddRef, SubRef, MulRef, DivRef, NegRef}`，不持久保存第二份值。

Unbounded values must not be narrowed to machine integers or pass through floating
point or decimal strings. Temporary native BigInt values use the pinned OSPF
operators and are not retained as mirrors of the public dataclass field.

### 除法 / Division

- `Integer.__truediv__` 实际使用 Python `//`，不是旧 docstring 所称的向零截断。
  例如 `-7 / 3` 的封装结果为 `-3`。固定 BigInt `DivRef` 向零截断；候选先取商，
  对异号且不整除的结果用固定 `MulRef` 检查、`SubRef` 减一，不复制除法内核。
- 两类有除法的公开类型在首次读到右字段等于零时返回 `self.__class__(0)`；
  严格私有计算接口默认返回 `ILLEGAL_ARGUMENT`，不得将两种合同混为一谈。
- 首次非零后再次读取右字段可能变成零，此时旧协议的 `ZeroDivisionError` 不是零值
  短路。不能用单次字段快照无说明地改变动态对象行为。

Public signed division floors, while pinned BigInt division truncates toward zero.
The boundary adapts only the quotient semantics. The public zero sentinel and the
strict private failure remain separate. The second divisor read is observable.

### 钳制 / Clamping

`NumericInteger.safe_add/safe_mul` 接受本域对象或裸 `int`，必须先精确运算，
再读取当前 self 边界执行 `max(MIN_VALUE, min(MAX_VALUE, result))`。不得预钳 RHS。
结果始终调用模块全局的基类 `NumericInteger`，不是 self 类；因此子类宽边界的
结果还会经过基类默认边界二次钳制。合法构造在比较不等为假时不重写原字段对象。

Bounded safe operations calculate exactly before clamping, then use the module-level
base constructor, including its second clamp. Valid construction retains the input
object when the existing inequality check does not request replacement.

公开代码未验证逆序边界；例如子类 `MIN_VALUE=9, MAX_VALUE=2` 构造及安全加法会
得到 9。私有严格候选拒绝逆序边界，**不是可直接替换公开构造的实现**。边界及
`min/max` 本身可触发外部比较和模块全局钩子，必须实现或明确提出升级决定，不能
靠私有标量测试掩盖差异。

The strict candidate rejects reversed bounds, unlike the legacy public constructor.
It is not a drop-in constructor. Dynamic bounds, comparisons, and module-level
min/max hooks require an explicit facade implementation or a reviewed upgrade.

## 动态协议与发布顺序 / Dynamic protocols and publication order

类型注解不提供运行时 exact-int 保证。现有字段可承载 bool、int 子类、自定义数值，
甚至浮点值。int 子类的算术钩子不能通过 PyO3 BigInt 抽取而被绕过。后续实现应
按明确数值域派发：内置整数运算进入固定 Rust，外部数值调用其 Python 协议；
这不是保留一套可选择的旧整数内核，不提供 backend 开关或失败后静默 fallback。

Annotations do not enforce exact built-in int fields. Domain dispatch must preserve
external arithmetic and reflected hooks instead of extracting their payload and
bypassing them. Exact integer kernels move to pinned Rust; external numeric objects
remain Python extension points, not an optional legacy backend.

| 路径 / Path | 可观察顺序 / Observable order |
| --- | --- |
| `Integer` 加/减/乘/负 | 先捕获 `self.__class__`，再读取字段、执行算术，最后调用已捕获构造器。 / Capture constructor, read operands, calculate, publish. |
| `Integer` / `UInteger` 除法 | 先读右字段及零比较；零分支不读左字段；非零分支捕获构造器，再读左、再次读右。 / Guard RHS first; nonzero path captures constructor and rereads operands. |
| `UInteger` 减法 | 先读字段并计算，后捕获 self 构造器，再执行 `max(result, 0)`；不能预先捕获构造器。 / Calculate before capturing the constructor and applying max. |
| `UInteger` 负号 | 仅捕获构造器并传零，不读源 `value`。 / Construct zero without reading the source value. |
| `NumericInteger` 构造 | 读 MIN、MAX、字段，执行内外钳制，再读字段作不等比较，必要时写回。 / Read bounds/value, clamp, reread value for the conditional assignment. |
| `NumericInteger` 安全运算 | 先解析 RHS 及其字段，再读左字段、计算，再读 self 边界钳制，最后解析模块全局基类构造器。 / Resolve RHS first; capture the global constructor only after arithmetic and clamping. |
| `NumericUInteger` 四个加/乘方法 | 先解析模块全局基类构造器，再依次读取左右字段及算术；中途改变模块全局不影响已捕获 callable。 / Capture the module-level constructor before operand reads and arithmetic. |

以上顺序包括用户 `__getattribute__`、属性、副作用、重入、模块全局替换及首错停止。
普通算术的构造器/字段采集由原生门面按该顺序编排；Python 薄门面保留动态
isinstance/cmp 组合、必要的命名临时值和有界结果构造阶段。实际算术、比较、
钳制进入 `native/src/public_integer.rs`；不是直接把 raw BigInt helper 当作完整门面。

These sequences include user attribute access, reentrancy, global rebinding, and
first-error termination. Native facades compose ordinary constructor/operand reads;
Python retains dynamic isinstance/cmp composition, named temporaries, and bounded
publication stages. The native boundary handles arithmetic, comparison, and clamping rather than
pretending that a raw scalar helper implements the complete object protocol.

### 原生域派发 / Native domain dispatch

仅 exact builtin `int` 运算使用固定 OSPF traits；其他对象，包括
int 子类，直接使用 CPython 数值/富比较槽，保留反向运算优先级和非 bool 比较结果。
没有异常后重试旧实现、Python整数算术fallback或用户可切换backend。钳制的普通
整数比较在Rust执行；传入的非标准min/max callable及外部值仍执行各自Python协议。
相等时保留min/max的首参数身份，逆序公开边界保持原max/min组合语义。

Only exact built-in ints enter pinned OSPF arithmetic. Other values use their
CPython numeric/rich-comparison slots, preserving reflected dispatch and non-bool
results. Native min/max keeps first-argument ties and legacy reversed bounds.
There is no selectable backend or retry into a legacy integer kernel.

原生 `_IntegerOps` 只保存真实 builtin min/max 的 callable 身份，供传入函数的
快速路径确认，不保留用户标量、字段、构造器、外部钳制函数或跨调用算术结果。
对象提供GC traverse/clear，避免因Python对象图形成不可见的引用环。
`UInteger` 的生成顺序、hash/repr、dataclass及序列化仍是标准Python DTO集成，
不另行实现一套整数值或排序内核。

The native helper retains only builtin callable identities, with GC traversal and
clearing. It never caches user values, constructors, or external clamp callbacks.
Dataclass-generated ordering and Python hashing/representation remain DTO integration.

### 门面命名空间与临时值 / Facade namespaces and temporaries

模块局部 `_IntegerFacade` 保存对应 Python 函数的真实 `__globals__` 和
`__builtins__` 字典身份，以及内部 `_IntegerOps` 的 builtin min/max 身份。
每次使用时重新解析全局构造器、钳制函数和错误类：先查 globals，再查该函数
实际持有的 builtins。模块变量 `__builtins__` 重新绑定不会改变既有函数的
builtins 身份，但原字典内容的修改与 global override 均即时生效。
缺失名称使用保留 `.name` 与 `.args` 的 `NameError`，不替换成 `KeyError`。

Each module-local facade retains the actual function globals and builtins dictionaries,
plus its nested helper's builtin identities. Constructors, hooks, and error classes
are resolved live with Python global-then-builtins lookup. Rebinding the module's
`__builtins__` does not replace a function's builtins; mutations and global overrides
remain observable. Missing names retain Python NameError metadata.

这些是函数环境引用，不是“原生对象只持两个 builtin”的承诺；字典可间接保活模块
成员和钩子。门面不另外缓存当前构造器、用户数值或结果，不为每个 DTO 新增句柄。
GC traverse/clear 暴露并清理所有实际强引用，包括两个字典和嵌套 builtin；
不可达的门面/命名空间环可以回收，外部仍可达环境不会被误清理。只读门面允许
回调在同一门面上重入，不能以跨用户调用的可变原生借用阻止它。

These are function-environment references, not a promise of only two builtin edges;
namespace dictionaries may indirectly retain module members and hooks. There is no
additional cached constructor, value, result, or per-DTO handle. GC exposes and clears
all real edges, collecting unreachable namespace cycles without clearing reachable
environments. Read-only facade callbacks may reenter the same facade.

`NumericInteger` 的 `result` 必须在钳制前进入 Python 命名局部，`clamped`
必须在第二次字段读取、不等比较及赋值前进入 Python 命名局部。后续失败的原
traceback 保留这些值，清除 traceback 后方可释放；不能用一个先计算并钳制、
后返回 tuple 的调用替代，也不能把保活状态塞进异常属性。成功返回时仍保留
原 Python 局部及调用参数的释放边界，构造器必须先于临时值销毁。

Bounded arithmetic publishes `result` into a Python local before clamping, and
construction publishes `clamped` before late reads, comparison, or assignment.
Failure tracebacks retain those locals until cleared. A fused calculate/clamp tuple
or extra exception attributes do not preserve that contract. Successful publication
also retains Python local/argument cleanup boundaries, after the constructor call.
Permanent coverage is in `tests/math/algebra/number/test_integer_facade_protocols.py`.

### 精确字长专门化 / Exact word specialization

exact builtin `int` 先通过公开 `PyLong_AsLongLongAndOverflow` 分成可精确容纳的
signed64、负向越界、正向越界三类。该分类不是数值转换失败后的降级，不截断原值，
不读私有 PyLong 布局，也不调用用户 `__index__`。int 子类和其他外部值完全绕过此路径。
可证明顺序的范围比较直接在 Rust 完成；同号的两个大整数仍转换临时 BigInt 比较。

Exact built-in ints are classified using the public overflow-reporting C API,
without truncation, private layouts, or user index hooks. Proven range ordering
does not require whole-value conversion; same-sign large pairs still use BigInt.
External objects and int subclasses never enter this specialization.

两个 signed64 操作数仅在 checked 运算证明结果可表示后，才用固定 OSPF 的 i64
traits 计算；checked 结果本身不作为运算出口。floor 商保持异号非整除减一的适配。
溢出、最小值除以 -1、最小值取负继续使用固定 BigInt 任意精度路径，零除仍保留
原协议错误；不形成固定字长公开上限、Python 整数内核 fallback 或持久值镜像。

Checked operations prove representability only; pinned OSPF i64 traits calculate
the actual result. Overflow and minimum-word corner cases remain arbitrary
precision. Floor semantics and zero-division protocol errors are unchanged.
There is no public word limit, Python integer kernel fallback, or persistent mirror.

永久 `tests/math/algebra/number/test_integer_native_boundaries.py` 保护字长边界、
正负 100000 位值、全部算术/比较、外部子类、钳制对象身份及处理中的异常状态。
阶段成本下降不等于完整调用预算通过；四自然类仍保留所有正式切换前置。

Permanent boundary tests cover word limits, 100000-bit values, arithmetic and
relations, external subclasses, clamp identities, and handled exceptions.
Stage-level speedups do not satisfy complete-call budgets or clear cutover gates.

### 任意精度二进制出口 / Arbitrary-precision binary export

任意精度算术和取负的 Rust 结果通过公开 `PyLong_FromNativeBytes` 构造 exact builtin
`int`。出口只在调用内从 BigInt 的公开 `to_u64_digits` 取得临时 magnitude 缓冲，
为零值或最高有效符号位补字，对负值按字编码二补码，并逐字规范为小端后传入明确的
little-endian flags。缓冲在 C API 返回前保持有效，拥有引用由 PyO3 接管，失败仍
原样传播 Python 错误；不读取或写入私有 PyLong 布局。

Arbitrary-precision arithmetic and negation results use the public native-byte C
API to create exact built-in ints. Public BigInt magnitude digits form a temporary
buffer with explicit sign padding, word-level two's-complement encoding, and
little-endian normalization. The buffer outlives the C call; PyO3 owns its returned
reference and preserves any Python error. No private PyLong layout is accessed.

这是二进制序列化适配，不是另一套加减乘除内核；实际计算仍使用固定 OSPF traits。
signed64 已证明安全的算术仍使用原字长出口，外部数值/子类槽、字段/构造顺序、
钳制首对象身份和处理中的异常状态均不改变。新永久
`tests/math/algebra/number/test_integer_binary_bridge.py` 覆盖密集/稀疏位模式、符号
补位、跨字进位、零结果、100000 位以及四类公开构造政策。

This is serialization, not a second arithmetic kernel. Pinned OSPF operators,
proven-safe word results, external numeric slots, observable facade order, clamp
identities, and handled exceptions remain unchanged. Permanent tests cover dense
and sparse digits, sign padding, carries, zero, 100000-bit results, and all four
public constructor policies.

出口阶段的成本优化不清除完整自然调用预算、输入成本、领域和平台前置；四自然类
仍为 `specified`，不以私有阶段诊断冒称完整切换或总体加速。

Export-stage improvements do not clear complete-call, ingress, domain, or platform
gates. All four public classes remain specified until those gates are accepted.

## 比较、结果类与生态 / Comparison, result classes, and integration

- `Integer`/`UInteger` 相等只接受各自基类的 `isinstance`，其他直接返回
  `NotImplemented`。`Integer` 的顺序读取对方 `.value`；`UInteger` 的 dataclass
  生成顺序比较要求双方 exact same class，不能因跨子类相等可真而放宽顺序限制。
- `NumericInteger` 相等支持本域与 builtin int（含 bool），其顺序会解析本域右字段
  或使用原 RHS；`NumericUInteger` 相等仅同域，仅承诺已有 `<`/`<=`，不擅自补全
  `RealNumber` 或 `cmp`。
- `Integer.cmp` 先作 `<`，必要时再读取字段作 `>`；`partial_cmp` 动态调用 `self.cmp`，
  不能跳过子类 override。外部富比较返回值和真值转换属于 Python 协议。
- 字段、frozen dataclass、hash/repr/str、replace/asdict、copy/deepcopy/pickle、
  子类、额外属性、图中重复引用和自环仍是 Python DTO/生态集成职责。没有原生隐藏
  owner、跨调用值缓存或必须安装 solver 才能构造整数的要求。
- `number.__init__` 现有导出保持原样；不因盘点而擅自把两个 Numeric 类加入重导出。

Equality domains, dataclass ordering class checks, and dynamic partial comparison
remain distinct. Public DTOs and serialization retain class identity, extra fields,
aliases, and cycles. No hidden native owner or persistent mirror is introduced.

## 错误与控制流 / Errors and control flow

严格私有算术返回既有 Result/ExErr；无效域、缺失/逆序边界、未知操作和严格零除
返回 `ILLEGAL_ARGUMENT`。显式零兼容仅是诊断政策，不改变私有严格默认。

现有公开操作符仍返回数值对象。不能把严格 helper 的失败 `.unwrap()` 后抛业务异常，
也不能在本包静默将公开操作符变成 Result。新公共可失败能力须遵循项目 Result
规则；公开数据类校验和外部协议异常按既有协议边界处理。未来若升级公开签名，
须与全部消费者、文档和测试原子切换。

The private helper uses existing Result/ExErr with semantic input failures. Public
operators still return values; no implicit Result signature change or failure unwrap
is approved. New fallible public APIs follow the project Result policy.

外部原异常、原 traceback 和处理中的 `sys.exception()` 必须保留；不调用用户异常
`str/repr`，不把控制异常吞为普通失败，首错后不发布构造结果。数据类负值校验是
已有快速失败协议，不等同于新的业务异常接口。

Preserve original external exceptions, traceback objects, handled-exception state,
and BaseException propagation, without formatting user exceptions or publishing a
partial result after failure.

## 原子切换门槛 / Atomic cutover gates

以下前置未清空前，四自然类不得登记 `verified`、`switched` 或 `legacy_removed`：

1. 完整门面及默认路径接通固定 Rust；保留上述构造、字段读取、外部协议、比较和
   错误时序，或提出有证据的显式升级，不用标量子集替代完整公共能力。
2. 四类全部公开/生成方法、字段、导出和仓库消费者有盘点；运行现有代数/法则、
   转换及新协议测试。静态未见生产引用不代表不存在仓库外使用者。
3. 真实领域消费者及必要的 SCIP/Gurobi 求解链，核对精确输入到 solver Float64
   边界，不以私有批处理或 import smoke 代替公共完整调用验收。
4. 同数据、真正旧实现基线的自然调用性能和资源预算；逐标量 BigInt FFI 可能慢于
   CPython int，不能通过持久双份缓存、降低预算或扩大批次来掩盖失败。
5. 生产 wheel/sdist、无相邻仓库安装、支持的 Windows/Linux 与 NumPy/解释器组合、
   类型提示和文档一致。候选 debug/release 编译不等同于发行认证。

The source implementation now integrates the public protocol, not a second
scalar-only wrapper. Retain all distribution, consumer, performance, and resource
gates until evidence of the actual public default path satisfies them. The public
example is `examples/integer_binding_example.py`; complete-call benchmarks are in
`benchmarks/test_public_integer_hot_path.py`, and minimal native MILP consumers are
in `tests/native/test_public_integer_solver.py`. A minimal MILP is not acceptance of
all framework domains or all solver/platform combinations.
