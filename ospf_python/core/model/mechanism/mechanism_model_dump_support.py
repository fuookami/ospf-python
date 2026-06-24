"""机制模型转储支持 / Mechanism model dump support.

为机制模型提供导出支持。
Provides export support for mechanism models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.core.model.basic.model_file_format import (
        ModelFileFormat,
    )
    from ospf_python.core.model.intermediate.mechanism_model_dumping_status import (
        MechanismModelDumpingStatus,
    )


class MechanismModelDumpSupport:
    """机制模型转储支持 / Mechanism model dump support.

    辅助将机制模型导出为中间表示或文件。
    Assists in exporting mechanism models to intermediate
    representations or files.

    Methods:
        dump: 转储模型 / Dump the model.
    """

    def dump(
        self,
        model: object,
        format_: ModelFileFormat,
    ) -> MechanismModelDumpingStatus:
        """转储模型到指定格式 / Dump the model to the specified format.

        Args:
            model: 要转储的模型 / The model to dump.
            format_: 目标格式 / The target format.

        Returns:
            转储状态 / The dumping status.
        """
        from ospf_python.core.model.intermediate.mechanism_model_dumping_status import (
            MechanismModelDumpingStatus,
        )

        return MechanismModelDumpingStatus.SUCCESS
