# 公共数组映射切换 / Public Array Mapping Cutover

## 接口与边界 / Interface and Boundary

`MultiArray.map(f)`、`flat_map(f)` 与 `MutableMultiArray` 对应方法返回现有三参
`BindingResult[MultiArray[T, S]]`；自然名和单个参数 `f` 不变。成功值始终为基本
不可变 `MultiArray`，不是输入子类。下游自定义 `AbstractMultiArray` 实现也须升级
返回合同；不自动包装用户覆盖的方法。

```python
mapped = source.map(lambda value: value * 2).unwrap()
expanded = source.flat_map(lambda value: (value, value * 2)).unwrap()
```

业务代码应处理 `Ok/Failed`；`unwrap()` 只用于已经验证的示例/断言。无可选 legacy
backend 或静默回退。固定 Rust `Shape<1>::indices()` 驱动物理槽位遍历，原生边界
编排外部读取和 Python 回调；NumPy 保留为输出 dtype/广播/array 协议集成边界。
**这不是任意 Python 回调算术、完整数组存储或 fast_sum 的 Rust 化。**

The four eager public methods have one native traversal path. Lazy view mapping,
block arrays and private snapshot mapping remain separate contracts, not aliases.

## Live 与输出 / Live Reads and Output

- 在首叶之前读取 `size` 并执行整数索引协议一次，固定本次遍历数。非正自定义 size
  生成空 `np.array([])`（float64），不调用回调。rank-zero 按原 size 读取一叶。
- 每槽重新读取当前 `_data`，不预先快照输入、不经过覆盖的 `__iter__`，不按多维
  逻辑坐标重排。正/负/零步长、共享更新、子类属性和整个存储替换对下一槽可见。
  临时存储在叶转换之前释放，保持原下标表达式的析构时机。
- 真正的 NumPy scalar 输入执行 `item()`；不把所有输入转 float。回调输出不额外
  调用 item，也不自动拆包 `Ok/Failed/Fatal`。它们交给 NumPy 按原规则构造输出。
- `map` 在回调之前解析 `np.array` callable；`flat_map` 在完整遍历/扩展之后解析。
  输出转换之后才读取当前 `_shape` 并调用基本 `MultiArray`；输出 `__array__`
  协议也可改变结果 shape。map 临时列表在构造器之前释放；flat_map 列表保活至返回。
- `flat_map` 使用真正内置 `list.extend`，完整消费每个返回 iterable 才读下一输入。
  支持 generator、字符串、list 子类及 length_hint/next 协议；不是只接受 Sequence，
  注解保留历史 Sequence 承诺但不缩窄运行时。扩展失败不发布部分结果，不回滚副作用。
- 结果 ndarray 独立于源存储；object 叶可能继续共享身份。保留 NumPy dtype 推断、
  嵌套/广播及 array-interface 协议，**不承诺所有输出叶都保持 opaque 身份**。
- 历史构造器不校验 shape 与数据尺寸一致；本操作不增加新检查：flat_map 可扩张/收缩，
  map 也可产生嵌套数据，仍保留最终 shape。后续 to_list 等可能因此失败；不能无说明
  改为提前截断、padding、拒绝扩张或自动重塑。尺寸安全升级属于独立合同决策。

## 失败与资源 / Failure and Resources

外部读取、整数/item 协议、回调、extend、NumPy 转换和构造的普通 Exception
成为 `Failed(ExErr)`，`APPLICATION_ERROR / EXTERNAL_MAPPING`，保留**原异常对象
和 traceback，不格式化异常**。`callback_index=None`，不伪造未知内部失败序号。
直接回调的 StopIteration 是普通失败，iterable 的正常 StopIteration 则按 extend 结束。
KeyboardInterrupt/SystemExit/GeneratorExit 原样传播。失败后允许重试。

正 size 超过 usize 在任何叶访问之前返回结构化 `OVERFLOW`；不截断、不用浮点、不回退
Python range。这是显式原生容量升级，不改变公共 Shape 任意精度元数据。flat_map
输出不受初始 shape 长度限制，由 Python list/NumPy 自身容量和外部错误协议约束。

同步持 GIL，周期性检查 signals；外部协议无业务锁，可以重入或释放 GIL 等待另一线程。
不承诺共享写入事务一致性或任意用户协议的取消延迟。无持久原生 owner/cache 或第二份
可变源数据。临时结果列表 O(输出项数)，NumPy 构造可能同时持有列表和 ndarray，与旧
边界同类；安全 append 保证任意重入 GC 只能观察有效列表，不暴露 NULL 槽位。
错误 traceback 可按 Python 语义保留局部变量，这不是原生缓存。

## 验证范围 / Verification Scope

映射读取公共 shape.size。当前源码已在 Windows CPython 3.13 完成独立复验：
两轮 96 组合中的 64 个受门禁组合全部满足原 `1.15x` 门槛；4 个独立资源进程
全部满足 `32 MiB` 峰值增量 / `4 MiB` 预热后增长包络；默认与
`PYTHONMALLOC=debug` + `-X dev` 合同各 **116 passed**。

可执行合同位于 `tests/multiarray/test_public_array_mapping.py`。精确物理量示例和真实
SCIP/Gurobi10 消费者覆盖 live map 后 flat_map 的整数配置优化；类型、默认及隔离安装
回归、完整调用性能/资源、wheel/sdist 验证的实际证据留在被忽略的 logs 追踪文档。
仅按实际证据登记操作/平台验收，Linux/Gurobi11/12、完整领域和长期资源预算不由本切片代替。

当前源码 `scip,gurobi10` wheel 的隔离安装覆盖不可变/可变源、行/列布局、
`map -> flat_map` 链式路径和直接 `flat_map` 路径，均进入同一精确配置 MILP；
映射合同与 solver 消费者合跑 **132 passed / 16 skipped**，Gurobi 11/12 因未编译
跳过，不计为通过。同一 sdist 的仓库外 `--locked` 重建/安装已按当前源码验证。
四条合同仍保持 `specified`，只保留
`fixed-runner-full-domain-and-long-term-resource` 与
`linux-and-gurobi11-12-validation`，不标为完整 `switched`。
