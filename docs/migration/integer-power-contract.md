# Integer Power / 整数幂

## Natural Entry Point / 自然入口

`ospf_python.math.ordinary.pow.pow_int(base, exp)` 返回既有三参数 Result。底数为
任意精度有符号整数，指数为非负整数，成功值为精确内置 int，含 `0**0 == 1`。
固定 revision 为 `119854756a0aeb66d2998055f96fa7175c7bfb37`，生产计算唯一调用
`ospf_rust_math::ordinary::powi::<BigInt>`，不保留 Python `**` / builtin pow
fallback，也不在绑定内复制快速幂。原八测试仅显式升级 Result 消费。

The public function is a source candidate until its actual validation, distribution,
complete-call budgets, resource contracts and promised platforms are evidenced.
It is not a declaration that all ordinary math, P3, or the full migration is complete.

## Full Integer Inputs / 完整整数输入

- 公开参数位置/关键字名 base/exp 保持，按 base 后 exp 对两个 SupportsIndex 各
  采集一次；即便底数是0/1/-1或指数0，也不跳过另一个输入协议。首错停止。
  bool 和真实 NumPy 整数可用，真 int 子类使用存储整数，原 __pow__/__int__
  覆盖不是新整数采集协议；不经 float/string 转换，不先窄化底数。
- 0/1/-1 的非负指数即使超过 u64 或有数千位，仍能返回其精确整数结果。绑定
  只对这些已证明的恒等域规范指数为0/1，最终数值仍交给固定上游 powi 生成。
  其它底数和可容纳指数直接交上游，不复制平方/连乘循环。
- 负指数不属于原声明的非负指数域，返回 ILLEGAL_ARGUMENT。旧 `int(base**exp)`
  对负指数可能先转float再截断，对float/其它可幂对象也可能偶然接受；这些需
  明示升级，不登记为精确整数幂应保留的数学语义。

## Resource Envelope / 资源包络

固定 generic powi 的指数参数为 u64，但底数可为 BigInt。对绝对值至少2的底数，
超u64指数至少需2 EiB的结果幅值存储；在当前宿主资源中不能据此生成结果。
绑定对此返回 RESOURCE_EXHAUSTED，不截断指数后给出另一个答案、不返回
NOT_SUPPORTED或回退Python，也不把0/±1的可实现巨大指数一并拒绝。
这不是无限资源的跨平台任意指数证明，未来宿主资源/指数核包络变化须重新验收。

对可交上游的调用，以 `base_bits * exponent + 1` 的u128结果幅值上界检查
地址可表示性并try_reserve字节容量。此检查不是求幂算法、物理内存预留保证或
沙箱；上游中间乘积、系统/并发OOM、进程终止仍不能保证恢复。没有任意的小
指数白名单或用户底数镜像。纯Rust计算释放GIL，前后检查信号；不宣称上游
连乘内部有及时取消回调。巨输出及长期资源合同独立于小输入正确性。

## Failures And Acceptance / 失败与验收

外部普通Exception保留原实例和traceback且不格式化：TypeError映射
ILLEGAL_ARGUMENT，MemoryError映射RESOURCE_EXHAUSTED，其余APPLICATION_ERROR。
BaseException按原实例传播。原生失败复用Failure和既有ErrorCode/ExErr/
FailureContext，零不被误当缺失结果。输入/输出和异常生命周期须独立验证。

最终应覆盖数学域差分、符号/零/大底数/巨大恒等指数、外部协议、资源边界，
完整默认回归和真实SCIP/Gurobi消费者；完整自然调用预算必须对照迁移前公开
入口而非只计原生循环。当前wheel/sdist仓库外locked构建/安装、平台/后端版本、
长期资源和完整预算按实际证据追踪；RG-008/RG-009、223单位/小数维度、数组及
其余P3-P9与最终旧内核删除要求不因本能力取消。
