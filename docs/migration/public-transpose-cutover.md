# 公共数组转置 / Public Array Transpose

`MultiArray.transpose()` 与 `MutableMultiArray.transpose()` 返回现有
`BindingResult[MultiArray[T, DynShape]]`。成功结果始终为独立的基本不可变数组，形状为
动态 shape，不沿用旧的错误 `S` 返回注解；必须消费 Result 后再使用数组。
`reshape/flatten` 的四个公共方法仍是独立迁移项，不因本次转置替换而改变签名。

## 权威实现 / Authoritative Implementation

自然方法只保留薄委托，旧 Python `MultiIndexIterator`、反轴坐标循环及逐坐标 `sum`
已删除。原生 `CoordinatePlan` 使用固定 Rust `DynShape::indices()` 的 C-order 遍历；
反轴目标的精确整数步长若与固定上游行/列布局偏移完全相等，则目标偏移由上游
`DynShape::index_of()` 计算。不是直接调用只支持二维、列布局不等价的
`einsum::transpose`，也不是把需要快照的私有接口直接重导出。

源端每次重新解析当前 `owner._shape.flat_index(*coords)`。不缓存 bound method，
不先采集整批源叶；自定义 shape、后续源 shape 替换与 live 存储写入仍然可见。
非标准、有符号或截短的步长使用 Python 乘法与加法数值协议，保留反射运算、顺序及
`zip(..., strict=False)` 的整数步长扩展行为，不静默转换自定义对象为机器整数。
只有完全相等的精确内置整数才使用上游索引特化，不跳过自定义数值协议。

The native loop orchestrates pinned coordinates and upstream standard-layout indexing.
External shape/index/numeric/storage protocols remain Python extension points; this is
not arbitrary callback arithmetic or a complete native array-storage cutover.

## 时序与存储 / Timing and Storage

- 不可变源：捕获反轴 dims、反轴 strides，再按当前 `size` 与 `_data.dtype` 调用
  `np.empty`；随后捕获迭代 dims 并创建原生计划。不是先复制输入。
- 可变源：先以捕获的 `_shape` 和 `_data.copy()` 构造临时不可变所有者，再执行相同
  原生遍历；copy hooks/ndarray 子类和这一预复制与 live 的区别必须保持。
- 每槽先调用源 `flat_index`，再计算目标索引，随后重新解析 `_data` 并读取原始叶，
  最后执行 NumPy 目标赋值；不是公共 `get`，不隐式 `.item()` 或转 Float64。
- 反轴 dims 与 strides 保持捕获值，完成后才从当前源 `_shape.storage_order` 决定翻转
  布局。原地/替换元数据不提供事务快照；不把后来的 shape dims 重新套进旧采样结果。
- 最后两个外部索引如同原局部变量保活至结果构造之后。原生不持有持久 owner、叶缓存或
  第二份数组；失败 traceback 正常保留边界局部引用，不视为原生缓存。

标准形状反轴并翻转布局后保持完整物理序列，所有对应坐标应满足
`result.get(*reversed(coords)) == source.get(*coords)`（无副作用/并发改变时）。
输入正/负/零 NumPy strides、只读标记、端序、扩展浮点、复数、时间、字符串、结构化
object 字段与不透明 Quantity/Result/None 叶都由原 NumPy dtype/赋值协议保持；输出
不共享输入槽，object 叶仍共享身份。NumPy 赋值自身的转换与广播不因此删除。

任意非标准 shape 的输出仍按其源 strides 指定位置赋值，然后发布标准反轴 shape。
这保留历史自定义存储语义，不宣称不一致的自定义 strides/flat_index、重复覆盖、空洞
或源 shape/data 不匹配都能表示正确的逻辑转置；不能拿未初始化槽位作正确性 oracle。
越界和广播等失败仍由外部协议提供。NumPy 数组的任意底层 rank 不会被静默规范化。

## 失败与资源 / Failure and Resources

普通外部 `Exception` 返回 `APPLICATION_ERROR / EXTERNAL_TRANSPOSE`，保留原异常对象
与 traceback，不格式化异常。直接 `StopIteration` 不进行 PEP479 改写；
`KeyboardInterrupt/SystemExit/GeneratorExit` 原样传播。叶是 Result 时仍为数据。
出错不返回部分结果，但已发生的 copy、索引、读写或用户协议副作用不回滚。

非正迭代维度不访问叶；原公共 `DynShape` 输出构造仍拒绝零/负轴，构造失败进入 Result。
正维度/乘积/索引存储容量超过原生上限返回结构化 `OVERFLOW`，不截断、不回退 Python
坐标引擎。注意输出 NumPy 分配仍先于原生计划：不声称容量检查早于所有分配协议。

所有外部协议均无业务锁，允许线程重入；不保证共享并发写入的原子性。原生循环周期性
检查 signals，不承诺外部阻塞协议的取消时限。除独立输出与可变源预复制外，仅有
O(rank) 原生元数据、每槽临时坐标及最后两个索引；任意用户叶/协议分配不受局部资源
预算保证。完整性能、Windows 双后端消费者和 wheel/sdist 实测以 logs 进度记录为准。
固定 runner、Linux/Gurobi11/12、全领域/长期资源预算均为独立未完成项。

## 验证入口 / Verification Entry Points

转置读取公共 shape.size。当前源码已在 Windows CPython 3.13 完成独立复验：
两轮 48 组合测量中的 32 个受门禁组合全部满足原 `1.15x` 门槛；4 个独立资源进程
全部满足 `24 MiB` 峰值增量 / `4 MiB` 预热后增长包络；默认与
`PYTHONMALLOC=debug` + `-X dev` 合同各 **347 passed**。

`test_transform_compatibility.py` 保存原 rank/dtype/布局/自定义shape/历史不一致合同；
`test_public_array_transpose.py` 覆盖外部协议、失败、尾部索引保活与重入。
`test_public_materialization_solver.py` 经真实转置和 live 物化注册精确单位化配置 MILP；
`test_public_transpose_hot_path.py` 的完整操作基准使用独立物理/坐标 oracle。
`examples/mapped_materialization_example.py` 显式消费两个公共操作的 Result。

当前源码 `scip,gurobi10` wheel 的真实消费者覆盖不可变/可变数组和行/列布局：
转置结果经 live 物化后进入精确单位化配置 MILP，SCIP 与 Gurobi10 共
**8 passed / 8 skipped**；Gurobi 11/12 因未编译跳过，不计为通过。当前源码
发行物与仓库外安装证据已经收敛。两个入口仍保持 `specified`，只保留
`fixed-runner-full-domain-and-long-term-resource` 与
`linux-and-gurobi11-12-validation` 两道未关闭门槛，不标为完整 `switched`。

存储变换补充：reshape/flatten 四方法已有原生 Result 候选，旧候选的性能和发行证据
不能认证新的 shape.size 实现；当前操作门槛与其他平台、长期资源仍待验收，详见
`storage-transform-contract.md`。
