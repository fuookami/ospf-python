"""幂向量键。

Power vector key for monomial indexing.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PowerVectorKey:
    """幂向量键，用于单项式索引。

    Power vector key used for monomial indexing. Each
    component represents the exponent of a variable.

    Attributes:
        variables: 变量名列表。/ Variable name list.
        powers: 对应幂次列表。/ Corresponding powers.
    """

    variables: tuple[str, ...]
    powers: tuple[int, ...]

    def __post_init__(self) -> None:
        """校验变量与幂次长度一致。/
        Validate variables and powers have same length.
        """
        if len(self.variables) != len(self.powers):
            raise NotImplementedError

    @property
    def degree(self) -> int:
        """总次数。/ Total degree."""
        return sum(self.powers)

    @property
    def is_constant(self) -> bool:
        """是否为常数项。/ Whether constant term."""
        return all(p == 0 for p in self.powers)

    def get_power(self, variable: str) -> int:
        """获取指定变量的幂次。

        Get power of a specific variable.

        Args:
            variable: 变量名。/ Variable name.

        Returns:
            幂次值，不存在则返回 0。/
            Power value, 0 if not found.
        """
        for name, power in zip(self.variables, self.powers, strict=False):
            if name == variable:
                return power
        return 0
