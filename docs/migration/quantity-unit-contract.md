# Quantity / PhysicalUnit 绑定合同

本合同适用于 `ospf_python.quantities` 的完整迁移，不是仅对
`Quantity[Floating]` 或米/千米的验收声明。Rust 来源固定为
`119854756a0aeb66d2998055f96fa7175c7bfb37`；实现及验证只在 Python 仓库进行，
不使用相邻 Rust/WASM 工作树，不以本地 path/patch 改变来源。

## 范围

- `Quantity[T]` 的构造、转换、四则、相等、hash、字符串、继承、copy/pickle/DTO。
- 开放的、可运行时检查的 `PhysicalUnit` Protocol，包括自定义单位、回调、重入、
  动态属性与外部数值类型；不能封闭成预定义单位枚举。
- 33 个单位家族及全部 223 个预定义实例：Acceleration、Amount、AngularAcceleration、
  AngularVelocity、Area、Bandwidth、CatalyticActivity、Current、ElectricCharge、
  Energy、FlowRate、Force、Frequency、Information、Length、LuminousIntensity、Mass、
  MassDensity、Momentum、PlaneAngle、Power、Pressure、Resistance、SolidAngle、Stress、
  SurfaceDensity、Temperature、TimeUnit、Torque、Velocity、Voltage、Volume、Wavenumber。
- 七指数 `Dimensions`、`FundamentalQuantity`、`DerivedQuantity`、`QuantityDomain`。
- `QuantityValueRange`、min/max、时长转换和四个 `UnitSystem` DTO/常量。
- 与泛型数值、数组/序列化、模型 adapter 和各 framework 领域的集成；单独的
  same-unit Floating 测试不能证明这些能力全部迁移。

测试 `tests/quantities/test_quantity_migration_contracts.py` 固定以下迁移前事实。
其中明确标为 legacy 的精度损失/宽松单位行为是差异基线，**不是新绑定的正确性政策**。
未来改变这些行为须有显式迁移说明及新合同，不得把旧缺陷换个测试期望当作无损兼容。

## 公开 `.to()` Result 源码候选

自然入口现在为 `quantity.to(target_unit, *, context=None, exact=True,
numeric_adapter=None) -> BindingResult[Any]`，默认委托固定 Rust 单位数学与原生
开放回调控制面，不提供生产旧内核 fallback。调用方必须显式消费既有 Result，
不能再把返回对象直接当成 Quantity。示例见
`examples/quantity_conversion_example.py`；新增行为由
`tests/quantities/test_quantity_conversion_binding.py` 独立验证。
**源码默认接通不等于正式 switched**；RG-008、完整自然调用预算、所有数量辅助入口、
领域和平台验收仍是独立退出门槛。

```python
from fractions import Fraction

from ospf_python.quantities import Quantity
from ospf_python.quantities.unit.length import KILOMETER, METER
from ospf_python.utils.functional.result import Failed

result = Quantity(value=Fraction(1, 3), unit=KILOMETER).to(METER)
if not isinstance(result, Failed):
    assert result.unwrap().value == Fraction(1000, 3)
```

`Quantity[T]` 仍是仅有 value/unit 两字段的 frozen dataclass；构造、copy/pickle、
DTO、格式化及原运算符不因此改变。返回 Any 是刻意的诚实边界：开放目标回调和
迟查找的 Quantity 工厂可以输出不同数值域、不透明对象、None 或作为数据的 Result，
不能承诺所有输出都是 `Quantity[T]` 或 float。

### 内置数值域与表示政策

| 输入（精确类型） | 内置单位出口 | 政策 |
| --- | --- | --- |
| builtin int | int 或 Fraction | 任意精度；非整数结果提升 Fraction，不截断 |
| Fraction | Fraction | 精确有理数，不经 float |
| 私有/public Rational | 各自原域 | Rust BigRational 数学，公开 DTO 仍无持久句柄 |
| 有限 Decimal | Decimal | 中间精确有理数；只在实际出口调用 Context.divide |
| 有限 float / Floating | float / Floating | 显式 Float64 域，不宣称任意实数无损 |
| 其他开放 numeric | 显式 NumericAdapter | 无隐式 `__float__` 或全局类型注册 |

Decimal 的 `context=None` 使用实际输出时的 Python 当前上下文。默认 exact=True
拒绝数值损失，exact=False 才允许上下文舍入；flags/traps 及原异常按出口合同保留。
输出采用**规范有理表示**：不重建输入 quantum、尾零或负零；例如 1.2300 的同单位
转换输出为 1.23，-0.000 输出正零。原 Quantity 的 value 不被修改。这是显式表示
政策，不是声称保留旧量化元数据，也不影响两端 opaque 时的原样传递。

Float64 遵循固定 Rust 的 same-unit 短路与 `v * scale + 0` 次序；线性旧公式不加零，
故部分负零结果明确不同。转换经 SI 的两段路径不能合并成 Python 旧线性公式；
33 家族、三种比例、正负零的独立合同固定该政策。Floating 的 builtin int 载荷先
证明可无损表示为 Float64，失败返回 DATA_LOSS；不给 Floating 增加 `__float__`。
内置 bool、无适配器的未知类型不被隐式当成整数或浮点；非有限输入、零比例、
非有限结果及不支持系数由对应原生/适配域返回结构化失败，不回退旧数学。

内置两端按已登记十维量纲校验，米转千克失败。所有 223 常量均在范围内，原子质量
比例仍被 RG-008 防护拒绝，并未完成切换；原八项强制切换门禁继续真实失败。
温度 `.to()` 是 affine **点**换算，Kelvin 的零偏移也保留点身份；温差公开表示、
checked 运算符及小数维度完整适配尚未完成。

四则默认路径的完整替换约束及新增实测边界见
[Quantity arithmetic contract](quantity-arithmetic-contract.md)。它是预实现合同，
不是已切换声明；尤其不能把固定 Rust 的 checked 返回视为有限域/panic 安全证明，
也不能用普通 Temperature 的零 offset 伪装线性温差单位。

真实原生运行时 `Unit` 及原生输出点/差单位的公开消费链路见
[Runtime unit contract](runtime-unit-contract.md)。它接入既有转换/极值/范围/时长，
但不代表自然四则或完整数量切换；原生单位的完整pickle/DTO合同仍待验收。

### 开放单位与显式数值适配器

`PhysicalUnit[Input=Any, Standard=Any, Output=Any]` 仍是 runtime-checkable
开放 Protocol，保留 symbol/to_si/from_si；三个泛型描述回调输入、SI 中间值及输出，
不增加运行时白名单或强制 `_factor` 字段。普通内置类走固定 Rust，子类、被替换的
方法及动态 descriptor 保留外部回调。未知源没有维度证明，不按 symbol 猜测。

公开 `NumericAdapter[V]` 的 `to_fraction(value) -> Result[Fraction, Any, Any]`
与 `from_fraction(value) -> Result[V, Any, Any]` 连接自定义表示和精确数学。显式
策略也优先于 builtin 域，可覆盖 float/Floating/Decimal；用户负责自身表示映射的
正确性，Rust 只负责单位数学，不证明任意用户映射无损。

- 两端内置只在最终边界输出一次，不对内部 SI 调用 from_fraction；内置到 opaque
  在实际回调前导出，opaque 到内置将实际 SI 数据导入。两端 opaque 完全不读取适配器。
- 源内置系数本次快照完成后才导入适配器；对目标方法、字段和工厂的修改迟绑定可见。
  每次读取实际策略方法，无实例系数/数值缓存或跨调用状态。
- 策略必须返回 Result，只有 Ok 解一层；to_fraction 的 Ok 值必须为精确 builtin
  Fraction。raw 返回或错误导入类型为 ILLEGAL_ARGUMENT。Failed/Fatal/Warn/Success
  等失败或未支持结果外包 APPLICATION_ERROR，FailureContext.callback_result 保留
  原实例，不读取或格式化其 error。from_fraction 的 Ok 可保留任意自定义输出。
- 外部属性/回调/策略/工厂的 Exception 由原生控制面转为现有 Result/ExErr，保留
  原实例、traceback、cause/context/handled state；BaseException 原样传播。开放
  单位回调的 Result 仍是数据，与数值适配器的 Result 控制语义明确分开。

### 迁移前测试与真实消费者

六处既有普通 `.to()` 测试仅增加显式 unwrap，原数值断言不变。迁移前协议文件保留
旧全部断言/参数，但其旧 `.to()` 探针现在调用**测试专用冻结参考函数**，不再证明
生产入口仍为旧语义；参考函数使用真实 Quantity 模块的 globals/builtins，保留
迟查找工厂基线。新公开合同独立覆盖全部单位/域、动态协议、错误和表示变化。

当前生产源码没有直接调用 `.to()` 的既有消费者，不能据此声称整个 framework
已迁移。新的 `_Resource[V]` 真实 solver 测试通过自然 `.to(METER)` 处理容量和
因子，只在 solver 边界显式转换 Float64，求解后用原精确物理量复验资源。
Fraction/Decimal/自定义 adapter 及后端实际执行情况由日志记录；未编译的后端
真实 skip，不冒充已通过。极值、范围、时长、四则和所有领域仍按完整计划推进。

## 迁移前公开行为与调用顺序（冻结参考）

`Quantity` 是 frozen 泛型 dataclass，恰有 `value`、`unit` 两个字段；没有隐藏的
浮点值、Rust 缓存或单位 ID 字段。`__match_args__`、字段字典、按字段的相等/hash、
copy、replace 和 pickle 属于门面合同。相等要求 Quantity 的具体类相同，并比较
单位 dataclass 的全部字段，不等同于算术中的 symbol 判断。

### 旧转换基线（非当前生产入口）

迁移前 `to(target)` 按以下次序执行，不做同单位短路：

1. 读取 `self.unit`，取得并捕获其 `to_si` callable。
2. 读取 `self.value`，通过 Python `float` 协议转换。
3. 调用已捕获的源单位 callable，保留其返回对象为 SI 中间值。
4. 此时才取得目标单位的 `from_si` callable 并调用。
5. 此时才读取模块全局 `Quantity` 构造器，以目标回调的原始返回对象和目标单位构造。

即使源、目标是同一对象也要执行回调并创建新的基础 Quantity；不使用
`self.__class__`。转换过程中修改 `self.unit` 不会替换已经捕获的源 callable，
但源回调修改目标方法、目标回调修改全局构造器的效果可见。

迁移前 `to` 不检查 dimension，甚至允许米转千克；Fraction、Decimal、超大整数会
先损失到 float；没有 `__float__` 的 Floating 会失败。目标回调可返回非数值对象，
不能擅自再抽取为 f64 或调用其格式化函数。新绑定必须解决精确域/量纲问题，
而不是复制这些历史缺口或给 Floating 临时加 `__float__`。

### 四则与格式化基线

- 加减先按左、右顺序读取 `unit.symbol` 并执行 `!=`/truth 协议，不比较单位对象，
  不检查比例、偏移或量纲。同名不同因子的单位也会被接受。
- 单位不同则为错误消息再次依次读取两边 symbol，不读取 value；消息为
  `Cannot add/subtract quantities with different units: ... and ...`。
- guard 成功后先捕获模块全局 Quantity，再读取数值并调用相应 Python numeric slot，
  运算之后才重新读取左单位用于输出。乘除同样在数值运算前捕获构造器。
- 算术不隐式调用 float，整数、Fraction、Decimal、Floating 和外部类型按各自协议运算。
  当前同摄氏单位的加减直接算数值且保留摄氏单位，并没有温度点/温差语义。
- 字符串先以空 format spec 格式化 value，然后读取并格式化 `unit.symbol`。
- 迁移前 `.to` 及尚未迁移的工具函数不是 Result API。当前 `.to` 候选遵循 Result/ExErr 政策，
  不能把旧直接抛错的行为说成已满足错误边界，也不能捕获 BaseException 伪装 Failed。

### 单位与辅助入口基线

32 个线性家族的公式恰为 `value * factor` / `value / factor`；Temperature 为
`value * factor + offset` / `(value - offset) / factor`。运算顺序、额外加零与否、
二进制浮点常量和负零均可观察；不能融合运算、将因子解释成意图上的十进制常量，
或用一个通用 affine 公式无说明替换线性公式。

字段注解不是运行时类型白名单。自定义负/零因子及 Fraction/Decimal 因子目前可构造；
零因子反向转换会抛 ZeroDivisionError，inf/nan/overflow 可按 Python 浮点规则传播。
非默认 factor/offset、子类或动态属性不能被误当成缓存中的预定义单位。

min/max 依次取 `unit.to_si(float(value))` 为 key，返回原输入对象，平局保留首次；
空输入由 builtin 报错。范围 contains 先计算 min、max、候选的 SI 值，再链式比较，
当前也没有量纲检查。时长入口及 timedelta 的舍入/范围是单独的集成合同。
`UnitSystem` 是名称/说明/七种基本单位字符串 DTO，不是运行时 Rust UnitSystem 的直接别名。

## 固定 Rust 接口的实测差异

当前极值/范围入口的独立 Result、精确比较及开放 rich-comparison 候选见
[Quantity ordering contract](quantity-ordering-contract.md)。上述 helpers 旧行为只作为
迁移前冻结参考，不代表当前生产入口仍隐式 float 或允许已知跨量纲比较。三个自然时长
入口的独立 Result、精确/Float64 微秒与有符号范围候选见
[Quantity duration contract](quantity-duration-contract.md)；完整预算/发行/领域/平台验收
及 checked 四则仍是独立要求，不据此登记完整 Quantity switched。

隔离探针只依赖相同 Git revision，不修改生产 manifest/lock 或上游源码。
其 BigDecimal 实际锁定为 **0.4.11**，不是 Cargo.toml 中下限字符串 0.4.10；
BigInt/Ratio/num-traits 分别为 0.4.8/0.4.2/0.2.19，与生产 lock 一致。

| Rust 入口 | 已确认的行为 | 绑定约束 |
| --- | --- | --- |
| UnitConversionValue | f64、BigDecimal、BigRational；后两者没有自动遵循 Python Decimal context | 定义逐域 adapter；不一律抽取 f64 |
| UnitConversionCalculation | 线性也计算 `v * scale + 0`；`-0.0` 因而可能成为 `+0.0` | 当前候选显式采用固定 Rust 次序；符号零差异有独立合同 |
| checked 系数转换 | 过大的系数可能 None；极小系数可能成功转换为 0 | 不能把 Option::Some 当作输入、结果或非零校验 |
| checked f64 除法 | 零比例可返回 Some(inf/nan)，结果 overflow 也可 Some(inf) | 按域/公开政策先验证，不能传播虚假成功 |
| checked 精确域除法 | BigRational/BigDecimal 零比例仍会 panic | 必须在绑定边界避免进入此路径，不依赖 panic 捕获替代正常校验 |
| Scale::from_f64 | 有限非零系数可往返；-0 丢失符号；inf/nan 会 panic | 输入分类后才构造 Scale；不是无条件安全工厂 |
| Unit::PartialEq | 比较 dimension/domain/conversion，忽略名称和 symbol | 不能替代 Python dataclass equality 或 symbol guard |
| Quantity::to_unit | 检查维度；相同规则短路 clone，可能不执行标准化 | 不能替代动态 Python 回调/相同单位合同而无说明 |
| checked_add/sub | 两个 affine 点不可相加；两点相减返回 delta 线性单位 | 温度点/差与历史运算必须显式决定，不能静默改变 |
| runtime dimension | 基础幂次为 i64，另含信息/角度等维度 | Python 七指数允许小数/非有限值，不能直接窄化或吞并额外维度 |

BigRational 可精确执行带十进制系数/偏移的大整数转换。精确的只是所编码的系数：
`Scale::from_f64(0.01)` 对应二进制浮点 0.01 的精确分数，**不是** 1/100；
Fahrenheit 的既有浮点 5/9 也不是精确有理数 5/9。
BigDecimal 的 1/3 会形成有限精度结果，乘回 3 不等于 1；不应据类型名宣称所有域无损。

### 预定义单位不能按名字或 symbol 直接取别名

已调用固定 Rust 260 个 `define_unit!` / `define_unit_by!` 类型的运行时入口，读取
实际 scale/offset/symbol/dimension，不只扫描宏字符串。Python 223 常量中，按家族和
规范化名字可找到 135 个候选，88 个无同名候选；这 **不表示 88 个单位在 Rust 中缺失**，
只是需要显式的别名/自定义规则映射。135 候选中有 34 个 symbol、3 个 f64 比例、
1 个 f64 偏移不同；精确有理意义下分别还有 37 个比例和 2 个偏移不同。

| Python 常量 | Python 数据 | 同名 Rust 候选数据 | 要求 |
| --- | --- | --- | --- |
| HORSEPOWER | 745.69987158227 | 735 | 不按名字替换；机械/公制马力需区分 |
| KNOT | 0.514444 | 精确十进制近似 1852/3600 | 精度改变需显式说明 |
| CUBIC_FOOT | 0.028316846592 | f64 0.3048 的立方所形成的比例 | bit 级舍入不同，不以物理名义假装一致 |
| FAHRENHEIT offset | 255.3722222222222 | 255.37222222222222222222 | f64 仍不同；符号 C/F 与 Rust 的度符号也不同 |

可用同 revision 的运行时 Unit/Rule 构造器表达 Python 的已登记常量；
不要求修改上游常量，不增一套 Python 换算内核。新增“理想精确”单位应与历史常量分开登记。

## 原生适配要求与尚需实现的决策

1. 内置单位从**本次实际字段**构造已校验描述，维度按明确家族登记；不以 symbol 猜维度，
   不长期缓存第二份可变数值/单位状态。DTO 保留不等于核心计算继续留在 Python。
2. 数值域至少覆盖任意精度整数、有理数、有限 Decimal、Float64/Floating 和开放的
   Python numeric Protocol。整数转换产生非整数时的返回域、Decimal 的 context/舍入、
   NaN/Infinity/负零及不支持域的 Result 要逐一确定；不能用 float 注解掩盖类型变化。
3. 对原生内置单位用固定 Rust 的量纲/换算核心。开放自定义单位仍通过其 callable 集成，
   不读取不存在的 `_factor` 或强制转换其不透明返回值；无维度信息不能宣称已验证维度。
   为自定义单位增加显式元数据的工厂/adapter 不得排除现有 Protocol 扩展点。
4. 转换及范围/极值等可失败入口按新 Result 合同原子切换，保留外部异常实例、
   traceback、context/handled state；BaseException 原样传播。运算符的历史类型/异常
   协议与新增 checked 入口分别验收，不擅自扩大错误规则豁免。
5. 自然 `.to()` 的 Result 返回、整数提升、Decimal context/规范表示、内置跨量纲拒绝
   与 opaque 边界已按本文源码候选定义。affine 温差公开表示、小数维度的无损原生表示、
   helpers/算术及全部预算/领域/平台仍待完成；不据局部源码接通将 Quantity 登记为
   switched/verified，也不删除尚未被接管的其他旧内核。
6. 原子切换须带完整新域合同、类型提示、文档/示例、实际消费者、性能/资源及干净发行物验证。
   Windows 的本地探针不能代替 Linux、solver11/12、全部领域或长期资源验收；
   先前整数/Floating 性能缺口不因此取消。

本文件是语义合同与设计约束；执行记录、完整盘点、差分结果与源 hash 由被忽略的
logs 进度入口维护，不将机器生成清单复制进发布源码。

## 私有原生底座合同（不是公共切换）

`ospf_python._binding.quantities.Unit` 只持有一个 `_native._QuantityUnit`；
后者只有固定 Rust 的运行时 Unit。公开 `.to()` 候选经联合派发使用此底座，
既有 Quantity/单位 dataclass 仍无持久原生字段，不增加旧内核 backend 开关。

- 创建时显式给出十维整数指数，依次为 mass/length/time/current/temperature/amount/
  luminous_intensity/information/plane_angle/solid_angle。不接受 bool、截断小数指数
  或按 symbol 推断。Python 七指数小数维度的完整桥接仍是独立待实现合同。
- 比例及可选偏移支持内置 int、finite float、finite Decimal；float 按
  Decimal.from_float 的同一精确二进制值编码，但不先构造 Python Decimal。
  int/float 在原生输入边界接入，Decimal 保留显式存储位数快照。内部元数据为任意精度整数 coefficient 和
  BigDecimal scale，值为 `coefficient * 10**(-scale)`，不经过有限位数字符串或
  Decimal context 算术。offset=None 是线性，显式 offset=0 仍表示 affine 点。
- 零比例构造失败，负比例允许；超出固定指数表示范围返回 NOT_SUPPORTED。
  Scale 实际值必须与输入严格相等，否则 DATA_LOSS；这暴露 RG-008 而不是降低精度。
  单位系数的有符号零、非十进制有理系数及开放回调尚不由此严格元数据入口表达，
  不能将其限制转写为整个公开 PhysicalUnit 的限制。
- `convert_exact` 对 int/Fraction/finite Decimal/私有 Rational 接入既有精确适配，
  调用 `Quantity<BigRational, Unit>::to_unit`，返回 Rational。整数除不尽不截断，
  Decimal 不按当前 context 暗中舍入；公开 `.to()` 候选的出口政策见前文。
- `convert_float64` 是显式近似域，仅接收内置 finite float。拒绝非有限系数、
  系数下溢为零和非有限输出；普通结果舍入/下溢遵循 Float64。遵循固定 Rust 的
  same-unit 短路和额外加零顺序，不宣称已保持公开单位的全部负零历史行为。
- `binary_exact` 调用固定 Rust checked_add/sub，输出值及实际点/差单位；不同
  量纲失败，两个 affine 点相加失败，差减点失败。精确 mixed-affine 运算先构造
  与点比例相同的临时线性单位，经固定 Rust 的 `to_unit` 精确换算差值，再交给
  checked 运算；不复制数学内核。Float64 路径不改变求值次序。上游原始 mixed-affine
  缺陷和 RG-008 的高精度 Scale 缺口仍存在，不能据此宣称完整 affine 支持。
- 所有业务失败经现有三参 Result/ExErr。严格入口不调用任意外部对象的
  __float__/__index__/格式化方法；开放协议与原异常保真仍须在公共编排边界实现。
- 版本 1 的 `ospf.unit` JSON 只编码元数据，整数系数用规范十进制字符串，
  不受 Python 4300 位字符串整数限制；未知字段、错误版本、零比例和非整数指数
  拒绝。snapshot/descriptor 是新副本，不创建第二份常驻权威数据。

该底座有真实 Rust 计算、精确域与线程/序列化测试，但 RG-008 的原子质量单位等
完整切换门禁仍应为红灯。不得据此登记 Quantity switched/verified、删除旧内核，
或跳过公共扩展点、性能、发行与领域验收。

### Decimal 输出适配

私有 `Unit.convert_decimal(*, value, target, context=None, exact=True)` 先执行原有
`convert_exact`，取得固定 Rust `Quantity<BigRational, Unit>::to_unit` 的结果，
成功后才交给 `Rational.to_decimal` 作最终 Decimal 输出。context 不参与中间换算，
不将源/目标 scale 或中间 SI 值先舍入；原生换算失败不执行输出 context，保持原失败。
输出边界的舍入许可、flags/traps、精确比较与异常保真见 `numeric-contract.md`。

此私有方法提供独立的显式 Decimal 出口；公开联合派发复用相同 Rational 出口政策。
公开候选采用规范 Decimal 表示而不保留 quantum；本方法本身不证明开放回调、
小数维度、完整温度点/差、非有限域或 RG-008 已完成。原有八项原子质量切换门禁
继续保留且不得改成预期失败。

## 开放单位回调通道（原生控制面候选）

私有 `ospf_python._binding.quantity_conversion.convert_callback(owner=..., target=...)`
委托 `_native._convert_quantity_callback` 编排开放 PhysicalUnit 回调。这是完整转换的
扩展通道，不是内置单位的旧 Python 算术 fallback；公开 `.to()` 经下述联合派发接入，不能据此
登记 Quantity switched，或把既有 223 单位和 RG-008 从最终验收范围移除。

候选的顺序为：读取 owner.unit、捕获其 to_si、读取 owner.value、调用捕获的源方法、
此时才读取 target.from_si 并调用、最后才读取 Quantity 模块的当前 Quantity 工厂，
以 value/unit 关键字构造。工厂名称遵循 globals 优先、builtins 后备的查找规则。
源方法捕获后更换 owner.unit 不替换它；源回调对目标方法的修改、目标回调对工厂的
修改仍可见。即使同一单位，也执行两个开放回调并构造新结果，不借 Rust Unit 的
same-unit 短路跳过扩展点。默认工厂仍是基础 Quantity，不使用 owner 的具体子类。

与迁移前基线的**明确差异**：此通道不执行隐式 `float(owner.value)`，也不调用
任意值的 __float__/__index__/格式化协议。源回调接收原输入对象，SI 中间值和目标
输出同样保持不透明。这样外部策略可以处理 Fraction、Decimal、Floating、Rust
Rational 或自定义数值，而不是由绑定先丢失精度。这个选择不是宣称迁移前 `.to()`
本来就无损；旧的 float 行为仍由冻结协议基线记录，最终公开签名与消费者升级须
单独验收。标准内置单位要用固定 Rust 的明确数值域派发，不能用该开放通道绕回
它们的旧 to_si/from_si 算术。

- 本通道不读取 symbol、猜测维度、要求 _factor/_offset 字段或关闭自定义 Protocol。
  没有显式维度元数据的开放回调不等于已完成量纲验证；混合派发已由下述入口接通，
  开放显式元数据协议、小数维度及完整温度点/差要求继续待实现。
- 回调返回的 None、不透明对象或既有 Result 均按数据传至下一个阶段/工厂，
  不自动 unwrap、float 化或把数据中的 Failed 当成外层转换失败。工厂自身可返回
  不透明值/None/Result，外层既有 Ok 保留该输出，不建立平行结果类型。
- 任一属性读取、调用或工厂查找的 Exception 为外层 Failed/ExErr，码统一为
  APPLICATION_ERROR，源为 ospf-python-native，error_class 为 QUANTITY_CALLBACK。
  消息含 source-unit/source-method/source-value/source-call/target-method/target-call/
  factory-lookup/factory-call 阶段，不根据错误消息推断分类。原异常实例、traceback、
  cause/context/handled state 保留，不调用异常 str/repr/__class__；BaseException
  原样传播，不能把中断伪装为 Failed。
- Rust 只在调用栈持有引用，不增加 owner/value/unit 的跨调用镜像或缓存，不持有
  存储锁执行用户代码。callable 在其临时参数之前释放；SI/目标局部值依原顺序清理。
  异常由普通 Python tuple 传输，引用边可被 GC 看见，不引入有隐藏引用的新 pyclass。
  Result 为保真而保留 traceback 所产生的正常引用生命周期不视为泄漏。

`tests/native/test_quantity_callback_conversion.py` 检查每阶段失败/中断、动态捕获、
不透明数值/Result、工厂替换/后备、通用 Python 参考编排的析构顺序、同源重入及
跨线程回调；另以真正的固定 Rust Unit/BigRational 策略做完整两阶段精确换算。
它不把开放回调算术说成 Rust 内核，也不替代全部公开能力、发行、性能/资源和
领域/平台验收。阶段证据仍只记录于 logs 的唯一进度文档。

### 单位系数传输与成本边界

`Unit.create` 的 int/float 系数通过 `_create_quantity_unit_encoded` 进入原生边界，
避免反复创建 Python Decimal、数字 tuple 和嵌套编码闭包。float 用锁定 BigDecimal
的二进制接入表达同一精确值；次正规数单独去掉依赖保留的可约十进制尾零，以维持
原 `Decimal.from_float` 的 coefficient/scale 及 JSON 快照，而非仅保持近似数值。
普通整数 float 不因规范化而改变旧的 scale=0 表示。Decimal 仍按实际 as_tuple
编码，保留系数元数据的 quantum；这与公开转换结果采用规范有理表示是不同边界。

原低层 tuple 系数入口保留兼容传输，两个编码入口共用唯一的固定 Rust Unit 构造与
Scale 精度校验，不构成旧单位数学 fallback。非有限/未知数值、bool、子类及不合法
元数据仍按显式域政策拒绝；原生 codec 不调用任意 `__float__`、`__index__`、
`__class__` 或格式化协议。Python 参数边界错误的来源/原码政策保持；没有实例系数、
转换结果缓存或额外的常驻单位状态，只有拥有所有权的本次 Rust 元数据可离开 GIL。

`tests/native/test_quantity_coefficient_transport.py` 逐项比较全部223常量、正负
normal/subnormal Float64、固定种子的二进制位样本、任意精度整数与 Decimal 元数据，
同时保留原八个强制失败切换门禁。完整 `.to().unwrap().value` 的构造、出口和释放
仍计入性能预算，私有 Unit.create 或编码成本下降不能证明整体预算已通过。

## 内置与开放单位联合派发（公开候选的内部入口）

`ospf_python._binding.unit_conversion.convert_quantity(owner=..., target=...,
context=None, exact=True, numeric_adapter=None)` 将固定 Rust Unit 数学与上述开放
回调控制面联合。公开 `Quantity.to()` 已默认调用此入口，但完整正式验收尚未完成。

33 个普通单位家族在 dataclass 定义完成时登记原类、十维指数、原转换函数及
代码身份，不按 symbol 推断、不在第一次转换时快照已被替换的方法，不新增
实例字段或缓存系数。只有登记的精确类型、捕获的原绑定方法及普通字段路径
进入 Rust；子类、函数/code/defaults 替换、动态属性或字段 descriptor 保留
开放协议。已捕获的原方法不因后来替换类槽而被替换；执行前重新检查动态化，
此时才读取实际 factor/offset，故 value getter 的修改仍可见。symbol 不参与
转换也不被额外读取。温度家族包括零偏移 Kelvin 均作为 affine 点登记。

- 两端内置：用固定 Rust 转至带明确量纲的内部 SI，再向目标转换；两端已知
  维度不匹配由 Rust 拒绝。内部 SI 不导出 Decimal、不按 context 提前舍入。
  这里只实现整数十维及已登记温度点换算，不宣称小数维度/温差公开 API 完成。
- 内置到开放：迟取目标方法后，在实际回调边界导出 SI 值，再交给开放回调。
  开放到内置：把开放结果作为目标家族的 SI 数值导入，不声称已证明未知源的
  维度。两端开放仍不读取数值域、不自动 unwrap Result 或执行 float。
- 内部 SI 标记必须是本次派发真正产生的对象；外部回调返回相同私有类型的
  对象仍是外部数据，不能冒充当前调用的原生维度/数值快照。
- 内置精确输入为 builtin int、Fraction、有限 Decimal、私有及精确类型的
  public Rational；分数换算不经 float。出口 int 的非整数结果提升 Fraction，
  其余精确域保持域。Decimal 仅最终输出使用所选 context，exact 默认拒绝损失；
  quantum、尾零及负零按前文规范有理表示政策不重建，非保留原量化元数据。
- builtin float 及精确类型的 public Floating 显式进入有限 Float64 通道。
  Floating 的 builtin int 载荷通过 Rust Rational 到 Float64 的无损证明后才
  接入；不能无损表示时 DATA_LOSS，不调用任意对象的 __float__。其他内置
  数值域、bool 及非有限域按前文显式拒绝政策返回输入/不支持失败；自定义 numeric
  由显式 NumericAdapter 接入，不静默使用旧 Python 数学。
- 内置单位的 factor/offset 遵循 Unit.create 的 int/float/Decimal 精确元数据
  合同；不把 Fraction 系数隐式转 float。RG-008 防护继续返回 DATA_LOSS，
  所有 223 常量仍在验收范围，原八条原子质量切换门禁不因新增防护测试变绿。

原生控制面共用同一执行引擎，prepare 阶段不读取系数；检查式内部调用的失败
短路目标/工厂，原 BindingResult 实例保留。开放回调的 Result 仍按数据传递。
成功工厂输出 None 与内部失败分开传输，工厂仍遵循 globals/builtins 的迟查找。
属性/回调/prepare 的 Exception 映射为 APPLICATION_ERROR/QUANTITY_DISPATCH，
含阶段名并保留原异常与 traceback；BaseException 原样传播。Decimal 自身的
类型化出口失败保留原来源，不被重包装为通用回调失败。

单位/数值及外部 SI 快照只在本次调用栈保活，外部 SI 保持至工厂完成；无跨调用
句柄镜像、实例系数缓存或共享派发状态。此候选不代替完整公开性能/资源预算、
真实领域消费者、全部后端/平台与发行验收。新合同见
`tests/native/test_quantity_unit_dispatch.py`，旧开放回调合同继续适用。
