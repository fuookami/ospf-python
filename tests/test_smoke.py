"""Smoke test for the ospf_python package.

Verifies that the package can be imported and the basic structure is intact.
"""


def test_import_ospf_python() -> None:
    """Verify that the ospf_python package can be imported."""
    import ospf_python

    assert ospf_python is not None


def test_import_utils() -> None:
    """Verify that the utils sub-package can be imported."""
    from ospf_python import utils

    assert utils is not None


def test_import_multiarray() -> None:
    """Verify that the multiarray sub-package can be imported."""
    from ospf_python import multiarray

    assert multiarray is not None


def test_import_math() -> None:
    """Verify that the math sub-package can be imported."""
    from ospf_python import math

    assert math is not None


def test_import_quantities() -> None:
    """Verify that the quantities sub-package can be imported."""
    from ospf_python import quantities

    assert quantities is not None


def test_import_core() -> None:
    """Verify that the core sub-package can be imported."""
    from ospf_python import core

    assert core is not None


def test_import_framework() -> None:
    """Verify that the framework sub-package can be imported."""
    from ospf_python import framework

    assert framework is not None
