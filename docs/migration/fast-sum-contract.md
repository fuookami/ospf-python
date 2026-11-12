# 公共 fast_sum 的替换合同

## 边界与状态

`ospf_python.math.multiarray.fast_sum.fast_sum` 尚未切换，仍使用原 NumPy 实现。
此文是切换前合同，不是新接口发布说明；`api-map.toml` 状态为 `specified`。
新增兼容测试通过不代表 Rust 归约、发行物或领域性能已经验收。
API map 的 `pending_acceptance` 显式列出待完成项；范围门禁拒绝在这些项仍非空时
标成 `verified`、`switched` 或 `legacy_removed`。这只验证已声明的前置一致性，
不自动证明消掉条目后行为正确。

固定上游 revision 为 `119854756a0aeb66d2998055f96fa7175c7bfb37`。
只在 Python 仓库研究绑定边界，不修改相邻 WASM 工作区，也不使用本地 path/patch。

Public `fast_sum` is still NumPy-backed. This is a pre-cutover contract, not a
published replacement API. Compatibility tests do not certify a Rust binding or
domain performance. The pinned upstream and the adjacent WASM workspace stay unchanged.

## 已观察的有效行为

当前签名为 `fast_sum(arr, *, axis: int | None = None) -> Any`。
`axis=None` 返回 Python `float`；指定轴返回独立、行布局的 `MultiArray`，
即使一维数值数组归约后 shape 为 `()`。标量返回的强制浮点包装是待升级边界，
不是泛型数值合同。测试明确区分当前包装与不能保留的数值损失。

| 输入域或边界 | 需要处理的行为 |
| --- | --- |
| bool、窄有符号整数 | NumPy 默认提升到平台整数累加；不能直接用源 dtype 归约 |
| 无符号整数 | 默认提升到平台无符号整数；与有符号域分开 |
| int64/uint64 | 累加为模整数；Rust debug 溢出 panic 不能成为错误合同 |
| float16 | 默认输出仍为 float16，但中间累加不能等同于逐次 float16 相加 |
| float32/float64 | 输出 dtype 保持；舍入次序不是逐项数学恒等式 |
| longdouble/clongdouble | 平台相关，Windows 别名不能证明 Linux 扩展精度已支持 |
| complex64/complex128 | 沿轴保持复数域；全量归约丢虚部是错误，不是兼容政策 |
| 非原生字节序 | NumPy 按输入值解释后给出正确提升结果，不可直接重解释字节 |
| object | Fraction/Decimal/下游加法对象必须审查，不能统一 float 或只接受一张白名单 |
| timedelta | 沿轴保留时间单位；NaT、溢出和全量标量出口需独立合同 |
| NaN/infinity/signed zero | 保留明确的 IEEE 政策，不能一律当非法 solver 系数拒绝 |
| 负轴/NumPy 整数轴 | 正常有效；先规范化再进入 Rust usize 轴边界 |
| rank-zero | 旧 NumPy 接受轴 0/-1；固定 Rust `sum_axis(0)` 拒绝，需要明确适配 |
| 共享、只读、负/零步长输入 | 读取原始值，不要求调用方交出共享存储；输出与输入不共享槽位 |
| 零长度维度 | 旧公共 DynShape 构造器拒绝，但私有 Rust Shape 支持；不是已发布的公共空数组承诺 |

未注解但 NumPy 运行时接受的 tuple 轴、`__index__` 对象、自定义 Shape 与 ndarray
子类协议需在最终升级清单中明确处置。当前审计没有确认这些扩展已全部穷尽，
不能因旧测试少而把有效输入缩窄为 Float64 的一维/二维行布局。

The matrix separates dtype promotion, modular integers, object arithmetic,
extended precision, units, layouts and external protocols. Runtime capabilities
outside the annotated axis signature still require review; they are not silently retired.

## 不能固化的旧缺陷

这些项目以 `strict=True` 的 xfail 保留预期正确结果；修复后必须移除对应 xfail，
不能将 xfail 当作切换验收通过。

| 编号 | 最小问题 | 处置 |
| --- | --- | --- |
| FS-001 | `(2,3,4)` 列布局，任一轴归约按 C reshape 得到错误结果 | 依据 shape 的真实布局归约，结果明确为行布局 |
| FS-002 | `[1+2j,3+4j]` 全量归约返回 4.0 并发出 ComplexWarning | 保留复数值 4+6j，不静默舍弃虚部 |
| FS-003 | int64 `[2**53,1]` 全量归约舍入成 `2**53` | 泛型出口不能强制 float；Float64 转换必须显式受检 |
| FS-004 | 一维 Fraction/Decimal object 数组沿轴归约读取叶的 `.shape` 而失败 | 用归约形状创建标量数组，不要求叶实现 ndarray 属性 |
| FS-005 | NumPy 吞掉 `__array_function__`/`__array_ufunc__` descriptor 查找异常，甚至 BaseException，然后继续默认归约 | 已声明 descriptor 的原普通异常映射 Result，控制异常原样传播，失败后不解析轴或归约 |
| FS-006 | axis 回调缩小 rank 后，NumPy 仍用初始 rank 的轴访问仅按最终 rank 初始化的 flags，可能读取未初始化字节 | 保留初始轴含义；最终不存在的轴安全返回 OUT_OF_RANGE，不复现未定义行为；其余合法 rank 变化正常归约 |

Known defects must be fixed explicitly, not blessed as compatibility. Strict
xfails are pending correctness requirements, never evidence of binding acceptance.

## 固定 Rust 的可用能力与差异

固定版 `ospf-rust-multiarray::FastSum` 已提供 `sum_all`、`sum_axis` 和 `sum_axes`。
源物理次序决定加法顺序，轴归约投影到新建的行布局数组。绑定应直接使用此能力，
不在 Python/native crate 另写归约循环，不把 ndarray 包装后仍调用 `np.sum` 称作迁移。

还须解决以下区别：

- `sum_all` 从 `T::zero()` 左折叠。NumPy 的浮点 pairwise 行为不同：
  `[1e16,1,1,1,1,1,1,-1e16]` 在已测 NumPy 返回 4，固定 Rust 返回 0。
  仅在普通数据上 `allclose` 不能证明取消误差合同相同；最终精度/误差预算尚未定稿。
- 非空 object 归约可从第一个叶开始，不要求 `0 + leaf`。直接套用 Rust `Zero`
  会破坏只有同域 `__add__` 的下游类型；不能为迁移而要求叶接受 Python int 0。
- `Wrapping<i64/u64>` 可实现模累加，但只是边界候选，不代表所有整数域已绑定。
- 不应直接暴露固定版 `sum_axes(&[])` 的列布局克隆：其默认行 shape 与原物理槽位
  没有统一。当前公共签名不需要通过这个分支实现 `axis=None`。
- 静态 rank 与静态 storage order 特化仍调用同一上游算法，属于合法绑定优化；
  本地动态/静态/固定布局探针均不能代替最终 FFI、数据转换和输出发布的测量。

The upstream owns reduction traversal. A binding may normalize dtype/axis and
specialize shape types, but must not duplicate the mathematical kernel. Roundoff,
object identity and scalar publication need explicit contracts before switching.

## 累加域可行性与未通过门槛 / Accumulator Feasibility and Unmet Gate

取消误差不是只有一个 Float64 标量的边缘问题：行/列布局、全量/轴/多轴的自然候选
在 float16/32/64、complex64/128 均有敏感输入失配。仅给 float16 提升到 float32
仍不够；512个65504、128个1、512个-65504的float16输入，已测NumPy沿轴得到128，
现有float32左折叠候选得到0。不能用普通随机数或相对较宽的allclose替代这些检查。

三种答案必须区分。对 `[1e16,1,1,1,1,1,1,-1e16]`：固定FastSum<Float64>得到0，
已测NumPy得到4，而输入二进制值的独立Fraction精确和为6。对float32的相同形式
（大值为2**24），本机已测NumPy为5，float32左折叠为0，提升到float64或精确域为6。
这些观察不是全部平台/版本的NumPy位级保证，也不授权把旧的4断言改为0或6。
数学精确、NumPy舍入次序、特定dtype/FPE兼容不是同一合同。

固定FastSum的既有BigRational泛型可在不新增归约循环的情况下，对**有限实数**的
精确二进制有理值求和。该诊断用Fraction逐组独立对照并输出分子/分母，避免只凭
最后一次float转换认定精确。但它不能直接作为浮点默认替代：

- 不表示NaN、正负无穷或负零的原始域信息；不能据此拒绝既有浮点有效输入。
- 有限输入也不保持部分和溢出的IEEE行为。`[max,max,-max,-max]` 的固定Float64
  左折叠产生无穷并设置overflow标记，精确域得0且无该标记；这会改变raise/warn/call
  等既有错误合同。只在最终转换补报错误无法恢复已发生的累加语义。
- 全部转有理数的分配、约分和转换有独立成本；纯Rust诊断计时不包含Python捕获、
  FFI/输出工厂/销毁，不构成完整操作或领域预算通过。float32局部提升也不解决
  float64/扩展精度、复数及全部非有限/FPE合同。

`tests/math/multiarray/test_fast_sum_roundoff_protocols.py` 保留五种dtype、轴和正负/
跨步输入的当前自然舍入基线；不增加xfail，也不将候选差异登记为通过。固定revision
的数值门槛见 [RG-007](rust-gaps.md#rg-007-fastsum)，与
RG-005的轴成本分开。生产路径和pin均未改变。后续应先确定并验证覆盖完整浮点域的
累加政策；需要通用内核能力时作为独立Rust前置处理，不在绑定复制pairwise/Kahan
算法，不默许精确域/加宽域替换，不新增NumPy默认求和fallback。

Pinned primitive accumulation, NumPy partial-pairwise results and exact rational sums
are demonstrably different. Reusing the pinned BigRational generic is a diagnostic,
not approval for an implicit float-domain change: IEEE specials, intermediate overflow,
error publication and complete costs remain incompatible. RG-007 is an unmet cutover
requirement, not a reason to stop independent fixed-revision migration work.

## Object 累加适配约束 / Object Accumulator Adapter Constraints

固定 `FastSum` 的 `Zero` 要求不意味着必须对 Python 叶执行 `0 + leaf`。
可研究一个仅在本次调用内存在的内部空槽：首次贡献直接保留该叶，后续贡献通过原始
Python 加法生成新累加值。空槽判定不得执行叶的真值、相等、反向加零或原地修改协议。
成功的 singleton 组保留原叶身份；空组的单位元、输出 dtype 和公共空形状支持仍需
按完整数值域政策分别定义，不能用 object 适配替代 numeric dtype 提升。

上游的 `AddAssign` 不返回错误。一个可验证的适配方向是共享本次调用的首错状态：
普通异常和 BaseException 都先保留原 PyErr，之后不再执行输入读取或外部加法，
遍历结束后由业务边界分别发布现有 Result 或传播控制异常。不格式化原异常，不在
外部协议调用期间持有锁或 RefCell 借用；嵌套求和必须有独立状态。
这仍让固定上游完成内部坐标循环，不是立即中止整个 Rust 循环；失败延迟、信号响应
及完整资源预算必须另外测量，不能因外部回调首错停止就认证响应性。

输入适配必须区分**固定源容器**和**固定全部输入叶**。当前有效 object 归约在操作开始
捕获 reshape 后的缓冲；加法回调对该缓冲后续槽位的修改可以被后续读取观察到，
但 owner 的 `_data` 重绑定不会重定向本次归约。预先采集全部叶会破坏这个合同。
隔离适配可以通过调用内槽位描述符在上游访问时晚读源，不能把源快照冒称 live 行为，
也不能为修复它增加跨调用 owner/叶缓存。成功结果只能保留真正返回的叶，不额外
保活源容器；失败 traceback 的合法保活与成功无缓存不是同一合同。

外部 `__add__` 可以返回 None、Ok、Failed、Fatal、Warn 或普通对象作为累加值。
最后一次加法返回这些对象时，它们是输出叶，而不是访问传输，不能递归解包。
如果后续仍需加法，是否支持由叶的真实协议决定，而不是绑定的类型白名单。

`tests/math/multiarray/test_fast_sum_object_protocols.py` 在当前自然入口保护这些有效
行为：首叶 identity、非原地加法、Result 叶、捕获缓冲的晚读/重绑定差别，以及原异常
对象、既有 traceback、handled state、BaseException 和全组首错停止。
这是切换前协议基线；命名入口未来的显式 Result 升级仍须同步调整调用方式。

以上方向已在隔离测试模块中直接实例化固定上游 FastSum 验证；**未接入生产默认路径**。
实验不认证原始 ndarray 子类的 reshape/ufunc 协议、全部 dtype/时间单位、浮点误差、
tuple/负轴/标量轴规范化、空轴集合、公共输出发布或发行物。输入描述符的 O(n) 存储和
逐槽外部协议成本也没有通过完整性能预算；RG-005 和 FS-001/002/003/004 均未关闭。

An invocation-local vacant accumulator can avoid imposing integer-zero arithmetic on
arbitrary object leaves. A shared first-error latch must suppress later external reads
and additions without borrowing across callbacks. Late reads of one captured buffer
are not a leaf snapshot and do not follow owner rebinding. This remains an isolated
adapter experiment, not a public implementation, numeric-domain whitelist or cutover.

## 轴与 ndarray 分派次序 / Axis and ndarray Dispatch Order

标准 ndarray 的轴转换不能作为所有输入的统一预检。当前有效顺序是先捕获
`arr._data.reshape` callable，再读取 `arr.shape.dims` 并调用 reshape；其返回值不一定
是精确 ndarray。NumPy 的 `__array_function__`、自定义 `sum` 和 `__array_ufunc__`
可以在轴整数转换之前接管归约。真实覆盖可以接受任意轴对象，甚至在接管操作时接受
标准路径会拒绝的超长轴 tuple；绑定不能先执行 `__index__` 或 rank 检查再调用覆盖。

这些是真正的外部扩展点，不是为继承的默认 ndarray 求和保留旧数学内核的理由。
未来默认标准路径必须由固定 Rust 归约；需要区分真正覆盖与继承默认实现，不能仅按
owner 类型猜测，也不能在原生失败后调用 `np.sum` fallback。外部扩展的接入与输出
协议还须有完整候选验证，隔离轴解析器本身没有实现这些分派。

轴归一化须区分以下行为，不能只用 Python `int(axis)` 或无条件转换成 usize：

- None 表示全量；空 tuple 表示不删除任何轴，但仍可能发生 dtype 提升及独立输出。
  不能直接用固定 Rust 存在列布局问题的 `sum_axes(&[])` 克隆作为正确实现。
- rank-zero 的非 tuple 整数 0/-1 是有效特殊情况；tuple `(0,)`/`(-1,)` 则越界。
  标量轴出口和全量出口的公开载体仍需在 Result 升级时分别说明。
- 负轴、NumPy 整数及合法零维整数 ndarray 由整数协议解释；bool/NumPy bool、浮点、
  非零维数组等不能通过宽松 int 转换混入。原始 `__index__` 异常不得被新异常替换。
- tuple 子类使用真实 tuple 内容，不执行其 Python `__iter__`、`__len__` 或
  `__getitem__` 覆盖；int 子类同样保留实际整数转换路径，而非主动调用替换的方法。
- tuple 各项按顺序完成整数及边界检查，随后才检测规范化后的重复轴。
  `(Axis(0), Axis(0), Axis(9))` 在 rank 2 下先得到第三项越界，不能提前以重复轴失败；
  若第三项 `__index__` 抛原始异常，也必须保留它。首个转换/越界失败后不消费后续项。
- 已观察的 NumPy 2.x 在超过 64 个 tuple 轴时先拒绝，不调用任何项的整数协议；
  64 个轴仍先完成转换再检查重复。容量检查不能前移到真实外部覆盖之前。

隔离轴适配复用 NumPy 稳定的 `PyArray_AxisConverter` C API 执行整数转换，只返回
拥有整数的轴计划或已有 Failure DTO；不执行求和、不保活 axis/owner，也不缓存用户
协议结果。全量、正常轴集、空轴集与 scalar identity 在内部明确分开。自定义协议异常
保留原 PyErr 和既有 traceback；公开 Result 发布与真正默认 dispatcher 尚未接入。
该实验的 NumPy 2.x 容量约束不是最终跨版本 ABI 政策；现有 metadata 的 `numpy>=1.26`
和 `requires-python>=3.13` 均未被此实验更改，不能仅从本机版本推高依赖下限或宣称
所有可安装组合已认证。

沿轴结果的实际 `.shape` 先求值，再解析当前 DynShape 工厂；该工厂成功后才调用
结果的 `.flatten`，最后解析当前 MultiArray 工厂。全量的旧 float 包装属于前述显式
泛型升级，不应把它当作所有新数值域必须保留的合同。替换默认内核时不能通过提前
捕获工厂、强制 ndarray 输出或额外探测 dtype 改变真实扩展的发布/首错顺序。

`tests/math/multiarray/test_fast_sum_dispatch.py` 保护自然入口的有效轴、容量/消费顺序、
三个真实扩展层的原异常/handled state、原始轴身份及 reshape/发布求值次序。
这些仍是切换前基线；它们不认证新的 dispatcher、全部 dtype/误差、性能或发行物。

External NumPy overrides may own the axis protocol before integer conversion. The
normalizer belongs after selecting the standard path, not before extension dispatch.
Tuple conversion/bounds precede duplicate detection; empty axes and scalar identities
remain distinct. The isolated C-API adapter performs no summation and does not certify
the public dispatcher, dtype policy or a cross-version ABI decision.

## 已捕获 object 管线的整合约束 / Captured Object Pipeline Integration

在真正扩展分派已完成、调用内源元数据已经取得后，可以将拥有整数的轴计划与
object 晚读适配组合。该内部边界不能冒充完整自然入口：它不负责选择 ndarray
真实覆盖，不证明 owner 的 reshape/shape 捕获次序，也不将其他 dtype 拒绝后退回
NumPy 求和。数值 dtype 的完整政策和默认 dispatcher 仍是原子切换前置。

标准 object 输入可以来自共享、只读、非连续或负步长的一维物理缓冲。轴的
`__index__` 会执行用户代码，可能写入槽位或改变 ndarray header；轴协议之后必须
重新核对实际 rank、dtype 和存储容量。之后从同一个捕获缓冲晚读，不缓存裸数据
指针，也不把 owner 重绑定后的存储替换进本次归约。加法过程中 header 再失效的
完整语义、并发同步与资源响应仍须另验，不能由此单次重检认证全部失效路径。

进入固定上游之前还须防止 shape/stride 与描述符字节容量溢出。私有零维度不能
掩盖其他非零维度乘积的溢出：删除零长度轴后可能得到非空归约输出。隔离管线以
非零维度乘积和实际描述符大小建立保守实验包络，越界返回结构化 OVERFLOW，
不执行巨大分配；这不是全部可表示空形状的最终公共支持政策，也不认证实际
内存不足时的资源恢复、分配延迟或常驻内存预算。

空轴集合只产生逻辑行序的独立输出，不执行外部加法。可以直接复用固定上游
`MultiArray::flatten(AccessOrder::RowMajor)` 重排调用内描述符，再读取实际叶；
不另写坐标公式，也不调用有列布局问题的 `sum_axes(&[])`。scalar identity 同样
与真正的全量归约分开。非空轴和全量仍由固定 `FastSum` 完成归约。

归约形状由上游结果决定，不从最后一个叶的 `.shape` 推断。输出 object ndarray
须从拥有的 Python 引用构造，不能通过 `np.asarray(leaves)` 等序列推断让任意叶的
`__array__`、长度或嵌套形状协议抢先运行。None、Result、list、ndarray 和下游对象
均可作为不透明叶；singleton 保留其身份，独立输出只隔离槽位，不深复制叶。

全量的泛型候选直接保留归约叶，不强制 float；指定轴的候选按实际输出 shape
创建当前 DynShape，再 flatten，最后解析当前 MultiArray。普通外部异常以原对象
及既有 traceback 进入现有 FailureContext；BaseException 传播。工厂返回的 None
或 Result 仍是数据，只包一次 outer Ok；成功发布器自身的异常不在同一业务边界
重新捕获。成功结果不得额外保活源容器或轴协议 owner，嵌套调用状态必须独立。

这些整合约束已在隔离的已捕获 object 管线验证；**生产 fast_sum 尚未使用该管线**。
私有零长度形状观察不扩大公共 DynShape 的空形状支持，不等于 FS 缺陷已在自然入口
修复。完整 dtype/时间单位/误差、真实扩展分派、GC/并发失效、性能/资源/响应、
solver 消费者与 wheel/sdist 仍须全部满足，才可以删除旧默认内核。

The integrated experiment starts after real extension dispatch and metadata capture.
Pinned row-order flattening handles empty-axis copies without another coordinate
kernel. Owned object references preserve opaque leaves without array coercion;
upstream shape metadata handles scalar-array publication. This does not certify the
public dispatcher, numeric dtype policy, concurrency, performance or distribution.

## 数值累加与错误状态 / Numeric Accumulation and Error State

标准数值路径的类型政策不能直接套用 object 的首叶 identity：bool/窄整数需要默认
整数提升；有符号和无符号整数分别按目标位宽模累加，不能过浮点或让 debug overflow
成为错误。float16 的中间累加至少需要 float32，float32/64 与 complex64/128 保留
各自域。非原生字节序须先正确转换；输出 dtype 使用本机字节序，并保留时间单位。
泛型全量出口不执行旧 float 包装。

数值空轴与 scalar identity 仍执行 typed zero 加法。例如 `sum([-0.], axis=())`
产生正零；只复制输入会错误地保留负零，不能把 object singleton 不加零的合同套给
numeric。隔离候选以内部新增 extent=1 的轴委托同一固定 FastSum，归约后恢复原
rank/行布局，不另写坐标或归约循环。内部 Rust rank 可以暂为65，最终 NumPy 输出
仍不超过64；这不是扩大公共 rank 政策。

轴协议能修改 dtype、槽值和错误状态。已观察 NumPy2.5.4与2.1.0均在 `__index__`
完成后使用当前 dtype 和错误政策；先前 int8 的 [-1,2] 在轴回调改成 uint8 后得到
uint64 的257，回调将 overflow 改为 raise 也立即生效。真正扩展分派仍须早于该
标准路径。这里的 dtype 是**实际捕获的 reshape 结果**的 header；只改 owner 原缓冲
的 dtype，不会改掉已创建 view 的 dtype。自然入口在后一种情况下仍按 int8 求和
得到 int64 的1，不能把直接 np.sum 原缓冲的257错误推广给自然调用。反过来，轴回调
直接修改捕获 view 的 dtype 确实得到257，两种行为都必须保留。
数值候选在轴后重检标准缓冲，转换成独立本机 dtype 快照，再转拥有的
Rust Vec 执行固定归约；不在外部 callback/signal 期间持有 ndarray 数据借用。
这与 object 必须从捕获缓冲晚读的协议不同，不认证无同步的并发写入。

浮点归约还须遵守 NumPy 的 ignore/warn/raise/call/log/print 政策；不能只返回 inf
或 NaN，也不能借格式化异常构造失败。原 handler 的异常对象、既有 traceback、
handled state 和 BaseException 均按原规则保留。隔离 primitive 桥读取本线程硬件
浮点状态，并经公开 `PyUFunc_GiveFloatingpointErrors("reduce", flags)` 发布，
不调用 NumPy 求和。该入口在 NumPy2.0起的公开 ufunc capsule 第46槽，两份实装
头文件签名一致；不能访问已删除的 checkfperr 槽。实验使用运行时 ABI guard，
不据此擅改现有 numpy>=1.26 metadata 或宣称所有版本已认证。

timedelta 的错误政策不能一律定义为裸 int64 wrapping。实测2.5.4在若干超限加法
抛 OverflowError，而2.1.0的结果不同；两个版本对同一输入有不同有效结果。扩展
浮点/复数的表示也与平台有关。隔离候选以真实 NumPy scalar 算术适配这些域，
遍历仍由固定 FastSum 负责，不经 Python float、不调用 np.sum，也不靠版本字符串
猜算术政策。本机 longdouble/clongdouble 的验证不认证 Linux 扩展精度或资源预算。

仍有明确的**未通过边界**：固定左折叠的取消误差示例得到0而 NumPy得到4；float16
输出转换目前在 cast 而非 reduce 发布 overflow；扩展 scalar 的多次错误合并、消息
和 callback 时点仍须与完整归约一致。不得因为正常数值矩阵通过而关闭这些前置，
也不得通过放宽原 oracle/预算或保留默认 NumPy 求和 fallback 绕过。

`tests/math/multiarray/test_fast_sum_numeric_protocols.py` 保护现有自然入口的错误模式、
原 handler 异常、轴副作用和数值空轴符号零；它不是新候选的默认切换证明。
完整 dtype/精度/错误边界、真正 dispatcher、性能/响应/资源和发行仍须一起验收。

Numeric empty axes still require typed-zero arithmetic, unlike opaque object leaves.
The candidate uses a unit-axis lift with pinned FastSum, not a second reduction kernel.
Primitive FPE publication uses the documented NumPy API; timedelta arithmetic follows
the installed scalar policy rather than a hard-coded wrapping assumption. Cancellation,
half-output error timing and extended-scalar error aggregation remain explicit cutover
blockers. The public default and dependency metadata are unchanged.

## 归约末尾浮点错误发布 / Reduction-End Floating Error Publication

上一节记录的 half cast 消息和扩展 scalar 逐次发布问题属于此前的数值候选，
不能作为新编排的默认行为。后续隔离编排收集整个归约的错误位，在恢复原错误
上下文后只调用一次共享的 `PyUFunc_GiveFloatingpointErrors("reduce", flags)`。
该改进仍是隔离候选，不是生产入口切换，也不解决固定左折叠的取消误差。

用户轴对象的 `__index__` 必须在原始错误上下文中执行一次；其自身触发的浮点
错误立即按原政策处理，轴回调对 policy/handler 的修改随后保持有效。不能为了
收集归约错误而提前覆盖轴协议的上下文。内部再次解析时只接收自有普通整数、
tuple 或 None，不重复调用用户轴协议。

归约阶段借标准 `np.errstate(all="call", call=recorder)` 收集 primitive 归约、
half 输出转换和扩展 scalar 算术的错误位，recorder 只按位 OR，不执行用户
handler、不保留输入或轴引用。算术与遍历仍委托现有数值适配及固定 FastSum，
不新增第二套数学归约，不回退 `np.sum`。标准 Python `with` 负责成功、普通异常
及 BaseException 的上下文恢复，不能用 `__exit__(None, None, None)` 伪造异常退出。

上下文恢复后再发布合并 flags，消息属于 reduce 而非 cast/scalar add。多个输出组
同时产生 overflow/invalid 时，应发布合并位10，并依 NumPy 的顺序先 overflow、
再 invalid；不是逐叶或逐组运行用户 callback。handler 中可修改原 policy、替换
handler 或重入；本次已捕获的 publisher 仍完成自己的发布，修改对之后调用有效。
发布期间不持有 recorder 借用或锁，普通外部异常保留原对象和既有 traceback，
BaseException 原样传播，既有 handled exception state 不得被覆盖。

最终错误发布早于公开 shape/array 工厂。raise 或 handler 失败不能发布部分数组；
成功 handler 对晚取工厂的替换仍须生效。线程使用各自的 policy/handler，不将
线程局部错误配置缓存为全局状态。注入 NumPy 工厂失败可用于检查清理路径，
但不能据此声称任意 NumPy monkeypatch、signal 或扩展分派已认证。

`tests/math/multiarray/test_fast_sum_fpe_publication.py` 固定自然入口与独立 NumPy
的 ignore/warn/raise/call/log/print、handler 修改/重入及原异常合同。隔离编排
仍需经过完整原生矩阵和现有合同回归；它并未导入生产扩展。每次构造 Python
上下文 helper 的分配和编排成本尚未计入完整调用预算，不能将功能测试当作性能
或 wheel/sdist 验收。本机扩展 scalar 观察不代表 Linux 扩展精度。

The isolated orchestration aggregates flags across the entire reduction, restores the
original context with a real Python `with`, then publishes through the existing NumPy
API exactly once. User axis protocols run first and only once. This addresses the
previous half-output and extended-scalar FPE publication gaps, not cancellation,
complete dispatch, performance, distribution, or the unchanged production default.

## 已捕获缓冲的扩展分派 / Extension Dispatch of Captured Buffers

隔离分派器接收已经捕获的逻辑缓冲；这不是最终 owner/reshape 入口，不认证该入口的
属性查找次序、列布局 reshape 或完整 Shape 权威。标准 ndarray 与只继承默认协议的
子类不能因此继续执行 NumPy 求和；默认归约仍委托固定 FastSum。显式重赋值为相同
ndarray 默认方法不构成真实覆盖。对非 ndarray 对象，挂上 ndarray 的未绑定 descriptor
不构成合法继承，不能把其 TypeError 静默当作标准路径。

真实 `__array_function__` 先于普通 sum 查找、ufunc 和轴解析；它收到原 `np.sum`
函数身份、单一相关类型、原输入及原轴对象。None 轴对应缺省 kwargs，不擅自附加
`axis=None`。特殊协议在类型上查找，descriptor 绑定时 instance 为 None，并在调用
时显式传入原输入；实例的同名特殊属性被忽略。metaclass 的正常类型查找及跨调用
重绑定仍须可观察，不缓存协议 callable。普通 sum 则按正常实例属性规则查找，
传递 axis/out；descriptor/实例方法覆盖不能被按类猜测丢掉。

继承的 ndarray sum 不是外部覆盖；若存在真实 `__array_ufunc__`，将原 np.add、
reduce、输入和未经转换的轴交给它。ndarray 默认 sum 触发的 ufunc kwargs 包括
dtype/keepdims/where，而普通非 ndarray 的 reduce 路径不补 keepdims/where；
两实装 NumPy 版本已用于核对该差异。只有真正覆盖可以自行选择委托 NumPy，绑定
不能在其拒绝或失败后偷偷执行默认求和。

`__array_function__`/`__array_ufunc__` 的 NotImplemented 表示拒绝，或 ufunc=None
表示禁用时，候选返回现有 NOT_SUPPORTED，不解析轴或调用默认数学内核。这是 Result
升级后的明确拒绝出口，不将旧 NumPy 新建的 TypeError 包装成用户原异常。普通 sum
方法的 NotImplemented 则只是返回数据；全量泛型出口须保留它，不能误当传输拒绝。
同样，外部覆盖返回 None/Ok/Failed/Fatal/Warn 等时，不递归解包输出叶。

FS-005 是单独的失败规则修复，不是有效协议兼容。已观察 NumPy2.5.4与2.1.0均吞掉
descriptor 的 ValueError/TypeError/AttributeError/控制异常并继续归约。新候选通过
静态识别已声明协议、再执行正常类型查找，区分“未定义”与 descriptor 自身抛出
AttributeError，保留后者原对象/traceback/handled state；BaseException 不得吞掉。
自然入口的18项 strict xfail 保持可见，只有真正默认切换并去掉 xfail 才能关闭 FS-005。

标准路径在真正分派后先解析一次用户轴，再创建基础 ndarray view、读取当前 dtype。
因此轴回调修改实际捕获 header 或槽位仍有效。object 的任意跨步逻辑缓冲使用 flatiter
晚读，列遍历只调整基础 view 的轴序；不通过 flatten/reshape 预采集全部 object 叶。
归约坐标与加法顺序仍由固定 FastSum 接管。numeric 沿用已有独立快照及统一 FPE
发布，不能用 object 晚读政策代替 numeric 政策。输出 shape/flatten/array 工厂按原顺序
晚取，失败不发布部分数组，成功不额外保活输入。

`tests/math/multiarray/test_fast_sum_extension_protocols.py` 保护自然入口的继承、
descriptor、实例覆盖、跨调用重绑定及拒绝合同，并显式暴露 FS-005；它不是默认
Rust 切换证明。捕获层候选不认证 owner 入口、全部扩展或动态 NumPy monkeypatch、
取消误差、完整性能/响应/GC/发行预算，且不改变 NumPy metadata 下限。

The captured-buffer dispatcher separates genuine extensions from inherited defaults.
Only explicit external hooks may delegate to NumPy; inherited defaults use pinned
FastSum, never a fallback. Declared descriptor errors are preserved rather than
suppressed as NumPy currently does (FS-005). Owner capture, roundoff, complete budgets
and distribution remain separate cutover requirements.

## 自然入口捕获与物理布局 / Natural Capture and Physical Layout

自然入口候选复用捕获层 dispatcher，按原表达式顺序获取 `_data`、其 reshape
callable、owner.shape、shape.dims，然后调用已经捕获的 reshape。后续 owner/data/
shape/callable 重绑定不重定向本次操作；dims 不在 reshape 前另作迭代或整数转换。
捕获阶段普通外部异常进入现有 FailureContext，保留原对象、既有 traceback 和
handled state，BaseException 原样传播；失败不继续读取后续属性或解析 axis。

标准布局识别同时要求**精确的公共 Shape1/2/3/4/DynShape 类型**和实际继承的
ndarray reshape callable。只认标准 storage-order 枚举身份，不执行未知对象的
真值、相等或字符串化；被破坏的标准布局字段返回结构化 ILLEGAL_ARGUMENT。
自定义 Shape 或真正 reshape 覆盖不被猜作标准映射，不额外读取其 storage_order，
调用仍只有原 dims 参数；这既不退役自定义映射，也不认证其完整权威策略。

即使标准列布局，仍保留原 C-reshape 捕获表达式。真实外部覆盖收到同一个捕获对象，
原轴及分派时点不变。只有进入默认 Rust 路径后，才将其 C-flat 槽位与已捕获的
逻辑 dims/column order 组合，交固定 FastSum 投影。不能直接将多维 backing 按
F 次序 reshape：backing 的 rank/strides 不等于公共 Shape 的物理槽位合同。
对本来就是多维、转置或负步长 backing，C-flat 物理序列仍先于列坐标解释；不另写
坐标或数学归约循环。原 reshape 必须复制时，本次捕获的就是该独立结果；不是随后
跟随 owner 或原 backing 重绑定。

捕获的 view header 与 owner 原缓冲 header 不是同一对象。轴回调只改原 backing
dtype，不会自动改变捕获 view 的 dtype；直接改捕获 view 才对本次归约有效。
同 rank 的 shape extent 修改在轴协议之后重新读取，用户 `__index__` 不执行第二次。
object 沿用捕获缓冲的晚读，numeric 沿用独立快照与统一 FPE 发布，成功输出不额外
保活 owner/源容器。标量泛型出口不调用 float，复数、大整数、Fraction/Decimal 和
外部 opaque/Result 叶不因包装丢域；沿轴 scalar-array 使用归约 shape，而非叶.shape。

轴回调改变 rank 的初版候选曾显式返回 NOT_SUPPORTED；后续安全候选已取消一律拒绝，
按下一节保留初始轴解释并使用最终 header。此前两版各35项观察中的最终失效轴结果
不再充当正确性 oracle；这不是将合法动态 rank 输入退役或默许原版不确定行为。

`tests/math/multiarray/test_fast_sum_owner_protocols.py` 在当前自然入口保护捕获首错、
重绑定、同 rank header 副作用、输出失败/原异常和未知映射合同。自然候选在隔离
测试内组合原 dispatcher/数值/object/FPE 管线；生产扩展与自然入口均未切换。
完整 Shape 权威、动态 header 的生产集成、取消误差、端到端性能/响应/GC/资源及
wheel/sdist/真实消费者仍是切换前置，不以局部候选替代完整公共操作。

The natural candidate preserves the original capture expression and external dispatch.
Canonical column projection happens in pinned Rust over C-flat physical slots, not by
reading an ND backing in F order. Same-rank header mutations are observed after axis
conversion; the safe dynamic-rank candidate below supersedes the initial blanket refusal.
The production entry and extension are unchanged.

## 动态 Rank 与安全轴复验 / Dynamic Rank and Safe Axis Revalidation

NumPy v2.1.0 和 v2.5.4 的 `numpy/_core/src/umath/ufunc_object.c` 均先读取输入
rank，再调用轴的 `__index__`，按初始 rank 规范化负轴和做边界检查。
`PyUFunc_Reduce` 随后重新读取实际 rank，只以该长度 `memset(axis_flags, 0, ndim)`，
却仍直接读取旧 `axis_flags[axis]`，不重新验证轴。因此缩小 rank 后仍指向被删维度
的轴可能读到未初始化字节。此前偶发的输出或重复轴异常不是稳定协议，不应复制。
这一安全缺陷单列 FS-006，不把它与合法动态 rank 的兼容混为一谈，也不以执行这些
不确定归约作为测试 oracle。源码核对不等于已认证全部 NumPy 版本或平台。

隔离自然入口候选采用以下合同，仍未切换公共默认：

- 用户轴转换只执行一次，负轴按初始 rank 规范化，初始越界立即失败，不因回调扩维
  而重新变成合法。tuple 所有转换/初始边界检查完成后才检查重复，维持既有首错顺序。
- 初始 rank-zero 的非 tuple 整数 0/-1 解释为**空轴 tuple**，而非最终 rank 的轴0。
  即使回调把 scalar 扩为 `(1,1)` 或 rank64，仍保留最终完整 shape 和 dtype/空轴规则。
- 所有轴回调完成后重新读取捕获 view 的完整 dims/dtype。普通拥有整数 tuple 交给既有
  原生轴计划作最终边界复验；不再运行用户 `__index__`，不重解释负轴、不丢弃失效轴。
- 最终 rank 中仍存在的规范轴正常归约，包括扩维及安全缩维；最终不存在的轴返回
  现有 OUT_OF_RANGE Result。非 scalar 变为 scalar 后的原轴0也失效，不能重新触发
  scalar 0/-1 特例。失败早于算术、FPE handler 和输出工厂，不发布部分结果。
- 后续轴 callback 的原异常优先于最终复验；保留异常对象、既有 traceback、handled
  state 与控制异常传播。观察最终一次 header 副作用，仍不跟随 owner 数据重绑定。
- C-flat 物理槽位/逻辑缓冲的两种内部捕获合同不变，最终 dims 的行/列投影与全部
  数学遍历仍交固定 FastSum，object 保留晚读，numeric 保留拥有快照和统一FPE发布；
  不新增 NumPy 默认求和 fallback 或第二套坐标/归约循环。

rank64 的真实红灯还暴露 NumPy `flatiter` 仅支持32维，不能将该内部迭代器限制当作
公共 object rank 上限。候选在最终 rank 大于32时使用 call-local 原生槽位 accessor：
只持有捕获的精确基础 ndarray 与受检固定行布局 Shape，每次读取由上游 `vector_of`
取得 C-flat 坐标并对同一 ndarray 作 tuple 访问，不预复制叶、不重写坐标公式、不用
NumPy 求和；其余 rank 仍沿用 flatiter。每次晚读复核 header/dtype，失效则停止。
原生 holder 的强引用纳入 traverse/clear；成功返回不保活源。此局部引用检查不等于
解决 NumPy object buffer 的全局循环 GC/AS-001，也不认证低 rank 加法期间所有 header
失效策略、并发、完整性能或资源预算。

`tests/math/multiarray/test_fast_sum_rank_protocols.py` 保护当前自然入口中安全合法的
rank 变化和首错合同，不执行失效最终轴的 NumPy 归约。FS-006 的安全拒绝在隔离原生
候选中覆盖；只有生产默认升级、回归和发行验收后才能关闭。当前 api-map 仍为
specified，动态 header 的生产集成和完整资源/响应策略继续 pending。

Axis conversion uses the initial rank exactly once; the captured post-callback header
supplies final extents and dtype. Owned normalized integer axes are safely revalidated
against the final rank, with OUT_OF_RANGE instead of uninitialized-flag behavior.
Scalar 0/-1 retains empty-axis semantics across rank growth. Valid dynamic inputs are
not retired; neither the public entry nor production extension has switched yet.

## 原子切换门槛

1. 自然名统一返回现有三参 sealed `BindingResult`，同时更新原调用方、重导出、
   类型、示例和升级说明。该签名变更尚未实施；不增加隐藏 legacy backend 或新业务异常。
2. 泛型全量出口保留数值域；需要 Float64 的求解边界沿用显式受检转换。
   明确 NumPy dtype 提升、模整数、扩展浮点/复数、object 与时间单位的处置。
3. 标准布局不得调用旧 Python 索引/求和内核；自定义映射或协议不能被猜测为标准映射。
   明确共享输入快照时机、并发同步、外部回调副作用和输出所有权。
4. 外部加法/转换普通异常映射到现有 FailureContext，保留原对象/traceback；
   BaseException 按进程控制协议传播。不在持锁时调用外部协议，不发布部分数组。
5. 去掉 FS-001/002/003/004/005 的 xfail 并验收 FS-006 的安全失败合同；数值域、非对称多维布局、空/标量、
   非有限值和取消误差测试全部验收。现有包装测试随显式升级而调整，不能掩盖数值损失。
6. 包含输入适配、FFI、归约、输出转换/销毁的候选绑定通过代表性性能与资源预算，
   再通过真实 solver/领域消费者和 wheel/sdist 隔离验收。纯 Rust 下界不能算预算通过。

Only then can this capability become `switched` and the NumPy implementation be
removed. No partial Float64-only implementation is substituted for the current public operation.

## 可复现检查

兼容合同：

```powershell
& logs/p0-venv/Scripts/python.exe -m pytest tests/math/multiarray/test_fast_sum.py tests/math/multiarray/test_fast_sum_compatibility.py
```

当前 Python 仓库的被忽略目录 `logs/p3/fast-sum-audit/` 保存纯 Rust release 探针、
独立 Cargo.lock 和九轮交替测量脚本；所有 OSPF Git 依赖固定到同一 revision。
测量比较已有 Rust 数组、克隆输入下界、正确布局的 NumPy 和旧公共操作；
进程启动/JSON 不计入 Rust 时间，后者也不含 FFI/输出转换。
列布局的旧公共输出有 FS-001，不能拿它当正确性 oracle；独立 NumPy 逻辑布局才是 oracle。

```powershell
$env:CARGO_TARGET_DIR = (Resolve-Path native/target).Path
cargo test --release --locked --manifest-path logs/p3/fast-sum-audit/probe/Cargo.toml
cargo build --release --locked --manifest-path logs/p3/fast-sum-audit/probe/Cargo.toml
& logs/p0-venv/Scripts/python.exe logs/p3/fast-sum-audit/measure.py dynamic
& logs/p0-venv/Scripts/python.exe logs/p3/fast-sum-audit/measure.py static
& logs/p0-venv/Scripts/python.exe logs/p3/fast-sum-audit/measure.py fixed-order
```

本地探针不随 sdist 发行，不能把发布文档当作包含探针的证明。没有固定 runner、
完整绑定或领域预算证据时，保持未验收。性能前置见 [RG-005](rust-gaps.md#rg-005-fastsum)。
