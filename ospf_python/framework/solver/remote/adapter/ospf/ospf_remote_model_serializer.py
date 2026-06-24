"""OSPF 远程模型序列化器 / OSPF remote model serializer.

提供 OSPF 模型的序列化和反序列化。
Provides serialization and deserialization of OSPF models.
"""

from __future__ import annotations

import abc
from typing import Any


class OspfRemoteModelSerializer(abc.ABC):
    """OSPF 远程模型序列化器 / OSPF remote model serializer.

    将优化模型序列化为传输格式，以及从传输格式反序列化。
    Serializes optimization models to transfer format and
    deserializes from transfer format.
    """

    @abc.abstractmethod
    def serialize(self, model: object) -> bytes:
        """序列化模型 / Serialize model.

        Args:
            model: 优化模型 / The optimization model.

        Returns:
            序列化后的字节数据 / The serialized bytes.
        """
        ...

    @abc.abstractmethod
    def deserialize(self, data: bytes) -> Any:
        """反序列化模型 / Deserialize model.

        Args:
            data: 序列化数据 / The serialized data.

        Returns:
            反序列化后的模型 / The deserialized model.
        """
        ...
