//! Rust 唯一持有可变模型；Python 只持身份句柄。 / Rust owns model state; Python holds identity handles.

use num_rational::BigRational;
use ospf_rust_core::model::{
    ConstraintRelation, LinearObjectiveInput, MetaModel, ObjectiveCategory,
};
use ospf_rust_core::variable::{
    Binary, Continuous, Integer, VariableId, VariableItem, VariableRange, VariableType,
};
use ospf_rust_math::operator::AddRef;
use pyo3::prelude::*;
use std::collections::{BTreeMap, HashMap, HashSet};
use std::sync::Arc;

use crate::control::SolveHandle;
use crate::dual::DualCertificate;
use crate::failure::{Failure, Transport, transport, transport_unit};
use crate::owner::Owner;
use crate::solve::SolveRequest;

type VariableInput = (String, String, Option<f64>, Option<f64>);
type Terms = Vec<(VariableHandle, f64)>;
type ConstraintInput = (String, Terms, String, f64);
type Snapshot = (u64, String, usize, usize);
type LinearExportVariable = (String, String, Option<f64>, Option<f64>);
type LinearExportRow = (String, String, BTreeMap<String, f64>, f64, String);
type LinearExport = (
    String,
    Vec<LinearExportVariable>,
    Vec<LinearExportRow>,
    BTreeMap<String, f64>,
    String,
    f64,
);

enum Coefficient {
    Single(f64),
    Sum(BigRational),
}

#[pyclass(frozen, from_py_object, module = "ospf_python._native")]
#[derive(Clone, Debug)]
pub struct VariableHandle {
    #[pyo3(get)]
    pub model_identity: u64,
    #[pyo3(get)]
    pub index: usize,
    #[pyo3(get)]
    pub variable_identity: (usize, usize),
    provenance: Arc<u8>,
}

#[pyclass(frozen, from_py_object, module = "ospf_python._native")]
#[derive(Clone, Debug)]
pub struct ConstraintHandle {
    #[pyo3(get)]
    pub model_identity: u64,
    #[pyo3(get)]
    pub source_identity: String,
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub relation: &'static str,
    provenance: Arc<u8>,
}

#[pyclass(frozen, module = "ospf_python._native", name = "MetaModel")]
pub struct Model {
    owner: Arc<Owner>,
}

impl Model {
    pub fn create(name: String) -> Result<Self, Failure> {
        Owner::new(name).map(|owner| Self {
            owner: Arc::new(owner),
        })
    }

    pub(crate) fn variable_index(
        model: &MetaModel<f64>,
        handle: &VariableHandle,
        provenance: &Arc<u8>,
    ) -> Result<usize, Failure> {
        if !Arc::ptr_eq(&handle.provenance, provenance)
            || handle.model_identity != model.model_identity()
        {
            return Err(Failure::input(
                "变量属于其他模型 / Variable belongs to another model",
            ));
        }
        if !model.tokens().get(handle.index).is_some_and(|token| {
            let id = token.variable.id();
            token.solver_index == handle.index
                && (id.group_id, id.index_in_group) == handle.variable_identity
        }) {
            return Err(Failure::binding(
                "NOT_FOUND",
                "变量句柄已失效 / Variable handle is stale",
            ));
        }
        Ok(handle.index)
    }

    fn terms(
        model: &MetaModel<f64>,
        terms: Terms,
        provenance: &Arc<u8>,
    ) -> Result<Vec<(usize, f64)>, Failure> {
        let mut indices: HashMap<usize, usize> = HashMap::new();
        let mut combined: Vec<(usize, Coefficient)> = Vec::new();
        for (handle, coefficient) in terms {
            let index = Self::variable_index(model, &handle, provenance)?;
            finite(coefficient)?;
            if let Some(&position) = indices.get(&index) {
                let sum = &mut combined[position].1;
                let value = crate::dual::exact(coefficient)?;
                let total = match &*sum {
                    Coefficient::Single(first) => {
                        BigRational::add_ref(&crate::dual::exact(*first)?, &value)
                    }
                    Coefficient::Sum(previous) => BigRational::add_ref(previous, &value),
                };
                *sum = Coefficient::Sum(total);
            } else {
                indices.insert(index, combined.len());
                combined.push((index, Coefficient::Single(coefficient)));
            }
        }
        combined
            .into_iter()
            .map(|(index, coefficient)| {
                let value = match coefficient {
                    Coefficient::Single(value) => value,
                    Coefficient::Sum(value) => {
                        crate::numeric::Rational { value }.float_value(true)?
                    }
                };
                Ok((index, value))
            })
            .collect()
    }
}

fn source_constraints(
    model: &MetaModel<f64>,
    provenance: &Arc<u8>,
) -> Result<Vec<ConstraintHandle>, Failure> {
    let snapshot = model.linear_model_snapshot().map_err(Failure::from)?;
    if snapshot.rows.len() != model.num_constraints() {
        return Err(Failure::binding(
            "NOT_SUPPORTED",
            "仅支持直接线性约束 / Only direct linear constraints are supported",
        ));
    }
    Ok(snapshot
        .rows
        .into_iter()
        .map(|row| ConstraintHandle {
            model_identity: model.model_identity(),
            provenance: Arc::clone(provenance),
            source_identity: row.id,
            name: row.source_name,
            relation: match row.relation {
                ConstraintRelation::LessEqual => "<=",
                ConstraintRelation::GreaterEqual => ">=",
                ConstraintRelation::Equal => "==",
            },
        })
        .collect())
}

fn resolve_constraint(
    model: &MetaModel<f64>,
    handle: &ConstraintHandle,
    provenance: &Arc<u8>,
) -> Result<usize, Failure> {
    if !Arc::ptr_eq(&handle.provenance, provenance)
        || handle.model_identity != model.model_identity()
    {
        return Err(Failure::input(
            "约束属于其他模型 / Constraint belongs to another model",
        ));
    }
    source_constraints(model, provenance)?
        .iter()
        .position(|current| current.source_identity == handle.source_identity)
        .ok_or_else(|| Failure::binding("NOT_FOUND", "约束句柄已失效 / Constraint handle is stale"))
}

fn finite(value: f64) -> Result<(), Failure> {
    if value.is_finite() {
        Ok(())
    } else {
        Err(Failure::input(
            "数值必须有限 / Numeric value must be finite",
        ))
    }
}

fn checked_range(
    kind: &str,
    mut lower: Option<f64>,
    mut upper: Option<f64>,
) -> Result<VariableRange<f64>, Failure> {
    if kind == "binary" {
        lower = Some(lower.unwrap_or(0.0));
        upper = Some(upper.unwrap_or(1.0));
    }
    for bound in [lower, upper].into_iter().flatten() {
        finite(bound)?;
        if (kind == "integer" || kind == "binary")
            && (bound.fract() != 0.0 || bound.abs() > 9_007_199_254_740_991.0)
        {
            return Err(Failure::input(
                "整数边界必须可精确表示 / Integer bound must be exactly representable",
            ));
        }
        if kind == "binary" && !(0.0..=1.0).contains(&bound) {
            return Err(Failure::input(
                "二元变量边界必须在 0..1 / Binary bounds must be within 0..1",
            ));
        }
    }
    if lower.zip(upper).is_some_and(|(lo, hi)| lo > hi) {
        return Err(Failure::input(
            "变量下界大于上界 / Lower bound exceeds upper bound",
        ));
    }
    Ok(VariableRange::new(lower, upper))
}

#[cfg(test)]
fn register(
    model: &mut MetaModel<f64>,
    input: VariableInput,
    provenance: &Arc<u8>,
) -> Result<VariableHandle, Failure> {
    let (name, kind, lower, upper) = input;
    let range = checked_range(&kind, lower, upper)?;
    register_validated(model, &name, &kind, range, provenance)
}

#[cfg(test)]
fn register_validated(
    model: &mut MetaModel<f64>,
    name: &str,
    kind: &str,
    range: VariableRange<f64>,
    provenance: &Arc<u8>,
) -> Result<VariableHandle, Failure> {
    let index = match kind {
        "continuous" => model.register_auto_variable_with_range::<Continuous>(name, range),
        "integer" => model.register_auto_variable_with_range::<Integer>(name, range),
        "binary" => model.register_auto_variable_with_range::<Binary>(name, range),
        _ => return Err(Failure::input("未知变量类型 / Unknown variable kind")),
    }
    .map_err(Failure::from)?;
    variable_handle(model, index, provenance)
}

fn variable_handle(
    model: &MetaModel<f64>,
    index: usize,
    provenance: &Arc<u8>,
) -> Result<VariableHandle, Failure> {
    let id = model.tokens()[index].variable.id();
    Ok(VariableHandle {
        model_identity: model.model_identity(),
        index,
        variable_identity: (id.group_id, id.index_in_group),
        provenance: Arc::clone(provenance),
    })
}

fn register_homogeneous(
    model: &mut MetaModel<f64>,
    inputs: Vec<(String, VariableRange<f64>)>,
    kind: &str,
    provenance: &Arc<u8>,
) -> Result<Vec<VariableHandle>, Failure> {
    let indices = match kind {
        "continuous" => model
            .register_variables(
                inputs
                    .into_iter()
                    .map(|(name, range)| VariableItem::<Continuous>::auto_with_range(&name, range)),
            )
            .map_err(Failure::from)?,
        "integer" => model
            .register_variables(
                inputs
                    .into_iter()
                    .map(|(name, range)| VariableItem::<Integer>::auto_with_range(&name, range)),
            )
            .map_err(Failure::from)?,
        "binary" => model
            .register_variables(
                inputs
                    .into_iter()
                    .map(|(name, range)| VariableItem::<Binary>::auto_with_range(&name, range)),
            )
            .map_err(Failure::from)?,
        _ => return Err(Failure::input("未知变量类型 / Unknown variable kind")),
    };
    indices
        .into_iter()
        .map(|index| variable_handle(model, index, provenance))
        .collect()
}

fn register_batch(
    model: &mut MetaModel<f64>,
    inputs: Vec<(String, String, VariableRange<f64>)>,
    provenance: &Arc<u8>,
) -> Result<Vec<VariableHandle>, Failure> {
    let mut handles = Vec::with_capacity(inputs.len());
    let mut run: Vec<(String, VariableRange<f64>)> = Vec::new();
    let mut run_kind = String::new();
    for (name, kind, range) in inputs {
        if run_kind != kind {
            if !run.is_empty() {
                handles.extend(register_homogeneous(
                    model,
                    std::mem::take(&mut run),
                    &run_kind,
                    provenance,
                )?);
            }
            run_kind = kind;
        }
        run.push((name, range));
    }
    if !run.is_empty() {
        handles.extend(register_homogeneous(model, run, &run_kind, provenance)?);
    }
    Ok(handles)
}

fn export_kind(var_type: VariableType) -> Result<&'static str, Failure> {
    match var_type {
        VariableType::Continuous => Ok("continuous"),
        VariableType::Integer => Ok("integer"),
        VariableType::Binary => Ok("binary"),
        _ => Err(Failure::binding(
            "NOT_SUPPORTED",
            "线性三元组导出仅支持 continuous、integer、binary / ".to_owned()
                + "The linear-triad export supports continuous, integer and binary only",
        )),
    }
}

fn linear_export(model: &MetaModel<f64>) -> Result<LinearExport, Failure> {
    let snapshot = model.linear_model_snapshot().map_err(Failure::from)?;
    let names: BTreeMap<VariableId, String> = snapshot
        .variables
        .iter()
        .map(|state| (state.variable, state.name.clone()))
        .collect();
    let variables = snapshot
        .variables
        .iter()
        .map(|state| {
            Ok((
                state.name.clone(),
                export_kind(state.var_type)?.to_owned(),
                state.lower_bound,
                state.upper_bound,
            ))
        })
        .collect::<Result<Vec<_>, Failure>>()?;

    let mut row_names = HashSet::new();
    let rows = snapshot
        .rows
        .into_iter()
        .map(|row| {
            if row.source_name.is_empty() || !row_names.insert(row.source_name.clone()) {
                return Err(Failure::binding(
                    "ALREADY_EXIST",
                    format!(
                        "约束名称必须非空且唯一 / Constraint name must be non-empty and unique: {}",
                        row.source_name
                    ),
                ));
            }
            let coefficients = row
                .coefficients
                .into_iter()
                .map(|(variable, coefficient)| {
                    names
                        .get(&variable)
                        .cloned()
                        .map(|name| (name, coefficient))
                        .ok_or_else(|| {
                            Failure::binding(
                                "DATA_LOSS",
                                "约束引用未知变量 / Constraint references an unknown variable",
                            )
                        })
                })
                .collect::<Result<BTreeMap<_, _>, _>>()?;
            let relation = match row.relation {
                ConstraintRelation::LessEqual => "<=",
                ConstraintRelation::GreaterEqual => ">=",
                ConstraintRelation::Equal => "==",
            };
            Ok((
                row.id,
                row.source_name,
                coefficients,
                row.rhs,
                relation.to_owned(),
            ))
        })
        .collect::<Result<Vec<_>, Failure>>()?;

    let objective = snapshot
        .objective
        .into_iter()
        .map(|(variable, coefficient)| {
            names
                .get(&variable)
                .cloned()
                .map(|name| (name, coefficient))
                .ok_or_else(|| {
                    Failure::binding(
                        "DATA_LOSS",
                        "目标引用未知变量 / Objective references an unknown variable",
                    )
                })
        })
        .collect::<Result<BTreeMap<_, _>, _>>()?;
    let sense = match snapshot.objective_category {
        ObjectiveCategory::Minimum => "minimize",
        ObjectiveCategory::Maximum => "maximize",
    };

    Ok((
        model.name.clone(),
        variables,
        rows,
        objective,
        sense.to_owned(),
        snapshot.objective_constant,
    ))
}

#[pymethods]
impl Model {
    #[getter]
    fn model_identity(&self) -> u64 {
        self.owner.identity
    }

    fn snapshot(&self, py: Python<'_>) -> Transport<Snapshot> {
        transport(py.detach(|| {
            self.owner.with_model(|model| {
                Ok((
                    model.model_identity(),
                    model.name.clone(),
                    model.num_tokens(),
                    model.num_constraints(),
                ))
            })
        }))
    }

    fn generation(&self, py: Python<'_>) -> Transport<u64> {
        transport(py.detach(|| {
            self.owner
                .with_model_and_generation(|_, generation| Ok(generation))
        }))
    }

    fn to_linear_triad(&self, py: Python<'_>) -> Transport<LinearExport> {
        transport(py.detach(|| self.owner.with_model(linear_export)))
    }

    fn constraint_handles(&self, py: Python<'_>) -> Transport<Vec<ConstraintHandle>> {
        let provenance = Arc::clone(&self.owner.provenance);
        transport(py.detach(|| {
            self.owner
                .with_model(move |model| source_constraints(model, &provenance))
        }))
    }

    #[pyo3(signature = (*, handle))]
    fn constraint_index(&self, py: Python<'_>, handle: ConstraintHandle) -> Transport<usize> {
        let provenance = Arc::clone(&self.owner.provenance);
        transport(py.detach(|| {
            self.owner
                .with_model(move |model| resolve_constraint(model, &handle, &provenance))
        }))
    }

    fn close(&self, py: Python<'_>) -> Transport<()> {
        transport_unit(py.detach(|| self.owner.close()))
    }

    #[pyo3(signature = (*, decisions, blocks))]
    fn create_projection(
        &self,
        py: Python<'_>,
        decisions: Vec<(String, String, VariableHandle)>,
        blocks: Vec<String>,
    ) -> Transport<crate::projection::Projection> {
        transport(py.detach(|| {
            crate::projection::Projection::create(Arc::clone(&self.owner), decisions, blocks)
        }))
    }

    fn add_variables(
        &self,
        py: Python<'_>,
        inputs: Vec<VariableInput>,
    ) -> Transport<Vec<VariableHandle>> {
        let provenance = Arc::clone(&self.owner.provenance);
        transport(py.detach(|| {
            self.owner.mutate(move |model| {
                let mut names: HashSet<String> = model
                    .tokens()
                    .iter()
                    .map(|token| token.variable.name().to_owned())
                    .collect();
                let mut validated = Vec::with_capacity(inputs.len());
                for (name, kind, lower, upper) in inputs {
                    if !names.insert(name.clone()) {
                        return Err(Failure::binding(
                            "ALREADY_EXIST",
                            format!("变量名称重复 / Duplicate variable name: {name}"),
                        ));
                    }
                    let range = checked_range(&kind, lower, upper)?;
                    validated.push((name, kind, range));
                }
                register_batch(model, validated, &provenance)
            })
        }))
    }

    fn add_constraints(&self, py: Python<'_>, inputs: Vec<ConstraintInput>) -> Transport<()> {
        let provenance = Arc::clone(&self.owner.provenance);
        transport_unit(py.detach(|| {
            self.owner.mutate(move |model| {
                for (name, terms, relation, rhs) in inputs {
                    finite(rhs)?;
                    let terms = Self::terms(model, terms, &provenance)?;
                    let relation = match relation.as_str() {
                        "<=" => ConstraintRelation::LessEqual,
                        ">=" => ConstraintRelation::GreaterEqual,
                        "==" => ConstraintRelation::Equal,
                        _ => {
                            return Err(Failure::input(
                                "未知约束关系 / Unknown constraint relation",
                            ));
                        }
                    };
                    model
                        .add_linear_constraint(&terms, relation, rhs, &name)
                        .map_err(Failure::from)?;
                }
                Ok(())
            })
        }))
    }

    #[pyo3(signature = (*, handle, lower, upper))]
    fn set_bounds(
        &self,
        py: Python<'_>,
        handle: VariableHandle,
        lower: Option<f64>,
        upper: Option<f64>,
    ) -> Transport<()> {
        let provenance = Arc::clone(&self.owner.provenance);
        transport_unit(py.detach(|| {
            self.owner.mutate_prevalidated(
                move |model| {
                    let index = Self::variable_index(model, &handle, &provenance)?;
                    let kind = match model.tokens()[index].var_type() {
                        VariableType::Continuous => "continuous",
                        VariableType::Integer => "integer",
                        VariableType::Binary => "binary",
                        _ => {
                            return Err(Failure::binding(
                                "NOT_SUPPORTED",
                                "不支持此变量类型 / Unsupported variable kind",
                            ));
                        }
                    };
                    Ok((index, checked_range(kind, lower, upper)?))
                },
                |model, (index, range)| {
                    model
                        .set_variable_range_by_index(index, range)
                        .map_err(Failure::from)
                },
            )
        }))
    }

    #[pyo3(signature = (*, terms, sense, name="objective".to_string(), constant=0.0))]
    fn set_objective(
        &self,
        py: Python<'_>,
        terms: Terms,
        sense: String,
        name: String,
        constant: f64,
    ) -> Transport<()> {
        let provenance = Arc::clone(&self.owner.provenance);
        transport_unit(py.detach(|| {
            self.owner.mutate_prevalidated(
                move |model| {
                    finite(constant)?;
                    if constant != 0.0 {
                        return Err(Failure::binding(
                            "NOT_SUPPORTED",
                            "固定 Rust revision 未保留线性目标常数 / Pinned Rust revision does not preserve linear objective constants",
                        ));
                    }
                    let terms = Self::terms(model, terms, &provenance)?;
                    let objective = match sense.as_str() {
                        "minimize" => LinearObjectiveInput::minimize(name),
                        "maximize" => LinearObjectiveInput::maximize(name),
                        _ => return Err(Failure::input("未知目标方向 / Unknown objective sense")),
                    };
                    Ok(objective.terms(terms).constant(constant))
                },
                |model, objective| {
                    model.set_linear_objective_input(objective);
                    Ok(())
                },
            )
        }))
    }

    #[pyo3(signature = (*, solver, time_limit=None, cancellation=None, on_progress=None))]
    fn solve(
        &self,
        py: Python<'_>,
        solver: String,
        time_limit: Option<f64>,
        cancellation: Option<SolveHandle>,
        on_progress: Option<Py<PyAny>>,
    ) -> Transport<(u64, String)> {
        if on_progress
            .as_ref()
            .is_some_and(|callback| !callback.bind(py).is_callable())
        {
            return transport(Err(Failure::input(
                "进度回调必须可调用 / Progress callback must be callable",
            )));
        }
        let request = SolveRequest {
            solver,
            time_limit,
            cancellation,
            on_progress,
        };
        transport(py.detach(|| {
            self.owner
                .with_model_and_generation(move |model, generation| {
                    crate::solve::solve(model, request).map(|report| (generation, report))
                })
        }))
    }

    #[pyo3(signature = (*, solver, time_limit=None, cancellation=None, on_progress=None))]
    fn solve_compiled(
        &self,
        py: Python<'_>,
        solver: String,
        time_limit: Option<f64>,
        cancellation: Option<SolveHandle>,
        on_progress: Option<Py<PyAny>>,
    ) -> Transport<(u64, String, Option<DualCertificate>, Option<Failure>)> {
        if on_progress
            .as_ref()
            .is_some_and(|callback| !callback.bind(py).is_callable())
        {
            return transport(Err(Failure::input(
                "进度回调必须可调用 / Progress callback must be callable",
            )));
        }
        let request = SolveRequest {
            solver,
            time_limit,
            cancellation,
            on_progress,
        };
        let provenance = Arc::clone(&self.owner.provenance);
        transport(py.detach(|| {
            self.owner
                .with_model_and_generation(move |model, generation| {
                    crate::solve::solve_compiled(model, request, provenance, generation)
                        .map(|(raw, certificate, error)| (generation, raw, certificate, error))
                })
        }))
    }

    #[pyo3(signature = (*, solver, time_limit=None, cancellation=None, on_progress=None))]
    fn solve_relaxed_compiled(
        &self,
        py: Python<'_>,
        solver: String,
        time_limit: Option<f64>,
        cancellation: Option<SolveHandle>,
        on_progress: Option<Py<PyAny>>,
    ) -> Transport<(u64, String, Option<DualCertificate>, Option<Failure>)> {
        if on_progress
            .as_ref()
            .is_some_and(|callback| !callback.bind(py).is_callable())
        {
            return transport(Err(Failure::input(
                "进度回调必须可调用 / Progress callback must be callable",
            )));
        }
        let request = SolveRequest {
            solver,
            time_limit,
            cancellation,
            on_progress,
        };
        let provenance = Arc::clone(&self.owner.provenance);
        transport(py.detach(|| {
            self.owner
                .with_model_and_generation(move |model, generation| {
                    crate::solve::solve_relaxed_compiled(model, request, provenance, generation)
                        .map(|(raw, certificate, error)| (generation, raw, certificate, error))
                })
        }))
    }

    #[pyo3(signature = (*, certificate, handle))]
    fn source_price(
        &self,
        py: Python<'_>,
        certificate: DualCertificate,
        handle: ConstraintHandle,
    ) -> Transport<f64> {
        let provenance = Arc::clone(&self.owner.provenance);
        transport(py.detach(|| {
            self.owner
                .with_model_and_generation(move |model, generation| {
                    if !Arc::ptr_eq(&handle.provenance, &provenance)
                        || handle.model_identity != model.model_identity()
                    {
                        return Err(Failure::input(
                            "约束属于其他模型 / Constraint belongs to another model",
                        ));
                    }
                    // 相同所有者和代次使证书中的源行表成为当前快照。 / Matching owner and generation make the certificate's source rows current.
                    certificate.price(&provenance, generation, &handle.source_identity)
                })
        }))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn duplicate_terms_use_exact_sum_and_keep_first_variable_order() {
        let mut model = MetaModel::<f64>::new("exact terms");
        let provenance = Arc::new(0);
        let x = register(
            &mut model,
            ("x".into(), "continuous".into(), None, None),
            &provenance,
        )
        .unwrap();
        let y = register(
            &mut model,
            ("y".into(), "continuous".into(), None, None),
            &provenance,
        )
        .unwrap();
        let terms = vec![
            (x.clone(), 1e16),
            (y.clone(), 1.25),
            (x.clone(), 1.0),
            (y, -0.25),
            (x.clone(), -1e16),
        ];
        assert_eq!(
            Model::terms(&model, terms, &provenance).unwrap(),
            vec![(0, 1.0), (1, 1.0)]
        );
        let single_zero = Model::terms(&model, vec![(x.clone(), -0.0)], &provenance).unwrap();
        assert!(single_zero[0].1.is_sign_negative());
        let error = Model::terms(
            &model,
            vec![(x.clone(), 1.0), (x, 2_f64.powi(-53))],
            &provenance,
        )
        .unwrap_err();
        assert_eq!(error.category, "DATA_LOSS");
    }

    #[test]
    fn batch_preserves_declaration_order_and_mixed_types() {
        let mut model = MetaModel::<f64>::new("homogeneous batch");
        let provenance = Arc::new(0);
        let handles = register_batch(
            &mut model,
            vec![
                (
                    "x".into(),
                    "continuous".into(),
                    VariableRange::bounded(0.0, 2.0),
                ),
                ("y".into(), "binary".into(), VariableRange::new(None, None)),
            ],
            &provenance,
        )
        .unwrap();
        assert_eq!(
            handles
                .iter()
                .map(|handle| handle.index)
                .collect::<Vec<_>>(),
            vec![0, 1]
        );
        assert_eq!(model.num_tokens(), 2);
        assert_eq!(
            model
                .tokens()
                .iter()
                .map(|token| token.variable.name())
                .collect::<Vec<_>>(),
            vec!["x", "y"]
        );
        assert_eq!(model.tokens()[1].var_type(), VariableType::Binary);
    }

    #[test]
    #[ignore = "manual registration timing probe"]
    fn probe_batch_registration_time() {
        use std::time::Instant;

        for count in [50, 500, 5000] {
            let mut model = MetaModel::<f64>::new("probe");
            let variables = (0..count)
                .map(|index| {
                    VariableItem::<Continuous>::auto_with_range(
                        &format!("x_{index}"),
                        VariableRange::bounded(0.0, 1.0),
                    )
                })
                .collect::<Vec<_>>();
            let started = Instant::now();
            let indices = model.register_variables(variables).unwrap();
            println!(
                "count={count} elapsed={:?} indices={}",
                started.elapsed(),
                indices.len()
            );
        }
    }

    #[test]
    fn pinned_snapshot_rounds_duplicate_terms_before_publication() {
        let mut model = MetaModel::<f64>::new("upstream duplicate rounding");
        let provenance = Arc::new(0);
        let x = register(
            &mut model,
            ("x".into(), "continuous".into(), None, None),
            &provenance,
        )
        .unwrap();
        let terms = vec![(x.index, 1e16), (x.index, 1.0), (x.index, -1e16)];
        model
            .add_linear_constraint(&terms, ConstraintRelation::LessEqual, 0.0, "row")
            .unwrap();
        model.set_linear_objective_input(LinearObjectiveInput::maximize("obj").terms(terms));
        let snapshot = model.linear_model_snapshot().unwrap();
        assert!(snapshot.rows[0].coefficients.is_empty());
        assert!(snapshot.objective.is_empty());
        assert_eq!((1e16_f64 + 1.0) - 1e16, 0.0);
    }

    #[test]
    fn invalid_upstream_snapshot_is_rejected_without_mutation() {
        let mut model = MetaModel::<f64>::new("invalid upstream snapshot");
        let provenance = Arc::new(0);
        let handle = register(
            &mut model,
            ("x".into(), "continuous".into(), None, None),
            &provenance,
        )
        .unwrap();
        model
            .add_linear_constraint(
                &[(handle.index, 1e308), (handle.index, 1e308)],
                ConstraintRelation::LessEqual,
                1.0,
                "overflow",
            )
            .unwrap();
        assert!(source_constraints(&model, &provenance).is_err());
        assert_eq!((model.num_tokens(), model.num_constraints()), (1, 1));
    }

    #[test]
    fn linear_export_preserves_source_names_bounds_rows_and_objective() {
        let mut model = MetaModel::<f64>::new("linear export");
        let provenance = Arc::new(0);
        let x = register(
            &mut model,
            ("x".into(), "continuous".into(), Some(-2.0), Some(5.0)),
            &provenance,
        )
        .unwrap();
        let y = register(
            &mut model,
            ("y".into(), "binary".into(), None, None),
            &provenance,
        )
        .unwrap();
        model
            .add_linear_constraint(
                &[(x.index, 1.0), (y.index, -2.0)],
                ConstraintRelation::GreaterEqual,
                3.0,
                "balance",
            )
            .unwrap();
        model.set_linear_objective_input(
            LinearObjectiveInput::minimize("cost").terms(vec![(x.index, 2.0), (y.index, 3.0)]),
        );

        let (name, variables, rows, objective, sense, constant) = linear_export(&model).unwrap();

        assert_eq!(name, "linear export");
        assert_eq!(
            variables,
            vec![
                ("x".into(), "continuous".into(), Some(-2.0), Some(5.0)),
                ("y".into(), "binary".into(), Some(0.0), Some(1.0)),
            ]
        );
        assert_eq!(rows.len(), 1);
        assert_eq!(rows[0].1, "balance");
        assert_eq!(
            rows[0].2,
            BTreeMap::from([("x".into(), 1.0), ("y".into(), -2.0)])
        );
        assert_eq!(rows[0].3, 3.0);
        assert_eq!(rows[0].4, ">=");
        assert_eq!(
            objective,
            BTreeMap::from([("x".into(), 2.0), ("y".into(), 3.0)])
        );
        assert_eq!(sense, "minimize");
        assert_eq!(constant, 0.0);
    }

    #[test]
    fn upstream_rejects_duplicate_constraint_names_before_export() {
        let mut model = MetaModel::<f64>::new("duplicate export rows");
        let provenance = Arc::new(0);
        let x = register(
            &mut model,
            ("x".into(), "continuous".into(), None, None),
            &provenance,
        )
        .unwrap();
        model
            .add_linear_constraint(
                &[(x.index, 1.0)],
                ConstraintRelation::LessEqual,
                1.0,
                "same",
            )
            .unwrap();
        let error = model
            .add_linear_constraint(
                &[(x.index, -1.0)],
                ConstraintRelation::LessEqual,
                1.0,
                "same",
            )
            .unwrap_err();
        let error = Failure::from(error);

        assert_eq!(error.category, "MODEL_BUILD_FAILED");
    }

    #[test]
    fn variable_handle_checks_owner_even_when_all_numeric_fields_match() {
        let mut model = MetaModel::<f64>::new("variable identity wrap");
        let provenance = Arc::new(0);
        let handle = register(
            &mut model,
            ("x".into(), "continuous".into(), None, None),
            &provenance,
        )
        .unwrap();
        assert_eq!(
            Model::variable_index(&model, &handle, &provenance).unwrap(),
            0
        );

        let other = Arc::new(0);
        let foreign = VariableHandle {
            provenance: Arc::clone(&other),
            ..handle.clone()
        };
        assert_eq!(foreign.model_identity, handle.model_identity);
        assert_eq!(foreign.index, handle.index);
        assert_eq!(foreign.variable_identity, handle.variable_identity);
        assert_eq!(
            Model::variable_index(&model, &foreign, &provenance)
                .unwrap_err()
                .category,
            "ILLEGAL_ARGUMENT"
        );
        assert_eq!(
            Model::terms(&model, vec![(foreign, 1.0)], &provenance)
                .unwrap_err()
                .category,
            "ILLEGAL_ARGUMENT"
        );
        drop(provenance);
        assert_eq!(
            Model::variable_index(&model, &handle, &other)
                .unwrap_err()
                .category,
            "ILLEGAL_ARGUMENT"
        );
        let stale = VariableHandle { index: 1, ..handle };
        assert_eq!(
            Model::variable_index(&model, &stale, &stale.provenance)
                .unwrap_err()
                .category,
            "NOT_FOUND"
        );
    }

    #[test]
    fn source_identity_survives_reordering_but_not_removal_and_readdition() {
        let mut model = MetaModel::<f64>::new("constraint identity");
        let provenance = Arc::new(0);
        model
            .add_linear_constraint(&[], ConstraintRelation::Equal, 0.0, "a")
            .unwrap();
        model
            .add_linear_constraint(&[], ConstraintRelation::LessEqual, 0.0, "b")
            .unwrap();
        let handles = source_constraints(&model, &provenance).unwrap();
        model.retain_constraints(|constraint| constraint.name != "a");
        assert_eq!(
            resolve_constraint(&model, &handles[1], &provenance).unwrap(),
            0
        );
        assert_eq!(
            resolve_constraint(&model, &handles[0], &provenance)
                .unwrap_err()
                .category,
            "NOT_FOUND"
        );
        model
            .add_linear_constraint(&[], ConstraintRelation::Equal, 0.0, "a")
            .unwrap();
        let added = source_constraints(&model, &provenance).unwrap();
        assert_ne!(added[1].source_identity, handles[0].source_identity);
        assert_eq!(
            resolve_constraint(&model, &handles[0], &provenance)
                .unwrap_err()
                .category,
            "NOT_FOUND"
        );
        assert_eq!(
            resolve_constraint(&model, &added[1], &provenance).unwrap(),
            1
        );
    }

    #[test]
    fn source_handle_rejects_matching_integer_identity_from_another_owner() {
        let mut model = MetaModel::<f64>::new("identity wrap");
        model
            .add_linear_constraint(&[], ConstraintRelation::LessEqual, 1.0, "row")
            .unwrap();
        let original = Arc::new(0);
        let foreign = Arc::new(0);
        let handle = source_constraints(&model, &foreign).unwrap().remove(0);
        assert_eq!(handle.model_identity, model.model_identity());
        assert_eq!(
            resolve_constraint(&model, &handle, &original)
                .unwrap_err()
                .category,
            "ILLEGAL_ARGUMENT"
        );
    }

    #[cfg(feature = "scip")]
    #[test]
    fn certificate_lookup_rejects_removed_rows_after_index_compaction() {
        let model = Model::create("certificate after compaction".into()).unwrap();
        let x = model
            .owner
            .mutate(|model| {
                let x = model
                    .register_auto_variable_with_range::<Continuous>(
                        "x",
                        VariableRange::with_lower(0.0),
                    )
                    .map_err(Failure::from)?;
                model
                    .add_linear_constraint(
                        &[(x, 1.0)],
                        ConstraintRelation::LessEqual,
                        2.0,
                        "removed",
                    )
                    .map_err(Failure::from)?;
                model
                    .add_linear_constraint(&[(x, 1.0)], ConstraintRelation::LessEqual, 4.0, "kept")
                    .map_err(Failure::from)?;
                model.set_linear_objective_input(
                    LinearObjectiveInput::maximize("objective").terms(vec![(x, 3.0)]),
                );
                Ok(x)
            })
            .unwrap();
        let provenance = Arc::clone(&model.owner.provenance);
        let old = model
            .owner
            .with_model(move |model| source_constraints(model, &provenance))
            .unwrap();
        model
            .owner
            .mutate(move |model| {
                model.retain_constraints(|constraint| constraint.name != "removed");
                model
                    .add_linear_constraint(
                        &[(x, 1.0)],
                        ConstraintRelation::LessEqual,
                        2.0,
                        "removed",
                    )
                    .map_err(Failure::from)
            })
            .unwrap();
        let provenance = Arc::clone(&model.owner.provenance);
        let current = model
            .owner
            .with_model(move |model| source_constraints(model, &provenance))
            .unwrap();
        assert_eq!(old[1].source_identity, current[0].source_identity);
        assert_ne!(old[0].source_identity, current[1].source_identity);
        let provenance = Arc::clone(&model.owner.provenance);
        let certificate = model
            .owner
            .with_model_and_generation(move |model, generation| {
                crate::solve::solve_compiled(
                    model,
                    SolveRequest {
                        solver: "scip".into(),
                        time_limit: None,
                        cancellation: None,
                        on_progress: None,
                    },
                    provenance,
                    generation,
                )
                .map(|(_, certificate, _)| certificate.unwrap())
            })
            .unwrap();
        Python::initialize();
        Python::attach(|py| {
            let (value, error) = model.source_price(py, certificate.clone(), old[0].clone());
            assert!(value.is_none());
            assert_eq!(error.unwrap().category, "NOT_FOUND");
            let (value, error) = model.source_price(py, certificate.clone(), old[1].clone());
            assert_eq!(value, Some(0.0));
            assert!(error.is_none());
            let (value, error) = model.source_price(py, certificate.clone(), current[1].clone());
            assert_eq!(value, Some(3.0));
            assert!(error.is_none());
            model.owner.close().unwrap();
            let (_, error) = model.source_price(py, certificate, current[1].clone());
            assert_eq!(error.unwrap().category, "NOT_INITIALIZED");
        });
    }

    #[test]
    fn snapshot_compilation_maps_source_rows_and_normalizes_the_objective() {
        use ospf_rust_core::model::ObjectiveCategory;
        use ospf_rust_core::solver::linear_model_fingerprint;

        let mut model = MetaModel::<f64>::new("row mapping");
        let x = model.register_auto_variable::<Continuous>("x").unwrap();
        for (name, relation) in [
            ("a", ConstraintRelation::Equal),
            ("a_eq_le", ConstraintRelation::LessEqual),
            ("lower", ConstraintRelation::GreaterEqual),
        ] {
            model
                .add_linear_constraint(&[(x, 1.0)], relation, 1.0, name)
                .unwrap();
        }
        model.set_linear_objective_input(
            LinearObjectiveInput::maximize("objective").terms(vec![(x, 3.0)]),
        );
        let source = source_constraints(&model, &Arc::new(0)).unwrap();
        let snapshot = model.linear_model_snapshot().unwrap();
        let compiled = snapshot.compile_flt64().unwrap();
        assert_eq!(compiled.rows.len(), 4);
        assert_eq!(
            compiled
                .rows
                .iter()
                .map(|row| (row.source.as_str(), row.multiplier))
                .collect::<Vec<_>>(),
            vec![
                (source[0].source_identity.as_str(), 1),
                (source[0].source_identity.as_str(), -1),
                (source[1].source_identity.as_str(), 1),
                (source[2].source_identity.as_str(), -1),
            ]
        );
        assert_eq!(
            compiled.model.objective_category,
            ObjectiveCategory::Minimum
        );
        assert_eq!(compiled.model.c, vec![-3.0]);
        assert_ne!(
            linear_model_fingerprint(&compiled.model).unwrap(),
            linear_model_fingerprint(&model.try_to_linear_triad_model().unwrap()).unwrap()
        );
    }

    #[test]
    fn symbolic_rows_are_not_misidentified_as_direct_constraints() {
        use ospf_rust_core::model::SymbolicLinearInequality;
        use ospf_rust_math::symbol::Linear;

        let mut model = MetaModel::<f64>::new("symbolic row");
        model.add_symbolic_inequality(
            SymbolicLinearInequality::less_equal(Linear::new(vec![], 0.0), 1.0),
            "symbolic",
        );
        assert_eq!(
            source_constraints(&model, &Arc::new(0))
                .unwrap_err()
                .category,
            "NOT_SUPPORTED"
        );
    }
}
