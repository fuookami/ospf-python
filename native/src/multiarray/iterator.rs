//! 活跃游标只持源和访问元数据，不跨调用保存借用或叶快照。 / Live cursors retain source and access metadata, never cross-call borrows or leaf snapshots.

use super::*;
use pyo3::exceptions::PyTypeError;

struct Ownership {
    source: Py<PyAny>,
    owner: Py<PyAny>,
}

struct State {
    ownership: Option<Ownership>,
    position: usize,
}

#[pyclass(frozen, module = "ospf_python._native")]
pub struct MultiArrayIterator {
    access_shape: Shape,
    region: Option<MultiArrayView>,
    state: Mutex<State>,
}

impl MultiArrayIterator {
    fn create(
        source: &Bound<'_, PyAny>,
        owner: &Bound<'_, PyAny>,
        region: Option<&MultiArrayView>,
        column_major: Option<bool>,
    ) -> Result<Self, Failure> {
        let storage = reference_storage(source)?;
        let inner = storage.inner();
        if let Some(region) = region {
            region.check_source(&inner.shape)?;
        }
        {
            let guard = inner
                .value
                .lock()
                .unwrap_or_else(|error| error.into_inner());
            guard.as_ref().ok_or_else(MultiArray::cleared)?;
        }
        let shape = operand_shape(inner, region);
        Ok(Self {
            access_shape: Shape {
                value: DynShape::new_with_order(
                    shape.dims(),
                    order(column_major.unwrap_or_else(|| shape.column_major())),
                ),
            },
            region: region.cloned(),
            state: Mutex::new(State {
                ownership: Some(Ownership {
                    source: source.clone().unbind(),
                    owner: owner.clone().unbind(),
                }),
                position: 0,
            }),
        })
    }

    fn read(
        &self,
        py: Python<'_>,
        source: &Bound<'_, PyAny>,
        position: usize,
    ) -> Result<Py<PyAny>, Failure> {
        let storage = reference_storage(source)?;
        let inner = storage.inner();
        let index = if self.region.is_none()
            && self.access_shape.column_major() == inner.shape.column_major()
        {
            // 物理顺序直接使用上游公开存储索引；其他顺序交给上游坐标映射。 / Physical order uses upstream public storage offsets; other orders use upstream coordinate mapping.
            position
        } else {
            let mut indices = self
                .access_shape
                .value
                .vector_of(position)
                .map_err(index_failure)?;
            if let Some(region) = &self.region {
                for (index, offset) in indices.iter_mut().zip(&region.offsets) {
                    *index += offset;
                }
            }
            inner
                .shape
                .value
                .index_of(&indices)
                .map_err(index_failure)?
        };
        let guard = inner
            .value
            .lock()
            .unwrap_or_else(|error| error.into_inner());
        let value = guard.as_ref().ok_or_else(MultiArray::cleared)?;
        value
            .as_slice()
            .get(index)
            .map(|value| value.clone_ref(py))
            .ok_or_else(|| {
                Failure::binding(
                    "APPLICATION_ERROR",
                    "迭代游标超出存储 / Iterator cursor exceeds storage",
                )
            })
    }

    fn next_value(&self, py: Python<'_>) -> Result<Option<Py<PyAny>>, Failure> {
        let (result, released) = {
            let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
            let Some(ownership) = &state.ownership else {
                return Ok(None);
            };
            let result = self.read(py, ownership.source.bind(py), state.position);
            if result.is_ok() {
                state.position += 1;
            }
            let released = if result.is_err() || state.position == self.access_shape.size() {
                state.ownership.take()
            } else {
                None
            };
            (result.map(Some), released)
        };
        // 先终结游标并解锁，再释放可能析构重入的门面及原生源。 / Finalize and unlock before releasing facades/native sources whose destructors may reenter.
        drop(released);
        result
    }
}

#[pymethods]
impl MultiArrayIterator {
    fn __reduce__(&self) -> PyResult<Py<PyAny>> {
        Err(PyTypeError::new_err(
            "活跃数组游标不支持序列化或深复制；请显式保存快照 / Live array cursors do not support serialization or deep copy; save an explicit snapshot",
        ))
    }

    fn __reduce_ex__(&self, _protocol: &Bound<'_, PyAny>) -> PyResult<Py<PyAny>> {
        self.__reduce__()
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&self, py: Python<'_>) -> PyResult<Option<Py<PyAny>>> {
        self.next_value(py)
            .map_err(|error| PyValueError::new_err(error.message))
    }

    fn __length_hint__(&self) -> usize {
        let state = self.state.lock().unwrap_or_else(|error| error.into_inner());
        if state.ownership.is_none() {
            0
        } else {
            self.access_shape.size() - state.position
        }
    }

    fn advance(&self, py: Python<'_>) -> Transport<(bool, Option<Py<PyAny>>)> {
        transport(self.next_value(py).map(|value| (value.is_some(), value)))
    }

    fn close(&self) {
        self.__clear__();
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        let state = self.state.lock().unwrap_or_else(|error| error.into_inner());
        if let Some(ownership) = &state.ownership {
            visit.call(&ownership.source)?;
            visit.call(&ownership.owner)?;
        }
        Ok(())
    }

    fn __clear__(&self) {
        let ownership = {
            let mut state = self.state.lock().unwrap_or_else(|error| error.into_inner());
            state.ownership.take()
        };
        drop(ownership);
    }
}

#[pyfunction]
#[pyo3(signature = (*, source, owner, column_major=None, region=None))]
pub fn _create_reference_iterator(
    source: &Bound<'_, PyAny>,
    owner: &Bound<'_, PyAny>,
    column_major: Option<bool>,
    region: Option<&MultiArrayView>,
) -> Transport<MultiArrayIterator> {
    transport(MultiArrayIterator::create(
        source,
        owner,
        region,
        column_major,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cleared_sources_fail_once_then_leave_both_iterator_interfaces_exhausted() {
        Python::initialize();
        Python::attach(|py| {
            let source = Py::new(
                py,
                MultiArray::full(
                    Shape::create(vec![2.into()], false).unwrap(),
                    &py.None().into_bound(py),
                )
                .unwrap(),
            )
            .unwrap();
            let make_cursor = || {
                MultiArrayIterator::create(
                    source.bind(py).as_any(),
                    source.bind(py).as_any(),
                    None,
                    None,
                )
                .unwrap()
            };
            let checked = make_cursor();
            let protocol = make_cursor();
            source.borrow(py).__clear__();
            let (_, failure) = checked.advance(py);
            assert_eq!(failure.unwrap().category, "FAILED_PRECONDITION");
            assert_eq!(checked.__length_hint__(), 0);
            assert!(checked.next_value(py).unwrap().is_none());
            assert!(
                protocol
                    .__next__(py)
                    .unwrap_err()
                    .is_instance_of::<PyValueError>(py)
            );
            assert!(protocol.__next__(py).unwrap().is_none());
            assert!(make_cursor_result(py, &source).is_err());
        });
    }

    fn make_cursor_result(
        py: Python<'_>,
        source: &Py<MultiArray>,
    ) -> Result<MultiArrayIterator, Failure> {
        MultiArrayIterator::create(
            source.bind(py).as_any(),
            source.bind(py).as_any(),
            None,
            None,
        )
    }
}
