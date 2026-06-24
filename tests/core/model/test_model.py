"""ospf_python.core.model 测试 / Tests for ospf_python.core.model.

覆盖 Phase 13 中所有 44 个模型文件的基本功能。
Covers basic functionality of all 44 model files from Phase 13.
"""

from __future__ import annotations

import pytest

# ---- basic / ----
from ospf_python.core.model.basic.constraint_priority import (
    ConstraintPriority,
)
from ospf_python.core.model.basic.constraint_sign import (
    ConstraintSign,
)
from ospf_python.core.model.basic.expression_range import (
    ExpressionRange,
)
from ospf_python.core.model.basic.model import Model
from ospf_python.core.model.basic.model_building_stage import (
    ModelBuildingStage,
)
from ospf_python.core.model.basic.model_building_status import (
    ModelBuildingStatus,
)
from ospf_python.core.model.basic.model_file_format import (
    ModelFileFormat,
)
from ospf_python.core.model.basic.model_view import ModelView
from ospf_python.core.model.basic.multi_object import MultiObject
from ospf_python.core.model.basic.object_category import (
    ObjectCategory,
)
from ospf_python.core.model.basic.registration_status import (
    RegistrationStatus,
)

# ---- callback / ----
from ospf_python.core.model.callback.call_back_model import (
    CallBackModel,
)
from ospf_python.core.model.callback.call_back_model_interface import (
    CallBackModelInterface,
)

# ---- intermediate / ----
from ospf_python.core.model.intermediate.batch_dispatch_policy import (
    BatchDispatchPolicy,
)
from ospf_python.core.model.intermediate.cell import Cell
from ospf_python.core.model.intermediate.dump_helpers import (
    DumpHelpers,
)
from ospf_python.core.model.intermediate.intermediate_model_dumping_status import (
    IntermediateModelDumpingStatus,
)
from ospf_python.core.model.intermediate.linear_triad_dump_builders import (
    LinearTriadDumpBuilders,
)
from ospf_python.core.model.intermediate.linear_triad_elastic_builder import (
    LinearTriadElasticBuilder,
)
from ospf_python.core.model.intermediate.linear_triad_model import (
    LinearTriadModel,
)
from ospf_python.core.model.intermediate.mechanism_model_dumping_status import (
    MechanismModelDumpingStatus,
)
from ospf_python.core.model.intermediate.memory_cleanup_policy import (
    MemoryCleanupPolicy,
)
from ospf_python.core.model.intermediate.quadratic_tetrad_dump_builders import (
    QuadraticTetradDumpBuilders,
)
from ospf_python.core.model.intermediate.quadratic_tetrad_elastic_builder import (
    QuadraticTetradElasticBuilder,
)
from ospf_python.core.model.intermediate.quadratic_tetrad_model import (
    QuadraticTetradModel,
)
from ospf_python.core.model.intermediate.sparse_matrix import (
    SparseMatrix,
)
from ospf_python.core.model.intermediate.triad_dual_solver_support import (
    TriadDualSolverSupport,
)

# ---- mechanism / ----
from ospf_python.core.model.mechanism.basic_mechanism_model import (
    BasicMechanismModel,
)
from ospf_python.core.model.mechanism.basic_model import BasicModel
from ospf_python.core.model.mechanism.constraint import Constraint
from ospf_python.core.model.mechanism.linear_constraint_input import (
    LinearConstraintInput,
)
from ospf_python.core.model.mechanism.math_inequality_dsl import (
    MathInequalityDsl,
)
from ospf_python.core.model.mechanism.math_inequality_flatten import (
    MathInequalityFlatten,
)
from ospf_python.core.model.mechanism.mechanism_model import (
    MechanismModel,
)
from ospf_python.core.model.mechanism.mechanism_model_cut_support import (
    MechanismModelCutSupport,
)
from ospf_python.core.model.mechanism.mechanism_model_dump_support import (
    MechanismModelDumpSupport,
)
from ospf_python.core.model.mechanism.mechanism_model_flt64_conversion import (
    MechanismModelFlt64Conversion,
)
from ospf_python.core.model.mechanism.mechanism_model_objective_support import (
    MechanismModelObjectiveSupport,
)
from ospf_python.core.model.mechanism.meta_constraint import (
    MetaConstraint,
)
from ospf_python.core.model.mechanism.meta_model import MetaModel
from ospf_python.core.model.mechanism.meta_model_export_support import (
    MetaModelExportSupport,
)
from ospf_python.core.model.mechanism.object_ import Object
from ospf_python.core.model.mechanism.relation import Relation
from ospf_python.core.model.mechanism.sub_object import SubObject

# ============================================================
# basic/ tests
# ============================================================


class TestConstraintPriority:
    """ConstraintPriority 枚举测试 / Enum tests."""

    def test_required_value(self) -> None:
        """REQUIRED 值为 0 / REQUIRED value is 0."""
        assert ConstraintPriority.REQUIRED.value == 0

    def test_preferred_value(self) -> None:
        """PREFERRED 值为 1 / PREFERRED value is 1."""
        assert ConstraintPriority.PREFERRED.value == 1

    def test_optional_value(self) -> None:
        """OPTIONAL 值为 2 / OPTIONAL value is 2."""
        assert ConstraintPriority.OPTIONAL.value == 2

    def test_member_count(self) -> None:
        """共有 3 个成员 / Has 3 members."""
        assert len(ConstraintPriority) == 3


class TestConstraintSign:
    """ConstraintSign 枚举测试 / Enum tests."""

    def test_le_value(self) -> None:
        """LE 值为 '<=' / LE value is '<='."""
        assert ConstraintSign.LE.value == "<="

    def test_ge_value(self) -> None:
        """GE 值为 '>=' / GE value is '>='."""
        assert ConstraintSign.GE.value == ">="

    def test_eq_value(self) -> None:
        """EQ 值为 '==' / EQ value is '=='."""
        assert ConstraintSign.EQ.value == "=="


class TestExpressionRange:
    """ExpressionRange 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        r = ExpressionRange(lower=0.0, upper=10.0)
        with pytest.raises(AttributeError):
            r.lower = 5.0  # type: ignore[misc]

    def test_values(self) -> None:
        """正确存储上下界 / Correctly stores bounds."""
        r = ExpressionRange(lower=-1.5, upper=3.5)
        assert r.lower == -1.5
        assert r.upper == 3.5


class TestModelABC:
    """Model 抽象基类测试 / ABC tests."""

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化抽象类 / Cannot instantiate ABC."""
        with pytest.raises(TypeError):
            Model()  # type: ignore[abstract]

    def test_subclass(self) -> None:
        """子类可以实例化 / Subclass can be instantiated."""

        class DummyModel(Model):
            @property
            def name(self) -> str:
                return "dummy"

            def add_constraint(self, constraint: object) -> None:
                pass

            def add_objective(self, objective: object) -> None:
                pass

        m = DummyModel()
        assert m.name == "dummy"


class TestModelBuildingStage:
    """ModelBuildingStage 枚举测试 / Enum tests."""

    def test_init_value(self) -> None:
        """INIT 值为 0 / INIT value is 0."""
        assert ModelBuildingStage.INIT.value == 0

    def test_extracting_value(self) -> None:
        """EXTRACTING 值为 4 / EXTRACTING value is 4."""
        assert ModelBuildingStage.EXTRACTING.value == 4


class TestModelBuildingStatus:
    """ModelBuildingStatus 枚举测试 / Enum tests."""

    def test_success_value(self) -> None:
        """SUCCESS 值为 0 / SUCCESS value is 0."""
        assert ModelBuildingStatus.SUCCESS.value == 0

    def test_infeasible_value(self) -> None:
        """INFEASIBLE 值为 2 / INFEASIBLE value is 2."""
        assert ModelBuildingStatus.INFEASIBLE.value == 2


class TestModelFileFormat:
    """ModelFileFormat 枚举测试 / Enum tests."""

    def test_lp_value(self) -> None:
        """LP 值为 'lp' / LP value is 'lp'."""
        assert ModelFileFormat.LP.value == "lp"

    def test_mps_gz_value(self) -> None:
        """MPS_GZ 值为 'mps.gz' / MPS_GZ value is 'mps.gz'."""
        assert ModelFileFormat.MPS_GZ.value == "mps.gz"


class TestModelView:
    """ModelView 冻结数据类测试 / Frozen dataclass tests."""

    def test_default_empty(self) -> None:
        """默认视图为空 / Default views are empty."""
        v = ModelView()
        assert v.constraint_views == ()
        assert v.objective_views == ()

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        v = ModelView()
        with pytest.raises(AttributeError):
            v.constraint_views = ("a",)  # type: ignore[misc]


class TestMultiObject:
    """MultiObject 冻结数据类测试 / Frozen dataclass tests."""

    def test_default_empty(self) -> None:
        """默认为空 / Default is empty."""
        m = MultiObject()
        assert m.objectives == ()
        assert m.weights == ()

    def test_with_data(self) -> None:
        """可携带数据 / Can carry data."""
        m = MultiObject(
            objectives=("obj1", "obj2"),
            weights=(1.0, 2.0),
        )
        assert len(m.objectives) == 2
        assert m.weights[1] == 2.0


class TestObjectCategory:
    """ObjectCategory 枚举测试 / Enum tests."""

    def test_variable_value(self) -> None:
        """VARIABLE 值为 0 / VARIABLE value is 0."""
        assert ObjectCategory.VARIABLE.value == 0

    def test_objective_value(self) -> None:
        """OBJECTIVE 值为 2 / OBJECTIVE value is 2."""
        assert ObjectCategory.OBJECTIVE.value == 2


class TestRegistrationStatus:
    """RegistrationStatus 枚举测试 / Enum tests."""

    def test_registered_value(self) -> None:
        """REGISTERED 值为 0 / REGISTERED value is 0."""
        assert RegistrationStatus.REGISTERED.value == 0

    def test_already_exists_value(self) -> None:
        """ALREADY_EXISTS 值为 1 / ALREADY_EXISTS is 1."""
        assert RegistrationStatus.ALREADY_EXISTS.value == 1


# ============================================================
# callback/ tests
# ============================================================


class TestCallBackModel:
    """CallBackModel 类测试 / Class tests."""

    def test_register(self) -> None:
        """注册回调 / Register a callback."""
        m = CallBackModel()
        m.register(lambda: None)
        assert len(m.callbacks) == 1

    def test_clear(self) -> None:
        """清除回调 / Clear callbacks."""
        m = CallBackModel()
        m.register(lambda: None)
        m.clear()
        assert len(m.callbacks) == 0


class TestCallBackModelInterface:
    """CallBackModelInterface 协议测试 / Protocol tests."""

    def test_protocol_check(self) -> None:
        """CallBackModel 符合协议 / CallBackModel satisfies protocol."""
        m = CallBackModel()
        assert isinstance(m, CallBackModelInterface)


# ============================================================
# intermediate/ tests
# ============================================================


class TestBatchDispatchPolicy:
    """BatchDispatchPolicy 枚举测试 / Enum tests."""

    def test_all_value(self) -> None:
        """ALL 值为 0 / ALL value is 0."""
        assert BatchDispatchPolicy.ALL.value == 0

    def test_member_count(self) -> None:
        """共 3 个成员 / Has 3 members."""
        assert len(BatchDispatchPolicy) == 3


class TestCell:
    """Cell 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        c = Cell(row=0, col=1, value=3.14)
        with pytest.raises(AttributeError):
            c.value = 2.71  # type: ignore[misc]

    def test_values(self) -> None:
        """正确存储值 / Correctly stores values."""
        c = Cell(row=2, col=3, value=5.0)
        assert c.row == 2
        assert c.col == 3
        assert c.value == 5.0


class TestDumpHelpers:
    """DumpHelpers 工具类测试 / Utility class tests."""

    def test_format_integer_coefficient(self) -> None:
        """整数系数无小数点 / Integer coefficient has no dot."""
        assert DumpHelpers.format_coefficient(3.0) == "3"

    def test_format_float_coefficient(self) -> None:
        """浮点系数保留小数 / Float coefficient keeps decimal."""
        result = DumpHelpers.format_coefficient(3.14)
        assert "3.14" in result

    def test_format_sign_le(self) -> None:
        """LE 符号保持不变 / LE sign stays the same."""
        assert DumpHelpers.format_sign("<=") == "<="

    def test_format_sign_eq(self) -> None:
        """EQ 符号映射为 '=' / EQ sign maps to '='."""
        assert DumpHelpers.format_sign("==")


class TestIntermediateModelDumpingStatus:
    """IntermediateModelDumpingStatus 枚举测试."""

    def test_success_value(self) -> None:
        """SUCCESS 值为 0 / SUCCESS value is 0."""
        assert IntermediateModelDumpingStatus.SUCCESS.value == 0

    def test_cancelled_value(self) -> None:
        """CANCELLED 值为 3 / CANCELLED value is 3."""
        assert IntermediateModelDumpingStatus.CANCELLED.value == 3


class TestLinearTriadModel:
    """LinearTriadModel 测试 / Tests."""

    def test_default_name(self) -> None:
        """默认名称为空 / Default name is empty."""
        m = LinearTriadModel()
        assert m.name == ""

    def test_add_constraint(self) -> None:
        """可添加约束 / Can add constraints."""
        m = LinearTriadModel()
        m.constraints["c1"] = {"x": 1.0, "y": 2.0}
        assert "c1" in m.constraints


class TestLinearTriadDumpBuilders:
    """LinearTriadDumpBuilders 测试 / Tests."""

    def test_build_lp_contains_name(self) -> None:
        """LP 输出包含模型名 / LP output contains model name."""
        m = LinearTriadModel(name="test_model")
        result = LinearTriadDumpBuilders.build_lp(m)
        assert "test_model" in result

    def test_build_lp_contains_subject_to(self) -> None:
        """LP 输出包含 Subject To / LP output contains Subject To."""
        m = LinearTriadModel()
        result = LinearTriadDumpBuilders.build_lp(m)
        assert "Subject To" in result

    def test_build_mps_contains_name(self) -> None:
        """MPS 输出包含模型名 / MPS output contains model name."""
        m = LinearTriadModel(name="mps_model")
        result = LinearTriadDumpBuilders.build_mps(m)
        assert "mps_model" in result


class TestLinearTriadElasticBuilder:
    """LinearTriadElasticBuilder 测试 / Tests."""

    def test_add_elastic(self) -> None:
        """为约束添加弹性变量 / Add elastic variable."""
        m = LinearTriadModel()
        m.constraints["c1"] = {"x": 1.0}
        LinearTriadElasticBuilder.add_elastic(m, "c1", 10.0)
        assert "elastic_c1" in m.constraints["c1"]
        assert m.constraints["c1"]["elastic_c1"] == 10.0

    def test_add_elastic_missing_constraint(self) -> None:
        """对不存在的约束不操作 / No-op for missing constraint."""
        m = LinearTriadModel()
        LinearTriadElasticBuilder.add_elastic(m, "no_such")
        assert len(m.constraints) == 0


class TestSparseMatrix:
    """SparseMatrix 测试 / Tests."""

    def test_set_get(self) -> None:
        """设置和获取值 / Set and get values."""
        sm = SparseMatrix(name="test")
        sm.set(0, 1, 3.14)
        assert sm.get(0, 1) == 3.14

    def test_get_default(self) -> None:
        """不存在的键返回默认值 / Missing key returns default."""
        sm = SparseMatrix()
        assert sm.get(99, 99) == 0.0
        assert sm.get(99, 99, default=-1.0) == -1.0

    def test_nnz(self) -> None:
        """非零元素计数 / Non-zero element count."""
        sm = SparseMatrix()
        sm.set(0, 0, 1.0)
        sm.set(1, 1, 2.0)
        assert sm.nnz == 2

    def test_to_cells(self) -> None:
        """转换为单元列表 / Convert to cell list."""
        sm = SparseMatrix()
        sm.set(0, 1, 5.0)
        cells = sm.to_cells()
        assert len(cells) == 1
        assert cells[0].row == 0
        assert cells[0].col == 1
        assert cells[0].value == 5.0


class TestTriadDualSolverSupport:
    """TriadDualSolverSupport 测试 / Tests."""

    def test_extract_dual_values(self) -> None:
        """提取对偶值 / Extract dual values."""
        m = LinearTriadModel()
        m.constraints["c1"] = {"x": 1.0}
        m.constraints["c2"] = {"y": 1.0}
        dual = {"c1": 0.5, "c2": 1.5}
        result = TriadDualSolverSupport.extract_dual_values(
            m,
            dual,
        )
        assert result["c1"] == 0.5
        assert result["c2"] == 1.5

    def test_extract_dual_missing(self) -> None:
        """缺失约束对偶值默认为 0 / Missing dual defaults to 0."""
        m = LinearTriadModel()
        m.constraints["c1"] = {"x": 1.0}
        result = TriadDualSolverSupport.extract_dual_values(
            m,
            {},
        )
        assert result["c1"] == 0.0


class TestMechanismModelDumpingStatus:
    """MechanismModelDumpingStatus 枚举测试."""

    def test_success_value(self) -> None:
        """SUCCESS 值为 0 / SUCCESS value is 0."""
        assert MechanismModelDumpingStatus.SUCCESS.value == 0

    def test_skipped_value(self) -> None:
        """SKIPPED 值为 2 / SKIPPED value is 2."""
        assert MechanismModelDumpingStatus.SKIPPED.value == 2


class TestMemoryCleanupPolicy:
    """MemoryCleanupPolicy 枚举测试 / Enum tests."""

    def test_none_value(self) -> None:
        """NONE 值为 0 / NONE value is 0."""
        assert MemoryCleanupPolicy.NONE.value == 0

    def test_aggressive_value(self) -> None:
        """AGGRESSIVE 值为 2 / AGGRESSIVE value is 2."""
        assert MemoryCleanupPolicy.AGGRESSIVE.value == 2


class TestQuadraticTetradModel:
    """QuadraticTetradModel 测试 / Tests."""

    def test_default_name(self) -> None:
        """默认名称为空 / Default name is empty."""
        m = QuadraticTetradModel()
        assert m.name == ""

    def test_add_linear_constraint(self) -> None:
        """可添加线性约束 / Can add linear constraints."""
        m = QuadraticTetradModel()
        m.linear_constraints["c1"] = {"x": 1.0}
        assert "c1" in m.linear_constraints


class TestQuadraticTetradDumpBuilders:
    """QuadraticTetradDumpBuilders 测试 / Tests."""

    def test_build_qp_contains_name(self) -> None:
        """QP 输出包含模型名 / QP output contains model name."""
        m = QuadraticTetradModel(name="qp_test")
        result = QuadraticTetradDumpBuilders.build_qp(m)
        assert "qp_test" in result


class TestQuadraticTetradElasticBuilder:
    """QuadraticTetradElasticBuilder 测试 / Tests."""

    def test_add_elastic(self) -> None:
        """为约束添加弹性变量 / Add elastic variable."""
        m = QuadraticTetradModel()
        m.linear_constraints["c1"] = {"x": 1.0}
        QuadraticTetradElasticBuilder.add_elastic(
            m,
            "c1",
            5.0,
        )
        assert "elastic_c1" in m.linear_constraints["c1"]


# ============================================================
# mechanism/ tests
# ============================================================


class TestBasicMechanismModel:
    """BasicMechanismModel 测试 / Tests."""

    def test_register_variable(self) -> None:
        """注册变量 / Register a variable."""
        m = BasicMechanismModel()
        m.register_variable("x")
        assert "x" in m.registered_variables

    def test_register_constraint(self) -> None:
        """注册约束 / Register a constraint."""
        m = BasicMechanismModel()
        m.register_constraint("c1")
        assert len(m.registered_constraints) == 1


class TestBasicModel:
    """BasicModel 测试 / Tests."""

    def test_add_constraint(self) -> None:
        """添加约束 / Add a constraint."""
        m = BasicModel()
        m.add_constraint("c1")
        assert len(m.constraints) == 1

    def test_add_objective(self) -> None:
        """添加目标函数 / Add an objective."""
        m = BasicModel()
        m.add_objective("obj1")
        assert len(m.objectives) == 1


class TestConstraint:
    """Constraint 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        c = Constraint(
            name="c1",
            expr=None,
            sign=ConstraintSign.LE,
            rhs=10.0,
        )
        with pytest.raises(AttributeError):
            c.rhs = 20.0  # type: ignore[misc]

    def test_values(self) -> None:
        """正确存储值 / Correctly stores values."""
        c = Constraint(
            name="c2",
            expr="expr",
            sign=ConstraintSign.GE,
            rhs=5.0,
        )
        assert c.name == "c2"
        assert c.sign == ConstraintSign.GE
        assert c.rhs == 5.0


class TestLinearConstraintInput:
    """LinearConstraintInput 冻结数据类测试."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        i = LinearConstraintInput(name="lc1")
        with pytest.raises(AttributeError):
            i.name = "new"  # type: ignore[misc]

    def test_default_sign(self) -> None:
        """默认方向为 LE / Default sign is LE."""
        i = LinearConstraintInput(name="lc1")
        assert i.sign == ConstraintSign.LE


class TestMathInequalityDsl:
    """MathInequalityDsl 测试 / Tests."""

    def test_le(self) -> None:
        """小于等于 / Less than or equal."""
        dsl = MathInequalityDsl("x").le(10.0)
        assert dsl.sign == "<="
        assert dsl.rhs == 10.0

    def test_ge(self) -> None:
        """大于等于 / Greater than or equal."""
        dsl = MathInequalityDsl("x").ge(5.0)
        assert dsl.sign == ">="
        assert dsl.rhs == 5.0

    def test_eq(self) -> None:
        """等于 / Equal to."""
        dsl = MathInequalityDsl("x").eq(3.0)
        assert dsl.sign == "=="
        assert dsl.rhs == 3.0


class TestMathInequalityFlatten:
    """MathInequalityFlatten 测试 / Tests."""

    def test_add_term(self) -> None:
        """添加项 / Add a term."""
        f = MathInequalityFlatten()
        f.add_term("x", 2.0)
        f.add_term("x", 3.0)
        assert f.terms["x"] == 5.0

    def test_add_constant(self) -> None:
        """添加常数 / Add a constant."""
        f = MathInequalityFlatten()
        f.add_constant(1.0)
        f.add_constant(2.5)
        assert f.constant == 3.5


class TestMechanismModel:
    """MechanismModel 测试 / Tests."""

    def test_inherits_basic(self) -> None:
        """继承 BasicMechanismModel / Inherits BasicMechanismModel."""
        m = MechanismModel()
        assert isinstance(m, BasicMechanismModel)

    def test_build(self) -> None:
        """构建不抛异常 / Build does not raise."""
        m = MechanismModel()
        m.build()

    def test_validate(self) -> None:
        """验证返回 True / Validate returns True."""
        m = MechanismModel()
        assert m.validate() is True


class TestMechanismModelCutSupport:
    """MechanismModelCutSupport 测试 / Tests."""

    def test_add_cut(self) -> None:
        """添加切割平面 / Add a cut."""
        s = MechanismModelCutSupport()
        s.add_cut("cut1")
        assert s.cut_count == 1

    def test_clear_cuts(self) -> None:
        """清除切割 / Clear cuts."""
        s = MechanismModelCutSupport()
        s.add_cut("cut1")
        s.clear_cuts()
        assert s.cut_count == 0


class TestMechanismModelDumpSupport:
    """MechanismModelDumpSupport 测试 / Tests."""

    def test_dump_returns_success(self) -> None:
        """转储返回 SUCCESS / Dump returns SUCCESS."""
        s = MechanismModelDumpSupport()
        status = s.dump(object(), ModelFileFormat.LP)
        assert status == MechanismModelDumpingStatus.SUCCESS


class TestMechanismModelFlt64Conversion:
    """MechanismModelFlt64Conversion 测试 / Tests."""

    def test_convert_value(self) -> None:
        """转换值为浮点 / Convert value to float."""
        assert MechanismModelFlt64Conversion.convert_value(3) == 3.0

    def test_convert_coefficients(self) -> None:
        """转换系数 / Convert coefficients."""
        result = MechanismModelFlt64Conversion.convert_coefficients(
            {"x": 1, "y": 2},
        )
        assert result["x"] == 1.0
        assert result["y"] == 2.0


class TestMechanismModelObjectiveSupport:
    """MechanismModelObjectiveSupport 测试 / Tests."""

    def test_add_objective(self) -> None:
        """添加目标函数 / Add an objective."""
        s = MechanismModelObjectiveSupport()
        s.add_objective("obj1")
        assert s.objective_count == 1

    def test_clear_objectives(self) -> None:
        """清除目标函数 / Clear objectives."""
        s = MechanismModelObjectiveSupport()
        s.add_objective("obj1")
        s.clear_objectives()
        assert s.objective_count == 0

    def test_default_minimize(self) -> None:
        """默认为最小化 / Default is minimize."""
        s = MechanismModelObjectiveSupport()
        assert s.minimize is True


class TestMetaConstraint:
    """MetaConstraint 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        mc = MetaConstraint(
            name="mc1",
            expr=None,
            sign=ConstraintSign.LE,
            rhs=10.0,
        )
        with pytest.raises(AttributeError):
            mc.name = "new"  # type: ignore[misc]

    def test_default_priority(self) -> None:
        """默认优先级为 REQUIRED / Default priority is REQUIRED."""
        mc = MetaConstraint(
            name="mc1",
            expr=None,
            sign=ConstraintSign.LE,
            rhs=10.0,
        )
        assert mc.priority == ConstraintPriority.REQUIRED


class TestMetaModel:
    """MetaModel 测试 / Tests."""

    def test_register_variable(self) -> None:
        """注册变量 / Register a variable."""
        m = MetaModel()
        status = m.register_variable("x", "var_obj")
        assert status == RegistrationStatus.REGISTERED
        assert m.find_variable("x") == "var_obj"

    def test_register_variable_duplicate(self) -> None:
        """重复注册返回 ALREADY_EXISTS / Duplicate returns ALREADY_EXISTS."""
        m = MetaModel()
        m.register_variable("x", "v1")
        status = m.register_variable("x", "v2")
        assert status == RegistrationStatus.ALREADY_EXISTS

    def test_register_constraint(self) -> None:
        """注册约束 / Register a constraint."""
        m = MetaModel()
        status = m.register_constraint("c1", "con_obj")
        assert status == RegistrationStatus.REGISTERED

    def test_register_objective(self) -> None:
        """注册目标函数 / Register an objective."""
        m = MetaModel()
        status = m.register_objective("obj1", "obj_obj")
        assert status == RegistrationStatus.REGISTERED

    def test_find_missing_variable(self) -> None:
        """查找不存在的变量返回 None / Missing var returns None."""
        m = MetaModel()
        assert m.find_variable("no_such") is None

    def test_find_missing_constraint(self) -> None:
        """查找不存在的约束返回 None / Missing constraint returns None."""
        m = MetaModel()
        assert m.find_constraint("no_such") is None


class TestMetaModelExportSupport:
    """MetaModelExportSupport 测试 / Tests."""

    def test_export_contains_name(self) -> None:
        """导出包含模型名 / Export contains model name."""
        m = MetaModel(name="export_test")
        result = MetaModelExportSupport.export(
            m,
            ModelFileFormat.LP,
        )
        assert "export_test" in result

    def test_export_contains_counts(self) -> None:
        """导出包含计数 / Export contains counts."""
        m = MetaModel()
        m.register_variable("x", None)
        result = MetaModelExportSupport.export(
            m,
            ModelFileFormat.LP,
        )
        assert "Variables: 1" in result


class TestObject:
    """Object 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        o = Object(name="x", category=ObjectCategory.VARIABLE)
        with pytest.raises(AttributeError):
            o.name = "y"  # type: ignore[misc]

    def test_default_index(self) -> None:
        """默认索引为 -1 / Default index is -1."""
        o = Object(name="x", category=ObjectCategory.VARIABLE)
        assert o.index == -1


class TestRelation:
    """Relation 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        r = Relation(source="a", target="b")
        with pytest.raises(AttributeError):
            r.source = "c"  # type: ignore[misc]

    def test_values(self) -> None:
        """正确存储值 / Correctly stores values."""
        r = Relation(
            source="x",
            target="y",
            relation_type="depends_on",
        )
        assert r.relation_type == "depends_on"


class TestSubObject:
    """SubObject 冻结数据类测试 / Frozen dataclass tests."""

    def test_frozen(self) -> None:
        """实例不可变 / Instance is frozen."""
        s = SubObject(parent="c1", name="x")
        with pytest.raises(AttributeError):
            s.name = "y"  # type: ignore[misc]

    def test_default_coefficient(self) -> None:
        """默认系数为 1.0 / Default coefficient is 1.0."""
        s = SubObject(parent="c1", name="x")
        assert s.coefficient == 1.0

    def test_custom_coefficient(self) -> None:
        """自定义系数 / Custom coefficient."""
        s = SubObject(parent="c1", name="x", coefficient=2.5)
        assert s.coefficient == 2.5
