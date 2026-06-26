"""航空器异步服务接口 / Aircraft async service interface.

航空器领域异步操作的抽象基类。
Abstract base class for async operations in the
aircraft domain.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft import Aircraft
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft_aggregation import (
        AircraftAggregation,
    )
    from examples.framework_demo.demo2.domain.aircraft.model.aircraft_model import (
        AircraftModel,
    )
    from ospf_python.utils.error.error import Error
    from ospf_python.utils.functional.result import Result


class AircraftServiceAsync(ABC):
    """航空器异步服务 / Aircraft async service.

    定义航空器领域中需要异步执行的操作接口，包括
    查询、验证和模型加载等功能。
    Defines async operation interfaces in the aircraft domain,
    including query, validation, and model loading.
    """

    @abstractmethod
    async def get_aircraft(
        self,
        registration: str,
    ) -> Result[Aircraft, str, Error[str]]:
        """根据注册号获取航空器 / Get aircraft by registration.

        Args:
            registration: 航空器注册号 / Aircraft registration number.

        Returns:
            包含航空器的结果 / Result containing aircraft.
        """
        ...

    @abstractmethod
    async def get_all_aircraft(self) -> Result[AircraftAggregation, str, Error[str]]:
        """获取所有航空器 / Get all aircraft.

        Returns:
            包含航空器聚合的结果 / Result containing aircraft aggregation.
        """
        ...

    @abstractmethod
    async def get_aircraft_model(
        self,
        registration: str,
    ) -> Result[AircraftModel, str, Error[str]]:
        """获取航空器完整模型 / Get full aircraft model.

        加载航空器实体及其关联的约束、甲板、集装器等信息。
        Loads the aircraft entity and its associated constraints,
        decks, ULDs, etc.

        Args:
            registration: 航空器注册号 / Aircraft registration number.

        Returns:
            包含航空器模型的结果 / Result containing aircraft model.
        """
        ...

    @abstractmethod
    async def validate_aircraft(
        self,
        aircraft: Aircraft,
    ) -> Result[bool, str, Error[str]]:
        """验证航空器数据有效性 / Validate aircraft data.

        检查航空器参数是否满足业务规则。
        Checks whether aircraft parameters satisfy business rules.

        Args:
            aircraft: 待验证的航空器 / Aircraft to validate.

        Returns:
            验证结果 / Validation result.
        """
        ...

    @abstractmethod
    async def save_aircraft(
        self,
        aircraft: Aircraft,
    ) -> Result[None, str, Error[str]]:
        """保存航空器 / Save aircraft.

        Args:
            aircraft: 待保存的航空器 / Aircraft to save.

        Returns:
            操作结果 / Operation result.
        """
        ...

    @abstractmethod
    async def delete_aircraft(
        self,
        registration: str,
    ) -> Result[None, str, Error[str]]:
        """删除航空器 / Delete aircraft.

        Args:
            registration: 待删除航空器的注册号 / Registration to delete.

        Returns:
            操作结果 / Operation result.
        """
        ...
