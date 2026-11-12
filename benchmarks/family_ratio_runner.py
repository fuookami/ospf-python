"""族级比值门禁（通用 runner）：同一族在"切换前基线树"与"当前树"上的调用成本比。

Family ratio gate: measures one family's call cost on a baseline tree (an archived
pre-cutover package) and on the current tree, in separate child processes, and
compares medians. Ratio > 1 means the current implementation is slower.

设计要点 / Design:
  * 两侧各起子进程，避免一边的 import 缓存/模块状态影响另一边；
  * 交替轮次（先天平后基线，再反过来），抑制机器状态漂移；
  * 判定用**中位比值**，阈值与已有门禁一致（`<= 1.15` 记为通过）；
  * `--smoke` 明确标注"只验证机制、不构成验收"。

用法 / Usage:
  python benchmarks/family_ratio_runner.py --policy <policy.json> --baseline-tree <dir>
      --rounds 3 --output report.json [--smoke]
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import textwrap
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SELF_CHECK_TOLERANCE = 0.25
"""自检允许的最大偏离。 / Maximum deviation allowed by the self-check."""

CHILD = textwrap.dedent(
    '''
    """子进程：对一个族执行 case 并输出计时 JSON。 / Child: time one family's case.

    支持两种调用形式：
      * 普通形式：`module` + `attrs` + `args`（参数必须 JSON 可序列化）；
      * 构造器形式：`builder`（在 `BUILDERS` 中注册，用于枚举、数组等无法 JSON 化的参数）。
    两种形式都在**各自的树**里导入，保证两侧比较的是同一段调用语义。
    """
    import json, os, sys, time
    sys.path.insert(0, sys.argv[1])
    # 新 pin 下 `_native` 动态链接 libscip.dll / gurobi100.dll，而 Python 3.8+
    # 不从 PATH 搜索扩展模块的 DLL 依赖，必须显式注册目录。
    # Under the new pin `_native` links libscip/gurobi dynamically; Python 3.8+ does not
    # search PATH for extension DLL dependencies, so register them explicitly.
    if os.name == "nt":
        _handles = [
            os.add_dll_directory(_d)
            for _d in os.environ.get("OSPF_NATIVE_DLL_DIRS", "").split(os.pathsep)
            if _d and os.path.isdir(_d)
        ]
    payload = json.loads(sys.argv[2])


    def resolve(module_name, attrs):
        module = __import__(module_name, fromlist=["_"])
        for attr in attrs:
            if hasattr(module, attr):
                return getattr(module, attr)
        return None


    def _dto_fixtures():
        """DTO 构造用例需要的小夹具；按名字在 params.kwargs 里引用。

        Fixtures for DTO-construction cases, referenced by name from params.kwargs.
        """
        from ospf_python._binding.bpp1d import VariableRef
        from ospf_python._binding.quantities import Unit

        return {
            "unit": Unit.create(
                name="length",
                symbol="m",
                powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0),
            ).unwrap(),
            "ref": VariableRef(model_identity=1),
        }

    def build_dto(module_name, params):
        """构造一个 DTO：`attrs` 给类名，`kwargs` 里字符串若命中夹具名则替换为夹具。

        Construct one DTO: `attrs` names the class; string kwargs that match a fixture
        name are replaced by that fixture.
        """
        target = resolve(module_name, params["attrs"])
        fixtures = _dto_fixtures()
        raw = dict(params.get("kwargs", {}))
        kwargs = {
            key: fixtures[value]
            if isinstance(value, str) and value in fixtures
            else value
            for key, value in raw.items()
        }
        return lambda: target(**kwargs)

    def build_trivalent_and(module_name, params):
        module = __import__(module_name, fromlist=["_"])
        enum = module.Trivalent
        members = {"UNKNOWN": enum.UNKNOWN, "TRUE": enum.TRUE, "FALSE": enum.FALSE}
        target = module.and_
        left, right = members[params["left"]], members[params["right"]]
        return lambda: target(left, right)


    def build_fractal_iterate(module_name, params):
        module = __import__(module_name, fromlist=["_"])
        set_type = module.MandelbrotSet
        point = complex(float(params["real"]), float(params["imag"]))
        limit = int(params["limit"])
        return lambda: set_type.iterate(point, limit)


    def build_fractal_contains(module_name, params):
        module = __import__(module_name, fromlist=["_"])
        instance = module.MandelbrotSet()
        point = complex(float(params["real"]), float(params["imag"]))
        return lambda: instance.contains(point)


    def build_multiarray_map(module_name, params):
        import numpy as np
        from ospf_python.multiarray import DynShape, MultiArray, StorageOrder

        order = getattr(StorageOrder, params["order"])
        data = np.arange(int(params["count"]), dtype=np.int16)
        shape = DynShape(tuple(params["dims"]), order)
        array = MultiArray(shape, data)
        delta = int(params.get("delta", 1))
        return lambda: array.map(lambda value: value + delta)


    def _binding_array(params):
        """构造 `_binding.multiarray.MultiArray`（门禁只测绑定层自身方法）。"""
        from ospf_python._binding.multiarray import MultiArray
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        dims = tuple(int(v) for v in params["dims"])
        order = getattr(StorageOrder, params.get("order", "ROW_MAJOR"))
        total = 1
        for v in dims:
            total *= v
        data = [
            [index for index in row]
            for row in _nest(range(total), dims)
        ]
        shape = DynShape(dims, order)
        return MultiArray.from_list(data=data, shape=shape).unwrap()


    def _nest(values, dims):
        """把扁平序列折成 dims 指定的嵌套 list。"""
        if len(dims) == 1:
            return list(values)
        step = 1
        for v in dims[1:]:
            step *= v
        return [_nest(values[i * step:(i + 1) * step], dims[1:]) for i in range(dims[0])]


    def build_binding_to_list(module_name, params):
        array = _binding_array(params)
        return lambda: array.to_list()


    def build_binding_transpose(module_name, params):
        array = _binding_array(params)
        return lambda: array.transpose()


    def build_binding_equals(module_name, params):
        array = _binding_array(params)
        return lambda: array.equals(array)


    def build_binding_describe(module_name, params):
        array = _binding_array(params)
        return lambda: array.describe()


    def build_binding_view(module_name, params):
        array = _binding_array(params)
        return lambda: array.view()


    def build_binding_iter_snapshot(module_name, params):
        array = _binding_array(params)
        return lambda: array.iter_snapshot()


    def build_binding_from_list(module_name, params):
        from ospf_python._binding.multiarray import MultiArray
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        dims = tuple(int(v) for v in params["dims"])
        order = getattr(StorageOrder, params.get("order", "ROW_MAJOR"))
        total = 1
        for v in dims:
            total *= v
        shape = DynShape(dims, order)
        data = _nest(range(total), dims)
        return lambda: MultiArray.from_list(data=data, shape=shape)


    def build_multiarray_reduce(module_name, params):
        import numpy as np
        from ospf_python.multiarray import DynShape, MultiArray, StorageOrder

        order = getattr(StorageOrder, params["order"])
        data = np.arange(int(params["count"]), dtype=np.int16)
        shape = DynShape(tuple(params["dims"]), order)
        array = MultiArray(shape, data)
        return lambda: array.reduce(lambda left, right: left + right)


    def build_mapped_materialize(module_name, params):
        import numpy as np
        from ospf_python.multiarray import (
            DynShape,
            MappedMultiArrayView,
            MultiArray,
            MultiArrayView,
            StorageOrder,
        )

        order = getattr(StorageOrder, params["order"])
        data = np.arange(int(params["count"]), dtype=np.int16)
        shape = DynShape(tuple(params["dims"]), order)
        source = MultiArray(shape, data)
        view = MultiArrayView(source, offsets=tuple(params["offsets"]))
        return lambda: MappedMultiArrayView(view, f=lambda value: value * 2).materialize()


    def build_julia_iterate(module_name, params):
        module = __import__(module_name, fromlist=["_"])
        z = complex(float(params["z_real"]), float(params["z_imag"]))
        c = complex(float(params["c_real"]), float(params["c_imag"]))
        limit = int(params["limit"])
        return lambda: module.JuliaSet.iterate(z, c, limit)


    def build_julia_contains(module_name, params):
        module = __import__(module_name, fromlist=["_"])
        instance = module.JuliaSet()
        return lambda: instance.contains(float(params["x"]), float(params["y"]))


    def build_trivalent_to_bool(module_name, params):
        from ospf_python.math.ordinary.trivalent import Trivalent

        member = getattr(Trivalent, params["value"])
        return lambda: member.to_bool()


    def build_duration_to_timedelta(module_name, params):
        from ospf_python.quantities.quantity.duration_extensions import (
            from_hours,
            to_timedelta,
        )

        quantity = from_hours(int(params["hours"]))
        quantity = quantity.unwrap() if hasattr(quantity, "unwrap") else quantity
        return lambda: to_timedelta(quantity)


    def build_quantity_add(module_name, params):
        from fractions import Fraction

        from ospf_python.quantities.quantity.quantity import Quantity
        from ospf_python.quantities.unit.amount import MOLE

        left = Quantity(Fraction(params["left"]), MOLE)
        right = Quantity(Fraction(params["right"]), MOLE)
        return lambda: left + right


    def build_attractor_call(module_name, params):
        import numpy as np

        module = __import__(module_name, fromlist=["_"])
        instance = module.BurkeShawAttractor()
        point = np.array(params["point"], dtype=np.float64)
        return lambda: instance(point)


    def build_unit_registry_family(module_name, params):
        # Family 是纯元数据 DTO。必须用 _binding.quantities.Unit：它是唯一带 _handle 且
        # 被 @register_runtime_unit 装饰的类型；quantities.unit.* 下的 Amount 没有 _handle，
        # 用它会让 register_runtime_unit 抛 KeyError 'to_si'。
        # Family is a pure metadata DTO. It must use _binding.quantities.Unit, the only type
        # carrying _handle and decorated with @register_runtime_unit; the Amount classes under
        # quantities.unit.* lack _handle and make register_runtime_unit raise KeyError 'to_si'.
        from ospf_python._binding.quantities import Unit
        from ospf_python._binding.unit_registry import Family

        namespace = vars(Unit)
        methods = {
            name: (namespace[name], namespace[name].__code__)
            for name in ("to_si", "from_si")
        }
        return lambda: Family(
            cls=Unit,
            powers=(0,) * 10,
            affine=False,
            methods=dict(methods),
            handle_descriptor=namespace["_handle"],
        )

    def build_unit_registry_runtime(module_name, params):
        from ospf_python._binding.quantities import Unit
        from ospf_python._binding.unit_registry import register_runtime_unit

        return lambda: register_runtime_unit(Unit)

    def build_unit_registry_family_register(module_name, params):
        from ospf_python._binding.quantities import Unit
        from ospf_python._binding.unit_registry import register_unit_family

        decorator = register_unit_family(powers=(0,) * 10, affine=False)
        return lambda: decorator(Unit)

    def build_unit_registry_native_family(module_name, params):
        from ospf_python._binding.quantities import Unit
        from ospf_python._binding.unit_registry import native_family

        unit = Unit.__new__(Unit)
        return lambda: native_family(unit=unit, callback=unit.to_si, direction="source")

    def build_unit_registry_arithmetic_family(module_name, params):
        from ospf_python._binding.quantities import Unit
        from ospf_python._binding.unit_registry import arithmetic_family

        unit = Unit.__new__(Unit)
        return lambda: arithmetic_family(unit)

    def _shared_array(module_name, params):
        """按 params 造一个共享数组 / Build one shared array from params."""
        import numpy as np

        from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        order = getattr(StorageOrder, params["order"])
        data = np.arange(int(params["count"]), dtype=np.int16)
        shape = DynShape(tuple(params["dims"]), order)
        cls = MutableMultiArray if params.get("mutable") else MultiArray
        return cls(shape, data)

    def build_public_array_read(module_name, params):
        from ospf_python._binding import public_array_access as access

        owner = _shared_array(module_name, params)
        indices = tuple(int(i) for i in params["indices"])
        return lambda: access.read(owner=owner, indices=indices, standard_layout=True)

    def build_public_array_write(module_name, params):
        from ospf_python._binding import public_array_access as access

        owner = _shared_array(module_name, params)
        indices = tuple(int(i) for i in params["indices"])
        value = int(params["value"])
        return lambda: access.write(
            owner=owner, indices=indices, value=value, standard_layout=True
        )

    def build_public_array_read_many(module_name, params):
        from ospf_python._binding import public_array_access as access

        owner = _shared_array(module_name, params)
        indices = [tuple(int(i) for i in pair) for pair in params["indices"]]
        return lambda: access.read_many(
            owner=owner, indices=indices, standard_layout=True
        )

    def build_public_array_raw_snapshot(module_name, params):
        import numpy as np

        from ospf_python._binding import public_array_access as access

        count = int(params["count"])
        data = np.arange(count, dtype=np.int16)
        return lambda: access.raw_snapshot(data=data, count=count)

    def build_storage_reshape(module_name, params):
        from ospf_python._binding.storage_transform import reshape_storage
        from ospf_python.multiarray.multi_array import MultiArray, _storage_constructor
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        order = getattr(StorageOrder, params["order"])
        owner = MultiArray(
            DynShape(tuple(params["dims"]), order),
            __import__("numpy").arange(int(params["count"]), dtype="int16"),
        )
        target = DynShape(tuple(params["target"]), order)
        return lambda: reshape_storage(
            owner=owner, target=target, precopy=False, resolve=_storage_constructor
        )

    def build_storage_flatten(module_name, params):
        from ospf_python._binding.storage_transform import flatten_storage
        from ospf_python.multiarray.multi_array import MultiArray, _storage_constructor
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        order = getattr(StorageOrder, params["order"])
        owner = MultiArray(
            DynShape(tuple(params["dims"]), order),
            __import__("numpy").arange(int(params["count"]), dtype="int16"),
        )
        return lambda: flatten_storage(owner, _storage_constructor, standard=True)

    def build_shared_view_materialize(module_name, params):
        from ospf_python._binding.shared_view import materialize_shared_view
        from ospf_python.multiarray.multi_array import MultiArray
        from ospf_python.multiarray.multi_array_view import (
            MultiArrayView,
            _materialized_constructor,
        )
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        order = getattr(StorageOrder, params["order"])
        source = MultiArray(
            DynShape(tuple(params["dims"]), order),
            __import__("numpy").arange(int(params["count"]), dtype="int16"),
        )
        view = MultiArrayView(source, offsets=tuple(int(o) for o in params["offsets"]))
        return lambda: materialize_shared_view(view, _materialized_constructor)

    def _trivalent_members():
        """`_binding.trivalent` 的成员元组（该模块不导出枚举，需本地造一个）。

        Members for `_binding.trivalent`; the module exports no enum, so build a local one.
        """
        import enum

        class Members(enum.Enum):
            UNKNOWN = 0
            TRUE = 1
            FALSE = 2

        return Members, (Members.UNKNOWN, Members.TRUE, Members.FALSE)

    def build_trivalent_logic(module_name, params):
        """`trivalent.logic(members, operation, left, right)`。"""
        from ospf_python._binding.trivalent import logic

        members_type, members = _trivalent_members()
        operation = str(params["operation"])
        left = getattr(members_type, str(params["left"]))
        right = getattr(members_type, params["right"]) if params.get("right") else None
        return lambda: logic(
            members=members, operation=operation, left=left, right=right
        )

    def build_trivalent_optional_bool(module_name, params):
        """`trivalent.optional_bool(members, owner)`。"""
        from ospf_python._binding.trivalent import optional_bool

        members_type, members = _trivalent_members()
        owner = getattr(members_type, str(params["owner"]))
        return lambda: optional_bool(members=members, owner=owner)

    def _binding_array_for(params):
        """构造 `_binding.multiarray.MultiArray`（与 `_binding_array` 同源，供新 builder 复用）。"""
        return _binding_array(params)

    def build_binding_map(module_name, params):
        """`MultiArray.map`——端到端穿过 `_binding.array_callback.map_callback`。"""
        array = _binding_array_for(params)
        return lambda: array.map(lambda value: value + 1)

    def build_binding_reduce(module_name, params):
        """`MultiArray.reduce`——端到端穿过 `_binding.array_callback.reduce_callback`。"""
        array = _binding_array_for(params)
        return lambda: array.reduce(lambda left, right: left + right)

    def _variable_handle():
        """建一个 MetaModel 并加一个变量，取它的 `VariableHandle`。

        Build a MetaModel with one variable and take its `VariableHandle`.
        """
        from ospf_python._binding.model import MetaModelFloat64, VariableSpec

        model = MetaModelFloat64.create("gate-dto").unwrap()
        handle = model.add_variables([VariableSpec(name="x", lower=0, upper=1)]).unwrap()[0]
        return model, handle

    def build_column_decision_spec(module_name, params):
        """`ColumnDecisionSpec` 需要 `_native.VariableHandle`，所以要真建一个模型。"""
        from ospf_python._binding.model import ColumnDecisionSpec

        model, handle = _variable_handle()
        spec = ColumnDecisionSpec(id="d", block="b", variable=handle)
        return lambda: (spec, model.close())

    def build_quantity_calculate(module_name, params):
        """`quantity_arithmetic.calculate`：两个 `Quantity` + 字面量 operation。"""
        from fractions import Fraction

        from ospf_python._binding.quantity_arithmetic import calculate
        from ospf_python.quantities import Quantity
        from ospf_python.quantities.unit.length import Length

        unit = Length("m", 1)
        owner = Quantity(Fraction(int(params["left"])), unit)
        other: Any = (
            Quantity(Fraction(int(params["right"])), unit)
            if params["operation"] in ("add", "subtract")
            else Fraction(int(params["right"]))
        )
        operation = str(params["operation"])
        return lambda: calculate(
            owner=owner,
            other=other,
            operation=operation,
            context=None,
            exact=True,
            numeric_adapter=None,
        )

    def build_convert_unit_value(module_name, params):
        """`unit_conversion.convert_unit_value`：`Unit.create` 造单位（需十个指数）。"""
        from ospf_python._binding.quantities import Unit
        from ospf_python._binding.unit_conversion import convert_unit_value

        powers = tuple(int(x) for x in params["powers"])
        unit = Unit.create(name=str(params["name"]), symbol=str(params["symbol"]), powers=powers).unwrap()
        value = params["value"]
        reverse = bool(params["reverse"])
        return lambda: convert_unit_value(unit=unit, value=value, reverse=reverse)

    def build_duration_from_value(module_name, params):
        """`quantity_duration.from_value`（context/numeric_adapter 传 None）。"""
        from ospf_python._binding.quantity_duration import from_value

        value = int(params["value"])
        factor = int(params["factor"])
        return lambda: from_value(
            value=value,
            factor=factor,
            context=None,
            exact=True,
            numeric_adapter=None,
        )

    def build_duration_to_timedelta(module_name, params):
        """`quantity_duration.to_timedelta`：先造一个 duration 再转换。"""
        from ospf_python._binding.quantity_duration import from_value, to_timedelta

        owner = from_value(
            value=int(params["value"]),
            factor=int(params["factor"]),
            context=None,
            exact=True,
            numeric_adapter=None,
        ).unwrap()
        return lambda: to_timedelta(owner=owner, numeric_adapter=None)

    def build_binding_iterator(module_name, params):
        """`MultiArray.iter_live()` 返回 `MultiArrayIterator`。"""
        array = _binding_array_for(params)
        return lambda: array.iter_live()

    def build_binding_mutable_view(module_name, params):
        """`MutableMultiArray.view()` 返回 `MutableMultiArrayView`。"""
        from ospf_python._binding.multiarray import MutableMultiArray
        from ospf_python.multiarray.shape import DynShape, Shape2, StorageOrder

        dims = tuple(int(v) for v in params["dims"])
        order = getattr(StorageOrder, params.get("order", "ROW_MAJOR"))
        rows = [[index for index in range(dims[1])] for _ in range(dims[0])]
        source = MutableMultiArray.from_list(
            data=rows, shape=DynShape(dims, order)
        ).unwrap()
        return lambda: source.view(
            offsets=(0, 0), shape=Shape2(int(params["view_dims"][0]), int(params["view_dims"][1]))
        )

    def build_shared_view_external_failure(module_name, params):
        from ospf_python._binding.shared_view import external_failure

        return lambda: external_failure(ValueError("benchmark failure"))

    def build_shared_mapping_map(module_name, params):
        from ospf_python._binding.shared_mapping import map_shared_array
        from ospf_python.multiarray.multi_array import MultiArray
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        order = getattr(StorageOrder, params["order"])
        owner = MultiArray(
            DynShape(tuple(params["dims"]), order),
            __import__("numpy").arange(int(params["count"]), dtype="int16"),
        )
        return lambda: map_shared_array(
            owner=owner,
            callback=lambda value: value + 1,
            flat=False,
            finish=lambda data: MultiArray(owner._shape, data),
        )

    def build_shared_nested(module_name, params):
        from ospf_python._binding.shared_nested import nested_shared_array
        from ospf_python.multiarray.multi_array import MultiArray
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        order = getattr(StorageOrder, params["order"])
        owner = MultiArray(
            DynShape(tuple(params["dims"]), order),
            __import__("numpy").arange(int(params["count"]), dtype="int16"),
        )
        return lambda: nested_shared_array(owner)

    def build_shared_reduction(module_name, params):
        from ospf_python._binding.shared_reduction import reduce_shared_array
        from ospf_python.multiarray.multi_array import MultiArray
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        order = getattr(StorageOrder, params["order"])
        owner = MultiArray(
            DynShape(tuple(params["dims"]), order),
            __import__("numpy").arange(int(params["count"]), dtype="int16"),
        )
        return lambda: reduce_shared_array(owner, lambda left, right: left + right)

    def build_shared_transpose(module_name, params):
        from ospf_python._binding.shared_transpose import transpose_shared_array
        from ospf_python.multiarray.multi_array import MultiArray
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        order = getattr(StorageOrder, params["order"])
        owner = MultiArray(
            DynShape(tuple(params["dims"]), order),
            __import__("numpy").arange(int(params["count"]), dtype="int16"),
        )
        return lambda: transpose_shared_array(
            owner=owner,
            precopy=False,
            finish=lambda shape, data: MultiArray(shape, data),
        )

    def build_coordinate_materialization(module_name, params):
        from ospf_python._binding.coordinate_materialization import (
            materialize_coordinates,
        )
        from ospf_python.multiarray.multi_array import MultiArray
        from ospf_python.multiarray.multi_array_view import (
            MultiArrayView,
            _materialized_constructor,
        )
        from ospf_python.multiarray.shape import DynShape, StorageOrder

        order = getattr(StorageOrder, params["order"])
        source = MultiArray(
            DynShape(tuple(params["dims"]), order),
            __import__("numpy").arange(int(params["count"]), dtype="int16"),
        )
        view = MultiArrayView(source, offsets=tuple(int(o) for o in params["offsets"]))
        return lambda: materialize_coordinates(
            owner=view, finish=_materialized_constructor
        )

    BUILDERS = {
        "shared_mapping_map": build_shared_mapping_map,
        "shared_nested": build_shared_nested,
        "shared_reduction": build_shared_reduction,
        "shared_transpose": build_shared_transpose,
        "coordinate_materialization": build_coordinate_materialization,
        "storage_reshape": build_storage_reshape,
        "storage_flatten": build_storage_flatten,
        "shared_view_materialize": build_shared_view_materialize,
        "shared_view_external_failure": build_shared_view_external_failure,
        "public_array_read": build_public_array_read,
        "public_array_write": build_public_array_write,
        "public_array_read_many": build_public_array_read_many,
        "public_array_raw_snapshot": build_public_array_raw_snapshot,
        "unit_registry_family": build_unit_registry_family,
        "unit_registry_runtime": build_unit_registry_runtime,
        "unit_registry_family_register": build_unit_registry_family_register,
        "unit_registry_native_family": build_unit_registry_native_family,
        "unit_registry_arithmetic_family": build_unit_registry_arithmetic_family,
        "julia_iterate": build_julia_iterate,
        "julia_contains": build_julia_contains,
        "trivalent_to_bool": build_trivalent_to_bool,
        "duration_to_timedelta": build_duration_to_timedelta,
        "quantity_add": build_quantity_add,
        "attractor_call": build_attractor_call,
        "trivalent_and": build_trivalent_and,
        "fractal_iterate": build_fractal_iterate,
        "fractal_contains": build_fractal_contains,
        "multiarray_map": build_multiarray_map,
        "multiarray_reduce": build_multiarray_reduce,
        "binding_to_list": build_binding_to_list,
        "binding_transpose": build_binding_transpose,
        "binding_equals": build_binding_equals,
        "binding_describe": build_binding_describe,
        "binding_view": build_binding_view,
        "binding_iter_snapshot": build_binding_iter_snapshot,
        "binding_from_list": build_binding_from_list,
        "mapped_materialize": build_mapped_materialize,
        "dto": build_dto,
        "trivalent_logic": build_trivalent_logic,
        "trivalent_optional_bool": build_trivalent_optional_bool,
        "binding_map": build_binding_map,
        "binding_reduce": build_binding_reduce,
        "binding_iterator": build_binding_iterator,
        "column_decision_spec": build_column_decision_spec,
        "quantity_calculate": build_quantity_calculate,
        "convert_unit_value": build_convert_unit_value,
        "duration_from_value": build_duration_from_value,
        "duration_to_timedelta": build_duration_to_timedelta,
        "binding_mutable_view": build_binding_mutable_view,
    }

    if "builder" in payload:
        factory = BUILDERS.get(payload["builder"])
        if factory is None:
            print(json.dumps({"error": "unknown builder " + str(payload["builder"])}))
            raise SystemExit(0)
        try:
            call = factory(payload["module"], payload["params"])
        except Exception as error:
            print(json.dumps({"error": "builder failed: " + type(error).__name__ + ": " + str(error)}))
            raise SystemExit(0)
    else:
        target = resolve(payload["module"], payload["attrs"])
        if target is None:
            print(json.dumps({"error": "unresolved target"}))
            raise SystemExit(0)
        args = tuple(payload.get("args", ()))
        kwargs = dict(payload.get("kwargs", {}))
        call = lambda: target(*args, **kwargs)

    repeats = int(payload["repeats"])
    # 每个样本做 batch 次调用再除以 batch，把样本值放大到计时器分辨率之上。
    # Windows 的 perf_counter_ns 实际分辨率约 100 ns；单次调用的用例（如 2x3 reshape 约 3,100 ns）
    # 会因此只有约 4.6 个量化步的判定余量，导致比值逐次漂移（B372/B375）。
    # Batch each sample and divide, so the sample lands well above the clock resolution.
    # Windows perf_counter_ns resolves about 100 ns; single-call cases (~3,100 ns) then have only
    # ~4.6 quantisation steps of margin, which is why those ratios drift run to run.
    batch = max(1, int(payload.get("batch", 1)))
    for _ in range(max(1, repeats // 10)):
        call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        for _ in range(batch):
            call()
        samples.append((time.perf_counter_ns() - start) / batch)
    print(json.dumps({"samples_ns": samples}))
    '''
)


def run_child(tree: Path, case: dict, repeats: int) -> dict:
    """在指定树里跑一个 case。 / Run one case inside a given tree."""
    payload: dict[str, object] = {
        "module": case["module"],
        "repeats": repeats,
        "batch": int(case.get("batch", 1)),
    }
    if "builder" in case:
        payload["builder"] = case["builder"]
        payload["params"] = case["params"]
    else:
        payload["attrs"] = list(case["attrs"])
        payload["args"] = case.get("args", [])
        if "kwargs" in case:
            payload["kwargs"] = case["kwargs"]
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(tree)
    environment["PYTHONIOENCODING"] = "utf-8"
    completed = subprocess.run(
        [sys.executable, "-c", CHILD, str(tree), json.dumps(payload)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(tree),
        env=environment,
        check=False,
    )
    if completed.returncode != 0:
        return {
            "error": f"child exit {completed.returncode}: {completed.stderr.strip()[:200]}"
        }
    try:
        return json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as error:
        return {"error": f"bad child output: {error}"}


def measure_family(policy: dict, baseline: Path, current: Path, rounds: int) -> dict:
    """测量一个族。 / Measure one family."""
    cases = policy["cases"]
    threshold = float(policy["threshold"])
    per_case: list[dict] = []
    for case in cases:
        # 用例可用 repeats / batch 覆盖全局策略：batch 放大单个样本的跨度以获得计时分辨率，
        # 同时按比例减少样本数，使总调用次数与原来相当（不放大工作量）。
        # A case may override repeats/batch: batch widens one sample for clock resolution while
        # repeats shrinks proportionally, keeping total calls comparable to the original.
        repeats = int(case.get("repeats", policy["repeats_by_count"][str(case["count"])]))
        baseline_samples: list[float] = []
        current_samples: list[float] = []
        errors: list[str] = []
        for round_index in range(rounds):
            # 交替顺序 / Alternate the order
            order = (
                ("baseline", "current")
                if round_index % 2 == 0
                else ("current", "baseline")
            )
            for side in order:
                result = run_child(
                    baseline if side == "baseline" else current, case, repeats
                )
                if "error" in result:
                    errors.append(f"{side}: {result['error']}")
                    continue
                samples = [float(value) for value in result["samples_ns"]]
                (baseline_samples if side == "baseline" else current_samples).extend(
                    samples
                )
        if errors:
            per_case.append({"case": case["label"], "error": errors[0]})
            continue
        baseline_median = statistics.median(baseline_samples)
        current_median = statistics.median(current_samples)
        ratio = current_median / baseline_median if baseline_median else float("inf")
        per_case.append(
            {
                "case": case["label"],
                "count": case["count"],
                "baseline_median_ns": baseline_median,
                "current_median_ns": current_median,
                "ratio": round(ratio, 4),
                "within_threshold": ratio <= threshold,
                "gated": case["count"] >= int(policy["gated_minimum"]),
            }
        )
    gated = [item for item in per_case if item.get("gated")]
    failures = [item for item in gated if not item["within_threshold"]]
    errors = [item for item in per_case if "error" in item]
    family = policy.get("family") or ",".join(
        sorted({str(item.get("family", "?")) for item in cases})
    )
    return {
        "family": family,
        "cases": per_case,
        "gated_cases": len(gated),
        "failures": len(failures),
        "errors": len(errors),
        "accepted": not failures and not errors,
    }


def main() -> int:
    """执行门禁。 / Run the gate."""
    parser = argparse.ArgumentParser(description="族级比值门禁 / Family ratio gate")
    parser.add_argument("--policy", required=True)
    parser.add_argument(
        "--policy-dir", default=None, help="政策目录（可含多个 policy json）"
    )
    parser.add_argument("--baseline-tree", required=True)
    parser.add_argument("--current-tree", default=str(ROOT))
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--output", required=True)
    parser.add_argument("--smoke", action="store_true", help="只验证机制，不构成验收")
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="自检：两侧用同一棵树，比值应接近 1，用于发现测量偏置",
    )
    arguments = parser.parse_args()

    policy_path = Path(arguments.policy)
    policies = [policy_path]
    if arguments.policy_dir:
        policies = sorted(Path(arguments.policy_dir).glob("*.json"))
    baseline = Path(arguments.baseline_tree)
    current = Path(arguments.current_tree)
    if arguments.self_check:
        # 自检把两侧压成同一棵树：若 harness 有系统性偏置，比值会偏离 1。
        baseline = current

    started = time.perf_counter()
    reports = []
    for path in policies:
        policy = json.loads(path.read_text(encoding="utf-8"))
        reports.append(measure_family(policy, baseline, current, arguments.rounds))

    elapsed = time.perf_counter() - started
    if arguments.self_check:
        worst = max(
            abs(item["ratio"] - 1.0)
            for report in reports
            for item in report["cases"]
            if "ratio" in item
        )
        biased = worst > SELF_CHECK_TOLERANCE
        document = {
            "mode": "self-check",
            "baseline_tree": str(baseline),
            "current_tree": str(current),
            "rounds": arguments.rounds,
            "elapsed_seconds": round(elapsed, 1),
            "policies": [str(path) for path in policies],
            "families": reports,
            "worst_deviation_from_one": round(worst, 4),
            "tolerance": SELF_CHECK_TOLERANCE,
            "accepted": not biased,
            "note": "Self-check compares the same tree on both sides; deviation reveals harness bias.",
        }
        Path(arguments.output).write_text(
            json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(
            f"self-check worst deviation {worst:.4f} (tolerance {SELF_CHECK_TOLERANCE}) -> biased={biased}"
        )
        return 0 if not biased else 1

    document = {
        "mode": "smoke" if arguments.smoke else "acceptance",
        "baseline_tree": str(baseline),
        "current_tree": str(current),
        "rounds": arguments.rounds,
        "elapsed_seconds": round(elapsed, 1),
        "policies": [str(path) for path in policies],
        "families": reports,
        "accepted": all(report["accepted"] for report in reports),
        "note": (
            "SMOKE: 只验证 runner 机制，不构成任何合同验收 / mechanism check only"
            if arguments.smoke
            else "Acceptance run; requires an idle machine."
        ),
    }
    Path(arguments.output).write_text(
        json.dumps(document, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for report in reports:
        print(
            f"{report['family']:24} gated={report['gated_cases']} "
            f"failures={report['failures']} errors={report['errors']} accepted={report['accepted']}"
        )
    print(
        f"elapsed {elapsed:.1f}s | mode={'smoke' if arguments.smoke else 'acceptance'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
