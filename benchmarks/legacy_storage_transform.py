"""Frozen pre-native storage-transform comparison baseline.

These methods are copied from the implementation frozen before native
reshape/flatten orchestration. They are benchmark-only reference code and must
not be imported by production modules.
"""

from __future__ import annotations

from typing import Any

from ospf_python.multiarray.multi_array import MultiArray, MutableMultiArray
from ospf_python.multiarray.shape import DynShape


class LegacyMultiArray(MultiArray[Any, Any]):
    """Frozen immutable reference methods."""

    def reshape(self, new_shape: DynShape) -> MultiArray[Any, DynShape]:
        """Copy through the frozen NumPy reshape/flatten chain."""
        new_data = self._data.reshape(new_shape.dims).flatten()
        return MultiArray(new_shape, new_data.copy())

    def flatten(self) -> MultiArray[Any, DynShape]:
        """Copy through the frozen flatten path."""
        flat_shape = DynShape(dims=(self.size,))
        return MultiArray(flat_shape, self._data.copy())


class LegacyMutableMultiArray(MutableMultiArray[Any, Any]):
    """Frozen mutable reference methods."""

    def reshape(self, new_shape: DynShape) -> MultiArray[Any, DynShape]:
        """Create the frozen immutable copy, then apply frozen reshape."""
        immutable = MultiArray(self._shape, self._data.copy())
        return LegacyMultiArray.reshape(immutable, new_shape)

    def flatten(self) -> MultiArray[Any, DynShape]:
        """Copy through the frozen flatten path."""
        flat_shape = DynShape(dims=(self.size,))
        return MultiArray(flat_shape, self._data.copy())
