# 嵌套数组输入合同 / Nested Array Input Contract

私有 `MultiArray.from_list(*, data, shape)` 与 `MutableMultiArray.from_list` 从显式形状
取得受检 Rust 存储。Python 只适配 shape 与 Result，原生边界负责 Python 容器结构解析，
固定上游 builder 负责布局和数组所有权，不新增 Python/NumPy 数学内核。

These private factories parse Python container structure in the native boundary and delegate
array layout/storage to the pinned Rust builder. They do not switch the public array classes.

## 结构与叶 / Structure and Leaves

- 必须提供现有 Rust Shape 或内置公开 shape 的受检快照，不推断 shape。标准自定义形状可先
  显式 `Shape.from_shape(..., standard_layout=True)`，不调用旧索引算法。
- 对于 rank D，前 D 层必须是**内置** list/tuple，逐轴长度严格等于 dims。允许混合 list/tuple，
  不接受结构层的 ndarray、range、任意 Sequence 或容器子类，不调用它们的协议来猜测形状。
- 深度 D 的值原样作为不透明叶，允许 None、Result、list/tuple/ndarray 及其子类、数值、单位、
  领域对象；不调用叶的 len/iter/array/item/copy，不解包 Result，不深拷贝。
  因而“多一层 list”不必然是错误：若到达声明的叶深度，它就是 list 叶。
- scalar shape `()` 不读取结构，整个 data（即使它是容器）是单个叶。零长轴仍按已有稠密 shape
  边界拒绝；不发明空数组的数值零、归约初值或特殊布局。
- 结构不足、非内置结构、逐轴长度错误返回现有三参 Result 的 Failed，带原生来源与 INPUT
  分类；不按相同总元素数自动 reshape、补值、截断或广播，不发布部分数组。
- shape 有限地约束深度；共享/循环容器不会触发无界搜索。若某个 list 回边在结构深度内出现，
  继续按该轴长度校验；到叶深度后保留原 list 身份，不递归展开或重定位对象图。

```python
from ospf_python._binding.multiarray import MultiArray
from ospf_python.multiarray.shape import Shape2, StorageOrder

leaf = ["opaque", "leaf"]
array = MultiArray.from_list(
    data=[[0, leaf], [2, 3]],
    shape=Shape2(2, 2, StorageOrder.COLUMN_MAJOR),
).unwrap()
assert array.at((0, 1)).unwrap() is leaf
assert array.flatten(access_order=StorageOrder.COLUMN_MAJOR).unwrap() == [0, 2, leaf, 3]
```

## 布局与所有权 / Layout and Ownership

嵌套结构表达**逻辑坐标**，由外到内对应 dims 的各轴。原生解析得到逻辑 row-major 叶序列，
固定 `MultiArrayBuilder::from_list_with_order(..., RowMajor)` 转为声明的目标存储布局。
任意布局下 `to_list()` 与此入口可按同一 shape 组合，保留所有叶身份；scalar 返回原叶。
它不同于 `from_legacy_state` 的物理平铺输入，也不同于没有 shape 的任意嵌套推断。

唯一 Rust 叶 Vec 持每个槽位的强引用，源 list/tuple 的结构不被保留（除非本身是明确的叶，
或经其他叶回指源）。输入结构后续修改与可变输出写入相互独立；叶自身的可变状态仍共享。
重复叶逐槽计入现有 GC 遍历；leaf.owner -> facade 等环可回收。成功/失败均不保留解析栈。
失败时已经取出的暂存引用在没有数组锁的情况下释放，不持久保留成功前缀。

解析使用 O(rank) 显式栈，不依赖 Python/Rust 递归深度，不引入索引/stride/广播数学算法。
在分配前检查叶与栈字节容量，超 isize 为 OVERFLOW；fallible reserve 失败为
APPLICATION_ERROR/RESOURCE。输出及栈容量受检不表示任意大请求都可成功，也不防止 OS
资源策略终止进程。布局转换内部仍遵循固定上游自己的分配行为，全面资源预算尚待验收。

标准 CPython 3.13 构建中，此解析不释放 GIL，不执行用户协议或持有数组锁。结构读取不跨
用户回调分段；不据此承诺 free-threaded Python 或任意外部 C 扩展绕过 GIL 的写入安全。
新 facade 子类构造仍按既有工厂规则执行；不承诺重写用户构造器/异常协议。

## dtype、Scalar 与广播 / Dtype, Scalars and Broadcasting

这是通用 Python 引用存储，没有持久 ndarray dtype。内置 int/float、Fraction、Decimal、
NumPy scalar 及 Rust 精确值均保持原对象与类型；不会统一转换成 float、调用 item，或因
相邻叶类型不同而推断/提升 dtype。新可变数组写入也不使用旧 ndarray 的 dtype 强制转换。
纯 Rust 数学需显式受检转换，例如 `map(Rational.from_value)` 后调用原生数值操作。

此入口不广播：普通标量不能填充正 rank，长度为 1 的行不能扩展到更长轴。需要同一叶填充
使用 `full`；需要 NumPy 外部数据的显式坐标快照使用 `from_numpy(copy=True)`。不得将这几种
入口互换而声称 dtype、叶身份、存储顺序或共享行为保持不变。

## 公共替换剩余条件 / Remaining Public Cutover Gates

| 旧公共 from_list / Existing public from_list | 私有新入口 / New private factory |
| --- | --- |
| 接受 Sequence，再调用 `np.array(dtype=object).flatten()` | 显式 shape-directed 内置结构，无 NumPy 摄入 |
| 总量/嵌套层级与 shape 不一致仍可能构造成功 | 各轴严格校验，失败返回 Result |
| 平铺结果作为目标物理序列；列布局与输入逻辑行不一致 | 输入永远表达逻辑坐标，Rust 转换存储布局 |
| NumPy 可能继续展开 sequence/ndarray 叶或调用数组协议 | 到叶深度后保持不透明身份 |
| 公开静态方法、位置参数、旧 ABC/双泛型类身份 | 私有 classmethod/keyword-only/单元素泛型 |

旧公共入口目前保持原样。任意 Sequence 的外部协议适配、公共错误签名、旧列布局行为修复、
额外序列叶的明确解释以及类型/子类兼容须在公共原子切换时一起验收，不能把本严格入口
当成所有历史输入的 drop-in replacement。输入边界可以适配外部协议，但最终数组/数学必须
仍由 Rust 执行，不能再经过旧数组算法或静默 fallback。

`tests/native/test_nested_array.py` 覆盖逻辑/物理两布局、结构校验、无 NumPy 路径、opaque
数值/容器/Result 叶、scalar、深 rank、重复边/GC/失败清理、写入隔离、直接 transport 和并发
独立构造。真实 solver 合同将 Fraction 嵌套行和成本受检转换为 Rust Rational，再显式导出
Float64 注册真实 SCIP/Gurobi10 LP；不据此声称所有数值域、领域闭环或公共替换完成。
