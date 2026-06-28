"""Volume minimization behavioral tests.

Covers build_objective_terms, compute_volume_savings, savings_ratio,
objective_name_for, _var_name for all volume minimization modules:
- TimeVolumeMinimization (task_compilation)
- BatchVolumeMinimization (task_compilation)
- TaskVolumeMinimization (task_compilation)
- ResourceVolumeMinimization (task_compilation)
- ProduceVolumeMinimization (produce)
- ResourceVolumeMinimization (resource)
"""

from __future__ import annotations

import pytest

from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_volume_minimization import (
    ProduceVolumeMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.produce.service.limits.produce_volume_minimization import (
    VolumeSavingsResult as ProduceVolumeSavings,
)
from ospf_python.framework.gantt_scheduling.domain.resource.service.limits.resource_volume_minimization import (
    ResourceVolumeMinimization,
)
from ospf_python.framework.gantt_scheduling.domain.resource.service.limits.resource_volume_minimization import (
    VolumeSavingsResult as ResourceVolumeSavings,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.batch_volume_minimization import (
    BatchVolumeMinimization,
    BatchVolumeSavingsResult,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.resource_volume_minimization import (
    ResourceVolumeMinimization as TaskCompResourceVolumeMin,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.resource_volume_minimization import (
    ResourceVolumeSavingsResult as TaskCompResourceVolumeSavings,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.task_volume_minimization import (
    TaskVolumeMinimization,
    TaskVolumeSavingsResult,
)
from ospf_python.framework.gantt_scheduling.domain.task_compilation.service.limits.time_volume_minimization import (
    TimeVolumeMinimization,
    TimeVolumeObjectiveTerm,
    TimeVolumeSavingsResult,
)

# ==================== TimeVolumeMinimization tests ====================


class TestTimeVolumeObjectiveTerm:
    """TimeVolumeObjectiveTerm behavioral tests."""

    def test_construction(self) -> None:
        term = TimeVolumeObjectiveTerm(
            window_start=0.0, window_end=1.0, weight=1.5, capacity=100.0,
            variable_name="time_vol_0.0_1.0",
        )
        assert term.window_start == pytest.approx(0.0)
        assert term.weight == pytest.approx(1.5)
        assert term.capacity == pytest.approx(100.0)
        assert term.fixed_cost == pytest.approx(0.0)

    def test_custom_fixed_cost(self) -> None:
        term = TimeVolumeObjectiveTerm(
            window_start=0.0, window_end=1.0, weight=1.0, capacity=50.0,
            variable_name="v", fixed_cost=10.0,
        )
        assert term.fixed_cost == pytest.approx(10.0)


class TestTimeVolumeSavingsResult:
    """TimeVolumeSavingsResult behavioral tests."""

    def test_savings_ratio_normal(self) -> None:
        r = TimeVolumeSavingsResult(original_volume=100.0, optimized_volume=60.0)
        assert r.savings_ratio == pytest.approx(0.4)

    def test_savings_ratio_no_savings(self) -> None:
        r = TimeVolumeSavingsResult(original_volume=100.0, optimized_volume=100.0)
        assert r.savings_ratio == pytest.approx(0.0)

    def test_savings_ratio_zero_original(self) -> None:
        r = TimeVolumeSavingsResult(original_volume=0.0, optimized_volume=0.0)
        assert r.savings_ratio == pytest.approx(0.0)

    def test_savings_ratio_negative_clamped(self) -> None:
        r = TimeVolumeSavingsResult(original_volume=100.0, optimized_volume=150.0)
        assert r.savings_ratio == pytest.approx(0.0)


class TestTimeVolumeMinimization:
    """TimeVolumeMinimization behavioral tests."""

    def test_defaults(self) -> None:
        m = TimeVolumeMinimization()
        assert m.objective_name == "time_volume_min"
        assert m.default_weight == pytest.approx(1.0)

    def test_build_objective_terms_basic(self) -> None:
        m = TimeVolumeMinimization()
        terms = m.build_objective_terms(
            time_windows=((0.0, 1.0), (1.0, 2.0)),
            window_capacities={(0.0, 1.0): 100.0, (1.0, 2.0): 200.0},
        )
        assert len(terms) == 2
        assert terms[0].window_start == pytest.approx(0.0)
        assert terms[0].capacity == pytest.approx(100.0)
        assert terms[1].capacity == pytest.approx(200.0)

    def test_build_objective_terms_empty(self) -> None:
        m = TimeVolumeMinimization()
        terms = m.build_objective_terms(time_windows=(), window_capacities={})
        assert len(terms) == 0

    def test_build_objective_terms_zero_capacity_skipped(self) -> None:
        m = TimeVolumeMinimization()
        terms = m.build_objective_terms(
            time_windows=((0.0, 1.0),),
            window_capacities={(0.0, 1.0): 0.0},
        )
        assert len(terms) == 0

    def test_build_objective_terms_zero_weight_skipped(self) -> None:
        m = TimeVolumeMinimization()
        terms = m.build_objective_terms(
            time_windows=((0.0, 1.0),),
            window_capacities={(0.0, 1.0): 100.0},
            weights={(0.0, 1.0): 0.0},
        )
        assert len(terms) == 0

    def test_build_objective_terms_custom_weights(self) -> None:
        m = TimeVolumeMinimization()
        terms = m.build_objective_terms(
            time_windows=((0.0, 1.0),),
            window_capacities={(0.0, 1.0): 100.0},
            weights={(0.0, 1.0): 2.5},
        )
        assert terms[0].weight == pytest.approx(2.5)

    def test_build_objective_terms_fixed_costs(self) -> None:
        m = TimeVolumeMinimization()
        terms = m.build_objective_terms(
            time_windows=((0.0, 1.0),),
            window_capacities={(0.0, 1.0): 100.0},
            fixed_costs={(0.0, 1.0): 15.0},
        )
        assert terms[0].fixed_cost == pytest.approx(15.0)

    def test_compute_volume_savings(self) -> None:
        m = TimeVolumeMinimization()
        result = m.compute_volume_savings(
            original_volumes={(0.0, 1.0): 100.0, (1.0, 2.0): 200.0},
            optimized_volumes={(0.0, 1.0): 80.0, (1.0, 2.0): 150.0},
        )
        assert result.original_volume == pytest.approx(300.0)
        assert result.optimized_volume == pytest.approx(230.0)
        assert result.savings_ratio == pytest.approx(1.0 - 230.0 / 300.0)

    def test_objective_name_for_window(self) -> None:
        m = TimeVolumeMinimization()
        assert m.objective_name_for_window(0.0, 1.0) == "time_volume_min_0.0_1.0"

    def test_var_name(self) -> None:
        m = TimeVolumeMinimization()
        assert m._var_name(window_start=0.0, window_end=1.0) == "time_vol_0.0_1.0"


# ==================== BatchVolumeMinimization tests ====================


class TestBatchVolumeSavingsResult:
    """BatchVolumeSavingsResult behavioral tests."""

    def test_savings_ratio_normal(self) -> None:
        r = BatchVolumeSavingsResult(original_volume=200.0, optimized_volume=120.0)
        assert r.savings_ratio == pytest.approx(0.4)

    def test_savings_ratio_zero_original(self) -> None:
        r = BatchVolumeSavingsResult(original_volume=0.0, optimized_volume=0.0)
        assert r.savings_ratio == pytest.approx(0.0)


class TestBatchVolumeMinimization:
    """BatchVolumeMinimization behavioral tests."""

    def test_defaults(self) -> None:
        m = BatchVolumeMinimization()
        assert m.objective_name == "batch_volume_min"
        assert m.default_weight == pytest.approx(1.0)

    def test_build_objective_terms_basic(self) -> None:
        m = BatchVolumeMinimization()
        terms = m.build_objective_terms(
            batch_keys=("b1", "b2"),
            batch_capacities={"b1": 50.0, "b2": 100.0},
        )
        assert len(terms) == 2
        assert terms[0].batch_key == "b1"
        assert terms[1].batch_key == "b2"

    def test_build_objective_terms_empty(self) -> None:
        m = BatchVolumeMinimization()
        terms = m.build_objective_terms(batch_keys=(), batch_capacities={})
        assert len(terms) == 0

    def test_build_objective_terms_zero_weight_skipped(self) -> None:
        m = BatchVolumeMinimization()
        terms = m.build_objective_terms(
            batch_keys=("b1",),
            batch_capacities={"b1": 50.0},
            weights={"b1": 0.0},
        )
        assert len(terms) == 0

    def test_build_objective_terms_custom_weights(self) -> None:
        m = BatchVolumeMinimization()
        terms = m.build_objective_terms(
            batch_keys=("b1",),
            batch_capacities={"b1": 50.0},
            weights={"b1": 3.0},
        )
        assert terms[0].weight == pytest.approx(3.0)

    def test_build_objective_terms_fixed_costs(self) -> None:
        m = BatchVolumeMinimization()
        terms = m.build_objective_terms(
            batch_keys=("b1",),
            batch_capacities={"b1": 50.0},
            fixed_costs={"b1": 20.0},
        )
        assert terms[0].fixed_cost == pytest.approx(20.0)

    def test_compute_volume_savings(self) -> None:
        m = BatchVolumeMinimization()
        result = m.compute_volume_savings(
            original_volumes={"b1": 100.0, "b2": 200.0},
            optimized_volumes={"b1": 80.0, "b2": 150.0},
        )
        assert result.original_volume == pytest.approx(300.0)
        assert result.optimized_volume == pytest.approx(230.0)

    def test_objective_name_for(self) -> None:
        m = BatchVolumeMinimization()
        assert m.objective_name_for("b1") == "batch_volume_min_b1"

    def test_var_name(self) -> None:
        m = BatchVolumeMinimization()
        assert m._var_name("b1") == "batch_vol_b1"


# ==================== TaskVolumeMinimization tests ====================


class TestTaskVolumeSavingsResult:
    """TaskVolumeSavingsResult behavioral tests."""

    def test_savings_ratio_normal(self) -> None:
        r = TaskVolumeSavingsResult(original_volume=100.0, optimized_volume=70.0)
        assert r.savings_ratio == pytest.approx(0.3)

    def test_savings_ratio_zero_original(self) -> None:
        r = TaskVolumeSavingsResult(original_volume=0.0, optimized_volume=0.0)
        assert r.savings_ratio == pytest.approx(0.0)


class TestTaskVolumeMinimization:
    """TaskVolumeMinimization behavioral tests."""

    def test_defaults(self) -> None:
        m = TaskVolumeMinimization()
        assert m.objective_name == "task_volume_min"
        assert m.default_weight == pytest.approx(1.0)

    def test_build_objective_terms_basic(self) -> None:
        m = TaskVolumeMinimization()
        terms = m.build_objective_terms(
            task_keys=("t1", "t2"),
            task_volumes={"t1": 5.0, "t2": 10.0},
        )
        assert len(terms) == 2
        assert terms[0].task_key == "t1"
        assert terms[0].volume == pytest.approx(5.0)
        assert terms[1].task_key == "t2"

    def test_build_objective_terms_empty(self) -> None:
        m = TaskVolumeMinimization()
        terms = m.build_objective_terms(task_keys=(), task_volumes={})
        assert len(terms) == 0

    def test_build_objective_terms_zero_volume_skipped(self) -> None:
        m = TaskVolumeMinimization()
        terms = m.build_objective_terms(
            task_keys=("t1",),
            task_volumes={"t1": 0.0},
        )
        assert len(terms) == 0

    def test_build_objective_terms_zero_weight_skipped(self) -> None:
        m = TaskVolumeMinimization()
        terms = m.build_objective_terms(
            task_keys=("t1",),
            task_volumes={"t1": 5.0},
            weights={"t1": 0.0},
        )
        assert len(terms) == 0

    def test_build_objective_terms_custom_weights(self) -> None:
        m = TaskVolumeMinimization()
        terms = m.build_objective_terms(
            task_keys=("t1",),
            task_volumes={"t1": 5.0},
            weights={"t1": 2.0},
        )
        assert terms[0].weight == pytest.approx(2.0)

    def test_compute_volume_savings(self) -> None:
        m = TaskVolumeMinimization()
        result = m.compute_volume_savings(
            original_volumes={"t1": 10.0, "t2": 20.0},
            optimized_volumes={"t1": 8.0, "t2": 15.0},
        )
        assert result.original_volume == pytest.approx(30.0)
        assert result.optimized_volume == pytest.approx(23.0)

    def test_objective_name_for(self) -> None:
        m = TaskVolumeMinimization()
        assert m.objective_name_for("t1") == "task_volume_min_t1"

    def test_var_name(self) -> None:
        m = TaskVolumeMinimization()
        assert m._var_name("t1") == "task_vol_t1"


# ==================== ResourceVolumeMinimization (task_compilation) tests ====================


class TestTaskCompResourceVolumeSavings:
    """ResourceVolumeSavingsResult (task_compilation) behavioral tests."""

    def test_savings_ratio_normal(self) -> None:
        r = TaskCompResourceVolumeSavings(original_volume=200.0, optimized_volume=100.0)
        assert r.savings_ratio == pytest.approx(0.5)

    def test_savings_ratio_zero_original(self) -> None:
        r = TaskCompResourceVolumeSavings(original_volume=0.0, optimized_volume=0.0)
        assert r.savings_ratio == pytest.approx(0.0)


class TestTaskCompResourceVolumeMinimization:
    """ResourceVolumeMinimization (task_compilation) behavioral tests."""

    def test_defaults(self) -> None:
        m = TaskCompResourceVolumeMin()
        assert m.objective_name == "resource_volume_min"
        assert m.default_weight == pytest.approx(1.0)
        assert m.fixed_cost_weight == pytest.approx(0.0)

    def test_build_objective_terms_basic(self) -> None:
        m = TaskCompResourceVolumeMin()
        terms = m.build_objective_terms(
            resource_keys=("r1", "r2"),
            resource_capacities={"r1": 100.0, "r2": 200.0},
        )
        assert len(terms) == 2
        assert terms[0].resource_key == "r1"
        assert terms[1].resource_key == "r2"

    def test_build_objective_terms_empty(self) -> None:
        m = TaskCompResourceVolumeMin()
        terms = m.build_objective_terms(resource_keys=(), resource_capacities={})
        assert len(terms) == 0

    def test_build_objective_terms_zero_weight_skipped(self) -> None:
        m = TaskCompResourceVolumeMin()
        terms = m.build_objective_terms(
            resource_keys=("r1",),
            resource_capacities={"r1": 100.0},
            weights={"r1": 0.0},
        )
        assert len(terms) == 0

    def test_build_objective_terms_custom_weights(self) -> None:
        m = TaskCompResourceVolumeMin()
        terms = m.build_objective_terms(
            resource_keys=("r1",),
            resource_capacities={"r1": 100.0},
            weights={"r1": 2.5},
        )
        assert terms[0].weight == pytest.approx(2.5)

    def test_build_objective_terms_fixed_costs(self) -> None:
        m = TaskCompResourceVolumeMin()
        terms = m.build_objective_terms(
            resource_keys=("r1",),
            resource_capacities={"r1": 100.0},
            fixed_costs={"r1": 10.0},
        )
        assert terms[0].fixed_cost == pytest.approx(10.0)

    def test_compute_volume_savings(self) -> None:
        m = TaskCompResourceVolumeMin()
        result = m.compute_volume_savings(
            original_volumes={"r1": 100.0, "r2": 200.0},
            optimized_volumes={"r1": 80.0, "r2": 150.0},
        )
        assert result.original_volume == pytest.approx(300.0)
        assert result.optimized_volume == pytest.approx(230.0)

    def test_objective_name_for(self) -> None:
        m = TaskCompResourceVolumeMin()
        assert m.objective_name_for("r1") == "resource_volume_min_r1"

    def test_var_name(self) -> None:
        m = TaskCompResourceVolumeMin()
        assert m._var_name("r1") == "volume_r1"


# ==================== ProduceVolumeMinimization tests ====================


class TestProduceVolumeSavings:
    """VolumeSavingsResult (produce) behavioral tests."""

    def test_savings_ratio_normal(self) -> None:
        r = ProduceVolumeSavings(original_volume=200.0, optimized_volume=150.0)
        assert r.savings_ratio == pytest.approx(0.25)

    def test_savings_ratio_zero_original(self) -> None:
        r = ProduceVolumeSavings(original_volume=0.0, optimized_volume=0.0)
        assert r.savings_ratio == pytest.approx(0.0)


class TestProduceVolumeMinimization:
    """ProduceVolumeMinimization behavioral tests."""

    def test_defaults(self) -> None:
        m = ProduceVolumeMinimization()
        assert m.objective_name == "produce_volume_min"
        assert m.default_weight == pytest.approx(1.0)

    def test_build_objective_terms_basic(self) -> None:
        m = ProduceVolumeMinimization()
        terms = m.build_objective_terms(
            produce_keys=("p1", "p2"),
            produce_capacities={"p1": 50.0, "p2": 100.0},
        )
        assert len(terms) == 2
        assert terms[0].produce_key == "p1"
        assert terms[1].produce_key == "p2"

    def test_build_objective_terms_empty(self) -> None:
        m = ProduceVolumeMinimization()
        terms = m.build_objective_terms(produce_keys=(), produce_capacities={})
        assert len(terms) == 0

    def test_build_objective_terms_zero_weight_skipped(self) -> None:
        m = ProduceVolumeMinimization()
        terms = m.build_objective_terms(
            produce_keys=("p1",),
            produce_capacities={"p1": 50.0},
            weights={"p1": 0.0},
        )
        assert len(terms) == 0

    def test_build_objective_terms_custom_weights(self) -> None:
        m = ProduceVolumeMinimization()
        terms = m.build_objective_terms(
            produce_keys=("p1",),
            produce_capacities={"p1": 50.0},
            weights={"p1": 3.0},
        )
        assert terms[0].weight == pytest.approx(3.0)

    def test_build_objective_terms_fixed_costs(self) -> None:
        m = ProduceVolumeMinimization()
        terms = m.build_objective_terms(
            produce_keys=("p1",),
            produce_capacities={"p1": 50.0},
            fixed_costs={"p1": 5.0},
        )
        assert terms[0].fixed_cost == pytest.approx(5.0)

    def test_compute_volume_savings(self) -> None:
        m = ProduceVolumeMinimization()
        result = m.compute_volume_savings(
            original_volumes={"p1": 100.0},
            optimized_volumes={"p1": 80.0},
        )
        assert result.original_volume == pytest.approx(100.0)
        assert result.optimized_volume == pytest.approx(80.0)

    def test_objective_name_for(self) -> None:
        m = ProduceVolumeMinimization()
        assert m.objective_name_for("p1") == "produce_volume_min_p1"

    def test_var_name(self) -> None:
        m = ProduceVolumeMinimization()
        assert m._var_name("p1") == "volume_p1"


# ==================== ResourceVolumeMinimization (resource) tests ====================


class TestResourceVolumeSavings:
    """VolumeSavingsResult (resource) behavioral tests."""

    def test_savings_ratio_normal(self) -> None:
        r = ResourceVolumeSavings(original_volume=150.0, optimized_volume=100.0)
        assert r.savings_ratio == pytest.approx(1.0 - 100.0 / 150.0)

    def test_savings_ratio_zero_original(self) -> None:
        r = ResourceVolumeSavings(original_volume=0.0, optimized_volume=0.0)
        assert r.savings_ratio == pytest.approx(0.0)


class TestResourceVolumeMinimization:
    """ResourceVolumeMinimization (resource domain) behavioral tests."""

    def test_defaults(self) -> None:
        m = ResourceVolumeMinimization()
        assert m.objective_name == "resource_volume_min"
        assert m.default_weight == pytest.approx(1.0)
        assert m.fixed_cost_weight == pytest.approx(0.0)

    def test_build_objective_terms_basic(self) -> None:
        m = ResourceVolumeMinimization()
        terms = m.build_objective_terms(
            resource_keys=("r1",),
            resource_capacities={"r1": 100.0},
        )
        assert len(terms) == 1
        assert terms[0].resource_key == "r1"
        assert terms[0].weight == pytest.approx(1.0)

    def test_build_objective_terms_empty(self) -> None:
        m = ResourceVolumeMinimization()
        terms = m.build_objective_terms(resource_keys=(), resource_capacities={})
        assert len(terms) == 0

    def test_build_objective_terms_zero_weight_skipped(self) -> None:
        m = ResourceVolumeMinimization()
        terms = m.build_objective_terms(
            resource_keys=("r1",),
            resource_capacities={"r1": 100.0},
            weights={"r1": 0.0},
        )
        assert len(terms) == 0

    def test_build_objective_terms_custom_weights(self) -> None:
        m = ResourceVolumeMinimization()
        terms = m.build_objective_terms(
            resource_keys=("r1",),
            resource_capacities={"r1": 100.0},
            weights={"r1": 2.0},
        )
        assert terms[0].weight == pytest.approx(2.0)

    def test_build_objective_terms_fixed_costs(self) -> None:
        m = ResourceVolumeMinimization()
        terms = m.build_objective_terms(
            resource_keys=("r1",),
            resource_capacities={"r1": 100.0},
            fixed_costs={"r1": 7.5},
        )
        assert terms[0].fixed_cost == pytest.approx(7.5)

    def test_compute_volume_savings(self) -> None:
        m = ResourceVolumeMinimization()
        result = m.compute_volume_savings(
            original_volumes={"r1": 100.0, "r2": 200.0},
            optimized_volumes={"r1": 90.0, "r2": 160.0},
        )
        assert result.original_volume == pytest.approx(300.0)
        assert result.optimized_volume == pytest.approx(250.0)

    def test_objective_name_for(self) -> None:
        m = ResourceVolumeMinimization()
        assert m.objective_name_for("r1") == "resource_volume_min_r1"

    def test_var_name(self) -> None:
        m = ResourceVolumeMinimization()
        assert m._var_name("r1") == "volume_r1"
