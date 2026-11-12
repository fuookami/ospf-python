"""私有 BPP1D 列池示例 / Private BPP1D column pool example."""

from __future__ import annotations

from ospf_python import _native
from ospf_python._binding.bpp1d import (
    AuxiliaryVariable,
    BinSpec,
    ExtensionConstraint,
    ItemSpec,
    PackingContext,
    PatternExtension,
    PatternExtensionSpec,
    PatternExtraction,
    PatternRegistration,
)
from ospf_python._binding.numeric import Rational
from ospf_python._binding.quantities import Unit


def main() -> None:
    """重建候选池并复核 LP 与最终整数模型 / Rebuild the pool and validate LP and final integer models."""
    zero = Rational.from_value(0).unwrap()
    one = Rational.from_value(1).unwrap()
    two = Rational.from_value(2).unwrap()
    length = Unit.create(
        name="length", symbol="m", powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    mass = Unit.create(
        name="mass", symbol="kg", powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    ).unwrap()
    context = PackingContext.create(
        items=[
            ItemSpec(id="a", length=one, weight=zero, amount=1),
            ItemSpec(id="b", length=one, weight=zero, amount=1),
        ],
        bins=[BinSpec(id="bin", length=two, max_weight=zero, cost=one)],
        spacing=zero,
        length_unit=length,
        weight_unit=mass,
    ).unwrap()

    def register(snapshot: PatternRegistration) -> PatternExtensionSpec:
        flag = snapshot.auxiliary("flag")
        return PatternExtensionSpec(
            variables=[AuxiliaryVariable(name="flag", kind="binary")],
            constraints=[
                ExtensionConstraint(
                    name="half", terms=[(flag, (2, 1))], relation=">=", rhs=(1, 1)
                )
            ],
            objective=[(flag, (1, 1))],
        )

    def extract(snapshot: PatternExtraction) -> dict[str, str]:
        flag = next(key for key in snapshot.values if key.auxiliary == "flag")
        return {"flag": str(snapshot.values[flag][0])}

    pool = context.column_pool(
        patterns=[("bin", {"a": 1, "b": 1})],
        extension=PatternExtension(register=register, extract_solution=extract),
    ).unwrap()
    try:
        snapshot = pool.add_columns(patterns=[("bin", {"a": 1})]).unwrap()
        assert snapshot.generation == 1
        solvers = _native.build_info()["native_solvers"].split(",")
        if solvers[0]:
            solved = pool.solve_lp(solver=solvers[0]).unwrap()
            assert solved.report.model_generation == snapshot.generation
            assert solved.solution.unwrap().model_objective == (3, 2)
            final = pool.solve_final_milp(solver=solvers[0], expansion_limit=2).unwrap()
            assert final.report.model_generation == snapshot.generation
            assert final.report.model_identity != snapshot.model_identity
            assert final.solution.unwrap().model_objective == (2, 1)
            assert final.solution.unwrap().indicators == {"flag": "1"}
            print("BPP1D pool: generation=1, LP=3/2, final=2")
        else:
            print("BPP1D pool: generation=1, compile a solver to run models")
    finally:
        pool.close().unwrap()


if __name__ == "__main__":
    main()
