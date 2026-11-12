# 原生绑定开发与真实后端验证

本页描述私有迁移边界，不是公共 API 升级指南。完整进度和执行证据仅保存在被忽略的 `logs/`。

## 精确数值开发入口

`ospf_python._binding.numeric.Rational` 为私有任意精度桥接，与仍未迁移的公共 Rational 类不同。使用默认无 solver 构建即可验证：

```python
from decimal import Decimal
from ospf_python._binding.numeric import Rational

value = Rational.from_value(Decimal("0.1")).unwrap()
print(value.as_integer_ratio())  # 精确 1/10 / Exactly 1/10.
assert value.to_float().is_failed()
assert value.to_float(exact=False).unwrap() == 0.1
assert Rational.from_json(value.to_json()).unwrap() == value
```

该入口只持 Rust 值，四则使用固定版 ospf-rust-math 运算 traits。工厂/可能失败的操作返回既有 Result；不把 Decimal、整数和物理量统一降为 Float64。完整域矩阵、负零/非有限值/舍入与严格 JSON 合同见 `numeric-contract.md`。私有桥接通过不等于公共数值和单位 API 已切换。

批量归约不必逐项包装 Python Rational：

```python
from ospf_python._binding.numeric import RationalArray

values = RationalArray.create([(1, 2), (1, 3)]).unwrap()
assert values.sum().as_integer_ratio() == (5, 6)
assert values.dot(values).unwrap().as_integer_ratio() == (13, 36)
```

数组不可变，`at` 和整数对快照拥有独立值；长度不匹配和零除数返回 Result，不截断或发布部分结果。这不是 NumPy view 或通用多维数组。可执行基准 `benchmarks/test_native_numeric_hot_path.py` 分离创建、已有值点积与包含创建的流程；当前精确计算的性能缺口见 RG-003，不能仅因批量化就宣称优于旧公共接口。

精确多维数组使用同一固定版 `ospf-rust-multiarray`：

```python
from ospf_python._binding.multiarray import RationalMultiArray, Shape
from ospf_python.multiarray.shape import StorageOrder

shape = Shape.create(dims=(1, 2), storage_order=StorageOrder.COLUMN_MAJOR).unwrap()
array = RationalMultiArray.create(values=values, shape=shape).unwrap()
assert array.at((0, 1)).unwrap().as_integer_ratio() == (1, 3)
assert array.flatten().unwrap().sum().as_integer_ratio() == (5, 6)
```

`access_order` 表示输入/展平时的坐标遍历，独立于存储布局。索引严格检查维数和范围，
`reshape` 拒绝截断、补值和隐式布局改变。元素、形状与展平批次均独立拥有 Rust 值。
完整合同与公开 NumPy/可变/视图替换前置见 `multiarray-contract.md`；此入口尚非公共数组替换。

`RationalMultiArray.create/reshape` 也接受现有公开 Shape1–4/DynShape，自动取受检快照，
不要求调用方改用私有形状类。自定义 Shape 协议/子类的映射不自动假定为标准布局；
可显式用 `Shape.from_shape(source, standard_layout=True)` 创建标准快照后传入。
超出机器寻址范围的公开稀疏形状只在原生稠密边界失败，不改变源对象能力。
公开形状的完整保留/决策合同及可执行性能基准见 `public-shape-contract.md`。

通用 Python 元素使用 `_binding.multiarray.MultiArray[T]`。它复制 list 中的强引用到 Rust
存储，不把元素转成 Float64/Rational，不共享 NumPy 缓冲，也不深拷贝元素：

```python
from ospf_python._binding.multiarray import MultiArray
from ospf_python.multiarray.shape import Shape2

payload = {"label": "item"}
objects = MultiArray.create(values=[payload, None], shape=Shape2(1, 2)).unwrap()
assert objects.at((0, 0)).unwrap() is payload
assert objects.at((0, 1)).is_ok()  # None 也是成功值 / None is also a successful value.
assert objects.flatten().unwrap()[0] is payload
```

原生 GC 遍历每个实际强引用，包括重复元素；清理时解锁后才释放元素，允许 Python 析构重入。
对应对象身份、循环回收、复活与并发读取合同见 `tests/native/test_object_multiarray.py`。
此私有容器尚未替换公开 NumPy/mutable/view API。

可变存储和矩形视图同样只使用 Rust 一份元素缓冲。NumPy 输入必须明确选择快照，
`copy=False` 返回 `NOT_SUPPORTED`，不会静默复制后冒称共享：

```python
import numpy as np
from ospf_python._binding.multiarray import MutableMultiArray
from ospf_python.multiarray.shape import Shape2

source = np.arange(6).reshape(2, 3)
array = MutableMultiArray.from_numpy(values=source, copy=True).unwrap()
view = array.view(offsets=(1, 0), shape=Shape2(1, 3)).unwrap()
snapshot = view.materialize().unwrap()
assert snapshot.flatten().unwrap() == [3, 4, 5]
assert view.set_many([((0, 0), 30), ((0, 2), 50)]).is_ok()
assert array.at((1, 0)).unwrap() == 30
assert snapshot.at((0, 0)).unwrap() == source[1, 0] == 3
```

`set_many` 先校验整个批次并拒绝重复坐标，再原子发布；解锁后才释放旧元素，析构允许重入。
视图持有最终源，嵌套视图在 Rust 中组合 offset，不持有跨调用 Rust 借用或第二份元素状态。
支持 strided/转置/负步长/广播/只读 NumPy 源的显式快照，以及 object 身份；保留 NumPy scalar
类型，不借用外部可变缓冲。结构化/void dtype、共享缓冲、零长轴及完整公开 slice/映射视图
仍须单独验收；并发外部 NumPy 写入由调用方同步。详见 `multiarray-contract.md`。

私有通用数组和矩形 view 也提供快照 `transpose()`（反转全部轴、翻转布局）、
`map(callback, *, access_order=...)` 和
`flat_map(callback, *, shape=..., access_order=...)`。输出是独立不可变容器，保持元素身份。
映射在 Rust 解锁后调用 Python，普通值和 `Ok(value)` 均可作为输出；失败/警告 Result
保留在 `FailureContext.callback_result`，普通异常保留在 `callback_exception`，
并附零基 `callback_index`。进程控制异常不吞。回调修改源不改变已快照的输入槽位，
但不回滚回调副作用、不 deepcopy 元素。完整合同和 RG-004 任意轴映射前置见上述文档。

惰性元素映射显式使用 `MappedMultiArrayView.create(source=..., callback=...)`，创建和 shape
读取不执行函数。`at(tuple)` 每次经单次 Rust 受检读取后重新执行函数；`materialize()`
使用完整 Rust 槽位快照并原子发布独立数组。以 mapped view 为 source 可组成有序回调链，
无中间权威数组/结果缓存；函数和最终源保活至 lazy facade 释放。源的后续写入会影响下一次
at，但不改变已物化容器。原 Result/异常合同同上。公开旧 view.map 的惰性语义、共享 ndarray、
scalar 转换、copy/pickle 与非 Result 签名差异见 `public-array-contract.md`，尚未公开切换。

通用数组和矩形 view 支持 `reduce(callback, *, access_order=...)`、`to_list()` 和
`iter_snapshot(*, access_order=...)`。reduce 从第一个槽位开始左结合，单元素不执行函数；
回调 Result/异常规则同 map，失败序号是二元调用的零基序号。Rust 快照后才调用 Python，
允许再次归约或写源，不发布部分累加值。to_list 委托 Rust 行遍历并包装嵌套容器，
列布局/offset 正确，scalar 返回原元素，保持叶对象身份而不调用 item/iter/len。
iter_snapshot 是显式 O(N) 引用快照的标准迭代器，不是 live iterator 或零拷贝；
所有原生失败在发布前以 Result 返回，耗尽使用标准 StopIteration。
这些私有合同不自动替代旧公共物理迭代/non-Result 接口或证明纯 Rust 数值性能预算通过。

公共 `ospf_python.multiarray` 的两个 `reduce(f)` 则单独接通固定 Rust 索引的 live
物理左折叠并返回现有 Result，详见 `public-reduction-cutover.md`。它不快照全部叶，
不自动解包回调返回的 Result；不能将上面私有快照归约的失败序号/解包政策混用。

通用/可变数组还提供 `full(shape=..., value=...)`，由 Rust 填充同一不透明叶引用并
直接交给固定上游存储；`zeros/ones(shape=...)` 是内置 float 的静态便捷工厂。
full 不广播 sequence、不推断 dtype 或调用叶协议；共享的是叶对象状态，不是可变槽位。
超出引用存储字节容量返回 OVERFLOW，预留失败返回结构化资源失败。此合同不替代旧公开
NumPy full/from_list 的广播、dtype、共享、序列化及错误签名。

通用/可变数组的 `to_snapshot()` / `from_snapshot(payload)` 返回受检 Python 引用 DTO，
显式保存 schema/version/kind/dims/storage_order/物理序列，不是 JSON，不自动重定位叶的 owner。
Shape、对象数组与矩形/惰性 view 支持标准 copy/deepcopy/pickle 图：浅复制共享句柄，深复制/
pickle 用 memo 保留新图中的重复叶、回边和共享句柄，native state 一次发布。顶层函数遵循
标准 pickle，局部 lambda 不自动变成可序列化。详见 `array-state-contract.md`；旧公开 payload、
共享 ndarray、原生精确数值/模型叶与跨语言 wire 不在本项验收中。

## 基础构建

使用 CPython 3.13、`rust-toolchain.toml` 指定的 nightly 及固定 Maturin。依赖来自 `native/Cargo.toml` 的完整 Rust Git revision，不要求相邻 Rust checkout。

源码包包含文档和示例，但不包含 `tests/`、`benchmarks/` 或 `scripts/`。本文中
引用这些目录的测试、基准及发行检查命令需要源码仓库；构建扩展后可直接运行源码包示例。

```powershell
python -m pip install maturin==1.15.0
python -m maturin develop --release --locked
cargo test --manifest-path native/Cargo.toml --locked
python -m pytest tests/native tests/packaging -q
```

`develop` 要求已激活的 venv；若使用 uv，可传 `--uv`。默认构建不编译任何 solver，真实求解测试明确跳过对应 feature，而不是用 Python SDK 替代。

`cargo test` 直接链接一个具体解释器（未启用 abi3），未指定 `PYO3_PYTHON` 时会挑选 PATH 上任意
Python，内置异常文案随版本不同而失败，且 `python313.dll` 不在 venv 目录而需工具链根目录。测试
前把 `PYO3_PYTHON`、`PATH` 指到项目 venv 及其基座解释器，不要把这种错链当成绑定缺陷。

Rust GC 单测会嵌入 CPython。Windows 使用 venv 时，测试进程的 PATH 还需包含该解释器
`sys.base_prefix`（`python313.dll` 所在目录）；仅在当前 shell 中配置，不改永久 PATH。
缺少该目录时测试可编译但启动返回 `0xc0000135`，不能记为单测通过。

```python
from ospf_python import _native
print(_native.build_info())
```

`native_solvers` 仅表示编译进扩展的后端，不是已找到动态库或已验证许可证。

## Windows SCIP 源码构建

需要 SCIP 9.x 的 headers、import library 和 DLL，以及可供 bindgen 使用的 libclang。环境变量仅为当前构建进程配置，路径按本机实际安装调整：

```powershell
$env:SCIPOPTDIR = 'C:\path\to\scip9'
$env:LIBCLANG_PATH = 'C:\path\to\llvm\bin'
python -m maturin develop --release --locked --features scip
```

仅在 User PATH 加入 LLVM 的 bin 目录不保证 clang-sys 能发现 libclang；当前依赖可使用 `LIBCLANG_PATH`。不能将开发机绝对路径写入 Cargo 配置或发行包。

Windows CPython 的扩展依赖搜索不等于 shell PATH 搜索。导入 solver-feature 扩展前，显式注册可信的 DLL 目录并保持返回句柄存活：

```python
import os

scip_dll_directory = os.add_dll_directory(r"C:\path\to\scip9\bin")
from ospf_python import _native
```

仓库原生测试及发行验证工具支持 `OSPF_NATIVE_DLL_DIRS`，多个目录使用当前平台路径分隔符。它只是这些验证工具的约定，不是库自动加载任意 PATH 或全局安装 SDK 的机制。

```powershell
$env:OSPF_NATIVE_DLL_DIRS = Join-Path $env:SCIPOPTDIR 'bin'
python -m pytest tests/native -q -rs
```

不自动把第三方 DLL 打入 wheel，不改变许可证/分发责任。

## Gurobi

仅显式支持 Rust 的 `gurobi10`、`gurobi11`、`gurobi12`，选择与本地 SDK 一致的一个 feature。多个 Gurobi 版本同时启用会由 Rust 编译门禁拒绝。没有 `gurobi` 自动版本别名，也不支持 13。

```powershell
python -m maturin develop --release --locked --features gurobi10
$env:OSPF_NATIVE_DLL_DIRS = Join-Path $env:GUROBI_HOME 'bin'
python -m pytest tests/native -q -rs
```

需要匹配 SDK、本地动态库和有效许可证。编译成功或安装 Python extra 都不能替代真实运行。`pip install ...[gurobi]` 不会给已经编译的 wheel 增加 Cargo feature。

## 最小私有闭环

```python
from ospf_python._binding.model import MetaModelFloat64, VariableSpec

model = MetaModelFloat64.create("example").unwrap()
x = model.add_variables([VariableSpec(name="x", lower=0, upper=2)]).unwrap()[0]
model.set_objective(terms=[(x, 1)], sense="maximize").unwrap()
report = model.solve(solver="scip").unwrap()
print(report.problem_status, report.objective)
model.close().unwrap()
```

示例为简洁而显式 unwrap；应用应传播 Result。模型、变量和求解状态只有 Rust 一份，Python 仅持句柄及结果快照。限制与待验证能力见 ADR 0002。

私有模型可通过 `model.set_bounds(handle=x, lower=0, upper=1)` 替换变量范围；
连续/整数变量的 `None` 表示无界，二元变量的 `None` 恢复相应的 0/1 默认界。
范围验证失败不会修改模型。固定为零不等同于删除变量或完成列生成；已有报告
仍是原求解的快照。公共泛型 `MetaModel` 尚未切换。

私有模型的 `generation()` 返回所有者线程的单调修改代次；
`report.model_generation` 是求解时的代次快照。成功的空批次或重复设置也会
推进代次，失败事务或单项校验失败不推进；提交阶段意外出错则保守推进，代次
耗尽时拒绝修改。关闭后查询失败，历史报告
仍可读取。此字段是诊断信息，不是不可伪造的证书。普通 `solve()` 的报告仍未绑定
带源行映射的编译模型；私有 `solve_compiled()` 单独返回同次编译的标准最小化
报告以及认证证书 Result。`source_price()` 仅接受该模型、当前代次的原生证书及
原约束句柄，返回原目标口径的价格；不可认证时不改写正常报告。证书不能从 JSON
构造，修改、关闭或跨模型使用会失败。该能力尚不是公共模型或生产列生成切换。
SCIP 的编译路径暂拒绝显式时限，见 RG-013；完整限制见 `linear-dual-contract.md`。

固定 Rust revision 的线性目标常数存在 RG-001，当前私有原型显式拒绝非零常数，不自动修改 Rust 报告。该缺口尚未解决，详见 `rust-gaps.md`。

`time_limit` 以秒传入，先转换为纳秒分辨率的 Rust `Duration`；正数若舍入为零
会在接受求解前返回失败。当前绑定将转换后的同一限制传入后端配置和单次选项，
使实际后端调用的报告及配置指纹包含该限制；不在 Python 中补写报告。报告记录
转换后的配置而非输入的全部小数位。预取消报告的配置摘要不代表后端已启动，
其配置指纹可为 None。此适配不表示 RG-012 的 Rust 通用单次选项问题已修复。

## 取消与进度回调

```python
from ospf_python._binding.control import SolveHandle, SolveProgress

control = SolveHandle()

def on_progress(event: SolveProgress) -> None:
    print(event.source, event.stage, event.objective_value)
    if event.source == "backend":
        control.cancel(origin="callback", reason="example stop").unwrap()

report = model.solve(
    solver="scip", cancellation=control, on_progress=on_progress
).unwrap()
```

此片段用于尚未关闭的模型；每次求解使用新的 `SolveHandle`。也可由其他线程调用 `cancel()`，不必等待模型所有者。预取消与运行中取消以正常 CANCELLED 报告返回；取消请求不保证立即生效，也不改写早已完成的结果。

回调在 Rust/后端线程运行，接收不可变快照，可返回 None 或既有 `Ok(None)`。失败 Result 保留原对象和领域 payload；异常及无效返回变成 `Failed`，分类为 CALLBACK。回调访问同一模型（包括查询/close/修改/solve）立即 busy Failed，不允许重入。请勿在回调中等待依赖调用线程的应用锁或 UI 操作。

`source=reporter` 与 `source=backend` 区分统一进度与实际后端遥测；未知进度为 None。求解结束时绑定释放 Python callback 引用，但 RG-002 的 SCIP 底层观察者保留仍待上游修复；不能把 Python callable 可回收当成完整原生资源验收。

## 数组 Live 游标

私有数组/矩形 view 的 `view(*, offsets=None, shape=None)` 可由 Rust 推导有效剩余范围，
嵌套范围以当前父区域为界。旧 view 字段可显式用
`MultiArrayView.from_legacy_state(payload=vars(old_view), copy=True)` 复制迁移，仍不接管
公共共享/自动 pickle/默认入口。所有权、拒绝范围和示例见 `view-extent-contract.md`。

私有数组和矩形 view 可调用 `iter_live(*, access_order=None)`，返回受检的
MultiArrayIterator。None 沿用物理布局，显式行/列顺序按逻辑坐标；每次读取一个当前槽位，
不预先快照。next 与 advance 共享原生位置，advance 返回 Result 包装的
(present, value)，可区分 None 叶和耗尽；close 或最后一次成功消费即释放源/facade。
GC、并发、协议错误和非序列化政策见 `array-iteration-contract.md`。公共默认 generator
另走原生 shared-storage 协议适配器，并保留原 ndarray 共享与最后 yield 后保活；不是接入
私有 iter_live，兼容说明见 `public-iteration-cutover.md`。其他公共存储/数学路径仍待迁移。

## 数组诊断

数组诊断可使用私有 `describe(*, formatter=repr, max_items=20, max_chars=4096)`：
Rust 仅快照逻辑前缀，标明存储布局/view offset，在解锁后格式化，按 Unicode 字符裁剪整个
输出。返回现有 Result，保留格式器失败/异常/位置，并防护线程内同源递归；不改写默认 repr。
完整资源边界和剩余公开协议门槛见 `array-description-contract.md`，逻辑比较见
`array-comparison-contract.md`。字符预算不是用户 formatter 的执行沙箱。

## 混沌系统单步私有入口

```python
from ospf_python._binding.chaotic_system import SUPPORTED_SYSTEMS, chaotic_system_step

result = chaotic_system_step(
    system="RosslerAttractor", params=[0.2, 0.2, 5.7, 0.005], state=[1.0, 1.0, 1.0]
)
print(result.value if result.is_ok() else result.error)
```

`_native._chaotic_system_step(*, system, params, state)` 把 20 个上游吸引子系统按固化参数
映射委托固定 Rust revision，返回同长度的新状态分量。输入只接受 `list`/`tuple` 里的内置
`float`，长度或元数超过 9、维度不符、未知名都返回结构化 `ILLEGAL_ARGUMENT` 而不是抛异常；
计算在 `py.detach()` 内进行并在前后各检查一次信号，因此 `Ctrl+C` 不会被吞。逐位平价、
证伪的 5 个类与允许的处置见 `chaotic-system-contract.md`。

这是**私有**候选通道，只有 `ospf_python._binding.chaotic_system.array_step_or_none` 被公开类使用：

```python
import numpy as np
from ospf_python._binding.chaotic_system import array_step_or_none

state = np.asarray([0.7, 1.3, 2.1], dtype=np.float64)
result = array_step_or_none(
    system="BurkeShawAttractor", params=(10.0, 4.272, 0.001), state=state
)
print(None if result is None else result.tolist())
```

它只覆盖可证明逐位且同形的窄域——`float64` 数组，或每个分量恰为内置 `float` 且全部有限的
`list`/`tuple`，且参数分量同样如此；任何超域输入返回 `None`，由调用方原样保留既有实现。
`BurkeShawAttractor`、`ChenCelikovskyAttractor`、`ChenLeeAttractor`、`ChenSystem`、`ChuaCircuit`
这 5 个 ndarray 形状的公开类已经接这条快路（完整调用预算比值 0.704–0.810），其余 15 个候选类
仍走原 Python 内核：标量/tuple 调用形状在单步原生入口上是 2.4–7.1× 的回归，需要上游提供
批量/多步入口才可能达标。tuple/scalar 形状、`np.float64`/`Decimal`/`Fraction` 等开放数值协议
仍未委托，完整调用预算也只做了本地时间比值，未做内存包络与 Linux/多平台矩阵证据，
因此这 5 个类停在 `bound`，不构成退役或全平台声明。

## 发行验证

```powershell
python -m maturin build --release --locked --out dist/wheels
python -m maturin sdist --manifest-path native/Cargo.toml --out dist/sdist
python scripts/verify_binding_distribution.py --wheel <wheel> --sdist <sdist>
```

基础 wheel 必须报告空后端。验证 solver-feature wheel 时显式添加 `--native-solver scip` 或对应 Gurobi feature；工具将验证准确的编译能力、执行真实 Rust 求解、进度回调、单次句柄及预取消，并在提供 sdist 时以相同 feature 和 `--locked` 从仓库外重建。

禁止将不同 feature 的同名 wheel 混放在同一候选目录或当作不同的正式发行身份。按验证场景隔离输出目录；默认正式策略仍是无 solver 的基础 wheel。

发行检查器只接受求解器 SDK 的单个非空 `extra == '名称'` 标记；无标记或更复杂
的标记均会拒绝，即使后者按 PEP 508 可能是安全的。这个保守约束覆盖当前 Maturin
元数据，若发行策略改变，须重新审查标记而非通过字符串包含判断其可选性。
开发 extra 包含 CI 的 `pytest-timeout` 插件；求解器测试使用的 `--timeout=60`
是逐测试超时，不代表原生求解器取消或资源释放已验收。
