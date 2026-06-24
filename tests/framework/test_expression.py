"""Tests for persistence expression module.

持久化表达式模块测试。
"""

from __future__ import annotations

import abc

import pytest

from ospf_python.framework.persistence.expression.column_binder import ColumnBinder
from ospf_python.framework.persistence.expression.package import (
    ColumnBinder as PackageColumnBinder,
)
from ospf_python.framework.persistence.expression.package import (
    SortBy as PackageSortBy,
)
from ospf_python.framework.persistence.expression.package import (
    UnsupportedPredicatePolicy as PackagePolicy,
)
from ospf_python.framework.persistence.expression.persistence_field_resolver import (
    PersistenceFieldResolver,
)
from ospf_python.framework.persistence.expression.predicate_annotations import (
    PredicateAnnotations,
)
from ospf_python.framework.persistence.expression.repository_api import RepositoryApi
from ospf_python.framework.persistence.expression.scalar_function_dsl import (
    ScalarFunctionDsl,
)
from ospf_python.framework.persistence.expression.sort_by import SortBy
from ospf_python.framework.persistence.expression.unsupported_predicate_policy import (
    UnsupportedPredicatePolicy,
)
from ospf_python.framework.persistence.expression.update_assignment import (
    UpdateAssignment,
)

# -- ColumnBinder ----------------------------------------------------


class TestColumnBinderExtra:
    """Test ColumnBinder extra edge cases."""

    def test_create_non_primary(self) -> None:
        """非主键创建 / Non-primary creation."""
        b = ColumnBinder(
            column_name="user_id",
            field_name="userId",
        )
        assert b.is_primary is False

    def test_create_primary(self) -> None:
        """主键创建 / Primary creation."""
        b = ColumnBinder(
            column_name="id",
            field_name="id",
            is_primary=True,
        )
        assert b.is_primary is True

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        b = ColumnBinder(column_name="c", field_name="f")
        with pytest.raises(AttributeError):
            b.column_name = "d"  # type: ignore[misc]

    def test_equality(self) -> None:
        """相等性 / Equality."""
        a = ColumnBinder(column_name="c", field_name="f")
        b = ColumnBinder(column_name="c", field_name="f")
        assert a == b


# -- PersistenceFieldResolver ----------------------------------------


class TestPersistenceFieldResolverExtra:
    """Test PersistenceFieldResolver extra edge cases."""

    def test_is_abstract(self) -> None:
        """是抽象类 / Is abstract class."""
        assert issubclass(PersistenceFieldResolver, abc.ABC)

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate."""
        with pytest.raises(TypeError):
            PersistenceFieldResolver()  # type: ignore[abstract]


# -- PredicateAnnotations --------------------------------------------


class TestPredicateAnnotationsExtra:
    """Test PredicateAnnotations extra edge cases."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        ann = PredicateAnnotations()
        assert ann.description == ""
        assert ann.category == ""
        assert ann.metadata is None

    def test_with_metadata(self) -> None:
        """带元数据 / With metadata."""
        ann = PredicateAnnotations(
            description="desc",
            category="cat",
            metadata={"k": "v"},
        )
        assert ann.metadata is not None
        assert ann.metadata["k"] == "v"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ann = PredicateAnnotations()
        with pytest.raises(AttributeError):
            ann.description = "x"  # type: ignore[misc]


# -- RepositoryApi ---------------------------------------------------


class TestRepositoryApiExtra:
    """Test RepositoryApi extra edge cases."""

    def test_is_abstract(self) -> None:
        """是抽象类 / Is abstract class."""
        assert issubclass(RepositoryApi, abc.ABC)

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate."""
        with pytest.raises(TypeError):
            RepositoryApi()  # type: ignore[abstract]


# -- ScalarFunctionDsl -----------------------------------------------


class TestScalarFunctionDslExtra:
    """Test ScalarFunctionDsl extra edge cases."""

    def test_sum_function(self) -> None:
        """SUM 函数 / SUM function."""
        dsl = ScalarFunctionDsl(function_name="SUM")
        assert dsl.function_name == "SUM"
        assert dsl.arguments == ()

    def test_coalesce_with_args(self) -> None:
        """COALESCE 带参数 / COALESCE with args."""
        dsl = ScalarFunctionDsl(
            function_name="COALESCE",
            arguments=("col_a", 0),
            alias="result",
        )
        assert len(dsl.arguments) == 2

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        dsl = ScalarFunctionDsl(function_name="X")
        with pytest.raises(AttributeError):
            dsl.function_name = "Y"  # type: ignore[misc]


# -- SortBy ----------------------------------------------------------


class TestSortByExtra:
    """Test SortBy extra edge cases."""

    def test_ascending(self) -> None:
        """升序 / Ascending."""
        sort = SortBy(field_name="name")
        assert sort.ascending is True

    def test_descending(self) -> None:
        """降序 / Descending."""
        sort = SortBy(field_name="date", ascending=False)
        assert sort.ascending is False

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        sort = SortBy(field_name="f")
        with pytest.raises(AttributeError):
            sort.field_name = "g"  # type: ignore[misc]


# -- UnsupportedPredicatePolicy --------------------------------------


class TestUnsupportedPredicatePolicyExtra:
    """Test UnsupportedPredicatePolicy extra edge cases."""

    def test_ignore(self) -> None:
        """忽略 / Ignore."""
        assert UnsupportedPredicatePolicy.IGNORE.value == 0

    def test_warn(self) -> None:
        """警告 / Warn."""
        assert UnsupportedPredicatePolicy.WARN.value == 1

    def test_error(self) -> None:
        """报错 / Error."""
        assert UnsupportedPredicatePolicy.ERROR.value == 2


# -- UpdateAssignment ------------------------------------------------


class TestUpdateAssignmentExtra:
    """Test UpdateAssignment extra edge cases."""

    def test_string_value(self) -> None:
        """字符串值 / String value."""
        ua = UpdateAssignment(field_name="name", value="Alice")
        assert ua.value == "Alice"

    def test_numeric_value(self) -> None:
        """数值 / Numeric value."""
        ua = UpdateAssignment(field_name="age", value=30)
        assert ua.value == 30

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ua = UpdateAssignment(field_name="f", value="v")
        with pytest.raises(AttributeError):
            ua.field_name = "g"  # type: ignore[misc]


# -- Package exports -------------------------------------------------


class TestPackageExportsExtra:
    """Test package exports."""

    def test_column_binder_exported(self) -> None:
        """ColumnBinder 已导出 / ColumnBinder exported."""
        assert PackageColumnBinder is ColumnBinder

    def test_sort_by_exported(self) -> None:
        """SortBy 已导出 / SortBy exported."""
        assert PackageSortBy is SortBy

    def test_policy_exported(self) -> None:
        """Policy 已导出 / Policy exported."""
        assert PackagePolicy is UnsupportedPredicatePolicy
