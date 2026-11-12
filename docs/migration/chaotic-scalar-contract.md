# 标量混沌映射迁移合同

固定 Rust revision：`119854756a0aeb66d2998055f96fa7175c7bfb37`。
本合同只覆盖下表 13 个既有 Python 类；混沌模块的二维/高维映射、吸引子与其他
系统仍在迁移范围内，不能由本调查推断已覆盖。当前这 13 个公共类仍使用原
Python 实现，没有任何类完成切换。另有一个未接入公共入口的受限 Logistic 原生
候选，不能将它当作公共类的绑定或完整数值域实现。

## 现有计算与候选

同名并不等于相同数学模型。以下表格中的 Rust 候选仅表示可继续调查，均不表示
完整数值域、Python 协议或跨平台兼容已经验收。

| Python 类 | 当前表达式及默认参数 | 固定 Rust 观察 |
| --- | --- | --- |
| `LogisticMap` | `r*x*(1-x)`，`r=3.9` | 同名 `LogisticMap::new(r)` 已有未接入公共入口的受限浮点候选 |
| `DyadicTransformation` | `(2*x)%1` | 同名实现以 `2*x-floor(2*x)` 计算，NaN 位模式需决策 |
| `TentMap` | `mu*min(x,1-x)`，`mu=2.0` | 同名实现默认 `mu=1.5`，必须显式传 Python 参数 |
| `GaussIteratedMap` | `exp(-alpha*x*x)+beta`，`alpha=6.2, beta=-0.5` | 显式参数的同名实现是候选；默认参数及溢出行为不同 |
| `SineMap` | `a*sin(pi*x)`，`a=1.0` | 显式参数的同名实现是候选，非有限值错误行为不同 |
| `SinusoidalMap` | `a*x*x*sin(pi*x)`，`a=2.3` | 显式参数的同名实现是候选，非有限值错误行为不同 |
| `ArnoldTongue` | `x+omega-k/(2*pi)*sin(2*pi*x)`，`omega=0, k=0.5` | 显式参数的同名实现是候选；Rust 默认参数不同 |
| `CircleMap` | 同 `ArnoldTongue`，`omega=0.5, k=1.0`，当前代码不取模 | Rust 同名类取模；显式参数的 Rust `ArnoldTongue` 是候选 |
| `SinusMap` | `sin(pi*x)` | Rust 同名类是幂形式；`SineMap::new(1.0)` 是候选 |
| `ChebyshevMap` | `cos(n*acos(x))`，`n=2` | 有界数值可调查同名实现；Python 越界抛错、NaN 保留，Rust 分支均返回 0 |
| `GaussMap` | `1/x-floor(1/x)` | Rust 同名类为 `mu/x` 且零值返回 0；不能直接替换 |
| `ExponentialMap` | `x*exp(r*(1-x))`，`r=2.7` | Rust 同名类为 `exp(x)+c`；不能直接替换 |
| `SingerMap` | `mu*(a1*x-a2*x*x-a3*x*x*x)`，`mu=1.07, a1=1.5, a2=0.5, a3=0` | Rust 同名类使用固定四次多项式，不支持这组系数；不能直接替换 |

例如 `GaussMap()(0.4)` 当前返回 `0.5`，Rust 同名类传 `mu=1` 时返回 `2.5`；
`ExponentialMap()(0)` 当前返回 `0`，Rust 同名类传 `c=2.7` 时返回 `3.7`。
这些名称相同但公式不同的模型不自动判定为上游错误。需寻找实际等价的公共
上游能力或单独跟踪缺口，不能把局部公式复制到绑定伪装成上游实现。

## 数值与调用边界

- 目前 `__call__` 返回原始值；`math` 函数、除法及调用方数值协议的异常按当前
  Python 行为传播。目标业务边界必须遵循项目 Result 规则，切换时需明确错误
  分类及升级影响，不能把异常静默变成 NaN/0。迁移前保留真实旧行为作为基线。
- `SineMap`、`SinusMap`、`SinusoidalMap` 和 `ArnoldTongue` 的无穷输入以及
  使 `pi*x` 溢出为无穷的大有限输入会触发 `ValueError`；
  `GaussIteratedMap(alpha=-1, beta=0)(1000)` 会触发 `OverflowError`。
  固定 Rust 浮点计算对应返回 NaN 或无穷。`GaussMap` 的零输入会触发
  `ZeroDivisionError`。`ChebyshevMap` 在域外抛 `ValueError`，NaN 输入返回 NaN。
- 类型注解为 `float` 不等于运行时只接收内置 float。`LogisticMap` 例如可执行
  NumPy 数组运算和用户定义的乘/反向减协议，表达式顺序可观察；实例参数也能
  是开放数值对象。不能在不做明确兼容设计的情况下先对任意值调用 `float()`，
  也不能静默使用旧 Python 公式作为失败 fallback。
- 13 个类保持现有 dataclass 构造、字段、默认值及冻结语义，公共导入和子类
  行为属于迁移范围。标量终值式 `iterate` 在 `n<=0` 时原样返回输入对象；
  `ArnoldTongue`、`ChebyshevMap`、`CircleMap` 的列表式 `iterate` 返回包含原
  输入对象的单元素列表。正步数逐次调用 `self(...)`，子类覆盖必须生效。
- Rust generator 的首项是初始状态，不是第一步输出；不得直接将它当作 Python
  终值式迭代的第一步。长时间迭代的信号、回调、资源与浮点累计误差须独立验证。
- 比较应区分有限值、signed zero、无穷、NaN 分类和可观察的 NaN 位模式；先明确
  按平台的兼容政策，不能把数学近似、单次样本相等或不同平台 libm 当成逐位保证。

## Logistic 受限原生候选

私有 `_native._logistic_float64_step(rate=..., value=...)` 对两个**真实内置**
`float` 调用固定上游 `LogisticMap::new(rate).step(value)`。它不检查 `[0, 1]`
或参数范围；NaN、无穷和 signed zero 沿用固定 Rust 的 `f64` 语义。成功以
`(float, None)` 传输，非内置 float 以 `(None, Failure)` 返回
`ILLEGAL_ARGUMENT`；包括 `int`、`bool`、NumPy 数值和 float 子类均不转换、
不调用其数值协议。Python 对象分配失败仍按 Python 内存异常传播。这个私有传输
不是公共 `BindingResult`，也不是已确定的公开错误政策。

公共 `LogisticMap` 目前始终执行原 Python 公式，不自动派发到这个候选；候选不
复制开放数值公式，也不在拒绝输入后回退旧内核。此前评估过按输入分支并在原生
层重演 Python 乘减槽的方案，但该分支仍构成独立算法，未采用。固定上游的标量
映射要求 `S: Field + Float`，其数值运算是同类型、无 `Result` 返回的 Rust
操作；不能直接把具有异构返回值、回调异常和生命周期副作用的任意 Python 数值
协议当作上游浮点值。需要分别确定数值适配、Result 和兼容政策，不能把失败路径
包装成已迁移，也不能修改固定 pin 来掩盖缺口。

Windows CPython 3.13 的当前候选测试包括 10000 组随机浮点位模式、36 组各
100 步轨迹，以及错误域的真实类型检查；多步比较对 NaN 仅比较分类。公共原实现
另覆盖 NumPy、开放协议操作顺序、异常身份、临时对象释放和子类迭代。它们是
当前机器上的专项证据，不表示跨平台、完整性能、发行验收或公共切换已完成。

## 已有证据与限制

固定 revision 的独立 release Rust 探针对 15 个候选分别比较 17 个输入；生产和
探针锁文件中七个关键依赖的版本、来源与 checksum 一致，`ospf-rust-math` 为
default feature。`SinusMap` 对比 Rust `SineMap::new(1.0)` 时，14 个有限样本
逐位相等、NaN 双方均为 NaN、两个无穷输入为 Python `ValueError`；这不是全域
证明。独立探针也确认了 Gauss 零、Chebyshev NaN、正弦最大有限值与负 alpha
Gauss 迭代溢出的 Rust 行为。

Windows CPython 3.13 与本机 release Rust 的确定性单步对照进一步覆盖：

- Logistic：110121 组参数/状态，109994 个非 NaN 结果及 127 个 NaN 结果均
  逐位相等；包括 100000 组任意浮点位模式、10000 组有界数和 121 组边界交叉。
- Tent：100196 组中 100063 个非 NaN 与 133 个 NaN 结果均逐位相等。
- Dyadic：100196 次中 100038 个非 NaN 和 112 个 NaN 结果逐位相等；另外
  46 次双方都是 NaN，但符号位不同。该探针按 Tent 参数交叉重复部分 Dyadic
  输入，不能将次数理解成互不相同的值。

原始输出、生成器与比较脚本、固定 seed、hash 和真实退出码保存在忽略的
`logs/p3/chaotic-scalar-discovery/`。这些是当前机器单步对照，不覆盖任意数值
对象、完整多步/信号/资源、其他平台或发行验收，也不证明公共类已绑定。

## 切换前条件

1. 逐类确定等价的固定 Rust 入口及参数、全域/非有限值和异常到 Result 的明确
   政策；无法表达的模型按 [Rust 缺口](rust-gaps.md) 跟踪，不修改固定 pin。
2. 明确并测试开放数值协议、子类和迭代 hook，保留真实采集顺序、异常来源、
   初始对象身份和列表形状；不得引入静默旧内核 fallback 或隐式缩窄。
3. 对自然入口提供 Rust 直接差分、属性/边界、真实调用者、跨平台和完整调用
   性能/资源测试，并在当前 wheel/sdist 的仓库外安装中验证。
4. 对应公开算法、兼容说明、示例、类型和调用者一并迁移后，才可更新 api-map
   状态；任何单类的推进均不等于整个混沌模块或 P3 完成。
