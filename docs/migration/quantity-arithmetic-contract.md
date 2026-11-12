# Quantity Arithmetic Contract / 物理量四则替换合同

本文件记录完整四则替换的**源码候选合同与实测约束**，不是当前已发布 API 或通过
切换验收的声明。自然方法及默认运算符已接入同一候选，尚须完成发行、完整消费链路、
生命周期与性能验收。固定 Rust revision 为 `119854756a0aeb66d2998055f96fa7175c7bfb37`；
不使用相邻 Rust/WASM 工作树、path/patch、Python 内置单位数学或可选择的旧内核。

This is a source-candidate contract, not a public arithmetic cutover. Source,
runtime, distribution, performance, domain and platform acceptance remain separate.

## Scope / 完整范围

- 替换自然 Quantity 的加、减、标量乘、标量除默认权威路径。源码候选提供 `add`、
  `subtract`、`multiply`、`divide`，接收 context/exact/numeric_adapter 的
  keyword-only 政策；四个运算符须委托同一实现并返回现有三参 Result。旧直接
  返回 Quantity/抛错合同需明确升级，不能只新增无人消费的私有函数。
- 保留 value/unit 两字段 frozen 泛型 DTO、构造、copy/pickle、按字段相等/hash、
  格式化与继承，不统一 float、不新增 owner/value/unit 镜像。
- 全部33家族、223常量、任意精度整数、Fraction、Decimal、公开/私有 Rational、
  有限 float/Floating、混合域、子类、NumericAdapter 和开放 numeric 均在范围内。
- 加减处理同量纲不同单位；标量乘除不隐式扩大为 quantity-by-quantity 单位代数。
  后者及小数维度仍按完整迁移计划单独验收。

Named operations do not replace migrating the default operators. Existing Result,
generic domains, open extensions and the two-field DTO remain mandatory.

## Observed Legacy Behavior / 当前运行时基线

真实入口14域×14域×4运算共784调用，逐项对照相同操作数的 Python numeric slot：
389成功、395异常。14域为 int、Fraction、Decimal、公开/私有 Rational、float、
Floating、bool、str、开放 numeric、NumPy float64/int64、int/Fraction 子类。
另有56边界和每个预定义单位的四次 Fraction 运算（892次），不以少数单位代替清单。

| 当前入口 | 实测行为 | 替换约束 |
| --- | --- | --- |
| 加减 guard | 仅比较 symbol，同名异比例甚至异量纲直接算数值 | 内置单位用实际 Rust 量纲/比例 |
| 同维度不同 symbol | 米与千米抛 TypeError，不转换 | 采用明确 checked 换算合同并升级调用方 |
| int 真除法 | 1/3及超大整数除法返回近似 float | 精确通道非整数结果提升有理域 |
| public Rational 零除 | 当前数值类可返回0/1，数量外层照收 | 数量精确除法先受检，不把0当有效商 |
| NumPy float64 零除 | infinity并发布 RuntimeWarning | 显式外部数值政策，不冒充有限 Float64 |
| Decimal 算术 | 运算时受当前 context 舍入并设置 flags | 精确中间运算不经 Python Decimal，仅最终出口舍入 |
| 温度点 | 点可相加、缩放；相减仍为点单位 | 点/差语义及可继续公开消费的温差单位 |
| 返回/失败 | 直接 Quantity/开放工厂输出，异常传播 | 既有 Result，保留原异常，BaseException仍传播 |

这些旧缺陷不是正确性政策；混合域的旧异常也不能自动成为新数值能力的白名单。
必须审查返回类型，不能只比较成功数量。

另32个真实协议探针核实：数值 slot 前捕获 Quantity 工厂、slot 后读取输出单位、
惰性 builtins fallback、Result-as-data、不透明输出、NotImplemented/反射、子类
反射优先级、原 Exception/BaseException 身份及无持久 owner 缓存。

Thirty-two protocol probes record observable control behavior. Their old exceptions
are migration-before evidence, not proof that existing operators satisfy Result.

## Pinned Rust Safety / 固定 Rust 安全边界

独立 crate 仅依赖固定远程 revision，继承既有 lock，仅更改隔离 root package 名。
17项探针分别在debug/release运行并经strict Clippy；不是生产绑定106测试的重跑。

| 固定 Rust 实测 | 绑定必须执行的防护/适配 |
| --- | --- |
| checked_add/sub 检查量纲并将右值转至左单位 | 调用真实 checked 方法，不装饰未消费的原生调用 |
| 同名异比例仍按实际比例换算 | 输出单位来自实际原生运算，不由 symbol 推断 |
| 两 affine 点不可加；两点相减生成线性 delta | 输出温差成为可继续公开消费的真实单位 |
| 差+点/点+差为点；点-差为点；差-点失败 | 测试双向次序，不能一律返回左单位 |
| Rust Kelvin 为linear，Python Temperature含零offset仍为affine点 | 继续按Python点合同构造，不直接取Kelvin别名 |
| mixed-affine比例1/3先在BigDecimal舍入 | 精确域先用固定 Rust 的 `to_unit` 将差换到点的线性比例，再调用 checked 运算；Float64 次序不变 |
| checked f64可接受NaN或成功返回infinity | 独立验证输入/结果，Ok不是有限域证明 |
| 非零比例1e-400转f64为0，运算仍返回有限0 | 验证系数非零保持，仅检查结果finite不够 |
| f64标量零除为infinity/NaN | 运算前检查零，之后检查有限性 |
| BigRational零除、affine点标量乘除panic | 调用前拒绝，不以catch_unwind作生产合同 |
| BigRational标量1/3精确，BigDecimal不保证除后乘回相等 | Decimal经既有精确Rational中间通道 |
| 同规则f64加减有可观察的signed-zero次序 | 保留固定Rust分支，不统一替换为SI两段公式 |

catch_unwind仅用于隔离探针观测已知panic，不加入生产作为正常失败处理。探针自身
首轮编译/Clippy问题及修复日志保留，不宣称上游出错或生产原生测试曾失败。

## Numeric And Extension Policy / 数值与扩展政策

实现必须给出可执行的对称/非对称混合域矩阵，不能由 Rust 泛型 V 的同型限制
悄悄裁掉 Python 能力；下面是必须落实的约束，不是已有实现的承诺。

1. 精确值及两种 Rational 表示统一导入既有 Rust Rational 数学；整数除不尽提升
   Fraction，其他混合域的输出/提升次序明示。Decimal只最终遵循context/exact，
   延续已声明的规范有理表示，不承诺原quantum、尾零或负零。
2. float/Floating是有限Float64通道。混合精确值进入时须有无损证明或显式近似政策，
   不暗调任意__float__。Floating整数载荷、极大整数、次正规数、signed-zero、
   NaN/infinity均须测试；舍入政策不能伪装成精确转换。
3. NumericAdapter按实际操作数导入，按结果政策导出；adapter返回Result是控制，
   开放numeric slot返回Result仍是数据，两者不能混淆。
4. 开放numeric的反射/子类优先级、opaque输出、重入/跨线程仍按Python协议。
   外部扩展不是builtin Rust数学失败后的fallback；需要换算却缺少可证明的数值
   域时明确失败或使用显式策略，不重启旧单位公式。
5. 开放单位没有原生量纲/affine证明；不能靠名称、symbol、鸭子字段或被替换方法
   冒充内置来源。元数据/value/callback/factory顺序及快照逐阶段定义，防止数值
   回调修改单位后输出与实际计算不符的单位，或提前触发动态descriptor。

The promotion matrix and native output-unit facade are integrated source
prerequisites, not full cutover acceptance. They must remain usable through
conversion, extrema, ranges and durations; a private tuple alone is insufficient.

## Implemented Candidate Policy / 已实现候选政策

七个内置数值域的双向混合矩阵采用以下提升优先级，左右对称：

`int < Fraction < public Rational < private Rational < Decimal < float < Floating`

- 两个整数的真除法不整除时提升为Fraction；其他精确域保留矩阵选定的表示。
  Decimal只在最终出口受context/exact约束，不能用中间Python Decimal算术代替。
- 混合结果进入float/Floating时，精确操作数必须通过原生无损Float64出口；
  exact=False显式放宽该导入及Decimal出口的近似政策，不能放宽有限性、系数下溢、
  零除或点差防护。Floating自身的整数载荷沿用既有无损导入合同。
- NumericAdapter显式替代双方内置导入/输出政策；实际左、右操作数依次各导入一次，
  最终结果仅重建一次，不在中间单位换算出口反复调用策略。失败Result及原异常保真。
- bool、NumPy标量、内置类型子类和其他开放数值不被偷偷封闭为七内置域。已证明相同
  线性单位时，Rust控制面调用实际Python数值slot（含反射/子类优先级）；不透明输出
  和slot返回Result均为数据。需要跨比例换算或已知affine运算却没有数值域证明时，
  必须显式使用NumericAdapter，返回NOT_SUPPORTED而不重启旧公式。
- 元数据未知的开放单位只允许同一个单位对象参与加减，不依赖symbol相等或猜量纲，
  不预读开放symbol/to_si属性。默认由其开放数值协议定义计算；显式NumericAdapter
  可通过既有Rust Rational运算相同单位的数值，但不获得假的维度/点证明。

原生控制先捕获当前Quantity工厂，再采集左、右单位的来源及真实句柄/系数，之后
读取左、右value并执行数值策略；不会让adapter或value回调改写已经参与运算的单位。
原生输出以固定Rust实际生成的单位为准，点减点输出真实delta，差+点可输出右点。
只有原单位的当前来源、完整native metadata及显示属性身份仍与实际输出相符，才
复用该原单位对象以保持普通DTO字段身份；否则保留实际native输出快照。开放单位
路径保留数值slot后的owner.unit迟读取。工厂替换不影响已经捕获的工厂。

本候选仍不承诺未知单位之间的自动换算、quantity-by-quantity单位代数或小数维度。
native输出Unit的copy/pickle/deepcopy及数量显式DTO现有独立候选及隔离安装合同，
详见数量快照合同，不再将其误列为完全未实现。整体迁移的既有验收要求没有取消。

四则实际输出现另有永久矩阵：add/subtract/multiply/divide × 七个内置数值域 ×
copy/deepcopy/pickle protocol 0至5，共224项。每项验证结果域、unit descriptor、
显式JSON DTO及换算回原单位，并由默认和debug解释器复跑。该证据关闭
`complete-native-output-dto-pickle-copy`，不关闭完整调用预算、RG-008/223单位、
真实消费者、跨平台或整体切换。

The seven builtin domains use the symmetric precedence above. Exact-to-Float64
mixes require lossless import unless explicitly approximate; arbitrary Python
numeric protocols are not implicit coercions. Native metadata is captured before
value/adapter callbacks, while opaque-unit labels retain late lookup. Reusing an
original unit requires fresh provenance/metadata equality with the actual output.

## Provenance Cost / 来源证明成本

每次捕获实际单位时只做一次静态家族/字段描述符检查，同时验证两方向方法的原始
类槽、实际实例绑定、函数code/defaults/kwdefaults身份。不能先构造伪绑定方法，
再反复执行同一全套检查；真正的实例方法仍必须被验证，不能只信任类登记。
输出复用原标签之前重新执行完整证明和实际native metadata比较，不能缓存实例
来源、系数、descriptor或此前结果，也不能把数值回调后的变化忽略。

Class-field descriptor detection reads type metadata without executing a field's
metaclass hooks. Replaced descriptors and dynamic attributes remain open protocols;
mutations during numeric callbacks cannot relabel the captured native output.
One shared static proof replaces redundant checks, not pinned unit construction,
unit math, Result consumption, output factories or late failure propagation.

永久回归覆盖33家族、线性/affine/runtime的类/实例方法替换、code/defaults/
kwdefaults、descriptor与动态访问、回调中变更、重复调用无缓存及原异常身份。
CPU profile仅定位重复证明；正式预算仍按全部96完整自然调用配置、相同冻结旧
参考及两轮排序计时，既有数值/数组与领域端到端预算不能由该局部优化替代。

## Acceptance And Deletion / 验收与删除

- 自然方法/运算符、所有域和单位、错误/反射/副作用/释放/重入的永久合同。保留原
  断言；升级语义使用明确测试专用旧参考，不伪称生产语义不变。
- 原生温差单位继续参与.to、四则、极值、范围及to_timedelta的量纲拒绝；零offset、
  工厂替换或重建不能混淆点与差。
- 真实SCIP/Gurobi消费者用公开四则装配领域容量/系数，仅solver边界显式Float64，
  解后用原域复验，不仅私有模型smoke。
- 两配置原生检查、debug/完整Python身份审计、当前wheel/同sdist仓库外locked
  安装、来源/动态库审计；未执行的平台/后端明确待验收。
- 至少两轮完整自然调用计时，包括Result消费、单位准备、数值导入/出口、工厂及
  释放；不以缓存、私有微基准、不同域或减去边界成本代替。
- RG-008八真实失败、223常量完整切换、既有数值/数组预算、完整领域、Linux/
  Gurobi11/12、P3-P9及最终旧内核删除始终保留。

没有上述实证不登记verified/switched、不删除待替换能力。候选源码或本合同不等于
完整四则验收，主计划继续记录完整目标及下一实际执行步骤。

后续已接入原生输出单位copy/pickle及自然Quantity显式DTO源码候选，详见
[数量快照合同](quantity-snapshot-contract.md)。这只补齐序列化实现，不取消本合同
的完整性能、RG-008、223单位切换、领域/平台及最终旧内核删除门槛。
