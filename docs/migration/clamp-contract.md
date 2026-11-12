# Ordinary Clamp / 常规值域限制

`ospf_python.math.ordinary.clamp.clamp(value, *, min_val, max_val)` 现在返回
既有 `BindingResult`，调用方须先处理成功或失败。例如：

```python
from ospf_python.math.ordinary.clamp import clamp

assert clamp(5, min_val=0, max_val=3).unwrap() == 3
```

This is a source candidate, not complete migration acceptance. The similarly named
`ospf_python.utils.functional.min_max.clamp` remains a separate, unchanged API.

## Ordering / 排序

自然入口通过两次固定 revision `119854756a0aeb66d2998055f96fa7175c7bfb37`
的 `ospf_rust_math::ordinary::minmax` 排序；旧的 Python 嵌套 `min/max`
表达式不作为默认路径或失败后的 fallback。固定上游 `clamp` 的比较顺序、
反向边界和 NaN 行为与现有 Python 表达式不总相同，不能直接替换。

绑定只适配 Python 的富比较和两个位置的顺序：先调用上界对值的 `<`，再由
第一次选择的原对象对下界调用 `>`；保留反射比较、`NotImplemented`、真值
转换、平手的首对象、NaN、正负零、反向边界及任意精度，不转换为 `float`。
Rust 比较器缓存这一对位置的一次比较结果，而不缓存用户对象或跨调用状态。
模块或 `builtins` 中显式替换的 `min/max` 是外部钩子，按原次序调用，并非
失败后的隐式旧内核；外部钩子可以返回任意对象，包括 `None` 和 Result 本身。

## Failures And Acceptance / 失败与验收

普通比较或钩子异常转为 `Failed`，`FailureContext.callback_exception` 保留原
实例和 traceback，不调用其字符串化协议。`TypeError`/`ValueError` 映射
`ILLEGAL_ARGUMENT`，`OverflowError` 映射 `OVERFLOW`，`MemoryError` 映射
`RESOURCE_EXHAUSTED`，其他 `Exception` 映射 `APPLICATION_ERROR`；
`KeyboardInterrupt`、`SystemExit` 等 `BaseException` 按原实例传播。
成功值仍是被选中的原对象，而非复制值或展开后的嵌套 Result。

完整自然调用性能、长期资源、隔离发行和 Linux/Gurobi 11/12 验收以实际证据
为准。此次接通不表示其余普通数学、已知 RG-008/RG-010 缺口或整体迁移完成。

2026-10-31 当前源码两轮完整调用复测仍为红灯：精确内置整数的公开调用约
`3.82x–4.85x`，`Fraction` 约 `1.76x`。ordinary extrema 新增的精确小整数
列表快路径不会改变本入口两次独立原生 pair 调用的成本，也没有把该成本合并后
当作完整调用通过。入口继续为 `specified`；证据见
`logs/p3/ordinary-scalars-int-fastpath-20261031/`。
