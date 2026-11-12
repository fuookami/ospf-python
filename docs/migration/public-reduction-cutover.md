# 公共数组归约切换 / Public Array Reduction Cutover

## 接口与权威路径 / Interface and Authority

`MultiArray.reduce(f)` 与 `MutableMultiArray.reduce(f)` 使用同一个原生入口，
不再执行 Python 逐槽归约循环。`AbstractMultiArray` 的返回注解同步为现有三参
`BindingResult[T]`。自然类名、方法名及单个位置/命名参数 `f` 保持；返回值显式升级：

```python
total = source.reduce(lambda left, right: left + right).unwrap()
```

业务代码应消费 `Ok/Failed` 而不是依赖 `unwrap` 抛错。`unwrap` 适用于已验证示例和断言。
自定义 `AbstractMultiArray` 实现也须按此返回合同升级；不会自动包装下游自己覆盖的实现。

The public methods have one default native path and return the existing Result type.
There is no selectable legacy backend, silent fallback or duplicate mutable storage.

固定 `ospf-rust-multiarray::Shape<1>::indices()` 负责遍历物理槽位；绑定只编排逐槽
外部读取和 Python 二元回调。泛型回调本身仍是 Python 扩展点，**不宣称任意用户算术
已经变成 Rust 数值运算**，也不将此操作等同于 `fast_sum` 切换。

## 数值与共享合同 / Numeric and Sharing Contracts

- 按物理次序严格左折叠，不按多维逻辑坐标重排，不使用结合律、交换律、树归约或并行求和。
  非交换运算、浮点舍入顺序和回调次数保持：N 个叶调用 N-1 次；首叶不交回调。
- 与旧实现相同，先读取 `_data[0]` 并转换首叶，再读取 `size` 一次，以整数索引协议固定
  本次访问数量。首叶的 scalar/item 协议可能改变 shape；回调之后改变 shape 不改变次数。
- 每个后续槽位重新读取当前 `_data`，因此别名写入、负/零/正步长、子类属性以及整个
  存储替换在下一槽可见。不先快照全部数据，不缓存 ndarray，不调用覆盖的 `__iter__`。
- 不读取 dims/order/flat_index，不假定自定义 shape 是标准行列布局；两种存储顺序均保持
  原物理归约次序。源数组无需满足新私有稠密数组的构造合同。
- 仅真正继承 `np.generic` 的叶执行 `item()`；扩展浮点、复数、datetime、timedelta、void
  保留其原生 item 结果，不转换为统一 float。普通对象、ndarray、None 保持身份。
- 任意精度整数、Fraction、Decimal、Quantity 及用户对象由原回调决定运算，不新增数值域
  白名单。不隐式换单位，不调用叶的 float/eq/hash/item 等额外协议。
- 回调返回的 `Ok/Failed/Fatal` 同样是数据，不自动拆包或提前终止；最终 `Ok(inner_result)`
  与操作本身失败必须区分。最终 None 为 `Ok(None)`，不是失败哨兵。
- 单叶不检查/调用 f。历史自定义非正 size 仍先读首叶并返回它；真实空/失效存储不能
  虚构加法零元，读取失败按下述错误合同返回。

## 错误、线程与资源 / Errors, Threads and Resources

普通 Exception（包括读取、size/index、scalar 转换、非可调用回调和回调本身的错误）
在薄边界中成为 `Failed(ExErr(...))`，code 为 `APPLICATION_ERROR`，分类为
`EXTERNAL_REDUCTION`，保留原异常对象及 traceback，**不格式化异常**。
不改写异常，不用新 ValueError 代替外部错误；不承诺失败的外部回调副作用可回滚。
callback_index 保持 None，此入口不伪称知道失败的内部回调序号。

KeyboardInterrupt/SystemExit/GeneratorExit 原样传播。特别地，回调直接抛出的
StopIteration 是普通外部失败，不应像 generator 叶错误那样进行 PEP479 转换。
一次失败不会永久毒化源数组，后续调用可以重试。

固定上游索引为 usize：大于原生索引容量的 size 在读首叶/整数协议之后返回结构化
`OVERFLOW`，不截断、不转浮点、不在失败后回退 Python range。这是明确的容量合同
升级；不是删除公共 Shape 任意精度的稀疏元数据能力。

没有业务锁、持久原生 owner、叶数组、后台线程或 cursor。回调及外部协议可重入本操作，
也可释放 GIL 等待另一线程执行独立归约；不承诺跨线程写入原 ndarray 的事务一致性。
同步持 GIL，长遍历周期性检查 signals；不承诺外部回调的固定取消延迟。

绑定额外状态为 O(1) 索引/累加器/当前叶，不保留整批元素。回调可返回任意大对象，
其分配及保活不受绑定资源包络约束。Result 的原 traceback 可能按 Python 正常语义保留
调用栈；这不是持久原生缓存。旧数组本身的 GC、共享所有权和 pickle 合同未在本次更改。

## 验证范围 / Validation Scope

归约读取公共 shape.size。当前源码已在 Windows CPython 3.13 完成独立复验：
两轮 48 组合中的 32 个受门禁组合全部满足原 `1.15x` 门槛，最大比率分别为
`1.039398x` 和 `1.096063x`；4 个独立资源进程全部满足 `16 MiB` 峰值增量 /
`4 MiB` 预热后增长包络，最大峰值增量 `65,536 B`，预热后增长均为 `0 B`；
默认与 `PYTHONMALLOC=debug` + `-X dev` 合同各 **93 passed**。

可执行合同在 `tests/multiarray/test_public_array_reduce.py`；既有公共 reduce 调用测试
同步显式消费 Result。真实求解消费者使用同单位 Quantity[Fraction] 的共享物理流，
经集中精确 Rational/受检 Float64 边界注册原生模型，而不是把 callback 留在 fake solver。
当前扩展已对不可变/可变公共数组和行/列布局完成该真实消费者复验：回调中修改共享
槽位后，后续读取可见；SCIP 与 Gurobi10 均得到预期 MILP 最优解，Gurobi 11/12 因未编译
而跳过。当前源码 `scip,gurobi10` wheel 的隔离安装中，归约合同与真实消费者合跑
**101 passed / 8 skipped**；运行器断言实际导入包位于 wheel 站点，不混入源码树。

两条合同已删除当前源码调用/资源和发行 pending，只保留
`fixed-runner-full-domain-and-long-term-resource` 与
`linux-and-gurobi11-12-validation`，因此继续保持 `specified`，不标为完整
`switched`。三档性能与资源、wheel 和同一 sdist 的隔离验证、静态门禁及实际平台
证据记录于被忽略的 logs 追踪文档，不在本页复制动态统计。只认证有证据的操作/平台
组合，不把这两个默认方法的切换当作公共数组存储、其余数学算法、整个 P3 或领域
迁移完成。
