//! 固定上游负责笛卡尔枚举，边界仅快照和发布 Python 槽位。 / Pinned upstream owns Cartesian enumeration; the boundary only snapshots and publishes Python slots.

use ospf_rust_math::combinatorics::{cross_iter, cross2, cross3};
use pyo3::prelude::*;
use pyo3::types::{PyList, PyTuple};

use crate::failure::{Failure, Transport, transport};

fn capacity(mut lengths: impl Iterator<Item = usize>, width: usize) -> Result<usize, Failure> {
    if width > i32::MAX as usize {
        return Err(Failure::binding(
            "OVERFLOW",
            "笛卡尔积维数超出原生容量 / Cartesian product rank exceeds native capacity",
        ));
    }
    let rows = lengths.try_fold(1_usize, |count, len| count.checked_mul(len));
    rows.filter(|count| {
        count.checked_mul(width.max(1)).is_some_and(|slots| {
            slots <= isize::MAX as usize / std::mem::size_of::<usize>()
        })
    })
    .ok_or_else(|| {
        Failure::binding(
            "OVERFLOW",
            "笛卡尔积引用数量超出原生容量 / Cartesian product reference count exceeds native capacity",
        )
    })
}

struct Row<'py> {
    position: usize,
    values: Vec<Bound<'py, PyAny>>,
}

impl<'py> IntoPyObject<'py> for Row<'py> {
    type Target = PyTuple;
    type Output = Bound<'py, PyTuple>;
    type Error = PyErr;

    fn into_pyobject(self, py: Python<'py>) -> PyResult<Self::Output> {
        if self.position.is_multiple_of(4096) {
            py.check_signals()?;
        }
        PyTuple::new(py, self.values)
    }
}

#[pyfunction]
pub fn _cross(py: Python<'_>, inputs: &Bound<'_, PyTuple>) -> PyResult<Transport<Py<PyList>>> {
    let mut pools = Vec::new();
    if pools.try_reserve_exact(inputs.len()).is_err() {
        return Ok(transport(Err(Failure::binding(
            "APPLICATION_ERROR",
            "无法分配笛卡尔输入快照 / Cannot allocate Cartesian input snapshots",
        ))));
    }
    for input in inputs.iter() {
        // 与旧 list(pool) 一致，先从左到右完整消费所有输入，再检查空池。 / Like legacy list(pool), consume every input left-to-right before checking empty pools.
        let snapshot = py
            .get_type::<PyList>()
            .call1((input,))?
            .cast_into::<PyList>()?;
        pools.push(snapshot.iter().collect::<Vec<_>>());
    }
    let output = PyList::empty(py);
    if pools.iter().any(Vec::is_empty) {
        return Ok(transport(Ok(output.unbind())));
    }
    if let Err(error) = capacity(pools.iter().map(Vec::len), pools.len()) {
        return Ok(transport(Err(error)));
    }
    if pools.is_empty() {
        // 上游空输入返回空；公共零元积的单位元是一个空 tuple。 / Upstream empty input is empty; the public nullary-product identity is one empty tuple.
        output.append(PyTuple::empty(py))?;
        return Ok(transport(Ok(output.unbind())));
    }
    py.check_signals()?;
    // 固定小元数直接打包 Rust tuple，避免每行临时 Vec；组合仍只由上游 cross2/cross3 生成。 / Pack small fixed arities as Rust tuples without per-row Vecs; only upstream cross2/cross3 enumerate combinations.
    let packed = match pools.as_slice() {
        [a] => Some(PyList::new(
            py,
            cross2(a, &[()]).into_iter().map(|(a, ())| (a,)),
        )?),
        [a, b] => Some(PyList::new(py, cross2(a, b))?),
        [a, b, c] => Some(PyList::new(py, cross3(a, b, c))?),
        [a, b, c, d] => Some(PyList::new(
            py,
            cross2(&cross2(a, b), &cross2(c, d))
                .into_iter()
                .map(|((a, b), (c, d))| (a, b, c, d)),
        )?),
        [a, b, c, d, e] => Some(PyList::new(
            py,
            cross2(&cross2(a, b), &cross3(c, d, e))
                .into_iter()
                .map(|((a, b), (c, d, e))| (a, b, c, d, e)),
        )?),
        [a, b, c, d, e, f] => Some(PyList::new(
            py,
            cross2(&cross3(a, b, c), &cross3(d, e, f))
                .into_iter()
                .map(|((a, b, c), (d, e, f))| (a, b, c, d, e, f)),
        )?),
        _ => None,
    };
    if let Some(output) = packed {
        py.check_signals()?;
        return Ok(transport(Ok(output.unbind())));
    }
    // 非空且完整受检后，首次 size_hint 的乘积可安全用于一次预分配；不复制上游枚举。 / After checking the nonempty product, its initial size_hint safely preallocates once; never duplicate upstream enumeration.
    let rows = cross_iter(&pools)
        .enumerate()
        .map(|(position, values)| Row { position, values });
    Ok(transport(Ok(PyList::new(py, rows)?.unbind())))
}

#[cfg(test)]
mod tests {
    use super::*;
    use ospf_rust_math::combinatorics::{combinations_of_size, permutations_of_size};

    #[test]
    fn pinned_fixed_size_combinations_keep_positional_lexicographic_order() {
        assert_eq!(
            combinations_of_size(&[0, 1, 2, 3], 2),
            vec![
                vec![0, 1],
                vec![0, 2],
                vec![0, 3],
                vec![1, 2],
                vec![1, 3],
                vec![2, 3]
            ]
        );
        assert!(combinations_of_size(&[0, 1], 3).is_empty());
    }

    #[test]
    fn pinned_partial_permutations_need_explicit_public_order_adaptation() {
        let actual = permutations_of_size(&[0, 1, 2], 2);
        let lexical = vec![
            vec![0, 1],
            vec![0, 2],
            vec![1, 0],
            vec![1, 2],
            vec![2, 0],
            vec![2, 1],
        ];
        assert_eq!(
            actual,
            vec![
                vec![0, 1],
                vec![1, 0],
                vec![0, 2],
                vec![2, 0],
                vec![1, 2],
                vec![2, 1]
            ]
        );
        assert_ne!(actual, lexical);
        let mut sorted = actual;
        sorted.sort_unstable();
        assert_eq!(sorted, lexical);
    }

    #[test]
    fn pinned_zero_length_selection_is_not_the_public_identity() {
        for input in [&[][..], &[0, 1][..]] {
            assert!(combinations_of_size(input, 0).is_empty());
            assert!(permutations_of_size(input, 0).is_empty());
        }
    }

    #[test]
    fn pinned_equal_values_keep_distinct_input_positions() {
        assert_eq!(
            combinations_of_size(&[1, 1, 2], 2),
            vec![vec![1, 1], vec![1, 2], vec![1, 2]]
        );
        assert_eq!(permutations_of_size(&[1, 1, 2], 2).len(), 6);
    }

    #[test]
    fn capacity_checks_products_and_upstream_signed_rank_before_enumeration() {
        assert_eq!(capacity([2, 3].into_iter(), 2).unwrap(), 6);
        assert_eq!(capacity(std::iter::empty(), 0).unwrap(), 1);
        assert!(capacity([usize::MAX, 2].into_iter(), 2).is_err());
        assert!(capacity([isize::MAX as usize].into_iter(), 2).is_err());
        assert!(capacity(std::iter::empty(), i32::MAX as usize + 1).is_err());
    }
}
