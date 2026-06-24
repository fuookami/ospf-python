"""Tests for persistence/expression module.

持久化/表达式模块测试。
"""

from __future__ import annotations

import abc
from datetime import UTC, datetime

import pytest

from ospf_python.framework.persistence.expression.column_binder import ColumnBinder
from ospf_python.framework.persistence.expression.predicate_annotations import (
    PredicateAnnotations,
)
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
from ospf_python.framework.persistence.log_record import PersistenceLogRecord
from ospf_python.framework.persistence.persistence_api_controller import (
    PersistenceApiController,
)
from ospf_python.framework.persistence.request import Request
from ospf_python.framework.persistence.request_record import RequestRecord

# -- PersistenceLogRecord --------------------------------------------


class TestPersistenceLogRecordExtra:
    """Test PersistenceLogRecord edge cases."""

    def test_success_default(self) -> None:
        """默认成功 / Default success."""
        ts = datetime.now(UTC)
        rec = PersistenceLogRecord(
            operation="INSERT",
            entity_name="User",
            timestamp=ts,
        )
        assert rec.success is True

    def test_failure(self) -> None:
        """失败记录 / Failure record."""
        ts = datetime.now(UTC)
        rec = PersistenceLogRecord(
            operation="DELETE",
            entity_name="Order",
            timestamp=ts,
            success=False,
        )
        assert rec.success is False

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ts = datetime.now(UTC)
        rec = PersistenceLogRecord(
            operation="INSERT",
            entity_name="User",
            timestamp=ts,
        )
        with pytest.raises(AttributeError):
            rec.operation = "UPDATE"  # type: ignore[misc]


# -- PersistenceApiController ----------------------------------------


class TestPersistenceApiControllerExtra:
    """Test PersistenceApiController edge cases."""

    def test_is_abstract(self) -> None:
        """是抽象类 / Is abstract class."""
        assert issubclass(PersistenceApiController, abc.ABC)

    def test_cannot_instantiate(self) -> None:
        """不能直接实例化 / Cannot instantiate."""
        with pytest.raises(TypeError):
            PersistenceApiController()  # type: ignore[abstract]

    def test_has_save(self) -> None:
        """有 save 方法 / Has save method."""
        assert hasattr(PersistenceApiController, "save")

    def test_has_find_by_id(self) -> None:
        """有 find_by_id 方法 / Has find_by_id method."""
        assert hasattr(PersistenceApiController, "find_by_id")

    def test_has_delete(self) -> None:
        """有 delete 方法 / Has delete method."""
        assert hasattr(PersistenceApiController, "delete")

    def test_has_find_all(self) -> None:
        """有 find_all 方法 / Has find_all method."""
        assert hasattr(PersistenceApiController, "find_all")


# -- Request ---------------------------------------------------------


class TestRequestExtra:
    """Test Request edge cases."""

    def test_create_with_defaults(self) -> None:
        """默认值创建 / Create with defaults."""
        req = Request(operation="SELECT", data={"id": 1})
        assert req.entity_name == ""

    def test_create_full(self) -> None:
        """全字段创建 / Full creation."""
        req = Request(
            operation="INSERT",
            data={"name": "Alice"},
            entity_name="User",
        )
        assert req.operation == "INSERT"
        assert req.entity_name == "User"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        req = Request(operation="SELECT", data={})
        with pytest.raises(AttributeError):
            req.operation = "UPDATE"  # type: ignore[misc]


# -- RequestRecord ---------------------------------------------------


class TestRequestRecordExtra:
    """Test RequestRecord edge cases."""

    def test_create(self) -> None:
        """创建记录 / Create record."""
        ts = datetime.now(UTC)
        rec = RequestRecord(
            request_id="r-001",
            operation="UPDATE",
            timestamp=ts,
            params={"table": "users"},
        )
        assert rec.request_id == "r-001"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ts = datetime.now(UTC)
        rec = RequestRecord(
            request_id="r-001",
            operation="UPDATE",
            timestamp=ts,
            params={},
        )
        with pytest.raises(AttributeError):
            rec.request_id = "r-002"  # type: ignore[misc]


# -- ColumnBinder ----------------------------------------------------


class TestColumnBinderExtra:
    """Test ColumnBinder edge cases."""

    def test_default_not_primary(self) -> None:
        """默认非主键 / Default not primary."""
        binder = ColumnBinder(column_name="col", field_name="field")
        assert binder.is_primary is False

    def test_primary_key(self) -> None:
        """主键 / Primary key."""
        binder = ColumnBinder(
            column_name="id",
            field_name="id",
            is_primary=True,
        )
        assert binder.is_primary is True

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        binder = ColumnBinder(column_name="c", field_name="f")
        with pytest.raises(AttributeError):
            binder.column_name = "d"  # type: ignore[misc]


# -- SortBy ----------------------------------------------------------


class TestSortByExtra:
    """Test SortBy edge cases."""

    def test_default_ascending(self) -> None:
        """默认升序 / Default ascending."""
        sort = SortBy(field_name="name")
        assert sort.ascending is True

    def test_descending(self) -> None:
        """降序 / Descending."""
        sort = SortBy(field_name="created_at", ascending=False)
        assert sort.ascending is False

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        sort = SortBy(field_name="name")
        with pytest.raises(AttributeError):
            sort.field_name = "other"  # type: ignore[misc]


# -- ScalarFunctionDsl -----------------------------------------------


class TestScalarFunctionDslExtra:
    """Test ScalarFunctionDsl edge cases."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        dsl = ScalarFunctionDsl(function_name="COUNT")
        assert dsl.arguments == ()
        assert dsl.alias == ""

    def test_with_arguments(self) -> None:
        """带参数 / With arguments."""
        dsl = ScalarFunctionDsl(
            function_name="COALESCE",
            arguments=("col_a", 0),
            alias="result",
        )
        assert dsl.arguments == ("col_a", 0)
        assert dsl.alias == "result"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        dsl = ScalarFunctionDsl(function_name="SUM")
        with pytest.raises(AttributeError):
            dsl.function_name = "AVG"  # type: ignore[misc]


# -- UpdateAssignment ------------------------------------------------


class TestUpdateAssignmentExtra:
    """Test UpdateAssignment edge cases."""

    def test_create(self) -> None:
        """创建赋值 / Create assignment."""
        ua = UpdateAssignment(field_name="status", value="active")
        assert ua.field_name == "status"
        assert ua.value == "active"

    def test_numeric_value(self) -> None:
        """数值赋值 / Numeric value."""
        ua = UpdateAssignment(field_name="count", value=42)
        assert ua.value == 42

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ua = UpdateAssignment(field_name="f", value="v")
        with pytest.raises(AttributeError):
            ua.field_name = "g"  # type: ignore[misc]


# -- PredicateAnnotations --------------------------------------------


class TestPredicateAnnotationsExtra:
    """Test PredicateAnnotations edge cases."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        ann = PredicateAnnotations()
        assert ann.description == ""
        assert ann.category == ""
        assert ann.metadata is None

    def test_with_values(self) -> None:
        """带值 / With values."""
        ann = PredicateAnnotations(
            description="filter",
            category="WHERE",
            metadata={"key": "val"},
        )
        assert ann.description == "filter"
        assert ann.metadata is not None


# -- UnsupportedPredicatePolicy --------------------------------------


class TestUnsupportedPredicatePolicyExtra:
    """Test UnsupportedPredicatePolicy edge cases."""

    def test_ignore(self) -> None:
        """忽略策略 / Ignore policy."""
        assert UnsupportedPredicatePolicy.IGNORE.value == 0

    def test_warn(self) -> None:
        """警告策略 / Warn policy."""
        assert UnsupportedPredicatePolicy.WARN.value == 1

    def test_error(self) -> None:
        """报错策略 / Error policy."""
        assert UnsupportedPredicatePolicy.ERROR.value == 2

    def test_is_enum(self) -> None:
        """是枚举 / Is enum."""
        import enum

        assert issubclass(UnsupportedPredicatePolicy, enum.Enum)
