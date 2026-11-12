"""固定Rust对数及任意宽整数的自然Result入口。 / Natural Result entry for pinned Rust logarithms and wide integers."""

from ospf_python.math.ordinary.log import log_base


def main() -> None:
    """演示普通、超Float64整数和域失败。 / Demonstrate ordinary and wider-than-Float64 integers and domain failure."""
    assert log_base(8, 2).unwrap() == 3
    assert abs(log_base(1 << 2048, 2).unwrap() - 2048) < 1e-10
    assert log_base(-1, 2).is_failed()
    assert log_base(8, 1).is_failed()


if __name__ == "__main__":
    main()
