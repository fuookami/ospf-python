"""Tests for remote solver (domain/client/port/adapter).

远程求解器测试。
"""

from __future__ import annotations

import abc
from datetime import UTC, datetime

import pytest

from ospf_python.framework.solver.remote.client.remote_solver_runtime_config import (
    RemoteSolverRuntimeConfig,
)
from ospf_python.framework.solver.remote.domain.errors import (
    ConnectionError,
    RemoteSolverError,
)
from ospf_python.framework.solver.remote.domain.errors import (
    TimeoutError as RemoteTimeoutError,
)
from ospf_python.framework.solver.remote.domain.execution_models import (
    ExecutionRequest,
    ExecutionResponse,
)
from ospf_python.framework.solver.remote.domain.normalized_models import (
    NormalizedModel,
    NormalizedResult,
)
from ospf_python.framework.solver.remote.domain.serialized_models import (
    SerializedModel,
    SerializedResult,
)
from ospf_python.framework.solver.remote.domain.storage_models import (
    StorageObject,
    StorageReference,
)
from ospf_python.framework.solver.remote.domain.task_models import (
    TaskInfo,
    TaskResult,
)
from ospf_python.framework.solver.remote.domain.value_types import (
    SolverCapability,
    SolverEndpoint,
)
from ospf_python.framework.solver.remote.port.object_storage_port import (
    ObjectStoragePort,
)
from ospf_python.framework.solver.remote.port.solver_execution_port import (
    SolverExecutionPort,
)

# -- SolverEndpoint --------------------------------------------------


class TestSolverEndpointExtra:
    """Test SolverEndpoint edge cases."""

    def test_default_protocol(self) -> None:
        """默认协议 / Default protocol."""
        ep = SolverEndpoint(host="localhost", port=8080)
        assert ep.protocol == "https"

    def test_custom_protocol(self) -> None:
        """自定义协议 / Custom protocol."""
        ep = SolverEndpoint(host="localhost", port=8080, protocol="http")
        assert ep.protocol == "http"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        ep = SolverEndpoint(host="h", port=1)
        with pytest.raises(AttributeError):
            ep.host = "x"  # type: ignore[misc]


# -- SolverCapability ------------------------------------------------


class TestSolverCapabilityExtra:
    """Test SolverCapability edge cases."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        cap = SolverCapability(solver_type="LP")
        assert cap.supports_integer is False
        assert cap.supports_quadratic is False
        assert cap.max_variables == 0

    def test_full_capability(self) -> None:
        """全能力 / Full capability."""
        cap = SolverCapability(
            solver_type="MIP",
            supports_integer=True,
            supports_quadratic=True,
            max_variables=1000000,
        )
        assert cap.supports_integer is True
        assert cap.max_variables == 1000000


# -- Error types -----------------------------------------------------


class TestRemoteSolverErrors:
    """Test remote solver error types."""

    def test_solver_error_defaults(self) -> None:
        """求解器错误默认值 / Solver error defaults."""
        err = RemoteSolverError(code=500, message="fail")
        assert err.task_id == ""

    def test_solver_error_full(self) -> None:
        """求解器错误全字段 / Solver error full."""
        err = RemoteSolverError(code=400, message="bad", task_id="t1")
        assert err.code == 400
        assert err.task_id == "t1"

    def test_connection_error(self) -> None:
        """连接错误 / Connection error."""
        err = ConnectionError(url="https://x.com", message="refused")
        assert err.url == "https://x.com"

    def test_timeout_error(self) -> None:
        """超时错误 / Timeout error."""
        err = RemoteTimeoutError(timeout_seconds=30.0, operation="solve")
        assert err.timeout_seconds == pytest.approx(30.0)


# -- Execution models ------------------------------------------------


class TestExecutionModelsExtra:
    """Test execution model edge cases."""

    def test_request_with_options(self) -> None:
        """带选项请求 / Request with options."""
        req = ExecutionRequest(
            model_data=b"data",
            solver_type="LP",
            options={"tolerance": 1e-6, "timeout": 60},
        )
        assert req.options["tolerance"] == pytest.approx(1e-6)

    def test_response_defaults(self) -> None:
        """响应默认值 / Response defaults."""
        resp = ExecutionResponse(task_id="t-1", status="PENDING")
        assert resp.message == ""

    def test_response_with_message(self) -> None:
        """响应带消息 / Response with message."""
        resp = ExecutionResponse(
            task_id="t-1",
            status="RUNNING",
            message="Processing",
        )
        assert resp.message == "Processing"


# -- Normalized models -----------------------------------------------


class TestNormalizedModelsExtra:
    """Test normalized model edge cases."""

    def test_model_with_multiple_vars(self) -> None:
        """多变量模型 / Multi-variable model."""
        model = NormalizedModel(
            variables=(
                {"name": "x"},
                {"name": "y"},
            ),
            constraints=({"name": "c1"},),
            objective={"sense": "min"},
        )
        assert len(model.variables) == 2

    def test_result_values(self) -> None:
        """结果值 / Result values."""
        result = NormalizedResult(
            status="OPTIMAL",
            objective_value=42.5,
            variable_values={"x": 1.0, "y": 2.5},
        )
        assert result.variable_values["y"] == pytest.approx(2.5)

    def test_model_frozen(self) -> None:
        """模型不可变 / Model frozen."""
        model = NormalizedModel(
            variables=(),
            constraints=(),
            objective={},
        )
        with pytest.raises(AttributeError):
            model.objective = {}  # type: ignore[misc]


# -- Serialized models -----------------------------------------------


class TestSerializedModelsExtra:
    """Test serialized model edge cases."""

    def test_model_defaults(self) -> None:
        """模型默认值 / Model defaults."""
        sm = SerializedModel(format="json", data=b"{}")
        assert sm.checksum == ""

    def test_model_with_checksum(self) -> None:
        """模型带校验和 / Model with checksum."""
        sm = SerializedModel(
            format="protobuf",
            data=b"\x00",
            checksum="abc123",
        )
        assert sm.checksum == "abc123"

    def test_result_with_task_id(self) -> None:
        """结果带任务 ID / Result with task ID."""
        sr = SerializedResult(format="json", data=b"{}", task_id="t1")
        assert sr.task_id == "t1"


# -- Storage models --------------------------------------------------


class TestStorageModelsExtra:
    """Test storage model edge cases."""

    def test_object_defaults(self) -> None:
        """对象默认值 / Object defaults."""
        ts = datetime.now(UTC)
        obj = StorageObject(key="k", size=100, created_at=ts)
        assert obj.content_type == "application/octet-stream"

    def test_object_custom_content_type(self) -> None:
        """自定义内容类型 / Custom content type."""
        ts = datetime.now(UTC)
        obj = StorageObject(
            key="k",
            size=100,
            created_at=ts,
            content_type="application/json",
        )
        assert obj.content_type == "application/json"

    def test_reference(self) -> None:
        """存储引用 / Storage reference."""
        ref = StorageReference(bucket="b", key="k")
        assert ref.bucket == "b"
        assert ref.key == "k"


# -- Task models -----------------------------------------------------


class TestTaskModelsExtra:
    """Test task model edge cases."""

    def test_task_info(self) -> None:
        """任务信息 / Task info."""
        ts = datetime.now(UTC)
        info = TaskInfo(
            task_id="t-001",
            status="RUNNING",
            created_at=ts,
            updated_at=ts,
        )
        assert info.task_id == "t-001"
        assert info.status == "RUNNING"

    def test_task_result_success(self) -> None:
        """任务成功 / Task success."""
        result = TaskResult(task_id="t-001", success=True)
        assert result.success is True
        assert result.result_data == b""
        assert result.error_message == ""

    def test_task_result_failure(self) -> None:
        """任务失败 / Task failure."""
        result = TaskResult(
            task_id="t-001",
            success=False,
            error_message="timeout",
        )
        assert result.success is False
        assert result.error_message == "timeout"

    def test_task_result_with_data(self) -> None:
        """任务带数据 / Task with data."""
        result = TaskResult(
            task_id="t-001",
            success=True,
            result_data=b"result",
        )
        assert result.result_data == b"result"


# -- Runtime config --------------------------------------------------


class TestRuntimeConfigExtra:
    """Test runtime config edge cases."""

    def test_defaults(self) -> None:
        """默认值 / Default values."""
        cfg = RemoteSolverRuntimeConfig(base_url="https://solver.com")
        assert cfg.timeout_seconds == pytest.approx(300.0)
        assert cfg.max_retries == 3
        assert cfg.api_key == ""

    def test_custom_values(self) -> None:
        """自定义值 / Custom values."""
        cfg = RemoteSolverRuntimeConfig(
            base_url="https://solver.com",
            timeout_seconds=60.0,
            max_retries=5,
            api_key="key-123",
        )
        assert cfg.timeout_seconds == pytest.approx(60.0)
        assert cfg.max_retries == 5
        assert cfg.api_key == "key-123"

    def test_frozen(self) -> None:
        """不可变性 / Immutability."""
        cfg = RemoteSolverRuntimeConfig(base_url="https://x.com")
        with pytest.raises(AttributeError):
            cfg.base_url = "https://y.com"  # type: ignore[misc]


# -- Ports (ABCs) ----------------------------------------------------


class TestPortsExtra:
    """Test port ABCs."""

    def test_object_storage_port_is_abstract(self) -> None:
        """对象存储端口是抽象类 / ObjectStoragePort is ABC."""
        assert issubclass(ObjectStoragePort, abc.ABC)

    def test_solver_execution_port_is_abstract(self) -> None:
        """求解器执行端口是抽象类 / SolverExecutionPort is ABC."""
        assert issubclass(SolverExecutionPort, abc.ABC)

    def test_execution_port_has_submit(self) -> None:
        """执行端口有 submit / Has submit."""
        assert hasattr(SolverExecutionPort, "submit")

    def test_execution_port_has_poll(self) -> None:
        """执行端口有 poll / Has poll."""
        assert hasattr(SolverExecutionPort, "poll")

    def test_execution_port_has_retrieve(self) -> None:
        """执行端口有 retrieve / Has retrieve."""
        assert hasattr(SolverExecutionPort, "retrieve")

    def test_execution_port_has_cancel(self) -> None:
        """执行端口有 cancel / Has cancel."""
        assert hasattr(SolverExecutionPort, "cancel")
