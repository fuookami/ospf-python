# 数组 Live 迭代与协议边界 / Live Array Iteration and Protocol Boundaries

私有 MultiArray、MutableMultiArray、矩形 MultiArrayView 及可变 view 提供
`iter_live(*, access_order=None) -> BindingResult[MultiArrayIterator[T]]`。
它是非快照游标，不改变公共或私有数组的默认 `__iter__`，也不替换显式 iter_snapshot。

Live iteration reads one Rust-owned slot per consumption. Cursor position, lifetime and coordinate
mapping stay in Rust; Python exposes the protocol and existing Result without an array traversal loop.

## 顺序与更新可见性 / Order and Update Visibility

- access_order=None 默认为源的物理 storage order。显式 ROW_MAJOR/COLUMN_MAJOR 指定
  逻辑坐标访问顺序，独立于存储布局。view 以自己的受检 extent/累计 offset 遍历，默认沿用
  源布局；保留 rank/singleton/scalar，不忽略 offset、不读取区域外数据。
- 每次 next/advance 时只读取当前槽位，之后的位置可以观察创建后或上次消费后的写入。
  已返回的位置不重读，旧返回对象不会变成新槽位对象；叶自身可变状态仍共享。
- 一个原生游标只有一个位置；所有 Python alias、直接 native next、受检 advance 和多线程
  消费共享并原子推进该位置。不同 iter_live 调用创建独立游标，不隐式 fork/tee/rewind。
- 每次读取与源的原子 set_many 批次互斥，但多次读取不构成同一版本事务。并发写入下，
  完整遍历可包含不同版本；需要一致槽位集合时显式 iter_snapshot 或 materialize。
- 叶保持不透明，包括 None、NumPy scalar、sequence、Failed/Ok/领域对象；不调用
  item/iter/float/truth，不解包作为数据存储的 Result。与旧公共 scalar.item 转换不同，
  不能无说明直接替换该公共转换政策。

## 协议与受检消费 / Protocol and Checked Consumption

MultiArrayIterator 是标准 iterator，iter(cursor) is cursor，可使用 next/list/for 等。
`operator.length_hint(cursor)` 返回尚未消费的槽位数，关闭/耗尽后为 0；它不是独立快照。

```python
cursor = array.iter_live().unwrap()
present, value = cursor.advance().unwrap()
if present:
    # value 可以为 None，存在标志仍为 True。 / A None leaf still has presence True.
    consume(value)
```

- `advance() -> BindingResult[tuple[bool, T | None]]` 与 next 消费同一位置；成功叶为
  `(True, leaf)`，耗尽为 `(False, None)`。因此 None 叶不与耗尽混淆，失败也不伪装成数据。
- 创建时校验原生源/区域/访问顺序与 ready 状态，非法或 pending/cleared 返回 Failed，
  不发布可部分使用的游标。不会执行叶用户协议。
- 普通协议 next 在正常耗尽时抛 StopIteration，不把 Failed 当协议返回值。若内部源在活动
  游标期间被明确清理等防御性失效发生，advance 返回原生类别的 Failed；next 使用带双语
  原因的 ValueError，这是项目规则允许的迭代器协议错误桥接。两种失败均终结游标，之后
  永久耗尽，不反复失败或静默恢复。正常可达游标保活源，不应被 GC 中途清理。
- close() 幂等且无业务失败，返回 None；关闭后永久耗尽。读取已取得的旧叶仍由调用方持有。

## 所有权、GC 与实现 / Ownership, GC and Implementation

活动原生游标保活 native source 和创建它的 Python facade（view 时含 view/source 链），
不只是保活底层数据；这样 facade 子类与附加状态不会在活动迭代期间被提前销毁。
只保存 O(rank) 形状/offset 元数据和整数位置，不保存元素 list/ndarray、已读叶缓存、
Python index generator、跨调用 Rust 借用或自引用 iterator；创建时不克隆全源叶引用。

物理整数组顺序使用固定上游公开连续存储索引；其他顺序由上游 Shape.vector_of/index_of
计算坐标与偏移，Rust 仅做已受检区域的 offset 投影，不重写坐标/布局算法。
每次只在受保护的短作用域内借用源与克隆当前叶，返回前释放存储锁，不跨调用持锁/GIL 借用。

最后一个叶成功返回时、显式 close、失败或游标自身释放时即释放源/facade，无需额外 next
才能释放。源锁和游标锁先释放，终结状态先发布，再执行可能重入的 Python 析构；析构可以
再次 next/advance/close 或等待其他线程消费，均看到终结状态。耗尽游标仍保留 O(rank)
无叶元数据，直到自身销毁；不是完整内存预算验收。

原生 GC 按实际强引用遍历 source 与 owner，即使两字段引用同一对象也不去重；clear 先
take/解锁再 decref。source -> leaf -> cursor -> owner/source 环可回收，外部可达游标不被
提前清理。Python 游标门面只持 native handle，不复制权威位置或元素。

## Copy 与序列化 / Copy and Serialization

- copy.copy(Python cursor) 为新门面、同一 native cursor，消费/close 互相可见，不生成独立流。
- 活动或耗尽 native cursor 的 pickle（全部 protocol）、直接 reduce 和 deepcopy 均显式
  TypeError，且不改变位置。原生显式拒绝 protocol 0/1，不能让 object 默认协议生成丢失源/
  位置的空 payload。需要保存数据时先显式创建数组快照并使用既有对象图序列化合同。
- 这与数组本身的 copy/pickle 不同，不限制既有数组对象图合同，也不自动序列化活跃流。

## 公开切换门槛 / Public Cutover Gates

公共 __iter__ 现保持 Python generator 外壳，逐槽 shared/live 读取与位置委托独立原生
协议适配器，scalar 转换只针对 NumPy scalar；最后 yield 后仍保活到额外 next/close。
具体能力切换和兼容变更见 public-iteration-cutover.md，不等于把共享 ndarray 变成
Rust-owned 数组，也不改变这里私有游标的提前释放/opaque scalar 合同。
旧 public offset view 的范围问题、共享 ndarray/dtype/metadata 变化、数学消费者、性能/
资源预算继续按 public-array-contract.md、legacy-array-bridge.md 和总计划推进。
惰性 mapped view 不在本原语中隐式求值/物化；其迭代 callback/失败合同需另行实现。

真实 solver 合同使用两布局的 Fraction 行：消费第一行后修改未读第二行 RHS，后续
advance 读取新值，经 Rust Rational 明确转换为 Float64 再注册 SCIP/Gurobi10，最优值
从旧 RHS 场景的 27/8 变为 7/2（x=4, y=2）。不将精确叶在迭代中隐式降精度，也不
以此取代完整领域消费者或性能验收。
