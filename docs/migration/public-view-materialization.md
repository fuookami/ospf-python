# 普通公共视图物化 / Plain Public View Materialization

`MultiArrayView.materialize()` 的默认入口已接通原生源码候选，显式返回现有
`BindingResult[MultiArray[Any, Any]]`，调用方必须消费 `Ok/Failed`。本合同只覆盖这一操作，
不代表整类 view、共享存储或性能/发行门槛已经验收。固定 Rust revision 见 `api-map.toml`。

## 有效区域与权威路径 / Valid Region and Authoritative Path

旧实现无条件复制全源，忽略 offset，导致 `view.get(0, 0)` 与物化结果同坐标不一致。
新实现复用原生受检矩形 view：源维度必须为正、乘积可表示；offset 为同 rank 的非 bool
整数 tuple，每轴满足 `0 <= offset < source_dim`。负数、等于/超过轴长、rank 错误及
容量溢出返回既有结构化失败；空区域不在当前受检 view 合同内。rank-zero 有一个槽。

- 全零 offset：保留读取到的源 shape 对象身份，使用实际 `source._data.copy()` 返回数据；
  不强制改变其 dtype、rank 或额外轴，也不把 copy 返回的 Result 当作操作失败拆包。
  dims/offsets 的整数协议、正维度、受检乘积、rank 和顺序仍逐次校验；确认恒等区域后
  不再构造不会用于索引的稠密形状/步长，不跳过原始字段校验或建立跨调用缓存。
- 非零 offset：输出 shape 为独立的 `DynShape(source_dims - offsets, storage_order)`。
  固定 Rust 的受检 view、源 `index_of` 和源/目标 strides 规划物理存储描述符；Python 不实现
  另一套坐标/布局循环，NumPy 不接收公共目标 shape 来替代 Rust 规划。
- 非零时复制结果的第一轴长度必须等于源逻辑槽数。标准 shape 加精确 ndarray 用一次
  dtype 感知区域复制：按固定 Rust 目标 strides 排列非 singleton 轴，源 `index_of` 提供
  起点、源 strides 提供槽步长，真实 ndarray 提供字节步长和附加轴。NumPy C API 仅复制
  该受检存储描述符，再调整新副本的第一轴 header；不生成另一套坐标索引，不逐叶探测。
- 自定义 shape、ndarray 子类及外部存储仍调用实际复制结果的
  `take(indices, axis=0)` 协议；标准描述符超过 NumPy 维数/字节步长容量时使用现有固定
  Rust 坐标 gather，而非旧 Python 算法。`(N, trailing...)` 附加轴保留，不推断新 dtype。
  标准 ndarray 的容器独立且拥有选中区域存储，object/含 object 字段的叶保留原身份。

Plain materialization copies storage; it does not sample live `get`, call scalar `.item()`,
evaluate mapped callbacks or infer a new dtype. Mapped materialization has a separate live
sampling/NumPy-output contract in `public-mapped-materialization.md`.

## 扩展点与求值次序 / Extension Points and Evaluation Order

保留旧表达式的关键顺序：实际 copy 完成，然后捕获当前公共 `MultiArray` 构造器，再重新
读取当前 `owner._source.shape`。copy hook 可替换源或构造器；shape getter 后来修改全局
构造器不影响已捕获者。元数据及 offset 验证发生在 copy 之后，不回滚 copy 等外部副作用。

维度按实际迭代顺序逐项执行整数协议，再检查正值和累计容量。首个失败立即停止，
不读取后续维度，不提前读取 storage_order 或 offsets；不能先收集全部整数再统一检查，
也不能通过重迭代自定义 dims 补回丢失的元数据。普通整数协议异常保留原对象并通过现有
外部失败边界发布，BaseException 继续原样传播。bool、非正维度及容量失败维持既有分类。
成功耗尽或失败退出时，原生边界释放本次维度迭代器和序列的临时引用，之后才读取顺序及
offsets；不为复用验证证明而延长这些外部对象的生命周期。恒等区域也完整执行此边界，
但不调用 shape 索引协议或输出 shape 工厂。

Dimension iteration, integer conversion, positivity and cumulative capacity checks remain
ordered and stop at the first failure, before later dimensions, storage order or offsets.
Validation reuse must neither precollect/reiterate external dimensions nor retain temporary
iterator/sequence references until later metadata lookups. Identity regions still validate
metadata without calling the shape indexer or output shape factory.
`tests/multiarray/test_public_view_metadata_order.py` 覆盖该顺序及释放边界。

只有精确的标准 Shape1/2/3/4/DynShape 使用固定 Rust 标准源索引。自定义 shape/子类的
`flat_index(*projected_coordinate)` 为外部扩展点，按目标物理次序调用，支持整数协议和
一次负索引归一化。重复源位置是合法读取别名，并非目标布局冲突；bool 和越界索引失败。
输出仍使用 Rust 标准区域 shape，不将自定义公式误称为已迁移。外部 copy/take/构造器的
返回数据及副作用遵循其协议，不承诺任意用户实现都真正复制或保留 dtype。

标准描述符在输出 shape 工厂及待处理 signal handler 执行后，再次检查复制结果真实第一轴，
失效时返回 `ILLEGAL_ARGUMENT` 且不调用结果构造器；不把工厂前的长度校验当作原始缓冲
访问的永久许可。第一轴仍有效时，工厂对附加存储轴的修改按实际 ndarray 元数据复制。
The descriptor path revalidates actual axis zero after the shape factory and pending signal
handlers; invalidated storage fails before publication, while valid trailing-axis changes remain live.

## 错误、状态与资源 / Failure, State and Resources

外部 copy/shape/dims/index/take/构造的普通 Exception 返回
`APPLICATION_ERROR / EXTERNAL_VIEW_MATERIALIZATION`，原异常对象与 traceback 保留且不
格式化。KeyboardInterrupt/SystemExit/GeneratorExit 原样传播。原生容量/范围/元数据失败
保留原有分类，不 fallback 旧全源复制，不发布部分结果。

发布外部失败时，Python 的 handled-exception 状态仍是该原异常，已有外层处理状态在返回后
恢复；失败发布器再抛出的异常不被同一边界二次捕获，其 `__context__` 保留原异常。
异常已有的 traceback 链必须完整保留；新产生的适配帧可因实现语言而不同，不能删除已有帧
或伪造旧包装帧。
原生入口的重构不能仅传递异常对象而丢失 `sys.exception()`/异常链语义，也不能为此格式化异常。
External failure publication preserves handled-exception state and chaining, restores the caller's
prior state, and does not recatch a failing publisher. The complete pre-existing traceback chain
survives; newly added adapter frames may differ, without deleting or fabricating prior frames.

原生描述符只在本次调用存在，不新增 view 字段、不建立持久 owner/叶镜像/metadata cache。
默认原生 `_SharedView` 只保留协议类型、顺序常量和既有 Result 工厂；与 reshape/flatten
共用 Rust 的结果发布部件。成功路径直接调用既有 `Ok`，不往返 Python 传输 tuple/lambda，
不另建 Result 类型。工厂各强引用均参与 GC，调用中的 owner、shape 工厂和结果构造器
不写入配置；输出 `None` 或本身为 Result 时仍只包一层外部 `Ok`，不解释叶结果。
`DynShape` 工厂和解析当前构造器的 callable 仍逐次传入，保留 monkeypatch/重入求值点；
原始传输函数保留为私有互操作接口，不是另一条旧算法 fallback。
用户协议不在业务锁内执行，允许重入及等待另一线程；不承诺并发修改源字段/缓冲的原子性。
普通机器整数元数据一次受检，不逐槽重复 BigInt/源形状验证。标准描述符路径只暂存 O(rank)
元数据、全源 copy 与区域输出；gather/take 路径仍另有 O(region size) 索引。存储指针仅在
持 GIL 且 Bound/base 保活期间交给 NumPy C API，不在 Rust 中解引用或改写叶，不跨调用保存。
NumPy 自己负责 dtype/对象引用及字符串 arena 的复制；零字节/空附加轴仅分配输出 header。
遍历定期检查 signals，批量 NumPy 复制不保证任意即时取消延迟。这不是零拷贝，也不保证
外部扩展分配上界。失败 traceback 对局部对象的正常保活不是缓存。

## 独立未完成门槛 / Separate Pending Gates

- `view.shape/ndim` 仍报告源范围，构造、直接 `get` 和组合 lazy view 未整体切换；不能根据
  本操作正确的剩余区域断言整类 view 已修复。
- AS-001 缓冲先行 deepcopy 别名、共享 object 环 GC、公共存储权威仍独立 pending，
  见 `public-array-state-contract.md`，现有 strict xfail 不删除。
- 当前源码的基础/`scip,gurobi10` wheel 与同一 sdist 已完成仓库外 locked 重建和
  隔离安装 smoke；当前源码本地全域回归为
  `32023 passed / 1746 skipped / 29 xfailed / 8 failed`，8 项均为既有 RG-008。
  这些只登记为 Windows CPython 3.13 当前候选证据。
- 完整默认调用性能/资源、真实后端领域预算及最终跨平台 wheel/sdist 矩阵仍须分别
  验收；中大规模 1.15 性能预算不因修复旧 offset 错误而放宽，旧错误输出不作正确性 oracle。
- Linux/Gurobi11/12 未实际运行时不得以 Windows/Gurobi10 证据代替。

可执行合同见 `tests/multiarray/test_public_view_materialization.py`、
`tests/multiarray/test_public_view_descriptor_copy.py`、
`tests/multiarray/test_public_view_publication.py`、
`tests/multiarray/test_public_view_exception_state.py`、
`tests/native/test_public_view_materialization_solver.py` 及
`benchmarks/test_public_view_materialization_hot_path.py`；单位示例见
`examples/view_materialization_example.py`。实际进度和独立测量证据只记录在被忽略的 logs。
