# 公共惰性映射物化 / Public Lazy Mapping Materialization

公共稠密 `shape.strides()` 和标准 `flat_index()` 变更后，本操作已按原范围重新完成
Windows CPython 3.13 操作级验收，api-map 登记为 `switched`。这不表示完整 view、
共享存储、Linux/Gurobi11/12 或固定 runner/长期资源门槛已经完成。
/ After the dense shape-stride and standard `flat_index()` changes, this operation
has been revalidated at operation scope on Windows CPython 3.13 and is registered as
`switched`; full view/storage, Linux/Gurobi11/12 and fixed-runner/long-term gates remain separate.

`MappedMultiArrayView.materialize()` 的自然入口返回现有
`BindingResult[MultiArray[Any, Any]]`。用户需消费 `Ok/Failed` 后使用数组；成功值仍为
基本不可变 `MultiArray`，不是视图子类。lazy 创建和 `get()` 的签名/行为不变：get
仍逐次执行 Python 回调并直接遵循索引协议异常，不拆包用户返回的 Result。

## 权威路径 / Authoritative Path

旧 Python `MultiIndexIterator`/append 循环由固定 Rust `DynShape::indices()` 替换。
先捕获 `self._source.shape` 对象及其 dims，一次原生遍历按逻辑 C-order 逐坐标重新解析
当前 `self.get`。覆盖方法、重入、源存储替换和共享写入对后续坐标可见；不预先快照源叶，
不缓存用户 get，不建立持久原生 owner。结果保持捕获的 shape 对象身份，不自动跟随后来
替换的源 shape；在一次操作中原地篡改 shape 元数据不属于事务一致性承诺。

Native traversal orchestrates live Python get/callback extensions. Arbitrary callback
arithmetic is not a Rust numeric kernel, and this is not a full view/storage cutover.

全部回调结果先按原 C-order 交给 `np.array(values)`：保留 dtype 推断、广播、嵌套数组、
`__array__` 等输出协议及其执行次序。不能先把叶按物理次序重排再探测它们。普通 object、
None、Quantity 和回调 Result 是数据，不额外 item/float、不拆包 Result、不隐式换单位；
NumPy 自己仍可能转换输出，不承诺任意输出协议都保持叶身份。

NumPy 转换后，内置标准 shape 的物理排列由固定 Rust `MultiArrayBuilder` 按目标布局
生成，边界只用 `np.take(..., axis=0)` 发布各逻辑槽的第一轴顺序。行布局/恒等排列不额外
gather。多维输出叶保留 NumPy 形成的附加轴；不把它们错误地展平为标量槽。

这修复 **TF-001**：旧代码总把 C-order 值列表放进原 shape，在列布局下坐标错位。
例如行布局源转置后变为列布局，lazy mapped view 物化必须对每个坐标保持
`result.get(*coord) == mapped.get(*coord)`（无并发/副作用变化时），而非仅保持数据集合。
`to_list` 自身旧列布局缺陷不在本操作中修复，不能用它验证逻辑坐标。

## 自定义形状与容量 / Custom Shapes and Capacity

自定义 shape/子类不是自动当作标准布局：NumPy 转换后调用其 `flat_index(*coord)`，
原生验证所有目标位置构成稠密双射。支持整数索引协议和 NumPy 风格的一次负索引归一化。
重复、越界或非稠密目标返回结构化失败；不发布有空洞/覆盖的部分数组。自定义布局函数
属于 Python 扩展点，不声称其公式已经迁入 Rust。布局阶段的额外函数调用是修复输出
坐标合同的显式升级，不回滚已经执行的 get/回调/NumPy 副作用。

非正维度与旧坐标迭代器一致，得到空输出（默认 float64），不调用 get/布局函数；
rank-zero 则采样一次空坐标。正维度/乘积/布局索引存储字节超过原生容量时，在叶采样前
返回 `OVERFLOW`，不截断、不回退 Python odometer。公共稀疏 Shape 的任意精度元数据
能力不因此删除。失败传输沿用现有 Result/ExErr，而非另建异常或结果体系。

## 错误与资源 / Failure and Resources

普通外部 Exception（shape/dims/get/item/回调/NumPy/自定义 indexer/构造）返回
`APPLICATION_ERROR / EXTERNAL_MATERIALIZATION`，保留原异常对象与 traceback，
不格式化异常、不自动进行 PEP479 转换。KeyboardInterrupt/SystemExit/GeneratorExit
原样传播。结构化容量/布局失败保留原生分类；callback_index 保持 None，不伪造序号。

所有用户协议均无业务锁，可重入、释放 GIL 等待另一线程；不保证共享写入的并发原子性。
长原生遍历周期性检查 signals，不承诺任意外部回调的取消延迟。采样列表与 NumPy 输出
可同时存在；列/自定义布局另有 O(N) ordinal/permutation 临时存储及 gather 输出。未使用
未初始化 PyList 槽位，不保留原生 source/leaf/cache。失败 traceback 正常保留局部变量，
不等于原生缓存泄漏。任意用户输出/回调分配不受本地资源包络保证。

## 未切换范围 / Separate Gates

- 普通 `MultiArrayView.materialize()` 已有受检剩余区域存储复制的原生 Result 候选，
  完整操作门槛尚未验收，见 `public-view-materialization.md`；它不是本 live 采样合同。
- 公开 view 的范围、构造、直接 get、pickle/GC 图和完整共享存储替换仍独立待验收。
- 两个公共 transpose 已接通原生 live/预复制编排及上游标准布局索引，并返回现有 Result，
  见 `public-transpose-cutover.md`；reshape/flatten 四方法仍未切换。
- 固定 einsum::transpose 限于二维且使用行偏移，不能代替任意 rank/列布局公共转置；
  Rust reshape 会截断/补值，不能代替公共数量匹配/物理重解释合同。

可执行合同见 `test_public_mapped_materialization.py` 与 `test_transform_compatibility.py`；
真实单位化配置 MILP、完整调用性能/资源、默认/无SDK回归、wheel/sdist 和平台实测证据
记录在被忽略的 logs 追踪文档。仅按实际证据登记，不把本操作当作 P3、全平台、完整领域
或长期资源预算完成。

当前源码复核使用固定 Rust revision，扩展 SHA-256 为
`347e90037bc0685a2900cc9b771f58fb8d8786362ddd616c72bda17cc201519e`：

- 48 项 benchmark oracle 通过；32 个中/大档性能门控全部保持原 `1.15` 门槛，
  原始旧路径比值最大 `1.00951`，正确参考比值最大 `0.99395`。
- 独立旧/新资源子进程均通过 `48 MiB` 峰值增量、`8 MiB` 预热后增长包络；
  新路径峰值 `10,997,760 B`、增长 `4,096 B`，旧路径峰值 `5,791,744 B`、增长 `0 B`。
- 默认扩展上定向合同 `405 passed / 16 skipped`；编译 `scip,gurobi10` 后为
  `413 passed / 8 skipped`，通过的 8 项是两类存储 × 两种布局 × 两个真实后端的
  单位化配置 MILP。Gurobi11/12 未编译，不计为通过。
- base/dual wheel 与同一个 locked sdist 均完成仓库外安装、重建和重装验证。

存储变换补充：reshape/flatten 四方法已有原生 Result 候选，旧候选的性能和发行证据
不能认证新的 shape.size 实现；当前操作门槛与其他平台、长期资源仍待验收，详见
`storage-transform-contract.md`。
