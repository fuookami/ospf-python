# 组合与排列合同 / Combination and Permutation Contract

## 范围和当前状态 / Scope and Current State

`combinations(items, k)`、`permutations(items, k)` 及两个 `_async` 自然入口
已按 Windows CPython3.13 的操作范围切换，并显式返回既有 `BindingResult`，两个旧 Python 回溯内核已从
生产门面移除。异步入口通过 executor 调用同一同步函数并返回同一 Result。
完整自然调用的局部性能/原生资源包络、响应探针、真实SCIP/Gurobi10消费者及当前
wheel/同sdist隔离重建/无SDK安装验证通过，API-map登记为 `switched`。
该登记不认证Linux、Gurobi11/12、固定runner/全领域/长期资源预算，其余数学、数组与
整个迁移仍须按各自合同完成，不以本操作切换替代。

The four natural public entry points are switched within the Windows CPython 3.13
operation scope and return the
existing Result. The old Python backtracking bodies are removed, without fallback.
Complete-call local performance/native resource envelopes, responsiveness, real
SCIP/Gurobi10 consumers and current isolated distributions/SDK-free installations
are verified. This does not certify Linux, Gurobi11/12, fixed-runner/full-domain/
long-term budgets, remaining math/array capabilities or the complete migration.

## 必须保留的结果语义 / Required Result Semantics

- 按输入**位置**选择，不比较、哈希、转换或去重叶；相同对象的两个槽仍为两个位置。
- 每行是独立的 Python list，行内叶保持源对象身份；修改结果容器不修改输入容器。
- 两个入口均按输入位置的字典序输出，不能用排序叶值修复顺序；叶可能不支持比较。
- `k == 0` 返回 `[[]]`，包括空输入；负 `k` 或大于输入长度返回 `[]`。
- 包导出与深层模块保持同一函数身份，不增加另一个供业务选择的原生/旧版入口。
- 异步入口仍使用同一个同步入口，保留实际结果及异常来源；取消等待不代表 executor
  中已启动的工作已终止，不冒称具有中断或事务回滚保证。纯 Rust 位置计划的生成、
  排序及正常释放不持 GIL；Python 行发布及外部协议每256步检查信号和已用时间，
  距上次检查至少1ms时，重新观察当前解释器的线程状态；存在其他线程状态或无法确认时，
  在不持GIL期间短暂休眠，避免立即重新加锁使等待线程饥饿。只有当前线程状态时跳过
  无竞争的休眠，但仍检查信号并更新检查点，不缓存单线程结论。使用当前标准CPython
  的公开C接口，仅比较线程链表头并查询当前有效线程的后继，不遍历、解引用或保留
  其他线程指针；不依赖会漏掉未注册低层线程的threading.active_count()。
  检查点不是严格时间上界，实际唤醒精度由系统调度决定。
  Python 对象访问仍在持 GIL 时执行。executor 身份测试不等于响应预算通过，局部响应
  探针与跨平台/领域验收仍须独立核实；不保证任意 getter、GC 或失败清理均有固定时限。

Selection is positional, rows are detached lists, and leaves retain identity. Both
outputs use lexicographic **position** order. Zero selections have one empty row.
Async composition must not create another enumeration kernel.
Pure-Rust metadata work runs detached, while Python publication cooperatively yields
between bounded batches. This is not a hard-real-time or arbitrary-callback guarantee.
Every elapsed checkpoint rechecks the current interpreter's thread states through
public CPython C accessors. With only the current state, it skips an uncontended
sleep, not signal checking; with a peer or uncertainty, the existing positive wait
remains. It never caches the observation, traverses/dereferences peer states, or
uses Python's incomplete registered-thread count. This operation is specific to
standard CPython, not certification for free-threaded Python, other interpreters or abi3.

## 固定上游能力与差异 / Pinned Upstream Capabilities and Differences

来源是 `ospf-rust-math/src/combinatorics/permutations.rs`，revision 为
`119854756a0aeb66d2998055f96fa7175c7bfb37`，不是相邻 Rust 工作区的当前 HEAD。

| 项目 / Item | 上游事实 / Upstream Fact | 迁移要求 / Migration Requirement |
| --- | --- | --- |
| 固定长度组合 | `combinations_of_size` 直接生成位置字典序组合 | 不通过全部子集生成再筛选 |
| 固定长度排列 | `permutations_of_size` 先组合，再对每组 QuickPerm | 不等于旧全局位置字典序；需要明确的位置顺序适配 |
| 零长度 | 两个上游入口均返回空 Vec | 在边界显式恢复公共 `[[]]` 单位元 |
| 叶复制 | 通用 `T: Clone`，不是 Python 值转换 | 仅复制受控槽引用或位置，不比较业务对象 |
| 容量 | `factorial`、排列容量乘法没有完整 checked 保护 | 调用上游之前检查行数、引用数、字节容量；不能等 Rust panic 后分类 |
| 外部序列 | 上游接受长度固定的借用切片 | 不能把动态 Python 索引协议悄然替换为快照语义 |

The pinned fixed-size functions exist and are directly compiled/tested by the binding
crate. Their zero identity and partial-permutation order differ from the public API.
The all-subset helper is not a substitute for fixed-size selection, and unchecked
factorial/allocation arithmetic needs preflight validation.

## 原生位置计划与外部协议 / Native Positional Plans and External Protocols

旧入口不是 `list(items)`：它先比较 `k`，再按需调用 `len` 和整数 `__getitem__`，
递归过程会重新读取长度，且前缀上的同一个叶会被后续多行复用。它不调用输入的
`__iter__`。自定义序列的 getter 可以修改后续元素；组合还能观察递归期间增长的长度。
因此，原生边界不把输入统一转换为 Vec/列表快照。

标准内置 list/tuple 与精确内置数值参数直接使用固定上游完整位置行；只排序整数位置，
不比较叶。单位置排列与组合相同，二者复用上游固定长度组合，避免为每个位置建立
QuickPerm 工作区；没有在绑定中生成选择行。已按字典序生成的完整组合不重复排序。
其余排序在位置键可安全容纳于128位时采用稳定的逐字节计数排序，键中的零值用于前缀
结束符；双缓冲仅重排已存在的上游位置行，不生成、去重选择行。短计划、较宽路径或
可选排序缓冲分配失败时，继续按完整位置字典序比较排序；容量检查包含两份临时键空间。
键宽不超过64位时，两份缓冲实际存储64位键；更宽的键才使用128位，最终重排行时仅更新
目标槽映射，不再搬移已经无用的键。两种键宽均与完整位置比较顺序交叉验证。
严格递增的组合前缀还可使用双位编码：00终止、01选择、10跳过；仅在位置域不超过64且
比通用数字键更短时采用，排列不使用该编码。它只编码并重排上游已生成的行，不产生选择
或删去无法完成的前缀。完整前缀计划的行数由同一容量检查受检计算，合并容器先预留空间，
避免逐深度合并时重复扩容；这不是跨调用缓存，也不影响上游枚举或外部协议求值。
内置 list/tuple 使用各自的受检
整数索引接口，完整读取一行后才分配 Python 行；临时引用缓冲逐行转移并复用，不缓存
源或叶，不把输入转为快照。自定义索引源、子类或带自定义比较的选取参数，则由固定上游生成各深度的
合法位置前缀，再按位置字典序编排 Python 访问。绑定只管理外部调用的前缀引用和每层
已读取的长度上限，不实现选择递推或自行产生合法组合。完整计划包含每个合法父前缀，
完成或拒绝后跳过整个子树，因此只按下一父路径的深度释放活动引用栈，不重复比较位置。
每个前缀的 k 相等比较、len、
getter 及引用释放按旧求值次序执行；长度增长时重新取得上游位置计划，活动祖先的长度
上限保持，后续读取仍 live。精确内置 int/bool/float 的相等判定可使用受检深度，
非整数或非有限 float 不会被强制转为可匹配深度；子类或外部 k 仍在每个前缀执行原始
Python 比较，不缓存其比较结果。两种协议适配共用相同上游函数，不是标准 list 旁路加旧内核。

前缀计划是临时索引元数据，不缓存源、叶或跨调用状态。它可能比旧 Python 回溯栈占用
更多内存；性能和资源必须独立实测，不以合同通过代替预算。上游调用前检查位置、行、
引用及字节容量和不受检 factorial 的中间界限。深度超过128的上游递归使用显式受检
工作栈，而不是 Python 所在线程的原生栈；独立进程测试覆盖129/512/4096深度，不据此
宣称任意输入或系统内存下均能成功。分配/创建工作栈失败返回结构化失败，无事务或沙箱保证。

Exact builtin protocols use full upstream positional rows. External indexed protocols
use upstream-generated prefixes solely to schedule live Python evaluation, retaining
prefix references and per-frame captured lengths. Growth regenerates upstream metadata
without changing ancestor limits. There is no second selection recurrence or Python
fallback. Temporary prefix plans have their own memory cost; checked addressability and
worker-stack tests do not certify complete resource budgets or an allocation sandbox.

Single-position permutations reuse the identical pinned fixed-size combination result.
Already ordered full combinations need no second sort. Other ordering uses stable
bytewise counting passes over checked integer keys up to 128 bits, with zero terminating
prefixes. Two temporary buffers reorder existing upstream rows without generating or
deduplicating selections. Short plans, wider keys, and optional buffer allocation failure
use full lexicographic comparison; capacity checks include both key buffers.
Keys up to 64 bits use actual 64-bit buffers, with 128-bit buffers reserved for wider
keys. Final row reordering updates only destination slots, not discarded key payloads;
both buffer types are cross-checked against full positional comparison.
Increasing combination prefixes may instead use two-bit symbols (00 ends, 01 selects,
10 skips), only for at most 64 input positions and when shorter than the general key.
This encodes existing upstream rows, never generates selections, and never applies to
permutations. The checked total prefix-row count also reserves the merge container before
upstream rows are appended, without a cross-call cache or any change to live evaluation.
Complete parent prefixes and whole-subtree skips let the active reference stack follow parent
depth alone, preserving observable release order. Builtin list/tuple access uses checked typed indexing, and a reusable
temporary reference buffer transfers each fully read row into a fresh Python list.
Neither this buffer nor the ordering plan retains sources or leaves across calls.
Exact builtin counts use checked depth equality, including noninteger/nonfinite float
handling. Count subclasses and external count protocols still perform the original
live Python comparison at every prefix; their comparison results are never cached.

`tests/math/combinatorics/test_selection_contract.py` 记录确切读取轨迹、负/零/过大值
短路、getter 写入、动态增长和原异常对象。bool、整数值 float 和非整数 float 的
历史输出均保留，不通过强制 int 转换收窄域。现有测试只显式解包 Result，并将普通
外部异常改为检查 Failed 中的原对象；BaseException 断言不变。

自然入口返回现有 `BindingResult`：外部普通 Exception
保留对象及 traceback，不调用其 `str`/`repr`；BaseException 原样传播。
异步同样保留 Result/异常对象。旧排列在 getter 增长输入后会访问越界的内部 used 表；
当前实现显式返回 `ILLEGAL_ARGUMENT`，不暴露已生成的部分行，也不把该内部故障误归为
外部 getter 的异常。它不是对任意期间修改的事务快照或回滚保证。

Legacy indexed extension calls are live and observable, including prefix reuse and
dynamic length. Their trace and noninteger-count behavior remain explicitly reviewed
migration requirements. Ordinary external failures retain their original exception and
traceback in Failed; BaseException propagates. The old permutation used-table overflow
after input growth is now an explicit input failure, not a fabricated external exception.

## 切换门禁 / Cutover Gates

自然同步/异步入口和所有消费者必须一起验证。完整调用预算包含输入摄入、原生枚举、
位置顺序适配、Python 行发布、Result/unwrap 与销毁；不能只测私有 Rust 枚举。
性能、资源、真实求解消费者、无 SDK 安装、两种 wheel 与同一 sdist 隔离 locked
重建及平台矩阵分别核验。源码接通和旧回溯体移除本身不构成验收；当前 `switched`
登记以实际完成的Windows操作范围为限，不宣称其余平台或完整P3通过。

Acceptance includes complete natural calls, extension/error semantics, resource and
domain budgets, consumers, and isolated distributions. Characterization alone does
not certify cutover. The switched registration reflects the verified Windows
operation scope only, not the remaining platforms or all of P3.

## 调用方升级 / Caller Upgrade

四个自然入口的导入路径与包重导出身份不变，但返回值从裸列表改为既有
`Result[list[list[T]], str, ExErr[...]]`。这是显式兼容升级，不是 list 的透明替身。
不要直接迭代 Result，也不要把所有错误都替换为 `[]`；空成功列表与读取失败有不同语义。
同步与异步都先消费成功值；业务路径可使用 `on_success` / `on_failure` 或模式匹配，
而不是用失败时会抛异常的 `unwrap()` 代替错误处理。

The import paths and package re-export identities do not change, but all four
functions now return the existing Result rather than a bare list. Consume success
explicitly; an empty successful selection is not the same as a failed indexed read.
Use Result callbacks or matching in application code, rather than unconditional
`unwrap()`, which raises on failure.

```python
from ospf_python.math.combinatorics import combinations, combinations_async
from ospf_python.utils.functional.result import Failed, Ok

match combinations(items, 2):
    case Ok(rows):
        consume(rows)
    case Failed(error):
        report(error.message)

# 在已有事件循环内等待同一个 Result。 / Await the same Result inside an event loop.
result = await combinations_async(items, 2)
result.on_success(consume).on_failure(lambda error: report(error.message))
```

`Failed.error.value.callback_exception` 保留原外部异常对象，包含原始 traceback；
不要为了日志先对该对象调用 `str` / `repr`。`BaseException`（如中断）仍正常传播。
异步取消只取消等待，不保证 executor 中的工作立即停止，也不提供外部 getter
副作用的回滚。输入仍是有长度与整数索引的序列，不升级为任意 iterable；不会调用
输入 `__iter__` 或先构造快照。`k == 0`、负值、过大值、既有 bool/float 行为和叶身份
按上文保留；排列增长导致旧内部 used 表越界的情况改为明确的输入失败。

The original external exception and traceback remain in the failure context;
formatting them is not required for handling the failure. BaseException propagates.
Cancellation stops awaiting, not necessarily executor work or external side effects.
Inputs retain the live length/index protocol, not arbitrary-iterable or snapshot
semantics. Positional ordering, boundary counts, legacy bool/float behavior and leaf
identity remain as specified; permutation growth beyond the original used-table
length is an explicit input failure.

完整可运行示例：`examples/selection_example.py`。它使用 `Quantity[Fraction]`，演示
两种同步与两种异步入口，并在每个失败点停止后续示例操作，不隐式转换为 float。
从同步程序运行 `python -m examples.selection_example`；已有事件循环应直接
`await examples.selection_example.main_async()`，不要再嵌套 `asyncio.run()`。
该示例不依赖 Python solver SDK 或商业许可；真实求解消费者另由后端测试覆盖。

The runnable example exercises all four entry points using exact fractional
quantities. Run `python -m examples.selection_example`, or await `main_async()`
inside an existing event loop. It requires no Python solver SDK or commercial
license; real solver consumers are validated separately.
