# Quantity Snapshots / 数量快照

This is an implemented source candidate, not full Quantity cutover acceptance.
固定远程 Rust revision 不变；schema、生命周期、发行和实际结果以 logs 主计划为准。

## Copy And Pickle / 复制与 Pickle

- 原生 `_QuantityUnit` 和 `Rational` 的 copy/deepcopy 克隆固定 Rust 数据；没有
  Python 系数镜像、实例缓存或第二套数学。普通 Quantity 仍为 value/unit 两字段
  frozen Generic dataclass。Python copy memo 和 pickle graph memo 管理共享引用。
- 所有标准 pickle 协议通过既有版本化 Rust JSON 编码/验证恢复原生对象。既有
  Python 门面/子类和开放值遵循标准 Python pickle，不能自动持久化不可 pickle
  的用户类、局部 callable 或运行中的 solver。
- 私有 pickle 恢复入口必须返回真实原生对象；损坏快照以 ValueError 终止该协议，
  不把 Failed 或二元传输当作单位。公开 Unit.from_json/Rational.from_json 保持
  原 Result，不因 pickle 扩展改变正常错误政策。
- Unit 仍采用既有身份相等政策，复制/恢复不保证相同对象身份或 Quantity 的身份
  单位相等；完整 descriptor 往返及 same_unit 才是其数学/元数据比较。旧家族的
  字段相等、Quantity 泛型字段、METER 等普通 DTO 政策保持，不建立隐蔽 intern 缓存。
- pickle 仅适用于受信任数据。跨语言或不受信任输入使用下面的纯数据 DTO，不把
  pickle 内容、模块名或 callable 放入 DTO。

## Natural DTO API / 自然 DTO API

Quantity.to_dict/to_json/from_dict/from_json 显式返回现有三参数 Result；失败保留
原始 Exception/traceback、失败回调 Result，BaseException 继续传播。

```python
import pickle
from fractions import Fraction
from ospf_python.quantities import Quantity
from ospf_python.quantities.unit.temperature import CELSIUS

difference = Quantity(value=Fraction(80), unit=CELSIUS).subtract(
    Quantity(value=Fraction(20), unit=CELSIUS)
).unwrap()
restored = Quantity.from_json(difference.to_json().unwrap()).unwrap()
assert restored.value == Fraction(60)
assert restored.unit.descriptor() == difference.unit.descriptor()
assert not restored.unit.is_affine
assert restored.divide(Fraction(4)).unwrap().value == 15
copied = pickle.loads(pickle.dumps(restored))
assert copied.unit.descriptor() == restored.unit.descriptor()
```

最外层只允许 schema="ospf.quantity", version=1, value, unit 四字段。拒绝重复
JSON 字段、非整数/未知 version、未知字段、非有限 JSON 数据和循环；from_dict
同样验证并复制所有数据，不信任 dict/list 子类的自定义遍历协议。输入和输出均
与 adapter 的可变数据分离，不能因之后修改调用方对象而改写已编码单位。

Numeric encodings are explicit: int uses canonical hexadecimal (no decimal-string
digit-limit dependency); finite float uses canonical float.hex preserving signed
zero and subnormals; Decimal uses its exact stored string, including signed zero,
trailing zeros and exponent, independently of the arithmetic context. Fraction,
public Rational and private Rational retain their distinct domain tags and use
the existing Rust rational wire encoding. Floating retains its actual int/float
payload rather than silently coercing it. bool is a separate tag, not int.

内置单位保留登记家族、原始 _factor/_offset 数值域和实际 Rust metadata；恢复只从
已经登记的33家族清单选择类型，不按 payload 中的字符串 import 或执行任意类。
字段重建后重新证明来源并核对完整 native descriptor，拒绝量纲/比例/offset/点差
身份冲突。native 输出单位恢复为同一单句柄公开 Unit；零 offset 仍为点，实际点
减点的线性差不会被错误重标为温度点。显示 symbol 不是量纲证据。

已登记家族若因固定 Rust 的精度缺口不能创建忠实原生单位，DTO 明确用 native=null
只存档原始带类型字段，绝不写入舍入后的假原生 metadata。解码必须重新证明该
原始字段确实触发 DATA_LOSS；不能把有效单位任意标成 null。恢复的是原家族数据，
其后公开计算仍失败 DATA_LOSS，没有 Python 数学 fallback。原子质量常量的字段
往返不等于其数学已切换，既有八项 RG-008 红灯保持真实失败。

dataclasses.asdict 仍是 Python 对象图，可能包含独立 native handle，不宣称是
可 JSON 编码的 DTO。to_dict 才是版本化、无原生句柄/内存地址的显式纯数据边界。
DTO 不自动恢复用户数量子类；调用 Derived.from_dict 由调用者显式选择当前工厂，
避免执行 wire 指定的代码。工厂回调的真实输出保留，不谎称必然为 Quantity。

## Open Data Policies / 开放数据策略

公开泛型 SnapshotAdapter[V] 提供 to_snapshot/from_snapshot，均返回 Result。
value_adapter 和 unit_adapter 独立、keyword-only；只有显式 custom tag 才调用
恢复策略，没有自动推测 Python 类型或 float 转换。策略可以保留非数值开放数据，
与用于精确数学的 NumericAdapter 不同，不强迫任意用户对象先变为 Fraction。

- 编码先捕获并完成单位快照，再读取/编码 value。单位 adapter 和数值 adapter
  各调用一次，不保存 callable、实例、类或策略到 wire，不跨调用缓存状态。
- 解码先复制完整输入并验证单位，再恢复 value，最后调用已选择的类工厂。
  adapter 的返回 JSON 数据被验证并复制；Ok(None) 是合法 payload/对象，不是
  失败标记。非 JSON 对象需要策略明确转为数据，不能把 Result 当作 JSON 控制对象。
- custom 恢复缺少相应 adapter 时明确 NOT_SUPPORTED。不静默猜测内置类型，
  不从未声明的 pickle、Python expression 或模块路径自动恢复对象。
- 普通 Exception 保留原实例，不在处理错误时格式化用户异常；中断不吞掉。
  adapter Failed/Fatal 等保留原 Result 的上下文，不把失败当作成功的数据。

## Remaining Acceptance / 剩余验收

永久矩阵已覆盖七域上的四则实际输出 × copy/deepcopy/pickle protocol 0至5，
验证结果域、unit descriptor、JSON DTO及换算；仍须持续覆盖33家族/223常量、
真实温差输出、极值/范围/后续四则、复制图共享、巨大整数/系数、Decimal 表示、
原异常/中断、schema 攻击、重入/线程及释放，并通过当前隔离安装和真实 solver
消费者。

序列化不得被用来宣称 RG-008 数学缺口已修复，也不代替原生输出所有后续算术、
完整调用性能/资源、Linux/Gurobi11/12、完整领域及 P3-P9/最终旧内核删除要求。
