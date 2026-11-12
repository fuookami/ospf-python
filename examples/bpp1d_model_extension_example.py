"""私有 BPP1D 精确扩展示例 / Private exact BPP1D extension example."""

from __future__ import annotations

from ospf_python import _native
from ospf_python._binding.bpp1d import (
    AuxiliaryVariable,
    BinSpec,
    ExtensionConstraint,
    ItemSpec,
    PackingContext,
    PackingSolution,
    PatternExtension,
    PatternExtensionSpec,
    PatternExtraction,
    PatternRegistration,
)
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit


def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
    """追加强制启用的辅助变量及成本 / Add a required auxiliary variable and cost.

    Args:
        snapshot: 此次注册的独立快照 / Detached snapshot for this registration.

    Returns:
        精确模型声明 / Exact model declaration.
    """
    auxiliary = snapshot.auxiliary("enabled")
    return PatternExtensionSpec(
        variables=[AuxiliaryVariable(name="enabled", kind="binary")],
        constraints=[
            ExtensionConstraint(
                name="require_enabled",
                terms=[(auxiliary, (1, 1))],
                relation="==",
                rhs=(1, 1),
            )
        ],
        objective=[(auxiliary, (2, 1))],
    )


def extract(snapshot: PatternExtraction) -> dict[str, str]:
    """从已复核的源值提取指标 / Extract an indicator from validated source values.

    Args:
        snapshot: 独立领域、候选和值快照 / Detached domain, candidate and value snapshot.

    Returns:
        字符串指标 / String indicators.
    """
    enabled = next(ref for ref in snapshot.values if ref.auxiliary == "enabled")
    numerator, denominator = snapshot.values[enabled]
    return {"enabled": f"{numerator}/{denominator}"}


def solve(*, solver: str) -> PackingSolution:
    """执行有限候选模型 / Solve the bounded-candidate model.

    Args:
        solver: 已编译且可用的后端 / Compiled and available backend.

    Returns:
        已复核方案；不证明全局最优 / Validated solution, not a global optimality proof.
    """
    zero = Rational.from_value(0).unwrap()
    one = Rational.from_value(1).unwrap()
    length = Unit.create(
        name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    mass = Unit.create(
        name="mass", symbol="kg", powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    context = PackingContext.create(
        items=[ItemSpec(id="a", length=one, weight=zero, amount=1)],
        bins=[BinSpec(id="bin", length=one, max_weight=zero, cost=one)],
        spacing=zero,
        length_unit=length,
        weight_unit=mass,
    ).unwrap()
    result = context.solve(
        solver=solver,
        max_patterns=10,
        max_nodes=100,
        expansion_limit=1,
        extension=PatternExtension(register=register, extract_solution=extract),
    ).unwrap()
    return result.solution.unwrap()


def main() -> None:
    """运行首个已编译后端，或说明需要后端 / Run the first compiled backend, or explain the requirement."""
    solvers = _native.build_info()["native_solvers"].split(",")
    if not solvers[0]:
        print("BPP1D extension: compile an available solver first")
        return
    solution = solve(solver=solvers[0])
    assert solution.packed[-1] == (1, 1)
    assert solution.model_objective == (3, 1)
    assert solution.indicators == {"enabled": "1/1"}
    print("BPP1D extension: base=1, complete=3, enabled=1")


if __name__ == "__main__":
    main()
