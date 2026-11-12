//! 外部存储的有界引用收集，不持久镜像或执行数组数学。 / Bounded reference collection from external storage, without persistent mirrors or array mathematics.

use pyo3::exceptions::{PyOverflowError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyList, PyType};

#[pyfunction]
#[pyo3(signature = (*, data, count, offsets=None, scalar_type=None))]
pub fn _read_shared_array(
    py: Python<'_>,
    data: &Bound<'_, PyAny>,
    count: usize,
    offsets: Option<Vec<usize>>,
    scalar_type: Option<&Bound<'_, PyType>>,
) -> PyResult<Py<PyList>> {
    if offsets
        .as_ref()
        .is_some_and(|offsets| offsets.len() != count)
    {
        return Err(PyValueError::new_err(
            "偏移数量与读取数量不符 / Offset count does not match read count",
        ));
    }
    if count > isize::MAX as usize / std::mem::size_of::<usize>() {
        return Err(PyOverflowError::new_err(
            "读取引用数量超出原生容量 / Read reference count exceeds native capacity",
        ));
    }
    if offsets.is_none() && scalar_type.is_none() {
        if data.len()? != count {
            return Err(PyValueError::new_err(
                "完整序列数量与读取数量不符 / Full sequence length does not match read count",
            ));
        }
        // 完整原始导入保留外部序列的原生迭代快路径；不逐槽重新索引或运行 NumPy 数学。 / Preserve the external sequence's native iteration fast path for whole raw imports, without per-slot reindexing or NumPy mathematics.
        let output = py
            .get_type::<PyList>()
            .call1((data,))?
            .cast_into::<PyList>()?;
        if output.len() != count {
            return Err(PyValueError::new_err(
                "收集期间序列数量发生变化 / Sequence length changed during collection",
            ));
        }
        return Ok(output.unbind());
    }
    let output = PyList::empty(py);
    for position in 0..count {
        let offset = offsets
            .as_ref()
            .map_or(position, |offsets| offsets[position]);
        // 索引已由固定 Rust Shape 检查；外部协议无锁执行，成功前不发布部分列表。 / Pinned Rust Shape checks indices; run external protocols without locks and publish no partial list.
        let leaf = data.get_item(offset)?;
        let leaf = if let Some(scalar_type) = scalar_type {
            if leaf.get_type().is_subclass(scalar_type)? {
                leaf.call_method0(pyo3::intern!(py, "item"))?
            } else {
                leaf
            }
        } else {
            leaf
        };
        output.append(leaf)?;
    }
    Ok(output.unbind())
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::exceptions::PyRuntimeError;
    use pyo3::types::PyDict;

    #[test]
    fn selected_reads_keep_order_duplicates_and_raw_identity() {
        Python::initialize();
        Python::attach(|py| {
            let leaf = PyDict::new(py);
            let data = PyList::new(py, [leaf.clone(), leaf.clone()]).unwrap();
            let result =
                _read_shared_array(py, data.as_any(), 3, Some(vec![1, 0, 1]), None).unwrap();
            assert_eq!(result.bind(py).len(), 3);
            for value in result.bind(py).iter() {
                assert!(value.is(&leaf));
            }
            assert!(
                _read_shared_array(py, data.as_any(), 2, Some(vec![0]), None)
                    .unwrap_err()
                    .is_instance_of::<PyValueError>(py)
            );
        });
    }

    #[test]
    fn failure_retains_external_exception_and_releases_partial_output() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(c"import weakref\nerror = RuntimeError('external')\nreferences = []\nclass Leaf: pass\nclass Data:\n def __len__(self): return 2\n def __getitem__(self, index):\n  if index == 1: raise error\n  leaf = Leaf()\n  references.append(weakref.ref(leaf))\n  return leaf\ndata = Data()", Some(&scope), None).unwrap();
            let data = scope.get_item("data").unwrap().unwrap();
            let error = _read_shared_array(py, &data, 2, None, None).unwrap_err();
            assert!(error.is_instance_of::<PyRuntimeError>(py));
            assert!(
                error
                    .value(py)
                    .is(scope.get_item("error").unwrap().unwrap())
            );
            py.run(c"assert references[0]() is None", Some(&scope), None)
                .unwrap();
            scope.clear();
        });
    }
}
