# 项目规范

## 1. 编码风格

### 1.1 注释语言
编写注释时，要中英双语。

### 1.2 版权声明
不需要添加版权声明。

### 1.3 ReadMe 文件
英文 ReadMe：README.md，中文 ReadMe：README_ch.md，要添加超链接能互相跳转。

### 1.4 Shell 工具
PowerShell 用：pwsh.exe。

### 1.5 函数签名规范
超过 2 个参数时，使用 keyword-only 参数（强制命名传递）。

```python
# 正确
def create_material(
    *,
    code: str,
    name: str,
    status: MaterialStatus = MaterialStatus.Active,
) -> Material:
    ...

# 错误：位置参数过多
def create_material(code, name, status):
    ...
```

### 1.6 Python 文件排版与 import 规范

本节约束 Python 源文件的基础排版风格。

#### 1.6.1 文件整体结构

文件各部分的排列顺序和间距必须遵循以下规范：

1. 模块级 docstring 放在文件最开头。
2. `from __future__ import annotations`（若使用）紧随其后。
3. 所有 `import` 语句位于 docstring 之后、顶层声明之前。
4. 最后一个 `import` 语句与首个顶层声明之间必须有且仅有一个空行。
5. 文件末尾必须有且仅有一个换行符。

#### 1.6.2 import 排列

**整体顺序**（各组之间用一个空行分隔）：

1. **标准库**（`os`、`sys`、`datetime`、`typing`、`enum`、`pathlib` 等）
2. **第三方库**（`numpy`、`pydantic`、`returns` 等）
3. **本项目内部模块**（`ospf_python.*`），按以下层级从底层到上层排列：
   - `ospf_python.utils.*`（基础工具）
   - `ospf_python.multiarray.*`（多维数组）
   - `ospf_python.math.*`（数学库）
   - `ospf_python.quantities.*`（物理量）
   - `ospf_python.core.*`（优化核心）
   - `ospf_python.framework.*`（应用框架）
   - `ospf_python.framework.<domain>.infrastructure.*`（领域基础设施）
   - `ospf_python.framework.<domain>.domain.*`（领域模型与服务）
   - `ospf_python.framework.<domain>.application.*`（应用服务）

**排列规则**：

1. 同组内 import 按模块名字典序升序排列。
2. 优先使用绝对导入（absolute import），禁止隐式相对导入。
3. 同一模块内的多个导入允许合并（但避免过多通配符 `*` 导入）。
4. 禁止未使用的 import。

**正确示例**：

```python
from __future__ import annotations

import enum
from typing import TypeVar

from ospf_python.utils.error import ErrorCode
from ospf_python.utils.functional import Result, Ok, Failed
from ospf_python.math.algebra.number import RealNumber
from ospf_python.core.variable import LinearVariable
from ospf_python.framework.bpp3d.infrastructure import Bpp3dContext
from ospf_python.framework.bpp3d.domain.item.model import Item
```

#### 1.6.3 缩进、空行与行宽

**基础规则**：

- 使用 4 空格缩进，不使用 tab。
- 行宽上限 88 字符（与 Black 默认一致）。
- 顶层声明之间保留两个空行。
- 类内方法之间保留一个空行。
- 类定义结束前不保留多余空行。

**函数声明与调用**：

- 1-2 个参数且语义简单时可单行书写。
- 超过 2 个参数时，按 `1.5 函数签名规范` 使用多行和 keyword-only 参数。
- 多行参数列表中，参数缩进一层；闭合括号与 `def` 或调用起始位置对齐或缩进一层。

```python
def create(
    *,
    code: str,
    name: str,
    status: MaterialStatus = MaterialStatus.Active,
) -> Material:
    ...
```

#### 1.6.4 注释与分段

- 公共类、接口、重要公共方法使用中文 docstring（Google 风格）。
- 简短属性可使用单行 docstring，如 `"""是否已加载用户组引用。"""`。
- 服务和仓储内部允许使用 `# ==================== 查询 ====================` 形式分段。
- 注释应说明业务意图、加载态语义或分段边界；避免重复描述代码本身。

#### 1.6.5 Docstring 标签与覆盖要求

**标签规范（Google 风格）**：

- 公共类必须在 docstring 中说明属性（语义明显者如 `id: int` 可省略）。
- 公共函数必须使用 `Args:` 标注每个参数，使用 `Returns:` 标注返回值（返回 `None` 或语义自明时可省略 `Returns:`）。
- 泛型类型参数语义非常规时在 docstring 中说明。
- 单行 docstring（仅一句话、无标签需求）仍然允许。

**覆盖要求**：

- 每个重载（`@overload`）都必须有独立的 docstring 或 type hint 注释。
- 每个 `TypeAlias` 都必须有独立的文档说明（允许单行注释）。

### 1.7 泛型化命名规范

对外 API 使用业务自然名表达稳定抽象，不使用迁移期技术命名。

- 泛型化后的主接口、主模型、主服务占用自然名。
- 不使用 `V`、`Typed`、`Generic` 作为迁移痕迹型前后缀。
- 需要保留的 `float` 专用接口、桥接接口或兼容入口，使用 `Float64` 后缀显式标识。
- `TypedValueRange`、`ClosedTypedValueRange`、`TypedPathBuilder` 等本身表达类型级抽象的稳定概念可以保留 `Typed`。
- 内部变量、测试名、文档示例应尽量同步上述命名，避免保留迁移期表达。
