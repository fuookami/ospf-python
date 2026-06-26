"""Generation configuration model.

生成配置模型 / Generation configuration model.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_MAX_BUNCH_SIZE: int = 50
DEFAULT_MIN_UTILIZATION: float = 0.6


@dataclass(frozen=True)
class GenerationConfig:
    """Configuration parameters for bunch generation.

    任务组生成的配置参数。
    """

    max_bunch_size: int = DEFAULT_MAX_BUNCH_SIZE
    min_utilization: float = DEFAULT_MIN_UTILIZATION

    def validate(self) -> list[str]:
        """Check configuration validity and return issues.

        检查配置有效性并返回问题列表。
        """
        issues: list[str] = []
        if self.max_bunch_size < 1:
            issues.append(f"max_bunch_size must be >= 1, got {self.max_bunch_size}")
        if self.max_bunch_size > 10000:
            issues.append(f"max_bunch_size must be <= 10000, got {self.max_bunch_size}")
        if self.min_utilization < 0.0:
            issues.append(f"min_utilization must be >= 0.0, got {self.min_utilization}")
        if self.min_utilization > 1.0:
            issues.append(f"min_utilization must be <= 1.0, got {self.min_utilization}")
        return issues

    @property
    def is_valid(self) -> bool:
        """Whether the configuration passes all checks.

        配置是否通过所有检查。
        """
        return len(self.validate()) == 0

    def with_max_bunch_size(
        self,
        size: int,
    ) -> GenerationConfig:
        """Create a copy with a different max bunch size.

        创建具有不同最大任务组大小的副本。
        """
        return GenerationConfig(
            max_bunch_size=size,
            min_utilization=self.min_utilization,
        )

    def with_min_utilization(
        self,
        utilization: float,
    ) -> GenerationConfig:
        """Create a copy with a different min utilization.

        创建具有不同最小利用率的副本。
        """
        return GenerationConfig(
            max_bunch_size=self.max_bunch_size,
            min_utilization=utilization,
        )
