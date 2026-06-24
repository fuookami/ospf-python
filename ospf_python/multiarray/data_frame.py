"""列式数据结构与构建器。

Columnar data structure and builder.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

# T: 元素类型 / Element type
T = TypeVar("T")


@dataclass(frozen=True)
class NullableValue(Generic[T]):
    """可空值包装器。

    Nullable value wrapper.

    Attributes:
        value: 包装的值，可能为 None。
            Wrapped value, may be None.
    """

    value: T | None

    @property
    def is_null(self) -> bool:
        """判断值是否为 None。/ Check if value is None."""
        return self.value is None

    @property
    def is_present(self) -> bool:
        """判断值是否存在。/ Check if value is present."""
        return self.value is not None

    def or_else(self, default: T) -> T:
        """若值为 None 则返回默认值。

        Return default if value is None.

        Args:
            default: 默认值。/ Default value.

        Returns:
            值或默认值。/ Value or default.
        """
        if self.value is None:
            return default
        return self.value


class DataFrame(Generic[T]):
    """列式数据结构。

    Columnar data structure.

    数据按列存储，每列有名称和等长的值列表。
    Data is stored by columns; each column has a name
    and an equal-length value list.

    Attributes:
        _columns: 列名到值列表的映射。
            Column name to value list mapping.
    """

    def __init__(self) -> None:
        """初始化空 DataFrame。/ Initialize empty DataFrame."""
        self._columns: dict[str, list[T | None]] = {}

    @property
    def row_count(self) -> int:
        """获取行数。/ Get row count."""
        if not self._columns:
            return 0
        return len(next(iter(self._columns.values())))

    def columns(self) -> list[str]:
        """获取所有列名。

        Get all column names.

        Returns:
            列名列表。/ List of column names.
        """
        return list(self._columns.keys())

    def rows(self) -> int:
        """获取行数。/ Get the number of rows."""
        return self.row_count

    def get(self, column: str, row: int) -> T | None:
        """获取指定列和行的值。

        Get the value at the specified column and row.

        Args:
            column: 列名。/ Column name.
            row: 行索引。/ Row index.

        Returns:
            单元格值或 None。/ Cell value or None.
        """
        if column not in self._columns:
            return None
        col_data = self._columns[column]
        if row < 0 or row >= len(col_data):
            return None
        return col_data[row]

    def add_column(
        self,
        name: str,
        values: Sequence[T | None],
    ) -> None:
        """添加新列。

        Add a new column.

        如果 DataFrame 已有数据，新列长度必须匹配行数。
        If the DataFrame already has data, the new column
        length must match the row count.

        Args:
            name: 列名。/ Column name.
            values: 列值序列。/ Column value sequence.
        """
        existing_rows = self.row_count
        value_list = list(values)

        # 如果已有数据，补齐或截断到正确长度
        # If data exists, pad or truncate to correct length
        if existing_rows > 0 and len(value_list) < existing_rows:
            value_list.extend([None] * (existing_rows - len(value_list)))
        elif existing_rows == 0 and value_list:
            # 首列设置行数；其他列补齐 None
            # First column sets row count; pad others with None
            for _col_name, col_data in self._columns.items():
                if len(col_data) < len(value_list):
                    col_data.extend([None] * (len(value_list) - len(col_data)))

        self._columns[name] = value_list

    def to_list(self) -> list[dict[str, T | None]]:
        """转换为字典列表（每行一个字典）。

        Convert to a list of dicts (one dict per row).

        Returns:
            字典列表。/ List of dicts.
        """
        if not self._columns:
            return []
        result: list[dict[str, T | None]] = []
        num_rows = self.row_count
        for r in range(num_rows):
            row_dict: dict[str, T | None] = {}
            for col_name, col_data in self._columns.items():
                row_dict[col_name] = col_data[r] if r < len(col_data) else None
            result.append(row_dict)
        return result


class DataFrameBuilder(Generic[T]):
    """DataFrame 流式构建器。

    Fluent builder for DataFrame.

    使用示例 / Usage example::

        df = (
            DataFrameBuilder()
            .add_column("name", ["Alice", "Bob"])
            .add_column("age", [30, 25])
            .build()
        )

    Attributes:
        _columns: 待构建的列数据。
            Column data to be built.
    """

    def __init__(self) -> None:
        """初始化构建器。/ Initialize builder."""
        self._columns: dict[str, list[T | None]] = {}

    def add_column(
        self,
        name: str,
        values: Sequence[T | None],
    ) -> DataFrameBuilder[T]:
        """添加列（链式调用）。

        Add a column (for chaining).

        Args:
            name: 列名。/ Column name.
            values: 列值序列。/ Column value sequence.

        Returns:
            构建器自身。/ Builder itself.
        """
        self._columns[name] = list(values)
        return self

    def build(self) -> DataFrame[T]:
        """构建 DataFrame。

        Build the DataFrame.

        Returns:
            构建好的 DataFrame。/ Built DataFrame.
        """
        df: DataFrame[T] = DataFrame()
        for name, values in self._columns.items():
            df.add_column(name, values)
        return df
