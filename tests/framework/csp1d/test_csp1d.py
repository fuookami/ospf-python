"""CSP1D framework tests."""

from __future__ import annotations

from ospf_python.framework.csp1d.application.model.csp1d_problem import Csp1dProblem
from ospf_python.framework.csp1d.application.model.csp1d_solution import Csp1dSolution
from ospf_python.framework.csp1d.domain.material.model.cutting_plan import CuttingPlan
from ospf_python.framework.csp1d.domain.material.model.machine import Machine
from ospf_python.framework.csp1d.domain.material.model.material import Material
from ospf_python.framework.csp1d.domain.material.model.product import Product


def test_material_creation() -> None:
    m = Material()
    assert m is not None


def test_product_creation() -> None:
    p = Product()
    assert p is not None


def test_machine_creation() -> None:
    m = Machine()
    assert m is not None


def test_cutting_plan_creation() -> None:
    cp = CuttingPlan()
    assert cp is not None


def test_problem_creation() -> None:
    p = Csp1dProblem()
    assert p is not None


def test_solution_creation() -> None:
    s = Csp1dSolution()
    assert s is not None
