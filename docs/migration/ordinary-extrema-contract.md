# Ordinary Extrema / 常规极值

`ospf_python.math.ordinary.min_max` 的 `min_of`、`max_of` 和 `min_max_of`
返回既有 `BindingResult`，不再返回裸值。调用方须先处理成功或失败：

```python
from ospf_python.math.ordinary.min_max import min_max_of

assert min_max_of([3, 1, 2]).unwrap() == (1, 3)
```

这是源码迁移候选，不是性能、平台或整个普通数学模块已验收的声明。其他工具模块
的同名能力不受影响。完整示例见 `examples/ordinary_extrema_example.py`。

## Ordering / 排序

固定 revision `119854756a0aeb66d2998055f96fa7175c7bfb37` 的
`ospf_rust_math::ordinary::minmax` 逐对选择，旧的内置 `min/max` 算法不作为
正常路径或错误 fallback。绑定复用 clamp 的比较适配：候选值与当前值以 Python
`<` 或 `>` 比较一次，保留反射、`NotImplemented`、比较结果的真值转换、平局时的
首个对象及 NaN 的先后行为。数据不隐式转换为 Float64，输出仍是原对象，`None`
和嵌套 Result 也是普通数据。

`min_of` 和 `max_of` 流式消费输入，不查询长度；`min_max_of` 按旧顺序先执行
`list(items)`，再完整计算最小值，最后完整计算最大值。列表是该公共方法原有的
临时快照，不是持久状态或另一套排序算法。元素的比较可以修改源或模块钩子；
流式与快照方法分别保留各自的观察顺序。显式替换模块或 builtins 的 `min/max`
仍作为用户钩子被调用，`max` 在最小值计算后才查找；它们不是隐式失败回退。

无用户钩子时，原生遍历分别持有当前值与其比较键，且在比较时分别持有候选值与
比较键；这与内置函数的对象生命周期一致，避免依赖可观察引用计数的比较器改变
结果。该细节已用 CPython 3.13 的源码入口及 3.15 的隔离 wheel 公开入口对照；
不外推至尚未验证的解释器或版本。

对于长度至少 64、元素全部为精确内置小整数的精确 `list`，绑定增加一个不分配
Python 迭代器的借用槽位快路径。它只为每个候选保留索引和 `i64` 值，但仍逐对
调用固定 revision 的 `ospf_rust_math::ordinary::minmax`，最后只发布一次原始
列表对象。遇到宽整数、`bool`、`int` 子类或其他对象时，快路径在产生任何用户
可观察比较前停止，并从开头重跑原迭代/富比较协议；模块或 builtins 钩子、异常
身份、平手首对象和比较顺序均不变。短列表继续使用原协议，避免快路径分派抵销
固定调用成本。

当前源码两轮完整调用测量中，1024/10000 项的 `min`、`max`、`minmax` 均通过
原 `1.15x` 门槛，最差为 `0.700678x`；此前约 `1.89x–2.13x` 的大列表红灯已
消除。1/16 项调用仍约为 `2.40x–4.89x`，由既有 Python 门面、PyO3 调用、
Result 发布和 `unwrap` 的固定成本主导，因此本入口仍不是 `switched`。证据见
`logs/p3/ordinary-scalars-int-fastpath-20261031/`。

空输入时，不计算极值；绑定让实际解释器的原始内置函数处理一个空 tuple，以
生成该解释器版本的异常类型和文案。用户比较、迭代和列表构造的普通异常转成
`Failed`，`FailureContext.callback_exception` 保留原实例与 traceback，不对其
字符串化。`TypeError`/`ValueError`、`OverflowError` 和 `MemoryError` 分别映射
`ILLEGAL_ARGUMENT`、`OVERFLOW` 和 `RESOURCE_EXHAUSTED`；其他 `Exception`
映射 `APPLICATION_ERROR`，`BaseException` 原样传播。

大列表快路径不代表完整自然调用性能通过：短输入仍超出预算，长期资源、隔离
wheel/sdist、Linux 和其他承诺平台也未验证，不能据此登记为正式 switched。
RG-008、RG-010 及全部迁移要求不因此关闭。
