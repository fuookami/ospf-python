"""束编组生成测试 / Bunch generation tests.

覆盖 bunch_generation 域中所有模块的基本功能，包括并行控制、
模板缓存、束编组生成器及模型桩。
Covers basic functionality of all bunch_generation domain modules,
including parallelism control, template cache, bunch generator,
and model stubs.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_context import (
    BunchGenerationContext,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_generation.model.bunch_generation_program_candidate_adapters import (
    BunchGenerationProgramCandidateAdapters,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_generation.service.bunch_generation_parallelism import (
    BunchGenerationParallelism,
    ParallelismConfig,
    WorkChunk,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_generation.service.bunch_generation_template_cache import (
    BunchGenerationTemplateCache,
    CacheEntry,
    CacheStats,
)
from ospf_python.framework.gantt_scheduling.domain.bunch_generation.service.bunch_generator import (
    BunchGenerator,
    GeneratedBunch,
    GenerationResult,
)

# =========================================================================
#  Test double for BunchGenerationContext
# =========================================================================


@dataclass(frozen=True)
class _StubConfig:
    """桩配置 / Stub config."""

    max_bunch_size: int = 3


@dataclass(frozen=True)
class _StubContext:
    """桩上下文，用于测试 BunchGenerator。

    Stub context for testing BunchGenerator.
    """

    item_keys: tuple[str, ...] = ()
    config: _StubConfig = _StubConfig()

    def with_progress(self, progress: float) -> _StubContext:
        """返回自身 / Return self."""
        return self

    def with_candidate(self, key: str) -> _StubContext:
        """返回自身 / Return self."""
        return self


# =========================================================================
#  BunchGenerationContext tests
# =========================================================================


class TestBunchGenerationContext:
    """束编组生成上下文测试 / Bunch generation context tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        ctx = BunchGenerationContext()
        assert ctx.name == "bunch_generation_context"

    def test_custom_name(self) -> None:
        """自定义名称 / Custom name."""
        ctx = BunchGenerationContext(name="custom")
        assert ctx.name == "custom"

    def test_is_valid_true(self) -> None:
        """有效时返回 True / Returns True when valid."""
        ctx = BunchGenerationContext(name="ok")
        assert ctx.is_valid is True

    def test_is_valid_false(self) -> None:
        """空名称时返回 False / Returns False for empty name."""
        ctx = BunchGenerationContext(name="")
        assert ctx.is_valid is False

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ctx = BunchGenerationContext()
        with pytest.raises(AttributeError):
            ctx.name = "changed"  # type: ignore[misc]


# =========================================================================
#  BunchGenerationProgramCandidateAdapters tests
# =========================================================================


class TestBunchGenerationProgramCandidateAdapters:
    """候选适配器测试 / Candidate adapters tests."""

    def test_default_name(self) -> None:
        """默认名称 / Default name."""
        adapters = BunchGenerationProgramCandidateAdapters()
        expected = "bunch_generation_program_candidate_adapters"
        assert adapters.name == expected

    def test_is_valid(self) -> None:
        """有效性检查 / Validity check."""
        adapters = BunchGenerationProgramCandidateAdapters()
        assert adapters.is_valid is True

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        adapters = BunchGenerationProgramCandidateAdapters()
        with pytest.raises(AttributeError):
            adapters.name = "x"  # type: ignore[misc]


# =========================================================================
#  ParallelismConfig tests
# =========================================================================


class TestParallelismConfig:
    """并行配置测试 / Parallelism config tests."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        cfg = ParallelismConfig()
        assert cfg.max_workers == 4
        assert cfg.chunk_size == 100
        assert cfg.enabled is True

    def test_custom_values(self) -> None:
        """自定义值 / Custom values."""
        cfg = ParallelismConfig(
            max_workers=8,
            chunk_size=50,
            enabled=False,
        )
        assert cfg.max_workers == 8
        assert cfg.chunk_size == 50
        assert cfg.enabled is False

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        cfg = ParallelismConfig()
        with pytest.raises(AttributeError):
            cfg.max_workers = 2  # type: ignore[misc]


# =========================================================================
#  WorkChunk tests
# =========================================================================


class TestWorkChunk:
    """工作分块测试 / Work chunk tests."""

    def test_required_field(self) -> None:
        """必需字段 / Required field."""
        chunk = WorkChunk(chunk_index=0)
        assert chunk.chunk_index == 0
        assert chunk.item_keys == ()
        assert chunk.worker_id == 0

    def test_with_items(self) -> None:
        """带物料项 / With items."""
        chunk = WorkChunk(
            chunk_index=1,
            item_keys=("a", "b"),
            worker_id=2,
        )
        assert chunk.item_keys == ("a", "b")
        assert chunk.worker_id == 2

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        chunk = WorkChunk(chunk_index=0)
        with pytest.raises(AttributeError):
            chunk.chunk_index = 1  # type: ignore[misc]


# =========================================================================
#  BunchGenerationParallelism tests
# =========================================================================


class TestBunchGenerationParallelism:
    """并行控制测试 / Parallelism control tests."""

    def test_default_config(self) -> None:
        """默认配置 / Default config."""
        p = BunchGenerationParallelism()
        assert p.config.max_workers == 4
        assert p.config.chunk_size == 100

    def test_split_work_disabled(self) -> None:
        """禁用时单一分块 / Single chunk when disabled."""
        cfg = ParallelismConfig(enabled=False)
        p = BunchGenerationParallelism(config=cfg)
        keys = ("a", "b", "c", "d", "e")
        chunks = p.split_work(keys)
        assert len(chunks) == 1
        assert chunks[0].item_keys == keys
        assert chunks[0].worker_id == 0

    def test_split_work_within_chunk_size(self) -> None:
        """未超过分块大小 / Within chunk size."""
        cfg = ParallelismConfig(chunk_size=10)
        p = BunchGenerationParallelism(config=cfg)
        keys = ("a", "b", "c")
        chunks = p.split_work(keys)
        assert len(chunks) == 1
        assert chunks[0].item_keys == keys

    def test_split_work_multiple_chunks(self) -> None:
        """多个分块 / Multiple chunks."""
        cfg = ParallelismConfig(chunk_size=3, max_workers=2)
        p = BunchGenerationParallelism(config=cfg)
        keys = tuple(str(i) for i in range(7))
        chunks = p.split_work(keys)
        assert len(chunks) == 3
        assert len(chunks[0].item_keys) == 3
        assert len(chunks[1].item_keys) == 3
        assert len(chunks[2].item_keys) == 1

    def test_split_work_worker_id_cycling(self) -> None:
        """工作线程标识循环 / Worker ID cycling."""
        cfg = ParallelismConfig(chunk_size=2, max_workers=2)
        p = BunchGenerationParallelism(config=cfg)
        keys = tuple(str(i) for i in range(6))
        chunks = p.split_work(keys)
        assert chunks[0].worker_id == 0
        assert chunks[1].worker_id == 1
        assert chunks[2].worker_id == 0

    def test_split_work_empty(self) -> None:
        """空输入 / Empty input."""
        p = BunchGenerationParallelism()
        chunks = p.split_work(())
        assert len(chunks) == 0

    def test_recommended_worker_count_normal(self) -> None:
        """正常推荐 / Normal recommendation."""
        cfg = ParallelismConfig(chunk_size=100, max_workers=4)
        p = BunchGenerationParallelism(config=cfg)
        assert p.recommended_worker_count(250) == 2

    def test_recommended_worker_count_capped(self) -> None:
        """不超过最大值 / Capped at max."""
        cfg = ParallelismConfig(chunk_size=10, max_workers=3)
        p = BunchGenerationParallelism(config=cfg)
        assert p.recommended_worker_count(1000) == 3

    def test_recommended_worker_count_disabled(self) -> None:
        """禁用时返回 1 / Returns 1 when disabled."""
        cfg = ParallelismConfig(enabled=False)
        p = BunchGenerationParallelism(config=cfg)
        assert p.recommended_worker_count(500) == 1

    def test_recommended_worker_count_zero_items(self) -> None:
        """零物料项 / Zero items."""
        p = BunchGenerationParallelism()
        assert p.recommended_worker_count(0) == 1

    def test_should_parallelize_true(self) -> None:
        """应并行化 / Should parallelize."""
        cfg = ParallelismConfig(chunk_size=100, enabled=True)
        p = BunchGenerationParallelism(config=cfg)
        assert p.should_parallelize(200) is True

    def test_should_parallelize_false_below(self) -> None:
        """低于阈值不并行化 / Below threshold."""
        cfg = ParallelismConfig(chunk_size=100, enabled=True)
        p = BunchGenerationParallelism(config=cfg)
        assert p.should_parallelize(50) is False

    def test_should_parallelize_disabled(self) -> None:
        """禁用时不并行化 / Disabled."""
        cfg = ParallelismConfig(enabled=False)
        p = BunchGenerationParallelism(config=cfg)
        assert p.should_parallelize(1000) is False

    def test_merge_chunk_keys(self) -> None:
        """合并分块键 / Merge chunk keys."""
        chunks = (
            WorkChunk(chunk_index=0, item_keys=("a", "b")),
            WorkChunk(chunk_index=1, item_keys=("c",)),
        )
        merged = BunchGenerationParallelism.merge_chunk_keys(
            chunks,
        )
        assert merged == ("a", "b", "c")

    def test_merge_chunk_keys_empty(self) -> None:
        """合并空分块 / Merge empty chunks."""
        merged = BunchGenerationParallelism.merge_chunk_keys(())
        assert merged == ()

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        p = BunchGenerationParallelism()
        with pytest.raises(AttributeError):
            p.config = ParallelismConfig(enabled=False)  # type: ignore[misc]


# =========================================================================
#  GeneratedBunch tests
# =========================================================================


class TestGeneratedBunch:
    """生成束编组测试 / Generated bunch tests."""

    def test_required_field(self) -> None:
        """必需字段 / Required field."""
        bunch = GeneratedBunch(bunch_key="b0")
        assert bunch.bunch_key == "b0"
        assert bunch.item_keys == ()
        assert bunch.score == 0.0

    def test_with_items_and_score(self) -> None:
        """带物料项和评分 / With items and score."""
        bunch = GeneratedBunch(
            bunch_key="b1",
            item_keys=("i1", "i2"),
            score=0.85,
        )
        assert bunch.item_keys == ("i1", "i2")
        assert bunch.score == pytest.approx(0.85)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        bunch = GeneratedBunch(bunch_key="b0")
        with pytest.raises(AttributeError):
            bunch.bunch_key = "b1"  # type: ignore[misc]


# =========================================================================
#  GenerationResult tests
# =========================================================================


class TestGenerationResult:
    """生成结果测试 / Generation result tests."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        ctx = BunchGenerationContext()
        result = GenerationResult(context=ctx)
        assert result.bunches == ()
        assert result.is_complete is False

    def test_with_bunches(self) -> None:
        """带束编组 / With bunches."""
        ctx = BunchGenerationContext()
        bunches = (GeneratedBunch(bunch_key="b0"),)
        result = GenerationResult(
            context=ctx,
            bunches=bunches,
            is_complete=True,
        )
        assert len(result.bunches) == 1
        assert result.is_complete is True


# =========================================================================
#  BunchGenerator tests
# =========================================================================


class TestBunchGenerator:
    """束编组生成器测试 / Bunch generator tests."""

    def test_default_prefix(self) -> None:
        """默认前缀 / Default prefix."""
        gen = BunchGenerator()
        assert gen.bunch_prefix == "gen"

    def test_custom_prefix(self) -> None:
        """自定义前缀 / Custom prefix."""
        gen = BunchGenerator(bunch_prefix="b")
        assert gen._bunch_key(0) == "b_0"
        assert gen._bunch_key(5) == "b_5"

    def test_generate_greedy_empty(self) -> None:
        """贪心策略空输入 / Greedy with empty input."""
        gen = BunchGenerator()
        ctx = _StubContext(item_keys=())
        result = gen.generate_greedy(ctx)  # type: ignore[arg-type]
        assert result.bunches == ()
        assert result.is_complete is True

    def test_generate_greedy_single_bunch(self) -> None:
        """贪心策略单束编组 / Greedy single bunch."""
        gen = BunchGenerator()
        ctx = _StubContext(
            item_keys=("a", "b"),
            config=_StubConfig(max_bunch_size=5),
        )
        result = gen.generate_greedy(ctx)  # type: ignore[arg-type]
        assert len(result.bunches) == 1
        assert result.bunches[0].item_keys == ("a", "b")
        assert result.bunches[0].bunch_key == "gen_0"
        assert result.is_complete is True

    def test_generate_greedy_multiple_bunches(self) -> None:
        """贪心策略多束编组 / Greedy multiple bunches."""
        gen = BunchGenerator()
        ctx = _StubContext(
            item_keys=("a", "b", "c", "d", "e"),
            config=_StubConfig(max_bunch_size=2),
        )
        result = gen.generate_greedy(ctx)  # type: ignore[arg-type]
        assert len(result.bunches) == 3
        assert result.bunches[0].item_keys == ("a", "b")
        assert result.bunches[1].item_keys == ("c", "d")
        assert result.bunches[2].item_keys == ("e",)
        assert result.bunches[2].bunch_key == "gen_2"

    def test_generate_balanced_empty(self) -> None:
        """均衡策略空输入 / Balanced with empty input."""
        gen = BunchGenerator()
        ctx = _StubContext(item_keys=())
        result = gen.generate_balanced(
            ctx,
            target_count=3,  # type: ignore[arg-type]
        )
        assert result.bunches == ()
        assert result.is_complete is True

    def test_generate_balanced_zero_target(self) -> None:
        """均衡策略零目标 / Balanced with zero target."""
        gen = BunchGenerator()
        ctx = _StubContext(item_keys=("a", "b"))
        result = gen.generate_balanced(
            ctx,
            target_count=0,  # type: ignore[arg-type]
        )
        assert result.bunches == ()
        assert result.is_complete is True

    def test_generate_balanced_even(self) -> None:
        """均衡策略均匀分配 / Balanced even distribution."""
        gen = BunchGenerator()
        ctx = _StubContext(item_keys=("a", "b", "c", "d"))
        result = gen.generate_balanced(
            ctx,
            target_count=2,  # type: ignore[arg-type]
        )
        assert len(result.bunches) == 2
        assert result.bunches[0].bunch_key == "gen_0"
        assert result.bunches[1].bunch_key == "gen_1"

    def test_generate_balanced_remainder(self) -> None:
        """均衡策略末尾分组获得余数 / Last group gets remainder."""
        gen = BunchGenerator()
        ctx = _StubContext(item_keys=("a", "b", "c", "d", "e"))
        result = gen.generate_balanced(
            ctx,
            target_count=2,  # type: ignore[arg-type]
        )
        assert len(result.bunches) == 2
        assert len(result.bunches[0].item_keys) == 2
        assert len(result.bunches[1].item_keys) == 3

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        gen = BunchGenerator()
        with pytest.raises(AttributeError):
            gen.bunch_prefix = "x"  # type: ignore[misc]


# =========================================================================
#  CacheEntry tests
# =========================================================================


class TestCacheEntry:
    """缓存条目测试 / Cache entry tests."""

    def test_required_field(self) -> None:
        """必需字段 / Required field."""
        entry = CacheEntry(cache_key="k1")
        assert entry.cache_key == "k1"
        assert entry.bunches == ()
        assert entry.hit_count == 0
        assert entry.item_count == 0

    def test_with_data(self) -> None:
        """带数据 / With data."""
        bunches = (GeneratedBunch(bunch_key="b0"),)
        entry = CacheEntry(
            cache_key="k1",
            bunches=bunches,
            hit_count=3,
            item_count=5,
        )
        assert len(entry.bunches) == 1
        assert entry.hit_count == 3
        assert entry.item_count == 5

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        entry = CacheEntry(cache_key="k1")
        with pytest.raises(AttributeError):
            entry.cache_key = "k2"  # type: ignore[misc]


# =========================================================================
#  CacheStats tests
# =========================================================================


class TestCacheStats:
    """缓存统计测试 / Cache stats tests."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        stats = CacheStats()
        assert stats.total_entries == 0
        assert stats.total_hits == 0
        assert stats.hit_rate == pytest.approx(0.0)

    def test_custom_values(self) -> None:
        """自定义值 / Custom values."""
        stats = CacheStats(
            total_entries=5,
            total_hits=10,
            hit_rate=2.0,
        )
        assert stats.total_entries == 5
        assert stats.total_hits == 10
        assert stats.hit_rate == pytest.approx(2.0)

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        stats = CacheStats()
        with pytest.raises(AttributeError):
            stats.total_entries = 1  # type: ignore[misc]


# =========================================================================
#  BunchGenerationTemplateCache tests
# =========================================================================


class TestBunchGenerationTemplateCache:
    """模板缓存测试 / Template cache tests."""

    def test_empty_cache(self) -> None:
        """空缓存 / Empty cache."""
        cache = BunchGenerationTemplateCache()
        assert cache.entries == ()
        assert cache.max_size == 100

    def test_get_miss(self) -> None:
        """缓存未命中 / Cache miss."""
        cache = BunchGenerationTemplateCache()
        assert cache.get("nonexistent") is None

    def test_put_and_get(self) -> None:
        """存取操作 / Put and get."""
        cache = BunchGenerationTemplateCache()
        bunches = (GeneratedBunch(bunch_key="b0"),)
        cache = cache.put(
            cache_key="k1",
            bunches=bunches,
            item_count=3,
        )
        result = cache.get("k1")
        assert result is not None
        assert len(result) == 1
        assert result[0].bunch_key == "b0"

    def test_contains(self) -> None:
        """包含检查 / Contains check."""
        cache = BunchGenerationTemplateCache()
        bunches = (GeneratedBunch(bunch_key="b0"),)
        cache = cache.put(
            cache_key="k1",
            bunches=bunches,
            item_count=1,
        )
        assert cache.contains("k1") is True
        assert cache.contains("k2") is False

    def test_record_hit(self) -> None:
        """记录命中 / Record hit."""
        cache = BunchGenerationTemplateCache()
        bunches = (GeneratedBunch(bunch_key="b0"),)
        cache = cache.put(
            cache_key="k1",
            bunches=bunches,
            item_count=1,
        )
        cache = cache.record_hit("k1")
        assert cache.get("k1") is not None
        stats = cache.stats()
        assert stats.total_hits == 1

    def test_record_hit_nonexistent_key(self) -> None:
        """对不存在的键记录命中 / Record hit for missing key."""
        cache = BunchGenerationTemplateCache()
        bunches = (GeneratedBunch(bunch_key="b0"),)
        cache = cache.put(
            cache_key="k1",
            bunches=bunches,
            item_count=1,
        )
        cache = cache.record_hit("nonexistent")
        stats = cache.stats()
        assert stats.total_hits == 0

    def test_stats_empty(self) -> None:
        """空缓存统计 / Stats on empty cache."""
        cache = BunchGenerationTemplateCache()
        stats = cache.stats()
        assert stats.total_entries == 0
        assert stats.total_hits == 0
        assert stats.hit_rate == pytest.approx(0.0)

    def test_stats_with_entries(self) -> None:
        """有条目时的统计 / Stats with entries."""
        cache = BunchGenerationTemplateCache()
        bunches = (GeneratedBunch(bunch_key="b0"),)
        cache = cache.put(
            cache_key="k1",
            bunches=bunches,
            item_count=1,
        )
        cache = cache.put(
            cache_key="k2",
            bunches=bunches,
            item_count=2,
        )
        cache = cache.record_hit("k1")
        cache = cache.record_hit("k1")
        stats = cache.stats()
        assert stats.total_entries == 2
        assert stats.total_hits == 2
        assert stats.hit_rate == pytest.approx(1.0)

    def test_compute_cache_key(self) -> None:
        """计算缓存键 / Compute cache key."""
        key = BunchGenerationTemplateCache.compute_cache_key(
            ("c", "a", "b"),
        )
        assert key == "a|b|c"

    def test_compute_cache_key_empty(self) -> None:
        """空键计算 / Empty key computation."""
        key = BunchGenerationTemplateCache.compute_cache_key(())
        assert key == ""

    def test_compute_cache_key_sorted(self) -> None:
        """缓存键排序 / Cache key sorted."""
        k1 = BunchGenerationTemplateCache.compute_cache_key(
            ("b", "a"),
        )
        k2 = BunchGenerationTemplateCache.compute_cache_key(
            ("a", "b"),
        )
        assert k1 == k2

    def test_clear(self) -> None:
        """清空缓存 / Clear cache."""
        cache = BunchGenerationTemplateCache(max_size=50)
        bunches = (GeneratedBunch(bunch_key="b0"),)
        cache = cache.put(
            cache_key="k1",
            bunches=bunches,
            item_count=1,
        )
        cleared = cache.clear()
        assert cleared.entries == ()
        assert cleared.max_size == 50

    def test_max_size_trimming(self) -> None:
        """超出最大容量裁剪 / Trimming on max size."""
        cache = BunchGenerationTemplateCache(max_size=2)
        bunches = (GeneratedBunch(bunch_key="b0"),)
        cache = cache.put(
            cache_key="k1",
            bunches=bunches,
            item_count=1,
        )
        cache = cache.put(
            cache_key="k2",
            bunches=bunches,
            item_count=2,
        )
        cache = cache.put(
            cache_key="k3",
            bunches=bunches,
            item_count=3,
        )
        assert len(cache.entries) == 2
        assert cache.contains("k1") is False
        assert cache.contains("k3") is True

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        cache = BunchGenerationTemplateCache()
        with pytest.raises(AttributeError):
            cache.max_size = 200  # type: ignore[misc]
