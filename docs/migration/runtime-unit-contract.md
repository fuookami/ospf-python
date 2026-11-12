# Native Runtime Unit / 原生运行时单位

`ospf_python.quantities.Unit` 与 `ospf_python.quantities.unit.Unit` 是现有单句柄
Rust 门面的公共入口，不增加第二套单位实现。实例只有 `_handle`，指向真实
`_QuantityUnit`；name/symbol/powers/is_affine/descriptor 从原生读取，不缓存
Python 比例、偏移、维度或数值镜像。固定远程 Rust revision 不变。

These exports alias the existing single-handle facade. This is the output-unit
prerequisite for checked arithmetic, not completed default-operator replacement.

## Construction And Consumption / 创建与消费

使用 Unit.create(name=..., symbol=..., powers=..., scale=1, offset=None)，显式
消费 Result。powers 为现有十个整数指数，系数精度政策与原生底座相同。None offset
为线性差；含零的 offset 是 affine 点。不靠 symbol 猜量纲，也不以零offset的
Temperature点代替温差。

```python
from fractions import Fraction

from ospf_python.quantities import Quantity, Unit

powers = (0, 0, 0, 0, 1, 0, 0, 0, 0, 0)
point = Unit.create(name="point", symbol="P", powers=powers, offset=273).unwrap()
value, difference = point.binary_exact(
    value=80, other=20, other_unit=point, subtract=True
).unwrap()
assert difference.is_affine is False
target = Unit.create(name="difference", symbol="dK", powers=powers).unwrap()
quantity = Quantity(value=Fraction(*value.as_integer_ratio()), unit=difference)
assert quantity.to(target).unwrap().value == 60
```

binary_exact 调用固定 Rust Quantity.checked_add/sub 产生实际输出单位，不在Python
补算温差或伪造同名单位。它仍是低层精确值/单位tuple入口，不是自然Quantity四则。
完整要求见[四则合同](quantity-arithmetic-contract.md)。新Unit接入Quantity.to、
min/max、范围和时长，工厂不会收到私有SI token或未消费的Result代替数值。

## Direct SI Methods / 直接 SI 方法

Unit.to_si(value)/from_si(value) 返回现有Result，共用数值导入/出口与原生控制面，
不执行Python单位公式、不强制float。直接方法使用当前Decimal context/exact=True；
显式context/exact/NumericAdapter经Quantity.to指定。SI标准单位保留affine身份，
零offset不会将点变为差。

开放PhysicalUnit仍可返回不透明数据/Result。未扩展的真实Unit被识别时，派发器
调用既有原生转换，不将其直接方法的Result误作opaque SI数据。类、方法/code/
defaults、__getattribute__或句柄槽descriptor扩展时保留开放协议，不预读动态属性。

## Provenance And Point Semantics / 来源与点差

- 原33家族表不变。Unit另存原类/方法/槽身份，不记录实例或假造静态powers；实际
  维度和affine状态来自经过类型检查的原生句柄。
- 类型在模块加载时捕获，不信任可替换的_native._QuantityUnit别名。非法_handle
  不能以descriptor鸭子类型伪造来源，调用返回输入失败。
- 源在adapter导入前保活本次实际原生句柄；输入门面被重写不改写已采集源。没有
  跨调用owner/value/unit缓存，目标仍遵循既有迟绑定。
- 已知点与差不能通过普通Quantity.to或比较混用。比较会在本次调用记住已见类型，
  opaque获胜者不能吞掉先前证明。未知开放单位不获得假的维度/点证明。
- 线性时间单位可转timedelta；已知非时间或affine时间点不能冒充时长。
- 低层Unit.convert_exact/convert_float64等保留固定Rust合同；公开Quantity的点/差
  政策在其边界单独校验，不将两个API混淆。

原Exception/traceback/cause/context及BaseException政策延续现有边界。直接SI的
普通外部异常保留原实例，不格式化、不吞中断。adapter仅最终出口重建一次，比较/
时长不重建数值时只导入，不调用出口。

## Remaining Gates / 尚未完成

源码集成不等于Quantity verified/switched。永久合同、原用例身份、真实热资源MILP、
当前wheel/同sdist安装及完整调用预算实际结果见logs主计划；未执行的平台和
Gurobi11/12不算通过。

支持版本化to_json/from_json。公共运行时Unit本体已覆盖linear、affine点和真实
native输出温差的copy/deepcopy及pickle protocol 0至5：结果保持类型、descriptor、
JSON DTO、powers与affine身份；浅拷贝共享不可变原生句柄，深拷贝和pickle重建
独立句柄，既有`eq=False`身份相等语义不变。该永久合同只认证运行时Unit本体，
不以普通METER或223个旧系数常量代替。Quantity的显式版本化DTO、身份相等与
DATA_LOSS原字段存档政策见[数量快照合同](quantity-snapshot-contract.md)。

自然四则/混合域、温差高层创建与生命周期、小数维度、RG-008八真实失败、223单位
完整切换、全部既有预算/领域/平台、P3-P9与旧内核删除仍为完整必需目标。上述
DTO通过不改变既有数学/性能红灯，最终验收及仍未执行的平台/领域以logs主计划为准。
