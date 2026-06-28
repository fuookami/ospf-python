# Math API Reference

Mathematical foundations: algebra, geometry, combinatorics, symbolic math.

## Algebra

```python
from ospf_python.math.algebra.number.integer import IntegerNumber
from ospf_python.math.algebra.number.floating import FloatingNumber
from ospf_python.math.algebra.concept.field import Field
from ospf_python.math.algebra.concept.group import Group
```

## Symbol

Core symbolic math types and operations.

### Core Types

```python
from ospf_python.math.symbol.symbol import Symbol
from ospf_python.math.symbol.category import Category
from ospf_python.math.symbol.dimensioned_symbol import DimensionedSymbol
```

### Monomials

```python
from ospf_python.math.symbol.monomial.canonical_monomial import CanonicalMonomial
from ospf_python.math.symbol.monomial.linear_monomial import LinearMonomial
from ospf_python.math.symbol.monomial.quadratic_monomial import QuadraticMonomial
```

### Polynomials

```python
from ospf_python.math.symbol.polynomial.canonical_polynomial import CanonicalPolynomial
from ospf_python.math.symbol.polynomial.linear_polynomial import LinearPolynomial
from ospf_python.math.symbol.polynomial.quadratic_polynomial import QuadraticPolynomial
from ospf_python.math.symbol.polynomial.mutable_canonical_polynomial import MutableCanonicalPolynomial
from ospf_python.math.symbol.polynomial.mutable_linear_polynomial import MutableLinearPolynomial
from ospf_python.math.symbol.polynomial.mutable_quadratic_polynomial import MutableQuadraticPolynomial
```

### Operations

| Operation | Module | Description |
|-----------|--------|-------------|
| Differentiation | `operation.differentiate` | Symbolic differentiation |
| Evaluation | `operation.evaluate` | Evaluate at a point |
| LaTeX | `operation.latex` | Render to LaTeX |
| Parsing | `operation.parse` | Parse string expressions |
| Serialization | `operation.serde` | Serialize/deserialize |
| Normalization | `operation.normalize` | Normalize polynomial form |
| Conversion | `operation.convert` | Convert between polynomial types |
| Compilation | `operation.compile` | Compile to callable functions |
| Factorization | `operation.factorization` | Factor expressions |
| Quick DSL | `operation.quick_dsl` | Fluent DSL for building expressions |
| FLT64 DSL | `operation.flt64_quick_dsl` | Float64-optimized DSL |
| Combine Terms | `operation.combine_terms` | Combine like terms |
| Canonical Ops | `operation.canonical_ops` | Canonical form operations |

```python
from ospf_python.math.symbol.operation.differentiate import Differentiator
from ospf_python.math.symbol.operation.evaluate import PolynomialEvaluator
from ospf_python.math.symbol.operation.latex import LatexRenderer
from ospf_python.math.symbol.operation.parse import PolynomialStringParser
from ospf_python.math.symbol.operation.serde import SerdeOps
from ospf_python.math.symbol.operation.normalize import PolynomialNormalizer
from ospf_python.math.symbol.operation.convert import PolynomialConverter
from ospf_python.math.symbol.operation.compile import PolynomialCompiler
from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
from ospf_python.math.symbol.operation.flt64_quick_dsl import Flt64QuickDsl
```

## Inequality

```python
from ospf_python.math.symbol.inequality.canonical_inequality import CanonicalInequality
from ospf_python.math.symbol.inequality.linear_inequality import LinearInequality
from ospf_python.math.symbol.inequality.comparison import Comparison
```

## Expression SerDe

```python
from ospf_python.math.symbol.expression.serde.expression_serde import ExpressionSerializer, ExpressionDeserializer
```

## Geometry

```python
from ospf_python.math.geometry.point import Point2D, Point3D
from ospf_python.math.geometry.vector import Vector2D, Vector3D
```

## Chaotic Maps

```python
from ospf_python.math.chaotic.complex_squaring_map import ComplexSquaringMap
from ospf_python.math.chaotic.coullet_attractor import CoulletAttractor
from ospf_python.math.chaotic.four_wing_attractor import FourWingAttractor
from ospf_python.math.chaotic.wang_sun_attractor import WangSunAttractor
```

## Trivalent

```python
from ospf_python.math.trivalent import TrivalentValue
```
