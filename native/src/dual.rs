//! 同次编译与求解的私有对偶证书。 / Private dual certificates from one compilation and solve.

use std::cmp::Ordering;
use std::collections::BTreeMap;
use std::sync::Arc;

use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use ospf_rust_core::model::intermediate::LinearTriadModel;
use ospf_rust_core::model::{
    ConstraintRelation, LinearModelCompilationFlt64, LinearModelSnapshot, ObjectiveCategory,
};
use ospf_rust_core::solver::{
    SolveReport, SolveSolution, TerminationReason, evaluate_linear_solution,
    linear_model_fingerprint, linear_model_mapping,
    require_optimal_lp_certificate_for_linear_model, require_optimal_lp_certificate_for_model,
};
use ospf_rust_core::variable::VariableType;
use pyo3::prelude::*;

use crate::failure::Failure;
use crate::numeric::compare_rationals;

#[pyclass(frozen, from_py_object, module = "ospf_python._native")]
#[derive(Clone)]
pub struct DualCertificate {
    provenance: Arc<u8>,
    generation: u64,
    prices: Arc<BTreeMap<String, f64>>,
}

fn unavailable(message: &'static str) -> Failure {
    Failure::binding("FAILED_PRECONDITION", message)
}

pub(crate) fn exact(value: f64) -> Result<BigRational, Failure> {
    BigRational::from_float(value)
        .ok_or_else(|| unavailable("证书含非有限值 / Certificate contains a nonfinite value"))
}

pub(crate) fn require_exact_lp<'a>(
    report: &'a SolveReport<f64>,
    model: &LinearTriadModel,
) -> Result<&'a [f64], Failure> {
    let mapping = linear_model_mapping(model).map_err(Failure::from)?;
    if report.model_mapping.as_ref() != Some(&mapping) {
        return Err(unavailable(
            "报告映射与编译模型不一致 / Report mapping differs from compiled model",
        ));
    }
    let fingerprint = linear_model_fingerprint(model).map_err(Failure::from)?;
    let certificate =
        require_optimal_lp_certificate_for_model(report, &fingerprint).map_err(Failure::from)?;
    let solution = report
        .solution
        .as_ref()
        .ok_or_else(|| unavailable("最优报告缺少解 / Optimal report has no solution"))?;
    if solution.values.len() != model.num_variables()
        || certificate.dual.len() != model.num_constraints()
    {
        return require_optimal_lp_certificate_for_linear_model(report, model)
            .map(|certificate| certificate.dual)
            .map_err(Failure::from);
    }
    let exact_result = exact_lp_objectives(model, &solution.values, certificate.dual);
    if let Ok((primal, bound)) = &exact_result
        && compare_rationals(primal, bound) != Ordering::Equal
        && upstream_accepts_gap(model, solution, primal, bound)
    {
        return Err(unavailable("对偶间隙非零 / Primal-dual gap is nonzero"));
    }
    require_optimal_lp_certificate_for_linear_model(report, model).map_err(Failure::from)?;
    let (primal, bound) = exact_result?;
    if compare_rationals(&primal, &bound) != Ordering::Equal {
        return Err(unavailable("对偶间隙非零 / Primal-dual gap is nonzero"));
    }
    Ok(certificate.dual)
}

fn exact_lp_objectives(
    model: &LinearTriadModel,
    values: &[f64],
    dual: &[f64],
) -> Result<(BigRational, BigRational), Failure> {
    let minimizing = model.objective_category == ObjectiveCategory::Minimum;
    let mut activity = vec![BigRational::zero(); model.num_variables()];
    let mut bound = BigRational::zero();
    for (index, row) in model.A.rows.iter().enumerate() {
        let multiplier = exact(dual[index])?;
        if (minimizing && multiplier.is_positive()) || (!minimizing && multiplier.is_negative()) {
            return Err(unavailable("对偶符号无效 / Invalid dual sign"));
        }
        let rhs = exact(model.b[index])?;
        bound += &multiplier * &rhs;
        let mut primal_row = BigRational::zero();
        for (column, coefficient) in &row.entries {
            let coefficient = exact(*coefficient)?;
            activity[*column] += &multiplier * &coefficient;
            primal_row += coefficient * exact(values[*column])?;
        }
        if compare_rationals(&primal_row, &rhs) == Ordering::Greater {
            return Err(unavailable(
                "解违反精确行约束 / Solution violates an exact row",
            ));
        }
    }
    let mut primal = BigRational::zero();
    for (index, row_activity) in activity.into_iter().enumerate() {
        let value = exact(values[index])?;
        let lower = model.lb[index];
        let upper = model.ub[index];
        if (lower.is_finite() && compare_rationals(&value, &exact(lower)?) == Ordering::Less)
            || (upper.is_finite() && compare_rationals(&value, &exact(upper)?) == Ordering::Greater)
        {
            return Err(unavailable(
                "解违反精确变量界 / Solution violates an exact bound",
            ));
        }
        let cost = exact(model.c[index])?;
        primal += &cost * &value;
        let residual = cost - row_activity;
        if !residual.is_zero() {
            let extremum = if residual.is_positive() == minimizing {
                lower
            } else {
                upper
            };
            if !extremum.is_finite() {
                return Err(unavailable(
                    "对偶残差缺少有限极界 / Dual residual has no finite extremal bound",
                ));
            }
            bound += residual * exact(extremum)?;
        }
    }
    Ok((primal, bound))
}

fn within_tolerance(left: &BigRational, right: &BigRational, tolerance: &BigRational) -> bool {
    let mut magnitude = BigRational::one();
    for value in [left.abs(), right.abs()] {
        if compare_rationals(&value, &magnitude) == Ordering::Greater {
            magnitude = value;
        }
    }
    compare_rationals(&(left - right).abs(), &(tolerance * magnitude)) != Ordering::Greater
}

// shortcut: 仅预筛固定上游的容差内间隙，升级上游门禁时需复核。
// shortcut: Only preflight gaps within the pinned upstream tolerance; reassess on upstream upgrades.
fn upstream_accepts_gap(
    model: &LinearTriadModel,
    solution: &SolveSolution<f64>,
    primal: &BigRational,
    bound: &BigRational,
) -> bool {
    let Some(reported) = solution
        .objective_value
        .or(solution.objective)
        .and_then(BigRational::from_float)
    else {
        return false;
    };
    let Some(tolerance) = BigRational::from_float(1e-7) else {
        return false;
    };
    if model.has_integer_variables()
        || !within_tolerance(primal, &reported, &tolerance)
        || !within_tolerance(primal, bound, &tolerance)
    {
        return false;
    }
    evaluate_linear_solution(model, &solution.values, 1e-7).is_ok_and(|diagnostics| {
        diagnostics
            .constraint_evaluations
            .iter()
            .all(|evaluation| evaluation.satisfied)
            && diagnostics
                .variable_bound_evaluations
                .iter()
                .all(|evaluation| evaluation.satisfied)
    })
}

impl DualCertificate {
    pub fn price(
        &self,
        provenance: &Arc<u8>,
        generation: u64,
        source: &str,
    ) -> Result<f64, Failure> {
        if !Arc::ptr_eq(&self.provenance, provenance) {
            return Err(Failure::input(
                "证书属于其他模型 / Certificate belongs to another model",
            ));
        }
        if self.generation != generation {
            return Err(unavailable(
                "模型已修改，证书失效 / Model changed; certificate is stale",
            ));
        }
        self.prices.get(source).copied().ok_or_else(|| {
            Failure::binding(
                "NOT_FOUND",
                "证书不含此源行 / Source row is absent from certificate",
            )
        })
    }
}

pub fn issue(
    snapshot: &LinearModelSnapshot<f64>,
    compilation: &LinearModelCompilationFlt64,
    report: &SolveReport<f64>,
    provenance: Arc<u8>,
    generation: u64,
    cancelled: bool,
) -> Result<DualCertificate, Failure> {
    if cancelled
        || report.termination_reason != TerminationReason::Completed
        || snapshot
            .variables
            .iter()
            .any(|state| state.var_type != VariableType::Continuous)
        || snapshot.objective_constant != 0.0
    {
        return Err(unavailable(
            "不是已完成的零常数 LP / Not a completed zero-constant LP",
        ));
    }
    let dual = require_exact_lp(report, &compilation.model)?;
    let prices = source_prices(snapshot, compilation, dual, true)?;
    Ok(DualCertificate {
        provenance,
        generation,
        prices: Arc::new(prices),
    })
}

pub(crate) fn source_prices(
    snapshot: &LinearModelSnapshot<f64>,
    compilation: &LinearModelCompilationFlt64,
    dual: &[f64],
    original_direction: bool,
) -> Result<BTreeMap<String, f64>, Failure> {
    if compilation.revision != snapshot.revision || compilation.rows.len() != dual.len() {
        return Err(unavailable(
            "编译版本或行数量不匹配 / Compiled revision or row count mismatch",
        ));
    }
    let mut rows = BTreeMap::new();
    for row in &snapshot.rows {
        let expected = match row.relation {
            ConstraintRelation::LessEqual => 1,
            ConstraintRelation::GreaterEqual => 2,
            ConstraintRelation::Equal => 3,
        };
        if rows
            .insert(
                row.id.as_str(),
                (0.0_f64, BigRational::zero(), 0_u8, expected),
            )
            .is_some()
        {
            return Err(unavailable("源行身份重复 / Duplicate source-row identity"));
        }
    }
    let direction =
        if original_direction && snapshot.objective_category == ObjectiveCategory::Maximum {
            -1.0
        } else {
            1.0
        };
    for (row, dual) in compilation.rows.iter().zip(dual) {
        let Some((price, exact_price, seen, expected)) = rows.get_mut(row.source.as_str()) else {
            return Err(unavailable("编译行来源未知 / Unknown compiled-row source"));
        };
        let flag = match row.multiplier {
            1 => 1,
            -1 => 2,
            _ => {
                return Err(unavailable(
                    "编译行乘数无效 / Invalid compiled-row multiplier",
                ));
            }
        };
        if *expected & flag == 0 || *seen & flag != 0 {
            return Err(unavailable(
                "编译行来源重复或方向错误 / Duplicate or invalid compiled-row source",
            ));
        }
        *seen |= flag;
        *price += direction * f64::from(row.multiplier) * dual;
        *exact_price += exact(direction * f64::from(row.multiplier))? * exact(*dual)?;
        if !price.is_finite() {
            return Err(unavailable(
                "源行价格非有限 / Source-row price is nonfinite",
            ));
        }
    }
    if rows.values().any(|(_, _, seen, expected)| seen != expected) {
        return Err(unavailable(
            "源行映射不完整 / Incomplete source-row mapping",
        ));
    }
    let mut prices = BTreeMap::new();
    for (id, (price, exact_price, _, _)) in rows {
        if compare_rationals(&exact(price)?, &exact_price) != Ordering::Equal {
            return Err(unavailable(
                "源行价格无法精确表示 / Source-row price is not exactly representable",
            ));
        }
        prices.insert(id.to_owned(), price);
    }
    Ok(prices)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::owner::Owner;
    use num_bigint::{BigInt, BigUint};
    use num_traits::ToPrimitive;
    use ospf_rust_core::model::{LinearObjectiveInput, MetaModel};
    use ospf_rust_core::solver::{
        ProblemStatus, SolveFingerprints, SolveProof, SolveSolution, linear_model_fingerprint,
    };
    use ospf_rust_core::variable::{Continuous, VariableRange};

    fn report(
        model: &LinearTriadModel,
        values: Vec<f64>,
        dual: Vec<f64>,
        objective: f64,
    ) -> SolveReport<f64> {
        let mut solution = SolveSolution::vector(values);
        solution.objective_value = Some(objective);
        solution.dual_solution = Some(dual);
        SolveReport::builder(ProblemStatus::Feasible, TerminationReason::Completed)
            .solution(solution)
            .proof(SolveProof::optimality())
            .model_mapping(Some(linear_model_mapping(model).unwrap()))
            .fingerprints(SolveFingerprints {
                model: Some(linear_model_fingerprint(model).unwrap()),
                ..Default::default()
            })
            .build()
            .unwrap()
    }

    #[test]
    fn synthetic_near_optimal_dual_does_not_issue_certificate() {
        let mut model = MetaModel::<f64>::new("synthetic dual gap");
        let x = model
            .register_auto_variable_with_range::<Continuous>("x", VariableRange::bounded(0.0, 1.0))
            .unwrap();
        model
            .add_linear_constraint(&[(x, 1.0)], ConstraintRelation::GreaterEqual, 1.0, "demand")
            .unwrap();
        model.set_linear_objective_input(
            LinearObjectiveInput::minimize("objective").terms(vec![(x, 1.0)]),
        );
        let snapshot = model.linear_model_snapshot().unwrap();
        let compiled = snapshot.compile_flt64().unwrap();
        let report = report(
            &compiled.model,
            vec![1.0],
            vec![-1.0 + 2.0_f64.powi(-25)],
            1.0,
        );
        assert!(require_optimal_lp_certificate_for_linear_model(&report, &compiled.model).is_ok());
        assert!(issue(&snapshot, &compiled, &report, Arc::new(0), 0, false).is_err());
    }

    // 两个 Float64 乘积的分母可达 2^2148；此见证深但不保证最深。
    // Products of two Float64 values can have denominator 2^2148; this witness is deep, not
    // necessarily the deepest one.
    const GOLDEN_DYADIC: &[u8] = b"19e3779b97f4a7c15f39cc0605cedc8341082276bf3a27251f86c6a11d0c1\
8e952767f0b153d27b7f0347045b5bf1827f01886f0928403002c1d64ba40f335e36f06ad7ae9717877e85839d6effbd\
7dc664d325d1c5371682cadd0cccfdffbbe1626e33b8d04b4331bbf73c790d94f79d471c4ab3ed3d82a5fec507705e4a\
e6e5e73a9b91f3aa4db287ae44f332e923a73cb91648e428e975a3781eb01b49d8674fa1508419e0eaa4038b352d9bad\
30f4485b71a8ef64452a0dd40dc8cb8f9a2d4c514f1b229dcaa222ac268e9666e4a866769145f5f5880a9d0acd3b9e8c\
682f4f810320abeb94034e70f21608c061ab1c1caef1ebdcefbc72134ecf06ed82bfb7d8eb1a41901d65f5c8cab29";

    fn negative_power_of_two(exponent: u32) -> f64 {
        // 2^-exponent：正常区间写指数字段，次正规区间直接落尾数位。 / Exponent field while normal, then a bare mantissa bit.
        if exponent <= 1022 {
            f64::from_bits(((1023 - exponent) as u64) << 52)
        } else {
            f64::from_bits(1_u64 << (1074 - exponent))
        }
    }

    fn deep_float64_terms() -> Vec<(f64, f64)> {
        let numerator = BigUint::parse_bytes(GOLDEN_DYADIC, 16).expect("golden dyadic numerator");
        let tiny = negative_power_of_two(1074);
        let mut terms = vec![(1.0_f64, 1.0_f64)];
        for segment in [0_usize, 1074] {
            for start in (0..1074_usize).step_by(53) {
                let end = (start + 53).min(1074);
                let chunk: BigUint = (&numerator >> (2148 - segment - end))
                    & ((BigUint::from(1_u8) << (end - start)) - 1_u8);
                if chunk.is_zero() {
                    continue;
                }
                terms.push((
                    chunk.to_f64().expect("53-bit chunk") * negative_power_of_two(end as u32),
                    if segment == 0 { 1.0 } else { tiny },
                ));
            }
        }
        // 验证该深递归见证可由 Float64 输入精确构造。
        // Verify the deep-recursion witness is exactly representable by Float64 inputs.
        let accumulated = terms
            .iter()
            .fold(BigRational::zero(), |sum, (cost, value)| {
                sum + exact(*cost).unwrap() * exact(*value).unwrap()
            });
        assert_eq!(
            accumulated,
            BigRational::new(
                BigInt::from(numerator),
                BigInt::from(BigUint::from(1_u8) << 2148)
            )
        );
        terms
    }

    fn deep_float64_report(
        model: &mut MetaModel<f64>,
    ) -> Result<(LinearTriadModel, SolveReport<f64>), Failure> {
        let terms = deep_float64_terms();
        let mut costs = Vec::with_capacity(terms.len() + 1);
        let mut values = Vec::with_capacity(terms.len() + 1);
        for (index, (cost, value)) in terms.iter().enumerate() {
            let variable = model
                .register_auto_variable_with_range::<Continuous>(
                    &format!("dyadic_{index}"),
                    VariableRange::bounded(*value, *value),
                )
                .map_err(Failure::from)?;
            costs.push((variable, *cost));
            values.push(*value);
        }
        let tiny = negative_power_of_two(1074);
        let gap = model
            .register_auto_variable_with_range::<Continuous>(
                "gap",
                VariableRange::bounded(0.0, tiny),
            )
            .map_err(Failure::from)?;
        costs.push((gap, tiny));
        values.push(tiny);
        model.set_linear_objective_input(LinearObjectiveInput::minimize("objective").terms(costs));
        model
            .add_le_constraint(&[], 0.0, "dummy")
            .map_err(Failure::from)?;
        let compiled = model
            .linear_model_snapshot()
            .map_err(Failure::from)?
            .compile_flt64()
            .map_err(Failure::from)?;
        let report = report(&compiled.model, values, vec![0.0], 1.618_033_988_749_895);
        Ok((compiled.model, report))
    }

    #[test]
    fn owner_thread_stack_survives_a_deep_float64_rational_recursion() {
        let owner = Owner::new("deep float64 recursion".into()).unwrap();
        let (upstream_accepted, rejection) = owner
            .mutate(|model| {
                let (compiled, report) = deep_float64_report(model)?;
                Ok((
                    require_optimal_lp_certificate_for_linear_model(&report, &compiled).is_ok(),
                    require_exact_lp(&report, &compiled).unwrap_err().message,
                ))
            })
            .unwrap();
        // 上游容差门禁接受 2^-2148 间隙；绑定精确门禁拒绝它，两者都在 owner 线程栈内完成。
        // The upstream tolerance gate accepts the 2^-2148 gap; the binding's exact gate rejects
        // it, and both finished inside the owner thread stack.
        assert!(upstream_accepted);
        assert!(rejection.contains("对偶间隙非零"), "{rejection}");
    }

    #[test]
    fn deep_invalid_certificate_is_rejected_on_a_small_stack() {
        const CHILD: &str = "OSPF_DEEP_INVALID_CERTIFICATE_CHILD";
        const READY: &str = "deep certificate fixture ready";
        if std::env::var_os(CHILD).is_some() {
            std::thread::Builder::new()
                .stack_size(512 * 1024)
                .spawn(|| {
                    use std::io::Write;

                    let mut model = MetaModel::<f64>::new("deep float64 recursion");
                    let (compiled, report) = deep_float64_report(&mut model).unwrap();
                    println!("{READY}");
                    std::io::stdout().flush().unwrap();
                    let rejection = require_exact_lp(&report, &compiled).unwrap_err();
                    assert_eq!(rejection.category, "FAILED_PRECONDITION");
                    assert!(rejection.message.contains("对偶间隙非零"));
                })
                .unwrap()
                .join()
                .unwrap();
            return;
        }
        let output = std::process::Command::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "dual::tests::deep_invalid_certificate_is_rejected_on_a_small_stack",
                "--nocapture",
            ])
            .env(CHILD, "1")
            .output()
            .unwrap();
        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);
        assert!(
            stdout.contains(READY),
            "fixture did not finish: {stdout}\n{stderr}"
        );
        assert!(
            output.status.success(),
            "child failed: {}\n{stdout}\n{stderr}",
            output.status
        );
    }

    #[test]
    fn exact_gate_retains_upstream_report_validation_and_error_priority() {
        let mut source = MetaModel::<f64>::new("report validation");
        let x = source
            .register_auto_variable_with_range::<Continuous>("x", VariableRange::bounded(0.0, 1.0))
            .unwrap();
        source.add_le_constraint(&[(x, 1.0)], 1.0, "upper").unwrap();
        source.add_le_constraint(&[], 0.0, "dummy").unwrap();
        source.set_linear_objective_input(
            LinearObjectiveInput::minimize("objective").terms(vec![(x, 1.0)]),
        );
        let model = source
            .linear_model_snapshot()
            .unwrap()
            .compile_flt64()
            .unwrap()
            .model;
        let good = report(&model, vec![0.0], vec![0.0, 0.0], 0.0);
        assert!(require_exact_lp(&good, &model).is_ok());

        let assert_upstream = |bad: &SolveReport<f64>, model: &LinearTriadModel| {
            let expected = Failure::from(
                require_optimal_lp_certificate_for_linear_model(bad, model).unwrap_err(),
            );
            let actual = require_exact_lp(bad, model).unwrap_err();
            assert_eq!(
                (
                    actual.category,
                    actual.source,
                    actual.rust_code,
                    actual.error_class,
                    actual.message
                ),
                (
                    expected.category,
                    expected.source,
                    expected.rust_code,
                    expected.error_class,
                    expected.message
                )
            );
        };

        for values in [vec![], vec![0.0, 0.0], vec![f64::NAN], vec![f64::INFINITY]] {
            let mut bad = good.clone();
            bad.solution.as_mut().unwrap().values = values;
            assert_upstream(&bad, &model);
        }
        for dual in [
            vec![],
            vec![0.0],
            vec![0.0, 0.0, 0.0],
            vec![f64::NAN, 0.0],
            vec![1.0, 0.0],
        ] {
            let mut bad = good.clone();
            bad.solution.as_mut().unwrap().dual_solution = Some(dual);
            assert_upstream(&bad, &model);
        }
        let mut missing_dual = good.clone();
        missing_dual.solution.as_mut().unwrap().dual_solution = None;
        assert_upstream(&missing_dual, &model);
        let mut wrong_fingerprint = good.clone();
        wrong_fingerprint.fingerprints.model = None;
        wrong_fingerprint.solution.as_mut().unwrap().values.clear();
        assert_upstream(&wrong_fingerprint, &model);
        let mut missing_proof = good.clone();
        missing_proof.proof = None;
        assert_upstream(&missing_proof, &model);
        let mut wrong_objective = good.clone();
        wrong_objective.solution.as_mut().unwrap().objective_value = Some(1.0);
        assert_upstream(&wrong_objective, &model);
        let mut bad_primal = good.clone();
        bad_primal.solution.as_mut().unwrap().values[0] = 2.0;
        assert_upstream(&bad_primal, &model);
        for (value, objective) in [(0.5, 0.5), (1e-8, 1.0), (0.5, 1.0), (1e-8, f64::NAN)] {
            let mut bad = good.clone();
            let solution = bad.solution.as_mut().unwrap();
            solution.values[0] = value;
            solution.objective_value = Some(objective);
            assert_upstream(&bad, &model);
        }
        let near = report(&model, vec![1e-8], vec![0.0, 0.0], 1e-8);
        assert!(require_optimal_lp_certificate_for_linear_model(&near, &model).is_ok());
        let error = require_exact_lp(&near, &model).unwrap_err();
        assert_eq!(error.category, "FAILED_PRECONDITION");
        assert!(error.message.contains("对偶间隙非零"));
        for value in [1e-7_f64.next_down(), 1e-7, 1e-7_f64.next_up()] {
            let candidate = report(&model, vec![value], vec![0.0, 0.0], value);
            if require_optimal_lp_certificate_for_linear_model(&candidate, &model).is_ok() {
                assert_eq!(
                    require_exact_lp(&candidate, &model).unwrap_err().category,
                    "FAILED_PRECONDITION"
                );
            } else {
                assert_upstream(&candidate, &model);
            }
        }
        for objective in [
            (1e-8_f64 + 1e-7).next_down(),
            1e-8 + 1e-7,
            (1e-8_f64 + 1e-7).next_up(),
        ] {
            let candidate = report(&model, vec![1e-8], vec![0.0, 0.0], objective);
            if require_optimal_lp_certificate_for_linear_model(&candidate, &model).is_ok() {
                assert_eq!(
                    require_exact_lp(&candidate, &model).unwrap_err().category,
                    "FAILED_PRECONDITION"
                );
            } else {
                assert_upstream(&candidate, &model);
            }
        }

        let mut maximum = model.clone();
        maximum.objective_category = ObjectiveCategory::Maximum;
        let value = 1.0 - 1e-8;
        let near_maximum = report(&maximum, vec![value], vec![0.0, 0.0], value);
        assert!(require_optimal_lp_certificate_for_linear_model(&near_maximum, &maximum).is_ok());
        assert_eq!(
            require_exact_lp(&near_maximum, &maximum)
                .unwrap_err()
                .category,
            "FAILED_PRECONDITION"
        );

        let mut integer_model = model.clone();
        integer_model.basic.var_types[0] = VariableType::Integer;
        let integer_report = report(&integer_model, vec![0.0], vec![0.0, 0.0], 0.0);
        assert_upstream(&integer_report, &integer_model);
        let integer_gap = report(&integer_model, vec![0.5], vec![0.0, 0.0], 0.5);
        assert_upstream(&integer_gap, &integer_model);

        let mut wrong_mapping = good.clone();
        wrong_mapping
            .model_mapping
            .as_mut()
            .unwrap()
            .constraints_by_row
            .swap(0, 1);
        let error = require_exact_lp(&wrong_mapping, &model).unwrap_err();
        assert_eq!(error.category, "FAILED_PRECONDITION");
        assert!(error.message.contains("报告映射与编译模型不一致"));
        let mut missing_mapping = good.clone();
        missing_mapping.model_mapping = None;
        assert_eq!(
            require_exact_lp(&missing_mapping, &model)
                .unwrap_err()
                .category,
            "FAILED_PRECONDITION"
        );
        let mut bad_model = model.clone();
        bad_model.basic.A.rows[0]
            .entries
            .push((model.num_variables(), 1.0));
        assert_upstream(&good, &bad_model);
        bad_model = model.clone();
        bad_model.c[0] = f64::NAN;
        assert_upstream(&good, &bad_model);
    }

    #[test]
    fn exact_gap_preflight_preserves_upstream_float_evaluation_errors() {
        let mut source = MetaModel::<f64>::new("float row overflow");
        let mut variables = Vec::new();
        for name in ["x", "y", "z"] {
            variables.push(
                source
                    .register_auto_variable_with_range::<Continuous>(
                        name,
                        VariableRange::bounded(0.0, 1.0),
                    )
                    .unwrap(),
            );
        }
        source
            .add_le_constraint(
                &[
                    (variables[0], f64::MAX),
                    (variables[1], f64::MAX),
                    (variables[2], -f64::MAX),
                ],
                f64::MAX,
                "row",
            )
            .unwrap();
        source.set_linear_objective_input(
            LinearObjectiveInput::minimize("objective").terms(vec![(variables[0], 1e-8)]),
        );
        let model = source
            .linear_model_snapshot()
            .unwrap()
            .compile_flt64()
            .unwrap()
            .model;
        let candidate = report(&model, vec![1.0, 1.0, 1.0], vec![0.0], 1e-8);
        assert!(evaluate_linear_solution(&model, &[1.0, 1.0, 1.0], 1e-7).is_err());
        let expected = Failure::from(
            require_optimal_lp_certificate_for_linear_model(&candidate, &model).unwrap_err(),
        );
        let actual = require_exact_lp(&candidate, &model).unwrap_err();
        assert_eq!(
            (
                actual.category,
                actual.source,
                actual.error_class,
                actual.message
            ),
            (
                expected.category,
                expected.source,
                expected.error_class,
                expected.message
            )
        );
    }

    #[test]
    fn synthetic_bound_can_contain_three_float_factors() {
        let tiny = f64::from_bits(1);
        let mut model = MetaModel::<f64>::new("three-factor bound");
        let x = model
            .register_auto_variable_with_range::<Continuous>("x", VariableRange::bounded(0.0, tiny))
            .unwrap();
        model.add_le_constraint(&[(x, -tiny)], 0.0, "row").unwrap();
        model.set_linear_objective_input(LinearObjectiveInput::minimize("zero"));
        let compiled = model
            .linear_model_snapshot()
            .unwrap()
            .compile_flt64()
            .unwrap();
        assert_eq!(compiled.model.A.rows[0].entries, vec![(0, -tiny)]);
        assert_eq!(compiled.model.ub[0], tiny);
        assert_eq!(compiled.model.c[0], 0.0);
        let report = report(&compiled.model, vec![0.0], vec![-tiny], 0.0);
        let dual = exact(
            report
                .solution
                .as_ref()
                .unwrap()
                .dual_solution
                .as_ref()
                .unwrap()[0],
        )
        .unwrap();
        let coefficient = exact(compiled.model.A.rows[0].entries[0].1).unwrap();
        let bound = (exact(compiled.model.c[0]).unwrap() - dual * coefficient)
            * exact(compiled.model.ub[0]).unwrap();
        assert_eq!(
            bound,
            -BigRational::new(BigInt::from(1_u8), BigInt::from(1_u8) << 3222)
        );
        assert!(require_optimal_lp_certificate_for_linear_model(&report, &compiled.model).is_ok());
        assert!(
            require_exact_lp(&report, &compiled.model)
                .unwrap_err()
                .message
                .contains("对偶间隙非零")
        );
    }

    #[test]
    fn synthetic_split_row_price_rounding_does_not_issue_certificate() {
        let mut model = MetaModel::<f64>::new("split price rounding");
        model
            .register_auto_variable_with_range::<Continuous>("x", VariableRange::bounded(0.0, 1.0))
            .unwrap();
        model
            .add_linear_constraint(&[], ConstraintRelation::Equal, 0.0, "row")
            .unwrap();
        model.set_linear_objective_input(LinearObjectiveInput::minimize("objective"));
        let snapshot = model.linear_model_snapshot().unwrap();
        let compiled = snapshot.compile_flt64().unwrap();
        let report = report(
            &compiled.model,
            vec![0.0],
            vec![-1.0, -2.0_f64.powi(-54)],
            0.0,
        );
        assert!(require_exact_lp(&report, &compiled.model).is_ok());
        assert!(issue(&snapshot, &compiled, &report, Arc::new(0), 0, false).is_err());
    }

    #[test]
    fn exact_gate_rejects_sub_tolerance_primal_row_and_bound_errors() {
        let mut model = MetaModel::<f64>::new("synthetic primal violations");
        let x = model
            .register_auto_variable_with_range::<Continuous>("x", VariableRange::bounded(0.0, 1.0))
            .unwrap();
        model
            .add_linear_constraint(&[(x, 1.0)], ConstraintRelation::GreaterEqual, 1.0, "demand")
            .unwrap();
        model.set_linear_objective_input(LinearObjectiveInput::minimize("zero"));
        let compiled = model
            .linear_model_snapshot()
            .unwrap()
            .compile_flt64()
            .unwrap();
        let good = report(&compiled.model, vec![1.0], vec![0.0], 0.0);
        assert!(require_exact_lp(&good, &compiled.model).is_ok());
        for value in [1.0 - 2.0_f64.powi(-25), 1.0 + 2.0_f64.powi(-25)] {
            let bad = report(&compiled.model, vec![value], vec![0.0], 0.0);
            assert!(require_optimal_lp_certificate_for_linear_model(&bad, &compiled.model).is_ok());
            assert!(require_exact_lp(&bad, &compiled.model).is_err());
        }
    }

    #[test]
    fn exact_gap_uses_recomputed_objective_not_backend_rounding() {
        let mut model = MetaModel::<f64>::new("rounded objective");
        let x = model
            .register_auto_variable_with_range::<Continuous>("x", VariableRange::bounded(3.0, 3.0))
            .unwrap();
        model.add_le_constraint(&[], 0.0, "row").unwrap();
        model.set_linear_objective_input(
            LinearObjectiveInput::minimize("objective").terms(vec![(x, 0.1)]),
        );
        let compiled = model
            .linear_model_snapshot()
            .unwrap()
            .compile_flt64()
            .unwrap();
        let rounded = 3.0_f64 * 0.1;
        let good = report(&compiled.model, vec![3.0], vec![0.0], rounded);
        assert!(require_exact_lp(&good, &compiled.model).is_ok());
        let one_ulp = report(&compiled.model, vec![3.0], vec![0.0], rounded.next_up());
        assert!(require_exact_lp(&one_ulp, &compiled.model).is_ok());
        let wrong = report(&compiled.model, vec![3.0], vec![0.0], 1.0);
        assert!(require_exact_lp(&wrong, &compiled.model).is_err());
    }

    #[test]
    fn exact_gate_checks_both_directions_and_unbounded_residuals() {
        let mut source = MetaModel::<f64>::new("dual directions");
        let x = source
            .register_auto_variable_with_range::<Continuous>("x", VariableRange::bounded(0.0, 1.0))
            .unwrap();
        source.add_le_constraint(&[(x, 1.0)], 1.0, "row").unwrap();
        source.set_linear_objective_input(
            LinearObjectiveInput::minimize("objective").terms(vec![(x, 1.0)]),
        );
        let mut model = source
            .linear_model_snapshot()
            .unwrap()
            .compile_flt64()
            .unwrap()
            .model;
        let minimum = report(&model, vec![0.0], vec![0.0], 0.0);
        assert!(require_exact_lp(&minimum, &model).is_ok());
        model.lb[0] = f64::NEG_INFINITY;
        let unbounded = report(&model, vec![0.0], vec![0.0], 0.0);
        assert!(require_exact_lp(&unbounded, &model).is_err());

        model.lb[0] = 0.0;
        model.objective_category = ObjectiveCategory::Maximum;
        let maximum = report(&model, vec![1.0], vec![0.0], 1.0);
        assert!(require_exact_lp(&maximum, &model).is_ok());
        let signed = report(&model, vec![1.0], vec![1.0], 1.0);
        assert!(require_exact_lp(&signed, &model).is_ok());
        let wrong_sign = report(&model, vec![1.0], vec![-1.0], 1.0);
        assert!(require_exact_lp(&wrong_sign, &model).is_err());
        model.ub[0] = f64::INFINITY;
        let unbounded_residual = report(&model, vec![1.0], vec![0.0], 1.0);
        assert!(require_exact_lp(&unbounded_residual, &model).is_err());
    }

    #[test]
    fn certificate_uses_pointer_identity_and_checked_generation() {
        let provenance = Arc::new(0);
        let other = Arc::new(0);
        let certificate = DualCertificate {
            provenance: Arc::clone(&provenance),
            generation: u64::MAX,
            prices: Arc::new(BTreeMap::from([("row".to_owned(), 3.0)])),
        };
        assert_eq!(
            certificate.price(&provenance, u64::MAX, "row").unwrap(),
            3.0
        );
        assert_eq!(
            certificate
                .price(&other, u64::MAX, "row")
                .unwrap_err()
                .category,
            "ILLEGAL_ARGUMENT"
        );
        assert_eq!(
            certificate
                .price(&provenance, u64::MAX - 1, "row")
                .unwrap_err()
                .category,
            "FAILED_PRECONDITION"
        );
        assert_eq!(
            certificate
                .price(&provenance, u64::MAX, "missing")
                .unwrap_err()
                .category,
            "NOT_FOUND"
        );
        drop(provenance);
        assert_eq!(
            certificate
                .price(&other, u64::MAX, "row")
                .unwrap_err()
                .category,
            "ILLEGAL_ARGUMENT"
        );
    }

    #[cfg(feature = "scip")]
    #[test]
    fn certificate_requires_the_real_report_mapping_and_complete_source_rows() {
        use ospf_rust_core_plugin_scip::{SCIPConfig, SCIPSolver};

        let mut model = MetaModel::<f64>::new("certificate gate");
        let x = model
            .register_auto_variable_with_range::<Continuous>("x", VariableRange::with_lower(0.0))
            .unwrap();
        model
            .add_linear_constraint(&[(x, 1.0)], ConstraintRelation::Equal, 2.0, "row")
            .unwrap();
        model.set_linear_objective_input(
            LinearObjectiveInput::maximize("objective").terms(vec![(x, 3.0)]),
        );
        let snapshot = model.linear_model_snapshot().unwrap();
        let compiled = snapshot.compile_flt64().unwrap();
        let solver = SCIPSolver::with_config(SCIPConfig {
            output_flag: false,
            ..Default::default()
        });
        let report = solver.solve_linear_report(&compiled.model).unwrap();
        let provenance = Arc::new(0);
        let certificate = issue(
            &snapshot,
            &compiled,
            &report,
            Arc::clone(&provenance),
            7,
            false,
        )
        .unwrap();
        assert_eq!(
            certificate
                .price(&provenance, 7, &snapshot.rows[0].id)
                .unwrap(),
            3.0
        );

        let mut missing = report.clone();
        missing.model_mapping = None;
        assert!(require_optimal_lp_certificate_for_linear_model(&missing, &compiled.model).is_ok());
        assert!(
            issue(
                &snapshot,
                &compiled,
                &missing,
                Arc::clone(&provenance),
                7,
                false
            )
            .is_err()
        );
        let mut wrong = report.clone();
        wrong
            .model_mapping
            .as_mut()
            .unwrap()
            .constraints_by_row
            .swap(0, 1);
        assert!(
            issue(
                &snapshot,
                &compiled,
                &wrong,
                Arc::clone(&provenance),
                7,
                false
            )
            .is_err()
        );
        let mut bad_rows = compiled.clone();
        bad_rows.rows[1].multiplier = 1;
        assert!(
            issue(
                &snapshot,
                &bad_rows,
                &report,
                Arc::clone(&provenance),
                7,
                false
            )
            .is_err()
        );
        bad_rows.rows[1].source = "foreign".into();
        assert!(
            issue(
                &snapshot,
                &bad_rows,
                &report,
                Arc::clone(&provenance),
                7,
                false
            )
            .is_err()
        );
        assert!(issue(&snapshot, &compiled, &report, provenance, 7, true).is_err());
    }
}
