"""Smoke tests to verify basic package structure and imports."""

import ospf_python
from ospf_python import core, framework, math, multiarray, quantities, utils


def test_package_import() -> None:
    """Verify ospf_python package can be imported."""
    assert ospf_python.__version__ == "0.1.0"
    assert ospf_python.__author__ == "fuookami"


def test_subpackages_exist() -> None:
    """Verify all required subpackages exist."""
    # Verify they are modules
    assert core is not None
    assert framework is not None
    assert math is not None
    assert multiarray is not None
    assert quantities is not None
    assert utils is not None
