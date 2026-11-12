//! 公共共享映射：上游物理索引与 Python list 扩展协议。 / Public shared mapping via upstream physical indices and Python list extension.

use num_bigint::BigInt;
use num_traits::ToPrimitive;
use ospf_rust_multiarray::{Shape, ShapeAccessOrderExt};
use pyo3::prelude::*;
use pyo3::types::{PyList, PyType};

use crate::failure::{Failure, Transport, transport};
use crate::shared_reduce::read_value;

#[pyfunction]
#[pyo3(signature = (*, owner, scalar_type, callback, flat))]
pub fn _map_shared_array(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    scalar_type: &Bound<'_, PyType>,
    callback: &Bound<'_, PyAny>,
    flat: bool,
) -> PyResult<Transport<Py<PyList>>> {
    // 与 range 一致，任何叶协议之前固定整数计数，非正计数为空。 / Like range, capture integer count before any leaf protocol; nonpositive counts are empty.
    let count = owner
        .getattr(pyo3::intern!(py, "size"))?
        .extract::<BigInt>()?;
    let output = PyList::empty(py);
    if count <= BigInt::from(0) {
        return Ok(transport(Ok(output.unbind())));
    }
    let Some(count) = count.to_usize() else {
        return Ok(transport(Err(Failure::binding(
            "OVERFLOW",
            "映射槽位数超出原生索引容量 / Mapping slot count exceeds native index capacity",
        ))));
    };
    let slots = Shape::<1>::new([count]);
    for [position] in slots.indices() {
        if position.is_multiple_of(4096) {
            py.check_signals()?;
        }
        let item = read_value(py, owner, scalar_type, position)?;
        let mapped = callback.call1((item,))?;
        if flat {
            // 使用真正 list.extend，完整保留 iterable/length_hint/next 协议。 / Use actual list.extend, preserving iterable/length_hint/next protocols.
            output.call_method1(pyo3::intern!(py, "extend"), (mapped,))?;
        } else {
            // 始终保持可被重入 Python/GC 观察的列表有效，不发布未初始化槽位。 / Keep the list valid for reentrant Python/GC; never expose uninitialized slots.
            output.append(mapped)?;
        }
    }
    Ok(transport(Ok(output.unbind())))
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::{PyDict, PyFloat};

    #[test]
    fn mapping_captures_count_but_reads_live_storage() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(c"class Source:\n size = 3\n _data = [1, 2, 3]\nsource = Source()\ndef callback(value):\n source.size = 1\n source._data = [4, 5, 6]\n return value * 2", Some(&scope), None).unwrap();
            let source = scope.get_item("source").unwrap().unwrap();
            let callback = scope.get_item("callback").unwrap().unwrap();
            for (flat, name) in [(false, "callback"), (true, "flat_callback")] {
                source.setattr("_data", vec![1, 2, 3]).unwrap();
                source.setattr("size", 3).unwrap();
                scope.set_item("callback", &callback).unwrap();
                py.run(
                    c"def flat_callback(value):\n yield callback(value)\n yield None",
                    Some(&scope),
                    None,
                )
                .unwrap();
                let (value, failure) = _map_shared_array(
                    py,
                    &source,
                    &py.get_type::<PyFloat>(),
                    &scope.get_item(name).unwrap().unwrap(),
                    flat,
                )
                .unwrap();
                assert!(failure.is_none());
                let expected = if flat {
                    vec![Some(2), None, Some(10), None, Some(12), None]
                } else {
                    vec![Some(2), Some(10), Some(12)]
                };
                assert_eq!(
                    value.unwrap().extract::<Vec<Option<i32>>>(py).unwrap(),
                    expected
                );
            }
        });
    }
}
