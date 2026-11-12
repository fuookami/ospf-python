# 公共数组逻辑嵌套导出 / Public Logical Nested Export

`MultiArray.to_list()` 与 `MutableMultiArray.to_list()` 的源码候选返回现有
`BindingResult[Any]`。调用方须显式消费 Result；rank-zero 成功值可能是任意叶，不能将
返回值写成仅 `list`，也不能靠 `None` 区分失败。本合同不宣布完整数组权威、性能或发行切换。

```python
import numpy as np
from ospf_python.multiarray import MultiArray, Shape2, StorageOrder

source = MultiArray(Shape2(2, 3, StorageOrder.COLUMN_MAJOR), np.arange(6))
assert source.to_list().unwrap() == [[0, 2, 4], [1, 3, 5]]
```

## 标准路径 / Standard Path

精确内置 ndarray 与精确公开 Shape1/2/3/4/DynShape 走一个原生完整调用：

1. 捕获源缓冲和 reshape callable，再捕获 shape/dims，保留原表达式的求值点。
2. 校验布局、维度整数协议及容量，复用唯一 `dense_shape` 防护并创建固定 Rust DynShape。
   bool、非正维度、超容量及 shape/data 数量不符返回 Failed，不填充、截断或修改输入。
   稀疏超大 raw 元数据不因导出而分配对应缓冲；维度失败后不再消费后续整数协议。
3. NumPy C API 只把实际源存储按 C-order 摄入一维 ndarray。正/负/零 stride、只读、
   非连续、多维及转置缓冲均保留实际 C-order 输入序列。
4. 固定 Rust 的 shape/offsets 决定末轴长度和物理步长，前缀 shape 的 indices 及完整
   shape 的 index_of 决定每个末轴行的物理起点。末轴超过 32 项时，受检计算每行末尾
   位置后，仅把一维物理 slice 交给 NumPy，按原 dtype 的 `tolist` 语义序列化该行。
   末轴不超过 32 项时，物理叶只序列化一次：行主序或两种布局的非 singleton offsets
   一致时直接按轴分组；真正跨步列主序每行只计算一次 `index_of` 起点，连续 stride
   使用 `PyList_GetSlice`，其余使用 C 级列表指针写入。更高轴使用预分配列表和
   `get_slice`，避免逐行 ndarray/dtype 调用。NumPy 不接收目标 shape/轴布局、不计算
   目标索引、不执行 reshape 或数组数学；跨步行的逐叶上游成本仍属于性能待办。
5. 更高轴仅在 Rust 中迭代组装列表；rank-one 直接序列化物理序列，rank-zero 返回
   唯一叶。不调用公共 get/flat_index，不使用 Python 递归；不将任意叶当作结构遍历。

存储切片使用精确 ndarray 的标准安全下标协议，不自行构造带裸数据指针的 ndarray
header、不手工转移 dtype/base 所有权。每个临时一维视图及其 base 均由 Python 引用
保活，结构化记录导出的子数组可正常持有该 base；结果容器不保留源门面缓存。
NumPy 的 rank 限制不施加到逻辑 shape，1024 轴仍由 Rust 的迭代容器组装覆盖。
短行策略的物理叶列表仅是一次导出中的临时序列化产物，不是第二份持久存储权威；
长行不创建该全量临时列表。当前内部批次分界为末轴 32 项，分界两侧必须具有完全相同的
dtype、共享和布局合同；这不是公共 API 或可放宽的性能验收预算。

旧公开实现始终用 C-order reshape，把列存储的物理顺序误当作逻辑行顺序。
标准列布局输出现按坐标修复；不能用旧错误输出作为正确性 oracle 或降低修复后的预算。
正确性参考须显式指定布局，性能同时保留真正旧 Shape/数组基线及坐标正确的参考路径。

## Dtype、所有权与错误 / Dtype, Ownership and Errors

- 采用 NumPy 的**导出序列化**语义，不采用公共 get 的 scalar.item 语义。
  数值 dtype 转成其标准 Python 值；object dtype 内的 NumPy scalar、ndarray、Result、
  Fraction、物理量和普通对象保持原始叶身份，不执行任意 item/iter/array 协议或 Result 拆包。
- structured/void/subarray、字符串/StringDType、datetime/timedelta、扩展浮点及字节序
  沿用 NumPy dtype 转换。结构化记录中 NumPy 自行返回的子数组仍是该转换协议的一部分，
  不假称所有嵌套 ndarray 都已降为独立 Python 容器。
- 新 Python 列表结构独立，叶不 deepcopy。源字段、输入缓冲、布局和 dtype 不变，
  外部修改仍影响后续调用；一次导出捕获的缓冲/shape 不随 owner 后续重绑定重新解析。
  不保留 owner、结果缓存或第二份持久元素权威，不承诺 NumPy 外部写线程的原子快照。
- 原生验证失败返回既有错误码。shape/storage/dtype 等外部普通异常保留原对象与 traceback，
  不格式化用户异常；BaseException 正常传播。即使外部 tolist 返回 Failed/Ok，也作为叶数据
  放进操作的外层 Ok，不使用私有 callback 解包规则。

## 验证与剩余门槛 / Verification and Remaining Gates

当前源码 `tests/multiarray/test_public_array_nested.py` 默认扩展与
`PYTHONMALLOC=debug` + `-X dev` 均为 **268 passed**。最终源码 release 扩展
SHA-256 为
`4c3b4fccf6c26b23cba43bcd416e8840df95315b597a6364dc0c24d425f1f69b`。
基础 wheel
`6435f8a561f53dc13d6063e311ae544624de80ce48bf38467f0d0912af029d6d`
与同一 sdist 已在仓库外无 solver SDK 环境下以 `--locked` 重建、安装并通过发行
smoke，wheel 内扩展与上述默认哈希一致。
最终 `scip,gurobi10` wheel
`ceea0cfde4bff0a86100da3cfb7a1b5999634435496193e75409b5a105688ac9`
的隔离站点扩展 SHA-256 为
`e4a45332169cdbf694c764331968e76e37a49d361767b5c6104521b42716573c`；
合跑公共嵌套合同与 `test_public_nested_solver.py` 为
**284 passed / 16 skipped**：公共嵌套合同 **268 passed**；真实消费者中
SCIP/Gurobi10 各覆盖两类数组、两种布局及 Fraction/Quantity 叶，共 **16 passed**，
Gurobi11/12 未编译跳过。runner 在导入后和测试后均断言所有 `ospf_python` 模块及
扩展来自 wheel 站点，并校验站内源码和扩展哈希。同源 sdist
`61b878e23a8b10134d7042e504c8d384e184b605138afedbe673c62c6b4866a9`
已在仓库外以两个后端和 `--locked` 重建、安装并通过发行 smoke；首次只声明 `scip`
的验证参数与双后端集合不符，失败日志保留，未计为通过。

完整调用性能仍为红：最终轮转测量中长行 **13/48** 失败、形状分布 **102/192** 失败，
其中包含 10k 方阵、多短行、单列及尾轴 singleton；正确参考最大 `3.72762805444706x`。
资源包络 **32/32 passed**，预热后增长 `0 B`，最大峰值增量 `4,194,304 B`，但固定
runner、全领域和长期资源仍未验收。没有放宽 `1.15x` 门槛，也没有选择性删除失败
形状。因此两条合同只删除已完成的发行与真实消费者项，仅保留
`complete-call-performance-and-resource`，状态继续为 `specified`。

## 扩展与状态 / Extensions and State

ndarray 子类、自定义 shape（包括内置 shape 的子类）及自定义 storage 保留捕获的
`reshape(dims).tolist()` 外部协议，保持 callable 求值次序、参数身份及回调的重入/副作用。
不擅自推断它们的自定义布局。标准列布局修复不强加给这些外部 hook；原生编排外部协议
不等于其算法已由 Rust 接管，也不是默认内核失败后回退旧实现。

公共类身份、双泛型、`_shape/_data` 旧字段、copy/pickle 和子类状态不改变。
恢复的字段直接使用同一个导出路径，不重新调用构造器或私有快照工厂。
完整共享状态与 AS-001 仍按 [public-array-state-contract.md](public-array-state-contract.md)
独立验收；本操作不修复 ndarray object GC 或 deepcopy memo 的缺口。

测试覆盖默认原生委托、两类/两布局、多维/stride/dtype/标量、错误及外部扩展，
真实后端合同将 Fraction/单位化系数的逻辑行经严格精度转换后注册 LP。
示例见 `examples/array_nested_example.py`。完整调用/资源与发行验证是独立门槛，
不以此成员的源码替换删除尚未接管的存储、get/set/view 或其他 NumPy 数学消费者。
完整调用基准同时覆盖长行、方阵、多短行、单列、向量、多轴和末轴 singleton，不能仅以
两条长行的局部加速宣称整个操作通过，也不能降低既定中大规模预算。
