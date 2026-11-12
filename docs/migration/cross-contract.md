# 公共笛卡尔积的 Rust 边界

## 接口升级

自然入口仍为 `ospf_python.math.combinatorics.cross` 和其原模块中的 `cross`，
现在返回现有三参 sealed `BindingResult[list[tuple[T, ...]]]`，不再直接返回 list。
成功值的排列次序和叶身份保持不变。普通输入协议失败返回 `Failed`，不新增业务异常。

The natural import paths remain unchanged. `cross` now returns the existing
three-parameter sealed Result rather than a bare list; tuple ordering and leaf
identity are preserved. Ordinary external protocol failures become `Failed`.

```python
from ospf_python.math.combinatorics import cross
from ospf_python.utils.functional.result import Failed, Ok

result = cross([1, 2], (label for label in ["a", "b"]))
match result:
    case Ok(rows):
        assert rows == [(1, "a"), (1, "b"), (2, "a"), (2, "b")]
    case Failed(error):
        print(error.message)
```

原来直接遍历 `cross(...)` 的调用方需改为消费 Result，组合流程可使用 `.map`/
`.flat_map`。只有调用方已经明确验证成功的代码才适合 `.unwrap()`。
没有 `backend='legacy'`、兼容别名或静默 Python fallback。

Callers must consume the Result before iterating. Use `map`/`flat_map` in fallible
pipelines; `unwrap` is only appropriate when success is already established.
There is one default authority and no selectable legacy implementation.

## 枚举、类型和存储

- 固定 revision `119854756a0aeb66d2998055f96fa7175c7bfb37` 的
  `ospf_rust_math::combinatorics::{cross_iter,cross2,cross3}` 负责所有非零元积枚举。
  Python 前缀扩积循环已移除。1–6 元使用上游静态组合并直接打包 Rust tuple；
  任意更高元数使用同一上游动态迭代器，不丢弃能力或改用 Python 算法。
- 快照依次使用真正的内置 `list(pool)` 语义，接受任意 iterable，包括一次性 generator、
  旧式 `__getitem__` 序列、自定义 iterator、dict/string/range 与 ndarray。
  `__iter__`、长度提示及异常顺序不改成另一套协议。
- 先从左到右完整消费所有输入，再判断空池。前面有空池也不会跳过后面的副作用或失败。
  非空池按输入位置保留重复元素；右侧池变化最快，和原结果次序一致。
- 零元积保持 `[()]`，含空池的积保持 `[]`。上游零输入返回空，边界只适配该单位元，
  不是另写枚举内核。
- 槽位快照独立于源池后续增删，但不深拷贝或冻结叶。后续池协议对已有叶的修改仍可见。
  同一个对象的重复引用、None、Result、Fraction/Decimal、任意精度整数、复数、
  NumPy scalar/ndarray、Quantity 以及下游对象都保持身份。
- 不对叶调用 `item`、数值转换、hash、相等、算术或用户复制协议。
  不移除单位、不统一到 float；该操作不承诺替换叶所属的数值/物理量内核。
- 输出是标准 Python list/tuple，没有持久 Rust 所有者、隐藏缓存或双份可变状态；
  按标准 Python copy/pickle 保持对象图。临时快照和枚举缓冲在返回/失败退出时释放。

The pinned Rust kernels own enumeration, including static-arity specializations.
Input slots are snapshotted once, leaves stay opaque, and output containers are
ordinary Python objects. Neither numeric coercion nor a second mutable model is introduced.

## 错误、容量和外部协议

所有池消费完成后，非空积先检查乘积、结果引用槽位字节数及上游 i32 轴游标的宽度限制。
超出原生地址容量返回结构化 `OVERFLOW`，来源为 `ospf-python-native`，不等到巨大枚举后
才失败。空池已经把结果消去时不错误报告乘积溢出，但后续输入的真实异常仍要保留。

普通输入协议异常（包括 TypeError/ValueError/OverflowError/MemoryError）原样存入
`FailureContext.callback_exception`，保留 traceback，不调用用户异常的 `str/repr`。
对应 code 为 `APPLICATION_ERROR`，结构分类为 `EXTERNAL_ITERABLE`。
`KeyboardInterrupt`、`SystemExit`、`GeneratorExit` 等 BaseException 按 Python 协议传播。
不发布部分输出，不回滚已经发生的用户迭代副作用，也不声称可以恢复操作系统级内存耗尽。

没有跨外部协议的锁，输入协议可以重入 `cross`。此同步接口持 GIL，未增加后台工作线程、
异步枚举或取消句柄；动态路径发布期间定期检查 Python signals，静态批量路径在前后检查。
不承诺固定取消延迟，尤其不能用输入回调测试证明大静态输出的信号响应时限。

Checked capacity failures are structured. Original external exceptions are
retained without formatting; process-control exceptions propagate. No lock spans
external iteration, no partial output escapes, and user side effects are not rolled back.
This is synchronous, not a new asynchronous or bounded-latency cancellation API.

## 验证和性能口径

合同覆盖 0/1/2/3/4/5/6/7/13/2048 元、重复/空池、一次性和自定义协议、可变叶、
错误与重入、身份/资源释放和标准对象图 roundtrip。
独立 `itertools.product` 只在测试/基准中作 oracle，生产路径不依赖它。

公开热路径基准见 `benchmarks/test_public_cross_hot_path.py`；比较旧实现的冻结源码及
本地测量保存在被忽略的 `logs/p3/public-cross/`。必须把快照、Result、输出创建和销毁
计入操作成本，不能把 solver 耗时缩短归因于枚举或掩盖操作回归。
静态打包会使用临时 Rust tuple 缓冲；时间改善不等于峰值内存改善。
本地资源探针单独运行旧/新路径，使用 100,000 个五元结果：事先限定进程峰值工作集
增量不超过 32 MiB，五次预热后再执行 50 次调用的 PrivateUsage 增长不超过 8 MiB。
另用弱引用检查每个静态元数和动态元数的叶释放；通过这些门槛也不能推断全部长期泄漏不存在。

真实后端合同用保留 `Quantity[Fraction]` 的配置积建立 binary 选择 MILP，在同一米单位下
经受检 Rational/Float64 转换注册长度和收益系数，选出唯一最优配置，核对原叶身份。
它只证明这一消费者闭环，不证明公开 MetaModel 或整个领域 framework 已切换。

当前平台证据限定 Windows CPython 3.13；固定 runner、长期/全领域资源预算与 Linux/
Gurobi11/12 的整体验收仍分别跟踪，不能由本地操作测试替代。
发行 smoke 在 wheel 安装及相同 sdist 的 locked 重建后执行相同自然入口和失败路径，
不要求相邻 Rust 仓库或 solver 许可证才能导入基础包。

The operation, real-solver consumer, and distribution checks have separate scopes.
Local operation budgets do not certify all platforms, long-term resources, or
the complete modeling/framework migration.
