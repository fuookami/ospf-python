"""Doc code snippet smoke tests.

Verifies all imports and code snippets from documentation
and examples work without errors.
"""

from __future__ import annotations

import pytest


class TestExampleImports:
    """示例文件导入冒烟测试。/ Example file import smoke tests."""

    def test_bpp1d_example_imports(self) -> None:
        """BPP1D 示例导入。/ BPP1D example imports."""
        from ospf_python.framework.bpp1d.domain.item.model.bin import Bin
        from ospf_python.framework.bpp1d.domain.item.model.item import Item
        from ospf_python.framework.bpp1d.domain.solution.service.bin_packer import (
            BinPacker,
        )
        assert Item is not None
        assert Bin is not None
        assert BinPacker is not None

    def test_bpp2d_example_imports(self) -> None:
        """BPP2D 示例导入。/ BPP2D example imports."""
        from ospf_python.framework.bpp2d.domain.item.model.rectangle import Rectangle
        from ospf_python.framework.bpp2d.domain.service.geometric_packer import (
            GeometricPacker,
        )
        assert Rectangle is not None
        assert GeometricPacker is not None

    def test_csp2d_example_imports(self) -> None:
        """CSP2D 示例导入。/ CSP2D example imports."""
        from ospf_python.framework.csp2d.domain.material.model.sheet import Sheet
        from ospf_python.framework.csp2d.domain.product.model.demand import Demand
        from ospf_python.framework.csp2d.domain.product.model.shape import Shape
        from ospf_python.framework.csp2d.domain.service.cutting_plan_generator import (
            CuttingPlanGenerator,
        )
        assert Sheet is not None
        assert Shape is not None
        assert Demand is not None
        assert CuttingPlanGenerator is not None

    def test_network_scheduling_example_imports(self) -> None:
        """网络排程示例导入。/ Network scheduling example imports."""
        from ospf_python.framework.network_scheduling.domain.edge.model.edge import Edge
        from ospf_python.framework.network_scheduling.domain.flow.model.demand import (
            Demand,
        )
        from ospf_python.framework.network_scheduling.domain.node.model.node import Node
        from ospf_python.framework.network_scheduling.domain.node.model.node_type import (
            NodeType,
        )
        from ospf_python.framework.network_scheduling.domain.service.flow_optimizer import (
            FlowOptimizer,
        )
        from ospf_python.framework.network_scheduling.domain.service.shortest_path import (
            ShortestPath,
        )
        assert Node is not None
        assert NodeType is not None
        assert Edge is not None
        assert Demand is not None
        assert ShortestPath is not None
        assert FlowOptimizer is not None

    def test_math_symbol_example_imports(self) -> None:
        """数学符号运算示例导入。/ Math symbol example imports."""
        from ospf_python.math.symbol.operation.differentiate import Differentiator
        from ospf_python.math.symbol.operation.evaluate import PolynomialEvaluator
        from ospf_python.math.symbol.operation.latex import LatexRenderer
        from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
        from ospf_python.math.symbol.polynomial.canonical_polynomial import (
            CanonicalPolynomial,
        )
        assert QuickDsl is not None
        assert PolynomialEvaluator is not None
        assert Differentiator is not None
        assert LatexRenderer is not None
        assert CanonicalPolynomial is not None


class TestExampleCodeSnippets:
    """示例代码片段运行测试。/ Example code snippet execution tests."""

    def test_bpp1d_snippet(self) -> None:
        """BPP1D 代码片段。/ BPP1D code snippet."""
        from ospf_python.framework.bpp1d.domain.item.model.item import Item
        from ospf_python.framework.bpp1d.domain.solution.service.bin_packer import (
            BinPacker,
        )

        items = (
            Item.create(item_key="a", width=4.0, height=1.0),
            Item.create(item_key="b", width=3.0, height=1.0),
        )
        packer = BinPacker.create(bin_capacity=10.0)
        solution = packer.pack(items)
        assert solution.total_items == 2
        assert solution.bin_count >= 1

    def test_bpp2d_snippet(self) -> None:
        """BPP2D 代码片段。/ BPP2D code snippet."""
        from ospf_python.framework.bpp2d.domain.item.model.rectangle import Rectangle
        from ospf_python.framework.bpp2d.domain.service.geometric_packer import (
            GeometricPacker,
        )

        r = Rectangle.create(item_key="r1", width=30.0, height=20.0)
        packer = GeometricPacker.create(container_width=100.0, container_height=100.0)
        result = packer.place_rectangle(r, 0.0, 0.0)
        assert result.is_ok()

    def test_network_scheduling_snippet(self) -> None:
        """网络排程代码片段。/ Network scheduling code snippet."""
        from ospf_python.framework.network_scheduling.domain.edge.model.edge import Edge
        from ospf_python.framework.network_scheduling.domain.node.model.node import Node
        from ospf_python.framework.network_scheduling.domain.node.model.node_type import (
            NodeType,
        )
        from ospf_python.framework.network_scheduling.domain.service.shortest_path import (
            ShortestPath,
        )

        nodes = (
            Node.create(node_key="A", name="Source", node_type=NodeType.SOURCE),
            Node.create(node_key="B", name="Sink", node_type=NodeType.SINK),
        )
        edges = (
            Edge.create(edge_key="e1", from_node_key="A", to_node_key="B", cost=3.0),
        )
        result = ShortestPath.dijkstra(nodes=nodes, edges=edges, source_key="A", sink_key="B")
        assert result.is_ok()

    def test_math_symbol_snippet(self) -> None:
        """数学符号运算代码片段。/ Math symbol code snippet."""
        from ospf_python.math.symbol.operation.evaluate import PolynomialEvaluator
        from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
        from ospf_python.math.symbol.polynomial.canonical_polynomial import (
            CanonicalPolynomial,
        )

        dsl = QuickDsl(factory=CanonicalPolynomial)
        ev = PolynomialEvaluator(factory=CanonicalPolynomial)
        x = dsl.var("x")
        one = dsl.constant(1.0)
        xp1 = dsl.sum(x, one)
        result = ev.evaluate(xp1, {"x": 2.0})
        assert result == pytest.approx(3.0)


class TestReadmeSnippets:
    """README 代码片段冒烟测试。/ README code snippet smoke tests."""

    def test_core_modeling_imports(self) -> None:
        """核心建模导入。/ Core modeling imports from README."""
        from ospf_python.core.model.mechanism.meta_model import MetaModel
        from ospf_python.core.solver.mock_solver import MockSolver
        from ospf_python.core.solver.solver import Solver
        assert MetaModel is not None
        assert Solver is not None
        assert MockSolver is not None

    def test_physical_quantities_imports(self) -> None:
        """物理量导入。/ Physical quantities imports from README."""
        from ospf_python.quantities.quantity.quantity import Quantity
        from ospf_python.quantities.unit.length import KILOMETER, METER
        from ospf_python.quantities.unit.mass import KILOGRAM
        assert Quantity is not None
        assert METER is not None
        assert KILOMETER is not None
        assert KILOGRAM is not None

    def test_error_handling_imports(self) -> None:
        """错误处理导入。/ Error handling imports from README."""
        from ospf_python.utils.error import ErrorCode
        from ospf_python.utils.functional import Failed, Ok, Result
        assert Result is not None
        assert Ok is not None
        assert Failed is not None
        assert ErrorCode is not None

    def test_math_symbol_readme_snippet(self) -> None:
        """README 数学符号代码片段。/ README math symbol code snippet."""
        from ospf_python.math.symbol.operation.evaluate import PolynomialEvaluator
        from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
        from ospf_python.math.symbol.polynomial.canonical_polynomial import (
            CanonicalPolynomial,
        )

        dsl = QuickDsl(factory=CanonicalPolynomial)
        ev = PolynomialEvaluator(factory=CanonicalPolynomial)
        x = dsl.var("x")
        poly = dsl.sum(dsl.product(x, x), dsl.constant(1.0))  # x^2 + 1
        val = ev.evaluate(poly, {"x": 3.0})
        assert val == pytest.approx(10.0)

    def test_persistence_plugin_imports(self) -> None:
        """持久化插件导入。/ Persistence plugin imports from README."""
        from ospf_python.framework.persistence.redis_repository import RedisRepository
        from ospf_python.framework.persistence.sqlite_repository import SQLiteRepository
        assert SQLiteRepository is not None
        assert RedisRepository is not None

    def test_solver_plugin_imports(self) -> None:
        """求解器插件导入。/ Solver plugin imports from README."""
        from ospf_python.core.solver.gurobi.gurobi_solver import GurobiSolver
        from ospf_python.core.solver.mock_solver import MockSolver
        assert MockSolver is not None
        assert GurobiSolver is not None


class TestPersistenceImports:
    """持久化导入冒烟测试。/ Persistence import smoke tests."""

    def test_sqlite_repository_import(self) -> None:
        """SQLite 仓储导入。/ SQLite repository import."""
        from ospf_python.framework.persistence.sqlite_repository import SQLiteRepository
        assert SQLiteRepository is not None

    def test_redis_repository_import(self) -> None:
        """Redis 仓储导入。/ Redis repository import."""
        from ospf_python.framework.persistence.redis_repository import RedisRepository
        assert RedisRepository is not None

    def test_repository_base_import(self) -> None:
        """仓储基类导入。/ Repository base import."""
        from ospf_python.framework.persistence.repository import Repository
        assert Repository is not None


class TestSolverImports:
    """求解器插件导入冒烟测试。/ Solver plugin import smoke tests."""

    def test_gurobi_import(self) -> None:
        """Gurobi 导入。/ Gurobi import."""
        from ospf_python.core.solver.gurobi.gurobi_solver import GurobiSolver
        assert GurobiSolver is not None

    def test_copt_import(self) -> None:
        """COPT 导入。/ COPT import."""
        from ospf_python.core.solver.copt.copt_solver import CoptSolver
        assert CoptSolver is not None

    def test_scip_import(self) -> None:
        """SCIP 导入。/ SCIP import."""
        from ospf_python.core.solver.scip.scip_solver import ScipSolver
        assert ScipSolver is not None

    def test_mindopt_import(self) -> None:
        """MindOpt 导入。/ MindOpt import."""
        from ospf_python.core.solver.mindopt.mindopt_solver import MindOPTSolver
        assert MindOPTSolver is not None

    def test_mock_solver_import(self) -> None:
        """MockSolver 导入。/ MockSolver import."""
        from ospf_python.core.solver.mock_solver import MockSolver
        assert MockSolver is not None


class TestFrameworkApiImports:
    """框架 API 导入冒烟测试。/ Framework API import smoke tests."""

    def test_bpp1d_api_imports(self) -> None:
        """BPP1D API 导入。/ BPP1D API imports."""
        from ospf_python.framework.bpp1d.domain.constraint.model.constraint import (
            Constraint,
        )
        from ospf_python.framework.bpp1d.domain.constraint.service.constraint_checker import (
            ConstraintChecker,
        )
        from ospf_python.framework.bpp1d.domain.item.model.bin import Bin
        from ospf_python.framework.bpp1d.domain.item.model.item import Item
        from ospf_python.framework.bpp1d.domain.solution.service.bin_packer import (
            BinPacker,
        )
        assert Item is not None
        assert Bin is not None
        assert BinPacker is not None
        assert Constraint is not None
        assert ConstraintChecker is not None

    def test_bpp2d_api_imports(self) -> None:
        """BPP2D API 导入。/ BPP2D API imports."""
        from ospf_python.framework.bpp2d.domain.constraint.model.geometric_constraint import (
            GeometricConstraint,
        )
        from ospf_python.framework.bpp2d.domain.constraint.model.weight_constraint import (
            WeightConstraint,
        )
        from ospf_python.framework.bpp2d.domain.item.model.circle import Circle
        from ospf_python.framework.bpp2d.domain.item.model.rectangle import Rectangle
        from ospf_python.framework.bpp2d.domain.service.geometric_packer import (
            GeometricPacker,
        )
        assert Rectangle is not None
        assert Circle is not None
        assert GeometricPacker is not None
        assert WeightConstraint is not None
        assert GeometricConstraint is not None

    def test_csp2d_api_imports(self) -> None:
        """CSP2D API 导入。/ CSP2D API imports."""
        from ospf_python.framework.csp2d.domain.material.model.sheet import Sheet
        from ospf_python.framework.csp2d.domain.product.model.demand import Demand
        from ospf_python.framework.csp2d.domain.product.model.shape import Shape
        from ospf_python.framework.csp2d.domain.service.cutting_plan_generator import (
            CuttingPlanGenerator,
        )
        from ospf_python.framework.csp2d.domain.service.material_optimizer import (
            MaterialOptimizer,
        )
        assert Sheet is not None
        assert Shape is not None
        assert Demand is not None
        assert CuttingPlanGenerator is not None
        assert MaterialOptimizer is not None

    def test_network_scheduling_api_imports(self) -> None:
        """网络排程 API 导入。/ Network scheduling API imports."""
        from ospf_python.framework.network_scheduling.domain.edge.model.edge import Edge
        from ospf_python.framework.network_scheduling.domain.flow.model.demand import (
            Demand,
        )
        from ospf_python.framework.network_scheduling.domain.node.model.node import Node
        from ospf_python.framework.network_scheduling.domain.node.model.node_type import (
            NodeType,
        )
        from ospf_python.framework.network_scheduling.domain.service.flow_optimizer import (
            FlowOptimizer,
        )
        from ospf_python.framework.network_scheduling.domain.service.shortest_path import (
            ShortestPath,
        )
        assert Node is not None
        assert NodeType is not None
        assert Edge is not None
        assert Demand is not None
        assert ShortestPath is not None
        assert FlowOptimizer is not None

    def test_math_symbol_operations_imports(self) -> None:
        """数学符号运算 API 导入。/ Math symbol operations API imports."""
        from ospf_python.math.symbol.operation.compile import PolynomialCompiler
        from ospf_python.math.symbol.operation.convert import PolynomialConverter
        from ospf_python.math.symbol.operation.differentiate import Differentiator
        from ospf_python.math.symbol.operation.evaluate import PolynomialEvaluator
        from ospf_python.math.symbol.operation.flt64_quick_dsl import Flt64QuickDsl
        from ospf_python.math.symbol.operation.latex import LatexRenderer
        from ospf_python.math.symbol.operation.normalize import PolynomialNormalizer
        from ospf_python.math.symbol.operation.parse import PolynomialStringParser
        from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
        from ospf_python.math.symbol.operation.serde import SerdeOps
        assert Differentiator is not None
        assert PolynomialEvaluator is not None
        assert LatexRenderer is not None
        assert PolynomialStringParser is not None
        assert SerdeOps is not None
        assert PolynomialNormalizer is not None
        assert PolynomialConverter is not None
        assert PolynomialCompiler is not None
        assert QuickDsl is not None
        assert Flt64QuickDsl is not None
