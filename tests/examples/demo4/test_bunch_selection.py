"""Bunch selection 测试 / Bunch selection tests.

覆盖 BunchSelector 和 SelectionResult。
Covers BunchSelector and SelectionResult.
"""

from __future__ import annotations

import pytest

from examples.framework_demo.demo4.domain.bunch_selection.model.selection_result import (
    SelectionResult,
)
from examples.framework_demo.demo4.domain.bunch_selection.service.bunch_selector import (
    BunchSelector,
    CandidateBunch,
)


class TestSelectionResult:
    """SelectionResult 测试 / SelectionResult tests."""

    def test_count(self) -> None:
        """选中数量 / Selected count."""
        r = SelectionResult(
            selected_bunches=("B1", "B2"),
            score=0.85,
        )
        assert r.count == 2

    def test_is_empty(self) -> None:
        """是否为空 / Is empty."""
        empty = SelectionResult(
            selected_bunches=(),
            score=0.0,
        )
        non_empty = SelectionResult(
            selected_bunches=("B1",),
            score=0.5,
        )
        assert empty.is_empty is True
        assert non_empty.is_empty is False

    def test_avg_score_per_bunch(self) -> None:
        """平均分数 / Average score."""
        r = SelectionResult(
            selected_bunches=("B1", "B2"),
            score=1.0,
        )
        assert r.avg_score_per_bunch == pytest.approx(0.5)

    def test_contains(self) -> None:
        """包含检查 / Contains check."""
        r = SelectionResult(
            selected_bunches=("B1", "B2"),
            score=0.8,
        )
        assert r.contains("B1") is True
        assert r.contains("B3") is False

    def test_merge(self) -> None:
        """合并 / Merge."""
        r1 = SelectionResult(
            selected_bunches=("B1",),
            score=0.5,
        )
        r2 = SelectionResult(
            selected_bunches=("B2",),
            score=0.3,
        )
        merged = r1.merge(r2)
        assert merged.count == 2
        assert merged.score >= r1.score

    def test_frozen(self) -> None:
        """不可变 / Frozen."""
        r = SelectionResult(
            selected_bunches=("B1",),
            score=0.5,
        )
        with pytest.raises(AttributeError):
            r.score = 0.9  # type: ignore[misc]


class TestBunchSelector:
    """BunchSelector 测试 / BunchSelector tests."""

    def test_select_basic(self) -> None:
        """基本选择 / Basic selection."""
        selector = BunchSelector(max_count=3, min_score=0.3)
        candidates = (
            CandidateBunch("B1", score=0.9, utilization=0.8),
            CandidateBunch("B2", score=0.7, utilization=0.6),
            CandidateBunch("B3", score=0.4, utilization=0.5),
            CandidateBunch("B4", score=0.1, utilization=0.2),
        )
        selected = selector.select(candidates)
        assert len(selected) == 3
        assert "B1" in selected
        assert "B4" not in selected

    def test_select_by_utilization(self) -> None:
        """按利用率选择 / Select by utilization."""
        selector = BunchSelector(max_count=10)
        candidates = (
            CandidateBunch("B1", score=0.9, utilization=0.8),
            CandidateBunch("B2", score=0.7, utilization=0.4),
        )
        selected = selector.select_by_utilization(candidates, min_utilization=0.5)
        assert len(selected) == 1
        assert selected[0] == "B1"

    def test_rank(self) -> None:
        """排名 / Rank."""
        selector = BunchSelector(max_count=10)
        candidates = (
            CandidateBunch("B1", score=0.5, utilization=0.5),
            CandidateBunch("B2", score=0.9, utilization=0.9),
            CandidateBunch("B3", score=0.7, utilization=0.7),
        )
        ranked = selector.rank(candidates)
        assert ranked[0] == "B2"

    def test_properties(self) -> None:
        """属性 / Properties."""
        selector = BunchSelector(max_count=5, min_score=0.3)
        assert selector.max_count == 5
        assert selector.min_score == pytest.approx(0.3)

    def test_empty_candidates(self) -> None:
        """空候选 / Empty candidates."""
        selector = BunchSelector(max_count=5)
        selected = selector.select(())
        assert len(selected) == 0
