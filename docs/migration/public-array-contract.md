# 公开数组替换合同 / Public Array Replacement Contract

本文件审查 `ospf_python.multiarray.multi_array` 和 `multi_array_view` 的现有公开行为。
它不是整个数组替换完成声明。默认迭代已独立委托原生 shared-storage 适配器，见
`public-iteration-cutover.md`；公共 reduce 另接通固定 Rust 索引的 live 左折叠及显式 Result，
见 `public-reduction-cutover.md`。公共 eager map/flat_map 另接通原生 live 编排与 Result，
见 `public-mapping-cutover.md`；输出 NumPy 协议及历史 shape 不一致行为保持。
公共 mapped view 的 materialize 另采用原生 live 坐标采样、正确目标布局与外层 Result，
见 `public-mapped-materialization.md`。两个公共 transpose 已接通原生逐槽遍历并显式返回
Result，见 `public-transpose-cutover.md`；普通 view 物化与 reshape/flatten 四方法已有原生
Result 源码候选，完整操作门槛仍未验收，分别见 `public-view-materialization.md` 和
`storage-transform-contract.md`。
存储及其余数学路径仍为 NumPy/Python，私有绑定不得作为
静默 fallback 与其混用。固定 Rust revision 见 `api-map.toml`。

默认 get/set、方括号与 view/原生采样消费者的原子迁移方案见
[public-default-access-migration.md](public-default-access-migration.md)。该方案的索引协议
政策尚待确认；不表示默认访问或完整数组已切换，也不授权修改现有错误处理规则。

两个公共 `to_list` 已有返回现有 Result 的逻辑嵌套导出源码候选，标准列布局不再按
错误的物理 C-order 输出；完整操作验收仍独立，见 [public-nested-export.md](public-nested-export.md)。

完整共享权威、门面独立重绑定、动态缓冲元数据和多根对象图恢复合同见
[public-array-state-contract.md](public-array-state-contract.md)。其中 AS-001 明确记录
object ndarray 缓冲先行 deepcopy 会拆散共享别名，严格 xfail 仍是未通过门槛，
不能用单数组 copy/pickle 的通过认证完整公共状态接管。

## 有效行为基线 / Valid Behavior Baseline

`tests/multiarray/test_array_compatibility.py` 在当前公开实现执行，覆盖：

- 包级/定义模块导入身份、`AbstractMultiArray[T,S]` 继承，普通下游子类及额外状态。
- 位置参数 `(shape, data)` 构造保留 shape 和 ndarray identity，包括 strided 输入。
  外部 ndarray 更新影响两个数组类的读取，可变数组写入反向影响外部缓冲。
  这是现有共享合同；私有 `from_numpy(copy=True)` 不等于该构造的兼容替代。
- `get(*indices)`、`array[tuple]`，一维整数索引、`len/size/ndim` 与物理顺序迭代。
  列存储的物理迭代顺序不等于逻辑行访问顺序，必须分别审查。
- 普通 object 元素/None、标量 shape=()；NumPy 数值 get/迭代会调用 `.item()`，
  返回 Python 标量。私有容器保留 NumPy scalar 类型，不能无说明替换这一边界。
- 行布局的 eager map、左结合 reduce（两者显式消费 Result）、嵌套 to_list、独立 flatten/reshape。
  本基线不把列布局错误输出当作应保留的正确行为。
- 工厂 zeros/ones 保留传入 shape identity，NumPy 存储 dtype 为 float64，读取为内置 float；
  scalar full 支持普通对象/None/字符串。from_list 复制输入容器结构但保留普通 object 叶身份。
  同 shape 的普通数值等值比较跨 dtype 成立，repr 显示物理数据；可变数组沿用 object
  identity 相等/hash/repr。基线不验证已知错误的 value hash。
- 全部 pickle protocol、copy/deepcopy：浅复制共享 `_shape/_data`，深复制独立复制；
  pickle 使用现有字段状态，恢复后保持类、shape、值和子类额外字段。
  仅含 `_shape/_data` 的旧状态恢复后仍可读取，不能删除字段而不提供旧 payload 迁移。
  补充图合同验证重复叶别名、leaf.owner 指回恢复数组、全局 callable 及 view/source alias；
  只比数值列表相等不足以证明替换兼容。
- 公开 `MultiArrayView.map` 是惰性元素映射：创建、读取 shape 不执行函数；
  每次 get 重新计算、不缓存、观察源的后续修改；materialize 是独立容器。
  `MappedMultiArrayView.get` 直接把回调返回的 Result 当作数据，普通异常直接传播。
  materialize 同样不拆包回调 Result，但操作本身已显式返回现有外层 Result，
  C-order 采样/NumPy 输出之后由固定 Rust builder 发布正确物理布局，修复 TF-001。
  新私有回调的 Result 解包/失败传播是新合同，不是无差别 drop-in replacement。

These baseline tests certify existing valid public contracts only. They neither switch
the public implementation nor ratify known defects.

私有 shape-directed `from_list` 已有严格嵌套/不透明叶/逻辑坐标合同，见
`nested-array-contract.md`。该入口不调用 NumPy、不推断 dtype 或广播；并不改变这里
公共 Sequence 摄入、非 Result 签名、类身份或旧列布局展平规则。

## 已复现的问题 / Reproduced Issues

独立所有权/行为探针已执行，不仅依据代码推测：

| 场景 / Scenario | 当前事实 / Current evidence | 替换要求 / Requirement |
| --- | --- | --- |
| 列布局 to_list | 旧实现给物理 C-order；当前标准源码候选改为逻辑 `[[0,2,4],[1,3,5]]` 并返回 Result，见 public-nested-export.md | 独立完成操作/性能/发行验收，不把自定义 hook 或完整权威视为已切换 |
| offset view | 旧 materialize 忽略 offset；shape 仍宣称完整源范围 | 普通物化源码候选已按受检剩余区域复制并返回 Result，见 public-view-materialization.md；shape/get 整类权威仍待切换 |
| TF-001 mapped 列布局物化 | 旧逻辑将 C-order 采样数据直接放进列布局 shape，转置后逐坐标值错位 | 当前 native mapped materialize 已按目标物理布局发布；见 public-mapped-materialization.md，不能用数据集合相同替代坐标合同 |
| flat_map | 回调逐项返回两个元素后，reported size=6 而底层元素数=12 | 公共 live 编排切换明确保留历史 shape，见 public-mapping-cutover.md；尺寸安全升级独立待决，不静默截断/重塑。私有快照入口仍要求显式匹配 shape |
| 错误维数/负坐标 | 少轴、额外轴、负坐标能静默混叠为有效线性位置 | 新严格边界返回 Result；旧非 Result 签名的兼容策略必须显式决定 |
| 只读 ndarray 写入 | MutableMultiArray 的 set 抛 ValueError | 共享与写权限必须有受检合同，不能复制后声称仍是原共享模式 |
| 任意 object.item | 已修正：公共 helper/原生迭代仅转换 np.generic，普通 object/ndarray 叶不再执行 item | 兼容说明及显式转换迁移见 public-iteration-cutover.md；不等于其他旧算法已替换 |
| object 引用环 | NumPy object -> payload -> array 环未被当前 GC 回收 | 新 Rust 权威存储逐槽 GC，覆盖 source/view/callback/output/traceback 环 |
| 相等与布局 | 同物理序列、不同 storage order 比较相等，但逻辑坐标不同 | 明确比较口径与布局转换政策，不静默引入逻辑/物理含义变化 |
| 等值异 hash | +0.0/-0.0 比较相等，但 raw-byte hash 不等；跨 dtype 等值也不能用 bytes 作为值 hash | 不复刻违反 Python 等值同 hash 要求的算法；共享可写或不可哈希叶须有明确政策 |
| 外部写入与 hash | 标为不可变的数组仍共享 ndarray，外部写入会改变其 hash | 不在共享可写状态上提供会变化的值 hash；不能静默复制后声称保持共享 |

独立工厂探针还复现：full(shape=(2,), value=[1,2]) 使用 NumPy 广播得到两个整数，
并非把同一 list 当作每个槽位的叶对象；from_list 对列布局按物理 C-order 输入，
其 get 坐标与原嵌套行含义不同。NumPy scalar full 推断存储 dtype，如 int16。
这些属于必须显式决定的广播/dtype/访问顺序边界，不能用私有 full 的不透明叶语义
无说明覆盖。新私有 full/zeros/ones 规则见 `multiarray-contract.md`；公开 from_list
尚未替换或默认接入私有快照工厂。

这些是错误或需决定的历史行为，不是原生必须复刻的语义规范。修复公开行为须同时有迁移说明、
差分合同和真实调用方验证，不通过改测试 oracle 掩盖差异。

私有矩形 view 已支持省略 shape 时由 Rust 推导 offset 后的有效剩余范围，以及旧 view 字段的
显式复制导入，见 `view-extent-contract.md`。旧公共 view 仍未切换，不能用复制导入代替
共享/默认构造、旧 scalar.item、非 Result 错误和自动 pickle 图恢复的验收。

## 惰性映射桥接 / Lazy Mapping Bridge

私有 `_binding.multiarray.MappedMultiArrayView.create(source=..., callback=...)`
保留 Rust 通用数组/矩形 view 和 Python 函数；不会复制元素、执行函数或缓存结果。
再次以 mapped view 为 source 构造时，保留最终源与有序函数链，不保留中间元素数组。

- `at(indices)` 在一次 FFI 中受检读取一个槽位，解除 Rust 存储锁后调用函数链。
  每次调用重新读取当前源，None 为成功数据；索引/cleared 失败不调用用户函数。
- `materialize(access_order=...)` 使用现有 Rust snapshot + mapped builder 路径，
  一次取得完整槽位快照，按元素依次执行函数链，完整成功后才发布独立 immutable 数组。
  保持 shape、storage order 和坐标对应，不丢失矩形 view offset。
- 每个阶段按 `multiarray-contract.md` 的单层 Result 解包规则处理：
  plain/Ok/Success 成功，Failed/Fatal/Warn 立即停止并保留原 Result，
  普通异常保留原始对象/traceback，进程控制 BaseException 不吞。
  callback_index 是元素访问序号，不是函数链阶段；单点读取失败时为 0。
- 函数按访问需求保活到最后一个 lazy facade 释放；无 native 持久 callback、
  Python 数组遍历内核、持久 Rust 借用或权威元素镜像。
  Python 函数链的迭代只编排用户扩展点，不执行数组索引算法。
- 回调可再次读取/映射/写入源，不在锁内执行；at 仅快照一个槽位，materialize 快照全部槽位。
  不回滚外部副作用、不 deepcopy 元素，也不承诺线程安全的用户 callable。
- 同一个 lazy view 并发访问是独立操作。materialize 的槽位快照与原子 batch writes 互斥；
  多次 at 不是一个跨调用事务，不承诺看到同一个版本。

这与 RG-004 的 Rust PlaceHolder 轴映射不同，不使用有缺陷的 mapped-axis iterator。
现有私有 `MultiArrayView.map` 仍为 eager，不能在原地将其语义改成 lazy；公开切换时应明确适配。

## 切换前剩余条件 / Remaining Cutover Conditions

公共新增 `at` / `set_at` / `at_many` 已有受检 Rust 坐标及原共享 ndarray 的独立合同，见
`public-array-access.md`。它们是返回现有 Result 的增量迁移入口，不改变旧 get/set
或方括号协议，不处理任意自定义映射，也不代表完整存储接管。
at_many 批量检查后原生收集一个捕获 buffer 的有序槽位；旧字段复制导入已复用 raw
收集器而不再走 ravel/list/重复一维形状构造。二者不提供并发原子快照或共享 GC 修复。

私有显式 `equals` 的逻辑坐标、受检布尔比较器、同源两侧快照与错误合同见
`array-comparison-contract.md`；它没有改写 Python `__eq__`/hash。该文档同时明确 repr、
offset view 范围仍为未完成的公共协议门槛，不复刻已知 hash 缺陷。公共默认 physical/live
迭代的独立原生协议切换见 `public-iteration-cutover.md`，不代表共享存储接管。

私有 `describe` 已有逻辑前缀、布局/offset 标签、字符/叶数预算、递归守卫及格式器错误合同，
见 `array-description-contract.md`。它不改变默认 repr，不承诺限制任意用户格式器内部资源。

私有 `iter_live` 已有默认物理顺序、逐槽读取、受检 advance/标准 next、源/facade 保活和
耗尽释放合同，见 `array-iteration-contract.md`。公共默认迭代另走保持 generator 语义的
共享外部存储适配器，不是隐式接入本私有游标；不能用 O(rank) 游标空间证明领域性能/
完整资源预算通过。

旧字段已有显式私有 `from_legacy_state(payload=..., copy=True)` 导入，详见
`legacy-array-bridge.md`：按旧一维物理序列解释布局，拒绝未知子类字段，不调用旧索引。
它不保留共享缓冲/dtype 赋值约束、不重定位对象图，也不接管公共 pickle 自动恢复。
该文档同时列出直接消费者及共享存储验收条件；Vector 是类型别名，不是 `_data` 读取者。

- 公开错误/索引协议与 Result、共享 ndarray/只读输入、dtype/scalar 转换、空轴/不一致 shape，
  都需要明确兼容决定，不能静默收紧或自动复制。
- 私有 reduce、坐标正确的 to_list 和显式 iter_snapshot 已有独立合同，见 `multiarray-contract.md`。
  公开 reduce 已单独采用固定 Rust 物理槽位遍历，但保留 live 读取与任意回调结果作为数据，
  不直接重导出私有快照归约；其 Result 升级见 `public-reduction-cutover.md`。
  公共 eager map/flat_map 同样保留 live 读取、NumPy 输出与 Result-as-data，
  不直接重导出会拆包回调 Result 的私有快照映射；见 `public-mapping-cutover.md`。
  to_list 的布局修复、完整存储及其他默认路径仍须分别验收。
  私有 full/zeros/ones 已有独立填充合同，但公开广播/dtype/from_list 和相等/hash/repr
  策略、泛型/自定义形状、view 范围与子类协议仍须在切换前验收。
- 新原生对象的公开 pickle/wire、旧字段 payload 恢复、copy/deepcopy 和 callback 可序列化政策。
  私有 Shape/对象存储/矩形与惰性 view 已有标准 copy/pickle 图合同与受检 Python 引用 DTO，
  见 `array-state-contract.md`；这不自动等价于旧公开 pickle、NumPy dtype/共享恢复或 JSON，
  不默认序列化任意 Python 函数或尚不支持 pickle 的原生数值/模型叶。
- 代表性领域调用方、性能/资源预算和发行验证完成后，才原子切换入口并删除接管的旧算法。
- BlockMultiArray/DataFrame/indices/einsum 等不属于本合同的完成范围，仍按独立 api-map 推进。

AST import/`_data` 属性候选仅用于定位审查面，不证明动态调用/外部下游已穷尽，也不能用作删除依据。

存储变换补充：reshape/flatten 四方法已有原生 Result 候选，旧候选的性能和发行证据
不能认证新的 shape.size 实现；当前操作门槛与其他平台、长期资源仍待验收，详见
`storage-transform-contract.md`。
