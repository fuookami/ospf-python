# 公共默认迭代切换 / Public Default Iteration Cutover

后续公共 reduce 的独立 Result/live 归约升级见 `public-reduction-cutover.md`。
本文的迭代协议验收不自动覆盖该操作或其余数组算法。

## 切换范围 / Scope

公共 `MultiArray.__iter__` 和 `MutableMultiArray.__iter__` 移除各自的 Python
`range(size)`/逐槽索引循环，统一委托 PyO3 `SharedArrayIterator`。公共类、导入身份、双泛型、
ABC、构造/旧字段/pickle、ndarray 共享保持不变。没有 backend 选择或失败后旧循环 fallback。

这是**迭代协议能力**的切换，不是完整数组存储/数学内核切换。源当前仍以共享 ndarray 为
唯一权威存储；原生边界通过 Python 的外部存储索引协议读取，不调用 NumPy 数学算法、旧
array.get/flat_index、也不把 ndarray 复制成 Rust Vec 或缓存叶。固定 ospf-rust revision
不变；原生 Rust-owned 数组的显式 iter_live 仍使用固定上游，二者不隐式互转。

This replaces the public Python traversal loop with a native shared-storage protocol adapter.
It does not claim that the public ndarray storage or remaining Python mathematical kernels
have become ospf-rust arrays. No second mutable authority or silent legacy fallback is added.

## 保留的 Generator 合同 / Preserved Generator Contract

- `iter(array)` 仍返回 Python generator。创建时不读取 size/数据，不取得叶快照；首次
  next 才按 `operator.index(size)` 确定计数，之后 size 变化不改变该次迭代的范围。
  子类的 size 协议保留；负数同原 range 一样为空。原生计数是机器 usize；真正可寻址的
  一维 ndarray 不会超限，不承诺继续容忍超机器计数与短数据不一致的非法稠密状态。
- 默认按一维物理槽位顺序，不将 column storage 重新解释为 row-coordinate 访问。
  每次消费重新读取当前 owner._data 和当前槽位；外部写入、正/负步长、只读缓冲和源替换
  可见。开始后不保存 ndarray 指针/借用，也不缓存旧缓冲或已读叶。
- `next/for/list`、`send(None)`、开始后 `send(value)`（忽略发送值并继续）、`throw`、
  `close` 仍按 generator 工作。未开始时 send 非 None 由 Python generator 自身拒绝。
  不保证旧 bytecode/gi_code 或 gi_yieldfrom 的内部对象身份；后者现在是原生游标。
- 最后一次 yield 后仍保活公共源及子类状态，直到额外 next 确认耗尽、close、throw 或
  放弃 generator。与私有 iter_live 最后一个叶返回即释放源的合同不同，不混淆两者。
- ndarray 缩小/失效、外部索引/NumPy scalar 转换错误经标准 next 协议传播，并终结
  generator；之后不会恢复、重读或静默 fallback。普通异常和 BaseException 身份保留。
  叶/存储抛出 StopIteration 须按 PEP 479 转 RuntimeError 并以原异常为 cause，不能被
  yield-from 吞成正常耗尽。
- generator 本身仍不可 pickle/deepcopy。原生游标全部 pickle 协议显式拒绝，不产生
  丢失 owner/position 的空 payload。

## Scalar 修正 / Scalar Correction

旧 helper 对任意 `hasattr(value, "item")` 对象调用 item，这会执行普通领域对象的方法，
也会对作为 object 叶保存的 ndarray 意外降维或抛错。现在仅对象真实类型继承 np.generic
时执行 NumPy scalar 的 item；普通对象、ndarray、None、Result 都是数据，保持身份。
不通过可伪造的对象 __class__ 判断类型，不执行其 __class__ 属性。

该修正作用于现有 get/map/flat_map/reduce 共用的 `_to_python_scalar` 边界，以及原生公共
迭代的相同类型政策；没有因此迁移这些方法的其他旧数组算法。数值/字符串/datetime/
timedelta/void/longdouble 等真正 NumPy scalar 保留其原 item 输出，不强转 float。
NumPy scalar 子类有意覆盖 item 的协议仍执行，错误/副作用仍由该扩展负责。

依赖普通对象 item 隐式执行的调用方须显式转换，例如 `array.map(lambda value: value.item())`；
不要依靠存储读取执行任意业务方法。新的私有 Rust 引用数组依旧保持 NumPy scalar 本身的
身份，不把本公共转换政策移植到私有 opaque-leaf 存储。

## 并发、GC 与资源 / Concurrency, GC and Resources

原生游标只有一个位置与忙标志；外部 `_data` 属性、索引和 scalar.item 可能执行 Python
或释放 GIL，必须在所有游标锁之外运行。重入或重叠直接消费原生游标返回 ValueError busy，
不提前推进、不死锁；公共 generator 自身还保留 Python 的 executing 防护。
不声称用户 ndarray/回调可无同步跨外部线程写入，也不把多次读取视为事务。

仅持 owner、NumPy scalar 类型及 O(1) 游标状态，无叶缓存、持久原生存储借用或新增线程。
GC 按实际两条强引用遍历，先终结/解锁后 decref；直接 owner/generator 环可回收。
测试包含析构重入及等待另一线程消费、1,000 个源的耗尽/关闭/放弃无残留实例。
这不修复旧 ndarray(object) -> leaf -> owner 非 GC 边的已知环，也不构成完整共享 object
存储/长期原生资源预算通过；该门槛仍见 `legacy-array-bridge.md`。

## 验证与剩余范围 / Verification and Remaining Scope

迭代首次消费时读取公共 shape.size。2026-10-31 当前源码复验在 Windows
CPython 3.13 上登记两个入口为局部 `switched`。原始“先 legacy 后 public”的
ratio-of-medians 两轮中，第一轮 `10000` numeric 行/列布局出现 2/16 个
`1.165x`、`1.169x` 漂移失败，第二轮通过；该失败样本没有删除或改写。
随后执行两轮 ABBA/BAAB 交错完整调用复验，保持原三档输入、oracle 和
`1.15x` 门槛不变，连续两轮 32/32 通过，最大比率分别为 `1.107915x` 和
`1.101447x`。

16 个独立资源进程全部满足 `24 MiB / 4 MiB` 包络；native 最大峰值增量
`774144 B`、预热后增长 `0 B`。默认与调试分配器合同各 78 passed；隔离基础/
求解器站点各 78 passed 且工作区模块泄漏为空；隔离求解器 wheel 的真实
SCIP/Gurobi10 消费者为 8 passed / 8 skipped，跳过项仅为未编译的 Gurobi
11/12。当前源码基础/求解器 wheel 与同一 sdist 已完成仓库外验证和 locked
重建。固定 runner、全领域、长期资源、Linux 和 Gurobi 11/12 仍未认证；本机
局部切换不外推为完整数组内核或跨平台完成。

`tests/multiarray/test_public_array_iteration.py` 直接验证公共入口实际委托原生类，覆盖两类、
两布局、strided/live/replacement、lazy count、scalar/opaque/Result/ndarray 叶、NumPy scalar
子类、send/throw/close、异常/PEP479、生命周期、GC、并发及全 pickle protocol。
真实 SCIP/Gurobi10 合同从公共物理 live 流建立显式 Rust 快照，后续 RHS 写入须可见，
再以 Rational/受检 Float64 转换注册 LP；不能用初始数据快照或 fake 代替。
当前扩展已对不可变/可变公共数组和行/列布局完成该真实消费者复验，SCIP 与 Gurobi10
均得到预期最优解；Gurobi 11/12 因未编译而跳过。当前源码的性能、资源和发行门禁
已完成，两个入口因此删除
`current-source-complete-call-and-resource-revalidation` 与
`current-source-distribution-revalidation`。上述固定 runner、全领域、长期
资源、Linux 与 Gurobi 11/12 限制保留在合同说明中，但不阻止 Windows
CPython 3.13 局部操作范围登记 `switched`。

首版逐叶 Python 转换回调方案有明显局部性能回归，未作为验收版；改为原生 scalar 类型
边界与 intern 属性名后，两轮三档 physical sum 测量单独记录，包含游标创建/消费，不含源
创建。小输入固定成本不外推到整体；局部结果不证明固定 runner、完整领域或长期资源
预算通过。
实际回归、发行、静态检查与性能证据只在 logs 总进度记录，不在本文件复制动态统计。

公共共享 storage 的完整原生接管、get/set 的受检 Result、相等/hash/repr、view 范围、
数学消费者、单位/数值泛型、旧 pickle 自动图恢复及整体 P3 仍待独立验收。
