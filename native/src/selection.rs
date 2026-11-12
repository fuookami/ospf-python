//! 上游枚举位置，边界只编排 Python 索引协议。 / Upstream enumerates positions; the boundary schedules Python index protocols only.

use ospf_rust_math::combinatorics::{combinations_of_size, permutations_of_size};
use pyo3::basic::CompareOp;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyFloat, PyInt, PyList, PyTuple};
use std::time::{Duration, Instant};

use crate::failure::{Failure, Transport, transport};

const COOPERATION_STEPS: usize = 256;
const COOPERATION_INTERVAL: Duration = Duration::from_millis(1);

fn overflow() -> Failure {
    Failure::binding(
        "OVERFLOW",
        "选择计划超出原生容量 / Selection plan exceeds native capacity",
    )
}

fn capacity(n: usize, depth: usize, permutations: bool, prefixes: bool) -> Result<usize, Failure> {
    let ceiling = isize::MAX as u128;
    let key_width = PositionEncoding::new(n, depth, prefixes && !permutations).width();
    let sort_bytes = if depth > 1 && (prefixes || permutations) {
        match key_width {
            Some(1..=64) => 2 * std::mem::size_of::<(u64, usize)>(),
            Some(65..=128) => 2 * std::mem::size_of::<(u128, usize)>(),
            _ => 0,
        }
    } else {
        0
    };
    let mut bytes = (n as u128) * std::mem::size_of::<usize>() as u128;
    if bytes > ceiling {
        return Err(overflow());
    }
    let mut count = 1_u128;
    let mut total_rows = 0_u128;
    let steps = if prefixes || permutations {
        depth
    } else {
        depth.min(n - depth)
    };
    for d in 1..=steps {
        count = count
            .checked_mul((n - d + 1) as u128)
            .ok_or_else(overflow)?;
        if !permutations {
            count /= d as u128;
        }
        if count > ceiling {
            return Err(overflow());
        }
        if prefixes {
            total_rows = total_rows.checked_add(count).ok_or_else(overflow)?;
            bytes = bytes
                .checked_add(
                    count
                        * (std::mem::size_of::<Vec<usize>>()
                            + d * std::mem::size_of::<usize>()
                            + sort_bytes) as u128,
                )
                .ok_or_else(overflow)?;
        }
        if bytes > ceiling {
            return Err(overflow());
        }
    }
    if !prefixes {
        bytes = bytes
            .checked_add(
                count
                    .checked_mul(
                        (std::mem::size_of::<Vec<usize>>() as u128)
                            + (depth as u128) * std::mem::size_of::<usize>() as u128
                            + sort_bytes as u128,
                    )
                    .ok_or_else(overflow)?,
            )
            .ok_or_else(overflow)?;
    }
    if bytes > ceiling {
        return Err(overflow());
    }
    usize::try_from(if prefixes {
        total_rows
    } else if depth == 0 {
        0
    } else {
        count
    })
    .map_err(|_| overflow())
}

fn upstream(n: usize, depth: usize, permutations: bool) -> Result<Vec<Vec<usize>>, Failure> {
    let mut positions = Vec::new();
    positions.try_reserve_exact(n).map_err(|_| {
        Failure::binding(
            "APPLICATION_ERROR",
            "无法分配输入位置 / Cannot allocate input positions",
        )
    })?;
    positions.extend(0..n);
    let enumerate = move || {
        // 单位置排列与组合完全相同，复用上游组合以避免逐个建立 QuickPerm 工作区。 / Single-position permutations equal combinations; reuse upstream combinations without per-slot QuickPerm workspaces.
        if permutations && depth != 1 {
            permutations_of_size(&positions, depth)
        } else {
            combinations_of_size(&positions, depth)
        }
    };
    if depth <= 128 {
        return Ok(enumerate());
    }
    // 上游组合递归不能耗尽 Python 所在线程的栈。 / Upstream combination recursion must not exhaust the Python caller's stack.
    let stack = depth
        .checked_mul(8192)
        .filter(|bytes| *bytes <= isize::MAX as usize)
        .ok_or_else(overflow)?;
    std::thread::Builder::new()
        .stack_size(stack.max(2 * 1024 * 1024))
        .spawn(enumerate)
        .map_err(|_| {
            Failure::binding(
                "APPLICATION_ERROR",
                "无法创建枚举工作栈 / Cannot create enumeration worker stack",
            )
        })?
        .join()
        .map_err(|_| {
            Failure::binding(
                "APPLICATION_ERROR",
                "上游枚举失败 / Upstream enumeration failed",
            )
        })
}

fn plan(
    n: usize,
    depth: usize,
    permutations: bool,
    prefixes: bool,
) -> Result<Vec<Vec<usize>>, Failure> {
    let row_count = capacity(n, depth, permutations, prefixes)?;
    let mut result = if prefixes {
        let mut rows = Vec::new();
        rows.try_reserve_exact(row_count).map_err(|_| {
            Failure::binding(
                "APPLICATION_ERROR",
                "无法分配位置计划 / Cannot allocate position plan",
            )
        })?;
        for d in 1..=depth {
            rows.extend(upstream(n, d, permutations)?);
        }
        rows
    } else {
        upstream(n, depth, permutations)?
    };
    if depth > 1 && (prefixes || permutations) {
        order_positions(&mut result, n, depth, prefixes && !permutations);
    }
    Ok(result)
}

fn position_key(row: &[usize], depth: usize, bits: u32) -> u128 {
    let key = row
        .iter()
        .fold(0_u128, |key, index| (key << bits) | (*index as u128 + 1));
    key << ((depth - row.len()) * bits as usize)
}

#[derive(Clone, Copy)]
enum PositionEncoding {
    Digits { depth: usize, bits: u32 },
    Increasing { n: usize },
}

impl PositionEncoding {
    fn new(n: usize, depth: usize, increasing: bool) -> Self {
        let bits = usize::BITS - n.leading_zeros();
        if increasing
            && (1..=64).contains(&n)
            && depth
                .checked_mul(bits as usize)
                .is_none_or(|width| 2 * n < width)
        {
            Self::Increasing { n }
        } else {
            Self::Digits { depth, bits }
        }
    }

    fn width(self) -> Option<usize> {
        match self {
            Self::Digits { depth, bits } => depth.checked_mul(bits as usize),
            Self::Increasing { n } => Some(2 * n),
        }
    }

    fn key(self, row: &[usize]) -> u128 {
        match self {
            Self::Digits { depth, bits } => position_key(row, depth, bits),
            Self::Increasing { n } => {
                // 仅编码已有递增行：00终止、01选择、10跳过；不枚举选择。 / Encode existing increasing rows only: 00 ends, 01 selects, 10 skips; no selection enumeration.
                let skips = (u128::MAX / 3 * 2) >> (128 - 2 * n);
                let suffix = 2 * (n - row[row.len() - 1] - 1);
                let selected = row.iter().fold(0_u128, |mask, index| {
                    mask | (1_u128 << (2 * (n - index - 1)))
                });
                (skips & (u128::MAX << suffix)) - selected
            }
        }
    }
}

fn order_positions(rows: &mut [Vec<usize>], n: usize, depth: usize, increasing: bool) {
    let encoding = PositionEncoding::new(n, depth, increasing);
    let Some(width @ 1..=128) = encoding.width() else {
        rows.sort_unstable();
        return;
    };
    if rows.len() < 64 {
        rows.sort_unstable();
        return;
    }
    // 小键使用真实64位缓冲，避免每趟搬移无效高位。 / Use actual 64-bit buffers for narrow keys, avoiding unused high-word traffic on every pass.
    let ordered = if width <= 64 {
        radix_order(rows, width, |row| encoding.key(row) as u64)
    } else {
        radix_order(rows, width, |row| encoding.key(row))
    };
    if !ordered {
        rows.sort_unstable();
    }
}

fn radix_order<K>(rows: &mut [Vec<usize>], width: usize, key: impl Fn(&[usize]) -> K) -> bool
where
    K: Copy + Default + Into<u128>,
{
    let mut keys = Vec::new();
    let mut scratch = Vec::new();
    if keys.try_reserve_exact(rows.len()).is_err() || scratch.try_reserve_exact(rows.len()).is_err()
    {
        return false;
    }
    keys.extend(
        rows.iter()
            .enumerate()
            .map(|(index, row)| (key(row), index)),
    );
    scratch.resize(keys.len(), (K::default(), 0_usize));
    // 只对带前缀结束符的整数键做稳定字节排序，不生成或去重任何选择行。 / Stable byte sorting only orders terminated integer keys; it never generates or deduplicates selections.
    for byte in 0..width.div_ceil(8) {
        let shift = byte * 8;
        let mut offsets = [0_usize; 256];
        for &(key, _) in &keys {
            offsets[((key.into() >> shift) & 255) as usize] += 1;
        }
        let mut total = 0;
        for count in &mut offsets {
            let length = *count;
            *count = total;
            total += length;
        }
        for &entry in &keys {
            let offset = &mut offsets[((entry.0.into() >> shift) & 255) as usize];
            scratch[*offset] = entry;
            *offset += 1;
        }
        std::mem::swap(&mut keys, &mut scratch);
    }
    // 复用另一缓冲记录旧槽的目标位置，以受检交换原地重排上游行。 / Reuse the other buffer for destinations and reorder upstream rows with checked in-place swaps.
    for (destination, &(_, original)) in keys.iter().enumerate() {
        scratch[original].1 = destination;
    }
    for position in 0..rows.len() {
        while scratch[position].1 != position {
            let destination = scratch[position].1;
            rows.swap(position, destination);
            scratch[position].1 = scratch[destination].1;
            scratch[destination].1 = destination;
        }
    }
    true
}

fn publish_standard<'py>(
    py: Python<'py>,
    rows: &[Vec<usize>],
    output: &Bound<'py, PyList>,
    get: impl Fn(usize) -> PyResult<Bound<'py, PyAny>>,
) -> PyResult<()> {
    let mut checkpoint = Instant::now();
    let mut values = Vec::new();
    for (ordinal, row) in rows.iter().enumerate() {
        if ordinal.is_multiple_of(COOPERATION_STEPS) {
            cooperate(py, &mut checkpoint)?;
        }
        for &index in row {
            values.push(get(index)?);
        }
        // 先读取整行再分配 Python list；drain 转移引用并复用缓冲，不改变 GC 可见的读取次序。 / Read the whole row before allocating its Python list; drain transfers references and reuses storage without changing GC-visible read order.
        output.append(PyList::new(py, values.drain(..))?)?;
    }
    Ok(())
}

fn exact_depth(k: &Bound<'_, PyAny>) -> Option<usize> {
    if k.is_exact_instance_of::<PyInt>() || k.is_exact_instance_of::<PyBool>() {
        k.extract().ok()
    } else if k.is_exact_instance_of::<PyFloat>() {
        let value = k.extract::<f64>().ok()?;
        (value.is_finite()
            && value >= 0.0
            && value < (usize::MAX as u128 + 1) as f64
            && value.fract() == 0.0)
            .then_some(value as usize)
    } else {
        None
    }
}

fn has_other_thread_states(_py: Python<'_>) -> bool {
    // 安全性：Python令牌保证标准CPython的当前线程已附加且持GIL；仅查询其有效状态，不解引用/保留其他线程指针。 / SAFETY: the Python token guarantees an attached current thread holding standard CPython's GIL; only query its valid state, never dereference or retain peer pointers.
    unsafe {
        let current = pyo3::ffi::PyThreadState_Get();
        if current.is_null() {
            return true;
        }
        let interpreter = pyo3::ffi::PyThreadState_GetInterpreter(current);
        if interpreter.is_null() {
            return true;
        }
        pyo3::ffi::PyInterpreterState_ThreadHead(interpreter) != current
            || !pyo3::ffi::PyThreadState_Next(current).is_null()
    }
}

fn cooperate(py: Python<'_>, checkpoint: &mut Instant) -> PyResult<()> {
    // 即刻重新加锁可能饿死等待线程；按时间让出一个调度片，避免小调用每批等待。 / Immediate reacquisition can starve waiters; yield a scheduling interval by elapsed time, not on every small batch.
    if checkpoint.elapsed() >= COOPERATION_INTERVAL {
        // 每次重新观察，不能缓存“单线程”；回调可能刚刚创建低层线程。 / Observe afresh, never cache single-threadedness: a callback may have just created a low-level thread.
        if has_other_thread_states(py) {
            py.detach(|| std::thread::sleep(Duration::from_micros(1)));
        }
        *checkpoint = Instant::now();
    }
    py.check_signals()
}

fn after_subtree(rows: &[Vec<usize>], position: usize, cursor: &mut Vec<usize>) -> usize {
    let following = position + 1;
    let path = &rows[position];
    if rows
        .get(following)
        .is_none_or(|next| !next.starts_with(path))
    {
        return following;
    }
    cursor.clone_from(path);
    cursor.push(usize::MAX);
    following + rows[following..].partition_point(|row| row.as_slice() <= cursor.as_slice())
}

#[pyfunction]
#[pyo3(signature = (*, items, k, permutations))]
pub fn _selection(
    py: Python<'_>,
    items: &Bound<'_, PyAny>,
    k: &Bound<'_, PyAny>,
    permutations: bool,
) -> PyResult<Transport<Py<PyList>>> {
    let output = PyList::empty(py);
    if k.rich_compare(0, CompareOp::Lt)?.is_truthy()? {
        return Ok(transport(Ok(output.unbind())));
    }
    let initial = items.len()?;
    if k.rich_compare(initial, CompareOp::Gt)?.is_truthy()? {
        return Ok(transport(Ok(output.unbind())));
    }
    let used_length = if permutations { items.len()? } else { 0 };
    if PyInt::new(py, 0).as_any().eq(k)? {
        output.append(PyList::empty(py))?;
        return Ok(transport(Ok(output.unbind())));
    }
    let root_length = items.len()?;
    let depth = exact_depth(k);
    let primitive_count = k.is_exact_instance_of::<PyInt>()
        || k.is_exact_instance_of::<PyBool>()
        || k.is_exact_instance_of::<PyFloat>();
    let standard = (items.is_exact_instance_of::<PyList>()
        || items.is_exact_instance_of::<PyTuple>())
        && primitive_count;
    py.check_signals()?;
    if standard {
        let Some(depth) = depth.filter(|depth| *depth <= root_length) else {
            return Ok(transport(Ok(output.unbind())));
        };
        let rows = match py.detach(|| plan(root_length, depth, permutations, false)) {
            Ok(rows) => rows,
            Err(error) => return Ok(transport(Err(error))),
        };
        if let Ok(items) = items.cast::<PyList>() {
            publish_standard(py, &rows, &output, |index| items.get_item(index))?;
        } else {
            let items = items.cast::<PyTuple>()?;
            publish_standard(py, &rows, &output, |index| items.get_item(index))?;
        }
        py.detach(move || drop(rows));
        return Ok(transport(Ok(output.unbind())));
    }

    let mut maximum = root_length;
    let mut rows = match py.detach(|| {
        plan(
            maximum,
            depth.unwrap_or(maximum).min(maximum),
            permutations,
            true,
        )
    }) {
        Ok(rows) => rows,
        Err(error) => return Ok(transport(Err(error))),
    };
    let mut cursor = Vec::new();
    let mut values: Vec<Bound<'_, PyAny>> = Vec::new();
    let mut limits = vec![root_length];
    let mut ordinal = 0_usize;
    let mut next = 0_usize;
    let mut checkpoint = Instant::now();
    while let Some(path) = rows.get(next) {
        if ordinal.is_multiple_of(COOPERATION_STEPS) {
            cooperate(py, &mut checkpoint)?;
        }
        ordinal += 1;
        // 排序后的计划包含每个合法前缀；跳过子树后，下一个父路径仍在活动栈中。 / Sorted plans contain every legal prefix; after subtree skips, the next parent remains on the active stack.
        let parent_depth = path.len() - 1;
        while values.len() > parent_depth {
            values.pop();
        }
        limits.truncate(parent_depth + 1);
        if values.len() != parent_depth || limits.len() != parent_depth + 1 {
            return Ok(transport(Err(Failure::binding(
                "APPLICATION_ERROR",
                "索引协议计划失效 / Indexed protocol plan is invalid",
            ))));
        }
        let index = path[path.len() - 1];
        if index >= limits[parent_depth] {
            next = after_subtree(&rows, next, &mut cursor);
            continue;
        }
        if permutations && index >= used_length {
            return Ok(transport(Err(Failure::input(
                "排列输入长度在读取期间增长 / Permutation input length grew during indexed reads",
            ))));
        }
        values.push(items.get_item(index)?);
        // 精确内置 k 没有比较钩子；子类和外部 k 仍逐前缀执行原始比较。 / Exact builtin counts have no comparison hooks; subclasses and external counts still compare at every prefix.
        let complete = if primitive_count {
            depth == Some(values.len())
        } else {
            PyInt::new(py, values.len()).as_any().eq(k)?
        };
        if complete {
            output.append(PyList::new(py, &values)?)?;
            next = after_subtree(&rows, next, &mut cursor);
        } else {
            let length = items.len()?;
            limits.push(length);
            if length > maximum {
                cursor.clone_from(path);
                maximum = length;
                let replacement = match py.detach(|| {
                    plan(
                        maximum,
                        depth.unwrap_or(maximum).min(maximum),
                        permutations,
                        true,
                    )
                }) {
                    Ok(rows) => rows,
                    Err(error) => return Ok(transport(Err(error))),
                };
                let old = std::mem::replace(&mut rows, replacement);
                py.detach(move || drop(old));
                next = rows.partition_point(|row| row <= &cursor);
            } else {
                // 计划已排序，普通前缀可直接前进；只有跳过子树或增长后才重新定位。 / The plan is sorted; relocate only when skipping a subtree or after growth.
                next += 1;
            }
        }
    }
    while values.pop().is_some() {}
    py.detach(move || drop(rows));
    Ok(transport(Ok(output.unbind())))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn builtin_depth_matches_python_equality_including_noninteger_and_nonfinite_counts() {
        Python::initialize();
        Python::attach(|py| {
            let mut counts = (-1..=7)
                .map(|value| PyInt::new(py, value).into_any())
                .collect::<Vec<_>>();
            counts.extend([
                PyBool::new(py, false).to_owned().into_any(),
                PyBool::new(py, true).to_owned().into_any(),
            ]);
            counts.extend(
                [
                    -1.0,
                    -0.0,
                    0.5,
                    1.0,
                    2.5,
                    3.0,
                    f64::NAN,
                    f64::INFINITY,
                    f64::NEG_INFINITY,
                ]
                .into_iter()
                .map(|value| PyFloat::new(py, value).into_any()),
            );
            for count in counts {
                for length in 0..=8 {
                    assert_eq!(
                        exact_depth(&count) == Some(length),
                        PyInt::new(py, length).as_any().eq(&count).unwrap()
                    );
                }
            }
        });
    }

    #[test]
    fn single_position_plan_matches_both_fixed_upstream_functions() {
        for n in 0..=16 {
            let positions = (0..n).collect::<Vec<_>>();
            let combinations = combinations_of_size(&positions, 1);
            assert_eq!(combinations, permutations_of_size(&positions, 1));
            assert_eq!(upstream(n, 1, false).unwrap(), combinations);
            assert_eq!(upstream(n, 1, true).unwrap(), combinations);
        }
    }

    #[test]
    fn cached_position_order_matches_full_lexicographic_plan() {
        for n in 1..=6 {
            for depth in 1..=n {
                for permutations in [false, true] {
                    for prefixes in [false, true] {
                        let mut rows = if prefixes {
                            (1..=depth)
                                .flat_map(|d| upstream(n, d, permutations).unwrap())
                                .collect::<Vec<_>>()
                        } else {
                            upstream(n, depth, permutations).unwrap()
                        };
                        let mut expected = rows.clone();
                        expected.sort_unstable();
                        order_positions(&mut rows, n, depth, prefixes && !permutations);
                        assert_eq!(rows, expected);
                    }
                }
            }
        }
    }

    #[test]
    fn position_order_handles_key_width_boundaries_and_prefix_terminators() {
        for (n, depth) in [
            (255, 8),
            (16, 15),
            (65535, 8),
            (4096, 1000),
            (1, 128),
            (1, 129),
            (usize::MAX, 2),
        ] {
            let samples = vec![
                vec![n - 1],
                vec![0, 1, 2],
                vec![1],
                vec![0, 1],
                vec![0],
                vec![0, 2],
                vec![0; depth],
            ]
            .into_iter()
            .map(|row| {
                row.into_iter()
                    .take(depth)
                    .map(|index| index % n)
                    .collect::<Vec<_>>()
            })
            .collect::<Vec<_>>();
            // 同时覆盖比较回退、基数排序阈值、重复键和多轮交换。 / Cover comparison fallback, the radix threshold, duplicate keys, and swap cycles.
            for count in [0, 1, 7, 63, 64, 65, 112] {
                for reverse in [false, true] {
                    let mut rows = samples
                        .iter()
                        .cycle()
                        .take(count)
                        .cloned()
                        .collect::<Vec<_>>();
                    if reverse {
                        rows.reverse();
                    }
                    let mut expected = rows.clone();
                    expected.sort_unstable();
                    order_positions(&mut rows, n, depth, false);
                    assert_eq!(rows, expected, "n={n}, depth={depth}, count={count}");
                }
            }
        }
    }

    #[test]
    fn increasing_position_encoding_preserves_prefix_order_at_width_boundaries() {
        assert_eq!(PositionEncoding::new(16, 15, true).width(), Some(32));
        assert_eq!(PositionEncoding::new(16, 15, false).width(), Some(75));
        assert_eq!(PositionEncoding::new(64, 63, true).width(), Some(128));
        assert_eq!(PositionEncoding::new(65, 64, true).width(), Some(448));
        for (n, depth) in [(3, 2), (16, 15), (32, 31), (63, 62), (64, 63), (65, 64)] {
            let samples = [
                vec![n - 1],
                vec![0, n - 1],
                vec![0, 1],
                vec![0],
                vec![n / 2],
                (0..depth).collect::<Vec<_>>(),
                vec![0, 2],
            ];
            for count in [7, 63, 64, 65, 128] {
                let mut rows = samples
                    .iter()
                    .rev()
                    .cycle()
                    .take(count)
                    .cloned()
                    .collect::<Vec<_>>();
                let mut expected = rows.clone();
                expected.sort_unstable();
                order_positions(&mut rows, n, depth, true);
                assert_eq!(rows, expected, "n={n}, depth={depth}, count={count}");
                if let Some(1..=128) = PositionEncoding::new(n, depth, true).width() {
                    let keys = rows
                        .iter()
                        .map(|row| PositionEncoding::new(n, depth, true).key(row))
                        .collect::<Vec<_>>();
                    assert!(keys.windows(2).all(|pair| pair[0] <= pair[1]));
                    assert!(
                        rows.windows(2)
                            .zip(keys.windows(2))
                            .all(|(rows, keys)| (rows[0] == rows[1]) == (keys[0] == keys[1]))
                    );
                }
            }
        }
    }

    #[test]
    fn narrow_and_wide_radix_buffers_reorder_the_same_upstream_rows() {
        let mut rows = plan(6, 3, true, true).unwrap();
        rows.extend_from_within(..16);
        rows.reverse();
        let mut expected = rows.clone();
        expected.sort_unstable();
        let mut narrow = rows.clone();
        let encoding = PositionEncoding::new(6, 3, false);
        let width = encoding.width().unwrap();
        assert!(radix_order(&mut narrow, width, |row| encoding.key(row) as u64));
        assert!(radix_order(&mut rows, width, |row| encoding.key(row)));
        assert_eq!(narrow, expected);
        assert_eq!(rows, expected);
    }

    #[test]
    fn standard_publication_releases_partial_rows_and_reused_buffer_references() {
        Python::initialize();
        Python::attach(|py| {
            let token = PyList::empty(py);
            let sys = py.import("sys").unwrap();
            let references = || {
                sys.call_method1("getrefcount", (&token,))
                    .unwrap()
                    .extract::<usize>()
                    .unwrap()
            };
            let baseline = references();
            let output = PyList::empty(py);
            let result = publish_standard(py, &[vec![0, 0], vec![0, 1]], &output, |index| {
                if index == 1 {
                    Err(pyo3::exceptions::PyIndexError::new_err("indexed failure"))
                } else {
                    Ok(token.clone().into_any())
                }
            });
            assert!(result.is_err());
            assert_eq!(output.len(), 1);
            assert_eq!(references(), baseline + 2);
            drop(output);
            assert_eq!(references(), baseline);
        });
    }

    #[test]
    fn prefix_cursor_skips_only_descendants_in_upstream_sorted_metadata() {
        let rows = plan(3, 2, false, true).unwrap();
        let mut cursor = Vec::new();
        assert_eq!(after_subtree(&rows, 0, &mut cursor), 3);
        assert_eq!(after_subtree(&rows, 1, &mut cursor), 2);
        assert_eq!(after_subtree(&rows, 3, &mut cursor), 5);
        assert_eq!(after_subtree(&rows, 5, &mut cursor), 6);
    }

    #[test]
    fn prefix_depth_stack_retains_the_exact_parent_under_every_subtree_skip_policy() {
        for n in 1_usize..=3 {
            for depth in 1..=n.min(2) {
                for permutations in [false, true] {
                    let rows = plan(n, depth, permutations, true).unwrap();
                    // 每行独立选择继续、getter前拒绝、getter后完成。 / Independently continue, reject before get, or complete after get at every row.
                    for policy in 0..3_usize.pow(rows.len() as u32) {
                        let mut active = Vec::new();
                        let mut cursor = Vec::new();
                        let mut next = 0;
                        while let Some(path) = rows.get(next) {
                            active.truncate(path.len() - 1);
                            assert_eq!(active, path[..path.len() - 1]);
                            let action = policy / 3_usize.pow(next as u32) % 3;
                            if action == 1 {
                                next = after_subtree(&rows, next, &mut cursor);
                            } else {
                                active.push(*path.last().unwrap());
                                next = if action == 2 {
                                    after_subtree(&rows, next, &mut cursor)
                                } else {
                                    next + 1
                                };
                            }
                        }
                    }
                }
            }
        }
    }

    #[test]
    fn positional_metadata_can_be_built_and_released_without_the_gil() {
        Python::initialize();
        Python::attach(|py| {
            let rows = py.detach(|| plan(4, 2, true, true)).unwrap();
            assert_eq!(rows.len(), 16);
            py.detach(move || drop(rows));
            cooperate(py, &mut Instant::now()).unwrap();
        });
    }

    #[test]
    fn elapsed_publication_budget_controls_cooperative_waits() {
        Python::initialize();
        Python::attach(|py| {
            let future = Instant::now() + Duration::from_secs(1);
            let mut checkpoint = future;
            cooperate(py, &mut checkpoint).unwrap();
            assert_eq!(checkpoint, future);
            checkpoint = Instant::now() - Duration::from_secs(1);
            let previous = checkpoint;
            cooperate(py, &mut checkpoint).unwrap();
            assert!(checkpoint > previous);
        });
    }

    #[pyfunction]
    fn observe_peer_thread_states(py: Python<'_>) -> bool {
        has_other_thread_states(py)
    }

    #[test]
    fn elapsed_checkpoints_observe_new_raw_threads_from_both_list_positions() {
        Python::initialize();
        Python::attach(|py| {
            let _initial_observation = has_other_thread_states(py);
            let context = pyo3::types::PyDict::new(py);
            context
                .set_item(
                    "probe",
                    pyo3::wrap_pyfunction!(observe_peer_thread_states, py).unwrap(),
                )
                .unwrap();
            py.run(
                c"import _thread, threading\nstarted=threading.Event()\nstop=threading.Event()\nfinished=threading.Event()\nobserved=[]\ndef worker():\n try:\n  observed.append(probe())\n  started.set()\n  stop.wait()\n finally:\n  finished.set()\n_thread.start_new_thread(worker, ())\nassert started.wait(5)\n",
                Some(&context),
                None,
            )
            .unwrap();
            let parent_saw_peer = has_other_thread_states(py);
            py.run(
                c"stop.set()\nassert finished.wait(5)\nassert observed == [True]\n",
                Some(&context),
                None,
            )
            .unwrap();
            assert!(parent_saw_peer);
        });
    }

    #[test]
    fn selection_capacity_checks_upstream_intermediates_and_prefix_storage() {
        assert!(capacity(5, 3, false, false).is_ok());
        assert!(capacity(5, 5, false, false).is_ok());
        assert!(capacity(5, 3, true, true).is_ok());
        assert!(capacity(usize::MAX, 1, false, false).is_err());
        assert!(capacity(100, 50, false, false).is_err());
        assert!(capacity(30, 30, true, false).is_err());
        assert!(capacity(100, 100, false, true).is_err());
    }

    #[test]
    fn checked_capacity_counts_match_the_fixed_upstream_rows() {
        for n in 0..=6 {
            for depth in 0..=n {
                for permutations in [false, true] {
                    for prefixes in [false, true] {
                        let count = capacity(n, depth, permutations, prefixes).unwrap();
                        let rows = plan(n, depth, permutations, prefixes).unwrap();
                        assert_eq!(count, rows.len());
                    }
                }
            }
        }
        assert_eq!(capacity(16, 15, false, true).unwrap(), 65534);
    }

    #[test]
    fn upstream_prefix_plan_is_positional_depth_first_without_reimplementing_selection() {
        assert_eq!(
            plan(3, 2, false, true).unwrap(),
            vec![
                vec![0],
                vec![0, 1],
                vec![0, 2],
                vec![1],
                vec![1, 2],
                vec![2]
            ]
        );
        assert_eq!(
            plan(3, 2, true, false).unwrap(),
            vec![
                vec![0, 1],
                vec![0, 2],
                vec![1, 0],
                vec![1, 2],
                vec![2, 0],
                vec![2, 1]
            ]
        );
    }
}
