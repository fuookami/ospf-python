"""Rust 所有者线性结构导出合同 / Rust-owned linear export contracts."""

from __future__ import annotations

from ospf_python._binding.model import (
    ConstraintSpec,
    MetaModelFloat64,
    VariableSpec,
)


def _model() -> tuple[MetaModelFloat64, object, object]:
    model = MetaModelFloat64.create("linear-export").unwrap()
    x, y = model.add_variables(
        [
            VariableSpec(name="x", lower=-2, upper=5),
            VariableSpec(name="y", kind="binary"),
        ]
    ).unwrap()
    model.add_constraints(
        [
            ConstraintSpec(
                name="balance",
                terms=[(x, 1), (y, -2)],
                relation=">=",
                rhs=3,
            )
        ]
    ).unwrap()
    model.set_objective(terms=[(x, 2), (y, 3)], sense="minimize").unwrap()
    return model, x, y


def test_export_preserves_complete_structure_and_names() -> None:
    model, _, _ = _model()
    try:
        exported = model.to_linear_triad().unwrap()

        assert exported.name == "linear-export"
        assert [
            (variable.name, variable.kind, variable.lower, variable.upper)
            for variable in exported.variables
        ] == [
            ("x", "continuous", -2.0, 5.0),
            ("y", "binary", 0.0, 1.0),
        ]
        assert len(exported.rows) == 1
        row = exported.rows[0]
        assert row.name == "balance"
        assert row.relation == ">="
        assert row.rhs == 3.0
        assert row.coefficients == {"x": 1.0, "y": -2.0}
        assert exported.objective == {"x": 2.0, "y": 3.0}
        assert exported.sense == "minimize"
        assert exported.constant == 0.0
    finally:
        model.close().unwrap()


def test_export_is_a_detached_snapshot() -> None:
    model, x, _ = _model()
    try:
        exported = model.to_linear_triad().unwrap()
        model.set_bounds(handle=x, lower=0, upper=1).unwrap()
        changed = model.to_linear_triad().unwrap()

        assert exported.variables[0].lower == -2.0
        assert exported.variables[0].upper == 5.0
        assert changed.variables[0].lower == 0.0
        assert changed.variables[0].upper == 1.0
    finally:
        model.close().unwrap()


def test_failed_batch_does_not_change_exported_rows() -> None:
    model, x, _ = _model()
    try:
        before = model.to_linear_triad().unwrap()
        result = model.add_constraints(
            [
                ConstraintSpec(
                    name="temporary",
                    terms=[(x, 1)],
                    relation="<=",
                    rhs=1,
                ),
                ConstraintSpec(
                    name="balance",
                    terms=[(x, 1)],
                    relation="<=",
                    rhs=1,
                ),
            ]
        )

        assert result.is_failed()
        after = model.to_linear_triad().unwrap()
        assert [row.name for row in after.rows] == [row.name for row in before.rows]
        assert after.rows == before.rows
    finally:
        model.close().unwrap()


def test_closed_model_cannot_export() -> None:
    model, _, _ = _model()
    model.close().unwrap()

    assert model.to_linear_triad().is_failed()
