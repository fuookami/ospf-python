# Geometry Distance / 几何距离

## Scope And Status / 范围与状态

本合同覆盖 `distance`、`distance3`、`distance_squared`、`manhattan_distance`、
`Vector.magnitude` 与 `Edge.length` 六个现有入口及其自然调用。它们目前仍执行
原 Python 实现，**没有切换到 Rust**；`Vector.normalize` 也会调用 `magnitude`。
本合同不覆盖其他几何算法或整个几何模块。

固定 revision `119854756a0aeb66d2998055f96fa7175c7bfb37` 的 `Euclidean`、
`Point.distance`、`Edge.length` 和二维 `Vector.norm` 是相关候选，但直接替换
欧氏路径在极端数值和非有限值上不等价，见 [RG-019](rust-gaps.md#rg-019)。
独立 debug/release Rust 见证不经过 Python 绑定，生产与探针 lock 的 115 个共有
依赖条目的版本、来源和 checksum 一致，实际 `ospf-rust-math` 依赖树的 28 个
不同条目亦一致。`logs/p3/geometry-distance-contract/`
保存探针、逐项位模式比较及真实执行记录；证据仅针对本机 Windows。

平方距离与曼哈顿距离的 Float64 数值语义另行见证：同一固定 revision 的
`Point.distance_squared`、`Edge.length_squared` 和 `Manhattan.distance` 在 10 组
位模式（普通、大有限数、反向大数、极小、次正规、负零、`inf`+`nan`、`nan`+`inf`、
`inf-inf`、常规小数）上与当前 Python 逐位相同，debug 与 release 一致，
见 `logs/p3/geometry-squared-manhattan-contract/comparison.json`。因此 RG-019 的
缩放/非有限差异不适用于这两个入口；真正的阻碍是上游度量被 sealed 到 `f32`/`f64`，
无法接收现有公开域，见 [RG-020](rust-gaps.md#rg-020-f32f64)。

## Public Numeric And Protocol Boundary / 公开数值与协议边界

- 二维 `distance` 先分别计算 `p1.x - p2.x`、`p1.y - p2.y`，再将两个差值交给
  `math.hypot`；`Edge.length` 的差值方向为 `end - start`。`Vector.magnitude`
  将 `x`、`y` 交给 `math.hypot`。大有限数、极小数和次正规值不应因为中间平方
  而不必要地变成无穷或零；无穷与 NaN 混合时 `hypot` 返回无穷。
- 三维 `distance3` 将两个点的坐标先分别组成元组，再调用 `math.dist`。这不是
  二维计算的机械扩展：当两点坐标分别为 `2**1024` 与 `2**1024 - 3` 时，二维
  先做整数减法可以得到 `3.0`；三维对原坐标做浮点转换会发生 `OverflowError`。
  本机 CPython 3.13 中，六个字段先按第一个点、第二个点顺序读取；后续浮点
  转换按轴交错采集两个点。迁移前需明确该可观察顺序的兼容政策。
- 平方距离先计算两个差值，再分别平方并相加；曼哈顿距离在读取第二个轴前已对
  第一个差值取绝对值。两者实际接受大整数、`Decimal`（受其上下文约束）、
  `Fraction`、NumPy 数组及满足运算槽的用户对象，结果也不一定是 float。
  类型注解不是将这些输入隐式压成 Float64 的许可。
- 点不要求是 `Point` 实例，字段读取、减法、乘法、绝对值、加法和转换可能是
  用户回调。测试覆盖调用次序、首个减法异常及其原对象身份、减法抛出
  `BaseException` 的传播，以及成功后不保留点对象。不要在前置快照中提前读取
  后续字段或隐藏回调异常；其他回调失败的完整覆盖仍待补充。
- 现有自然入口返回原始值并可能抛出异常；目标业务接口须按项目的 Result 规则
  明确升级策略及真实调用方，不得把异常悄悄变成 NaN/0。`Vector` 和 `Edge` 的
  DTO、子类、字段身份、序列化及 `normalize` 消费合同还须各自验证。

### 平方与曼哈顿完整公开域 / Squared And Manhattan Full Public Domain

以下行为已由 `tests/math/geometry/test_squared_manhattan_domain_contracts.py` 固定，
实测记录在同目录 `logs/p3/geometry-squared-manhattan-contract/explore*.log`：

- `Decimal` 受**调用方上下文**约束：在 `prec=28` 时 `(1E+20-1)` 的平方和为
  `1.999999999999999999960000000E+40`（28 位有效数字），`prec=60` 时给出更长的精确值；
  默认 `Emax` 下的平方溢出抛出 `decimal.Overflow` 信号异常，不是 `inf`。`Infinity`、
  `NaN`、`-0` 保持 Decimal 语义（`-0` 的平方与绝对值和均为 `Decimal('0')`）。
- `Fraction` 保持精确；复数不是度量域：平方得到 `(-14+48j)` 这类非实数（甚至非负
  实数不成立），曼哈顿因 `abs(complex)` 折算成 `float` 模长 `10.0`。迁移不能把
  “距离必为非负实数”当作既有事实。
- 任意宽整数精确；`bool` 坐标在减法后加宽为 `int`（`True/False` 的平方为 `2`）。
- NumPy 整数**不回扩位宽**：`np.int8(20)` 与 `np.int8(4)` 的平方回绕为 `np.int8(0)`
  并发出两次 `RuntimeWarning: overflow encountered in scalar multiply`；`int16` 数组
  元素级回绕（`[300,400]` 平方和为 `[-16608,-7680]`），曼哈顿则保留 `[600,800]`；
  `np.float32(1e20)` 的平方为 `inf`。dtype/shape 与元素级语义必须原样保留。
- 失败与次序：不支持的操作数（`Fraction` 与 `Decimal`、`str`、`None`）在**第一个轴**
  的减法上抛出原 `TypeError`；`__mul__` 失败发生在读取两个轴的 `y` 之后、第二个乘积
  之前并保留原异常身份；缺少 `__abs__` 时曼哈顿在读取 `y` 之前失败。
- 完成调用后不保留点对象强引用（weakref + `gc.collect()` 验证）。
- 包级别名：`ospf_python.math.geometry.distance_squared` 等与
  `ospf_python.math.geometry.distance` 模块中的定义是同一对象，且四个函数均在
  `__all__` 中；同名子模块 `ospf_python.math.geometry.distance` 被同名函数**遮蔽**，
  `from ospf_python.math.geometry import distance` 得到函数而非模块，别名身份只能
  通过 `importlib.import_module("ospf_python.math.geometry.distance")` 证明。
  `ospf_python.math` 包不重新导出这些函数，全仓仅此处定义。

## Required Cutover / 切换要求

1. 使用能表达完整数值政策的上游 Rust 能力，或经授权修复并审查固定 revision；
   不能在绑定中复制平方和/缩放算法，也不能仅对普通 Float64 走 Rust 后静默
   回退旧 Python。允许保留协议适配不等于保留另一套几何计算内核。
2. 为浮点精度、非有限值、signed zero、跨平台误差、开放数值协议和不同的二维/
   三维转换顺序制定一致且可审查的合同；平方和曼哈顿路径各自审核，不将
   RG-019 的结论自动推广为它们不可迁移。
3. 同步公开返回值/异常政策、类型、调用方、示例、DTO 与序列化；验证字段和
   回调次序、异常身份、资源释放，以及 `Vector.normalize` 等真实消费者。
4. 完成全域差分、真实业务、完整自然调用性能和资源预算、当前 wheel/sdist
   仓库外隔离安装与承诺的平台矩阵，之后才能标记切换并删除相应旧算法。
   本机探针、合同基线和其他私有 Rust 桥接均不替代这些门槛。
