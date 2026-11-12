# Integer Number Theory / 整数数论

## Scope And Status / 范围与状态

本合同覆盖现有自然入口 `ordinary.gcd.gcd`、`ordinary.gcd.extended_gcd`、
`ordinary.lcm.lcm`、`ordinary.factorization.prime_factors` 与
`ordinary.prime.is_prime`，不是新增窄域旁路。
这些入口尚未绑定或切换到 Rust；有效整数域基线不代表已完成替换。固定 revision
为 `119854756a0aeb66d2998055f96fa7175c7bfb37`，完整直接替换受 RG-009 阻止。

No machine-word-only implementation, silent Python fallback or binding-local copy
of Euclid/trial division is accepted as the completed arbitrary-precision migration.
See [upstream gaps](rust-gaps.md) for the independent Rust failure contracts.

## Existing Valid Domain / 现有有效域

- `gcd` 与 `lcm` 接受任意精度有符号 Python 整数，输出非负内置整数；零及负数
  不能通过转无符号或缩窄机器整数悄悄改变。`gcd(0,0)=lcm(0,0)=0`。
- 两者的真实调用边界还接受 `__index__`，包括 bool 与真实 NumPy 整数；左、右
  顺序各采集一次，即使某一输入为零也不跳过另一输入协议。真实 int 子类使用
  存储整数，不允许其 `__index__` 覆盖伪造数值。现有 int 注解尚未完整表达此边界。
- `extended_gcd` 在非负任意精度域返回 `(g,x,y)`，满足 `g=gcd(a,b)` 与
  `a*x+b*y=g`。一般系数不唯一，不能把另一正确系数对误判为回归；正数与零的
  已有独立断言仍保留。旧实现的递归深度限制不是应保留的正确数学语义。
- `prime_factors` 在正整数域返回有序、重复的内置素因子列表，乘积等于原数；
  1 对应空列表。`2**4096` 等大而光滑的值在现实现中可行，不能仅因大于 u64
  就将它们排除，也不能将上游的 `(prime,exponent)` DTO 当作已兼容的最终列表。
- `is_prime` 的注解为 `int`，实际基线对任意精度整数执行精确比较和取模：
  负数返回 `False`，超出 u64 的合数仍可判断（审计实测 `2**64+1 -> False`），
  输出为内建 `bool`。当前实现没有显式整数守卫，因此浮点 `5.0` 也会返回
  `True`；这是待升级的历史观测，不是承诺输入域，也不能成为最终绑定的窄域借口。

The baseline includes signed machine boundaries, wider 128/1024/2048-bit inputs,
fixed-seed pairs, positive Bézout identities, index order and ownership release.
Factor expansion is an output representation obligation, not permission to replace
the upstream factorization kernel inside a Python adapter.

## Observations Requiring Explicit Migration / 需明确升级的历史行为

旧 `extended_gcd` 不走 `__index__`，直接递归 `%`、`//` 和算术；负输入可能返回
负 g，非整数也可能偶然被接受。旧 `prime_factors` 对零/负数返回空列表，并可能
对 float 发布非整数“因子”。这些作为历史观测保留，不登记为正确整数数学承诺。
未来须显式说明整数采集、负 g 规范化、非法分解输入和开放协议处置；不能仅用
已有少量正数测试为缩窄、静默舍入或额外 Python 算法背书。

目前四函数仍返回原始值并可能抛外部异常。目标业务入口应统一使用既有 Result/
ErrorCode/ExErr，而非新增平行错误体系。迁移时同步升级真实调用方及类型注解，
普通外部 Exception 保留原对象和 traceback，BaseException 按原对象传播，不在
错误处理中格式化用户异常。方括号赋值的政策缺口不适用于这些命名数论函数。

## Pinned Rust Capability / 固定 Rust 能力

普通模块的 gcd 导出为 usize/u64/i64，extended_gcd 仅 i64，lcm 为同样的固定
宽度，factorize 导出固定宽度及指数对。BigInt 在其他数值模块可用，不等于这些
普通函数已提供任意精度实现；不能凭 num-rational 内部的 gcd 推断扩展系数或
任意精度分解已经可绑定。`is_prime` 导出为 `usize`，另有一个 `u64` 包装入口；
两者都没有负整数或超过 64 位的表示，不能覆盖现有 Python 输入域。

独立 debug/release 探针复用生产依赖、lock 和固定 Git revision，并在编译时
核对真实函数签名。i64::MIN 的 gcd/extended/factorize、接近上界的 lcm 可触发
panic，或在 release 返回负数/回绕/空列表；MIN 与 -1 的扩展 gcd 两构建均 panic。
有效小整数与有界光滑分解则由 Python 独立数学核对，不能将缺口泛化为整个库错误。

## Required Cutover / 切换要求

1. 固定上游或经授权审查的新 revision 提供完整整数域能力及受检边界，包括
   `is_prime` 的任意精度输入；生产绑定不使用 catch_unwind 修复数学，
   不截断/取模/饱和，也不将只支持 u64 当完整替代。
2. 保持现有自然入口、完整宽度/符号/零/协议与原异常合同；真实删除被接管的旧
   递归、试除循环及 stdlib 内核依赖，不保留生产 fallback。
3. 同步 Result 消费、数值域差分/性质、巨大光滑值与连续调用释放；困难素数的
   时间和取消属于资源合同，不能用一次小整数正确性认证全部输入资源。
4. 完成完整自然调用预算、代表性后端消费者、当前 wheel/sdist 仓库外 locked
   构建/安装及承诺平台验证；合同基线或纯 Rust 探针不替代这些验收。

RG-009 不取消其余 P3–P9、RG-008、223 单位、小数维度、数组权威、领域/平台与
最终旧内核删除要求，也不意味着其他可推进能力已整体被阻塞。
