"""模型文件格式枚举 / Model file format enumeration.

定义模型导出支持的文件格式。
Defines the file formats supported for model export.
"""

from __future__ import annotations

import enum


class ModelFileFormat(enum.Enum):
    """模型文件格式 / Model file format.

    用于将模型导出到磁盘时指定目标格式。
    Used to specify the target format when exporting
    a model to disk.

    Attributes:
        value: 格式标识字符串 / The format identifier string.
    """

    LP = "lp"
    """LP 格式 / LP format."""

    MPS = "mps"
    """MPS 格式 / MPS format."""

    MPS_GZ = "mps.gz"
    """压缩 MPS 格式 / Compressed MPS format."""
