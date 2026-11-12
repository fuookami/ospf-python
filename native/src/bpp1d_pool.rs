//! BPP1D 列池的不可变精确快照与原子发布。 / Immutable exact BPP1D snapshots and atomic publication.

use std::collections::{BTreeMap, BTreeSet};
use std::sync::{Arc, Mutex};

use num_traits::Zero;
use ospf_rust_core::solver::{
    SolveReport, SolveValue, SolveValueConversionPolicy, linear_model_fingerprint,
    linear_model_mapping,
};
use ospf_rust_framework_bpp1d::domain::{PackingContext, PackingPattern};
use ospf_rust_quantities::unit::Unit;
use pyo3::prelude::*;
use pyo3::types::{PyWeakrefMethods, PyWeakrefReference};

use crate::bpp1d::{
    Column, ExtensionCallbacks, FinalSolved, FrozenLp, PatternInput, Ratio, pattern, prepare_lp,
    serialize_report, solve_final,
};
use crate::bpp1d_extension::Reference;
use crate::control::SolveHandle;
use crate::failure::{Failure, Transport, transport, transport_unit};
use crate::safe_rational::SafeRational;
use crate::solve::SolveRequest;

type PoolInfo = (u64, u64, Vec<PatternInput>, Vec<Column>);
pub(crate) type WeakCallbacks = Option<(Py<PyWeakrefReference>, Py<PyWeakrefReference>)>;
type LpSolution = (Vec<(Reference, Ratio)>, Ratio);
type LpSolve = (
    u64,
    u64,
    String,
    Vec<Column>,
    Option<LpSolution>,
    Option<Failure>,
);

struct Version {
    generation: u64,
    patterns: BTreeSet<PackingPattern>,
    model: FrozenLp,
}

impl Version {
    fn info(&self) -> PoolInfo {
        (
            self.generation,
            self.model.snapshot.revision.owner,
            self.patterns
                .iter()
                .map(|pattern| (pattern.bin_type_id.clone(), pattern.amounts.clone()))
                .collect(),
            self.model.columns.clone(),
        )
    }
}

#[pyclass(frozen, module = "ospf_python._native")]
pub struct Bpp1dPool {
    packing: PackingContext<SafeRational, Unit, Unit>,
    callbacks: WeakCallbacks,
    current: Mutex<Option<Arc<Version>>>,
}

fn closed() -> Failure {
    Failure::binding("NOT_INITIALIZED", "列池已关闭 / Column pool is closed")
}

fn unavailable() -> Failure {
    Failure::binding(
        "UNAVAILABLE",
        "列池状态不可用 / Column pool state is unavailable",
    )
}

fn drop_callbacks(callbacks: ExtensionCallbacks) {
    Python::attach(|_| drop(callbacks));
}

fn valid_callbacks(py: Python<'_>, callbacks: &ExtensionCallbacks) -> bool {
    callbacks.as_ref().is_none_or(|(register, extract)| {
        register.bind(py).is_callable() && extract.bind(py).is_callable()
    })
}

pub(crate) fn weak_callbacks(
    py: Python<'_>,
    callbacks: &ExtensionCallbacks,
) -> Result<WeakCallbacks, Failure> {
    callbacks
        .as_ref()
        .map(|(register, extract)| {
            let weak = |callback: &Py<PyAny>| {
                PyWeakrefReference::new(callback.bind(py))
                    .map(Bound::unbind)
                    .map_err(|_| {
                        Failure::input(
                            "列池回调必须支持弱引用 / Column pool callbacks must support weak references",
                        )
                    })
            };
            Ok((weak(register)?, weak(extract)?))
        })
        .transpose()
}

impl Bpp1dPool {
    pub(crate) fn create(
        packing: PackingContext<SafeRational, Unit, Unit>,
        patterns: Vec<PatternInput>,
        callbacks: ExtensionCallbacks,
        weak_callbacks: WeakCallbacks,
    ) -> PyResult<Result<Self, Failure>> {
        let patterns: BTreeSet<_> = patterns.into_iter().map(pattern).collect();
        let model = prepare_lp(
            packing.clone(),
            patterns.iter().cloned().collect(),
            callbacks,
        )?;
        Ok(model.map(|model| Self {
            packing,
            callbacks: weak_callbacks,
            current: Mutex::new(Some(Arc::new(Version {
                generation: 0,
                patterns,
                model,
            }))),
        }))
    }

    fn matches_callbacks(&self, callbacks: &ExtensionCallbacks) -> bool {
        Python::attach(|py| match (&self.callbacks, callbacks) {
            (None, None) => true,
            (Some((register, extract)), Some((candidate_register, candidate_extract))) => {
                register
                    .bind(py)
                    .upgrade()
                    .is_some_and(|value| value.is(candidate_register.bind(py)))
                    && extract
                        .bind(py)
                        .upgrade()
                        .is_some_and(|value| value.is(candidate_extract.bind(py)))
            }
            _ => false,
        })
    }

    fn current(&self) -> Result<Arc<Version>, Failure> {
        self.current
            .lock()
            .map_err(|_| unavailable())?
            .as_ref()
            .cloned()
            .ok_or_else(closed)
    }

    fn change(
        &self,
        patterns: Vec<PatternInput>,
        callbacks: ExtensionCallbacks,
        add: bool,
    ) -> PyResult<Result<PoolInfo, Failure>> {
        let original = match self.current() {
            Ok(original) => original,
            Err(error) => {
                drop_callbacks(callbacks);
                return Ok(Err(error));
            }
        };
        if !self.matches_callbacks(&callbacks) {
            drop_callbacks(callbacks);
            return Ok(Err(Failure::binding(
                "FAILED_PRECONDITION",
                "列池扩展不匹配 / Column pool extension does not match",
            )));
        }
        let changed: BTreeSet<_> = patterns.into_iter().map(pattern).collect();
        let patterns: BTreeSet<_> = if add {
            original.patterns.union(&changed).cloned().collect()
        } else {
            original.patterns.difference(&changed).cloned().collect()
        };
        if patterns == original.patterns {
            drop_callbacks(callbacks);
            return Ok(Ok(original.info()));
        }
        let Some(generation) = original.generation.checked_add(1) else {
            drop_callbacks(callbacks);
            return Ok(Err(Failure::binding(
                "OVERFLOW",
                "列池代次已耗尽 / Column pool generation exhausted",
            )));
        };
        let model = match prepare_lp(
            self.packing.clone(),
            patterns.iter().cloned().collect(),
            callbacks,
        )? {
            Ok(model) => model,
            Err(error) => return Ok(Err(error)),
        };
        let next = Arc::new(Version {
            generation,
            patterns,
            model,
        });
        let old = {
            let mut guard = match self.current.lock() {
                Ok(guard) => guard,
                Err(_) => return Ok(Err(unavailable())),
            };
            let Some(current) = guard.as_ref() else {
                return Ok(Err(closed()));
            };
            if !Arc::ptr_eq(current, &original) {
                return Ok(Err(Failure::binding(
                    "ABORTED",
                    "列池已并发修改 / Column pool changed concurrently",
                )));
            }
            guard.replace(Arc::clone(&next))
        };
        drop(old);
        Ok(Ok(next.info()))
    }
}

fn verify_lp(model: &FrozenLp, report: &SolveReport<f64>) -> Result<LpSolution, Failure> {
    if report.model_mapping.as_ref()
        != Some(&linear_model_mapping(&model.compiled).map_err(Failure::from)?)
        || report.fingerprints.model.as_ref()
            != Some(&linear_model_fingerprint(&model.compiled).map_err(Failure::from)?)
    {
        return Err(Failure::binding(
            "DATA_LOSS",
            "报告与编译模型不一致 / Report does not match compiled model",
        ));
    }
    let solution = report.solution.as_ref().ok_or_else(|| {
        Failure::binding("NO_SOLUTION", "后端没有解 / Backend returned no solution")
    })?;
    if solution.values.len() != model.compiled.basic.variables.len()
        || solution.values.len() != model.columns.len()
    {
        return Err(Failure::binding(
            "DATA_LOSS",
            "解向量与编译列不一致 / Solution vector does not match compiled columns",
        ));
    }
    let values = model
        .compiled
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
    if values.len() != model.snapshot.variables.len() {
        return Err(Failure::binding(
            "DATA_LOSS",
            "变量映射不完整 / Incomplete variable mapping",
        ));
    }
    model
        .snapshot
        .validate_solution(&values, &SafeRational::zero())
        .map_err(Failure::from)?;
    let objective = model.snapshot.objective.iter().try_fold(
        model.snapshot.objective_constant.clone(),
        |total, (id, coefficient)| {
            values
                .get(id)
                .map(|value| total + coefficient.clone() * value.clone())
                .ok_or_else(|| {
                    Failure::binding("DATA_LOSS", "目标变量缺失 / Objective variable missing")
                })
        },
    )?;
    let entries = model
        .compiled
        .basic
        .variables
        .iter()
        .zip(&model.columns)
        .map(|(variable, column)| {
            let value = values.get(&variable.id()).ok_or_else(|| {
                Failure::binding("DATA_LOSS", "源变量缺失 / Source variable missing")
            })?;
            Ok((
                column.0.clone(),
                (value.0.numer().clone(), value.0.denom().clone()),
            ))
        })
        .collect::<Result<Vec<_>, Failure>>()?;
    Ok((entries, objective.0.into_raw()))
}

#[pymethods]
impl Bpp1dPool {
    fn snapshot(&self, py: Python<'_>) -> Transport<PoolInfo> {
        transport(py.detach(|| self.current().map(|version| version.info())))
    }

    #[pyo3(signature = (*, patterns, extension=None))]
    fn add_columns(
        &self,
        py: Python<'_>,
        patterns: Vec<PatternInput>,
        extension: ExtensionCallbacks,
    ) -> PyResult<Transport<PoolInfo>> {
        if !valid_callbacks(py, &extension) {
            return Ok(transport(Err(Failure::input(
                "建模扩展回调必须可调用 / Modeling extension callbacks must be callable",
            ))));
        }
        py.detach(|| self.change(patterns, extension, true))
            .map(transport)
    }

    #[pyo3(signature = (*, patterns, extension=None))]
    fn remove_columns(
        &self,
        py: Python<'_>,
        patterns: Vec<PatternInput>,
        extension: ExtensionCallbacks,
    ) -> PyResult<Transport<PoolInfo>> {
        if !valid_callbacks(py, &extension) {
            return Ok(transport(Err(Failure::input(
                "建模扩展回调必须可调用 / Modeling extension callbacks must be callable",
            ))));
        }
        py.detach(|| self.change(patterns, extension, false))
            .map(transport)
    }

    fn close(&self, py: Python<'_>) -> Transport<()> {
        transport_unit(py.detach(|| {
            let old = self.current.lock().map_err(|_| unavailable())?.take();
            drop(old);
            Ok(())
        }))
    }

    #[pyo3(signature = (*, solver, time_limit=None, cancellation=None, on_progress=None))]
    fn solve_lp(
        &self,
        py: Python<'_>,
        solver: String,
        time_limit: Option<f64>,
        cancellation: Option<SolveHandle>,
        on_progress: Option<Py<PyAny>>,
    ) -> Transport<LpSolve> {
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
            let version = self.current()?;
            let identity = version.model.snapshot.revision.owner;
            let compiled = version.model.compiled.clone();
            let report = crate::solve::execute_compiled(identity, request, &compiled)?;
            let raw = serialize_report(&report)?;
            let (solution, error) = transport(verify_lp(&version.model, &report));
            Ok((
                version.generation,
                identity,
                raw,
                version.model.columns.clone(),
                solution,
                error,
            ))
        }))
    }

    #[pyo3(signature = (*, solver, expansion_limit, time_limit=None, cancellation=None, on_progress=None, extension=None))]
    #[allow(clippy::too_many_arguments)]
    fn solve_final_milp(
        &self,
        py: Python<'_>,
        solver: String,
        expansion_limit: u64,
        time_limit: Option<f64>,
        cancellation: Option<SolveHandle>,
        on_progress: Option<Py<PyAny>>,
        extension: ExtensionCallbacks,
    ) -> PyResult<Transport<(u64, FinalSolved)>> {
        if !valid_callbacks(py, &extension) {
            return Ok(transport(Err(Failure::input(
                "建模扩展回调必须可调用 / Modeling extension callbacks must be callable",
            ))));
        }
        if on_progress
            .as_ref()
            .is_some_and(|callback| !callback.bind(py).is_callable())
        {
            return Ok(transport(Err(Failure::input(
                "进度回调必须可调用 / Progress callback must be callable",
            ))));
        }
        let request = SolveRequest {
            solver,
            time_limit,
            cancellation,
            on_progress,
        };
        py.detach(|| {
            let version = match self.current() {
                Ok(version) => version,
                Err(error) => {
                    drop_callbacks(extension);
                    return Ok(transport(Err(error)));
                }
            };
            if !self.matches_callbacks(&extension) {
                drop_callbacks(extension);
                return Ok(transport(Err(Failure::binding(
                    "FAILED_PRECONDITION",
                    "列池扩展不匹配 / Column pool extension does not match",
                ))));
            }
            let result = solve_final(
                self.packing.clone(),
                version.patterns.iter().cloned().collect(),
                extension,
                request,
                expansion_limit,
            )?;
            Ok(transport(result.map(|solved| (version.generation, solved))))
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::One;
    use ospf_rust_core::solver::{
        ProblemStatus, SolveFingerprints, SolveSolution, TerminationReason,
    };
    use ospf_rust_framework_bpp::infrastructure::SameUnitPackingValueAdapter;
    use ospf_rust_framework_bpp1d::domain::{BinType, Item, PackingObjective, PackingProblem};
    use ospf_rust_quantities::quantity::Quantity;
    use ospf_rust_quantities::unit::{CTUnit, Kilogram, Meter};

    fn model() -> FrozenLp {
        Python::initialize();
        let length = Meter::runtime_unit();
        let mass = Kilogram::runtime_unit();
        let packing = PackingContext::new(
            PackingProblem {
                items: ["a", "b"]
                    .into_iter()
                    .map(|id| Item {
                        id: id.into(),
                        length: Quantity::new(SafeRational::one(), length.clone()),
                        weight: Quantity::new(SafeRational::zero(), mass.clone()),
                        amount: 1,
                        materials: BTreeMap::new(),
                    })
                    .collect(),
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
        let patterns = [
            ("bin".into(), BTreeMap::from([("a".into(), 1)])),
            (
                "bin".into(),
                BTreeMap::from([("a".into(), 1), ("b".into(), 1)]),
            ),
        ];
        prepare_lp(packing, patterns.into_iter().map(pattern).collect(), None)
            .unwrap()
            .unwrap()
    }

    #[test]
    fn committed_snapshot_and_pool_are_send_and_sync() {
        fn check<T: Send + Sync>() {}
        check::<FrozenLp>();
        check::<Bpp1dPool>();
    }

    #[test]
    fn lp_solution_gate_checks_identity_mapping_and_native_rows() {
        let mut model = model();
        model.compiled.basic.variables.reverse();
        model.compiled.c.reverse();
        model.columns.reverse();
        let values = model
            .columns
            .iter()
            .map(|column| {
                if column.2.as_ref().unwrap().1.contains_key("b") {
                    1.0
                } else {
                    0.0
                }
            })
            .collect();
        let report = SolveReport::builder(ProblemStatus::Feasible, TerminationReason::Completed)
            .solution(SolveSolution::vector(values))
            .model_mapping(Some(linear_model_mapping(&model.compiled).unwrap()))
            .fingerprints(SolveFingerprints {
                model: Some(linear_model_fingerprint(&model.compiled).unwrap()),
                ..Default::default()
            })
            .build()
            .unwrap();
        let (entries, objective) = verify_lp(&model, &report).unwrap();
        assert_eq!(objective, (1.into(), 1.into()));
        assert_eq!(entries.len(), 2);
        for (entry, column) in entries.iter().zip(&model.columns) {
            assert_eq!(entry.0, column.0);
            assert_eq!(
                entry.1,
                if column.2.as_ref().unwrap().1.contains_key("b") {
                    (1.into(), 1.into())
                } else {
                    (0.into(), 1.into())
                }
            );
        }

        let mut invalid = report.clone();
        invalid.model_mapping = None;
        assert!(verify_lp(&model, &invalid).is_err());
        invalid = report.clone();
        invalid
            .model_mapping
            .as_mut()
            .unwrap()
            .variables_by_column
            .reverse();
        assert!(verify_lp(&model, &invalid).is_err());
        invalid = report.clone();
        invalid.fingerprints.model = None;
        assert!(verify_lp(&model, &invalid).is_err());
        let mut other = model.compiled.clone();
        other.c[0] += 1.0;
        invalid.fingerprints.model = Some(linear_model_fingerprint(&other).unwrap());
        assert!(verify_lp(&model, &invalid).is_err());
        invalid = report.clone();
        invalid.solution.as_mut().unwrap().values.pop();
        assert!(verify_lp(&model, &invalid).is_err());
        invalid = report.clone();
        invalid.solution.as_mut().unwrap().values.fill(0.0);
        assert!(verify_lp(&model, &invalid).is_err());
        invalid = report.clone();
        invalid.solution.as_mut().unwrap().values[0] = f64::NAN;
        assert!(verify_lp(&model, &invalid).is_err());
        invalid = report.clone();
        invalid.solution.as_mut().unwrap().objective_value = Some(123.0);
        assert!(verify_lp(&model, &invalid).is_ok());
    }
}
