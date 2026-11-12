//! 精确模型扩展的快照与声明式注册。 / Snapshot and declarative registration for exact model extensions.

use std::cell::{Cell, RefCell};
use std::collections::{BTreeMap, BTreeSet};
use std::rc::Rc;

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use ospf_rust_core::error::{CoreError, ModelError, Result};
use ospf_rust_core::model::flatten::{Linear, LinearMonomial};
use ospf_rust_core::model::{ConstraintRelation, LinearModelSnapshot, MetaModel, SubObjective};
use ospf_rust_core::token::TokenVariableData;
use ospf_rust_core::variable::{VariableId, VariableType, new_standalone_id};
use ospf_rust_framework_bpp1d::domain::{
    PackingContext, PackingModelStage, PackingObjective, PatternAggregation,
    PatternModelingExtension,
};
use ospf_rust_quantities::unit::Unit;
use pyo3::prelude::*;

use crate::quantities::QuantityUnit;
use crate::safe_rational::SafeRational;

pub(crate) type Ratio = (BigInt, BigInt);
pub(crate) type Reference = (u64, Option<(usize, usize)>, Option<String>);
type Term = (Reference, Ratio);
type Variable = (String, String, Option<Ratio>, Option<Ratio>);
type Row = (String, Vec<Term>, String, Ratio);
type Registration = (Vec<Variable>, Vec<Row>, Vec<Term>, Ratio);
type Pattern = (String, BTreeMap<String, u64>);
type ItemSnapshot = (String, Ratio, Ratio, u64, BTreeMap<String, u64>);
type BinSnapshot = (String, Ratio, Ratio, Ratio, Option<u64>);
type Domain = (
    Vec<ItemSnapshot>,
    Vec<BinSnapshot>,
    Ratio,
    Py<QuantityUnit>,
    Py<QuantityUnit>,
    &'static str,
);

pub(crate) fn reference(owner: u64, id: VariableId) -> Reference {
    (owner, Some((id.group_id, id.index_in_group)), None)
}

fn invalid(message: &'static str) -> CoreError {
    ModelError::InvalidConstraint(message.into()).into()
}

fn rational((numerator, denominator): Ratio) -> Result<SafeRational> {
    if !denominator.is_positive() {
        return Err(invalid("extension denominator must be positive"));
    }
    Ok(SafeRational(BigRational::new(numerator, denominator)))
}

fn ratio(value: &SafeRational) -> Ratio {
    (value.0.numer().clone(), value.0.denom().clone())
}

fn domain(py: Python<'_>, packing: &PackingContext<SafeRational, Unit, Unit>) -> PyResult<Domain> {
    let problem = packing.problem();
    let items = problem
        .items
        .iter()
        .map(|item| {
            (
                item.id.clone(),
                ratio(&item.length.value),
                ratio(&item.weight.value),
                item.amount,
                item.materials.clone(),
            )
        })
        .collect();
    let bins = problem
        .bin_types
        .iter()
        .map(|bin| {
            (
                bin.id.clone(),
                ratio(&bin.length.value),
                ratio(&bin.max_weight.value),
                ratio(&bin.cost),
                bin.inventory,
            )
        })
        .collect();
    let objective = match problem.objective {
        PackingObjective::BinCount => "bin_count",
        PackingObjective::ConsumedLength => "consumed_length",
        PackingObjective::Cost => "cost",
    };
    Ok((
        items,
        bins,
        ratio(&problem.spacing.value),
        Py::new(py, QuantityUnit::from_unit(problem.length_unit.clone()))?,
        Py::new(py, QuantityUnit::from_unit(problem.weight_unit.clone()))?,
        objective,
    ))
}

#[derive(Default)]
pub(crate) struct ExtensionState {
    used: Cell<bool>,
    error: RefCell<Option<PyErr>>,
    references: RefCell<BTreeMap<VariableId, Reference>>,
    patterns: RefCell<BTreeMap<VariableId, Pattern>>,
    packing: RefCell<Option<PackingContext<SafeRational, Unit, Unit>>>,
    lp_origin: RefCell<Option<LinearModelSnapshot<SafeRational>>>,
}

impl ExtensionState {
    pub(crate) fn begin(&self) -> bool {
        !self.used.replace(true)
    }

    pub(crate) fn take_error(&self) -> Option<PyErr> {
        self.error.borrow_mut().take()
    }

    pub(crate) fn lookup(&self, id: VariableId) -> Option<Reference> {
        self.references.borrow().get(&id).cloned()
    }

    pub(crate) fn pattern(&self, id: VariableId) -> Option<Pattern> {
        self.patterns.borrow().get(&id).cloned()
    }

    pub(crate) fn reference_count(&self) -> usize {
        self.references.borrow().len()
    }

    pub(crate) fn take_lp_origin(&self) -> Option<LinearModelSnapshot<SafeRational>> {
        self.lp_origin.borrow_mut().take()
    }

    pub(crate) fn rebind(&self, owner: u64) {
        for reference in self.references.borrow_mut().values_mut() {
            reference.0 = owner;
        }
    }
}

pub(crate) struct PythonExtension {
    pub(crate) callbacks: Option<(Py<PyAny>, Py<PyAny>)>,
    pub(crate) state: Rc<ExtensionState>,
}

impl PythonExtension {
    fn callback<T>(&self, result: PyResult<Option<T>>) -> Result<T> {
        match result {
            Ok(Some(value)) => Ok(value),
            Ok(None) => Err(CoreError::callback_error("BPP1D extension callback failed")),
            Err(error) => {
                *self.state.error.borrow_mut() = Some(error);
                Err(CoreError::callback_error("BPP1D extension callback raised"))
            }
        }
    }
}

impl PatternModelingExtension<SafeRational, Unit, Unit> for PythonExtension {
    fn register(
        &self,
        model: &mut MetaModel<SafeRational>,
        packing: &PackingContext<SafeRational, Unit, Unit>,
        aggregation: &PatternAggregation<SafeRational>,
        stage: PackingModelStage,
    ) -> Result<()> {
        self.state.used.set(true);
        let Some((register, _)) = &self.callbacks else {
            if stage == PackingModelStage::Lp {
                *self.state.lp_origin.borrow_mut() = Some(model.linear_model_snapshot()?);
            }
            return Ok(());
        };
        let is_lp = stage == PackingModelStage::Lp;
        let owner = model.model_identity();
        let mut indices = BTreeMap::new();
        let mut references = BTreeMap::new();
        let mut patterns = BTreeMap::new();
        let mut candidates = Vec::new();
        let token_indices = model
            .tokens()
            .iter()
            .enumerate()
            .map(|(index, token)| (token.id(), index))
            .collect::<BTreeMap<_, _>>();
        for (pattern, id) in &aggregation.variables {
            let key = reference(owner, *id);
            let index = *token_indices
                .get(id)
                .ok_or_else(|| invalid("extension candidate variable missing"))?;
            indices.insert(key.clone(), index);
            references.insert(*id, key.clone());
            let snapshot = (pattern.bin_type_id.clone(), pattern.amounts.clone());
            patterns.insert(*id, snapshot.clone());
            candidates.push((key, snapshot));
        }
        let stage = match stage {
            PackingModelStage::Milp => "milp",
            PackingModelStage::Lp => "lp",
            PackingModelStage::FinalMilp => "final_milp",
        };
        let returned = Python::attach(|py| -> PyResult<Option<Registration>> {
            let (items, bins, spacing, length, weight, objective) = domain(py, packing)?;
            let snapshot = (
                owner, stage, items, bins, spacing, length, weight, objective, candidates,
            );
            register.bind(py).call1((snapshot,))?.extract()
        });
        let (variables, rows, objective, constant) = self.callback(returned)?;
        let mut names = model
            .tokens()
            .iter()
            .map(|token| token.name().to_owned())
            .collect::<BTreeSet<_>>();
        for (name, kind, lower, upper) in variables {
            if name.trim().is_empty() || !names.insert(name.clone()) {
                return Err(invalid("invalid or duplicate extension variable name"));
            }
            let variable_type = match kind.as_str() {
                "continuous" => VariableType::Continuous,
                "integer" => VariableType::Integer,
                "binary" => VariableType::Binary,
                _ => return Err(invalid("unknown extension variable type")),
            };
            let mut lower = lower.map(rational).transpose()?;
            let mut upper = upper.map(rational).transpose()?;
            if variable_type == VariableType::Binary {
                lower = Some(lower.unwrap_or_else(SafeRational::zero));
                upper = Some(upper.unwrap_or_else(SafeRational::one));
                if lower
                    .as_ref()
                    .is_some_and(|value| value < &SafeRational::zero())
                    || upper
                        .as_ref()
                        .is_some_and(|value| value > &SafeRational::one())
                {
                    return Err(invalid("binary extension bounds outside zero to one"));
                }
            }
            if matches!((&lower, &upper), (Some(lower), Some(upper)) if lower > upper) {
                return Err(invalid("reversed extension variable bounds"));
            }
            let id = new_standalone_id();
            let index = model.register_variable_data(TokenVariableData {
                id,
                index: 0,
                name: name.clone(),
                display_name: None,
                var_type: variable_type,
                lower_bound: lower,
                upper_bound: upper,
            })?;
            let key = (owner, None, Some(name));
            indices.insert(key.clone(), index);
            references.insert(id, key);
        }
        let terms = |terms: Vec<Term>| -> Result<Vec<LinearMonomial<SafeRational>>> {
            terms
                .into_iter()
                .map(|(key, coefficient)| {
                    let index = *indices
                        .get(&key)
                        .ok_or_else(|| invalid("unknown or stale extension variable"))?;
                    Ok(LinearMonomial::new(rational(coefficient)?, index))
                })
                .collect()
        };
        let mut row_names = BTreeSet::new();
        for (name, row_terms, relation, rhs) in rows {
            if name.trim().is_empty() || !row_names.insert(name.clone()) {
                return Err(invalid("invalid or duplicate extension row name"));
            }
            let relation = match relation.as_str() {
                "<=" => ConstraintRelation::LessEqual,
                ">=" => ConstraintRelation::GreaterEqual,
                "==" => ConstraintRelation::Equal,
                _ => return Err(invalid("unknown extension relation")),
            };
            model.add_linear_polynomial_constraint(
                Linear::new(terms(row_terms)?, SafeRational::zero()),
                relation,
                rational(rhs)?,
                &name,
            )?;
        }
        model.add_sub_objective(SubObjective::minimize(
            Linear::new(terms(objective)?, rational(constant)?),
            "extension",
        ));
        let lp_origin = if is_lp {
            Some(model.linear_model_snapshot()?)
        } else {
            None
        };
        self.state.references.borrow_mut().extend(references);
        self.state.patterns.borrow_mut().extend(patterns);
        *self.state.packing.borrow_mut() = Some(packing.clone());
        *self.state.lp_origin.borrow_mut() = lp_origin;
        Ok(())
    }

    fn extract_solution(
        &self,
        values: &BTreeMap<VariableId, SafeRational>,
    ) -> Result<BTreeMap<String, String>> {
        let Some((_, extract)) = &self.callbacks else {
            return Ok(BTreeMap::new());
        };
        let entries = {
            let references = self.state.references.borrow();
            let patterns = self.state.patterns.borrow();
            let mut owner = None;
            values
                .iter()
                .map(|(id, value)| {
                    let key = references
                        .get(id)
                        .ok_or_else(|| invalid("extension solution variable missing"))?;
                    if owner.is_some_and(|previous| previous != key.0) {
                        return Err(invalid("extension solution spans multiple models"));
                    }
                    owner = Some(key.0);
                    let pattern = patterns.get(id).cloned();
                    if key.1.is_some() != pattern.is_some() {
                        return Err(invalid("extension solution candidate identity missing"));
                    }
                    Ok((key.clone(), pattern, ratio(value)))
                })
                .collect::<Result<Vec<_>>>()?
        };
        let packing = self
            .state
            .packing
            .borrow()
            .clone()
            .ok_or_else(|| invalid("extension solution domain missing"))?;
        let returned = Python::attach(|py| -> PyResult<Option<BTreeMap<String, String>>> {
            let (items, bins, spacing, length, weight, objective) = domain(py, &packing)?;
            let snapshot = (items, bins, spacing, length, weight, objective, entries);
            extract.bind(py).call1((snapshot,))?.extract()
        });
        self.callback(returned)
    }
}
