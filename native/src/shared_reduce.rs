//! 公共共享存储归约：上游索引遍历，锁外执行 Python 叶与二元协议。 / Public shared-storage reduction using upstream indices and lock-free Python protocols.

use num_bigint::BigInt;
use num_traits::ToPrimitive;
use ospf_rust_multiarray::{Shape, ShapeAccessOrderExt};
use pyo3::prelude::*;
use pyo3::types::PyType;

use crate::failure::{Failure, Transport, transport};
use crate::shared_iteration::convert_scalar;

pub(crate) fn read_value(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    scalar_type: &Bound<'_, PyType>,
    position: usize,
) -> PyResult<Py<PyAny>> {
    // 与旧下标表达式一致，转换叶之前释放临时存储引用。 / Like the old subscript expression, release temporary storage before converting the leaf.
    let leaf = owner
        .getattr(pyo3::intern!(py, "_data"))?
        .get_item(position)?;
    convert_scalar(leaf, scalar_type)
}

#[pyfunction]
#[pyo3(signature = (*, owner, scalar_type, callback))]
pub fn _reduce_shared_array(
    py: Python<'_>,
    owner: &Bound<'_, PyAny>,
    scalar_type: &Bound<'_, PyType>,
    callback: &Bound<'_, PyAny>,
) -> PyResult<Transport<Py<PyAny>>> {
    // 先读首叶，再固定 size；首叶 item/外部属性可改变后续存储与计数。 / Read the first leaf before capturing size; its protocols may change later storage/count.
    let mut accumulated = read_value(py, owner, scalar_type, 0)?;
    let count = owner
        .getattr(pyo3::intern!(py, "size"))?
        .extract::<BigInt>()?;
    if count <= BigInt::from(1) {
        return Ok(transport(Ok(accumulated)));
    }
    let Some(count) = count.to_usize() else {
        return Ok(transport(Err(Failure::binding(
            "OVERFLOW",
            "归约槽位数超出原生索引容量 / Reduction slot count exceeds native index capacity",
        ))));
    };
    // 一维形状表示物理槽位，不重新解释公开多维 shape 或自定义布局。 / A rank-one shape represents physical slots, never reinterpreting public multidimensional/custom layouts.
    let slots = Shape::<1>::new([count]);
    for [position] in slots.indices().skip(1) {
        if position.is_multiple_of(4096) {
            py.check_signals()?;
        }
        let item = read_value(py, owner, scalar_type, position)?;
        // 返回的 None/Result/不透明对象都是数据，不拆包用户回调结果。 / None, Result and opaque callback returns are data, not automatically unwrapped.
        accumulated = callback.call1((accumulated, item))?.unbind();
    }
    Ok(transport(Ok(accumulated)))
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::{PyDict, PyFloat};

    #[test]
    fn fold_reads_live_storage_in_upstream_physical_index_order() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(
                c"events = []\nclass Source:\n size = 3\n _data = [1, 2, 3]\nsource = Source()\ndef callback(left, right):\n events.append(right)\n source._data = [4, 5, 9]\n return left + right",
                Some(&scope),
                None,
            ).unwrap();
            let source = scope.get_item("source").unwrap().unwrap();
            let callback = scope.get_item("callback").unwrap().unwrap();
            let (value, error) =
                _reduce_shared_array(py, &source, &py.get_type::<PyFloat>(), &callback).unwrap();
            assert!(error.is_none());
            assert_eq!(value.unwrap().extract::<i32>(py).unwrap(), 12);
            assert_eq!(
                scope
                    .get_item("events")
                    .unwrap()
                    .unwrap()
                    .extract::<Vec<i32>>()
                    .unwrap(),
                [2, 9]
            );
        });
    }

    #[test]
    fn count_overflow_is_structured_after_initial_leaf_read() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(
                c"class Source:\n size = 1 << 100\n _data = [None]\nsource = Source()",
                Some(&scope),
                None,
            )
            .unwrap();
            let source = scope.get_item("source").unwrap().unwrap();
            let (value, error) =
                _reduce_shared_array(py, &source, &py.get_type::<PyFloat>(), py.None().bind(py))
                    .unwrap();
            assert!(value.is_none());
            assert_eq!(error.unwrap().category, "OVERFLOW");
        });
    }
}
