# ErrorCode、Failure 与 Result 桥接合同

最后更新：2026-10-31（Asia/Shanghai）。适用固定 Rust revision
`119854756a0aeb66d2998055f96fa7175c7bfb37`。

## 结论

Python 继续保留现有三参数 sealed `Result[T, C, E]`、`Ok`、`Failed`、`Fatal`、
`Warn` 和 `ErrorCode`。PyO3 业务失败继续作为 `(value, failure)` 数据返回，
再映射为现有 `Failed(ExErr(...))`；不改成 `typing.Union`，不把公共业务失败改成
统一抛异常的 `PyResult`，也不建立第二套错误类型。

Python 与 Rust 的错误码整数空间不同，因此只按语义 category 选择 Python
`ErrorCode`。原始 Rust 数值仅在原生明确提供时写入 `FailureContext.rust_code`；
未知 category 和不存在原始码的 Rust 枚举分支保持 `None`，禁止按整数强转或猜测。

## 结构化失败

原生 `ospf_python._native.Failure` 暴露五个只读字段：

| 字段 | 含义 |
| --- | --- |
| `source` | `ospf-python-native`、`ospf-rust-core` 等来源 |
| `category` | 稳定语义分类，例如 `ILLEGAL_ARGUMENT`、`NO_SOLUTION` |
| `rust_code` | 上游明确提供的原始 `u8` 错误码；没有则为 `None` |
| `error_class` | Rust 结构化分类，例如 `INPUT`、`CALLBACK`、`TERMINAL_PROJECTION` |
| `message` | 双语失败消息 |

Python 适配层把前四项原样保存到不可变 `FailureContext`，把 `message` 放入
`ExErr`。因此调用方可以稳定访问：

```python
result = operation()
if isinstance(result, Failed):
    code = result.error.code
    context = result.error.value
    assert context.category in ErrorCode.__members__ or code is ErrorCode.APPLICATION_ERROR
```

`ErrorCode.__members__` 中存在同名 category 时按名称映射；未知 category 回退到
`APPLICATION_ERROR`，但原 category、source、rust code 和 error class 仍保留，
不得用回退码覆盖来源。

## Rust CoreError 映射

固定 revision 的映射以 `native/src/failure.rs` 为唯一实现，关键边界如下：

| Rust 错误 | Python category | 原始 `rust_code` |
| --- | --- | --- |
| `VariableError::NotFound` | `NOT_FOUND` | 无 |
| `VariableError::AlreadyExists` / `NameConflict` | `ALREADY_EXIST` | 无 |
| `VariableError::InvalidRange` / `InvalidValue` | `ILLEGAL_ARGUMENT` | 无 |
| `ModelError::NotInitialized` | `NOT_INITIALIZED` | 无 |
| `ModelError::AlreadySolved` / `MissingObjective` / `SymbolNotRegistered` | `FAILED_PRECONDITION` | 无 |
| 其他 `ModelError` | `MODEL_BUILD_FAILED` | 无 |
| `SolverError::NotAvailable` | `SOLVER_NOT_AVAILABLE` | 无 |
| `SolverError::Cancelled` / `Interrupted` | `CANCELLED` | 无 |
| `SolverError::Parsing` | `PARSING_FAILED` | 无 |
| `SolverError::NoSolution` / `Unbounded` / `Infeasible*` | `NO_SOLUTION` | 无 |
| `SolverError::Overflow` | `OVERFLOW` | 无 |
| `SolverError::UnsupportedValueType` / `CoreError::NotImplemented` | `NOT_SUPPORTED` | 无 |
| `SolverError::Timeout` | `TIMEOUT` | 无 |
| `SolverError::LicenseError` | `PERMISSION_DENIED` | 无 |
| 其他 `SolverError` | `SOLVE_FAILED` | 无 |
| `SolverNotFound` | `SOLVER_NOT_AVAILABLE` | `0x23` |
| `SolverEnvironmentLost` | `UNAVAILABLE` | `0x24` |
| `SolverSolving` | `SOLVE_FAILED` | `0x27` |
| `SolverModeling` | `MODEL_BUILD_FAILED` | `0x26` |
| `SolverTerminated` | `ABORTED` | `0x28` |
| `CoreError::Internal` | `APPLICATION_ERROR` | 无 |

`SolverError` 同时保留 `solver_error_class_code()` 的结构化分类；例如回调失败是
`CALLBACK`、数值失败是 `NUMERICAL`、终止投影是 `TERMINAL_PROJECTION`。category
与 error class 解决不同问题，不能互相替代。

无解、不可行和无界是正常 `SolveReport` 终态，不转成异常或 `Failed`。本表只覆盖
确实通过错误通道返回的 Rust 错误。

## FFI 异常边界

通用 `_binding.result.invoke()` 在直接原生调用边界只捕获既有的 PyO3
类型/溢出转换异常并转换为现有 `Failed`，同时保留原异常对象和 traceback 在
`FailureContext.callback_exception`：

| Python 异常 | `ErrorCode` |
| --- | --- |
| `TypeError` / `ValueError` / `OverflowError` | `ILLEGAL_ARGUMENT` |
这些边界失败的 `source` 为 `ospf-python-native`，`error_class` 为
`FFI_TRANSPORT`，不伪造 Rust 错误码。`KeyboardInterrupt`、`SystemExit` 和其他
`BaseException` 原样传播，不转成业务失败。`MemoryError` 和其他未声明为转换失败的
普通异常也原样传播，避免把资源、回调或内部合同异常错误分类为输入失败；具体入口
若需要结构化资源/回调失败，必须由该入口显式保留异常后再发布 Result。

只有“直接 PyO3 调用或输入适配”这一边界转换异常。用户 `map`、`flat_map`、
`on_success`、`on_failure` 回调中的普通异常保持原实例传播，不能被 Result
框架静默吞掉或包装。

## `unwrap` 政策

`unwrap()` 保留现有运行时合同：

- `Ok`、`Success`、`Warn` 返回成功值；
- `Failed` / `Fatal` 抛 `RuntimeError`，消息包含原失败内容；
- `unwrap_or()` 是业务代码的默认安全路径；
- 新绑定适配器不得用 `unwrap()` 把业务失败转成异常，只允许调用方在已经证明成功
  的断言、示例或测试中显式使用；
- 失败对象在 `unwrap()` 抛错后保持不变，不触发映射、回调或重试。

该异常是既有公开 API 的显式“成功前置条件”逃逸口，不是新绑定新增的业务异常
通道。改变异常类型或删除该方法会破坏现有调用方，因此本轮审计选择保留并补测试，
而不是擅自调整。

## 验证范围

本合同的自动化证据包括：

- `tests/native/test_failure_contract.py`：已知/未知 category、原始码隔离、
  普通异常身份、`BaseException` 传播和 unit 成功；
- `tests/utils/test_result_policy.py`：`unwrap`、`unwrap_or`、用户回调异常与
  不可变结果对象；
- `tests/math/ordinary/test_prime_sieve_binding.py` 与
  `tests/math/ordinary/test_integer_power_binding.py`：真实绑定失败的原始异常、
  traceback 和结构化来源；
- `native/src/failure.rs` Rust 单元测试：语义映射及不伪造原始码。

上述测试只证明当前 Windows CPython 3.13 源码合同。Linux、Gurobi 11/12、固定
性能 runner、长期资源和其他未编译后端仍未认证，不能由本合同推导为完整迁移完成。
