//! 混沌系统单步的私有原生派发，不在此实现任何模型。
//! Private native dispatch for one chaotic step; no model is implemented here.
//!
//! 由 `logs/p3/chaotic-system-binding/gen_binding.py` 依据 `mapping.json` 生成；
//! 参数置换在生成期固化，调用方按公共类的字段顺序传入参数。
//! Generated from `mapping.json`; the parameter permutation is fixed at generation time and
//! callers pass parameters in the public class' own field order.

use pyo3::prelude::*;
use pyo3::types::{PyFloat, PyList, PyTuple};

use crate::failure::{Failure, Transport, transport};

/// 单次调用的最大输入长度，先于逐项检查拒绝异常大的序列。
/// Input ceiling enforced before the per-item scan.
const MAX_INPUTS: usize = 9;

/// 只接受 list/tuple 里的内置 float，不转换 int、bool、NumPy 标量或自定义协议。
/// Accept only builtin floats inside a list or tuple, without coercing other numeric types.
fn floats(argument: &Bound<'_, PyAny>, label: &str) -> PyResult<Result<Vec<f64>, Failure>> {
    let items: Vec<Bound<'_, PyAny>> = if let Ok(list) = argument.cast::<PyList>() {
        list.iter().collect()
    } else if let Ok(tuple) = argument.cast::<PyTuple>() {
        tuple.iter().collect()
    } else {
        return Ok(Err(Failure::input(format!(
            "{label} 必须是 list 或 tuple / {label} must be a list or tuple"
        ))));
    };
    if items.len() > MAX_INPUTS {
        return Ok(Err(Failure::input(format!(
            "{label} 超出长度上限 / {label} exceeds the length limit"
        ))));
    }
    let mut values = Vec::with_capacity(items.len());
    for item in items {
        if !item.is_exact_instance_of::<PyFloat>() {
            return Ok(Err(Failure::input(format!(
                "{label} 仅支持内置 float / Only builtin float values are supported in {label}"
            ))));
        }
        values.push(item.extract::<f64>()?);
    }
    Ok(Ok(values))
}

/// 检查两侧元数后执行一次上游步进。 / Check arities, then take exactly one upstream step.
fn run(
    params: &[f64],
    state: &[f64],
    arity: usize,
    dim: usize,
    step: impl FnOnce(&[f64], &[f64]) -> Vec<f64>,
) -> Result<Vec<f64>, Failure> {
    if params.len() != arity {
        return Err(Failure::input(format!(
            "参数个数应为 {arity} 个 / Expected {arity} parameters, got {}",
            params.len()
        )));
    }
    if state.len() != dim {
        return Err(Failure::input(format!(
            "状态维度应为 {dim} / Expected state dimension {dim}, got {}",
            state.len()
        )));
    }
    Ok(step(params, state))
}

/// 按名称派发到一个固定的上游混沌系统；未知名以结构化失败返回。
/// Dispatch by name to one pinned upstream system; unknown names fail as structured input.
fn step(system: &str, params: &[f64], state: &[f64]) -> Result<Vec<f64>, Failure> {
    match system {
        "BurkeShawAttractor" => run(params, state, 3, 3, |p, s| {
            let next = ospf_rust_math::chaotic::BurkeShawAttractor::<f64>::new(p[0], p[1], p[2])
                .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "ChenCelikovskyAttractor" => run(params, state, 4, 3, |p, s| {
            let next = ospf_rust_math::chaotic::ChenCelikovskyAttractor::<f64>::new(
                p[0], p[1], p[2], p[3],
            )
            .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "ChenLeeAttractor" => run(params, state, 4, 3, |p, s| {
            let next =
                ospf_rust_math::chaotic::ChenLeeAttractor::<f64>::new(p[0], p[1], p[2], p[3])
                    .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "ChenSystem" => run(params, state, 4, 3, |p, s| {
            let next = ospf_rust_math::chaotic::ChenSystem::<f64>::new(p[0], p[1], p[2], p[3])
                .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "ChuaCircuit" => run(params, state, 5, 3, |p, s| {
            let next =
                ospf_rust_math::chaotic::ChuaCircuit::<f64>::new(p[0], p[1], p[3], p[2], p[4])
                    .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "DequanLiAttractor" => run(params, state, 7, 3, |p, s| {
            let next = ospf_rust_math::chaotic::DequanLiAttractor::<f64>::new(
                p[0], p[4], p[1], p[5], p[3], p[2], p[6],
            )
            .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "DuffingEquation" => run(params, state, 6, 3, |p, s| {
            let next = ospf_rust_math::chaotic::DuffingEquation::<f64>::new(
                p[1], p[2], p[0], p[3], p[4], p[5],
            )
            .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "DuffingMap" => run(params, state, 2, 2, |p, s| {
            let next = ospf_rust_math::chaotic::DuffingMap::<f64>::new(p[0], p[1])
                .step(ospf_rust_math::geometry::Point2::new(s[0], s[1]));
            vec![next.x(), next.y()]
        }),
        "FinanceAttractor" => run(params, state, 4, 3, |p, s| {
            let next =
                ospf_rust_math::chaotic::FinanceAttractor::<f64>::new(p[0], p[1], p[2], p[3])
                    .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "HalvorsenAttractor" => run(params, state, 2, 3, |p, s| {
            let next = ospf_rust_math::chaotic::HalvorsenAttractor::<f64>::new(p[0], p[1])
                .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "HenonMap" => run(params, state, 2, 2, |p, s| {
            let next = ospf_rust_math::chaotic::HenonMap::<f64>::new(p[0], p[1])
                .step(ospf_rust_math::geometry::Point2::new(s[0], s[1]));
            vec![next.x(), next.y()]
        }),
        "Lorenz84Model" => run(params, state, 5, 3, |p, s| {
            let next =
                ospf_rust_math::chaotic::Lorenz84Model::<f64>::new(p[0], p[1], p[2], p[3], p[4])
                    .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "LorenzStenfloAttractor" => run(params, state, 5, 4, |p, s| {
            let next = ospf_rust_math::chaotic::LorenzStenfloAttractor::<f64>::new(
                p[0], p[1], p[3], p[2], p[4],
            )
            .step(ospf_rust_math::geometry::Point4::new(
                s[0], s[1], s[2], s[3],
            ));
            vec![next.x(), next.y(), next.z(), next.w()]
        }),
        "LotkaVolterraSystem" => run(params, state, 5, 2, |p, s| {
            let next = ospf_rust_math::chaotic::LotkaVolterraSystem::<f64>::new(
                p[0], p[1], p[2], p[3], p[4],
            )
            .step(ospf_rust_math::geometry::Point2::new(s[0], s[1]));
            vec![next.x(), next.y()]
        }),
        "NewtonLeipnikAttractor" => run(params, state, 3, 3, |p, s| {
            let next =
                ospf_rust_math::chaotic::NewtonLeipnikAttractor::<f64>::new(p[0], p[1], p[2])
                    .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "RabinovichFabrikantEquation" => run(params, state, 3, 3, |p, s| {
            let next =
                ospf_rust_math::chaotic::RabinovichFabrikantEquation::<f64>::new(p[0], p[1], p[2])
                    .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "RosslerAttractor" => run(params, state, 4, 3, |p, s| {
            let next =
                ospf_rust_math::chaotic::RosslerAttractor::<f64>::new(p[0], p[1], p[2], p[3])
                    .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "RucklidgeAttractor" => run(params, state, 3, 3, |p, s| {
            let next = ospf_rust_math::chaotic::RucklidgeAttractor::<f64>::new(p[1], p[0], p[2])
                .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "SakaryaAttractor" => run(params, state, 3, 3, |p, s| {
            let next = ospf_rust_math::chaotic::SakaryaAttractor::<f64>::new(p[0], p[1], p[2])
                .step(ospf_rust_math::geometry::Point3::new(s[0], s[1], s[2]));
            vec![next.x(), next.y(), next.z()]
        }),
        "TinkerbellMap" => run(params, state, 4, 2, |p, s| {
            let next = ospf_rust_math::chaotic::TinkerbellMap::<f64>::new(p[0], p[1], p[2], p[3])
                .step(ospf_rust_math::geometry::Point2::new(s[0], s[1]));
            vec![next.x(), next.y()]
        }),
        _ => Err(Failure::input("未知的混沌系统 / Unknown chaotic system")),
    }
}

/// 单步一个混沌系统：`(system, params, state)` 全为关键字参数。
/// Step one chaotic system; every argument is keyword-only.
#[pyfunction]
#[pyo3(signature = (*, system, params, state))]
pub(crate) fn _chaotic_system_step(
    py: Python<'_>,
    system: String,
    params: &Bound<'_, PyAny>,
    state: &Bound<'_, PyAny>,
) -> PyResult<Transport<Vec<f64>>> {
    let params = match floats(params, "params")? {
        Ok(values) => values,
        Err(failure) => return Ok(transport(Err(failure))),
    };
    let state = match floats(state, "state")? {
        Ok(values) => values,
        Err(failure) => return Ok(transport(Err(failure))),
    };
    py.check_signals()?;
    let result = py.detach(|| step(&system, &params, &state));
    py.check_signals()?;
    Ok(transport(result))
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 冻结的刷入位模式：出厂默认参数与两个状态，来自固定 revision 的 release 探针。
    /// Frozen probe bits at the shipped defaults for two states, release build, pinned rev.
    #[test]
    fn frozen_steps_keep_their_bit_patterns() {
        // BurkeShawAttractor @ defaults [10.0, 4.272, 0.001]
        assert_eq!(
            step(
                "BurkeShawAttractor",
                &[10.0, 4.272, 0.001],
                &[0.7, 1.3, 2.1]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3fe5c28f5c28f5c2, 0x3ff48b4395810625, 0x4000e82f944241c4]
        );

        // ChenCelikovskyAttractor @ defaults [36.0, 3.0, 20.0, 0.001]
        assert_eq!(
            step(
                "ChenCelikovskyAttractor",
                &[36.0, 3.0, 20.0, 0.001],
                &[0.7, 1.3, 2.1]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3fe71758e219652b, 0x3ff531465e892253, 0x4000c1c2e33eff1a]
        );

        // ChenLeeAttractor @ defaults [5.0, -10.0, -0.38, 0.001]
        assert_eq!(
            step(
                "ChenLeeAttractor",
                &[5.0, -10.0, -0.38, 0.001],
                &[0.7, 1.3, 2.1]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3fe66cb5350092cd, 0x3ff49d92b7fe08af, 0x4000cbc973c38dd1]
        );

        // ChenSystem @ defaults [35.0, 3.0, 28.0, 0.001]
        assert_eq!(
            step("ChenSystem", &[35.0, 3.0, 28.0, 0.001], &[0.7, 1.3, 2.1])
                .unwrap()
                .into_iter()
                .map(f64::to_bits)
                .collect::<Vec<u64>>(),
            vec![0x3fe7126e978d4fdf, 0x3ff547cd898b2e9d, 0x4000c1c2e33eff1a]
        );

        // ChuaCircuit @ defaults [9.0, 14.286, -1.27, -0.68, 0.01]
        assert_eq!(
            step(
                "ChuaCircuit",
                &[9.0, 14.286, -1.27, -0.68, 0.01],
                &[0.7, 1.3, 2.1]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3feab035bd512ec6, 0x3ff50a3d70a3d70a, 0x3ffea0e6299524c0]
        );

        // DequanLiAttractor @ defaults [40.0, 0.16, 55.0, 20.0, 11.0, 0.46, 0.0001]
        assert_eq!(
            step(
                "DequanLiAttractor",
                &[40.0, 0.16, 55.0, 20.0, 11.0, 0.46, 0.0001],
                &[0.7, 1.3, 2.1],
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3fe67a40e3caeb20, 0x3ff4e69df97aaac1, 0x4000d1abcc4c1e67]
        );

        // DuffingEquation @ defaults [0.3, -1.0, 1.0, 0.37, 1.2, 0.01]
        assert_eq!(
            step(
                "DuffingEquation",
                &[0.3, -1.0, 1.0, 0.37, 1.2, 0.01],
                &[0.7, 1.3, 2.1]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3fe6d0e560418937, 0x3ff4bf20bc0aa74e, 0x4000e147ae147ae1]
        );

        // DuffingMap @ defaults [2.75, 0.2]
        assert_eq!(
            step("DuffingMap", &[2.75, 0.2], &[0.7, 1.3])
                .unwrap()
                .into_iter()
                .map(f64::to_bits)
                .collect::<Vec<u64>>(),
            vec![0x3ff4cccccccccccd, 0x3ff3ced916872b00]
        );

        // FinanceAttractor @ defaults [0.001, 0.2, 1.1, 0.01]
        assert_eq!(
            step(
                "FinanceAttractor",
                &[0.001, 0.2, 1.1, 0.01],
                &[0.7, 1.3, 2.1]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3fe87ba450acc0bd, 0x3ff4ae147ae147ae, 0x40008f27bb2fec57]
        );

        // HalvorsenAttractor @ defaults [1.89, 0.001]
        assert_eq!(
            step("HalvorsenAttractor", &[1.89, 0.001], &[0.7, 1.3, 2.1])
                .unwrap()
                .into_iter()
                .map(f64::to_bits)
                .collect::<Vec<u64>>(),
            vec![0x3fe5de4e69f05ea2, 0x3ff482cc2d6a9c56, 0x4000b348b220791c]
        );

        // HenonMap @ defaults [1.4, 0.3]
        assert_eq!(
            step("HenonMap", &[1.4, 0.3], &[0.7, 1.3])
                .unwrap()
                .into_iter()
                .map(f64::to_bits)
                .collect::<Vec<u64>>(),
            vec![0x3ff9d2f1a9fbe76e, 0x3fcae147ae147ae1]
        );

        // Lorenz84Model @ defaults [0.25, 4.0, 8.0, 1.25, 0.01]
        assert_eq!(
            step(
                "Lorenz84Model",
                &[0.25, 4.0, 8.0, 1.25, 0.01],
                &[0.7, 1.3, 2.1]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3fe5083126e978d5, 0x3ff3ff2e48e8a71e, 0x40010a71de69ad43]
        );

        // LorenzStenfloAttractor @ defaults [1.0, 0.7, 26.0, 1.5, 0.005]
        assert_eq!(
            step(
                "LorenzStenfloAttractor",
                &[1.0, 0.7, 26.0, 1.5, 0.005],
                &[0.7, 1.3, 2.1, 3.5]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![
                0x3fe75604189374bc,
                0x3ff608ce703afb7f,
                0x4000c710cb295e9e,
                0x400bd4fdf3b645a2
            ]
        );

        // LotkaVolterraSystem @ defaults [1.0, 0.1, 1.5, 0.075, 0.01]
        assert_eq!(
            step(
                "LotkaVolterraSystem",
                &[1.0, 0.1, 1.5, 0.075, 0.01],
                &[0.7, 1.3]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3fe6984a0e410b63, 0x3ff47fb9389b5201]
        );

        // NewtonLeipnikAttractor @ defaults [0.4, 0.175, 0.005]
        assert_eq!(
            step(
                "NewtonLeipnikAttractor",
                &[0.4, 0.175, 0.005],
                &[0.7, 1.3, 2.1]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3feaee631f8a0902, 0x3ff54a57a786c227, 0x4000a1f8a0902de0]
        );

        // RabinovichFabrikantEquation @ defaults [1.1, 0.87, 0.001]
        assert_eq!(
            step(
                "RabinovichFabrikantEquation",
                &[1.1, 0.87, 0.001],
                &[0.7, 1.3, 2.1]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3fe67c5260f5e41d, 0x3ff4e4f54d1e96c4, 0x4000bb82c2bd7f52]
        );

        // RosslerAttractor @ defaults [0.2, 0.2, 5.7, 0.005]
        assert_eq!(
            step(
                "RosslerAttractor",
                &[0.2, 0.2, 5.7, 0.005],
                &[0.7, 1.3, 2.1]
            )
            .unwrap()
            .into_iter()
            .map(f64::to_bits)
            .collect::<Vec<u64>>(),
            vec![0x3fe5db22d0e56041, 0x3ff4e075f6fd21ff, 0x40006353f7ced917]
        );

        // RucklidgeAttractor @ defaults [2.0, 6.7, 0.005]
        assert_eq!(
            step("RucklidgeAttractor", &[2.0, 6.7, 0.005], &[0.7, 1.3, 2.1])
                .unwrap()
                .into_iter()
                .map(f64::to_bits)
                .collect::<Vec<u64>>(),
            vec![0x3fe721ff2e48e8a7, 0x3ff4db22d0e56042, 0x4000c89a02752546]
        );

        // SakaryaAttractor @ defaults [0.4, 0.2, 0.005]
        assert_eq!(
            step("SakaryaAttractor", &[0.4, 0.2, 0.005], &[0.7, 1.3, 2.1])
                .unwrap()
                .into_iter()
                .map(f64::to_bits)
                .collect::<Vec<u64>>(),
            vec![0x3fe6eecbfb15b574, 0x3ff4afe1da7b0b39, 0x4000e070b8cfbfc7]
        );

        // TinkerbellMap @ defaults [0.9, -0.6013, 2.0, 0.5]
        assert_eq!(
            step("TinkerbellMap", &[0.9, -0.6013, 2.0, 0.5], &[0.7, 1.3])
                .unwrap()
                .into_iter()
                .map(f64::to_bits)
                .collect::<Vec<u64>>(),
            vec![0xbff5a085b18548aa, 0x400ef5c28f5c28f5]
        );
    }

    #[test]
    fn unknown_system_and_arity_rejections_are_structured() {
        assert_eq!(
            step("NoSuchSystem", &[0.2], &[0.7, 1.3])
                .unwrap_err()
                .category,
            "ILLEGAL_ARGUMENT"
        );
        assert!(step("RosslerAttractor", &[0.2, 0.2, 5.7], &[0.7, 1.3, 2.1]).is_err());
        assert!(step("RosslerAttractor", &[0.2, 0.2, 5.7, 0.005], &[0.7, 1.3]).is_err());
    }
}
