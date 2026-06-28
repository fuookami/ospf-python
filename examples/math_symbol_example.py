"""数学符号运算示例 / Math symbol operation example.

基本多项式构建、求值、求导。
Basic polynomial construction, evaluation, differentiation.
"""

from ospf_python.math.symbol.operation.differentiate import Differentiator
from ospf_python.math.symbol.operation.evaluate import PolynomialEvaluator
from ospf_python.math.symbol.operation.latex import LatexRenderer
from ospf_python.math.symbol.operation.quick_dsl import QuickDsl
from ospf_python.math.symbol.polynomial.canonical_polynomial import CanonicalPolynomial

dsl = QuickDsl(factory=CanonicalPolynomial)
ev = PolynomialEvaluator(factory=CanonicalPolynomial)
diff = Differentiator(factory=CanonicalPolynomial)
latex = LatexRenderer(factory=CanonicalPolynomial)

# 构建 x^2 + 2x + 1 / Build x^2 + 2x + 1
x = dsl.var("x")
two = dsl.constant(2.0)
one = dsl.constant(1.0)
x2 = dsl.product(x, x)
two_x = dsl.product(two, x)
poly = dsl.sum(x2, two_x, one)

# 求值 / Evaluate
val = ev.evaluate(poly, {"x": 3.0})
print(f"f(3) = {val}")  # f(3) = 16.0

# 求导 / Differentiate
derivative = diff.differentiate(poly, "x")
deriv_val = ev.evaluate(derivative, {"x": 3.0})
print(f"f'(3) = {deriv_val}")  # f'(3) = 8.0

# LaTeX 渲染 / LaTeX render
print(f"LaTeX: {latex.render(poly)}")  # LaTeX: ...
