# 公共 Rational 替换合同

此文档记录公共类的兼容边界与切换要求。源码默认路径已接通原生计算候选，但完整调用性能、领域预算与跨平台发行尚未验收，不登记为 switched。`_binding.numeric.Rational`/`RationalArray` 仍是不同签名的私有严格底座，不直接重导出为公共类。

## 公开表面

| 表面 | 当前合同 | 替换约束 |
| --- | --- | --- |
| 导入 | `math.algebra.number.Rational` 与深层 `math.algebra.number.rational.Rational` 是同一类 | 保持类身份与自然导入；不能引入供用户选择的 legacy 分支 |
| 构造 | `Rational(numerator: int, denominator: int = 1)`，支持位置/命名参数 | 私有工厂 keyword-only + Result 不能直接替换这个签名 |
| dataclass | frozen；仅 numerator/denominator 两个字段；`__match_args__` 为二者 | `fields/asdict/astuple/replace`、位置模式匹配必须保留；原生 handle 不得泄入公开 dataclass 数据 |
| 规范化 | 任意精度整数；约分、正分母、零为 0/1 | Rust 数值必须唯一负责数学运算；不以 i64/f64 限定旧域 |
| 算术 | `+ - * /`、取负直接返回 Self | 保留泛型 Protocol；不能把全部操作符返回值无说明改为 Result |
| 继承 | `self.__class__` 创建运算/copy/zero/one 结果 | 不能仅用 `__new__` 绕过自定义子类构造与不变量；普通子类应继续返回自身类型 |
| 相等/hash | Rational 及普通子类按规范数值比较；其他类型返回 NotImplemented；hash 等于分子/分母元组 hash | 不把原生 handle 身份用作数值相等或 hash；不要自动宣称与 Fraction/float 跨域相等 |
| 比较 | 精确全序，cmp/partial_cmp 返回既有 Order | 保留 `RealNumber` 及关联结构协议；不使用浮点近似比较 |
| repr | `Rational(n)` 或 `Rational(n/d)` | 原生类型名/地址不能取代现有表示 |
| copy/pickle | Python copy/deepcopy、各 pickle protocol、旧的仅含公开字段 payload 均能恢复可运算对象 | 仅让新对象 pickle 往返不足；须重建/验证 Rust 权威值，不能要求旧 payload 自带原生 handle |
| float_value | 显式属性进行有损整数比值转浮点 | 与私有默认 exact=True 导出不同；浮点精度及溢出政策需单独处理，不能悄悄改语义 |

## 零值与错误政策

当前测试明确要求：零分母构造得到 0，除以零得到 0。私有精确桥接则返回结构化 Failed，避免 num-rational 的零除 panic。

候选明确保留这些历史行为，仅用于既有公共数据类构造与操作符的兼容适配，不推荐新业务用 0 伪装失败。严格创建与运算仍走 `_binding.numeric.Rational.create/divide/reciprocal` 的既有 Result，不复用兼容零值政策。二者共享固定版 Rust BigRational/OSPF traits，不保留可选 Python 算法或隐式 fallback，也不更换公共操作符返回签名。

构造参数违反类型声明导致的快速失败属于规则中已存在的数据类不变量边界；这不允许在新业务/批量 API 中扩大异常 API 或抛裸 Exception。

## 源码候选与值所有权

- 唯一持久值仍为 frozen 数据类的 numerator/denominator 整数对；没有隐藏 native handle、全局缓存、第二份数值或新的 pickle 状态。每次调用临时建立 Rust BigRational，返回独立整数对后释放；不声称这是常驻 Rust-owned 对象。不可变编码是 Python DTO，规范化和数值运算的唯一实现位于 Rust。
- 构造委托原生规范化；精确整数直接用 BigRational。bool、NumPy 整数及其他整数协议输入仍保持旧的零分母短路、`__index__`、`//` 与符号调整协议；原生提供 Rust 约分因子，Python 不计算 gcd。外部协议异常对象原样传播，不格式化异常消息。
- 加、乘、除、取负调用固定 OSPF `AddRef/MulRef/DivRef/NegRef`；精确顺序共享原生比较适配：以固定 OSPF BigInt `MulRef` 形成无溢出的交叉乘积，再调用 BigInt Ord，不使用依赖中按连分数深度递归的 Ratio Ord。公共顺序、私有 compare/相等及私有精确 float 往返校验共享此适配，不回退 Python 数学；见 [RG-006](rust-gaps.md#rg-006num-rational)。正分母的已规范化字段可直接建立临时 raw ratio，无须每次输入重新求 gcd；非正分母在私有边界仍受检，不能 panic。任意手工破坏 frozen 字段、恶意 pickle 或并发属性改写不属于正常值对象合同。
- 减法继续组合 `self + (-other)`，`<=/>/>=` 和 cmp 继续调用原有 Python 操作符扩展点。它们是动态派发而非第二套数学算法。相等/hash/repr 保留规范字段的 DTO 比较、Python 元组 hash 与原表示。
- float_value 保留 CPython 的整数比值导出，含 ties-to-even、带符号下溢及 OverflowError；这是既有显式生态转换，不以私有 `to_float(exact=True)` 或 num-rational 的有损导出替换它。
- copy/pickle 保留标准 Python 图协议，含子类额外字段、自引用、重复引用和旧仅字段 payload；恢复后参与数学计算时从整数对重建 Rust 值，不要求历史文件携带原生句柄。

### 规范结果的构造作用域

原生算术完成后，在 Rust 中将规范结果转换成两个精确内置 `int`，并实际调用公共类或其子类构造器。构造器、`__post_init__` 和其中的用户逻辑仍然执行；不是通过 `__new__` 直接写字段。只有这次同步构造调用中的**同一对对象地址**，才可在原生 normalize 中复用已经完成的规范化，避免结果再次转换 BigInt 和求 gcd。

证明只是线程局部的临时地址对，不持有 Python/Rust 数值，不是跨操作缓存、隐藏字段或第二份权威值。Rust 栈上的两个强引用在构造期间阻止地址复用；RAII 在正常返回、Python Exception/BaseException 和 Rust unwind 时恢复上一层作用域。嵌套调用独立保存/恢复证明，其他线程不继承它；没有 Rust 借用、锁或 RefCell guard 跨越用户代码。

被证明的不可变整数参数可能直接成为结果字段，而不是再分配同值整数。子类不能把整数对象的 `is` 关系作为跨版本数值合同；构造器捕获仍发生在读取操作数字段之前，保留原调用表达式的 callable 求值点。字段值、类身份和对象图协议不因此改变，也不据此认证未知外部子类。

构造器替换任一参数（包括同值但不同身份的整数）、更改符号/分母、传入 NumPy 整数或其他整数协议对象时，仍执行原来的完整校验/规范化。证明不可由外部参数声明获得；只有原生运算已经规范化的结果能够在发布时建立它。取负对 raw 历史字段输入也先调用既有 Rust `reduced()`，不能因为临时 raw ratio 的分母为正就声称结果已经约分。构造退出后的普通创建与 pickle 恢复不享有该证明。

`test_rational_result_construction.py` 覆盖相同参数身份、变更参数、嵌套/线程隔离、构造异常对象与进程控制异常身份、退出清理、子类构造/后处理和仅字段恢复；Rust 单测另验证嵌套作用域和 unwind。这个边界优化不改变固定 Rust 的算术实现，也不解决 RG-003；减少重复计算不等于完整调用性能已达到门槛。

### 子类升级边界

运算结果仍实际调用 `self.__class__`，不以 `__new__` 绕过子类构造、不省略校验。Rust 返回的是**规范分子/分母**，而不是旧 Python 乘加中间的未约分参数；例如 `Rational(1, 2) + Rational(1, 2)` 的子类构造现在收到 `(1, 1)` 而不是 `(4, 4)`。依赖原始中间参数的外部构造器须升级；本地测试明确验证该区别，不宣称全部外部子类无差异。zero/one/copy 与除以零的原构造分支保留。

数值操作在读取一份左右分子/分母快照后执行；不承诺保留异常自定义属性 getter 与旧逐次交叉乘法交错的访问时序，也不执行自定义字段的乘法钩子。普通 Rational 子类的操作符覆写和构造器仍可扩展；字段必须表示整数域。未知扩展不能通过这次切片自动认证。上述候选差异与性能缺口均须在正式切换前验收，不以通过已有兼容测试替代。

## 仓库内调用审查

审查范围为当前 Python 包、测试、示例和基准。公共类的仓库内生产定义/重导出集中于 number/rational.py 与 number/__init__.py；代数概念和法则测试按结构性 Protocol 使用该类。普通数值转换/序列化函数主要消费 Python int/float/Fraction，不能将其 Fraction 输入误记为已消费或已替换公共 Rational。外部下游未在本地仓库中，不能根据本次扫描认定不存在外部扩展。

`tests/math/algebra/number/test_rational_compatibility.py` 保留构造、dataclass、继承、Protocol、pickle、copy、表示、严格差分基线。`test_rational_binding.py` 验证真实原生默认调用、独立 Fraction 差分、外部整数协议及异常身份、子类图恢复、规范结果构造和二进制大整数；`tests/native/test_public_rational_solver.py` 将公共计算与 pickle 后的精确值经显式精度检查接真实 Rust 求解后端。通过这些本地测试不等于性能、未知扩展或完整发行已验收。

`tests/native/test_rational_order_depth.py` 在独立进程验证长连分数（含旧实现栈溢出的深度）、正负/相等、全部公共顺序及私有比较/float精度政策，Fraction 为独立 oracle，并核对父/子进程扩展来源一致。不得以捕获 Python Exception 或 Rust panic 代替进程退出状态检查；栈耗尽可能直接终止进程。

## 切换门槛

1. 这些合同与既有代数测试在新唯一原生路径通过；对确有差异的行为同时提供明确兼容/升级决定。
2. 公共门面不再计算 gcd、精确域整数乘加/除法或大小比较；保留 DTO 字段相等/hash 和 CPython float 导出。不可变整数对与临时原生值的所有权要清晰，不引入两套持久数值状态。
3. 自定义子类构造、dataclass 提取和旧 pickle 恢复都不被优化路径绕过；不得将未知外部扩展伪称已验证。
4. 基准分别量出原生创建、逐项 FFI、Python 门面、批量归约与领域端到端。批量快不能抵销未说明的单项回归；反之，私有 Result 与旧裸值的微基准也不能直接当作领域预算判决。
5. 在 Windows/Linux 发行物中重验导入/类型/序列化及代表性业务；本机单平台证据不得扩展为全平台结论。

当前工作树候选已移除该类的 Python gcd/乘加/交叉比较实现，旧算法仅冻结在忽略的 logs 中用于差分，不作为运行时 fallback 或发行负载。源码路径已变化不代表门槛通过；上述全部验收满足后才能登记正式切换，不能将单项/批量测试抵销性能失败。实际执行与性能数据仅记入被忽略的 logs。
