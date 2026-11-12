# ADR 0001：Python/Rust 绑定边界与发行政策

日期：2026-10-25。状态：作为迁移实施基准；能力验收状态见本地 logs/，不是本文件。

## 背景

Python 当前为独立实现，具有深层导入、三参数 Result、数值 Protocol、领域扩展点及多个 Python solver SDK。Rust 为多个 crate 的 workspace，核心模型和错误码与 Python 并非同构。

直接包装所有旧 Python 对象会保留双内核；直接原样暴露 Rust 类型又会丢失 Python 合同。采用独立绑定 crate 和薄公共门面。

## 确定的边界

1. 包名保持 `ospf-python` / `ospf_python`，私有扩展为 `ospf_python._native`。
2. Python 专用包装放在 Python 仓库的 `native/`，Rust 核心不引入 PyO3。
3. 核心能力最终由 Rust 唯一实现；Python 只保留门面、必要 DSL、类型和生态桥接。
4. 一个模型只有一份权威可变状态。Python 变量/表达式包装持 Rust 对象或稳定句柄，不保留平行可变模型。
5. package/subpackage 公开导出、文档与示例使用的路径优先兼容；深层路径在能力清单登记后逐项迁移，未审查前不删除。
6. 旧实现不能作为隐式 fallback。已迁移能力失败必须报告，不自动重新走 Python 内核。
7. 领域上下文、aggregation、model component 和 pipeline 仍负责建模；application 只负责编排。
8. 保留 Python extra context/pipeline/策略扩展能力；仅绑定固定 solve() 不构成领域替换完成。

## 版本与依赖来源

- 起始 Rust 源码固定为 `119854756a0aeb66d2998055f96fa7175c7bfb37`，远程仓库为 `https://github.com/fuookami/ospf-rust.git`。
- 绑定 manifest 使用完整 Git revision，不跟随 main，直至验证有可用于发行的 crate 版本。
- 本地可用不提交的 Cargo patch 联调相邻仓库；正式源码构建不得要求相邻目录存在。
- Rust 工具链起始固定为 `nightly-2026-08-01`。stable 及较新 nightly 不自动视为可构建，升级工具链必须重新验证。
- 锁定工具链与 Cargo.lock；构建信息反映源码 revision、feature 和目标，不读取运行时开发机 Git。
- PyO3/Maturin/NumPy 桥接版本在真实构建后锁定，不将开发环境“已安装的最新版本”直接作为兼容承诺。

## Gurobi 和其他后端

- 用户已确认以 Rust 支持范围为准：当前使用互斥的 `gurobi10`、`gurobi11`、`gurobi12`。
- 不为了旧 Python 的 gurobipy 13 要求增加 Rust Gurobi 13 支持；13 不属于本次迁移承诺。
- COPT/MindOPT 尚无已核对的 Rust 后端，作为显式缺口保留，不默默退役。
- 优先评估补通用 Rust 后端。若使用 Python SDK adapter，则消费新 Rust 模型的明确导出合同，不复用旧模型内核；采用哪种路径须在 P4 切换前验证。
- 真实 solver 的可用性必须分别验证编译支持、本地库和许可证；没有执行的后端不能算通过。

## 默认分发策略

第一版基础 wheel **不编译实际 solver 后端**，支持基础数学与建模导入，不要求商业 SDK/许可证。该选择降低 wheel 的动态库与许可证耦合，不代表放弃真实求解。

- 实际 Rust 后端先提供固定 feature 的源码构建流程；SCIP 是第一个真实闭环候选。
- Gurobi 构建必须显式选择一个版本 feature，不依赖 Rust 的 gurobi -> gurobi10 默认别名作自动探测。
- `pip extras` 不能切换已经编译的 Cargo feature，安装文档不得提供误导性命令。
- 不发布身份相同、仅隐藏 feature 不同的冲突 wheel；独立后端发行如有需求，另立稳定注册协议。
- 迁移期间尚未切换的旧 Python 后端可继续使用已有 SDK；依赖改为按需加载/可选依赖，不能以此声称其已被 Rust 接管。
- P2 退出需要一个真正的 Rust solver 闭环，只有基础无 solver wheel 不足以验收。

## 平台与 Python ABI

- 第一轮验收目标为标准 CPython 3.13、Windows x86_64 和 Linux x86_64。
- 初始使用解释器专用 wheel，不先引入 abi3、不宣称支持 free-threaded、多解释器或未验证的 Python 版本。
- 不在前期无依据收紧现有 Python >=3.13 元数据；发布前必须让声明范围与实际验证范围一致。P1 只把实测组合记为通过。
- Windows 当前机器的通过不能代替 Linux 通过；跨平台 job 未执行时保持待验证。
- sdist 必须在没有相邻 Rust checkout 的目录构建。固定 Git 来源的构建需要网络获取源码；离线可构建是独立要求。

## 数值、单位与错误

- 保留 `RealNumber` 等 Python Protocol 的自然名，但原生侧只接受已定义的数值域，不能动态实例化任意 Rust 泛型。
- 对当前已有整数、浮点、大整数、Decimal、有理数等使用情况逐项核对；未支持的域返回结构化失败，不静默降精度。
- f64 只用于首个求解原型和明确的 solver 边界，不定义整个框架的上限。
- 物理量在 Python 暴露运行时单位与量纲，集中换算和精度检查。不得复制旧 Quantity.to() 中的隐式 float 精度损失。
- Python `Result[T, C, E]` 保持三参数门面和 Ok/Failed/Fatal/Warn；不得改成 Union 或统一抛异常的 PyResult 公共 API。
- Python/Rust ErrorCode 的整数值不同。例如 Python APPLICATION_ERROR=1，Rust ApplicationError=0x31。按语义映射并保留来源信息，禁止直接数值强转。
- 现有 unwrap 等异常行为单独审计；新绑定不扩展错误处理规则的豁免。

## 已知待定事项与验收责任

| 待定项 | 负责阶段 | 要求 |
| --- | --- | --- |
| 每个深层公开路径的最终转发/调整 | P3/P4/P6 | 符号清单、迁移说明与回归测试，不得直接删除 |
| 任意 object 注册与新模型 API 的兼容 | P2/P4 | 区分元数据和可求解注册，明确可变快照/句柄政策 |
| COPT/MindOPT 实现路线 | P4 | 真实 SDK/许可验证；退役须用户确认 |
| Python callback 的重入与取消 | P2/P5 | 不持可重入模型锁调用 Python，明确事务及异常映射 |
| 各数值域及单位的完整绑定 | P3/P4 | 显式矩阵和精度边界，不能只实现 float |
| solver 打包与真实运行 | P2/P8 | 源码构建可运行、能力查询准确、平台本地库可定位 |
| 跨平台发布证据 | P1/P8 | 分别验证 Windows/Linux，不把本地证据推广到所有平台 |

这些待定项有明确的阶段与验收条件，不表示迁移完成；不得通过缩小范围或增加长期 legacy 开关规避。

## 范围清单与静态门禁

`docs/migration/api-map.toml` 是人工维护的能力归属与特殊符号合同。按最长命名空间前缀匹配，每个当前模块必须有归属。新包、错误引用、重叠定义和失效合同由以下门禁检查：

```powershell
python scripts/check_binding_migration.py --report logs/p0/api-map-report.json
python -m pytest tests/test_binding_migration_contracts.py
```

报告为每个静态候选符号保留文件、行号、签名、领域和当前状态；未单列合同的符号保持 inventoried，不自动升为 specified 或 verified。类字段、协议方法、特殊方法、条件声明和显式重导出都参与盘点。

这只是范围归属检查，不验证继承后的运行时表面、Rust 对应符号、方法行为或签名兼容，不证明绑定已经实现。动态导出另列 unresolved，不执行表达式。切换/删除时还需要对应能力的合同与真实运行测试；不能仅凭静态门禁绿灯进行删除。
