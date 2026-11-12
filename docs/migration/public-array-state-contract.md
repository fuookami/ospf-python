# 公共数组的权威状态与恢复 / Public Array Authority and Restoration

本合同覆盖公共 `MultiArray[T,S]`、`MutableMultiArray[T,S]`、普通/惰性 view，以及它们
与 shape、外部 ndarray 和叶对象组成的完整对象图。它规定完整存储替换的边界，
不是新增私有入口或将旧类重导出为单泛型私有类的授权。公开类目前仍未接管为 Rust 权威存储。
私有 Rust-owned 存储已有的两阶段恢复见 [array-state-contract.md](array-state-contract.md)，
共享边界见 [legacy-array-bridge.md](legacy-array-bridge.md)。

## 单一权威与别名 / Single Authority and Aliases

现有位置构造 `(shape, data)` 保留两个输入对象，不复制、规范化、推断 dtype 或补齐元素。
`_shape` 和 `_data` 的原对象替换也是实际可观察行为，不仅是初始化细节：

- 外部缓冲写入、dtype/rank/容量/writeable 变化，影响所有持有该 ndarray 的门面。
  “不可变”公共类并不使输入缓冲只读；不能据此颁发不可变值证明或缓存其 hash。
- 门面的浅复制初始共享 shape 与缓冲，但不是同一个门面。替换浅复制的 `_shape` 或
  `_data` 只改变该门面，不应反向替换原门面的字段；缓冲原地写入仍影响共享它的各门面。
  不能仅让两门面共享一个可变 native owner，然后把属性赋值写入 owner 来模拟旧行为。
- 普通/惰性 view 持有源门面而非其初始缓冲。源字段替换后，后续读取看到新字段；
  已启动的公共迭代保留原来的迭代数量，但每一步仍解析 live 源存储。
  这不同于一开始捕获 ndarray 的显式 `at_many`，两者不可擅自互换。
- 外部把一维缓冲改为多维或改变 dtype 的 itemsize 后，现有受检 `at/set_at` 拒绝
  rank/数量不匹配，不自动 reshape、复制或修改源。恢复有效元数据后须可再次读取。
  任意精度稀疏 shape 仍可存在于公共字段中，不因重新赋值而分配对应大小的稠密缓冲。
- NumPy 已弃用原地 dtype/shape setter；对应测试仅模拟共享边界可能观察到的外部变化，
  不将这些 setter 推荐为应用接口，也不承诺未来 NumPy 版本继续提供它们。

Rust-owned 模式与共享外部缓冲模式须分别证明各自的唯一权威。暂时的受检快照不等于存储
接管；常驻 `Vec` 与仍允许外部修改的 ndarray 不能同时宣称为同一数组的权威。
也不能缓存叶来补 GC 图、凭正维度信任历史 raw 字段、或只替换属性名而保留 NumPy 数学内核。

## 完整状态图 / Complete State Graphs

有效的旧图不仅包含一个数组，还可同时包含其 shape、原 ndarray、共享该 ndarray 的其他数组、
普通/惰性 view 和有回边的重复叶。需要保留的有效合同包括：

- pickle protocols 0–5 保持精确同一 shape/ndarray 的别名、重复叶与回边、view/source 身份及
  全局 callable 引用。不能逐个恢复数组并各自复制原来共享的缓冲。
- deepcopy 同样须检查图根的访问顺序，而不是仅 deepcopy 数组后比较数值。
  已知失效的缓冲先行情况见 AS-001，不能将其登记为已兼容或将坏行为冻结为目标。
- 仅有 `_shape/_data` 的旧字段对象仍可恢复。copy/pickle 在处理状态前登记新门面，
  不重新执行公共 `__init__`，不隐式转为私有工厂、重新转换 dtype 或拆包 Result 叶。
- 普通下游子类的字典、slots、名称改写 slots 及其叶别名/回边均是图的一部分。
  现有有 slots 且未提供状态钩子的公共子类只在 deepcopy 和 pickle 2–5 下有有效基线；
  原类在协议 0/1 的限制不是迁移完成证明，若扩展支持须另作显式升级验收。
- ndarray views 的内存重叠与同一 ndarray 对象的身份不是一个合同。
  本合同测试前者时必须单独指定，不可用“数值相等”或后者的 memo 通过替代。

标准 pickle 不是 Result 业务 API，恢复过程遵循 Python 协议和可信输入限制。
完整原生恢复还须验证 pending/ready/cleared 生命周期、失败不发布部分状态、子类钩子、
BaseException 及叶恢复的重入；不能以 Python 字段基线代替这些 Rust 生命周期验收。

公开类的布局选择还受旧分配器约束：现有字段恢复会使用 `object.__new__(cls)`，旧
protocol-0 对象 payload 会使用 `copyreg._reconstructor(cls, object, None)`。
隔离 PyO3 布局实验证明，直接加一个支持 subclass/dict/weakref 的原生基类也会让这两个
入口报 TypeError；只增加 `__setstate__` 或验证新格式不能证明兼容。完整设计必须先解决
旧分配阶段，不得以绕过构造器的恢复测试“不适用于新类”为由删除断言。
该风险独立于 AS-001，不能用修复其中一个来认证另一个。

A native-layout base is not a transparent ownership migration: the existing object
allocator and old object reconstructor reject it before state restoration. New-format
round trips or a new state hook alone do not establish old-format compatibility.
Allocator compatibility and AS-001 remain separate acceptance obligations.

## AS-001：缓冲先行的 object deepcopy 会拆散共享别名

状态：公开共享存储的已复现缺口，未修复；不表示固定 OSPF Rust 的缺陷。

最小对象图是一个 object ndarray，两个对象的 `_data` 同时指向它，叶的 owner/peer 回指
这两个对象，叶在缓冲中重复出现。对 `[data, first, second, leaf]` 执行 deepcopy 后，
重复叶和回边可以正确，但三个应共享的 ndarray 引用不再全同一对象。
相同图换成叶先行，或使用标准 pickle，能保留这些精确别名。
纯 NumPy 加普通 Python holder 即可重现，无需导入 OSPF/PyO3。

NumPy object ndarray 的 deepcopy 在递归处理叶时尚未把当前缓冲登记到 memo；叶回到持有者
后再次复制同一原始缓冲，可能产生第二份副本。共享对象 GC 的既有问题也不能由简单保活
ndarray 解决：ndarray -> leaf 的边未被标准 GC 追踪。纯 NumPy/公共数组的循环叶会被保留，
显式断开缓冲中的叶后才释放；私有原生逐槽存储的对照不能认证公共共享模式。

`test_public_array_authority.py` 保留缓冲先行 deepcopy 的期望别名断言，以严格 xfail
标出此缺口。它们必须继续运行；unexpected pass 会失败并要求审查、移除标记。
这些 xfail 是**未完成验收项**，不是允许最终完成时保留的绿灯，不得通过跳过模式、改为
断言拆散后的身份或只测数组先行来掩盖缺口。完整接管必须消除失败，或经明确的公共所有权/
兼容决策定义可接受政策并迁移调用方；本合同没有授权放弃共享、全局 monkeypatch
`copy`/NumPy、替换上游 checkout 或升级固定 Rust revision。

## 原子切换门槛 / Atomic Cutover Gates

完整公共状态接管须同时覆盖构造/工厂、get/set/方括号、shape/data 属性、live/快照遍历、
两类 view、所有变换与数学消费者、比较/hash/repr，以及旧字段/新状态图恢复。
允许按工作包准备和验证，但不能把某一个入口通过记成整类 switched：

1. 明确 Rust-owned、外部共享与自定义 shape/storage 扩展的权威及状态转换；不得静默复制。
2. 接通所有默认消费者并删除已接管的 Python/NumPy 索引、布局与数学内核，而非增加无人调用的旁路。
3. 统一 Result 业务边界与 Python 协议边界，保留外部原异常，不用构造成功证明后续字段仍规范。
4. 验证整个状态图和两种根访问次序，处理 AS-001 与共享 object GC，不虚构不可见引用边。
5. 按真正旧 Shape/数组基线做完整性能/资源与领域验证，随后完成发行安装矩阵及清理。

基线由 `tests/multiarray/test_public_array_authority.py` 与既有兼容/访问/迭代测试共同维护。
这些测试不授予公共数组切换资格，不放宽性能预算，也不替代平台、solver、任意数值域或
外部下游协议的独立验收。
