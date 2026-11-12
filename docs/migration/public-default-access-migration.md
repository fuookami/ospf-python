# 公共默认访问迁移边界 / Public Default Access Migration Boundary

状态：**方案，协议政策待确认；尚未切换默认 get/set/方括号**。
固定上游 revision 为 `119854756a0aeb66d2998055f96fa7175c7bfb37`。
本文件不是第二份进度表，也不放宽 api-map 中任何验收条件。
受检旁路见 [public-array-access.md](public-array-access.md)，完整状态约束见
[public-array-state-contract.md](public-array-state-contract.md)。

Status: proposed, protocol policy pending. This document neither implements nor
certifies the default access cutover. Checked side APIs do not prove that the public
array, its consumers, or storage ownership have migrated.

## 当前真实路径 / Current Paths

| 生产入口 / Entry | 当前行为 / Current behavior | 原子迁移影响 / Atomic impact |
| --- | --- | --- |
| `AbstractMultiArray.get` | 返回元素 `T` 的抽象合同 | 返回类型、第三方实现及调用方同时审查 |
| 两数组的 `get` | 当前 `_shape.flat_index`，随后当前 `_data[key]`，仅真实 NumPy scalar 转换 | 不能把严格 `at` 机械别名到此处 |
| 两数组的 `__getitem__` | 将整数包为 tuple，再动态调用 `self.get` | Result 升级会泄漏外层包装；读取覆盖须有明确来源 |
| `MutableMultiArray.set` | 尾参数为值，定位后写当前缓冲 | 新业务接口统一 Result、明确 keyword-only 参数 |
| `MutableMultiArray.__setitem__` | 直接定位及写入，不调用 `self.set` | Python 赋值丢弃返回值；不能静默返回 Failed |
| `MultiArrayView.get` | 偏移加法，再动态调用源 `get` | 源的业务包装不能作为映射输入 |
| `MappedMultiArrayView.get` | 动态调用源 `get`，然后回调 | 回调返回的 Result 是合法数据，不是访问失败 |
| 原生 `CoordinatePlan.sample` | 每坐标动态查找 `owner.get`，返回对象加入临时 list | 必须与 view 协议同步升级，不能仅改 Python 消费者 |

`Vector` 是公共数组别名，不是独立读取实现。稀疏 `BlockMultiArray` 的字典和任意精度
索引合同须另行迁移；同名私有 `_binding.MultiArray` 不属于此公共类。
`DataFrame.get`、普通字典 `get` 和几何 `Vector2/Vector3` 不能按名字批量替换。

已审查的 `fast_sum`、`multi_array_extensions`、`einsum` 和 `einsum.operations` 直接
读取 `_data` 并按 `shape.dims` reshape。它们不会因命名 getter 升级自动迁移，也不能
因未调用 `get` 被排除在完整数组替换之外：布局、精确数值、权威存储及 NumPy 数学
内核仍是各自的迁移义务。默认迭代、reduce、eager map、to_list、transpose 及普通
view 物化也有直接存储路径，不能把新 getter 作为它们已被接管的证据。

静态 AST 搜索只能提供候选边，不能证明所有动态分派。动态属性、下游子类、重新导出、
duck source 和原生 `getattr` 均须结合实际源码与运行合同审查。

The native coordinate sampler is a real default consumer. Direct storage consumers
remain in the ownership and numeric migration scope even without calling `get`.

## 阻止机械替换的两个反例 / Two Counterexamples

### 方括号赋值无法交付 Result / Assignment Cannot Deliver a Result

`array[index] = value` 丢弃 `__setitem__` 返回值。直接调用 dunder 可以取得 Failed，
不表示赋值语法也能取得它。返回 Failed 而不写入会使普通赋值在调用方看来成功。
禁止增加 `last_error`、告警、全局状态或延迟抛错来伪造错误交付。

`.rules/error-handling.md` 要求业务操作使用 Result，列出的协议例外未明确包含索引。
因此本方案**建议但尚未获准**：命名 `get/set` 返回现有 Result；方括号保持 Python
协议，读取返回原始元素，写入成功返回 None，索引/类型错误遵循明确的
IndexError/TypeError 映射，外部协议异常保持原对象及 traceback。
这需要明确的索引协议例外，不能通过修改测试、泛化 iterator 例外或擅改规则获得授权。
如不接受例外，必须明确调整或退出赋值语法并迁移调用方；静默失败不是选项。

No indexing exception policy is authorized here. This requires a deliberate decision:
the setter's Result is discarded by the language, not by a wrapper.

### Result 元素不等于访问失败 / A Result Leaf Is Not Access Transport

raw getter 可以合法返回 `Ok(payload)`、`Failed(error)`、`Fatal(errors)` 或
`Warn(payload, warning)` 作为元素。映射回调也可以返回这些对象。
未来成功读取 Failed 元素时，业务结果应为 `Ok(the_same_failed_leaf)`，而不是访问
失败；消费者只处理操作的外层，不递归解包叶。

只把 `get` 改为 `at` 的包装会使方括号和 mapped callback 收到外层 Ok，Rust sampler
把外层 Ok 当元素存储。按 `isinstance(value, Result)` 猜测并解包又会吞掉合法叶。
两者都不是兼容的原子切换。

Transport requires explicitly identified producer provenance. It cannot be inferred
from the returned object's type, method name, or the owner's class alone.

## 拟采用的操作边界 / Proposed Operation Boundary

1. 命名读取/写入复用 Result、ErrorCode、ExErr 和 FailureContext，禁止另造 Result
   或用 unwrap 抛业务失败。新签名符合 keyword-only 规则；旧位置参数支持和退出窗口
   显式记录，不能默默把末参数或零维坐标改作他义。
2. 严格坐标、历史整数协议、负索引、rank 及任意精度逐项对照有效基线。不能沿用
   `at` 拒绝 bool/NumPy 整数等政策而不声明升级，也不能冻结越界 alias 等历史缺陷。
   原生失败不再调用旧 Python 数学实现 fallback。
3. 标准 Shape 索引交固定上游 Rust；自定义 `flat_index` 是外部扩展协议，不得在
   未获显式 standard-layout 确认时按 dims/order 重解释。`at` 要求真正一维且大小
   匹配的 ndarray；旧 getter 接受的其他 raw storage/非平坦协议需单独分类和政策。
4. 每次操作重新观察权威字段，保留实际方法/描述符查找和 scalar 转换。只允许本次
   调用内受检元数据；不得缓存 owner、叶、shape hash 或历史字段证明。外部 ndarray
   仍权威时不得增加常驻 Rust Vec 镜像；完整所有权转换另须验收。
5. 不缓存读取方法，不按类推断 override 协议；getter 可在回调中被替换。先设计明确的
   生产者来源/adapter，说明继承、instance override、描述符和 duck source 的 opt-in
   规则。未标记 raw override 返回的 Result 不能当传输。本文件未选定标记、adapter
   或 native ABI 实现，不能将尚未验证的方案当成最终合同。
6. 方括号读取当前动态分派到 raw getter；写入当前不分派到命名 setter。这是有效的
   扩展行为，不应因共用 helper 悄悄改变。若需升级分派，另有兼容决策和测试。
7. 普通外部 Exception 保留原对象及既有 traceback 后转业务失败，不格式化。
   BaseException 原样传播。首错后不再读取后续 getter 或执行回调，不发布部分输出。
   用户副作用、复杂 dtype 部分写入和并发字段更换不承诺回滚或快照事务。

These are design obligations, not implementation claims. Signatures, producer
provenance and compatibility adapters require review before the default cutover.

## 同一切换事务的范围 / Atomic Cutover Scope

切换覆盖抽象类型、两公共数组、两类 view、原生 sampler、注解/导出、实际访问消费者
及示例。业务失败不能流入 callback；raw Result 叶不能被当成失败。不能以单一 getter
通过将整个数组或 P3 标为 switched。

实施前应有标准/自定义 shape、live 共享及 strided 缓冲、旧字段恢复、子类与 instance
override、描述符失败、重入、原异常/traceback、BaseException、Result 叶及首错停止
矩阵。同步明确方括号异常映射、参数协议及新旧调用方升级示例。
实施后运行完整 `tests examples` 并比较原身份/结果，审查真实 SCIP/Gurobi 消费者及
完整自然入口性能/资源，完成相应 wheel/sdist 仓库外安装验证，才删除已接管旧内核。
不删除仍需保留的外部扩展回调，也不在 switched 项保留生产 Python fallback。

完整 Shape/数组状态、旧分配器、AS-001、共享 object GC、普通 view 性能缺口、其他
变换/数学及平台/solver 版本义务均保留。固定 Rust 的 Gurobi 支持仍是 10/11/12；
本机的 10 不能认证 11/12 或 Linux。

## 长期分派合同 / Durable Dispatch Contracts

`tests/multiarray/test_public_access_dispatch.py` 保护显式 raw 扩展的 Result 叶身份、
方括号动态 getter、命名 setter 与方括号写入的不同路径、逐坐标描述符查找及首错停止。
描述符普通失败通过既有 materialize 业务边界发布，控制异常按原对象传播。
这些测试不冻结默认方法的异常/返回策略，不授权新协议例外，也不是原生所有权或完整
默认访问迁移验收。与现有访问、数组状态及 mapped materialization 合同联合使用。
