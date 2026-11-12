# 数组受检描述与资源边界 / Checked Array Descriptions and Resource Boundaries

私有 MultiArray、MutableMultiArray、MultiArrayView 及可变 view 子类提供
`describe(*, formatter=repr, max_items=20, max_chars=4096) -> BindingResult[str]`。
这是公共 repr 切换前的受检原语，不改变当前 dataclass repr、identity equality/hash
或默认迭代，不调用旧 NumPy 数组、tolist 或索引算法。

The checked description delegates traversal to pinned Rust storage and invokes Python formatters
only after unlocking. It is not a cutover of the public Python representation protocol.

## 输出与布局 / Output and Layout

完整输出示例：

```text
Array(shape=(2, 3), storage_order=COLUMN_MAJOR, offsets=None, access_order=ROW_MAJOR, data=[0, 1, 2, 3, 4, 5])
```

- data 为逻辑 row-major 叶序列，不是物理缓冲；storage_order 显式标记实际布局。
  无维标量 shape=() 且最多格式化一个不透明叶；一维 shape 保留 tuple 尾逗号。
  不同存储类型使用相同 Array 标签，不以文本承诺具体 Python 类。
- view 只显示自身受检区域 shape、累计 offsets 和源布局，不输出全源数据，不物化数组。
- 这是诊断文本，不是 repr/eval 构造表达式、JSON 或稳定 wire schema，无类型恢复保证。
- formatter 默认调用 Python repr，不执行叶的 item/float/hash/truth 协议。自定义格式器可
  返回 exact 内置 str 或单层 Ok(str)；str 子类、NumPy str、None/bytes/数字/嵌套
  Ok/Success 均失败，不隐式 str()。
- Failed/Fatal/Warn 停止并保留原 Result；普通 Exception 保留对象与 traceback，不格式化
  异常；BaseException 原样传播。callback_index 是零基逻辑叶位置，含规范化失败阶段。

## 预算与快照 / Budgets and Snapshots

- max_items 必须为 [0, sys.maxsize] 内 exact 内置 int；max_chars 必须为
  [3, sys.maxsize] 内 exact 内置 int。拒绝 bool/子类/隐式转换，非法预算或不可调用的
  formatter 在读取/用户回调前失败。max_items=0 仍验证源/区域，然后显示元数据与省略号。
- 最多取得 min(max_items, 元数据后的剩余字符容量, 区域元素数) 个逻辑叶引用快照，
  不为 preview 复制全源引用。访问/存储顺序一致时使用上游公开连续存储前缀；其余顺序与
  view 使用上游受检 iterator.take，不手写坐标引擎。辅助引用空间随预览而非全源大小增长；
  形状/区域元数据和上游遍历仍有 O(rank) 成本。
- 所有预览槽位在同一源锁作用域内快照，解锁后执行用户代码/释放引用。格式器可重入读写
  源或等待另一线程写入；已快照槽位不受后续原子写入影响。叶自身可变状态仍共享，不承诺
  深对象事务，不回滚格式器副作用。
- max_items 截断使用 data 中的 `...`。max_chars 覆盖**全部输出**，以 Python Unicode
  code point 计数，含元数据/标点/省略号；结果不超过上限。字符不足时输出文本前缀，最后
  三个字符改为 `...`，括号可不完整。隐藏叶不调用 formatter；元数据耗尽预算时不取得叶
  引用，但 pending/cleared/错误区域仍必须失败。
- 高 rank 元数据也受字符预算限制，以迭代而非递归格式化。通过 CPython exact str
  拼接/切片保留非 BMP 字符和孤立代理码，不有损转成 Rust UTF-8，不调用 str 子类协议。
- **不是用户代码沙箱。** 无法预知 formatter 输出长度；一次调用可能先构造巨大字符串、
  永不返回或耗尽资源，之后才裁剪。也不限制叶自身 repr 的深度/工作量。预算限制最终输出
  与绑定累计文本，不证明格式器内部峰值内存、执行时限或长期资源预算通过。

## 递归与并发 / Recursion and Concurrency

同一 Python 线程在格式器中再次 describe 同一原生源（包括浅复制门面和任意同源 view），
返回 Ok("<recursive array>")；max_chars 小于 17 时返回 Ok("...")。递归占位不重新读取
源或调用格式器。守卫按原生源而非门面身份，因此不同区域也保守视为同源重入；独立源可
继续描述，跨源循环回到同源时停止。跨线程不共享守卫，不返回伪 busy。

守卫仅存线程局部身份数字，不持久保活源/叶/格式器；finally 在成功、失败及 BaseException
路径清理。错误保留 traceback 会自然保活其引用，释放错误后相应 Python/Rust 环须可回收。
守卫不是任意用户递归调用的全局深度限制。

## 切换门槛 / Cutover Gates

公开 repr 仍未改写。须独立决定公开格式、完整/有界显示、失效/格式器失败的 Python 字符串
协议适配、子类及递归行为，并同步文档/差分/下游；不能把 Failed 强制成文本或格式化用户
异常，不能把受检 describe 通过记为默认 repr 已兼容。
默认 physical/live generator 的独立原生切换见 public-iteration-cutover.md；公共比较/hash、
view 范围、完整共享存储、旧 pickle 自动恢复、
数学消费者和性能/资源预算仍按总计划，见 array-comparison-contract.md、
public-array-contract.md 和 legacy-array-bridge.md。
