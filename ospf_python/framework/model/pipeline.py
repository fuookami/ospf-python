"""模型管道 / Model pipeline.

提供模型构建和求解的管道机制。
Provides pipeline mechanism for model building and solving.
"""

from __future__ import annotations

import abc
from typing import Generic, TypeVar

T = TypeVar("T")
R = TypeVar("R")


class Pipeline(abc.ABC, Generic[T, R]):
    """模型管道 / Model pipeline.

    定义数据处理管道的抽象接口，支持链式处理。
    Defines the abstract interface for data processing
    pipelines, supporting chained processing.

    Type Parameters:
        T: 输入类型 / The input type.
        R: 输出类型 / The output type.
    """

    @abc.abstractmethod
    def execute(self, input_data: T) -> R:
        """执行管道 / Execute the pipeline.

        Args:
            input_data: 管道输入数据 / The pipeline input data.

        Returns:
            管道输出结果 / The pipeline output result.
        """
        ...

    @abc.abstractmethod
    def reset(self) -> None:
        """重置管道状态 / Reset pipeline state.

        将管道恢复到初始状态。
        Resets the pipeline to its initial state.
        """
        ...
