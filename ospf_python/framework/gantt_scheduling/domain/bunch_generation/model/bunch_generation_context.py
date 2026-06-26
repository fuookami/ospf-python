"""Gantt scheduling bunch generation context."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BunchGenerationConfig:
    """束编组生成配置 / Bunch generation config.

    Attributes:
        max_bunch_size: 最大束编组尺寸 / Max bunch size.
    """

    max_bunch_size: int = 10


@dataclass(frozen=True)
class BunchGenerationContext:
    """Gantt scheduling bunch generation context."""

    name: str = "bunch_generation_context"
    item_keys: tuple[str, ...] = ()
    config: BunchGenerationConfig = field(
        default_factory=BunchGenerationConfig,
    )
    _progress: float = 0.0
    _candidates: tuple[str, ...] = ()

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return bool(self.name)

    def with_progress(
        self,
        progress: float,
    ) -> BunchGenerationContext:
        """创建带进度的上下文副本。/ Create copy with progress."""
        return BunchGenerationContext(
            name=self.name,
            item_keys=self.item_keys,
            config=self.config,
            _progress=progress,
            _candidates=self._candidates,
        )

    def with_candidate(
        self,
        candidate: str,
    ) -> BunchGenerationContext:
        """创建包含新候选的上下文副本。/ Create copy with candidate."""
        return BunchGenerationContext(
            name=self.name,
            item_keys=self.item_keys,
            config=self.config,
            _progress=self._progress,
            _candidates=(*self._candidates, candidate),
        )
