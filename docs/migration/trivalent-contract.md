# Trivalent Logic / 三值逻辑

## Public Surfaces / 公开表面

`ospf_python.math.trivalent` 保留独立的 Trivalent 和 BalancedTrivalent 枚举，
六个自然函数 and_/or_/not_/balanced_and/balanced_or/balanced_not 显式返回既有
三参数 Result。`ospf_python.math.ordinary.trivalent.Trivalent` 仍是第三个不同
枚举，&/|/~及to_bool同样返回Result；链式逻辑须在每一步显式消费成功值。
普通枚举is_true/is_false/is_unknown仅检查成员身份，仍返回bool，不把Result
隐式当作真假。构造、枚举次序、名字/字符串value、repr/hash/copy/pickle路径
及三家族间不相等的身份保持，不合并同名类型、不引入平行结果或别名主类型。

All valid states, all 3x3 AND/OR pairs and all three NOT states are supported.
Balanced BALANCED maps losslessly to upstream Unknown and returns the original
Balanced singleton. Enum metadata stays in the thin Python facade; logical
evaluation is authoritative in the pinned Rust crate.

## Pinned Kernel / 固定内核

固定revision为119854756a0aeb66d2998055f96fa7175c7bfb37。上游Trivalent本体仅
提供转换，不直接实现位运算；绑定构建两个常量的BooleanExpression::and/or
或一个常量的not_expr，唯一调用公开evaluate_boolean和EmptyEvaluationContext。
to_bool也通过上游常量求值及Option<bool>转换。绑定只编码三个有限标签与操作
名，Python真值表/条件分支内核删除，没有Python fallback、绑定本地真值表、
只支持true/false的缩水域或持久计算结果缓存。小AST每次调用即创建/释放，
没有Python对象图保存在Rust中；不宣称分配失败均可恢复或该通道无GIL运行。

## Adapter Cost / 适配成本

当前成本候选在Python边界以三个成员的身份分支代替enumerate/生成器编码；
仍按left后right验证，非法输入仍不进入FFI。原生成功传输直接投影到原枚举成员
或bool/None，然后只创建一个既有Ok，不先创建传输值Ok再map为第二个Ok。
原生失败继续使用既有invoke映射；外部异常/BaseException的合同不变。
输出三标签仅为类型/表示投影，不是逻辑真值表或计算结果缓存；每次有效自然
调用仍实际抵达固定Rust求值。Rust数学/传输/登记、固定revision及ABI均不变。

This removes redundant Python allocation and encoding only. It does not declare
that complete-call budgets pass. Frozen v1 bindings and the original Python
kernel remain benchmark references in logs only, never production fallbacks.

## DTO / Copy / Pickle / 数据传输

三个公开枚举家族的 3 个状态均已在 Windows CPython 3.13 上覆盖 pickle
protocol 0 至 5，并验证 `loads(dumps(member)) is member`、
`copy.copy(member) is member` 与 `copy.deepcopy(member) is member`。
`value`、`name`、`str`、`repr`、hash 身份集合以及三个同名家族的独立性
同时固定；协议失败不会被改写为业务 `Result`。该证据只关闭 Windows
CPython 3.13 的 DTO/copy/pickle 合同，不宣称其它平台、性能、资源、
Linux、Gurobi 11/12 或整体切换已经完成。

## Invalid Inputs And Errors / 非法输入与失败

公开参数只接受原家族实际成员，以身份匹配，不触发外部eq/hash/bool/str/index
或repr。bool/string/普通整数/None、其它家族及伪造同类对象为ILLEGAL_ARGUMENT；
按left后right验证，即便左值在数学上有吸收效果，也不将非法右值吞成正确答案。
旧ordinary的宽松比较可能把非法对象偶然当unknown或被吸收，root字典可能抛
KeyError/TypeError，这些均显式升级为Result，不作为有效有限数学域的兼容行为。
未添加反向位运算或标准Enum构造的新协议；构造/赋值/反向运算仍遵循Python。

原生私有传输只接受真bool或None，None成功值明确表示unknown，不是失败哨兵。
未知操作、额外一元操作数、非法传输为结构化ILLEGAL_ARGUMENT。公开有效输入的
FFI普通Exception保留原实例和traceback，不格式化；MemoryError映射
RESOURCE_EXHAUSTED，其余异常映射APPLICATION_ERROR。BaseException原样传播。

## Acceptance / 验收

本包必须穷举三个家族全部真值和三元代数、枚举身份/序列化/非法输入/原异常，
升级实际消费者并验证真实SCIP/Gurobi10模型、默认/debug/完整回归与既有身份。
性能须对照冻结的迁移前自然入口，计入Result及unwrap和嵌套调用，不能只计
上游循环或挑选快场景。两feature wheel与同sdist仓库外locked四安装、完整
资源/平台/领域预算分别以实际证据验收；当前为specified源码候选，不等同
整体三值/符号表达式、P3或迁移完成。RG-008/RG-009、整数幂小输入预算、所有
既有预算/领域/平台、Linux/Gurobi11/12与P3-P9/最终旧内核删除要求继续保留。
