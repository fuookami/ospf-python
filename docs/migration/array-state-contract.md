# 引用数组状态与对象图 / Reference Array State and Object Graphs

本合同覆盖私有 `_binding.multiarray` 的 Shape、MultiArray、MutableMultiArray、
两种矩形 view 和 MappedMultiArrayView。它不切换旧公开数组、旧 pickle 路径或 `_shape/_data`
payload，也不把共享 ndarray 转为副本后声称保持原共享合同。

公共模式的独立合同及 object ndarray deepcopy/GC 缺口见
[public-array-state-contract.md](public-array-state-contract.md)。本文件的原生两阶段恢复
不为外部 ndarray 提供 memo 登记或 GC 追踪，不能作为共享模式的间接验收。

## 受检 Python 引用快照 / Checked Python Reference Snapshots

两种存储类提供 `to_snapshot()` 与 classmethod `from_snapshot(payload)`，均返回现有 Result。
DTO 是以下严格字段的内置 dict：

| 字段 / Field | 合同 / Contract |
| --- | --- |
| schema | `ospf.python-reference-array` |
| version | 内置 int `1`；拒绝 bool 和未知版本 |
| kind | `immutable` 或 `mutable`，必须匹配目标工厂 |
| dims | 非负 rank 的整数 tuple，各轴严格为正；空 tuple 表示一个标量 |
| storage_order | `ROW_MAJOR` / `COLUMN_MAJOR`，不依赖 enum 的整数编号 |
| values | 内置 list，按物理存储顺序排列，数量与受检 shape 一致 |

导出通过一次固定上游遍历取得完整槽位快照。DTO 与源后续槽位写入独立，导入创建唯一新 Rust
容器，不保留 values list；叶对象身份和可变状态仍共享。元数据验证和调用编排在 Python，
布局、数量验证与所有权接管仍委托现有 Rust 边界。未知/缺失字段、不支持版本、kind/布局/
形状/数量错误均返回 Failed，不发布部分数组，不执行叶的序列化或数组协议。

这不是 JSON：values 可以包含任意 Python 对象，不能假设可移植到进程外。也不是对象图重定位：
若叶的 owner 指向源，直接 from_snapshot 后仍指向源。对象环、别名的复制/重定位由下述标准
copy/pickle memo 协议负责，不用隐式 deepcopy 或简单替换引用猜测对象关系。

## Copy 与 Pickle / Copy and Pickle

- `copy.copy(facade)` 创建新的门面，保留同一 native handle、叶、视图源和 callback 引用；
  可变数组的两个浅复制门面仍观察同一槽位写入。它不是 to_immutable 的独立槽位快照。
- `copy.deepcopy` 与 pickle protocols 0–5 使用标准 memo：重复叶仅复制一次；leaf.owner
  回边指向恢复后的数组；同一图中多个门面共享的 native handle 在新图中仍共享。
  不调用数组门面构造器或旧 NumPy 内核，也不保留原 Rust 容器。
- Python 门面显式委托 object.__getstate__ 取得字典/所有槽位，而非 frozen dataclass 仅列出
  自身字段的默认状态。恢复保留普通子类的 `__dict__`、额外 slots 和名称改写字段，以及类身份。
  显式 Python 状态钩子也兼容 protocols 0/1 的槽位检查；不直接把内置方法当作该钩子。
- Native Shape 与区域描述只序列化版本化维度、布局、offset 元数据，恢复时重新走严格 shape/
  region 检查。view 的源由 Python 图保存，保持 offset、最终 source identity 和 write-through。
- 惰性映射保存源及原 callback tuple，不执行、缓存或序列化映射结果。顶层可导入函数按标准
  pickle 全局引用恢复；可序列化 callable 对象的源/回边由 memo 保留；局部 lambda/不可序列化
  闭包遵循标准失败，不使用 cloudpickle/dill、代码求值或私下物化来改变语义。

当前永久矩阵已在 Windows CPython 3.13 覆盖 immutable/mutable 两布局、标量/多维、
Shape、两类 view、嵌套 view、mapped callback 图、子类 dict/slots、共享句柄、
重复叶/递归环、protocol 0–5、copy/deepcopy、协议失败和原子恢复。该证据关闭私有
数组 DTO/copy/pickle 门槛，不关闭公共 `_shape/_data` 权威、公共 pickle 路径、
跨平台 wheel/sdist 或完整性能/资源验收。

## 两阶段原生恢复 / Two-Phase Native Restore

Native 数组 reduction 先返回仅含版本/形状元数据的私有构造器和参数，再提供物理顺序元素 list
作为 state。pickle/deepcopy 在处理 state 前登记新句柄，因而元素可回指该句柄或外层门面。
把所有元素放进构造参数会在 memo 登记前递归，不能替代该两阶段协议。

恢复中的句柄没有元素缓冲，读取返回 FAILED_PRECONDITION。state 必须为内置 list，数量严格
匹配；完整构建后一次发布。已发布或经 GC clear 的句柄均不可再借 __setstate__ 初始化，不能
借反序列化修改不可变存储或复活 cleared 对象。clear 终结 pending 标记，解锁后释放引用。
对 pending/ready/cleared 的访问与发布使用同一存储锁，锁内不调用 Python，不释放 GIL。

Python 叶的 reduce/setstate/copy 是标准外部扩展点，不持有源存储锁；异常不改动原源，未完成
句柄不发布部分元素。普通 partially initialized Python facade 仍遵循标准 pickle 规则，叶不得
假设其 owner 的全部字段已经恢复；不承诺在外层 facade 字段恢复前调用其业务方法。

pickle 协议本身不能把 Result 当作“恢复对象”返回。私有 native 构造器/`__setstate__` 的非法
元数据、状态和生命周期错误以标准 ValueError/TypeError 拒绝；用户叶/callback 的协议异常按
标准传播。业务导入使用 from_snapshot 返回 Result，不在其失败分支抛异常。pickle 只能读取
可信来源，不能把本合同或元数据验证当作任意 pickle 字节的安全沙箱。

## 尚未接管的合同 / Remaining Gates

显式旧字段复制入口现见 `legacy-array-bridge.md`。该入口仅导入已经解码且字段齐全的
`_shape/_data` dict；不改变此处原生 copy/pickle 的 memo 图合同，不接管公共恢复。

- 旧公共 `_shape/_data` payload 的恢复与共享 ndarray、dtype/scalar 转换、错误签名仍待原子
  切换适配；不把本私有格式冒充旧 pickle 迁移完成。
- 本合同不为叶对象增加序列化能力。私有 Rational/RationalArray/RationalMultiArray、模型句柄
  和任意外部不可序列化对象仍按各自合同验收；不自动降为 float、字符串或旧 Python 类。
- JSON/跨语言 wire、长期 schema 升级、外部下游子类的自定义 pickle 协议和全面资源预算仍待
  独立验收。标准递归深度限制未被解除，不承诺任意深 Python 对象图可 pickle。

`tests/native/test_array_state.py` 验证全部 pickle protocol、布局/scalar/多维、子类字段、
重复叶与环、浅复制共享句柄、view/source/callback 图、错误状态、原子快照和恢复重入。
公开有效图合同另在 `tests/multiarray/test_array_compatibility.py` 于旧实现执行。
真实 solver 合同将恢复后的 Fraction 区域受检转换为 Rust Rational，再显式导出 Float64
注册 SCIP/Gurobi10 LP；不据此声称所有数值域和公开序列化已替换。
