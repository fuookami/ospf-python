"""基准数据集 fixtures / Benchmark dataset fixtures.

对齐 Kotlin @Param("small","medium","large") 参数化。
Aligned to Kotlin @Param("small","medium","large") parametrization.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """添加基准数据集大小命令行选项。

    Add benchmark dataset size CLI option.
    """
    parser.addoption(
        "--dataset-size",
        action="store",
        default="small,medium,large",
        help="Benchmark dataset sizes (comma-separated)",
    )


def _parse_sizes(request: pytest.FixtureRequest) -> list[str]:
    """解析数据集大小选项。

    Parse dataset size option.
    """
    raw = request.config.getoption("--dataset-size", default="small,medium,large")
    return [s.strip() for s in raw.split(",")]


# ==================== Core 热路径数据集 ====================
# ==================== Core hot path datasets ====================

CORE_SIZES: dict[str, dict[str, int]] = {
    "small": {"variables": 50, "constraints": 30, "objectives": 5},
    "medium": {"variables": 500, "constraints": 300, "objectives": 50},
    "large": {"variables": 5000, "constraints": 3000, "objectives": 500},
}


@pytest.fixture(
    params=["small", "medium", "large"],
    ids=["small", "medium", "large"],
)
def core_dataset(request: pytest.FixtureRequest) -> dict[str, int]:
    """Core 热路径数据集 / Core hot path dataset.

    对齐 Kotlin CoreHotPathBenchmark 的 small/medium/large 规模。
    Aligned to Kotlin CoreHotPathBenchmark small/medium/large scale.
    """
    return CORE_SIZES[request.param]


# ==================== Symbol 合并数据集 ====================
# ==================== Symbol combine datasets ====================

SYMBOL_SIZES: dict[str, dict[str, int]] = {
    "small": {"symbols": 5, "terms": 10, "polynomials": 20},
    "medium": {"symbols": 15, "terms": 50, "polynomials": 100},
    "large": {"symbols": 30, "terms": 200, "polynomials": 500},
}


@pytest.fixture(
    params=["small", "medium", "large"],
    ids=["small", "medium", "large"],
)
def symbol_dataset(request: pytest.FixtureRequest) -> dict[str, int]:
    """Symbol 合并数据集 / Symbol combine dataset.

    对齐 Kotlin SymbolCombineBenchmark 的 small/medium/large 规模。
    Aligned to Kotlin SymbolCombineBenchmark small/medium/large scale.
    """
    return SYMBOL_SIZES[request.param]


# ==================== MultiArray 运算数据集 ====================
# ==================== MultiArray ops datasets ====================

MULTIARRAY_SIZES: dict[str, dict[str, int | tuple[int, ...]]] = {
    "small": {"dims": (10, 10), "iterations": 100},
    "medium": {"dims": (50, 50), "iterations": 50},
    "large": {"dims": (200, 200), "iterations": 10},
}


@pytest.fixture(
    params=["small", "medium", "large"],
    ids=["small", "medium", "large"],
)
def multiarray_dataset(
    request: pytest.FixtureRequest,
) -> dict[str, int | tuple[int, ...]]:
    """MultiArray 运算数据集 / MultiArray ops dataset.

    对齐 Kotlin MultiArrayHotPathBenchmark 的 small/medium/large 规模。
    Aligned to Kotlin MultiArrayHotPathBenchmark small/medium/large scale.
    """
    return MULTIARRAY_SIZES[request.param]
