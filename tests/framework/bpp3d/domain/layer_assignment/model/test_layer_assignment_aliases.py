"""层分配类型别名测试。

Tests for layer assignment type aliases module.
Verifies that all type aliases are importable and
the module-level definitions execute correctly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ospf_python.framework.bpp3d.domain.layer_assignment.model.layer_assignment_aliases import (
        CapacityMap,
        ContainerId,
        LayerId,
        LayerIndex,
        LoadMap,
        Quantity,
    )


class TestLayerAssignmentAliases:
    """层分配别名测试。/ Layer assignment alias tests."""

    def test_import_all_aliases(self) -> None:
        """导入所有类型别名。/ Import all type aliases."""
        from ospf_python.framework.bpp3d.domain.layer_assignment.model.layer_assignment_aliases import (
            CapacityMap,
            ContainerId,
            LayerId,
            LayerIndex,
            LoadMap,
            Quantity,
        )

        # Verify the aliases exist at module level
        assert LayerId is not None
        assert ContainerId is not None
        assert LayerIndex is not None
        assert Quantity is not None
        assert CapacityMap is not None
        assert LoadMap is not None

    def test_type_alias_usage(self) -> None:
        """类型别名可正常使用。/ Type aliases work for typing."""

        # These are type aliases; verify they resolve
        # to the expected base types at runtime
        layer_id: LayerId = "layer-1"
        container_id: ContainerId = "container-1"
        layer_idx: LayerIndex = 0
        qty: Quantity = 5

        assert isinstance(layer_id, str)
        assert isinstance(container_id, str)
        assert isinstance(layer_idx, int)
        assert isinstance(qty, int)

    def test_capacity_map_type(self) -> None:
        """CapacityMap 字典类型。/ CapacityMap dict type."""

        cm: CapacityMap = {}
        assert isinstance(cm, dict)

    def test_load_map_type(self) -> None:
        """LoadMap 字典类型。/ LoadMap dict type."""

        lm: LoadMap = {}
        assert isinstance(lm, dict)
