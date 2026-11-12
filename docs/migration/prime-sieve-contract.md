# Prime Sieve / 素数筛

## Natural Entry Point / 自然入口

`ospf_python.math.ordinary.prime.primes_up_to` 返回既有三参数 Result，成功值为包含
上界 n 的递增内置 int 列表。调用方由 `primes_up_to(n)` 显式升级为 Result 消费，
不能忽略失败或把 Result 当列表。未切换的 is_prime/nth_prime 不受此返回升级影响。

本候选直接调用固定 revision `119854756a0aeb66d2998055f96fa7175c7bfb37` 的
`ospf_rust_math::ordinary::get_primes`；Python 旧筛法已从该函数移除，绑定不实现
第二套筛或在失败后回退 Python。其它函数的试除循环不是本筛的生产 fallback。
源码接通不等于当前发行、资源、完整预算及平台门槛均已验收；登记保持 specified。

The returned list is detached from the sole upstream process-global prime cache.
Mutating a prior result cannot change later queries. The Rust cache retains its
largest sieve and prime vector for process lifetime; this is deliberate upstream
state, not a second Python mirror, an evictable cache, or a constant-memory claim.

## Integer And Error Boundary / 整数与错误边界

- 公开边界对 SupportsIndex 调用一次 operator.index；bool/NumPy 真整数可用，
  真 int 子类采用存储整数，不调用其覆盖。只提供比较/算术而不提供 __index__ 的
  对象、float/string 偶然被旧实现接受，不作为声明整数域承诺继续保留。
- 所有负整数（包括超机器字）及 0/1 得空列表；负值规范为上游的空范围，而非
  取无符号回绕。正上界不能截断或取模，也不只批准小于某常量的子集。
- 原筛同样需要可寻址的 `n+1` 个槽。绑定先检查旧指针列表的容量可表示性并
  try_reserve 同一字节预算；不能表示或预留返回 RESOURCE_EXHAUSTED。此检查
  不构造筛、不计算素数，也不保证系统/并发 OOM 可以恢复，不是内存沙箱。
- 已采集 exact int 才进入私有 native 边界；原始 __index__ 不被二次执行。
  原生计算和缓存 mutex 等待释放 GIL，检查信号在计算前后。固定筛内无协作取消
  回调，不能宣称其任意长调用都能及时取消。
- 外部普通 Exception 保留同一个对象及 traceback，不调用其 __str__；TypeError
  映射 ILLEGAL_ARGUMENT、MemoryError 映射 RESOURCE_EXHAUSTED，其余为
  APPLICATION_ERROR。BaseException 不吞并，原样传播。原生失败复用 Failure
  与既有 ErrorCode/ExErr/FailureContext，不建立第二套 Result。

## Cutover Gates / 切换门槛

原测试仅四项显式升级 unwrap 消费，其余 is_prime/nth_prime 合同保留。新增合同
核对小范围独立数学、已知大范围计数、缓存扩展、并发、独立输出、完整负整数域、
输入协议及原异常。**仓库外 wheel/sdist locked 安装已验收（2026-10-30，
`logs/p3/primes-distribution/`）**：solver-enabled wheel 与 sdist 在 `D:\temp` 的全新 venv 中
安装/重建后，`primes_up_to` 在 1e5/1e6/1e7 上分别得到 9 592/78 498/664 579 个素数，
首末项与独立锚点一致；进程峰值工作集增量为 1.5–1.7 / 12.9–13.8 / 112.1–112.5 MiB，
其中 1e7 时 22.8 MiB 是返回的内置 int 列表（不是常量内存声明）。完整回归、真实
SCIP/Gurobi 消费者、Linux 与 Gurobi 11/12 仍须按实际证据验收。
合同中的 `current-source-and-isolated-wheel-sdist-validation` 已由这份当前扩展哈希
对应的隔离构建/安装证据收敛；其余 pending 门槛不随之关闭。

**当前扩展复测（2026-10-30，`logs/p3/primes-current-revalidation/`，SHA-256
`3469a86853febbaf207a9f6edeeac8cf39c9303f6688e376166da3d3d66153f0`）**：
两轮完整自然调用中，1 万与 100 万的冷/热档都通过 1.15；只有 `limit=100` 冷启动
仍为 **2.497×/2.729×**（独立 gate 为 2.807×）。3 个独立生命周期进程都显示
1e3→2e6 的私有内存约 23.4–23.5→33.95–34.09 MiB，之后 1000 次小上界调用不再增长，
GC 后增量为 0；但紧跟 2e6 调用的小查询中位仍为 10.15–19.45 µs，而连续小调用稳态为
2.50–2.60 µs，故缓存资源平稳通过、交互延迟仍未关闭。
本能力不解决 RG-009 的任意精度判断/分解或其余数论入口，不改 Rust revision，
不放宽 Quantity、数组、全领域/平台、P3-P9 与旧内核删除要求。
