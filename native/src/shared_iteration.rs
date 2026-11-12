//! 共享外部存储的协议适配，不复制数组或执行 NumPy 数学。 / Protocol adapter for shared external storage, without array copies or NumPy mathematics.

use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::exceptions::{PyRuntimeError, PyStopIteration, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyType;
use std::sync::Mutex;

pub(crate) fn convert_scalar(
    leaf: Bound<'_, PyAny>,
    scalar_type: &Bound<'_, PyType>,
) -> PyResult<Py<PyAny>> {
    if leaf.get_type().is_subclass(scalar_type)? {
        leaf.call_method0(pyo3::intern!(leaf.py(), "item"))
            .map(Bound::unbind)
    } else {
        Ok(leaf.unbind())
    }
}

struct Ownership {
    owner: Py<PyAny>,
    scalar_type: Py<PyType>,
}

struct State {
    ownership: Option<Ownership>,
    position: usize,
    busy: bool,
}

#[pyclass(frozen, module = "ospf_python._native")]
pub struct SharedArrayIterator {
    count: usize,
    state: Mutex<State>,
}

impl SharedArrayIterator {
    fn next_value(&self, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        let (attempt, released) = {
            let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
            if state.busy {
                return Err(Self::busy());
            }
            if state.position == self.count {
                (None, state.ownership.take())
            } else if let Some(ownership) = &state.ownership {
                let attempt = (
                    ownership.owner.clone_ref(py),
                    ownership.scalar_type.clone_ref(py),
                    state.position,
                );
                state.busy = true;
                (Some(attempt), None)
            } else {
                (None, None)
            }
        };
        drop(released);
        let Some((owner, scalar_type, position)) = attempt else {
            return Ok(None);
        };
        // 外部属性、索引及 scalar 协议可能重入/释放 GIL；绝不持游标锁执行。 / External attributes, indexing and scalar protocols may reenter/release the GIL; never run them under the cursor lock.
        let result = (|| {
            let data = owner.bind(py).getattr(pyo3::intern!(py, "_data"))?;
            let leaf = data.get_item(position)?;
            convert_scalar(leaf, scalar_type.bind(py))
        })();
        let released = {
            let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
            state.busy = false;
            if result.is_ok() {
                state.position += 1;
                None
            } else {
                state.ownership.take()
            }
        };
        drop(released);
        result.map(Some).map_err(|error| {
            // 保持原 generator 的 PEP 479，不能把叶/存储抛出的 StopIteration 吞成正常耗尽。 / Preserve the original generator's PEP 479 instead of swallowing leaf/storage StopIteration as exhaustion.
            if error.is_instance_of::<PyStopIteration>(py) {
                let converted = PyRuntimeError::new_err(
                    "生成器内部抛出 StopIteration / generator raised StopIteration",
                );
                converted.set_cause(py, Some(error));
                converted
            } else {
                error
            }
        })
    }

    fn busy() -> PyErr {
        PyValueError::new_err("生成器正在执行 / generator already executing")
    }
}

#[pymethods]
impl SharedArrayIterator {
    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&self, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        self.next_value(py)
    }

    fn send(&self, py: Python<'_>, _value: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        self.next_value(py)?
            .ok_or_else(|| PyStopIteration::new_err(()))
    }

    fn close(&self) -> PyResult<()> {
        let released = {
            let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
            if state.busy {
                return Err(Self::busy());
            }
            state.ownership.take()
        };
        drop(released);
        Ok(())
    }

    fn __reduce__(&self) -> PyResult<Py<PyAny>> {
        Err(PyTypeError::new_err(
            "共享数组游标不支持序列化或深复制 / Shared array cursors do not support serialization or deep copy",
        ))
    }

    fn __reduce_ex__(&self, _protocol: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        self.__reduce__()
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        let state = self.state.lock().unwrap_or_else(|error| error.into_inner());
        if let Some(ownership) = &state.ownership {
            visit.call(&ownership.owner)?;
            visit.call(&ownership.scalar_type)?;
        }
        Ok(())
    }

    fn __clear__(&self) {
        let released = {
            let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
            state.ownership.take()
        };
        drop(released);
    }
}

#[pyfunction]
#[pyo3(signature = (*, owner, scalar_type, count))]
pub fn _iterate_shared_array(
    owner: &Bound<'_, PyAny>,
    scalar_type: &Bound<'_, PyType>,
    count: usize,
) -> SharedArrayIterator {
    SharedArrayIterator {
        count,
        state: Mutex::new(State {
            ownership: Some(Ownership {
                owner: owner.clone().unbind(),
                scalar_type: scalar_type.clone().unbind(),
            }),
            position: 0,
            busy: false,
        }),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pyo3::types::{PyDict, PyFloat, PyList};

    #[test]
    fn shared_storage_replacement_is_live_and_clear_is_terminal() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(
                c"class Source:\n _data = [0, 1]\nsource = Source()",
                Some(&scope),
                None,
            )
            .unwrap();
            let source = scope.get_item("source").unwrap().unwrap();
            let cursor = _iterate_shared_array(&source, &py.get_type::<PyFloat>(), 2);
            assert_eq!(
                cursor
                    .next_value(py)
                    .unwrap()
                    .unwrap()
                    .extract::<i32>(py)
                    .unwrap(),
                0
            );
            source
                .setattr("_data", PyList::new(py, [8, 9]).unwrap())
                .unwrap();
            assert_eq!(
                cursor
                    .next_value(py)
                    .unwrap()
                    .unwrap()
                    .extract::<i32>(py)
                    .unwrap(),
                9
            );
            assert!(cursor.next_value(py).unwrap().is_none());
            cursor.__clear__();
            assert!(cursor.next_value(py).unwrap().is_none());
            let abandoned = _iterate_shared_array(&source, &py.get_type::<PyFloat>(), 2);
            abandoned.__clear__();
            assert!(abandoned.next_value(py).unwrap().is_none());
        });
    }

    #[test]
    fn external_storage_reentry_fails_without_deadlocking_or_advancing() {
        Python::initialize();
        Python::attach(|py| {
            let scope = PyDict::new(py);
            py.run(c"events = []\nclass Source:\n @property\n def _data(self):\n  try:\n   next(cursor)\n  except ValueError:\n   events.append('busy')\n  return [7]\nsource = Source()", Some(&scope), None).unwrap();
            let source = scope.get_item("source").unwrap().unwrap();
            let cursor = Py::new(
                py,
                _iterate_shared_array(&source, &py.get_type::<PyFloat>(), 1),
            )
            .unwrap();
            scope.set_item("cursor", &cursor).unwrap();
            assert_eq!(
                cursor
                    .borrow(py)
                    .next_value(py)
                    .unwrap()
                    .unwrap()
                    .extract::<i32>(py)
                    .unwrap(),
                7
            );
            assert!(cursor.borrow(py).next_value(py).unwrap().is_none());
            assert_eq!(
                scope
                    .get_item("events")
                    .unwrap()
                    .unwrap()
                    .extract::<Vec<String>>()
                    .unwrap(),
                ["busy"]
            );
            scope.clear();
        });
    }
}
