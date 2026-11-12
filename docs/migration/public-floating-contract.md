# 公开 Floating 的绑定合同 / Public Floating Binding Contract

## 范围与状态 / Scope and Status

`ospf_python.math.algebra.number.floating.Floating` 保留自然名、frozen dataclass
与唯一公开字段 `value`。源码默认计算候选连接固定 Rust revision
`119854756a0aeb66d2998055f96fa7175c7bfb37`，不修改相邻 Rust/WASM 工作区。
状态保持 `specified`；协议测试、源码接通和单机诊断均不等于完整性能、领域或
跨平台发行验收。没有 backend 开关、失败后旧内核重试或持久数值镜像。

The public class remains a frozen Python dataclass with its single authoritative
`value` field. Source arithmetic is a pinned-Rust candidate, not an accepted cutover.
There is no selectable backend, retry into the old kernel, or persistent value mirror.

## 数值域 / Numeric Domains

- exact builtin `float` 四则与取负调用固定 OSPF `AddRef/SubRef/MulRef/DivRef/NegRef`，
  比较保持 IEEE 语义，不使用全序浮点包装。NaN、无穷、有限溢出、subnormal、舍入
  和带符号零必须覆盖；不擅自引入容差、有限值白名单或拒绝无穷的 solver 政策。
- `value: float` 注解不执行构造转换。两个 exact `int` 字段加减乘/取负/比较共享
  已有固定 OSPF 任意精度整数边界，不能偷偷变成 f64、i64 或 Python 整数 fallback。
  整数真除法通过固定 OSPF BigRational `DivRef` 与依赖的受检 f64 转换适配，保留
  正确舍入、整数除法溢出异常及负向下溢/零结果的负零符号。
  两个 exact int 均可精确容纳于 i64 时，使用同一固定 `DivRef` 的 `Ratio<i128>`
  特化：输入先经公开、无截断范围探针证明，整数有理数的全部运算中间值可精确
  容纳于 i128（包括 i64 MIN/-1），随后由同一依赖转换并恢复负零；不先把整数
  转成 f64，不使用整数截断商。任一输入越界仍走原任意精度 BigRational 路径，
  不是溢出异常或 Python 计算 fallback，也不把范围特化升级为公开输入白名单。
- exact float/int 混合算术采用 Python 的显式浮点域转换顺序；过大整数转换失败
  必须保留原 `OverflowError` 政策，不能因另一侧是 NaN/无穷就跳过转换。
  除零同样由本机解释器抛出：绑定不再硬编码 `"float division by zero"`；
  本机实测 CPython 3.13 与 3.15 的除零文案不同，未据此推断变化的首个版本。
  异常类型、两侧字段的抽取次序与零除判定本身不变。
- float/int 子类、bool、Fraction、Decimal、complex、NumPy 标量及任意下游数值仍
  调用其原数值/富比较槽。保留 reflected 优先级、非 bool 比较结果、返回叶类型，
  不抽取子类载荷，不强制调用 `__float__`，不把名义浮点类型变成运行时类型白名单。

Exact floats use pinned OSPF operators and IEEE comparisons. Exact integers retain
their unbounded domain through the existing integer boundary; true division uses
the pinned rational operator and checked conversion, including signed underflow.
When both exact integers provably fit i64, the same pinned operator specializes to
`Ratio<i128>` with exact intermediates, including i64 MIN/-1; conversion never
pre-rounds either integer to f64. Out-of-range inputs retain the BigRational path.
Mixed builtin arithmetic retains float-conversion failures. External values keep
their original numeric slots, reflected dispatch, and result identities without
payload extraction or forced coercion.
Zero divisors delegate to the host interpreter, so the message follows it across
versions instead of a hard-coded string, and conversion order and the zero test
itself stay the same.

## 求值、构造和生命周期 / Evaluation, Construction, and Lifetimes

加减乘/取负先捕获 `self.__class__`，再读取字段和计算，最后调用已捕获的构造器。
临时二元操作数在结果构造前按左、右顺序释放；字段读取失败、运算失败、构造失败
不得发布伪结果或把临时叶保存在原生对象中。数据类、额外字段、aliases、cycles、
copy/deepcopy/pickle、hash/repr 与全部常量属性保持 Python DTO/生态集成。
原生 `__class__`/`value` 访问使用公开 PyO3 interned 名称，匹配原 Python 属性
语法传给动态 `__getattribute__` 的名称对象身份；不为每次读取新建不同名称对象。

除法保留 Python 薄门面的首次右字段读取和 `== 0.0` guard。零分支返回
`self.__class__(0.0)`，不读取左字段；guard 与结果构造使用同一个 Python 代码常量
对象身份。非零分支捕获构造器、读取左字段并再次读取右字段；第二次变零必须产生
原 `ZeroDivisionError`，不是首次零值兼容分支。不能以一个原生新建零对象替换代码
常量，或以一个字段快照消除动态重读。

Capture the self constructor before operand reads, retain its identity through
callbacks, and release ephemeral operands left-to-right before construction.
Native attribute reads use PyO3-interned names, preserving the original Python
name-object identities observed by dynamic `__getattribute__` hooks.
The Python division guard preserves its zero literal identity and first-read
sentinel; a later zero divisor still raises the original protocol exception.
DTO fields, object graphs, serialization, constants, and representation remain Python
integration rather than a second arithmetic implementation.

`__eq__/__ne__` 只接受现有 Floating 域，否则返回 `NotImplemented`；顺序读取
对方 `.value` 的原协议不扩大也不缩窄。`cmp` 仍先 `<`、必要时重新读取字段作 `>`，
两者均假时返回 `Order.EQ`（包括 NaN）；不能无说明地把它升级成 IEEE 全序。
`partial_cmp` 动态调用 `self.cmp`，保留继承重写和模块全局 Order 的求值。

Equality domain guards, ordered field reads, the legacy unordered-NaN `cmp` policy,
and dynamic subclass `partial_cmp` dispatch remain unchanged.

原生 `_FloatingOps` 只共享整数 helper 的两个 builtin callable 身份；GC 暴露并清理
这些实际字段引用；PyO3 另遍历实例的 heap type，清理字段后仅剩该类型引用。
不持有 DTO、字段、构造器或跨调用结果。外部回调不在原生锁或可变
借用下执行，可按 Python 协议重入；成功返回不额外保活输入对象。

The native helper traverses/clears its two builtin field references; PyO3 also
traverses the instance heap type, which remains after clearing the fields. It retains no
DTO, field, constructor, or result cache. External callbacks run without held
native locks or mutable borrows; successful results do not retain their sources.

## 错误与验收 / Errors and Acceptance

既有操作符仍返回值对象。外部原异常、原 traceback、处理中的 `sys.exception()`
以及 BaseException 必须原样保留，不格式化用户异常或失败后重试。数据类/数值协议
错误与新公共业务 Result 能力分开，不暗中改变全部操作符返回类型。

`test_floating_migration_contracts.py` 必须先在旧实现验证；新 binding 测试证明真正
原生边界及无 fallback。正式切换还须完成全部现有代数/转换/物理量消费者、真实
SCIP/Gurobi10及声明的其他版本/平台、完整公共调用与资源预算、wheel/sdist 仓库外
构建和安装、最低 NumPy 与无 SDK 验证。不能用 private helper 时间或只跑普通有限
f64 数据替代全部门槛。

Existing operators return values; original external failures and handled state
are preserved. Formal acceptance additionally requires full consumers, real solvers,
complete-call/resource budgets, isolated distribution, and the declared platform matrix.

同单位 `Quantity[Floating]` 的加减及对象图序列化有独立消费者合同，真实 MILP
通过显式 `.value` 适配构建系数、求解后再用公开 Floating 复验约束与目标。
这不代表全部物理量能力已经迁移。后续 `Quantity.to()` 源码候选已独立升级为
Result，以精确类型将 Floating 接入固定 Rust 有限 Float64 通道，不增加 `__float__`；
任意整数载荷必须先证明可无损表示。转换的符号零采用固定 Rust 顺序，与旧线性
公式的差异、显式 NumericAdapter 覆盖及 Decimal 规范表示见
[Quantity 合同](quantity-unit-contract.md)。物理量标量乘除、其他 helpers、温差和
完整数量验收仍独立 pending，不能用本包同单位测试或新增转换候选代替。

Same-unit quantities and real MILP adapters exercise public operations and object
graphs. The separate Quantity.to source candidate now returns Result and explicitly
routes Floating to pinned finite Float64 without adding __float__. Its signed-zero,
adapter and acceptance policies are documented in the quantity contract; scalar
operations, helpers and complete quantity replacement remain separate pending work.
