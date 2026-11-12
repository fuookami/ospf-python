"""浮点数值工具 / Float numeric helpers."""

from __future__ import annotations


def is_near_integer(ratio: float) -> bool:
    """判断比值是否贴近整数，吸收浮点除法噪点。

    Tell whether a ratio nears an integer, absorbing float division noise.

    浮点除法与取模都不可靠：``0.3 / 0.1 == 2.9999999999999996``、
    ``1.0 % 0.1 == 0.09999999999999995``、``0.7 / 0.1 == 6.999999999999999``。
    直接用 ``int()``、``%`` 或精确相等都会得到错误结果。
    Float division and modulo are unreliable: ``0.3 / 0.1 == 2.9999999999999996``,
    ``1.0 % 0.1 == 0.09999999999999995`` and ``0.7 / 0.1 == 6.999999999999999``. Plain
    ``int()``, ``%`` or exact equality all give wrong answers.

    容差按比值量级放大，否则大比值会被误判：比值 60 时 1e-9 的绝对容差不够。
    The tolerance scales with the ratio's magnitude; an absolute 1e-9 is too tight at large
    ratios such as 60.

    Args:
        ratio: 已算出的比值 / The already computed ratio.

    Returns:
        是否贴近整数 / Whether it nears an integer.
    """
    nearest = round(ratio)
    return abs(ratio - nearest) <= 1e-9 * max(1.0, abs(ratio))


def step_index(ratio: float) -> int:
    """把比值转成步进索引：贴近整数时取该整数，否则向零截断。

    Turn a ratio into a step index: take the near integer, otherwise truncate toward zero.

    Args:
        ratio: 已算出的比值 / The already computed ratio.

    Returns:
        步进索引 / Step index.
    """
    return round(ratio) if is_near_integer(ratio) else int(ratio)


def demo() -> None:
    """自检：浮点噪点必须被吸收，真分数必须被拒。 / Self-check: absorb float noise, reject real fractions."""
    # 三个真实噪点：朴素写法会判错。 / Three real noise cases that naive code gets wrong.
    assert is_near_integer(0.3 / 0.1), "0.3/0.1 == 2.9999999999999996 应判为整数"
    assert is_near_integer(0.7 / 0.1), "0.7/0.1 == 6.999999999999999 应判为整数"
    assert is_near_integer(1.0 / 0.1), "1.0/0.1 应判为整数"
    # 大比值：容差按量级放大到 1e-9 * 60 = 6e-8，所以 1e-8 的噪点能被吸收；
    # 而固定的 1e-9 绝对容差会把它判成非整数。
    # Large ratio: the scaled tolerance is 1e-9 * 60 = 6e-8, so 1e-8 of noise is absorbed,
    # while a fixed absolute 1e-9 would reject it.
    assert is_near_integer(60.0 + 1e-8), "比值 60 的 1e-8 噪点应被吸收"
    assert not is_near_integer(60.0 + 1e-6), "1e-6 已超出 6e-8 容差，应判为非整数"
    # 真分数必须被拒。 / Genuine fractions must be rejected.
    assert not is_near_integer(2.5), "2.5 不是整数"
    assert not is_near_integer(0.3 / 0.2), "1.5 不是整数"
    # step_index 的分支。 / step_index branches.
    assert step_index(0.3 / 0.1) == 3
    assert step_index(2.5) == 2, "非整数时向零截断"
    assert step_index(-2.5) == -2, "向零截断而非向下取整"
    print("numeric.demo: 全部断言通过")


if __name__ == "__main__":
    demo()
