# 精确数值域与转换合同

本页定义 P3 的数值边界，不是公共数值 API 已完成替换的声明。固定 Rust revision 与 ADR 0001 一致；邻仓库的 WASM 开发不参与 Python 绑定构建。

## 数值域矩阵

| Python 输入/概念 | Rust 目标域 | 当前绑定边界 | 后续替换要求 |
| --- | --- | --- | --- |
| 任意精度 int | BigInt；有理数中分母为 1 | 私有 Rational 无损输入/输出，不经过 i64/f64 | 公共 Integer、UInteger、整数算法分别验收；无符号域拒绝负数 |
| Fraction / Rational | num-rational BigRational | 私有 Rational 精确四则、比较、倒数、规范化与 JSON；公共 Rational 源码计算候选 | 公共兼容、完整调用性能、领域预算与跨平台发行分别验收 |
| 有限 Decimal | BigDecimal 或精确分数适配 | 可无损导入 Rational；不读取当前 Decimal 运算精度；私有 `_binding` 已提供 `Rational.to_decimal`、`unit_conversion.convert_decimal` 等 BigDecimal 输入/输出桥 | 不把 Decimal 的 scale、舍入模式、尾零语义等同于 Rational；公共 `Quantity`/`PhysicalUnit` 的 Decimal 入口仍待验收 |
| float / Floating | f64 | 私有 Float64 solver 边界；公开 Floating 完整协议源码候选；Rational 仅显式 from_float | IEEE 特殊值、动态外部域和 DTO 见 public-floating-contract.md；完整预算/领域/平台仍待验收，不把 solver 有限值政策强加给通用浮点 |
| NumericInteger / NumericUInteger | 固定位宽且明确溢出政策的域 | 未切换 | 保留/审查饱和行为，不以 PyO3 溢出异常替代 |
| 自定义 RealNumber Protocol | 明确域派发/适配器 | 未切换，不声称可动态实例化任意 Rust 泛型 | 支持的域登记；其余结构化失败；Python 策略扩展不能静默 float 化 |
| Quantity / PhysicalUnit | 对应数值域与 Rust 单位/量纲 | 未切换 | 换算集中且精确；单位不相容、单位偏移和数值损失分别验收 |
| NumPy 数组 | 明确 dtype、形状与所有权的批量域 | 未切换 | view/复制、连续性、生命周期、只读与整数精度各自验收 |

`BigRational` 是固定版 ospf-rust-math 已支持的数值类型，而非新建的 Python 数学内核。绑定调用该版本的 `AddRef/SubRef/MulRef/DivRef/NegRef/Reciprocal` 实现；约分使用相同 num-rational 类型。原生精确比较适配以固定 OSPF BigInt `MulRef` 的无溢出交叉乘积与 BigInt Ord 组合，公共/私有入口共享，避免依赖 Ratio Ord 在长连分数上的进程栈耗尽；详见 RG-006。依赖显式与 Rust 锁定版本一致，不修改 Rust 通用 crate、不复制 Python 运算算法或增加依赖。

## 私有 Rational 合同

入口为 `ospf_python._binding.numeric.Rational`。公共 `ospf_python.math.algebra.number.rational.Rational` 已有源码计算候选，但未正式验收；兼容零值与严格错误政策不同，两者不混用。

- 唯一权威值为 frozen PyO3 对象中的 Rust `BigRational`；Python 门面只持一个原生句柄。分子/分母 getter 为拥有所有权的不可变快照，不缓存第二份值。
- 工厂与可能失败的操作返回既有三参 sealed Result。分母为 0、除数为 0、零的倒数均 Failed，不能 panic 或用 0 代替失败。失败不改变任何操作数。
- 分母始终为正、分数约分，0 规范化为 0/1。相等/hash 按本域规范值；不隐式声明与所有 Python 数值域跨类型相等。
- int 通过 PyO3 的 num-bigint 二进制桥接，不经过浮点或 Python 十进制字符串；超过 Python 十进制数字限制的大整数仍可传输。bool 不作为整数域隐式输入。
- `from_value` 只接受 int、Fraction、有限 Decimal。Fraction/Decimal 的 `as_integer_ratio` 是 Python 生态转换，不在 Python 中实现数学算法；Decimal 的当前精度 context 不改变已存储值。
- float 必须显式 `from_float`：保留其精确 IEEE 二进制值，不用 limit_denominator 推测用户的十进制意图。NaN/无穷失败；-0.0 进入精确域后为 0/1，不保留负零符号。
- `to_float(exact=True)` 默认拒绝任何舍入或下溢，返回 DATA_LOSS。只有显式 `exact=False` 才允许有损舍入/下溢；即使允许舍入，溢出至无穷仍 OVERFLOW。源值不变。
- 长整数运算在 Rust 中释放 GIL；不可变值可跨线程共享。此合同不扩展到 free-threaded CPython、多解释器或其他尚未验收 ABI。

## 一维精确批次

`_binding.numeric.RationalArray` 在一个 frozen 原生对象中持有 `Vec<BigRational>`。`create` 一次接收整数对的 list，Python 只作域校验并提交拥有所有权的输入；原生规范化后整批发布。任一输入失败不返回部分数组。输入 list、输出整数对快照、`at()` 取出的值都不与数组共享可变状态。

- `sum()`、`dot()` 在一次 FFI 中完成精确归约，直接返回 Rust 数值/Result，不先构建逐元素 Python Rational。空批次的和及两个空批次的点积为精确 0/1。
- `add/subtract/multiply/divide` 逐项调用固定 OSPF 运算 traits；返回新批次，不修改源数组。长度必须相同，无广播、截断或隐式 float 转换。
- `divide` 预检所有除数，任一为零就 Failed 并报告索引；不发布部分商。输入非法域/长度不匹配同样以 Result 返回。
- `at` 为零基非负索引；负值和任意精度超界整数均为 OUT_OF_RANGE，bool/非整数为输入失败。不使用 Python 负索引语义。
- 运算释放 GIL，拥有所有权的结果在源数组回收后仍有效。这是批量值边界，不是 NumPy view、通用多维数组、无复制桥接或 solver model 的替代。
- 测试覆盖真实扩展、Fraction 差分、失败原子性、快照隔离、线程与 GC；性能须对比单项调用、旧接口和包含创建的完整流程，不能仅宣传一次跨语言即一定更快。

## 精确快照

JSON schema 为 `ospf.rational`、version 为整数 1。numerator/denominator 使用规范十进制字符串，避免 JSON 消费端浮点/整数位宽损失。例子：

```json
{"schema":"ospf.rational","version":1,"numerator":"-3","denominator":"4"}
```

拒绝未知/缺失/重复字段、其他版本、非整数字符串、前导零或加号等非规范整数编码及零分母。合法输入恢复时由 Rust 规范化分数；序列化不通过 Python 的 int-to-decimal 限制或 float。此 schema 仅为值快照，不是模型、Quantity 或所有数值域的通用序列化 schema。

## 公共替换前必须处理

旧 Rational 的零分母/零除数静默返回 0；这与私有 Result 边界不同。公共计算候选保留该兼容政策，严格业务错误仍使用私有 Result。候选保留公开数据类、字段/copy/hash/pickle/Protocol，由 Rust 接管规范化和数值运算；原生规范结果在实际调用子类构造期间使用线程局部、RAII 清理的临时身份证明，避免同一整数对再次求 gcd，不缓存数值或跳过用户构造/后处理。规范结果子类构造、外部字段快照和精度/性能边界见 `public-rational-contract.md`。源码接通不等于正式验收，不因私有批量速度或数学正确性测试通过就标记 switched。

普通 gcd/lcm 在固定 Rust 版主要面向 usize/u64/i64，而 Python 入口接受任意精度 int；不能直接缩窄后宣称替换完成。精确数值和单位迁移不会以全局 float 化绕过这些差异。

验收测试位于 `tests/native/test_exact_numeric.py`，覆盖真实扩展、固定种子的 Fraction 独立差分、数值边界、浮点转换、严格快照、线程共享及来源对象释放。发行验证工具也在仓库外检查大整数和精度策略。阶段/平台执行证据只记入 logs，不在本页复制完成率。

## 显式 Decimal 输出边界

私有 `Rational.to_decimal(*, context=None, exact=True)` 为公共物理量迁移提供
精确域的输出适配，不是新建 Decimal 数学内核，也不切换公共 Quantity。
单位换算与有理数运算在固定 Rust 中完成；仅最终输出调用 Python 的
`Context.divide(Decimal(numerator), Decimal(denominator))`，以采用 Python 自己的
舍入模式、指数限制、flags 和 traps。整数构造精确，不经过 float、字符串或当前精度。

- `context=None` 在调用时取当前线程/异步任务的 Decimal context；显式 context
  使用原对象，不复制、不替换全局 context、不修改 precision/rounding/traps。
  输出产生的 flags 原位保留，连失败时也不清除已有或新产生的 flags。
- 默认 `exact=True` 在导出后将有限 Decimal 精确重新导入 Rust Rational，
  按数值比较判断是否损失；损失返回 DATA_LOSS。判断不依赖可能预置的 flags，
  也不把 Rounded（例如 1200 输出为 1.2E3）等同于数值改变。
  非终止十进制如 1/3 通常失败，不自行提高精度或返回伪精确值。
- 只有显式 `exact=False` 才接受 context 舍入的有限结果，包括有符号下溢零。
  溢出为非有限输出即使未设 trap 仍为 OVERFLOW；本出口不产生成功的 NaN/Infinity。
  这不是通用公开 Floating/Decimal 输入域的非有限值政策。
- 原生分数没有 Decimal quantum、尾零或负零元数据。导出表示由 context 决定，
  例如输入 1.23000 再输出可为 1.23，精确零为正零；不宣称 Decimal 表示级往返。
  公共 Decimal 的表示保留需求仍需在公共门面单独确定，不添加常驻 Python 数值镜像。
- Decimal traps 和 context 子类的外部异常变为既有 Result/ExErr，来源为
  `python-decimal`，原异常实例和 traceback/context 保存在
  `FailureContext.callback_exception`，不调用异常的 str/repr。
  Overflow/Underflow 分别映射同名码，Inexact/Rounded 映射 DATA_LOSS，其他外部
  Exception 映射 APPLICATION_ERROR；BaseException 原样传播，不吞中断。
- 接受真正的 Context 及其子类，允许外部 context 协议重入；返回值必须为内置
  Decimal，不将不透明输出再强转。非法 context/非 bool 的 exact 是输入失败，
  验证不读取任意对象可伪装的 `__class__` 属性。

测试 `tests/native/test_decimal_export.py` 对全部八种 Decimal 舍入模式、不同精度、
正负值、traps/flags、指数边界、超长整数、外部异常/中断、重入、线程和异步 task
上下文逐项验证。此出口不替代公共数值/物理量完整调用、领域或跨平台验收。
