//! 整数 DTO 的临时计算边界及外部数值协议。 / Temporary integer DTO arithmetic and external numeric protocols.

use num_bigint::{BigInt, Sign};
use num_traits::{One, Signed, Zero};
use ospf_rust_math::operator::{AddRef, DivRef, MulRef, NegRef, SubRef};
use pyo3::class::basic::CompareOp;
use pyo3::class::gc::{PyTraverseError, PyVisit};
use pyo3::prelude::*;
use pyo3::types::{PyCFunction, PyDict, PyInt, PyString};
use std::cmp::Ordering;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum IntegerRange {
    Below,
    Small(i64),
    Above,
}

pub(crate) fn integer_range(value: &Bound<'_, PyAny>) -> PyResult<IntegerRange> {
    debug_assert!(value.is_exact_instance_of::<PyInt>());
    let mut overflow = 0;
    // SAFETY: 调用方只传 exact int，持有 GIL 和活引用；溢出标记不截断原值，也不调用 __index__。
    // Callers supply exact ints with the GIL and a live reference; overflow classification never truncates the value or invokes __index__.
    let small = unsafe { pyo3::ffi::PyLong_AsLongLongAndOverflow(value.as_ptr(), &mut overflow) };
    if small == -1 && overflow == 0 && PyErr::occurred(value.py()) {
        return Err(PyErr::fetch(value.py()));
    }
    Ok(match overflow.cmp(&0) {
        Ordering::Less => IntegerRange::Below,
        Ordering::Equal => IntegerRange::Small(small),
        Ordering::Greater => IntegerRange::Above,
    })
}

fn big_integer(value: &Bound<'_, PyAny>, range: IntegerRange) -> PyResult<BigInt> {
    match range {
        IntegerRange::Small(value) => Ok(BigInt::from(value)),
        _ => value.extract(),
    }
}

fn integer_object<'py>(py: Python<'py>, value: &BigInt) -> PyResult<Bound<'py, PyAny>> {
    let (sign, mut words) = value.to_u64_digits();
    // 为零值或最高有效位补足符号字；只编码临时二进制出口，不保存第二份整数值。
    // Supply a sign word for zero or a set high bit; encode only a temporary binary output, never a persistent integer mirror.
    if words.last().is_none_or(|last| last >> (u64::BITS - 1) != 0) {
        words.push(0);
    }
    if sign == Sign::Minus {
        let mut carry = true;
        for word in &mut words {
            (*word, carry) = (!*word).overflowing_add(u64::from(carry));
        }
    }
    for word in &mut words {
        *word = word.to_le();
    }
    // SAFETY: 缓冲已完整初始化为小端二补码；公开 C API 仅在持有 GIL 的调用内读取并返回拥有引用。
    // The fully initialized buffer contains little-endian two's complement; the public C API reads it during this GIL-held call and returns an owned reference.
    unsafe {
        Bound::from_owned_ptr_or_err(
            py,
            pyo3::ffi::PyLong_FromNativeBytes(
                words.as_ptr().cast(),
                std::mem::size_of_val(words.as_slice()),
                pyo3::ffi::Py_ASNATIVEBYTES_LITTLE_ENDIAN,
            ),
        )
    }
}

fn compare_integers(left: &Bound<'_, PyAny>, right: &Bound<'_, PyAny>) -> PyResult<Ordering> {
    if left.is(right) {
        return Ok(Ordering::Equal);
    }
    match (integer_range(left)?, integer_range(right)?) {
        (IntegerRange::Small(left), IntegerRange::Small(right)) => Ok(left.cmp(&right)),
        (IntegerRange::Below, IntegerRange::Below) | (IntegerRange::Above, IntegerRange::Above) => {
            let py = left.py();
            let left = left.extract::<BigInt>()?;
            let right = right.extract::<BigInt>()?;
            Ok(py.detach(move || left.cmp(&right)))
        }
        (IntegerRange::Below, _) | (_, IntegerRange::Above) => Ok(Ordering::Less),
        _ => Ok(Ordering::Greater),
    }
}

fn small_binary(left: i64, right: i64, operation: &str) -> Option<i64> {
    // checked 仅证明原生窄域不会溢出；结果仍由固定 OSPF traits 计算，越界回到任意精度域。
    // checked operations only prove native-range safety; pinned OSPF traits compute the result, with arbitrary precision outside that range.
    match operation {
        "add" if left.checked_add(right).is_some() => Some(i64::add_ref(&left, &right)),
        "subtract" if left.checked_sub(right).is_some() => Some(i64::sub_ref(&left, &right)),
        "multiply" if left.checked_mul(right).is_some() => Some(i64::mul_ref(&left, &right)),
        "floor-divide" if left.checked_div(right).is_some() => {
            let quotient = i64::div_ref(&left, &right);
            Some(
                if left.is_negative() != right.is_negative()
                    && left
                        .checked_rem(right)
                        .is_some_and(|remainder| remainder != 0)
                {
                    i64::sub_ref(&quotient, &1)
                } else {
                    quotient
                },
            )
        }
        _ => None,
    }
}

fn floor_quotient(left: &BigInt, right: &BigInt) -> BigInt {
    let quotient = BigInt::div_ref(left, right);
    // 只适配向零商与 Python floor 的差异，不复制除法内核。 / Adapt truncation to Python floor without duplicating division.
    if left.is_negative() != right.is_negative() && BigInt::mul_ref(&quotient, right) != *left {
        BigInt::sub_ref(&quotient, &BigInt::one())
    } else {
        quotient
    }
}

fn builtin(py: Python<'_>, name: &str) -> PyResult<Option<Py<PyAny>>> {
    let value = match py.import("builtins")?.getattr(name) {
        Ok(value) => value,
        Err(error) if error.is_instance_of::<pyo3::exceptions::PyAttributeError>(py) => {
            return Ok(None);
        }
        Err(error) => return Err(error),
    };
    // 导入前已经替换的 Python 钩子也不能获得内置函数的快速路径。 / Python hooks replaced before import must not gain the builtin fast path.
    Ok((value.is_instance_of::<PyCFunction>()
        && value.getattr("__name__")?.extract::<String>()? == name
        && value.getattr("__module__")?.extract::<String>()? == "builtins")
        .then(|| value.unbind()))
}

/// 仅持有内置 callable 身份，不保存用户值或算术缓存。 / Retain builtin callable identities only, never user values or arithmetic caches.
#[pyclass(module = "ospf_python._native", name = "_IntegerOps")]
pub struct IntegerOps {
    minimum: Option<Py<PyAny>>,
    maximum: Option<Py<PyAny>>,
}

impl IntegerOps {
    pub fn create(py: Python<'_>) -> PyResult<Self> {
        Ok(Self {
            minimum: builtin(py, "min")?,
            maximum: builtin(py, "max")?,
        })
    }

    fn is_builtin(&self, callable: &Bound<'_, PyAny>, minimum: bool) -> bool {
        let expected = if minimum {
            &self.minimum
        } else {
            &self.maximum
        };
        expected
            .as_ref()
            .is_some_and(|value| callable.is(value.bind(callable.py())))
    }

    pub(crate) fn is_or_current_builtin(
        &self,
        callable: &Bound<'_, PyAny>,
        minimum: bool,
    ) -> PyResult<bool> {
        if self.is_builtin(callable, minimum) {
            return Ok(true);
        }
        let cached = if minimum {
            &self.minimum
        } else {
            &self.maximum
        };
        if cached.is_some() {
            return Ok(false);
        }
        Ok(builtin(callable.py(), if minimum { "min" } else { "max" })?
            .is_some_and(|value| callable.is(value.bind(callable.py()))))
    }
}

#[pymethods]
impl IntegerOps {
    #[pyo3(signature = (*, reference, domain))]
    fn facade(
        &self,
        py: Python<'_>,
        reference: Bound<'_, PyAny>,
        domain: &str,
    ) -> PyResult<IntegerFacade> {
        let domain = match domain {
            "integer" => IntegerDomain::Signed,
            "uinteger" => IntegerDomain::Unsigned,
            "numeric_integer" => IntegerDomain::Bounded,
            "numeric_u_integer" => IntegerDomain::StrictUnsigned,
            _ => {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "无效内部整数门面 / Invalid internal integer facade",
                ));
            }
        };
        Ok(IntegerFacade {
            domain,
            namespace: Some(
                reference
                    .getattr("__globals__")?
                    .cast_into::<PyDict>()?
                    .unbind(),
            ),
            builtins: Some(
                reference
                    .getattr("__builtins__")?
                    .cast_into::<PyDict>()?
                    .unbind(),
            ),
            ops: IntegerOps {
                minimum: self.minimum.as_ref().map(|v| v.clone_ref(py)),
                maximum: self.maximum.as_ref().map(|v| v.clone_ref(py)),
            },
        })
    }

    #[pyo3(signature = (*, left, right, operation))]
    pub(crate) fn binary<'py>(
        &self,
        py: Python<'py>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
        operation: &str,
    ) -> PyResult<Bound<'py, PyAny>> {
        let calculate: fn(&BigInt, &BigInt) -> BigInt = match operation {
            "add" => BigInt::add_ref,
            "subtract" => BigInt::sub_ref,
            "multiply" => BigInt::mul_ref,
            "floor-divide" => floor_quotient,
            _ => {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "无效内部整数运算 / Invalid internal integer operation",
                ));
            }
        };
        if left.is_exact_instance_of::<PyInt>() && right.is_exact_instance_of::<PyInt>() {
            let left_range = integer_range(&left)?;
            let right_range = integer_range(&right)?;
            if let (IntegerRange::Small(left), IntegerRange::Small(right)) =
                (left_range, right_range)
                && let Some(value) = small_binary(left, right, operation)
            {
                return Ok(value.into_pyobject(py)?.into_any());
            }
            let left = big_integer(&left, left_range)?;
            let right = big_integer(&right, right_range)?;
            if operation == "floor-divide" && right.is_zero() {
                // 首次 guard 后的第二次字段读取仍可能变零；保留原运算协议异常。 / A second divisor read after the guard can become zero; retain the arithmetic protocol exception.
                return Err(pyo3::exceptions::PyZeroDivisionError::new_err(
                    "integer division or modulo by zero",
                ));
            }
            let result = py.detach(move || calculate(&left, &right));
            return integer_object(py, &result);
        }
        // 外部对象及 int 子类使用自己的数值槽，不抽取载荷绕过扩展。 / External values and int subclasses retain their numeric slots, without payload extraction.
        match operation {
            "add" => left.add(&right),
            "subtract" => left.sub(&right),
            "multiply" => left.mul(&right),
            "floor-divide" => left.floor_div(&right),
            _ => unreachable!(),
        }
    }

    pub(crate) fn negated<'py>(
        &self,
        py: Python<'py>,
        value: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        if value.is_exact_instance_of::<PyInt>() {
            let range = integer_range(&value)?;
            if let IntegerRange::Small(small) = range
                && small.checked_neg().is_some()
            {
                return Ok(i64::neg_ref(&small).into_pyobject(py)?.into_any());
            }
            let value = big_integer(&value, range)?;
            let result = py.detach(move || BigInt::neg_ref(&value));
            integer_object(py, &result)
        } else {
            value.neg()
        }
    }

    #[pyo3(signature = (*, left, right, operation))]
    pub(crate) fn relation<'py>(
        &self,
        py: Python<'py>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
        operation: &str,
    ) -> PyResult<Bound<'py, PyAny>> {
        let op = match operation {
            "eq" => CompareOp::Eq,
            "ne" => CompareOp::Ne,
            "lt" => CompareOp::Lt,
            "le" => CompareOp::Le,
            "gt" => CompareOp::Gt,
            "ge" => CompareOp::Ge,
            _ => {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "无效内部整数比较 / Invalid internal integer comparison",
                ));
            }
        };
        if left.is_exact_instance_of::<PyInt>() && right.is_exact_instance_of::<PyInt>() {
            let order = compare_integers(&left, &right)?;
            Ok(op.matches(order).into_pyobject(py)?.to_owned().into_any())
        } else {
            left.rich_compare(&right, op)
        }
    }

    #[pyo3(signature = (*, callable, left, right))]
    fn maximum<'py>(
        &self,
        callable: Bound<'py, PyAny>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        if self.is_builtin(&callable, false)
            && left.is_exact_instance_of::<PyInt>()
            && right.is_exact_instance_of::<PyInt>()
        {
            // max 在相等时保留第一个对象；不重新分配字段值。 / max keeps its first object on ties; do not reallocate field values.
            Ok(if compare_integers(&right, &left)?.is_gt() {
                right
            } else {
                left
            })
        } else {
            callable.call1((left, right))
        }
    }

    #[pyo3(signature = (*, maximum, lower, minimum, upper, value))]
    fn clamp<'py>(
        &self,
        maximum: Bound<'py, PyAny>,
        lower: Bound<'py, PyAny>,
        minimum: Bound<'py, PyAny>,
        upper: Bound<'py, PyAny>,
        value: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let inner = if self.is_builtin(&minimum, true)
            && upper.is_exact_instance_of::<PyInt>()
            && value.is_exact_instance_of::<PyInt>()
        {
            if compare_integers(&value, &upper)?.is_lt() {
                value
            } else {
                upper
            }
        } else {
            minimum.call1((upper, value))?
        };
        self.maximum(maximum, lower, inner)
    }

    pub(crate) fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.minimum)?;
        visit.call(&self.maximum)
    }

    pub(crate) fn __clear__(&mut self) {
        self.minimum = None;
        self.maximum = None;
    }
}

#[derive(Clone, Copy)]
enum IntegerDomain {
    Signed,
    Unsigned,
    Bounded,
    StrictUnsigned,
}

/// 保存函数的全局/内置命名空间身份，不缓存用户标量或构造器。 / Retain function namespace identities, never cached user scalars or constructors.
#[pyclass(module = "ospf_python._native", name = "_IntegerFacade")]
pub struct IntegerFacade {
    domain: IntegerDomain,
    namespace: Option<Py<PyDict>>,
    builtins: Option<Py<PyDict>>,
    ops: IntegerOps,
}

impl IntegerFacade {
    fn global<'py>(&self, py: Python<'py>, name: &str) -> PyResult<Bound<'py, PyAny>> {
        let key = match name {
            "min" => pyo3::intern!(py, "min").clone(),
            "max" => pyo3::intern!(py, "max").clone(),
            "object" => pyo3::intern!(py, "object").clone(),
            "ValueError" => pyo3::intern!(py, "ValueError").clone(),
            "NumericUInteger" => pyo3::intern!(py, "NumericUInteger").clone(),
            _ => PyString::new(py, name),
        };
        for namespace in [&self.namespace, &self.builtins].into_iter().flatten() {
            if let Some(value) = namespace.bind(py).get_item(&key)? {
                return Ok(value);
            }
        }
        let error = pyo3::exceptions::PyNameError::new_err(format!("name '{name}' is not defined"));
        error.value(py).setattr("name", key)?;
        Err(error)
    }

    fn field(&self) -> &'static str {
        match self.domain {
            IntegerDomain::Signed | IntegerDomain::Unsigned => "value",
            _ => "_value",
        }
    }

    fn constructor<'py>(
        &self,
        py: Python<'py>,
        owner: &Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        match self.domain {
            IntegerDomain::StrictUnsigned => self.global(py, "NumericUInteger"),
            _ => owner.getattr("__class__"),
        }
    }

    fn constructed_binary<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
        other: Bound<'py, PyAny>,
        operation: &str,
    ) -> PyResult<Bound<'py, PyAny>> {
        let constructor = self.constructor(py, &owner)?;
        let result = self.ops.binary(
            py,
            owner.getattr(self.field())?,
            other.getattr(self.field())?,
            operation,
        )?;
        constructor.call1((result,))
    }

    fn clamped<'py>(
        &self,
        py: Python<'py>,
        owner: &Bound<'py, PyAny>,
        value: Option<Bound<'py, PyAny>>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let maximum = self.global(py, "max")?;
        let lower = owner.getattr("MIN_VALUE")?;
        let minimum = self.global(py, "min")?;
        let upper = owner.getattr("MAX_VALUE")?;
        let value = match value {
            Some(value) => value,
            None => owner.getattr("_value")?,
        };
        self.ops.clamp(maximum, lower, minimum, upper, value)
    }

    fn divisor_is_zero(&self, py: Python<'_>, other: &Bound<'_, PyAny>) -> PyResult<bool> {
        self.ops
            .relation(
                py,
                other.getattr(self.field())?,
                0_i64.into_pyobject(py)?.into_any(),
                "eq",
            )?
            .is_truthy()
    }

    fn assign(
        &self,
        py: Python<'_>,
        owner: Bound<'_, PyAny>,
        field: &str,
        value: Bound<'_, PyAny>,
    ) -> PyResult<()> {
        self.global(py, "object")?
            .getattr("__setattr__")?
            .call1((owner, field, value))?;
        Ok(())
    }
}

#[pymethods]
impl IntegerFacade {
    #[pyo3(signature = (*, owner, other))]
    fn add<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.constructed_binary(py, owner, other, "add")
    }

    #[pyo3(signature = (*, owner, other))]
    fn multiply<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.constructed_binary(py, owner, other, "multiply")
    }

    #[pyo3(signature = (*, owner, other))]
    fn subtract<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.constructed_binary(py, owner, other, "subtract")
    }

    #[pyo3(signature = (*, owner, other))]
    fn divide<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
        other: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        if self.divisor_is_zero(py, &other)? {
            return self.constructor(py, &owner)?.call1((0,));
        }
        self.constructed_binary(py, owner, other, "floor-divide")
    }

    fn negate<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let constructor = self.constructor(py, &owner)?;
        let result = self.ops.negated(py, owner.getattr(self.field())?)?;
        constructor.call1((result,))
    }

    #[pyo3(signature = (*, left, right))]
    fn subtract_values<'py>(
        &self,
        py: Python<'py>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.ops.binary(py, left, right, "subtract")
    }

    #[pyo3(signature = (*, constructor, result))]
    fn unsigned_result<'py>(
        &self,
        py: Python<'py>,
        constructor: Bound<'py, PyAny>,
        result: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let result = self.ops.maximum(
            self.global(py, "max")?,
            result,
            0_i64.into_pyobject(py)?.into_any(),
        )?;
        constructor.call1((result,))
    }

    #[pyo3(signature = (*, owner, rhs))]
    fn bounded_add<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
        rhs: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.ops.binary(py, owner.getattr("_value")?, rhs, "add")
    }

    #[pyo3(signature = (*, owner, rhs))]
    fn bounded_multiply<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
        rhs: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.ops
            .binary(py, owner.getattr("_value")?, rhs, "multiply")
    }

    fn clamp_owner<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.clamped(py, &owner, None)
    }

    #[pyo3(signature = (*, owner, value))]
    fn clamp_result<'py>(
        &self,
        py: Python<'py>,
        owner: Bound<'py, PyAny>,
        value: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.clamped(py, &owner, Some(value))
    }

    fn initialize(&self, py: Python<'_>, owner: Bound<'_, PyAny>) -> PyResult<()> {
        if self
            .ops
            .relation(
                py,
                owner.getattr(self.field())?,
                0_i64.into_pyobject(py)?.into_any(),
                "lt",
            )?
            .is_truthy()?
        {
            match self.domain {
                IntegerDomain::StrictUnsigned => {
                    let error = self
                        .global(py, "ValueError")?
                        .call1(("NumericUInteger must be non-negative",))?;
                    return Err(PyErr::from_value(error));
                }
                _ => self.assign(py, owner, self.field(), 0_i64.into_pyobject(py)?.into_any())?,
            }
        }
        Ok(())
    }

    #[pyo3(signature = (*, left, right))]
    fn equal<'py>(
        &self,
        py: Python<'py>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.ops.relation(py, left, right, "eq")
    }

    #[pyo3(signature = (*, left, right))]
    fn not_equal<'py>(
        &self,
        py: Python<'py>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.ops.relation(py, left, right, "ne")
    }

    #[pyo3(signature = (*, left, right))]
    fn less<'py>(
        &self,
        py: Python<'py>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.ops.relation(py, left, right, "lt")
    }

    #[pyo3(signature = (*, left, right))]
    fn less_equal<'py>(
        &self,
        py: Python<'py>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.ops.relation(py, left, right, "le")
    }

    #[pyo3(signature = (*, left, right))]
    fn greater<'py>(
        &self,
        py: Python<'py>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.ops.relation(py, left, right, "gt")
    }

    #[pyo3(signature = (*, left, right))]
    fn greater_equal<'py>(
        &self,
        py: Python<'py>,
        left: Bound<'py, PyAny>,
        right: Bound<'py, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        self.ops.relation(py, left, right, "ge")
    }

    fn __traverse__(&self, visit: PyVisit<'_>) -> Result<(), PyTraverseError> {
        visit.call(&self.namespace)?;
        visit.call(&self.builtins)?;
        self.ops.__traverse__(visit)
    }

    fn __clear__(&mut self) {
        self.namespace = None;
        self.builtins = None;
        self.ops.__clear__();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::ToPrimitive;

    #[test]
    fn facade_uses_function_builtins_identity_and_live_global_values() {
        Python::initialize();
        Python::attach(|py| {
            let namespace = PyDict::new(py);
            py.run(
                c"table = {'token': 7}\n__builtins__ = table\ndef anchor(): pass",
                Some(&namespace),
                None,
            )
            .unwrap();
            let ops = IntegerOps::create(py).unwrap();
            let facade = ops
                .facade(
                    py,
                    namespace.get_item("anchor").unwrap().unwrap(),
                    "integer",
                )
                .unwrap();
            let original = namespace.get_item("table").unwrap().unwrap();
            namespace.set_item("__builtins__", PyDict::new(py)).unwrap();
            assert!(facade.builtins.as_ref().unwrap().bind(py).is(&original));
            assert_eq!(
                facade
                    .global(py, "token")
                    .unwrap()
                    .extract::<i32>()
                    .unwrap(),
                7
            );
            original.set_item("token", 9).unwrap();
            assert_eq!(
                facade
                    .global(py, "token")
                    .unwrap()
                    .extract::<i32>()
                    .unwrap(),
                9
            );
            namespace.set_item("token", 11).unwrap();
            assert_eq!(
                facade
                    .global(py, "token")
                    .unwrap()
                    .extract::<i32>()
                    .unwrap(),
                11
            );
        });
    }

    #[test]
    fn facade_missing_name_has_python_name_error_metadata() {
        Python::initialize();
        Python::attach(|py| {
            let namespace = PyDict::new(py);
            py.run(
                c"__builtins__ = {}\ndef anchor(): pass",
                Some(&namespace),
                None,
            )
            .unwrap();
            let facade = IntegerOps::create(py)
                .unwrap()
                .facade(
                    py,
                    namespace.get_item("anchor").unwrap().unwrap(),
                    "numeric_integer",
                )
                .unwrap();
            let error = facade.global(py, "max").unwrap_err();
            assert!(error.is_instance_of::<pyo3::exceptions::PyNameError>(py));
            assert_eq!(
                error
                    .value(py)
                    .getattr("name")
                    .unwrap()
                    .extract::<String>()
                    .unwrap(),
                "max"
            );
            assert_eq!(
                error
                    .value(py)
                    .getattr("args")
                    .unwrap()
                    .extract::<(String,)>()
                    .unwrap(),
                ("name 'max' is not defined".into(),)
            );
        });
    }

    #[test]
    fn facade_bounded_arithmetic_and_clamp_are_separate_publication_stages() {
        Python::initialize();
        Python::attach(|py| {
            let namespace = PyDict::new(py);
            py.run(
                c"events = []
def anchor(): pass
class Value:
    def __add__(self, right):
        events.append('add')
        return 13
class Owner:
    MIN_VALUE = 0
    MAX_VALUE = 9
    _value = Value()
    def __getattribute__(self, name):
        events.append(name)
        return object.__getattribute__(self, name)
def min(left, right):
    events.append('min')
    return right if right < left else left
def max(left, right):
    events.append('max')
    return right if right > left else left
owner = Owner()",
                Some(&namespace),
                None,
            )
            .unwrap();
            let facade = IntegerOps::create(py)
                .unwrap()
                .facade(
                    py,
                    namespace.get_item("anchor").unwrap().unwrap(),
                    "numeric_integer",
                )
                .unwrap();
            let owner = namespace.get_item("owner").unwrap().unwrap();
            let result = facade
                .bounded_add(
                    py,
                    owner.clone(),
                    3_i64.into_pyobject(py).unwrap().into_any(),
                )
                .unwrap();
            let events = namespace.get_item("events").unwrap().unwrap();
            assert_eq!(result.extract::<i32>().unwrap(), 13);
            assert_eq!(events.extract::<Vec<String>>().unwrap(), ["_value", "add"]);
            assert_eq!(
                facade
                    .clamp_result(py, owner, result)
                    .unwrap()
                    .extract::<i32>()
                    .unwrap(),
                9
            );
            assert_eq!(
                events.extract::<Vec<String>>().unwrap(),
                ["_value", "add", "MIN_VALUE", "MAX_VALUE", "min", "max"]
            );
        });
    }

    #[test]
    fn facade_namespace_cycle_is_collected_without_retaining_owners() {
        Python::initialize();
        Python::attach(|py| {
            let reference = {
                let namespace = PyDict::new(py);
                py.run(
                    c"import weakref\nclass Owner: pass\nowner = Owner()\nreference = weakref.ref(owner)\ndef anchor(): pass",
                    Some(&namespace),
                    None,
                )
                .unwrap();
                let facade = IntegerOps::create(py)
                    .unwrap()
                    .facade(
                        py,
                        namespace.get_item("anchor").unwrap().unwrap(),
                        "integer",
                    )
                    .unwrap();
                namespace
                    .set_item("context", Py::new(py, facade).unwrap())
                    .unwrap();
                namespace.get_item("reference").unwrap().unwrap()
            };
            py.import("gc").unwrap().call_method0("collect").unwrap();
            assert!(reference.call0().unwrap().is_none());
        });
    }

    #[test]
    fn binary_word_export_round_trips_zero_sign_padding_and_word_boundaries() {
        Python::initialize();
        Python::attach(|py| {
            for bits in [0, 1, 31, 32, 63, 64, 65, 127, 128, 129, 16385, 100000] {
                let base: BigInt = BigInt::one() << bits;
                for value in [
                    &base - 1,
                    base.clone(),
                    &base + 1,
                    -&base - 1,
                    -&base,
                    -&base + 1,
                ] {
                    let actual = integer_object(py, &value).unwrap();
                    let reference = value.clone().into_pyobject(py).unwrap();
                    assert!(actual.is_exact_instance_of::<PyInt>());
                    assert!(actual.eq(reference).unwrap());
                    assert_eq!(actual.extract::<BigInt>().unwrap(), value);
                    assert!(!PyErr::occurred(py));
                }
            }
        });
    }

    #[test]
    fn binary_word_export_preserves_dense_byte_order_and_sign_extension() {
        Python::initialize();
        Python::attach(|py| {
            for length in [0, 1, 7, 8, 9, 16, 17, 128, 2049, 12501] {
                let bytes = (0..length)
                    .map(|index| (index as u8).wrapping_mul(73).wrapping_add(19))
                    .collect::<Vec<_>>();
                for sign in [Sign::Minus, Sign::NoSign, Sign::Plus] {
                    let value = BigInt::from_bytes_le(sign, &bytes);
                    let actual = integer_object(py, &value).unwrap();
                    let reference = value.clone().into_pyobject(py).unwrap();
                    assert!(actual.is_exact_instance_of::<PyInt>());
                    assert!(actual.eq(reference).unwrap());
                    assert_eq!(actual.extract::<BigInt>().unwrap(), value);
                    assert!(!PyErr::occurred(py));
                }
            }
        });
    }

    #[test]
    fn checked_word_specialization_agrees_with_pinned_arbitrary_precision() {
        let values = [
            i64::MIN,
            i64::MIN + 1,
            -7,
            -3,
            -1,
            0,
            1,
            3,
            7,
            i64::MAX - 1,
            i64::MAX,
        ];
        for left in values {
            for right in values {
                for operation in ["add", "subtract", "multiply", "floor-divide"] {
                    let a = BigInt::from(left);
                    let b = BigInt::from(right);
                    let expected = match operation {
                        "add" => BigInt::add_ref(&a, &b),
                        "subtract" => BigInt::sub_ref(&a, &b),
                        "multiply" => BigInt::mul_ref(&a, &b),
                        "floor-divide" if right != 0 => floor_quotient(&a, &b),
                        _ => {
                            assert_eq!(small_binary(left, right, operation), None);
                            continue;
                        }
                    };
                    assert_eq!(small_binary(left, right, operation), expected.to_i64());
                }
            }
        }
    }

    #[test]
    fn exact_integer_range_comparison_preserves_sign_width_and_error_state() {
        Python::initialize();
        Python::attach(|py| {
            let huge: BigInt = BigInt::one() << 100000usize;
            let values = [
                -&huge,
                BigInt::from(i64::MIN) - 1,
                BigInt::from(i64::MIN),
                BigInt::from(-1),
                BigInt::zero(),
                BigInt::one(),
                BigInt::from(i64::MAX),
                BigInt::from(i64::MAX) + 1,
                huge,
            ];
            let objects = values
                .iter()
                .map(|value| value.into_pyobject(py).unwrap().into_any())
                .collect::<Vec<_>>();
            assert_eq!(integer_range(&objects[0]).unwrap(), IntegerRange::Below);
            assert_eq!(
                integer_range(&objects[2]).unwrap(),
                IntegerRange::Small(i64::MIN)
            );
            assert_eq!(integer_range(&objects[3]).unwrap(), IntegerRange::Small(-1));
            assert_eq!(
                integer_range(&objects[6]).unwrap(),
                IntegerRange::Small(i64::MAX)
            );
            assert_eq!(integer_range(&objects[8]).unwrap(), IntegerRange::Above);
            for (i, left) in objects.iter().enumerate() {
                for (j, right) in objects.iter().enumerate() {
                    assert_eq!(
                        compare_integers(left, right).unwrap(),
                        values[i].cmp(&values[j])
                    );
                    assert!(!PyErr::occurred(py));
                }
            }
        });
    }

    #[test]
    fn floor_is_exact_for_negative_nonmultiples_without_fixed_width_limits() {
        let value: BigInt = (BigInt::one() << 16385usize) + BigInt::from(17);
        let quotient = floor_quotient(&(-&value), &BigInt::from(3));
        assert!(BigInt::mul_ref(&quotient, &BigInt::from(3)) <= -&value);
        assert!(
            BigInt::mul_ref(
                &BigInt::add_ref(&quotient, &BigInt::one()),
                &BigInt::from(3)
            ) > -&value
        );
    }

    #[test]
    fn builtin_identities_do_not_certify_replaced_python_hooks() {
        Python::initialize();
        Python::attach(|py| {
            let ops = IntegerOps::create(py).unwrap();
            let builtins = py.import("builtins").unwrap();
            assert!(ops.is_builtin(&builtins.getattr("min").unwrap(), true));
            assert!(!ops.is_builtin(&builtins.getattr("max").unwrap(), true));
            let custom = py.eval(c"lambda a, b: a", None, None).unwrap();
            assert!(!ops.is_builtin(&custom, true));
        });
    }
}
