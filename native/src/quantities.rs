//! 固定 Rust 运行时单位及精确换算；不保存 Python 数值镜像。 / Pinned runtime units and exact conversion without Python numeric mirrors.

use bigdecimal::BigDecimal;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{ToPrimitive, Zero};
use ospf_rust_quantities::Quantity;
use ospf_rust_quantities::dimension::DerivedQuantity;
use ospf_rust_quantities::dimension::fundamental_quantity::{
    FundamentalQuantity, FundamentalQuantityEnum,
};
use ospf_rust_quantities::scale::Scale;
use ospf_rust_quantities::unit::{Unit, UnitConversionRule};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::{PyFloat, PyInt, PyTuple};
use serde::{Deserialize, Serialize};

use crate::failure::{Failure, Transport, transport};
use crate::numeric::Rational;

type DecimalParts = (BigInt, i64);

fn float_parts(value: f64) -> Result<DecimalParts, Failure> {
    let mut decimal = BigDecimal::try_from(value).map_err(|_| {
        let mut failure = Failure::binding(
            "ILLEGAL_ARGUMENT",
            "单位系数必须有限 / Unit coefficient must be finite",
        );
        failure.source = "ospf-python";
        failure
    })?;
    // 依赖对次正规数保留可约尾零；仅规范此分支以匹配 Decimal.from_float 的旧线编码。
    // Normalize only subnormals: the dependency retains reducible trailing zeros unlike Decimal.from_float.
    if value.is_subnormal() {
        decimal = decimal.normalized();
    }
    Ok(decimal.as_bigint_and_exponent())
}

fn encoded_parts(value: &Bound<'_, PyAny>) -> PyResult<Result<DecimalParts, Failure>> {
    if value.is_exact_instance_of::<PyInt>() {
        return Ok(Ok((value.extract()?, 0)));
    }
    if value.is_exact_instance_of::<PyFloat>() {
        return Ok(float_parts(value.extract()?));
    }
    if value.is_exact_instance_of::<PyTuple>() {
        let parts = value.cast::<PyTuple>()?;
        if parts.len() == 2
            && parts.get_item(0)?.is_exact_instance_of::<PyInt>()
            && parts.get_item(1)?.is_exact_instance_of::<PyInt>()
        {
            return Ok(Ok(parts.extract()?));
        }
    }
    Ok(Err(Failure::input(
        "无效单位系数传输 / Invalid unit coefficient transport",
    )))
}

fn axes() -> [FundamentalQuantityEnum; 10] {
    use FundamentalQuantityEnum as F;
    [
        F::Mass,
        F::Length,
        F::Time,
        F::ElectricCurrent,
        F::ThermodynamicTemperature,
        F::AmountOfSubstance,
        F::LuminousIntensity,
        F::Information,
        F::PlaneAngle,
        F::SolidAngle,
    ]
}

#[pyclass(frozen, name = "_QuantityUnit", module = "ospf_python._native")]
pub struct QuantityUnit {
    unit: Unit,
}

#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct DecimalWire {
    coefficient: String,
    scale: i64,
}

impl DecimalWire {
    fn encode(value: &BigDecimal) -> Self {
        let (coefficient, scale) = value.as_bigint_and_exponent();
        Self {
            coefficient: coefficient.to_string(),
            scale,
        }
    }

    fn decode(self) -> Result<DecimalParts, Failure> {
        let invalid =
            || Failure::input("无效十进制系数快照 / Invalid decimal coefficient snapshot");
        let coefficient: BigInt = self.coefficient.parse().map_err(|_| invalid())?;
        if coefficient.to_string() != self.coefficient {
            return Err(invalid());
        }
        Ok((coefficient, self.scale))
    }
}

#[derive(Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct UnitWire {
    schema: String,
    version: u32,
    name: String,
    symbol: String,
    powers: Vec<i64>,
    scale: DecimalWire,
    offset: Option<DecimalWire>,
}

impl QuantityUnit {
    pub(crate) fn from_unit(unit: Unit) -> Self {
        Self { unit }
    }

    pub(crate) fn cloned_unit(&self) -> Unit {
        self.unit.clone()
    }

    fn create(
        name: String,
        symbol: String,
        powers: Vec<i64>,
        scale: DecimalParts,
        offset: Option<DecimalParts>,
    ) -> Result<Self, Failure> {
        if powers.len() != axes().len() {
            return Err(Failure::input(
                "需要十个量纲指数 / Ten dimension powers are required",
            ));
        }
        // 上游精确域将十进制指数转换为 u32；在构造前拒绝越界。 / The upstream exact domain converts decimal exponents to u32; reject out-of-range inputs before construction.
        if std::iter::once(&scale)
            .chain(offset.iter())
            .any(|(_, exponent)| u32::try_from(exponent.unsigned_abs()).is_err())
        {
            return Err(Failure::binding(
                "NOT_SUPPORTED",
                "十进制指数超出固定内核范围 / Decimal exponent exceeds the pinned kernel range",
            ));
        }
        let factor = BigDecimal::new(scale.0, scale.1);
        if factor.is_zero() {
            return Err(Failure::input(
                "单位比例不能为零 / Unit scale must not be zero",
            ));
        }
        let upstream_scale = Scale::from_big_decimal(factor.clone());
        if upstream_scale.value() != &factor {
            return Err(Failure::binding(
                "DATA_LOSS",
                "固定比例尺改变了系数精度 / Pinned Scale changed coefficient precision",
            ));
        }
        let conversion = match offset {
            Some((coefficient, scale)) => {
                UnitConversionRule::affine(upstream_scale, BigDecimal::new(coefficient, scale))
            }
            None => UnitConversionRule::linear(upstream_scale),
        };
        let dimension = DerivedQuantity::from_quantities(
            name.clone(),
            axes()
                .into_iter()
                .zip(powers)
                .filter_map(|(axis, power)| {
                    (power != 0).then(|| FundamentalQuantity::new(axis, power))
                })
                .collect(),
        );
        Ok(Self {
            unit: Unit::new_with_conversion(name, symbol, dimension, conversion),
        })
    }

    pub(crate) fn dimensions(&self) -> Vec<i64> {
        axes()
            .iter()
            .map(|axis| self.unit.dimension().get_power(axis))
            .collect()
    }

    fn matching_dimension(&self, target: &Self) -> Result<(), Failure> {
        if self.unit.same_dimension(&target.unit) {
            Ok(())
        } else {
            Err(Failure::input(
                "物理量量纲不匹配 / Physical quantity dimensions do not match",
            ))
        }
    }

    fn exact_conversion(&self, value: &BigRational, target: &Self) -> Result<Rational, Failure> {
        self.matching_dimension(target)?;
        let quantity = Quantity::new(value.clone(), self.unit.clone());
        quantity.to_unit(&target.unit).map(|converted| Rational { value: converted.value })
            .map_err(|_| Failure::binding("NOT_SUPPORTED", "固定内核不能执行此精确换算 / Pinned kernel cannot perform this exact conversion"))
    }

    fn float_coefficients(&self) -> Result<(), Failure> {
        for coefficient in [self.unit.scale().value(), &self.unit.conversion().offset()] {
            let float = coefficient.to_f64().filter(|value| value.is_finite()).ok_or_else(|| {
                Failure::binding("OVERFLOW", "单位系数超出有限 Float64 范围 / Unit coefficient exceeds finite Float64 range")
            })?;
            if float == 0.0 && !coefficient.is_zero() {
                return Err(Failure::binding(
                    "DATA_LOSS",
                    "单位系数在 Float64 下溢为零 / Unit coefficient underflows to zero in Float64",
                ));
            }
        }
        Ok(())
    }

    fn float_conversion(&self, value: f64, target: &Self) -> Result<f64, Failure> {
        self.matching_dimension(target)?;
        if !value.is_finite() {
            return Err(Failure::input(
                "需要有限 Float64 数值 / A finite Float64 value is required",
            ));
        }
        self.float_coefficients()?;
        target.float_coefficients()?;
        let quantity = Quantity::new(value, self.unit.clone());
        let result = quantity.to_unit(&target.unit).map_err(|_| Failure::binding(
            "NOT_SUPPORTED", "固定内核不能执行此 Float64 换算 / Pinned kernel cannot perform this Float64 conversion"
        ))?.value;
        if !result.is_finite() {
            return Err(Failure::binding(
                "OVERFLOW",
                "换算结果超出有限 Float64 范围 / Conversion result exceeds finite Float64 range",
            ));
        }
        Ok(result)
    }

    fn exact_binary(
        &self,
        value: &BigRational,
        right: &BigRational,
        unit: &Self,
        subtract: bool,
    ) -> Result<(Rational, Self), Failure> {
        self.matching_dimension(unit)?;
        if !subtract && !self.unit.is_linear() && !unit.unit.is_linear() {
            return Err(Failure::input(
                "两个温度点不能相加 / Two affine temperature points cannot be added",
            ));
        }
        if subtract && self.unit.is_linear() && !unit.unit.is_linear() {
            return Err(Failure::input(
                "不能从温差减去温度点 / Cannot subtract an affine point from a linear difference",
            ));
        }
        let mut left = Quantity::new(value.clone(), self.unit.clone());
        let mut right = Quantity::new(right.clone(), unit.unit.clone());
        if self.unit.is_linear() != unit.unit.is_linear() {
            let (difference, point) = if self.unit.is_linear() {
                (&mut left, &right)
            } else {
                (&mut right, &left)
            };
            // 先用上游精确换算统一温差比例，避免上游混合点差分支的十进制舍入。
            // Convert the difference with the upstream exact path before its decimal-rounded mixed branch.
            let target = Unit::new_with_domain(
                difference.unit.name().into(),
                difference.unit.symbol().into(),
                point.unit.dimension().clone(),
                point.unit.scale().clone(),
                difference.unit.domain(),
            );
            *difference = difference.to_unit(&target).map_err(|_| {
                Failure::binding(
                    "NOT_SUPPORTED",
                    "固定内核不能精确换算温差 / Pinned kernel cannot convert the difference exactly",
                )
            })?;
        }
        let result = if subtract {
            left.checked_sub(&right)
        } else {
            left.checked_add(&right)
        };
        result.map(|value| (Rational { value: value.value }, Self { unit: value.unit }))
            .map_err(|_| Failure::binding("NOT_SUPPORTED", "固定内核不能执行此物理量运算 / Pinned kernel cannot perform this quantity operation"))
    }

    fn float_binary(
        &self,
        value: f64,
        other: f64,
        unit: &Self,
        subtract: bool,
    ) -> Result<(f64, Self), Failure> {
        self.matching_dimension(unit)?;
        if !value.is_finite() || !other.is_finite() {
            return Err(Failure::input(
                "需要有限 Float64 操作数 / Finite Float64 operands required",
            ));
        }
        self.float_coefficients()?;
        unit.float_coefficients()?;
        if (!subtract && !self.unit.is_linear() && !unit.unit.is_linear())
            || (subtract && self.unit.is_linear() && !unit.unit.is_linear())
        {
            return Err(Failure::input(
                "无效点差运算 / Invalid point/difference operation",
            ));
        }
        let left = Quantity::new(value, self.unit.clone());
        let right = Quantity::new(other, unit.unit.clone());
        let output = if subtract { left.checked_sub(&right) } else { left.checked_add(&right) }
            .map_err(|_| Failure::binding("NOT_SUPPORTED", "固定内核不能执行此 Float64 运算 / Pinned kernel cannot perform this Float64 operation"))?;
        if !output.value.is_finite() {
            return Err(Failure::binding(
                "OVERFLOW",
                "物理量结果超出有限 Float64 范围 / Quantity result exceeds finite Float64 range",
            ));
        }
        Ok((output.value, Self { unit: output.unit }))
    }

    fn exact_scalar(
        &self,
        value: &BigRational,
        scalar: &BigRational,
        divide: bool,
    ) -> Result<(Rational, Self), Failure> {
        if !self.unit.is_linear() {
            return Err(Failure::input(
                "温度点不能作为标量缩放 / Affine points cannot be scaled",
            ));
        }
        if divide && scalar.is_zero() {
            return Err(Failure::input(
                "物理量不能除以零 / Cannot divide a quantity by zero",
            ));
        }
        // 在进入固定内核前排除其已知 panic 条件，不以捕获 panic 实现错误合同。
        // Exclude known panic conditions before pinned operators; panic catching is not an error contract.
        let quantity = Quantity::new(value.clone(), self.unit.clone());
        let output = if divide {
            quantity / scalar.clone()
        } else {
            quantity * scalar.clone()
        };
        Ok((
            Rational {
                value: output.value,
            },
            Self { unit: output.unit },
        ))
    }

    fn float_scalar(&self, value: f64, scalar: f64, divide: bool) -> Result<(f64, Self), Failure> {
        if !self.unit.is_linear() {
            return Err(Failure::input(
                "温度点不能作为标量缩放 / Affine points cannot be scaled",
            ));
        }
        if !value.is_finite() || !scalar.is_finite() || (divide && scalar == 0.0) {
            return Err(Failure::input(
                "需要有限操作数及非零除数 / Finite operands and a nonzero divisor required",
            ));
        }
        let quantity = Quantity::new(value, self.unit.clone());
        let output = if divide {
            quantity / scalar
        } else {
            quantity * scalar
        };
        if !output.value.is_finite() {
            return Err(Failure::binding(
                "OVERFLOW",
                "物理量结果超出有限 Float64 范围 / Quantity result exceeds finite Float64 range",
            ));
        }
        Ok((output.value, Self { unit: output.unit }))
    }

    fn decode(text: &str) -> Result<Self, Failure> {
        let wire: UnitWire = serde_json::from_str(text)
            .map_err(|_| Failure::input("无效单位快照 / Invalid unit snapshot"))?;
        if wire.schema != "ospf.unit" || wire.version != 1 {
            return Err(Failure::input(
                "不支持的单位快照版本 / Unsupported unit snapshot version",
            ));
        }
        Self::create(
            wire.name,
            wire.symbol,
            wire.powers,
            wire.scale.decode()?,
            wire.offset.map(DecimalWire::decode).transpose()?,
        )
    }
}

#[pymethods]
impl QuantityUnit {
    fn __copy__(&self) -> Self {
        Self {
            unit: self.unit.clone(),
        }
    }

    fn __deepcopy__(&self, _memo: &Bound<'_, PyAny>) -> Self {
        self.__copy__()
    }

    fn __reduce__<'py>(&self, py: Python<'py>) -> PyResult<(Bound<'py, PyAny>, (String,))> {
        Ok((
            py.import("ospf_python._native")?
                .getattr("_restore_quantity_unit")?,
            (self.to_json(py),),
        ))
    }

    fn same_dimension(&self, other: &Self) -> bool {
        self.unit.same_dimension(&other.unit)
    }

    fn same_unit(&self, other: &Self) -> bool {
        self.unit == other.unit
    }

    fn descriptor(
        &self,
        py: Python<'_>,
    ) -> (String, String, Vec<i64>, DecimalParts, Option<DecimalParts>) {
        py.detach(|| {
            (
                self.unit.name().into(),
                self.unit.symbol().into(),
                self.dimensions(),
                self.unit.scale().value().as_bigint_and_exponent(),
                (!self.unit.is_linear())
                    .then(|| self.unit.conversion().offset().as_bigint_and_exponent()),
            )
        })
    }

    #[pyo3(signature = (*, value, target))]
    fn convert_exact(
        &self,
        py: Python<'_>,
        value: &Rational,
        target: &Self,
    ) -> Transport<Rational> {
        transport(py.detach(|| self.exact_conversion(&value.value, target)))
    }

    #[pyo3(signature = (*, value, target))]
    fn convert_float64(&self, py: Python<'_>, value: f64, target: &Self) -> Transport<f64> {
        transport(py.detach(|| self.float_conversion(value, target)))
    }

    #[pyo3(signature = (*, value, other, other_unit, subtract=false))]
    fn binary_exact(
        &self,
        py: Python<'_>,
        value: &Rational,
        other: &Rational,
        other_unit: &Self,
        subtract: bool,
    ) -> Transport<(Rational, Self)> {
        transport(py.detach(|| self.exact_binary(&value.value, &other.value, other_unit, subtract)))
    }

    #[pyo3(signature = (*, value, other, other_unit, subtract=false))]
    fn binary_float64(
        &self,
        py: Python<'_>,
        value: f64,
        other: f64,
        other_unit: &Self,
        subtract: bool,
    ) -> Transport<(f64, Self)> {
        transport(py.detach(|| self.float_binary(value, other, other_unit, subtract)))
    }

    #[pyo3(signature = (*, value, scalar, divide=false))]
    fn scalar_exact(
        &self,
        py: Python<'_>,
        value: &Rational,
        scalar: &Rational,
        divide: bool,
    ) -> Transport<(Rational, Self)> {
        transport(py.detach(|| self.exact_scalar(&value.value, &scalar.value, divide)))
    }

    #[pyo3(signature = (*, value, scalar, divide=false))]
    fn scalar_float64(
        &self,
        py: Python<'_>,
        value: f64,
        scalar: f64,
        divide: bool,
    ) -> Transport<(f64, Self)> {
        transport(py.detach(|| self.float_scalar(value, scalar, divide)))
    }

    fn to_json(&self, py: Python<'_>) -> String {
        py.detach(|| {
            serde_json::to_string(&UnitWire {
                schema: "ospf.unit".into(),
                version: 1,
                name: self.unit.name().into(),
                symbol: self.unit.symbol().into(),
                powers: self.dimensions(),
                scale: DecimalWire::encode(self.unit.scale().value()),
                offset: (!self.unit.is_linear())
                    .then(|| DecimalWire::encode(&self.unit.conversion().offset())),
            })
            .expect("validated unit metadata serializes")
        })
    }
}

#[pyfunction]
#[pyo3(signature = (*, name, symbol, powers, scale, offset=None))]
pub fn _create_quantity_unit(
    py: Python<'_>,
    name: String,
    symbol: String,
    powers: Vec<i64>,
    scale: DecimalParts,
    offset: Option<DecimalParts>,
) -> Transport<QuantityUnit> {
    transport(py.detach(|| QuantityUnit::create(name, symbol, powers, scale, offset)))
}

#[pyfunction]
#[pyo3(signature = (*, name, symbol, powers, scale, offset=None))]
pub fn _create_quantity_unit_encoded(
    py: Python<'_>,
    name: String,
    symbol: String,
    powers: Vec<i64>,
    scale: &Bound<'_, PyAny>,
    offset: Option<&Bound<'_, PyAny>>,
) -> PyResult<Transport<QuantityUnit>> {
    let scale = match encoded_parts(scale)? {
        Ok(scale) => scale,
        Err(failure) => return Ok(transport(Err(failure))),
    };
    let offset = match offset.map(encoded_parts).transpose()? {
        Some(Ok(offset)) => Some(offset),
        Some(Err(failure)) => return Ok(transport(Err(failure))),
        None => None,
    };
    // 只把拥有所有权的 Rust 元数据带出 GIL；固定 Unit 构造和精度防护仍共用唯一实现。
    // Only owned Rust metadata leaves the GIL; pinned Unit construction and precision guards remain shared.
    Ok(transport(py.detach(|| {
        QuantityUnit::create(name, symbol, powers, scale, offset)
    })))
}

#[pyfunction]
pub fn _quantity_unit_from_json(py: Python<'_>, text: &str) -> Transport<QuantityUnit> {
    transport(py.detach(|| QuantityUnit::decode(text)))
}

// pickle 协议必须返回真实对象或协议异常；公开 JSON 恢复仍返回 Result 传输。
// Pickle must restore an object or fail the protocol; public JSON restoration still uses Result transport.
#[pyfunction]
pub fn _restore_quantity_unit(py: Python<'_>, text: &str) -> PyResult<QuantityUnit> {
    py.detach(|| QuantityUnit::decode(text))
        .map_err(|failure| PyValueError::new_err(failure.message))
}

#[cfg(test)]
mod tests {
    use super::*;
    use ospf_rust_quantities::UnitConversionValue;

    #[test]
    fn copied_unit_retains_exact_metadata_and_zero_affine_identity() {
        Python::initialize();
        Python::attach(|py| {
            let point = QuantityUnit::create(
                "point".into(),
                "K".into(),
                vec![0; 10],
                (12300.into(), 4),
                Some((0.into(), 7)),
            )
            .unwrap();
            let cloned = point.__copy__();
            assert_eq!(point.to_json(py), cloned.to_json(py));
            assert!(!cloned.unit.is_linear());
            assert_eq!(
                point.to_json(py),
                _restore_quantity_unit(py, &point.to_json(py))
                    .unwrap()
                    .to_json(py)
            );
            assert!(_restore_quantity_unit(py, "{}").is_err());
            assert!(!PyErr::occurred(py));
        });
    }

    #[test]
    fn float_metadata_encoding_preserves_exact_binary_values_and_canonical_subnormals() {
        for value in [
            0.0,
            -0.0,
            1.0,
            1000.0,
            0.1,
            f64::MIN,
            f64::MAX,
            f64::from_bits(1),
            f64::from_bits(2),
            f64::from_bits(1 << 51),
            -f64::from_bits(2),
        ] {
            let (coefficient, scale) = float_parts(value).unwrap();
            let decimal = BigDecimal::new(coefficient.clone(), scale);
            let rational = <BigRational as UnitConversionValue>::from_decimal(&decimal).unwrap();
            assert_eq!(rational, BigRational::from_float(value).unwrap());
            if value.is_subnormal() {
                assert!(!(&coefficient % 10u8).is_zero());
            }
        }
        assert_eq!(float_parts(1000.0).unwrap(), (1000.into(), 0));
        assert_eq!(float_parts(f64::from_bits(2)).unwrap().1, 1073);
        for value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            let failure = float_parts(value).unwrap_err();
            assert_eq!(failure.category, "ILLEGAL_ARGUMENT");
            assert_eq!(failure.source, "ospf-python");
            assert_eq!(failure.rust_code, None);
        }
    }

    #[test]
    fn encoded_metadata_refuses_implicit_python_protocols() {
        Python::initialize();
        Python::attach(|py| {
            let scope = pyo3::types::PyDict::new(py);
            py.run(c"class Value:\n def __float__(self):\n  raise AssertionError('float')\n def __index__(self):\n  raise AssertionError('index')\nvalues = [Value(), True, (Value(), 0), (1, True), [1, 0], '1']", Some(&scope), None).unwrap();
            for value in scope
                .get_item("values")
                .unwrap()
                .unwrap()
                .try_iter()
                .unwrap()
            {
                assert!(encoded_parts(&value.unwrap()).unwrap().is_err());
            }
            let value = py.eval(c"(12300, 4)", None, None).unwrap();
            assert_eq!(encoded_parts(&value).unwrap().unwrap(), (12300.into(), 4));
            assert!(!PyErr::occurred(py));
        });
    }

    fn unit(scale: i64, affine: bool) -> QuantityUnit {
        QuantityUnit::create(
            "length".into(),
            "m".into(),
            vec![0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
            (scale.into(), 0),
            affine.then(|| (27315.into(), 2)),
        )
        .unwrap()
    }

    #[test]
    fn exact_conversion_and_dimension_guards() {
        let meter = unit(1, false);
        let kilometer = unit(1000, false);
        let big = BigRational::new((BigInt::from(1) << 512) + 1, 17.into());
        assert_eq!(
            meter.exact_conversion(&big, &kilometer).unwrap().value,
            &big / BigRational::from_integer(1000.into())
        );
        let mass = QuantityUnit::create(
            "mass".into(),
            "kg".into(),
            vec![1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            (1.into(), 0),
            None,
        )
        .unwrap();
        assert!(meter.exact_conversion(&big, &mass).is_err());
    }

    #[test]
    fn zero_scale_and_invalid_exponents_are_rejected_before_upstream() {
        assert!(
            QuantityUnit::create("zero".into(), "z".into(), vec![0; 10], (0.into(), 0), None)
                .is_err()
        );
        for scale in [i64::MIN, i64::MAX] {
            assert!(
                QuantityUnit::create(
                    "bad".into(),
                    "z".into(),
                    vec![0; 10],
                    (1.into(), scale),
                    None
                )
                .is_err()
            );
        }
    }

    #[test]
    fn float_checks_include_coefficients_and_result() {
        let meter = unit(1, false);
        assert!(meter.float_conversion(f64::NAN, &meter).is_err());
        assert!(
            unit(1000, false)
                .float_conversion(f64::MAX, &meter)
                .is_err()
        );
        assert_eq!(
            meter.float_conversion(-0.0, &meter).unwrap().to_bits(),
            (-0.0_f64).to_bits()
        );
        for exponent in [-1000, 1000] {
            let extreme = QuantityUnit::create(
                "extreme".into(),
                "e".into(),
                vec![0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
                (1.into(), exponent),
                None,
            )
            .unwrap();
            assert!(extreme.float_conversion(1.0, &meter).is_err());
        }
    }

    #[test]
    fn affine_points_and_differences_are_not_plain_scalars() {
        let point = unit(1, true);
        let ten = BigRational::from_integer(10.into());
        assert!(point.exact_binary(&ten, &ten, &point, false).is_err());
        let (difference, unit) = point.exact_binary(&ten, &ten, &point, true).unwrap();
        assert!(difference.value.is_zero());
        assert!(unit.unit.is_linear());
        assert_eq!(unit.unit.symbol(), "delta(m)");
    }

    #[test]
    fn pinned_decimal_scale_rounding_is_rejected_not_silently_exported() {
        let coefficient: BigInt = BigInt::from(10u8).pow(150) + 1;
        let factor = BigDecimal::new(coefficient.clone(), 151);
        assert_ne!(Scale::from_big_decimal(factor.clone()).value(), &factor);
        let failure = QuantityUnit::create(
            "precise".into(),
            "p".into(),
            vec![0; 10],
            (coefficient, 151),
            None,
        )
        .err()
        .unwrap();
        assert_eq!(failure.category, "DATA_LOSS");
    }

    #[test]
    fn mixed_affine_recurring_scale_ratio_uses_exact_conversion() {
        let point = unit(3, true);
        let delta = unit(1, false);
        let zero = BigRational::from_integer(0.into());
        let one = BigRational::from_integer(1.into());
        let raw = Quantity::new(zero.clone(), point.unit.clone())
            .checked_add(&Quantity::new(one.clone(), delta.unit.clone()))
            .unwrap();
        assert_ne!(raw.value, BigRational::new(1.into(), 3.into()));
        let third = BigRational::new(1.into(), 3.into());
        let (value, output) = point.exact_binary(&zero, &one, &delta, false).unwrap();
        assert_eq!(value.value, third);
        assert_eq!(output.unit, point.unit);
        assert_eq!(
            delta
                .exact_binary(&one, &zero, &point, false)
                .unwrap()
                .0
                .value,
            third
        );
        assert_eq!(
            point
                .exact_binary(&zero, &one, &delta, true)
                .unwrap()
                .0
                .value,
            -third
        );
    }

    #[test]
    fn checked_float_binary_rejects_nonfinite_overflow_and_coefficient_underflow() {
        let linear = unit(1, false);
        for value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            assert!(linear.float_binary(value, 1.0, &linear, false).is_err());
            assert!(linear.float_binary(1.0, value, &linear, true).is_err());
        }
        assert!(
            linear
                .float_binary(f64::MAX, f64::MAX, &linear, false)
                .is_err()
        );
        assert!(
            linear
                .float_binary(f64::MAX, -f64::MAX, &linear, true)
                .is_err()
        );
        let tiny = QuantityUnit::create(
            "tiny".into(),
            "t".into(),
            linear.dimensions(),
            (1.into(), 400),
            None,
        )
        .unwrap();
        assert_eq!(
            linear
                .float_binary(0.0, 1.0, &tiny, false)
                .err()
                .unwrap()
                .category,
            "DATA_LOSS"
        );
        assert!(
            linear
                .float_binary(-0.0, 0.0, &linear, true)
                .unwrap()
                .0
                .is_sign_negative()
        );
        assert!(
            !linear
                .float_binary(-0.0, 0.0, &linear, false)
                .unwrap()
                .0
                .is_sign_negative()
        );
    }

    #[test]
    fn checked_float_binary_publishes_actual_point_or_difference_units() {
        let point = unit(2, true);
        let delta = unit(1, false);
        assert!(point.float_binary(20.0, 10.0, &point, false).is_err());
        let (value, difference) = point.float_binary(20.0, 10.0, &point, true).unwrap();
        assert_eq!(value, 10.0);
        assert!(difference.unit.is_linear());
        assert!(
            !delta
                .float_binary(2.0, 20.0, &point, false)
                .unwrap()
                .1
                .unit
                .is_linear()
        );
        assert!(delta.float_binary(2.0, 20.0, &point, true).is_err());
    }

    #[test]
    fn checked_scalar_guards_panic_conditions_and_keeps_exact_quotients() {
        let linear = unit(1, false);
        let point = unit(1, true);
        let one = BigRational::from_integer(1.into());
        let zero = BigRational::zero();
        for divide in [false, true] {
            assert!(point.exact_scalar(&one, &one, divide).is_err());
            assert!(point.float_scalar(1.0, 1.0, divide).is_err());
        }
        assert!(linear.exact_scalar(&one, &zero, true).is_err());
        assert!(linear.float_scalar(1.0, -0.0, true).is_err());
        assert!(linear.float_scalar(f64::MAX, 2.0, false).is_err());
        assert!(linear.float_scalar(1.0, f64::NAN, false).is_err());
        let third = linear
            .exact_scalar(&one, &BigRational::from_integer(3.into()), true)
            .unwrap();
        assert_eq!(third.0.value, BigRational::new(1.into(), 3.into()));
        assert!(third.1.unit == linear.unit);
    }
}
