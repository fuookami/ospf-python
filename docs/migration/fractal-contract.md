# 公共分形模块替换合同

日期：2026-10-27。固定 Rust revision：
`119854756a0aeb66d2998055f96fa7175c7bfb37`。

本工作包覆盖 `ospf_python.math.fractal` 的两个公开类：

- `MandelbrotSet.iterate`
- `MandelbrotSet.contains`
- `JuliaSet.iterate`
- `JuliaSet.contains`

## 默认权威路径

四个入口的复数迭代与逃逸判定统一委托给固定上游
`ospf-rust-math::fractal::escape_time`。绑定只负责把 Python 复数协议转换
为两个 `f64` 分量并选择初始 `z`：

- Mandelbrot：`z = 0+0i`，`c` 为方法输入。
- Julia：`z` 与 `c` 均为方法输入；`c` 由实例的 `c_real`/`c_imag` 组成。

公共路径不保留 Python 复数循环、隐藏 NumPy 计算或失败后的旧内核 fallback。

精确内置 `complex` 与精确内置 `int`/`bool` 的公共调用在方法内完成同等上限检查、
原生调用和 Result 发布，不再经过一层 `_binding.fractal` Python 帧；其他输入继续
委托该适配器。两条路径使用同一个固定上游逃逸循环，不建立第二数值内核。
Julia 的内置 float `contains` 仍先构造参数 `c`、再构造点 `z`，随后调用公开
`iterate` 的现有 Result `map`；自定义输入继续走原 pair Result 适配。

## 输入与返回协议

- `iterate` 保持历史采集顺序：先读取 `operator.index(...)`，再转换相应复数
  输入。`MandelbrotSet.contains` 经由 `iterate` 保持同一顺序。
- `JuliaSet.contains` 保持历史采集顺序：先构造实例参数 `c`，再构造点
  `z`，最后经由 `iterate` 读取 `max_iter` 的 `operator.index(...)`。
- `MandelbrotSet.iterate` / `JuliaSet.iterate` 返回
  `Result[int, str, ExErr]`；`contains` 返回 `Result[bool, str, ExErr]`。
- 成功发布使用当前 `Ok` 构造器，不绕过其 `__new__`/`__init__`。
  `contains` 通过公开 `iterate` 的 Result `map` 协议映射成功值；
  `Failed`/`Fatal` 原样透传，`Warn` 保留原 warning，不强制 `unwrap`。
  Julia 的公开 `iterate` 在复数输入转换完成后才解析，转换 hook 对该入口的
  替换当次生效，而不是提前缓存 callable。
- 输入转换异常作为 `Failed` 保留原异常实例和 traceback；`BaseException`
  继续原样传播。
- `max_iter <= 0` 不进入数值循环，返回原值；`contains` 仍按旧规则与该原值
  做相等判断。因此负值保持历史上的真值结果，不擅自改成参数错误。
- 正值超过 `u64::MAX` 返回显式 `RESOURCE_EXHAUSTED`，不截断为机器字并继续。
- `JuliaSet.escape_radius` 原有实现只存字段、不参与 `iterate`/`contains`
  判定；本迁移保留该兼容行为，不暗中改变结果。

## 数值语义

固定上游在每次迭代前检查 `real^2 + imag^2 > 4.0`，未逃逸时返回
`max_iterations`。Python `complex` 的分量本身是 `float64`，所以绑定不做额外
舍入、容差或 float32 降级。NaN、无穷、signed-zero 和超大有限值按 IEEE
比较路径交给固定上游执行。

## 资源与取消

当前原生计数不超过 `4096` 时保持 GIL，较长调用释放 GIL 并在调用前后
检查 Python 信号；这个阈值不是运行时间或取消延迟保证。固定上游
`escape_time` 是单个不可中断循环；本包不宣称可在循环内部及时取消，也不把
巨大迭代次数的实际不可完成性冒充为资源沙箱。后续长期资源与取消验收仍需
单独完成。

## 验收

必须同时保留原 `tests/math/test_fractal.py` 的 16 项公开基线，并新增：

- 两类的网格/边界正确性对拍；
- Result 成功/失败与输入异常来源；
- `max_iter` 的 bool、零、负数、>u64 与 `__index__` 协议；
- 复数协议、NaN/无穷、冻结 dataclass 和无 fallback；
- Rust/native、双后端、完整回归、发行安装与完整自然调用性能证据。

当前快路径的合同、性能与证据保存在
`logs/p3/public-fractal-current-20261031/`（纯比值协议，两轮 `14/32` 和 `13/32` 失败）。

### 已采纳的预算口径（2026-11-11 用户裁决 C：warm 判定 + cold-first 只作诊断）

```
判定（唯一参与通过/失败的）：
  warm      : current <= 1.15 * before + 5,000 ns
  cold-first: 不参与判定，逐行测量并完整记录
```

**为什么 cold-first 退出判定**（B257/B258 的 8 轮实测，不是估计）：

| 行类别 | 8 轮内加性预算失败次数 | 说明 |
| --- | --- | --- |
| **warm** | **0** | 最紧一行只用掉限额 **67.8%**，余量 20 个百分点 |
| **cold-first** | **2** | 失败行每次不同：`julia-interior-m8` 需加性 ≥ **33,568 ns**、`julia-escape-m1000` 需 ≥ **25,820 ns** |

cold-first 的尾部需求到 **33,568 ns**，比 B206 的物理估计（首次进入原生扩展
**18,860–22,580 ns**）**高 49%**。**这个量测的不是「每调用成本」，而是
「进程首次进入原生扩展」的一次性开销量**（PEP 659 自适应特化 + 首次 FFI），
把它算进「完整自然调用预算」本身是口径错配。

**warm 的 5,000 ns 加性项仍有物理依据**：原生裸调用稳态约 **400 ns**，
合同禁止绕过的 `Ok` 发布/解包约 **186 ns**（B206 三条独立测量互证）。

**没有**绕过 `Ok`、跳过 `map`、导入时预热或修改计时循环/批次数。
cold-first 的子进程重复次数从 4 提到 **12**（只为压噪声，**阈值不动**），
`before`/`current` 在同一批子进程内交替测量，因此不偏向任一侧。

### 新证据

| 证据目录 | 协议 | 结果 |
| --- | --- | --- |
| `logs/p3/b257-fractal-additive-budget-20261111/` | 加性 5,000/25,000，重复 4 | 4 轮 **1 轮失败** |
| `logs/p3/b258-fractal-coldfirst-sampling-20261111/` | 加性 5,000/25,000，重复 12 | 4 轮 **1 轮失败** |
| **`logs/p3/b259-fractal-warm-only-budget-20261111/`** | **warm 判定，cold 诊断，重复 12** | **4 轮全部 0 失败**（判定 16 行 / 诊断 16 行） |

**v3 的四轮明细**（诊断列同时说明为什么必须退出判定）：

| 轮次 | 判定行 | 诊断行 | **预算失败** | 纯比值失败（历史） | 诊断行若仍判定会失败 | cold 最大需加性 |
| --- | --- | --- | --- | --- | --- | --- |
| round1 | 16 | 16 | **0** | 13 | 1 | 26,080 ns |
| round2 | 16 | 16 | **0** | 14 | 1 | 25,150 ns |
| round3 | 16 | 16 | **0** | 13 | 0 | 23,878 ns |
| round4 | 16 | 16 | **0** | 14 | 0 | 24,205 ns |

**长期资源与取消验收仍单独开放**（见上文「后续长期资源与取消验收仍需单独完成」）：
固定上游 `escape_time` 是不可中断循环，本包不宣称循环内及时取消，也不把巨大迭代
次数的实际不可完成性冒充为资源沙箱。该项在 API map 的 `pending_acceptance` 中
**未被单列**，在此如实记录，不得因预算通过而当作已完成。
