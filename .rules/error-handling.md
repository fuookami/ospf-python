# 错误处理规范

## 1. 核心原则

**整个项目统一使用返回错误（Result 模式），不抛出异常。**

所有可能失败的操作都应返回 `Result[T]` 或其变体（`ExResult[T]`、`Try`、`Ret[T]` 等），而不是抛出异常。

Python 中使用 `returns` 库或自定义 `Result` 类型实现此模式。

## 2. 错误类型体系

### 2.1 基础类型（ospf_python.utils.error）

- `ErrorCode` - 错误码枚举，定义所有标准错误码
- `Error` - 错误基类，包含 code 和 message
  - `Err` - 基本错误
  - `LazyErr` - 惰性消息错误，延迟消息构造
  - `ExErr` - 带关联值的错误

### 2.2 结果类型（ospf_python.utils.result）

- `Result[T]` - 基础结果类型（Union 形态）
  - `Ok(value)` - 成功结果，包含值
  - `Failed(error)` - 失败结果，包含单个错误
  - `Fatal(errors)` - 致命结果，包含多个错误

- `ExResult[T]` - 扩展结果类型
  - `Ok(value)` - 成功结果
  - `Failed(error)` - 失败结果
  - `Fatal(errors)` - 致命结果
  - `Warn(value, warning)` - 警告结果，同时包含值和警告

### 2.3 类型别名

- `Try` - 无返回值的结果：`Result[None]`
- `Ret[T]` - 带返回值的结果：`Result[T]`

## 3. 使用规范

### 3.1 函数签名

```python
from ospf_python.utils.result import Result, Ok, Failed
from ospf_python.utils.error import ErrorCode

# 正确：返回 Result
def parse(input: str) -> Ret[ParsedData]:
    if is_valid(input):
        return Ok(parse_data(input))
    return Failed(ErrorCode.ILLEGAL_ARGUMENT, "Invalid input format")

# 正确：返回 Try（无有意义返回值）
def save(data: Data) -> Try:
    if repository.save(data):
        return Ok(None)
    return Failed(ErrorCode.APPLICATION_FAILED, "Save failed")

# 错误：抛出异常
def parse(input: str) -> ParsedData:
    if not is_valid(input):
        raise ValueError("Invalid input format")
    return parse_data(input)
```

### 3.2 错误传播

使用 `run`、`pipe` 等函数顺序执行多个可能失败的操作：

```python
from ospf_python.utils.result import run

def process(input: str) -> Ret[Output]:
    return run(
        lambda: validate(input),
        lambda: transform(input),
        last_block=lambda output: save(output),
    )
```

### 3.3 错误映射

使用 `map` 转换成功值，使用 `on_failure` 处理失败：

```python
result: Ret[str] = parse(input)
output = (
    result
    .map(lambda it: str(it))
    .on_failure(lambda error: logger.error(f"Parse failed: {error.message}"))
)
```

### 3.4 工厂函数

使用提供的工厂函数创建结果：

```python
# 成功
Ok(value)
Ok(None)  # Try 的成功实例

# 失败
Failed(ErrorCode.ILLEGAL_ARGUMENT, "message")
Failed(ErrorCode.ILLEGAL_ARGUMENT, "message", additional_value)

# 致命
Fatal(ErrorCode.APPLICATION_ERROR, "fatal message")
Fatal([error1, error2])

# 警告
Warn(value, ErrorCode.OTHER, "warning message")
```

## 4. 禁止的模式

### 4.1 禁止抛出异常

```python
# 禁止
raise ValueError("...")
raise TypeError("...")
raise RuntimeError("...")
raise NotImplementedError("...")  # 用于接口定义时除外
```

### 4.2 禁止使用裸 Exception

`Exception` 存在是为了与外部库交互的兼容性，不应在业务代码中使用。

### 4.3 禁止在 Result 处理中抛异常

```python
# 禁止
match result:
    case Failed(error):
        raise RuntimeError(error.message)
```

## 5. 允许的例外情况

### 5.1 测试代码

测试代码中可以使用异常来：
- 模拟失败场景
- 断言预期行为
- 测试 stub 实现

```python
# 测试中允许
def method(self) -> Type:
    raise NotImplementedError("stub")
```

### 5.2 外部库交互

与不支持 Result 模式的外部库交互时，可以在边界处捕获异常并转换为 Result：

```python
def external_call() -> Ret[Response]:
    try:
        return Ok(external_library.do_something())
    except ExternalException as e:
        return Failed(ErrorCode.OTHER, f"External call failed: {e}")
```

### 5.3 协议边界不变量 / Protocol Boundary Invariants

以下场景因协议或不变量约束而保留 `raise`，不属于迁移范围：

- **迭代器协议**：`__next__()` 在 `StopIteration` 之外的错误仍应正常抛出。
- **上下文管理器协议**：`__enter__` / `__exit__` 中的异常应按标准 Python 协议传播。
- **值对象内部不变量**：数值类型的除零、溢出等在内部工厂返回 `Ret` 后的不可达路径中保留 `raise`，作为防御性断言。
- **数据类校验**：`__post_init__` 等校验在对象构造时运行，属于调用方契约违反的快速失败。

## 6. ErrorCode 扩展

当现有 ErrorCode 不足以表达错误类型时：

1. 首先检查是否可以复用现有 ErrorCode
2. 如果需要新的领域特定错误码，在相应模块定义扩展枚举
3. 确保错误码值不与现有 ErrorCode 冲突

## 7. 错误消息规范

- 使用简洁明了的中英双语消息
- 包含足够的上下文信息（如参数值、状态）
- 避免暴露内部实现细节
- 格式：`"操作失败：原因 / Operation failed: reason"`
