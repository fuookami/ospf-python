"""初等运算符Result示例 / Elementary-operator Result example."""

from __future__ import annotations

import math
from numbers import Real
from typing import cast

from ospf_python.math.operator.exp import exp2_op, exp10_op, exp_op
from ospf_python.math.operator.log import log2_op, log10_op, log_op
from ospf_python.math.operator.trigonometry import (
    acos_op,
    asin_op,
    atan_op,
    cos_op,
    sin_op,
    tan_op,
)


def main() -> None:
    """显式消费固定Rust初等运算结果 / Explicitly consume pinned-Rust elementary results."""
    exp = exp_op(1.0).unwrap()
    exp2 = exp2_op(10.0).unwrap()
    exp10 = exp10_op(cast("Real", 2.0)).unwrap()
    ln = log_op(math.e).unwrap()
    log2 = log2_op(8.0).unwrap()
    log10 = log10_op(1000.0).unwrap()
    sin = sin_op(math.pi / 2).unwrap()
    cos = cos_op(0.0).unwrap()
    tan = tan_op(0.0).unwrap()
    asin = asin_op(1.0).unwrap()
    acos = acos_op(0.0).unwrap()
    atan = atan_op(1.0).unwrap()
    print(f"Elementary: exp(1)={exp:.6f}; exp2(10)={exp2:.0f}; exp10(2)={exp10:.0f}")
    print(f"Logs: ln(e)={ln:.0f}; log2(8)={log2:.0f}; log10(1000)={log10:.0f}")
    print(
        f"Trig: sin(pi/2)={sin:.0f}; cos(0)={cos:.0f}; tan(0)={tan:.0f}; "
        f"asin(1)={asin:.6f}; acos(0)={acos:.6f}; atan(1)={atan:.6f}"
    )


if __name__ == "__main__":
    main()
