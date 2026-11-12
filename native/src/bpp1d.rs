//! BPP1D 精确领域上下文；候选和放置由固定 Rust 内核生成。 / Exact BPP1D context; candidates and placements come from the pinned Rust kernel.

use std::cell::RefCell;
use std::collections::{BTreeMap, BTreeSet};
use std::rc::Rc;

use num_bigint::BigInt;
use num_traits::{Signed, Zero};
use ospf_rust_core::error::{CoreError, Result as CoreResult};
use ospf_rust_core::model::intermediate::LinearTriadModel;
use ospf_rust_core::model::{LinearModelSnapshot, ObjectiveCategory};
use ospf_rust_core::solver::{
    SolveReport, SolveValue, SolveValueConversionPolicy, convert_mechanism_model_to_f64,
    linear_model_fingerprint, linear_model_mapping,
};
use ospf_rust_core::variable::VariableId;
use ospf_rust_framework_bpp::infrastructure::SameUnitPackingValueAdapter;
use ospf_rust_framework_bpp1d::domain::{
    AcceptAllPatterns, BinType, Item, PackingContext, PackingModelStage, PackingObjective,
    PackingPattern, PackingProblem, PackingResult, PatternAssignmentContext,
    PatternGenerationConfig, PatternGenerationResult, PatternModelingExtension, PatternPolicy,
};
use ospf_rust_quantities::quantity::Quantity;
use ospf_rust_quantities::unit::Unit;
use pyo3::prelude::*;
use pyo3::types::PyBool;

use crate::bpp1d_extension::{ExtensionState, PythonExtension, Reference, reference};
use crate::control::SolveHandle;
use crate::failure::{Failure, Transport, transport, transport_unit};
use crate::numeric::Rational;
use crate::quantities::QuantityUnit;
use crate::safe_rational::SafeRational;
use crate::solve::SolveRequest;

type ItemInput = (
    String,
    Py<Rational>,
    Py<Rational>,
    u64,
    BTreeMap<String, u64>,
);
type BinInput = (
    String,
    Py<Rational>,
    Py<Rational>,
    Py<Rational>,
    Option<u64>,
);
pub(crate) type PatternInput = (String, BTreeMap<String, u64>);
type UsageInput = (String, BTreeMap<String, u64>, u64);
type Generated = (Vec<PatternInput>, bool, usize);
pub(crate) type Ratio = (BigInt, BigInt);
type Placement = (String, Ratio, Ratio);
type Plan = (String, String, Vec<Placement>);
type Interval = (String, Ratio, Ratio);
type Packed = (
    Vec<Plan>,
    Vec<Interval>,
    BTreeMap<String, u64>,
    Ratio,
    Ratio,
    Ratio,
);
#[cfg(test)]
type Assignment = PatternAssignmentContext<SafeRational, Unit, Unit>;
type VerifiedSolution = (Vec<UsageInput>, Packed, Ratio, BTreeMap<String, String>);
pub(crate) type Column = (Reference, (usize, usize), Option<PatternInput>);
pub(crate) type ExtensionCallbacks = Option<(Py<PyAny>, Py<PyAny>)>;
pub(crate) type FinalSolved = (
    u64,
    String,
    Vec<Column>,
    Option<VerifiedSolution>,
    Option<Failure>,
);
type Solved = (
    u64,
    String,
    Vec<PatternInput>,
    Vec<Column>,
    bool,
    usize,
    Option<VerifiedSolution>,
    Option<Failure>,
);

#[pyclass(frozen, module = "ospf_python._native")]
pub struct Bpp1dContext {
    pub(crate) context: PackingContext<SafeRational, Unit, Unit>,
}

struct PythonPatternPolicy {
    callback: Py<PyAny>,
    error: RefCell<Option<PyErr>>,
}

impl PatternPolicy for PythonPatternPolicy {
    fn accept(&self, pattern: &PackingPattern) -> CoreResult<bool> {
        let result = Python::attach(|py| -> PyResult<Option<bool>> {
            let snapshot = (pattern.bin_type_id.clone(), pattern.amounts.clone());
            let returned = self.callback.bind(py).call1((snapshot,))?;
            if returned.is_none() {
                Ok(None)
            } else if returned.is_instance_of::<PyBool>() {
                returned.extract().map(Some)
            } else {
                Err(pyo3::exceptions::PyTypeError::new_err(
                    "候选策略须返回 bool 或 None / Pattern policy must return bool or None",
                ))
            }
        });
        match result {
            Ok(Some(accepted)) => Ok(accepted),
            Ok(None) => Err(CoreError::callback_error(
                "候选策略失败 / Pattern policy failed",
            )),
            Err(error) => {
                *self.error.borrow_mut() = Some(error);
                Err(CoreError::callback_error(
                    "候选策略异常 / Pattern policy raised",
                ))
            }
        }
    }
}

fn generate(
    context: &PackingContext<SafeRational, Unit, Unit>,
    config: PatternGenerationConfig,
    callback: Option<Py<PyAny>>,
) -> PyResult<Result<PatternGenerationResult, Failure>> {
    let Some(callback) = callback else {
        return Ok(context
            .generate_patterns(config, &AcceptAllPatterns)
            .map_err(Failure::from));
    };
    let policy = PythonPatternPolicy {
        callback,
        error: RefCell::new(None),
    };
    let result = context.generate_patterns(config, &policy);
    let error = policy.error.borrow_mut().take();
    Python::attach(|_| drop(policy));
    if let Some(error) = error {
        Err(error)
    } else {
        Ok(result.map_err(Failure::from))
    }
}

fn ratio(value: SafeRational) -> Ratio {
    value.0.into_raw()
}

pub(crate) fn pattern((bin_type_id, amounts): PatternInput) -> PackingPattern {
    PackingPattern {
        bin_type_id,
        amounts,
    }
}

fn packed(result: PackingResult<SafeRational, Unit>) -> Packed {
    let plans = result
        .plans
        .into_iter()
        .map(|plan| {
            (
                plan.bin_id,
                plan.bin_type_id,
                plan.placements
                    .into_iter()
                    .map(|placement| {
                        (
                            placement.item_id,
                            ratio(placement.start.value),
                            ratio(placement.length.value),
                        )
                    })
                    .collect(),
            )
        })
        .collect();
    let intervals = result
        .free_intervals
        .into_iter()
        .map(|interval| {
            (
                interval.bin_id,
                ratio(interval.start.value),
                ratio(interval.length.value),
            )
        })
        .collect();
    (
        plans,
        intervals,
        result.materials,
        ratio(result.total_length.value),
        ratio(result.packed_length.value),
        ratio(result.objective),
    )
}

pub(crate) fn serialize_report(report: &SolveReport<f64>) -> Result<String, Failure> {
    let raw = crate::solve::serialize(report)?;
    if serde_json::from_str::<SolveReport<f64>>(&raw).ok().as_ref() != Some(report) {
        return Err(Failure::binding(
            "DATA_LOSS",
            "报告无法无损序列化 / Report cannot be serialized losslessly",
        ));
    }
    Ok(raw)
}

#[derive(Debug)]
enum ReportColumn {
    Pattern(PackingPattern, VariableId),
    Auxiliary(VariableId),
}

fn compiled_columns<E: PatternModelingExtension<SafeRational, Unit, Unit>>(
    assignment: &PatternAssignmentContext<SafeRational, Unit, Unit, E>,
    snapshot: &LinearModelSnapshot<SafeRational>,
    compiled: &LinearTriadModel,
) -> Result<Vec<ReportColumn>, Failure> {
    if !snapshot.objective_constant.is_zero() {
        return Err(Failure::binding(
            "NOT_SUPPORTED",
            "固定 Rust revision 未保留线性目标常数 / Pinned Rust revision does not preserve linear objective constants",
        ));
    }
    let by_id = assignment
        .aggregation()
        .variables
        .iter()
        .map(|(pattern, id)| (*id, pattern))
        .collect::<BTreeMap<_, _>>();
    let source_ids = snapshot
        .variables
        .iter()
        .map(|variable| variable.variable)
        .collect::<BTreeSet<_>>();
    let compiled_ids = compiled
        .basic
        .variables
        .iter()
        .map(|variable| variable.id())
        .collect::<BTreeSet<_>>();
    if by_id.len() != assignment.aggregation().variables.len()
        || source_ids.len() != snapshot.variables.len()
        || compiled_ids.len() != compiled.basic.variables.len()
        || source_ids != compiled_ids
        || by_id.keys().any(|id| !source_ids.contains(id))
        || compiled.c.len() != compiled.basic.variables.len()
        || compiled.objective_category != ObjectiveCategory::Minimum
    {
        return Err(Failure::binding(
            "DATA_LOSS",
            "源变量与编译列不一致 / Source variables do not match compiled columns",
        ));
    }
    compiled
        .basic
        .variables
        .iter()
        .zip(&compiled.c)
        .map(|(variable, coefficient)| {
            let id = variable.id();
            let expected = snapshot
                .objective
                .get(&id)
                .cloned()
                .unwrap_or_else(SafeRational::zero)
                .to_f64_with_policy(SolveValueConversionPolicy::Strict)
                .map_err(Failure::from)?;
            if expected != *coefficient {
                return Err(Failure::binding(
                    "DATA_LOSS",
                    "源目标与编译目标不一致 / Source objective does not match compiled objective",
                ));
            }
            Ok(match by_id.get(&id) {
                Some(pattern) => ReportColumn::Pattern((*pattern).clone(), id),
                None => ReportColumn::Auxiliary(id),
            })
        })
        .collect()
}

struct PreparedAssignment {
    assignment: PatternAssignmentContext<SafeRational, Unit, Unit, PythonExtension>,
    snapshot: LinearModelSnapshot<SafeRational>,
    compiled: LinearTriadModel,
    columns: Vec<Column>,
}

pub(crate) struct FrozenLp {
    pub(crate) snapshot: LinearModelSnapshot<SafeRational>,
    pub(crate) compiled: LinearTriadModel,
    pub(crate) columns: Vec<Column>,
}

fn verify_lp_relaxation(
    original: &LinearModelSnapshot<SafeRational>,
    relaxed: &LinearModelSnapshot<SafeRational>,
) -> Result<(), Failure> {
    let variables = original
        .variables
        .iter()
        .map(|variable| variable.relaxed().map_err(Failure::from))
        .collect::<Result<Vec<_>, _>>()?;
    if variables != relaxed.variables
        || original.objective != relaxed.objective
        || original.objective_constant != relaxed.objective_constant
        || original.objective_category != relaxed.objective_category
        || original.rows.len() != relaxed.rows.len()
        || original
            .rows
            .iter()
            .map(|row| &row.id)
            .collect::<BTreeSet<_>>()
            .len()
            != original.rows.len()
        || relaxed
            .rows
            .iter()
            .map(|row| &row.id)
            .collect::<BTreeSet<_>>()
            .len()
            != relaxed.rows.len()
        || original
            .rows
            .iter()
            .zip(&relaxed.rows)
            .any(|(left, right)| {
                right.source_name != left.id
                    || left.coefficients != right.coefficients
                    || left.rhs != right.rhs
                    || left.relation != right.relation
                    || left.group_id != right.group_id
                    || left.lazy != right.lazy
                    || left.priority != right.priority
                    || left.args != right.args
                    || left.source_symbol_id != right.source_symbol_id
            })
    {
        return Err(Failure::binding(
            "DATA_LOSS",
            "LP 松弛与注册模型不一致 / LP relaxation differs from the registered model",
        ));
    }
    Ok(())
}

fn prepare_assignment(
    packing: PackingContext<SafeRational, Unit, Unit>,
    patterns: Vec<PackingPattern>,
    stage: PackingModelStage,
    callbacks: ExtensionCallbacks,
    state: &Rc<ExtensionState>,
) -> Result<PreparedAssignment, Failure> {
    if !state.begin() {
        return Err(Failure::binding(
            "FAILED_PRECONDITION",
            "扩展状态必须独立 / Extension state must be fresh",
        ));
    }
    let has_extension = callbacks.is_some();
    let assignment = PatternAssignmentContext::new(
        packing,
        patterns,
        stage,
        PythonExtension {
            callbacks,
            state: Rc::clone(state),
        },
    )
    .map_err(Failure::from)?;
    let snapshot = assignment
        .model()
        .linear_model_snapshot()
        .map_err(Failure::from)?;
    let owner = snapshot.revision.owner;
    if owner != assignment.model().model_identity() {
        return Err(Failure::binding(
            "DATA_LOSS",
            "模型快照身份不一致 / Model snapshot identity mismatch",
        ));
    }
    let registration_owner = if stage == PackingModelStage::Lp {
        let original = state.take_lp_origin().ok_or_else(|| {
            Failure::binding(
                "DATA_LOSS",
                "LP 注册快照缺失 / LP registration snapshot missing",
            )
        })?;
        verify_lp_relaxation(&original, &snapshot)?;
        original.revision.owner
    } else {
        owner
    };
    let mechanism = assignment
        .model()
        .try_to_mechanism_model()
        .map_err(Failure::from)?;
    let compiled = convert_mechanism_model_to_f64(&mechanism, SolveValueConversionPolicy::Strict)
        .and_then(|model| model.try_into_linear_triad_model_with_status_callback(None))
        .map_err(Failure::from)?;
    let registered = compiled_columns(&assignment, &snapshot, &compiled)?;
    if has_extension && state.reference_count() != registered.len() {
        return Err(Failure::binding(
            "DATA_LOSS",
            "扩展变量映射不完整 / Incomplete extension variable mapping",
        ));
    }
    let names = snapshot
        .variables
        .iter()
        .map(|variable| (variable.variable, &variable.name))
        .collect::<BTreeMap<_, _>>();
    let columns = registered
        .into_iter()
        .map(|column| match column {
            ReportColumn::Pattern(pattern, id) => {
                let value = (pattern.bin_type_id, pattern.amounts);
                if has_extension
                    && (state.lookup(id).as_ref() != Some(&reference(registration_owner, id))
                        || state.pattern(id).as_ref() != Some(&value))
                {
                    return Err(Failure::binding(
                        "DATA_LOSS",
                        "候选列身份缺失 / Candidate identity missing",
                    ));
                }
                Ok((
                    reference(owner, id),
                    (id.group_id, id.index_in_group),
                    Some(value),
                ))
            }
            ReportColumn::Auxiliary(id) => {
                let mut key = state
                    .lookup(id)
                    .filter(|key| {
                        key.0 == registration_owner
                            && key.1.is_none()
                            && key.2.is_some()
                            && key.2.as_ref() == names.get(&id).copied()
                            && state.pattern(id).is_none()
                    })
                    .ok_or_else(|| {
                        Failure::binding(
                            "DATA_LOSS",
                            "未声明的辅助列 / Undeclared auxiliary column",
                        )
                    })?;
                key.0 = owner;
                Ok((key, (id.group_id, id.index_in_group), None))
            }
        })
        .collect::<Result<Vec<_>, Failure>>()?;
    state.rebind(owner);
    Ok(PreparedAssignment {
        assignment,
        snapshot,
        compiled,
        columns,
    })
}

pub(crate) fn prepare_lp(
    packing: PackingContext<SafeRational, Unit, Unit>,
    patterns: Vec<PackingPattern>,
    callbacks: ExtensionCallbacks,
) -> PyResult<Result<FrozenLp, Failure>> {
    let state = Rc::new(ExtensionState::default());
    let result = prepare_assignment(packing, patterns, PackingModelStage::Lp, callbacks, &state);
    let error = state.take_error();
    let result = result.map(|prepared| {
        let PreparedAssignment {
            assignment,
            snapshot,
            compiled,
            columns,
        } = prepared;
        Python::attach(|_| drop(assignment));
        FrozenLp {
            snapshot,
            compiled,
            columns,
        }
    });
    Python::attach(|_| drop(state));
    match error {
        Some(error) => Err(error),
        None => Ok(result),
    }
}

fn verify_solution<E: PatternModelingExtension<SafeRational, Unit, Unit>>(
    assignment: &PatternAssignmentContext<SafeRational, Unit, Unit, E>,
    packing: &PackingContext<SafeRational, Unit, Unit>,
    compiled: &LinearTriadModel,
    report: &SolveReport<f64>,
    expansion_limit: u64,
) -> Result<VerifiedSolution, Failure> {
    let snapshot = assignment
        .model()
        .linear_model_snapshot()
        .map_err(Failure::from)?;
    compiled_columns(assignment, &snapshot, compiled)?;
    let solution = report.solution.as_ref().ok_or_else(|| {
        Failure::binding("NO_SOLUTION", "后端没有解 / Backend returned no solution")
    })?;
    if report.model_mapping.as_ref()
        != Some(&linear_model_mapping(compiled).map_err(Failure::from)?)
        || report.fingerprints.model.as_ref()
            != Some(&linear_model_fingerprint(compiled).map_err(Failure::from)?)
        || solution.values.len() != compiled.basic.variables.len()
    {
        return Err(Failure::binding(
            "DATA_LOSS",
            "报告与编译模型不一致 / Report does not match compiled model",
        ));
    }
    let values = compiled
        .basic
        .variables
        .iter()
        .zip(&solution.values)
        .map(|(variable, value)| {
            SafeRational::from_f64_with_policy(*value, SolveValueConversionPolicy::Strict)
                .map(|value| (variable.id(), value))
                .map_err(Failure::from)
        })
        .collect::<Result<BTreeMap<_, _>, _>>()?;
    if values.len() != compiled.basic.variables.len() || values.len() != snapshot.variables.len() {
        return Err(Failure::binding(
            "DATA_LOSS",
            "变量映射不完整 / Incomplete variable mapping",
        ));
    }
    let ordered = snapshot
        .variables
        .iter()
        .map(|variable| {
            values.get(&variable.variable).cloned().ok_or_else(|| {
                Failure::binding("DATA_LOSS", "源变量缺失 / Source variable missing")
            })
        })
        .collect::<Result<Vec<_>, _>>()?;
    let extracted = assignment
        .extract_solution(&ordered, &SafeRational::zero())
        .map_err(Failure::from)?;
    let objective = snapshot.objective.iter().try_fold(
        snapshot.objective_constant.clone(),
        |total, (id, coefficient)| {
            values
                .get(id)
                .map(|value| total + coefficient.clone() * value.clone())
                .ok_or_else(|| {
                    Failure::binding("DATA_LOSS", "目标变量缺失 / Objective variable missing")
                })
        },
    )?;
    let result = packing
        .pack(&extracted.usages, expansion_limit)
        .map_err(Failure::from)?;
    let usages = extracted
        .usages
        .into_iter()
        .map(|(pattern, count)| (pattern.bin_type_id, pattern.amounts, count))
        .collect();
    Ok((
        usages,
        packed(result),
        ratio(objective),
        extracted.indicators,
    ))
}

pub(crate) fn solve_final(
    packing: PackingContext<SafeRational, Unit, Unit>,
    patterns: Vec<PackingPattern>,
    callbacks: ExtensionCallbacks,
    request: SolveRequest,
    expansion_limit: u64,
) -> PyResult<Result<FinalSolved, Failure>> {
    let state = Rc::new(ExtensionState::default());
    let result = (|| {
        let PreparedAssignment {
            assignment,
            snapshot,
            compiled,
            columns,
        } = prepare_assignment(
            packing.clone(),
            patterns,
            PackingModelStage::FinalMilp,
            callbacks,
            &state,
        )?;
        let result = (|| {
            let identity = snapshot.revision.owner;
            let report = crate::solve::execute_compiled(identity, request, &compiled)?;
            let raw = serialize_report(&report)?;
            let (solution, error) = transport(verify_solution(
                &assignment,
                &packing,
                &compiled,
                &report,
                expansion_limit,
            ));
            Ok((identity, raw, columns, solution, error))
        })();
        Python::attach(|_| drop(assignment));
        result
    })();
    let error = state.take_error();
    Python::attach(|_| drop(state));
    match error {
        Some(error) => Err(error),
        None => Ok(result),
    }
}

#[pyfunction]
#[pyo3(signature = (*, items, bins, spacing, length_unit, weight_unit, objective))]
pub fn _create_bpp1d_context(
    py: Python<'_>,
    items: Vec<ItemInput>,
    bins: Vec<BinInput>,
    spacing: &Rational,
    length_unit: &QuantityUnit,
    weight_unit: &QuantityUnit,
    objective: String,
) -> Transport<Bpp1dContext> {
    let dimensions_match = length_unit.dimensions() == [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        && weight_unit.dimensions() == [1, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    let length_unit = length_unit.cloned_unit();
    let weight_unit = weight_unit.cloned_unit();
    let spacing = SafeRational(spacing.value.clone());
    let items = items
        .into_iter()
        .map(|(id, length, weight, amount, materials)| Item {
            id,
            length: Quantity::new(
                SafeRational(length.borrow(py).value.clone()),
                length_unit.clone(),
            ),
            weight: Quantity::new(
                SafeRational(weight.borrow(py).value.clone()),
                weight_unit.clone(),
            ),
            amount,
            materials,
        })
        .collect();
    let bins = bins
        .into_iter()
        .map(|(id, length, weight, cost, inventory)| BinType {
            id,
            length: Quantity::new(
                SafeRational(length.borrow(py).value.clone()),
                length_unit.clone(),
            ),
            max_weight: Quantity::new(
                SafeRational(weight.borrow(py).value.clone()),
                weight_unit.clone(),
            ),
            cost: SafeRational(cost.borrow(py).value.clone()),
            inventory,
        })
        .collect();
    transport(py.detach(|| {
        if !dimensions_match {
            return Err(Failure::input(
                "装箱单位需要长度和质量量纲 / Packing units require length and mass dimensions",
            ));
        }
        if !length_unit.is_linear()
            || !weight_unit.is_linear()
            || !length_unit.scale().value().is_positive()
            || !weight_unit.scale().value().is_positive()
        {
            return Err(Failure::input(
                "装箱单位必须线性且比例为正 / Packing units must be linear with positive scale",
            ));
        }
        let objective = match objective.as_str() {
            "bin_count" => PackingObjective::BinCount,
            "consumed_length" => PackingObjective::ConsumedLength,
            "cost" => PackingObjective::Cost,
            _ => return Err(Failure::input("未知装箱目标 / Unknown packing objective")),
        };
        let problem = PackingProblem {
            items,
            bin_types: bins,
            spacing: Quantity::new(spacing, length_unit.clone()),
            length_unit,
            weight_unit,
            objective,
        };
        PackingContext::new(
            problem,
            &SameUnitPackingValueAdapter,
            &SameUnitPackingValueAdapter,
        )
        .map(|context| Bpp1dContext { context })
        .map_err(Failure::from)
    }))
}

#[pymethods]
impl Bpp1dContext {
    #[pyo3(signature = (*, patterns, extension=None))]
    fn column_pool(
        &self,
        py: Python<'_>,
        patterns: Vec<PatternInput>,
        extension: ExtensionCallbacks,
    ) -> PyResult<Transport<crate::bpp1d_pool::Bpp1dPool>> {
        if extension.as_ref().is_some_and(|(register, extract)| {
            !register.bind(py).is_callable() || !extract.bind(py).is_callable()
        }) {
            return Ok(transport(Err(Failure::input(
                "建模扩展回调必须可调用 / Modeling extension callbacks must be callable",
            ))));
        }
        let weak_callbacks = match crate::bpp1d_pool::weak_callbacks(py, &extension) {
            Ok(callbacks) => callbacks,
            Err(error) => return Ok(transport(Err(error))),
        };
        py.detach(|| {
            crate::bpp1d_pool::Bpp1dPool::create(
                self.context.clone(),
                patterns,
                extension,
                weak_callbacks,
            )
        })
        .map(transport)
    }

    #[pyo3(signature = (*, max_patterns, max_nodes, policy=None))]
    fn generate_patterns(
        &self,
        py: Python<'_>,
        max_patterns: usize,
        max_nodes: usize,
        policy: Option<Py<PyAny>>,
    ) -> PyResult<Transport<Generated>> {
        if policy
            .as_ref()
            .is_some_and(|value| !value.bind(py).is_callable())
        {
            return Ok(transport(Err(Failure::input(
                "候选策略必须可调用 / Pattern policy must be callable",
            ))));
        }
        if max_patterns == 0 || max_nodes == 0 {
            return Ok(transport(Err(Failure::input(
                "搜索预算必须为正 / Search budgets must be positive",
            ))));
        }
        let generated = py.detach(|| {
            generate(
                &self.context,
                PatternGenerationConfig {
                    max_patterns,
                    max_nodes,
                },
                policy,
            )
        })?;
        Ok(transport(generated.map(|generated| {
            (
                generated
                    .patterns
                    .into_iter()
                    .map(|pattern| (pattern.bin_type_id, pattern.amounts))
                    .collect(),
                generated.complete,
                generated.visited_nodes,
            )
        })))
    }

    #[pyo3(signature = (*, bin_type_id, amounts))]
    fn validate_pattern(
        &self,
        py: Python<'_>,
        bin_type_id: String,
        amounts: BTreeMap<String, u64>,
    ) -> Transport<()> {
        transport_unit(py.detach(|| {
            self.context
                .validate_pattern(&pattern((bin_type_id, amounts)))
                .map_err(Failure::from)
        }))
    }

    #[pyo3(signature = (*, usages, expansion_limit))]
    fn pack(
        &self,
        py: Python<'_>,
        usages: Vec<UsageInput>,
        expansion_limit: u64,
    ) -> Transport<Packed> {
        transport(py.detach(|| {
            let mut by_pattern = BTreeMap::new();
            for (bin_type_id, amounts, count) in usages {
                if by_pattern
                    .insert(pattern((bin_type_id, amounts)), count)
                    .is_some()
                {
                    return Err(Failure::input("组合用量重复 / Duplicate pattern usage"));
                }
            }
            let result = self
                .context
                .pack(&by_pattern, expansion_limit)
                .map_err(Failure::from)?;
            Ok(packed(result))
        }))
    }

    #[pyo3(signature = (*, solver, max_patterns, max_nodes, expansion_limit, time_limit=None, cancellation=None, on_progress=None, policy=None, extension=None))]
    #[allow(clippy::too_many_arguments)]
    fn solve(
        &self,
        py: Python<'_>,
        solver: String,
        max_patterns: usize,
        max_nodes: usize,
        expansion_limit: u64,
        time_limit: Option<f64>,
        cancellation: Option<SolveHandle>,
        on_progress: Option<Py<PyAny>>,
        policy: Option<Py<PyAny>>,
        extension: Option<(Py<PyAny>, Py<PyAny>)>,
    ) -> PyResult<Transport<Solved>> {
        if on_progress
            .as_ref()
            .is_some_and(|callback| !callback.bind(py).is_callable())
        {
            return Ok(transport(Err(Failure::input(
                "进度回调必须可调用 / Progress callback must be callable",
            ))));
        }
        if policy
            .as_ref()
            .is_some_and(|value| !value.bind(py).is_callable())
        {
            return Ok(transport(Err(Failure::input(
                "候选策略必须可调用 / Pattern policy must be callable",
            ))));
        }
        if extension.as_ref().is_some_and(|(register, extract)| {
            !register.bind(py).is_callable() || !extract.bind(py).is_callable()
        }) {
            return Ok(transport(Err(Failure::input(
                "建模扩展回调必须可调用 / Modeling extension callbacks must be callable",
            ))));
        }
        let request = SolveRequest {
            solver,
            time_limit,
            cancellation,
            on_progress,
        };
        let generated = py.detach(|| {
            generate(
                &self.context,
                PatternGenerationConfig {
                    max_patterns,
                    max_nodes,
                },
                policy,
            )
        })?;
        py.detach(|| {
            let state = Rc::new(ExtensionState::default());
            let result = (|| -> Result<Solved, Failure> {
                let generated = generated?;
                let PreparedAssignment {
                    assignment,
                    compiled,
                    columns: compiled_columns,
                    snapshot: _,
                } = prepare_assignment(
                    self.context.clone(),
                    generated.patterns,
                    PackingModelStage::Milp,
                    extension,
                    &state,
                )?;
                let identity = assignment.model().model_identity();
                let columns = compiled_columns
                    .iter()
                    .filter_map(|column| column.2.clone())
                    .collect();
                let report = crate::solve::execute_compiled(identity, request, &compiled)?;
                let raw = serialize_report(&report)?;
                let (solution, error) = transport(verify_solution(
                    &assignment,
                    &self.context,
                    &compiled,
                    &report,
                    expansion_limit,
                ));
                Ok((
                    identity,
                    raw,
                    columns,
                    compiled_columns,
                    generated.complete,
                    generated.visited_nodes,
                    solution,
                    error,
                ))
            })();
            let error = state.take_error();
            Python::attach(|_| drop(state));
            match error {
                Some(error) => Err(error),
                None => Ok(transport(result)),
            }
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::One;
    use ospf_rust_core::model::flatten::{Linear, LinearMonomial};
    use ospf_rust_core::model::{ConstraintRelation, MetaModel, SubObjective};
    use ospf_rust_core::solver::{
        ProblemStatus, SolveFingerprints, SolveSolution, TerminationReason,
    };
    use ospf_rust_core::token::TokenVariableData;
    use ospf_rust_core::variable::{VariableId, VariableType, new_standalone_id};
    use ospf_rust_framework_bpp1d::domain::{
        NoPatternExtension, PatternAggregation, PatternModelingExtension,
    };
    use ospf_rust_quantities::unit::{CTUnit, Kilogram, Meter};
    use std::cell::Cell;
    use std::rc::Rc;

    struct ExtraVariable(RefCell<Option<VariableId>>, SafeRational, Rc<Cell<usize>>);

    impl PatternModelingExtension<SafeRational, Unit, Unit> for ExtraVariable {
        fn register(
            &self,
            model: &mut MetaModel<SafeRational>,
            _: &PackingContext<SafeRational, Unit, Unit>,
            aggregation: &PatternAggregation<SafeRational>,
            _: PackingModelStage,
        ) -> CoreResult<()> {
            let id = new_standalone_id();
            let index = model.register_variable_data(TokenVariableData {
                id,
                index: 0,
                name: "extra".into(),
                display_name: None,
                var_type: VariableType::Integer,
                lower_bound: Some(SafeRational::zero()),
                upper_bound: Some(SafeRational::one()),
            })?;
            let expression = Linear::new(
                vec![LinearMonomial::new(SafeRational::one(), index)],
                SafeRational::zero(),
            );
            model.add_linear_polynomial_constraint(
                expression.clone(),
                ConstraintRelation::Equal,
                SafeRational::one(),
                "extra_required",
            )?;
            let pattern = *aggregation.variables.values().next().unwrap();
            let pattern_index = model
                .tokens()
                .iter()
                .position(|token| token.id() == pattern)
                .unwrap();
            model.add_sub_objective(SubObjective::minimize(
                Linear::new(
                    vec![
                        LinearMonomial::new(SafeRational::one(), index),
                        LinearMonomial::new(
                            SafeRational::one() + SafeRational::one(),
                            pattern_index,
                        ),
                    ],
                    self.1.clone(),
                ),
                "extra_cost",
            ));
            *self.0.borrow_mut() = Some(id);
            Ok(())
        }

        fn extract_solution(
            &self,
            values: &BTreeMap<VariableId, SafeRational>,
        ) -> CoreResult<BTreeMap<String, String>> {
            self.2.set(self.2.get() + 1);
            let id = self.0.borrow().unwrap();
            Ok(BTreeMap::from([(
                "extra".into(),
                values[&id].0.to_string(),
            )]))
        }
    }

    #[test]
    fn extension_variables_are_mapped_and_verified_by_identity() {
        let length = Meter::runtime_unit();
        let mass = Kilogram::runtime_unit();
        let packing = PackingContext::new(
            PackingProblem {
                items: vec![Item {
                    id: "a".into(),
                    length: Quantity::new(SafeRational::one(), length.clone()),
                    weight: Quantity::new(SafeRational::zero(), mass.clone()),
                    amount: 1,
                    materials: BTreeMap::new(),
                }],
                bin_types: vec![BinType {
                    id: "bin".into(),
                    length: Quantity::new(SafeRational::one(), length.clone()),
                    max_weight: Quantity::new(SafeRational::zero(), mass.clone()),
                    cost: SafeRational::one(),
                    inventory: None,
                }],
                spacing: Quantity::new(SafeRational::zero(), length.clone()),
                length_unit: length,
                weight_unit: mass,
                objective: PackingObjective::BinCount,
            },
            &SameUnitPackingValueAdapter,
            &SameUnitPackingValueAdapter,
        )
        .unwrap();
        let candidate = PackingPattern {
            bin_type_id: "bin".into(),
            amounts: BTreeMap::from([("a".into(), 1)]),
        };
        let extractions = Rc::new(Cell::new(0));
        let assignment = PatternAssignmentContext::new(
            packing.clone(),
            [candidate.clone()],
            PackingModelStage::Milp,
            ExtraVariable(
                RefCell::new(None),
                SafeRational::zero(),
                Rc::clone(&extractions),
            ),
        )
        .unwrap();
        let mechanism = assignment.model().try_to_mechanism_model().unwrap();
        let mut compiled =
            convert_mechanism_model_to_f64(&mechanism, SolveValueConversionPolicy::Strict)
                .unwrap()
                .try_into_linear_triad_model_with_status_callback(None)
                .unwrap();
        #[cfg(any(feature = "scip", feature = "gurobi10"))]
        for solver in crate::compiled_solvers() {
            let report = crate::solve::execute_compiled(
                assignment.model().model_identity(),
                SolveRequest {
                    solver: solver.into(),
                    time_limit: None,
                    cancellation: None,
                    on_progress: None,
                },
                &compiled,
            )
            .unwrap();
            let verified = verify_solution(&assignment, &packing, &compiled, &report, 1).unwrap();
            assert_eq!(verified.2, (4.into(), 1.into()));
            assert_eq!(verified.3.get("extra").map(String::as_str), Some("1"));
        }
        compiled.basic.variables.reverse();
        compiled.c.reverse();
        let snapshot = assignment.model().linear_model_snapshot().unwrap();
        let columns = compiled_columns(&assignment, &snapshot, &compiled).unwrap();
        assert!(matches!(columns[0], ReportColumn::Auxiliary(_)));
        assert!(matches!(&columns[1], ReportColumn::Pattern(value, _) if value == &candidate));
        let report = SolveReport::builder(ProblemStatus::Feasible, TerminationReason::Completed)
            .solution(SolveSolution::vector(vec![1.0, 1.0]))
            .model_mapping(Some(linear_model_mapping(&compiled).unwrap()))
            .fingerprints(SolveFingerprints {
                model: Some(linear_model_fingerprint(&compiled).unwrap()),
                ..Default::default()
            })
            .build()
            .unwrap();
        let verified = verify_solution(&assignment, &packing, &compiled, &report, 1).unwrap();
        assert_eq!(
            verified.0,
            vec![("bin".into(), BTreeMap::from([("a".into(), 1)]), 1)]
        );
        assert_eq!(verified.2, (4.into(), 1.into()));
        assert_eq!(verified.3, BTreeMap::from([("extra".into(), "1".into())]));
        assert_eq!(verified.1.5, (1.into(), 1.into()));

        let mut invalid = report.clone();
        invalid.solution.as_mut().unwrap().values[0] = 0.0;
        let extraction_count = extractions.get();
        assert!(verify_solution(&assignment, &packing, &compiled, &invalid, 1).is_err());
        assert_eq!(extractions.get(), extraction_count);
        let mut altered = compiled.clone();
        altered.basic.variables[0] = altered.basic.variables[1].clone();
        assert_eq!(
            compiled_columns(&assignment, &snapshot, &altered)
                .unwrap_err()
                .category,
            "DATA_LOSS"
        );
        altered = compiled.clone();
        altered.basic.variables.pop();
        altered.c.pop();
        assert_eq!(
            compiled_columns(&assignment, &snapshot, &altered)
                .unwrap_err()
                .category,
            "DATA_LOSS"
        );
        altered = compiled.clone();
        altered.c[0] += 1.0;
        assert_eq!(
            compiled_columns(&assignment, &snapshot, &altered)
                .unwrap_err()
                .category,
            "DATA_LOSS"
        );

        let with_constant = PatternAssignmentContext::new(
            packing,
            [candidate],
            PackingModelStage::Milp,
            ExtraVariable(
                RefCell::new(None),
                SafeRational::one(),
                Rc::new(Cell::new(0)),
            ),
        )
        .unwrap();
        let mechanism = with_constant.model().try_to_mechanism_model().unwrap();
        let compiled =
            convert_mechanism_model_to_f64(&mechanism, SolveValueConversionPolicy::Strict)
                .unwrap()
                .try_into_linear_triad_model_with_status_callback(None)
                .unwrap();
        assert_eq!(
            compiled_columns(
                &with_constant,
                &with_constant.model().linear_model_snapshot().unwrap(),
                &compiled,
            )
            .unwrap_err()
            .category,
            "NOT_SUPPORTED"
        );
    }

    #[test]
    fn python_extension_failed_rebuild_keeps_previous_mapping() {
        use pyo3::types::PyDict;

        Python::initialize();
        let (callbacks, globals) = Python::attach(|py| {
            let globals = PyDict::new(py);
            py.run(
                c"fail = True\ndef register(snapshot):\n    if fail and len(snapshot[8]) > 1:\n        return ([('temporary', 'integer', (0, 1), (1, 1))], [], [((snapshot[0], None, 'missing'), (1, 1))], (0, 1))\n    return ([], [], [], (0, 1))\ndef extract(snapshot):\n    return {'ok': str(len(snapshot[6]))}\n",
                Some(&globals),
                None,
            )
            .unwrap();
            (
                (
                    globals.get_item("register").unwrap().unwrap().unbind(),
                    globals.get_item("extract").unwrap().unwrap().unbind(),
                ),
                globals.unbind(),
            )
        });
        let length = Meter::runtime_unit();
        let mass = Kilogram::runtime_unit();
        let item = |id: &str| Item {
            id: id.into(),
            length: Quantity::new(SafeRational::one(), length.clone()),
            weight: Quantity::new(SafeRational::zero(), mass.clone()),
            amount: 1,
            materials: BTreeMap::new(),
        };
        let packing = PackingContext::new(
            PackingProblem {
                items: vec![item("a"), item("b")],
                bin_types: vec![BinType {
                    id: "bin".into(),
                    length: Quantity::new(
                        SafeRational::one() + SafeRational::one(),
                        length.clone(),
                    ),
                    max_weight: Quantity::new(SafeRational::zero(), mass.clone()),
                    cost: SafeRational::one(),
                    inventory: None,
                }],
                spacing: Quantity::new(SafeRational::zero(), length.clone()),
                length_unit: length,
                weight_unit: mass,
                objective: PackingObjective::BinCount,
            },
            &SameUnitPackingValueAdapter,
            &SameUnitPackingValueAdapter,
        )
        .unwrap();
        let mixed = PackingPattern {
            bin_type_id: "bin".into(),
            amounts: BTreeMap::from([("a".into(), 1), ("b".into(), 1)]),
        };
        let single = PackingPattern {
            bin_type_id: "bin".into(),
            amounts: BTreeMap::from([("a".into(), 1)]),
        };
        let state = Rc::new(ExtensionState::default());
        let extension = PythonExtension {
            callbacks: Some(callbacks),
            state: Rc::clone(&state),
        };
        let mut assignment = PatternAssignmentContext::new(
            packing,
            [mixed.clone()],
            PackingModelStage::Milp,
            extension,
        )
        .unwrap();
        let old = assignment.model().linear_model_snapshot().unwrap();
        let old_id = assignment.aggregation().variables[&mixed];
        let old_reference = state.lookup(old_id).unwrap();
        assert!(assignment.add_columns([single.clone()]).is_err());
        assert_eq!(assignment.model().linear_model_snapshot().unwrap(), old);
        assert_eq!(state.lookup(old_id), Some(old_reference.clone()));
        assert_eq!(
            assignment
                .extract_solution(&[SafeRational::one()], &SafeRational::zero())
                .unwrap()
                .indicators["ok"],
            "1"
        );

        Python::attach(|py| globals.bind(py).set_item("fail", false).unwrap());
        assignment.add_columns([single]).unwrap();
        assert_ne!(assignment.model().model_identity(), old.revision.owner);
        assert_eq!(state.lookup(old_id), Some(old_reference));
        let mixed_id = assignment.aggregation().variables[&mixed];
        let values = assignment
            .model()
            .linear_model_snapshot()
            .unwrap()
            .variables
            .iter()
            .map(|variable| {
                if variable.variable == mixed_id {
                    SafeRational::one()
                } else {
                    SafeRational::zero()
                }
            })
            .collect::<Vec<_>>();
        assert_eq!(
            assignment
                .extract_solution(&values, &SafeRational::zero())
                .unwrap()
                .indicators["ok"],
            "2"
        );
        Python::attach(|_| {
            drop(assignment);
            drop(globals);
        });
    }

    fn extension_packing() -> (
        PackingContext<SafeRational, Unit, Unit>,
        PackingPattern,
        PackingPattern,
    ) {
        let length = Meter::runtime_unit();
        let mass = Kilogram::runtime_unit();
        let items = ["a", "b"]
            .into_iter()
            .map(|id| Item {
                id: id.into(),
                length: Quantity::new(SafeRational::one(), length.clone()),
                weight: Quantity::new(SafeRational::zero(), mass.clone()),
                amount: 1,
                materials: BTreeMap::new(),
            })
            .collect();
        let packing = PackingContext::new(
            PackingProblem {
                items,
                bin_types: vec![BinType {
                    id: "bin".into(),
                    length: Quantity::new(
                        SafeRational::one() + SafeRational::one(),
                        length.clone(),
                    ),
                    max_weight: Quantity::new(SafeRational::zero(), mass.clone()),
                    cost: SafeRational::one(),
                    inventory: None,
                }],
                spacing: Quantity::new(SafeRational::zero(), length.clone()),
                length_unit: length,
                weight_unit: mass,
                objective: PackingObjective::BinCount,
            },
            &SameUnitPackingValueAdapter,
            &SameUnitPackingValueAdapter,
        )
        .unwrap();
        let mixed = PackingPattern {
            bin_type_id: "bin".into(),
            amounts: BTreeMap::from([("a".into(), 1), ("b".into(), 1)]),
        };
        let single = PackingPattern {
            bin_type_id: "bin".into(),
            amounts: BTreeMap::from([("a".into(), 1)]),
        };
        (packing, mixed, single)
    }

    fn extension_globals() -> Py<pyo3::types::PyDict> {
        use pyo3::types::PyDict;

        Python::initialize();
        Python::attach(|py| {
            let globals = PyDict::new(py);
            py.run(
                c"seen = []\ndef register(snapshot):\n    seen.append((snapshot[0], snapshot[1]))\n    helper = (snapshot[0], None, 'flag')\n    kind, lower = ('continuous', (1, 3)) if len(snapshot[8]) > 1 else ('binary', None)\n    return ([(\"flag\", kind, lower, (1, 1))], [(\"required\", [(helper, (1, 1))], \"==\", (1, 1))], [(helper, (1, 1))], (0, 1))\ndef extract(snapshot):\n    return {'ok': str(len(snapshot[6]))}\n",
                Some(&globals),
                None,
            )
            .unwrap();
            globals.unbind()
        })
    }

    fn extension_callbacks(globals: &Py<pyo3::types::PyDict>) -> (Py<PyAny>, Py<PyAny>) {
        Python::attach(|py| {
            (
                globals
                    .bind(py)
                    .get_item("register")
                    .unwrap()
                    .unwrap()
                    .unbind(),
                globals
                    .bind(py)
                    .get_item("extract")
                    .unwrap()
                    .unwrap()
                    .unbind(),
            )
        })
    }

    #[test]
    fn prepared_lp_rebinds_only_after_validating_relaxation() {
        let (packing, mixed, _) = extension_packing();
        let globals = extension_globals();
        let state = Rc::new(ExtensionState::default());
        let prepared = prepare_assignment(
            packing.clone(),
            vec![mixed.clone()],
            PackingModelStage::Lp,
            Some(extension_callbacks(&globals)),
            &state,
        )
        .unwrap();
        let snapshot = prepared.assignment.model().linear_model_snapshot().unwrap();
        let final_state = Rc::new(ExtensionState::default());
        let final_master = prepare_assignment(
            packing,
            vec![mixed.clone()],
            PackingModelStage::FinalMilp,
            Some(extension_callbacks(&globals)),
            &final_state,
        )
        .unwrap();
        let seen: Vec<(u64, String)> = Python::attach(|py| {
            globals
                .bind(py)
                .get_item("seen")
                .unwrap()
                .unwrap()
                .extract()
                .unwrap()
        });
        assert_eq!(seen.len(), 2);
        assert_eq!(seen[0].1, "lp");
        assert_ne!(seen[0].0, snapshot.revision.owner);
        assert_eq!(seen[1].1, "final_milp");
        assert_eq!(seen[1].0, final_master.assignment.model().model_identity());
        assert!(
            final_master
                .assignment
                .model()
                .linear_model_snapshot()
                .unwrap()
                .variables
                .iter()
                .any(
                    |variable| variable.name == "flag" && variable.var_type == VariableType::Binary
                )
        );
        assert!(
            snapshot
                .variables
                .iter()
                .all(|v| v.var_type == VariableType::Continuous)
        );
        assert_eq!(prepared.columns.len(), 2);
        for column in &prepared.columns {
            assert_eq!(column.0.0, snapshot.revision.owner);
            let variable = snapshot
                .variables
                .iter()
                .find(|v| (v.variable.group_id, v.variable.index_in_group) == column.1)
                .unwrap();
            assert_eq!(state.lookup(variable.variable).unwrap(), column.0);
        }
        assert!(
            prepared.columns.iter().any(|column| column.2.as_ref()
                == Some(&(mixed.bin_type_id.clone(), mixed.amounts.clone())))
        );
        assert!(
            prepared
                .columns
                .iter()
                .any(|column| column.0.2.as_deref() == Some("flag"))
        );
        Python::attach(|_| {
            drop(prepared);
            drop(state);
            drop(final_master);
            drop(final_state);
            drop(globals);
        });
    }

    #[test]
    fn lp_relaxation_rejects_changed_rows_variables_and_objective() {
        let (packing, mixed, _) = extension_packing();
        let globals = extension_globals();
        let state = Rc::new(ExtensionState::default());
        let assignment = PatternAssignmentContext::new(
            packing,
            [mixed],
            PackingModelStage::Lp,
            PythonExtension {
                callbacks: Some(extension_callbacks(&globals)),
                state: Rc::clone(&state),
            },
        )
        .unwrap();
        let original = state.take_lp_origin().unwrap();
        let relaxed = assignment.model().linear_model_snapshot().unwrap();
        assert!(verify_lp_relaxation(&original, &relaxed).is_ok());
        let mut altered = relaxed.clone();
        altered.variables[0].lower_bound = Some(SafeRational::one());
        assert!(verify_lp_relaxation(&original, &altered).is_err());
        altered = relaxed.clone();
        altered.rows[0].source_name = "forged".into();
        assert!(verify_lp_relaxation(&original, &altered).is_err());
        altered = relaxed.clone();
        altered.rows[1].id = altered.rows[0].id.clone();
        assert!(verify_lp_relaxation(&original, &altered).is_err());
        altered = relaxed.clone();
        altered.rows[0].rhs = altered.rows[0].rhs.clone() + SafeRational::one();
        assert!(verify_lp_relaxation(&original, &altered).is_err());
        altered = relaxed.clone();
        let coefficient = altered.rows[0].coefficients.values_mut().next().unwrap();
        *coefficient = coefficient.clone() + SafeRational::one();
        assert!(verify_lp_relaxation(&original, &altered).is_err());
        altered = relaxed.clone();
        altered.rows[0].priority += 1;
        assert!(verify_lp_relaxation(&original, &altered).is_err());
        altered = relaxed.clone();
        let coefficient = altered.objective.values_mut().next().unwrap();
        *coefficient = coefficient.clone() + SafeRational::one();
        assert!(verify_lp_relaxation(&original, &altered).is_err());
        Python::attach(|_| {
            drop(assignment);
            drop(state);
            drop(globals);
        });
    }

    #[test]
    fn preparation_requires_fresh_state_even_without_callbacks_or_columns() {
        let (packing, mixed, _) = extension_packing();
        for stage in [
            PackingModelStage::Milp,
            PackingModelStage::Lp,
            PackingModelStage::FinalMilp,
        ] {
            let state = Rc::new(ExtensionState::default());
            let first = prepare_assignment(packing.clone(), vec![], stage, None, &state).unwrap();
            assert!(first.columns.is_empty());
            assert!(
                prepare_assignment(packing.clone(), vec![mixed.clone()], stage, None, &state)
                    .is_err()
            );
        }
    }

    #[test]
    fn failed_preparation_cannot_replace_or_modify_an_existing_model() {
        let (packing, mixed, single) = extension_packing();
        let globals = extension_globals();
        for stage in [
            PackingModelStage::Milp,
            PackingModelStage::Lp,
            PackingModelStage::FinalMilp,
        ] {
            let old_state = Rc::new(ExtensionState::default());
            let old = prepare_assignment(
                packing.clone(),
                vec![mixed.clone()],
                stage,
                Some(extension_callbacks(&globals)),
                &old_state,
            )
            .unwrap();
            let old_snapshot = old.assignment.model().linear_model_snapshot().unwrap();
            let old_columns = old.columns.clone();
            let failed_state = Rc::new(ExtensionState::default());
            let failure = prepare_assignment(
                packing.clone(),
                vec![mixed.clone(), single.clone()],
                stage,
                Some(extension_callbacks(&globals)),
                &failed_state,
            );
            let Err(failure) = failure else {
                panic!("nonrepresentable lower bound must fail");
            };
            assert!(failure.message.to_ascii_lowercase().contains("precision"));
            assert_eq!(Rc::strong_count(&failed_state), 1);
            assert!(
                prepare_assignment(packing.clone(), vec![], stage, None, &failed_state).is_err()
            );
            assert_eq!(
                old.assignment.model().linear_model_snapshot().unwrap(),
                old_snapshot
            );
            assert_eq!(old.columns, old_columns);
            for column in &old.columns {
                let variable = old_snapshot
                    .variables
                    .iter()
                    .find(|v| (v.variable.group_id, v.variable.index_in_group) == column.1)
                    .unwrap();
                assert_eq!(old_state.lookup(variable.variable), Some(column.0.clone()));
            }
            let values = vec![SafeRational::one(); old_snapshot.variables.len()];
            let result = old
                .assignment
                .extract_solution(&values, &SafeRational::zero());
            if stage == PackingModelStage::Lp {
                assert!(format!("{:?}", result.unwrap_err()).contains("integer master"));
            } else {
                assert_eq!(result.unwrap().indicators["ok"], "2");
            }
            Python::attach(|_| {
                drop(old);
                drop(old_state);
                drop(failed_state);
            });
        }
        Python::attach(|_| drop(globals));
    }

    #[test]
    fn solution_gate_checks_mapping_values_and_native_feasibility() {
        let length = Meter::runtime_unit();
        let mass = Kilogram::runtime_unit();
        let item = |id: &str, amount| Item {
            id: id.into(),
            length: Quantity::new(SafeRational::one(), length.clone()),
            weight: Quantity::new(SafeRational::zero(), mass.clone()),
            amount,
            materials: BTreeMap::new(),
        };
        let problem = PackingProblem {
            items: vec![item("a", 2), item("b", 1)],
            bin_types: vec![BinType {
                id: "bin".into(),
                length: Quantity::new(SafeRational::one(), length.clone()),
                max_weight: Quantity::new(SafeRational::zero(), mass.clone()),
                cost: SafeRational::one(),
                inventory: None,
            }],
            spacing: Quantity::new(SafeRational::zero(), length.clone()),
            length_unit: length,
            weight_unit: mass,
            objective: PackingObjective::BinCount,
        };
        let packing = PackingContext::new(
            problem,
            &SameUnitPackingValueAdapter,
            &SameUnitPackingValueAdapter,
        )
        .unwrap();
        let patterns = packing
            .generate_patterns(
                PatternGenerationConfig {
                    max_patterns: 10,
                    max_nodes: 100,
                },
                &AcceptAllPatterns,
            )
            .unwrap()
            .patterns;
        let assignment = Assignment::new(
            packing.clone(),
            patterns,
            PackingModelStage::Milp,
            NoPatternExtension,
        )
        .unwrap();
        let mechanism = assignment.model().try_to_mechanism_model().unwrap();
        let mut compiled =
            convert_mechanism_model_to_f64(&mechanism, SolveValueConversionPolicy::Strict)
                .unwrap()
                .try_into_linear_triad_model_with_status_callback(None)
                .unwrap();
        compiled.basic.variables.reverse();
        let by_id = assignment
            .aggregation()
            .variables
            .iter()
            .map(|(pattern, id)| {
                (
                    *id,
                    if pattern.amounts.contains_key("a") {
                        2.0
                    } else {
                        1.0
                    },
                )
            })
            .collect::<BTreeMap<_, _>>();
        let values = compiled
            .basic
            .variables
            .iter()
            .map(|variable| by_id[&variable.id()])
            .collect();
        let report = SolveReport::builder(ProblemStatus::Feasible, TerminationReason::Completed)
            .solution(SolveSolution::vector(values))
            .model_mapping(Some(linear_model_mapping(&compiled).unwrap()))
            .fingerprints(SolveFingerprints {
                model: Some(linear_model_fingerprint(&compiled).unwrap()),
                ..Default::default()
            })
            .build()
            .unwrap();
        let verified = verify_solution(&assignment, &packing, &compiled, &report, 3).unwrap();
        assert!(serialize_report(&report).is_ok());
        assert_eq!(verified.0.len(), 2);
        assert_eq!(verified.1.0.len(), 3);
        assert!(verify_solution(&assignment, &packing, &compiled, &report, 2).is_err());

        let mut changed = report.clone();
        changed.model_mapping = None;
        assert!(verify_solution(&assignment, &packing, &compiled, &changed, 3).is_err());
        changed = report.clone();
        changed.fingerprints.model = None;
        assert!(verify_solution(&assignment, &packing, &compiled, &changed, 3).is_err());
        let mut other = compiled.clone();
        other.c[0] += 1.0;
        changed = report.clone();
        changed.fingerprints.model = Some(linear_model_fingerprint(&other).unwrap());
        assert!(verify_solution(&assignment, &packing, &compiled, &changed, 3).is_err());
        changed = report.clone();
        changed
            .model_mapping
            .as_mut()
            .unwrap()
            .variables_by_column
            .reverse();
        assert!(verify_solution(&assignment, &packing, &compiled, &changed, 3).is_err());
        changed = report.clone();
        changed.solution.as_mut().unwrap().objective_value = Some(123.0);
        assert!(verify_solution(&assignment, &packing, &compiled, &changed, 3).is_ok());
        for value in [0.0, 1.00000001, f64::NAN, f64::INFINITY, -1.0] {
            changed = report.clone();
            changed.solution.as_mut().unwrap().values[0] = value;
            assert!(verify_solution(&assignment, &packing, &compiled, &changed, 3).is_err());
            if !value.is_finite() {
                assert!(serialize_report(&changed).is_err());
            }
        }
        changed = report.clone();
        changed.solution.as_mut().unwrap().values.pop();
        assert!(verify_solution(&assignment, &packing, &compiled, &changed, 3).is_err());
    }
}
