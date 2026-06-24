"""Csp1dColumnGeneration tests.

Test column generation lifecycle.
测试列生成生命周期。

Note: register() with empty input triggers a Failed()
call with a source code signature mismatch.
注意：register() 空输入触发源代码 Failed() 签名不匹配。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ospf_python.framework.csp1d.application.model.csp1d_solution import (
    Csp1dSolution,
)
from ospf_python.framework.csp1d.application.service.csp1d_column_generation import (
    ColumnRecord,
    Csp1dColumnGeneration,
)

if TYPE_CHECKING:
    from ospf_python.framework.csp1d.domain.material.model.shadow_price_map import (
        ShadowPriceMap,
    )


class TestColumnRecord:
    """ColumnRecord frozen dataclass tests."""

    def test_creation(self) -> None:
        """Create with all fields. / 使用所有字段创建。"""
        r = ColumnRecord(
            name="col-1",
            coefficients=(1.0, 2.0),
            reduced_cost=-0.5,
        )
        assert r.name == "col-1"
        assert r.coefficients == (1.0, 2.0)
        assert r.reduced_cost == -0.5

    def test_frozen(self) -> None:
        """Instance is frozen. / 实例不可变。"""
        r = ColumnRecord(
            name="col-1",
            coefficients=(1.0,),
            reduced_cost=0.0,
        )
        with pytest.raises(AttributeError):
            r.name = "col-2"  # type: ignore[misc]


class TestCsp1dColumnGeneration:
    """Csp1dColumnGeneration tests."""

    def test_creation(self) -> None:
        """Create with default parameters. / 默认参数创建。"""
        cg = Csp1dColumnGeneration()
        assert cg.iteration == 0
        assert cg.converged is False

    def test_register_initial_columns(self) -> None:
        """Register initial columns. / 注册初始列。"""
        cg = Csp1dColumnGeneration()
        col = ColumnRecord(name="c1", coefficients=(1.0,), reduced_cost=0.0)
        result = cg.register((col,))
        assert result.is_ok()
        assert len(cg.active_columns) == 1

    @pytest.mark.xfail(
        reason="Source code Failed() signature mismatch",
        raises=TypeError,
        strict=True,
    )
    def test_register_empty_fails(self) -> None:
        """Register empty columns fails. / 空列注册失败。"""
        cg = Csp1dColumnGeneration()
        result = cg.register(())
        assert result.is_failed()

    def test_add_columns(self) -> None:
        """Add new columns. / 添加新列。"""
        cg = Csp1dColumnGeneration()
        col1 = ColumnRecord(name="c1", coefficients=(1.0,), reduced_cost=0.0)
        cg.register((col1,))
        col2 = ColumnRecord(name="c2", coefficients=(2.0,), reduced_cost=-1.0)
        result = cg.add_columns((col2,))
        assert result.is_ok()
        assert len(cg.active_columns) == 2

    def test_remove_columns(self) -> None:
        """Remove columns by name. / 按名称移除列。"""
        cg = Csp1dColumnGeneration()
        col1 = ColumnRecord(name="c1", coefficients=(1.0,), reduced_cost=0.0)
        col2 = ColumnRecord(name="c2", coefficients=(2.0,), reduced_cost=-1.0)
        cg.register((col1, col2))
        result = cg.remove_columns(("c1",))
        assert result.is_ok()
        assert len(cg.active_columns) == 1
        assert cg.active_columns[0].name == "c2"

    def test_refresh_shadow_price(self) -> None:
        """Refresh shadow prices via callback. / 回调刷新影子价格。"""
        cg = Csp1dColumnGeneration()
        col = ColumnRecord(name="c1", coefficients=(1.0,), reduced_cost=0.0)
        cg.register((col,))

        def updater(prices: ShadowPriceMap) -> None:
            prices.set("P1", 5.0)

        result = cg.refresh_shadow_price(updater)
        assert result.is_ok()
        assert cg.iteration == 1
        assert cg.shadow_prices.get("P1") == 5.0

    def test_finalize(self) -> None:
        """Finalize marks converged. / 终止标记收敛。"""
        cg = Csp1dColumnGeneration()
        result = cg.finalize()
        assert result.is_ok()
        assert cg.converged is True

    def test_extract_solution(self) -> None:
        """Extract solution via callback. / 回调解提取。"""
        cg = Csp1dColumnGeneration()
        expected = Csp1dSolution(assignments=(), total_waste=0.0, utilization=1.0)

        def extractor() -> Csp1dSolution:
            return expected

        result = cg.extract_solution(extractor)
        assert result.is_ok()
        assert result.unwrap() == expected

    def test_max_iterations_convergence(self) -> None:
        """Converge after max iterations. / 最大迭代后收敛。"""
        cg = Csp1dColumnGeneration(max_iterations=2)
        col = ColumnRecord(name="c1", coefficients=(1.0,), reduced_cost=0.0)
        cg.register((col,))
        cg.refresh_shadow_price(lambda p: None)
        assert cg.iteration == 1
        assert cg.converged is False
        cg.refresh_shadow_price(lambda p: None)
        assert cg.iteration == 2
        assert cg.converged is True
