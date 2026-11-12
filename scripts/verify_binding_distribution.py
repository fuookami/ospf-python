"""在仓库外验证 wheel/sdist / Verify wheel and sdist outside the checkout."""

from __future__ import annotations

import argparse
import os
import posixpath
import re
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from email.parser import Parser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

_SOLVER_SDKS = {"gurobipy", "pyscipopt", "coptpy", "mindoptpy"}
# shortcut: 仅允许单一 extra 标记；扩展发行策略时需重审。
# shortcut: Only a single extra marker; reassess if the release policy changes.
_SOLVER_EXTRA = re.compile(
    r"\s*extra\s*==\s*(['\"])[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?\1\s*"
)
# shortcut: inline links only; use a parser for more. / 局限：仅行内链接，扩展时换解析器。
_MARKDOWN_LINK = re.compile(r"!?\[[^\]\n]+\]\(([^\s)]+)(?:\s+[^)]*)?\)")
_MARKDOWN_CODE = re.compile(
    r"^ {0,3}(`{3,})[^\n]*(?:\n|\Z).*?"
    r"(?:^ {0,3}\1`*[ \t]*(?:\r?\n|$)|\Z)"
    r"|^ {0,3}(~{3,})[^\n]*(?:\n|\Z).*?"
    r"(?:^ {0,3}\2~*[ \t]*(?:\r?\n|$)|\Z)"
    r"|`[^`\n]+`",
    re.MULTILINE | re.DOTALL,
)
_EXAMPLE_PATH = re.compile(r"`(examples/[A-Za-z0-9_./-]+\.py)`")
_EXAMPLE_MODULE = re.compile(r"\bpython\s+-m\s+(examples(?:\.[A-Za-z_]\w*)+)")
_SOLVER_RUNTIME = re.compile(
    r"^(?:lib)?(?:scip|gurobi\d*|copt|mindopt)(?:[._-].*)?"
    r"\.(?:so(?:\..*)?|dll|dylib)$",
    re.IGNORECASE,
)


def _inspect_wheel(path: Path) -> list[str]:
    issues: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        for required in ("ospf_python/py.typed", "ospf_python/_native.pyi"):
            if required not in names:
                issues.append(f"Missing wheel entry: {required}")
        extensions = [
            name
            for name in names
            if name.startswith("ospf_python/_native") and name.endswith((".pyd", ".so"))
        ]
        if len(extensions) != 1:
            issues.append("Expected exactly one native extension")
        metadata = [name for name in names if name.endswith(".dist-info/METADATA")]
        if len(metadata) != 1:
            issues.append("Expected exactly one METADATA entry")
        else:
            message = Parser().parsestr(archive.read(metadata[0]).decode("utf-8"))
            for requirement in message.get_all("Requires-Dist", []):
                name = re.split(r"[\s\[<>=!~;(]", requirement, maxsplit=1)[0].lower()
                if name in _SOLVER_SDKS:
                    _, separator, marker = requirement.partition(";")
                    if not separator:
                        issues.append(f"Mandatory solver SDK: {requirement}")
                    elif not _SOLVER_EXTRA.fullmatch(marker):
                        issues.append(f"Unsupported solver SDK marker: {requirement}")
        for name in names:
            parts = PurePosixPath(name).parts
            if PurePosixPath(name).is_absolute() or ".." in parts:
                issues.append(f"Unsafe archive entry: {name}")
            if _SOLVER_RUNTIME.match(PurePosixPath(name).name):
                issues.append(f"Bundled solver runtime: {name}")
            if (
                "logs" in parts
                or "target" in parts
                or "__pycache__" in parts
                or name.endswith((".pdb", ".pyc", ".pyo"))
            ):
                issues.append(f"Development artifact in wheel: {name}")
    return issues


def _inspect_sdist(path: Path) -> list[str]:
    issues: list[str] = []
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)):
            issues.append("Duplicate sdist entry")
        roots = {
            PurePosixPath(name).parts[0] for name in names if PurePosixPath(name).parts
        }
        if len(roots) != 1:
            issues.append("Expected exactly one sdist root")
        for member in members:
            name = member.name
            parts = PurePosixPath(name).parts
            if (
                not parts
                or PurePosixPath(name).is_absolute()
                or ".." in parts
                or "\\" in name
                or posixpath.normpath(name) != name
            ):
                issues.append(f"Unsafe archive entry: {name}")
            if not member.isfile() and not member.isdir():
                issues.append(f"Unsupported sdist entry: {name}")
            if any(part in {"logs", "target", "__pycache__", ".git"} for part in parts):
                issues.append(f"Development artifact in sdist: {name}")
            if name.endswith((".pyd", ".so", ".pyc", ".pyo", ".pdb", ".dll", ".dylib")):
                issues.append(f"Compiled artifact in sdist: {name}")
        if len(roots) == 1:
            root = next(iter(roots))
            files = {member.name for member in members if member.isfile()}
            for required in (
                "native/Cargo.toml",
                "native/Cargo.lock",
                "rust-toolchain.toml",
                "pyproject.toml",
                "README.md",
                "README_ch.md",
                "docs/index.md",
                "docs/migration/api-map.toml",
                "examples/__init__.py",
            ):
                if f"{root}/{required}" not in files:
                    issues.append(f"Missing sdist entry: {required}")
            for member in members:
                if not member.isfile() or not member.name.startswith(f"{root}/"):
                    continue
                if not member.name.endswith(".md"):
                    continue
                stream = archive.extractfile(member)
                assert stream is not None
                text = stream.read().decode("utf-8")
                prose = _MARKDOWN_CODE.sub("", text)
                references: set[str] = set()
                for link in _MARKDOWN_LINK.findall(prose):
                    try:
                        parsed = urlsplit(link)
                    except ValueError:
                        issues.append(
                            f"Invalid documentation link in {member.name}: {link}"
                        )
                        continue
                    if parsed.scheme or parsed.netloc or not parsed.path:
                        continue
                    references.add(
                        posixpath.normpath(
                            posixpath.join(
                                posixpath.dirname(member.name), unquote(parsed.path)
                            )
                        )
                    )
                references.update(
                    f"{root}/{name}" for name in _EXAMPLE_PATH.findall(text)
                )
                references.update(
                    f"{root}/{name.replace('.', '/')}.py"
                    for name in _EXAMPLE_MODULE.findall(text)
                )
                for target in sorted(references):
                    if not target.startswith(f"{root}/"):
                        issues.append(
                            f"Unsafe documentation reference in {member.name}: {target}"
                        )
                    elif target not in files:
                        issues.append(
                            f"Missing documentation reference in {member.name}: {target}"
                        )
    return issues


def _sdist_build_args(native_solvers: list[str], platform: str) -> str:
    arguments = "--locked"
    if native_solvers:
        arguments += " --features=" + ",".join(native_solvers)
        if platform.startswith("linux"):
            arguments += " --compatibility linux --auditwheel skip"
    return arguments


def _smoke(
    *,
    python: Path,
    workspace: Path,
    environment: dict[str, str],
    native_solvers: list[str],
) -> None:
    code = """
import importlib.util
import asyncio
import json
import os
import pickle
from pathlib import Path
import sys
from fractions import Fraction
directories = []
if os.name == 'nt':
    directories = [os.add_dll_directory(path) for path in
                   os.environ.get('OSPF_NATIVE_DLL_DIRS', '').split(os.pathsep) if path]
from ospf_python import _native
from ospf_python._binding import storage_transform as storage_bridge
from ospf_python._binding.bpp1d import (AuxiliaryVariable, BinSpec, ExtensionConstraint,
    ItemSpec, PackingContext, PatternExtension, PatternExtensionSpec)
from ospf_python._binding.control import SolveHandle
from ospf_python._binding.gantt_activity import Activity, Mode, Precedence, Resource, Row, solve_activity
from ospf_python._binding.gantt_bunch import solve_bunch_columns
from ospf_python._binding.gantt_task import solve_task_columns
from ospf_python._binding.model import ColumnDecisionSpec, ColumnSpec, ConstraintSpec, MetaModelFloat64, VariableSpec
from ospf_python._binding.numeric import Rational, RationalArray
from ospf_python._binding.quantities import Unit
from ospf_python._binding.multiarray import Shape, RationalMultiArray, MultiArray, MutableMultiArray, MultiArrayView, MappedMultiArrayView
from ospf_python.multiarray.multi_array import MultiArray as PublicArray
from ospf_python.multiarray.multi_array import MutableMultiArray as PublicMutableArray
from ospf_python.multiarray.multi_array_view import MultiArrayView as PublicView
from ospf_python.multiarray.shape import DynShape, Shape2, StorageOrder
from ospf_python.core import MetaModel
from ospf_python.framework.gantt_scheduling.application.model.gantt_problem import GanttProblem
from ospf_python.framework.gantt_scheduling.application.service.bunch.bunch_column import BunchColumn
from ospf_python.framework.gantt_scheduling.application.service.task import (
    TaskApplicationService,
    TaskColumnGenerationAlgorithm,
    TaskPricingResult,
)
from ospf_python.framework.gantt_scheduling.application.service.task.task_column import TaskColumn
from ospf_python.framework.gantt_scheduling.domain.resource.model.resource import Resource as LegacyResource
from ospf_python.framework.gantt_scheduling.domain.task.model.task import Task as LegacyTask
from ospf_python.math.combinatorics import cross, combinations, permutations, combinations_async, permutations_async
from ospf_python.math.algebra.number.rational import Rational as PublicRational
from ospf_python.math.fractal.julia_set import JuliaSet
from ospf_python.math.fractal.mandelbrot_set import MandelbrotSet
from ospf_python.math.ordinary.clamp import clamp
from ospf_python.quantities.quantity.quantity import Quantity
from ospf_python.quantities.unit.length import METER
from ospf_python.utils.error.code import ErrorCode
from ospf_python.utils.error.error import Err
from ospf_python.utils.functional.result import Failed, Ok
assert Path(_native.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
assert _native._checked_nonnegative(42) == (42, None)
assert _native._checked_nonnegative(-1)[1][0] == 0x34
length_unit = Unit.create(name='length', symbol='m', powers=(0, 1, 0, 0, 0, 0, 0, 0, 0, 0)).unwrap()
weight_unit = Unit.create(name='mass', symbol='kg', powers=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0)).unwrap()
bpp_zero = Rational.create(numerator=0).unwrap()
bpp_one = Rational.create(numerator=1).unwrap()
bpp = PackingContext.create(
    items=[ItemSpec(id=key, length=Rational.from_float(value).unwrap(), weight=bpp_zero, amount=1)
           for key, value in [('a', 0.1), ('c', 0.2), ('b', 0.03)]],
    bins=[BinSpec(id='bin', length=Rational.from_float(0.33).unwrap(), max_weight=bpp_zero, cost=bpp_one)],
    spacing=bpp_zero, length_unit=length_unit, weight_unit=weight_unit,
).unwrap()
bpp_patterns, bpp_complete, _ = bpp.generate_patterns(max_patterns=100, max_nodes=1000).unwrap()
assert bpp_complete and len(bpp_patterns) == 7 and ('bin', {'a': 1, 'b': 1, 'c': 1}) in bpp_patterns
bpp_singles, bpp_single_complete, _ = bpp.generate_patterns(
    max_patterns=100, max_nodes=1000, policy=lambda pattern: Ok(len(pattern[1]) == 1)
).unwrap()
assert bpp_single_complete and len(bpp_singles) == 3
bpp_policy_error = Failed(Err(_code=ErrorCode.PERMISSION_DENIED, _message='policy denied'))
bpp_failed = bpp.generate_patterns(max_patterns=100, max_nodes=1000, policy=lambda _: bpp_policy_error)
assert isinstance(bpp_failed, Failed) and bpp_failed.error.value.callback_result is bpp_policy_error
bpp_packed = bpp.pack(usages=[('bin', {'a': 1, 'b': 1, 'c': 1}, 1)], expansion_limit=3).unwrap()
assert Fraction(*bpp_packed[3]) == Fraction(*bpp_packed[4]) == Fraction.from_float(0.33)
assert bpp_packed[5] == (1, 1)
assert bpp.pack(usages=[], expansion_limit=3).is_failed()
assert bpp.solve(solver='unknown', max_patterns=100, max_nodes=1000, expansion_limit=3).is_failed()
activity_resource = Resource(id='r', capacity=bpp_one, unit=weight_unit)
activity_modes = tuple(Activity(id=task, modes=(Mode(
    id='m', duration_ns=2, starts_ns=starts, resources=(('r', bpp_one),), cost=bpp_one,
),)) for task, starts in (('a', (0,)), ('b', (0, 3))))
activity_args = dict(horizon_ns=(0, 5), resources=(activity_resource,), activities=activity_modes,
    dependencies=(Precedence(predecessor='a', successor='b', min_gap_ns=1),),
    rows=(Row(id='require-b3', unit=weight_unit, coefficients=(('b', 'm', 3, bpp_one),), lower=bpp_one),),
    cost_unit=weight_unit, max_work=1000)
assert solve_activity(**activity_args, solver='unknown').is_failed()
bunch_problem = GanttProblem(tasks=(LegacyTask('a', 'A', 0.1),),
    resources=(LegacyResource('r', 'R', 2.0),))
bunch_columns = (BunchColumn('duplicate', (('a', 0.0), ('a', 0.0)), 'r', -2.0),
    BunchColumn('empty', (), 'r', -1.0))
bunch_args = dict(problem=bunch_problem, columns=bunch_columns, resource_units={'r': weight_unit},
    cost_unit=weight_unit, max_work=1000)
assert solve_bunch_columns(**bunch_args, solver='unknown').is_failed()
joint_problem = GanttProblem(tasks=tuple(LegacyTask(key, key.upper(), 0.5,
    resource_requirements=(('crew', 0.75), ('r', 0.25), ('r', 0.25))) for key in ('a', 'b')),
    resources=(LegacyResource('r', 'R', 1.0), LegacyResource('crew', 'Crew', 1.0)),
    time_horizon=2.0)
joint_columns = (BunchColumn('a', (('a', 0.0),), 'r', 1.0),
    BunchColumn('overlap', (('b', 0.0),), 'r', -1.0),
    BunchColumn('late', (('b', 1.0),), 'r', 2.0))
joint_args = dict(problem=joint_problem, columns=joint_columns,
    resource_units={'r': weight_unit, 'crew': weight_unit}, cost_unit=weight_unit, max_work=10000)
assert solve_bunch_columns(**joint_args, solver='unknown').is_failed()
task_columns = (TaskColumn('early', (('a', 'r', 0.0), ('b', 'crew', 0.5)), 100.0),
    TaskColumn('late', (('a', 'crew', 1.0), ('b', 'r', 1.5)), -100.0),
    TaskColumn('duplicate', (('a', 'r', 0.0), ('a', 'crew', 0.0)), -200.0))
task_args = dict(problem=joint_problem, columns=task_columns,
    resource_units={'r': weight_unit, 'crew': weight_unit}, max_work=10000)
assert solve_task_columns(**task_args, solver='unknown').is_failed()
task_pricing = TaskColumnGenerationAlgorithm.create(task_count=2, executor_count=2).unwrap()
assert task_pricing.add_columns([(0, 0, 1.0), (1, 1, 2.0)]).unwrap() == [(0, 0, 1.0), (1, 1, 2.0)]
assert task_pricing.solve_lp(solver='unknown').is_failed()
assert callable(TaskApplicationService.run_task_pricing)
assert TaskPricingResult.__dataclass_fields__.keys() == {
    'task_keys', 'resource_keys', 'lp_report', 'batch', 'certified_lower_bound'
}
bpp_extension_error = Failed(Err(_code=ErrorCode.PERMISSION_DENIED, _message='extension denied'))
bpp_failed = bpp.solve(solver='unknown', max_patterns=100, max_nodes=1000, expansion_limit=3,
    extension=PatternExtension(register=lambda _: bpp_extension_error))
assert isinstance(bpp_failed, Failed) and bpp_failed.error.value.callback_result is bpp_extension_error
bpp_pool = bpp.column_pool(patterns=[('bin', {'a': 1, 'b': 1, 'c': 1})]).unwrap()
bpp_first = bpp_pool.snapshot().unwrap()
assert bpp_first.generation == 0 and len(bpp_first.compiled_columns) == 1
bpp_next = bpp_pool.add_columns(patterns=[('bin', {'a': 1})]).unwrap()
assert bpp_next.generation == 1 and bpp_next.model_identity != bpp_first.model_identity
assert bpp_pool.solve_lp(solver='unknown').is_failed()
assert bpp_pool.solve_final_milp(solver='unknown', expansion_limit=3).is_failed()
bpp_final_stages = []
def bpp_final_register(snapshot):
    bpp_final_stages.append(snapshot.stage)
    flag = snapshot.auxiliary('flag')
    return PatternExtensionSpec(
        variables=[AuxiliaryVariable(name='flag', kind='binary')],
        constraints=[ExtensionConstraint(name='half', terms=[(flag, (2, 1))], relation='>=', rhs=(1, 1))],
        objective=[(flag, (1, 1))],
    )
def bpp_final_extract(snapshot):
    flag = next(ref for ref in snapshot.values if ref.auxiliary == 'flag')
    return {'flag': str(snapshot.values[flag][0])}
bpp_final_pool = bpp.column_pool(
    patterns=[('bin', {'a': 1, 'b': 1, 'c': 1})],
    extension=PatternExtension(register=bpp_final_register, extract_solution=bpp_final_extract),
).unwrap()
assert bpp_final_stages == ['lp']
def bpp_register(snapshot):
    assert len(snapshot.items) == 3 and len(snapshot.candidates) == 7
    enabled = snapshot.auxiliary('enabled')
    return PatternExtensionSpec(
        variables=[AuxiliaryVariable(name='enabled', kind='binary')],
        constraints=[ExtensionConstraint(name='enabled_row', terms=[(enabled, (1, 1))], relation='==', rhs=(1, 1))],
        objective=[(enabled, (2, 1))],
    )
def bpp_extract(snapshot):
    assert len(snapshot.candidates) == 7 and len(snapshot.values) == 8
    enabled = next(ref for ref in snapshot.values if ref.auxiliary == 'enabled')
    assert snapshot.values[enabled] == (1, 1)
    return {'enabled': '1'}
assert PackingContext.create(items=[], bins=[], spacing=bpp_zero, length_unit=weight_unit, weight_unit=weight_unit).is_failed()
original = Fraction(2, 3)
assert clamp(original, min_val=Fraction(0), max_val=Fraction(1)).unwrap() is original
assert clamp(object(), min_val=object(), max_val=object()).is_failed()
logistic, logistic_error = _native._logistic_float64_step(rate=3.9, value=0.25)
assert logistic_error is None and logistic == 3.9 * 0.25 * (1.0 - 0.25)
logistic, logistic_error = _native._logistic_float64_step(rate=3.9, value=1)
assert logistic is None and logistic_error.category == 'ILLEGAL_ARGUMENT'
assert _native._fractal_escape_time(
    z=0j,
    c=0j,
    max_iterations=32,
) == (32, None)
assert MandelbrotSet(max_iter=100).contains(complex(-0.5, 0.0)).unwrap() is True
assert MandelbrotSet.iterate(complex(10.0, 10.0), 100).unwrap() == 1
assert JuliaSet(max_iter=100, c_real=-0.7, c_imag=0.27015).contains(0.1, 0.1).unwrap() is True
assert JuliaSet.iterate(complex(100.0, 100.0), complex(-0.7, 0.27015), 100).unwrap() == 0
assert SolveHandle().phase == 'READY'
public_bound = PublicRational(2, 3) / PublicRational(1, 3)
public_cost = PublicRational(1, 3) + PublicRational(2, 3)
public_bound, public_cost = pickle.loads(pickle.dumps((public_bound, public_cost)))
assert public_bound == PublicRational(2) and public_cost == PublicRational(1)
assert set(vars(public_bound)) == {'numerator', 'denominator'}
constructed_pairs = []
constructor_error = ValueError('installed rational constructor')
def broken_rational_constructor(numerator, denominator):
    constructed_pairs.append((numerator, denominator))
    assert _native._public_rational_normalize(numerator, denominator)[0] is numerator
    raise constructor_error
try:
    _native._public_rational_negated(((1 << 512) + 1, 17), constructor=broken_rational_constructor)
except ValueError as error:
    assert error is constructor_error
else:
    raise AssertionError('constructor exception was lost')
assert _native._public_rational_normalize(*constructed_pairs[0])[0] is not constructed_pairs[0][0]
def public_exact_float(value):
    return Rational.create(numerator=value.numerator, denominator=value.denominator).unwrap().to_float().unwrap()
assert cross().unwrap() == [()]
assert cross([1, 2], (v for v in ['a', 'b'])).unwrap() == [(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')]
assert cross(*[[0, 1] for _ in range(64)]).is_failed()
cross_leaf = object()
assert cross([cross_leaf], [None]).unwrap()[0][0] is cross_leaf
cross_error = RuntimeError('external cross input')
def broken_cross_input():
    raise cross_error
    yield None
cross_failure = cross([], broken_cross_input())
assert cross_failure.error.value.callback_exception is cross_error
assert combinations([], 0).unwrap() == [[]]
assert permutations([], 0).unwrap() == [[]]
assert combinations([0, 1, 2], 2).unwrap() == [[0, 1], [0, 2], [1, 2]]
assert permutations([0, 1, 2], 2).unwrap() == [[0, 1], [0, 2], [1, 0], [1, 2], [2, 0], [2, 1]]
for selection in (combinations, permutations):
    selection_leaf = Quantity(Fraction(1, 3), METER)
    class IndexedSelection:
        def __init__(self):
            self.values = [selection_leaf, None]
        def __len__(self):
            return len(self.values)
        def __getitem__(self, index):
            return self.values[index]
        def __iter__(self):
            raise AssertionError('installed selection must use indexed protocol')
    assert selection(IndexedSelection(), 1).unwrap()[0][0] is selection_leaf
    selection_error = TypeError('installed selection external getter')
    class BrokenSelection(IndexedSelection):
        def __getitem__(self, index):
            raise selection_error
    assert selection(BrokenSelection(), 1).error.value.callback_exception is selection_error
assert asyncio.run(combinations_async([0, 1], 1)).unwrap() == [[0], [1]]
assert asyncio.run(permutations_async([0, 1], 2)).unwrap() == [[0, 1], [1, 0]]
for public_type in (PublicArray, PublicMutableArray):
    import numpy as np
    for count in (int('10000'), sys.maxsize + 1):
        events = []
        original_shape_factory = storage_bridge.DynShape
        class ShapeFactory:
            def __call__(self, *, dims):
                events.append('shape')
                assert dims[0] is count
                storage_bridge.DynShape = original_shape_factory
                return original_shape_factory(dims=dims)
            def __del__(self):
                events.append('release')
        class SparseMetadata:
            size = count
        class CopyData:
            def copy(self):
                events.append('copy')
                return np.arange(3, dtype=np.int16)
        storage_bridge.DynShape = ShapeFactory()
        try:
            flat = public_type(SparseMetadata(), CopyData()).flatten().unwrap()
            assert type(flat.shape) is DynShape and flat.shape.dims[0] is count
            assert flat._data.tolist() == [0, 1, 2]
            assert events == ['shape', 'release', 'copy'], events
        finally:
            storage_bridge.DynShape = original_shape_factory
    external = np.arange(6, dtype=np.int16)[::-1]
    public_source = public_type(Shape2(2, 3, StorageOrder.COLUMN_MAJOR), external)
    reshape_target = DynShape((3, 2), StorageOrder.ROW_MAJOR)
    reshaped_public = public_source.reshape(reshape_target).unwrap()
    assert reshaped_public.shape is reshape_target
    assert reshaped_public._data.dtype == external.dtype
    assert reshaped_public._data.tolist() == external.tolist()
    assert not np.shares_memory(reshaped_public._data, external)
    assert public_source.to_list().unwrap() == [[5, 3, 1], [4, 2, 0]]
    assert public_source._data is external
    assert public_source.reduce(lambda a, b: a - b).unwrap() == -5
    reduce_error = ValueError('external reduction callback')
    def broken_reduction(a, b):
        raise reduce_error
    assert public_source.reduce(broken_reduction).error.value.callback_exception is reduce_error
    assert public_source.map(lambda value: value * 2).unwrap()._data.tolist() == [10, 8, 6, 4, 2, 0]
    expanded_public = public_source.flat_map(lambda value: iter((value, -value))).unwrap()
    assert expanded_public._data.tolist() == [5, -5, 4, -4, 3, -3, 2, -2, 1, -1, 0, 0]
    assert expanded_public.shape is public_source.shape
    mapping_error = ValueError('external mapping callback')
    def broken_mapping(value):
        raise mapping_error
    for method in ('map', 'flat_map'):
        assert getattr(public_source, method)(broken_mapping).error.value.callback_exception is mapping_error
    public_materialized = PublicView(public_source).map(lambda value: value*2).materialize().unwrap()
    assert public_materialized._data.tolist() == [10, 8, 6, 4, 2, 0]
    for row in range(2):
        for column in range(3):
            assert public_materialized.get(row, column) == public_source.get(row, column)*2
    assert PublicView(public_source).map(broken_mapping).materialize().error.value.callback_exception is mapping_error
    plain_copy = PublicView(public_source).materialize().unwrap()
    assert plain_copy.shape is public_source.shape
    assert plain_copy._data.dtype == external.dtype
    assert not np.shares_memory(plain_copy._data, external)
    plain_region = PublicView(public_source, offsets=(1, 1)).materialize().unwrap()
    assert plain_region.shape.dims == (1, 2)
    assert plain_region.shape.storage_order is StorageOrder.COLUMN_MAJOR
    assert plain_region._data.tolist() == [2, 0]
    assert plain_region._data.dtype == external.dtype
    assert PublicView(public_source, offsets=(2, 0)).materialize().is_failed()
    transposed_public = public_source.transpose().unwrap()
    assert transposed_public.shape.dims == (3, 2)
    assert transposed_public._data.dtype == external.dtype
    assert not np.shares_memory(transposed_public._data, external)
    for row in range(2):
        for column in range(3):
            assert transposed_public.get(column, row) == public_source.get(row, column)
    class BrokenTransposeShape:
        dims = (1,)
        size = 1
        def strides(self):
            raise mapping_error
    transpose_failure = public_type(BrokenTransposeShape(), np.array([7])).transpose()
    assert transpose_failure.error.value.callback_exception is mapping_error
    public_cursor = iter(public_source)
    assert next(public_cursor) == 5
    assert isinstance(public_cursor.gi_yieldfrom, _native.SharedArrayIterator)
    external[1] = 99
    assert public_cursor.send('ignored') == 99
    assert list(public_cursor) == [3, 2, 1, 0]
    assert public_source.at(indices=(1, 1)).unwrap() == 2
    assert public_source.at(indices=(0, 3)).is_failed()
    assert public_source.at(indices=(0,)).is_failed()
    assert public_source.at_many(indices=[(1, 1), (0, 1), (1, 1)]).unwrap() == [2, 3, 2]
    assert public_source.at_many(indices=[]).unwrap() == []
    assert public_source.at_many(indices=[(0, 0), (0, 3)]).is_failed()
    if public_type is PublicMutableArray:
        public_source.set_at(indices=(1, 1), value=12).unwrap()
        assert external[3] == 12
        external.flags.writeable = False
        assert public_source.set_at(indices=(1, 1), value=13).is_failed()
        assert external[3] == 12
    class OpaqueLeaf:
        @property
        def item(self):
            raise AssertionError('ordinary item must not run')
    opaque = OpaqueLeaf()
    values = np.empty(1, dtype=object)
    values[0] = opaque
    public_source = public_type(Shape2(1, 1), values)
    assert public_source.get(0, 0) is opaque
    assert public_source.to_list().unwrap()[0][0] is opaque
    assert next(iter(public_source)) is opaque
    assert public_source.at(indices=(0, 0)).unwrap() is opaque
    assert public_source.at_many(indices=[(0, 0), (0, 0)]).unwrap()[1] is opaque
    assert public_source.reduce(None).unwrap() is opaque
    class PretendScalar:
        @property
        def __class__(self):
            raise AssertionError('spoofed class must not run')
        def item(self):
            raise AssertionError('spoofed item must not run')
    pretend = PretendScalar()
    values[0] = pretend
    assert public_source.get(0, 0) is pretend
    assert next(iter(public_source)) is pretend
    assert public_source.at(indices=(0, 0)).unwrap() is pretend
    assert public_source.at_many(indices=[(0, 0)]).unwrap()[0] is pretend
exact = Rational.create(numerator=(1 << 20000) + 1, denominator=1 << 17000).unwrap()
assert exact.as_integer_ratio() == ((1 << 20000) + 1, 1 << 17000)
assert Rational.from_json(exact.to_json()).unwrap() == exact
assert Rational.create(numerator=1, denominator=0).is_failed()
tenth = Rational.create(numerator=1, denominator=10).unwrap()
assert tenth.to_float().is_failed()
assert tenth.to_float(exact=False).unwrap() == 0.1
batch = RationalArray.create([(1, 2), (1, 3)]).unwrap()
assert batch.sum().as_integer_ratio() == (5, 6)
assert batch.dot(batch).unwrap().as_integer_ratio() == (13, 36)
assert batch.add(batch).unwrap().as_integer_ratios() == [(1, 1), (2, 3)]
assert batch.at(-1).is_failed()
assert batch.dot(RationalArray.create([]).unwrap()).is_failed()
assert RationalArray.create([(1, 2), (1, 0)]).is_failed()
shape = Shape.create(dims=(1, 2), storage_order=StorageOrder.COLUMN_MAJOR).unwrap()
assert shape.strides() == (1, 1)
assert shape.index_of((0, 1)).unwrap() == 1
assert shape.vector_of(2).is_failed()
assert shape.indices_of([(0, 0), (0, 1)]).unwrap() == [0, 1]
array = RationalMultiArray.create(values=batch, shape=shape).unwrap()
assert array.at((0, 1)).unwrap().as_integer_ratio() == (1, 3)
assert array.flatten().unwrap().as_integer_ratios() == [(1, 2), (1, 3)]
assert array.reshape(Shape.create(dims=(3,)).unwrap()).is_failed()
assert array.to_storage_order(StorageOrder.ROW_MAJOR).unwrap().shape.dims == (1, 2)
public_shape = Shape2(1, 2, StorageOrder.COLUMN_MAJOR)
assert Shape.from_shape(public_shape).unwrap().dims == (1, 2)
assert RationalMultiArray.create(values=batch, shape=public_shape).unwrap().at((0, 1)).unwrap().as_integer_ratio() == (1, 3)
import gc
import weakref
class Payload:
    pass
fill_leaf = Payload()
filled = MultiArray.full(shape=public_shape, value=fill_leaf).unwrap()
assert all(value is fill_leaf for value in filled.flatten().unwrap())
filled_mutable = MutableMultiArray.full(shape=public_shape, value=None).unwrap()
assert filled_mutable.set(indices=(0, 1), value=fill_leaf).is_ok()
assert filled_mutable.at((0, 0)).unwrap() is None
assert filled_mutable.at((0, 1)).unwrap() is fill_leaf
assert MultiArray.zeros(shape=public_shape).unwrap().to_list().unwrap() == [[0.0, 0.0]]
assert MutableMultiArray.ones(shape=public_shape).unwrap().reduce(lambda a, b: a+b).unwrap() == 2.0
assert MultiArray.full(shape=Shape.create(dims=(sys.maxsize,)).unwrap(), value=None).is_failed()
def object_array_smoke():
    payload = Payload()
    objects = MultiArray.create(values=[payload, None], shape=public_shape).unwrap()
    assert objects.at((0, 0)).unwrap() is payload
    assert objects.at((0, 1)).is_ok() and objects.at((0, 1)).unwrap() is None
    assert objects.to_storage_order(StorageOrder.ROW_MAJOR).unwrap().at((0, 0)).unwrap() is payload
    assert objects.reshape(Shape.create(dims=(2,), storage_order=StorageOrder.COLUMN_MAJOR).unwrap()).unwrap().flatten().unwrap()[0] is payload
    payload.owner = objects
    return weakref.ref(payload)
reference = object_array_smoke()
gc.collect()
assert reference() is None
import copy
import pickle
def reference_state_smoke():
    leaf = Payload()
    source = MutableMultiArray.full(shape=public_shape, value=leaf).unwrap()
    leaf.owner = source
    for protocol in range(pickle.HIGHEST_PROTOCOL + 1):
        restored = pickle.loads(pickle.dumps(source, protocol=protocol))
        item = restored.at((0, 0)).unwrap()
        assert item.owner is restored and restored.at((0, 1)).unwrap() is item
    cloned = copy.deepcopy(source)
    assert cloned.at((0, 0)).unwrap().owner is cloned
    assert copy.copy(source)._handle is source._handle
    snapshot = source.to_snapshot().unwrap()
    imported = MutableMultiArray.from_snapshot(snapshot).unwrap()
    assert imported.at((0, 0)).unwrap() is leaf
    assert MutableMultiArray.from_snapshot({**snapshot, 'version': 2}).is_failed()
    view = source.view(offsets=(0, 1), shape=Shape2(1, 1, StorageOrder.COLUMN_MAJOR)).unwrap()
    new_source, new_view = pickle.loads(pickle.dumps((source, view)))
    assert new_view._source is new_source
    new_view.set(indices=(0, 0), value=None).unwrap()
    assert new_source.at((0, 1)).unwrap() is None
reference_state_smoke()
gc.collect()
import numpy as np
nested_leaf = Payload()
for storage in (MultiArray, MutableMultiArray):
    nested = storage.from_list(data=[[0, nested_leaf, 2], [3, 4, 5]], shape=Shape2(2, 3, StorageOrder.COLUMN_MAJOR)).unwrap()
    assert nested.at((0, 1)).unwrap() is nested_leaf
    assert nested.flatten(access_order=StorageOrder.COLUMN_MAJOR).unwrap() == [0, 3, nested_leaf, 4, 2, 5]
    assert storage.from_list(data=[[0, 1], [2]], shape=Shape2(2, 2)).is_failed()
    assert storage.from_list(data=nested_leaf, shape=Shape.create(dims=()).unwrap()).unwrap().at(()).unwrap() is nested_leaf
    logical_copy = storage.from_list(data=[[0, nested_leaf, 2], [3, 4, 5]], shape=Shape2(2, 3)).unwrap()
    assert nested.equals(logical_copy).unwrap() is True
    calls = []
    assert nested.equals(logical_copy, comparator=lambda a, b: calls.append((a, b)) or Ok(True)).unwrap() is True
    assert len(calls) == 6
    failed = nested.equals(logical_copy, comparator=lambda a, b: None)
    assert failed.is_failed() and failed.error.value.callback_index == 0
    left_region = nested.view(offsets=(0, 1), shape=Shape2(1, 2, StorageOrder.COLUMN_MAJOR)).unwrap()
    right_region = logical_copy.view(offsets=(0, 1), shape=Shape2(1, 2)).unwrap()
    assert left_region.equals(right_region).unwrap() is True
    assert nested.describe(formatter=lambda item: Ok('leaf'), max_items=2).unwrap().endswith('data=[leaf, leaf, ...])')
    assert 'storage_order=COLUMN_MAJOR' in nested.describe(max_items=0).unwrap()
    assert 'offsets=(0, 1)' in left_region.describe(max_items=0).unwrap()
    assert nested.describe(max_chars=3).unwrap() == '...'
    bad_description = nested.describe(formatter=lambda item: None)
    assert bad_description.is_failed() and bad_description.error.value.callback_index == 0
    physical = nested.iter_live().unwrap()
    assert list(physical) == [0, 3, nested_leaf, 4, 2, 5]
    logical = nested.iter_live(access_order=StorageOrder.ROW_MAJOR).unwrap()
    assert logical.advance().unwrap() == (True, 0)
    assert next(logical) is nested_leaf
    logical.close()
    assert logical.advance().unwrap() == (False, None)
    assert list(left_region.iter_live().unwrap()) == [nested_leaf, 2]
legacy_data = np.arange(6, dtype=np.int16)[::-1]
legacy_state = {'_shape': Shape2(2, 3, StorageOrder.COLUMN_MAJOR), '_data': legacy_data}
for storage in (MultiArray, MutableMultiArray):
    imported = storage.from_legacy_state(payload=legacy_state, copy=True).unwrap()
    assert imported.to_list().unwrap() == [[5, 3, 1], [4, 2, 0]]
    assert type(imported.at((0, 1)).unwrap()) is np.int16
    assert storage.from_legacy_state(payload=legacy_state, copy=False).is_failed()
legacy_data[:] = -1
assert imported.at((0, 1)).unwrap() == 3
imported.set(indices=(0, 1), value=99).unwrap()
assert legacy_data.tolist() == [-1] * 6
for order in (StorageOrder.ROW_MAJOR, StorageOrder.COLUMN_MAJOR):
    legacy_source = PublicArray(Shape2(2, 3, order), np.arange(6, dtype=np.int16))
    region = MultiArrayView.from_legacy_state(payload={'_source': legacy_source, '_offsets': (1, 1)}, copy=True).unwrap()
    assert region.shape.dims == (1, 2)
    assert region.at((0, 1)).unwrap() == 5
    assert type(region.at((0, 0)).unwrap()) is np.int16
    assert region.view().unwrap().shape.dims == (1, 2)
    assert region.view(offsets=(0, 1)).unwrap().materialize().unwrap().to_list().unwrap() == [[5]]
    assert region.view(offsets=(1, 0)).is_failed()
    assert MultiArrayView.from_legacy_state(payload={'_source': legacy_source, '_offsets': (0, 0)}, copy=False).is_failed()
    legacy_source._data[:] = -1
    assert region.at((0, 1)).unwrap() == 5
source = np.arange(6, dtype=np.int64).reshape(2, 3)
mutable = MutableMultiArray.from_numpy(values=source, copy=True, storage_order=StorageOrder.COLUMN_MAJOR).unwrap()
assert mutable.to_list().unwrap() == [[0, 1, 2], [3, 4, 5]]
view = mutable.view(offsets=(1, 1), shape=Shape2(1, 2, StorageOrder.COLUMN_MAJOR)).unwrap()
assert view.materialize().unwrap().flatten().unwrap() == [4, 5]
before = mutable.to_immutable().unwrap()
assert view.set_many([((0, 0), 40), ((0, 1), 50)]).unwrap() is None
assert mutable.at((1, 1)).unwrap() == 40
assert before.at((1, 1)).unwrap() == 4
assert source[1, 1] == 4
assert view.set_many([((0, 0), 0), ((1, 0), 0)]).is_failed()
assert view.flatten().unwrap() == [40, 50]
assert view.to_list().unwrap() == [[40, 50]]
assert view.reduce(lambda left, right: Ok(left + right)).unwrap() == 90
assert list(view.iter_snapshot().unwrap()) == [40, 50]
iterator_before_update = view.iter_snapshot().unwrap()
fold_failure = Failed(Err(ErrorCode.APPLICATION_ERROR, 'installed-fold-callback'))
failed_fold = view.reduce(lambda left, right: fold_failure)
assert failed_fold.is_failed() and failed_fold.error.value.callback_result is fold_failure
assert failed_fold.error.value.callback_index == 0
assert view.transpose().unwrap().shape.dims == (2, 1)
assert view.transpose().unwrap().flatten().unwrap() == [40, 50]
assert view.map(lambda value: value + 1).unwrap().flatten().unwrap() == [41, 51]
assert view.flat_map(lambda value: (value,), shape=Shape2(1, 2)).unwrap().flatten().unwrap() == [40, 50]
failure = Failed(Err(ErrorCode.APPLICATION_ERROR, 'installed-callback'))
failed = view.map(lambda value: failure)
assert failed.is_failed() and failed.error.value.callback_result is failure
assert failed.error.value.callback_index == 0
assert view.map(lambda value: Ok(value)).unwrap().flatten().unwrap() == [40, 50]
def mutate_during_map(value):
    view.set_many([((0, 0), 0), ((0, 1), 0)]).unwrap()
    return value
assert view.map(mutate_during_map).unwrap().flatten().unwrap() == [40, 50]
assert view.flatten().unwrap() == [0, 0]
assert list(iterator_before_update) == [40, 50]
lazy_calls = []
def lazy_callback(value):
    lazy_calls.append(value)
    return Ok(value + 1)
lazy = MappedMultiArrayView.create(source=view, callback=lazy_callback).unwrap()
assert lazy.shape.dims == (1, 2) and len(lazy) == 2 and lazy_calls == []
assert view.set(indices=(0, 0), value=42).is_ok()
assert lazy.at((0, 0)).unwrap() == 43 and lazy_calls == [42]
lazy_snapshot = lazy.materialize().unwrap()
assert lazy_snapshot.flatten().unwrap() == [43, 1]
assert view.set(indices=(0, 0), value=99).is_ok()
assert lazy.at((0, 0)).unwrap() == 100
assert lazy_snapshot.at((0, 0)).unwrap() == 43
lazy_failure = MappedMultiArrayView.create(source=lazy, callback=lambda value: failure).unwrap()
failed = lazy_failure.at((0, 0))
assert failed.is_failed() and failed.error.value.callback_result is failure
assert failed.error.value.callback_index == 0
assert MultiArray.from_numpy(values=source, copy=False).is_failed()
def view_cycle_smoke():
    payload = Payload()
    owner = MutableMultiArray.create(values=[payload], shape=Shape.create(dims=(1,)).unwrap()).unwrap()
    payload.owner = owner.view(offsets=(0,), shape=Shape.create(dims=(1,)).unwrap()).unwrap()
    return weakref.ref(payload)
reference = view_cycle_smoke()
gc.collect()
assert reference() is None
def lazy_cycle_smoke():
    payload = Payload()
    owner = MultiArray.create(values=[payload], shape=Shape.create(dims=(1,)).unwrap()).unwrap()
    payload.owner = MappedMultiArrayView.create(source=owner, callback=lambda value: value).unwrap()
    assert payload.owner.at((0,)).unwrap() is payload
    return weakref.ref(payload)
reference = lazy_cycle_smoke()
gc.collect()
assert reference() is None
actual = _native.build_info()['native_solvers']
assert set(actual.split(',')) - {''} == set(sys.argv[1:])
assert MetaModel(name='installed').name == 'installed'
model = MetaModelFloat64.create('rust-owned').unwrap()
assert model.generation().unwrap() == 0
x = model.add_variables([VariableSpec(name='x', lower=0, upper=public_exact_float(public_bound))]).unwrap()[0]
assert model.set_objective(terms=[(x, public_exact_float(public_cost))], sense='maximize').unwrap() is None
assert model.add_constraints([ConstraintSpec(name='capacity', terms=[(x, 1)], relation='<=', rhs=3)]).unwrap() is None
source_handle = model.constraint_handles().unwrap()[0]
assert source_handle.name == 'capacity' and source_handle.relation == '<='
assert model.constraint_index(handle=source_handle).unwrap() == 0
assert model.snapshot().unwrap()[2] == 1
assert model.set_bounds(handle=x, lower=0, upper=2).unwrap() is None
generation = model.generation().unwrap()
assert model.set_bounds(handle=x, lower=2, upper=1).is_failed()
assert model.generation().unwrap() == generation == 4
projection = model.create_projection(
    decisions=[ColumnDecisionSpec(id='x', block='a', variable=x)], blocks=['a']
).unwrap()
assert projection.add_columns([ColumnSpec(id='zero', block='a', values={'x': 0})]).is_ok()
master = projection.build_master().unwrap()
assert master.source_generation == generation and master.columns == 1
assert projection.add_columns([ColumnSpec(id='zero', block='a', values={'x': 1})]).is_failed()
assert projection.master_info().unwrap() == master
assert projection.pricing_request(block='a').is_failed()
try:
    _native.ColumnPricingRequest()
    raise AssertionError('pricing request must not be constructible')
except TypeError:
    pass
for solver in sys.argv[1:]:
    bunch_selection = solve_bunch_columns(**bunch_args, solver=solver).unwrap().solution.unwrap()
    assert bunch_selection.columns == bunch_columns and bunch_selection.cost == (-3, 1)
    joint_selection = solve_bunch_columns(**joint_args, solver=solver).unwrap().solution.unwrap()
    assert joint_selection.columns == (joint_columns[0], joint_columns[2]) and joint_selection.cost == (3, 1)
    task_output = solve_task_columns(**task_args, solver=solver).unwrap()
    task_selection = task_output.solution.unwrap()
    assert task_selection.columns == (task_columns[0],) and task_selection.makespan == 1.0
    assert task_output.report.solution_presence == 'OPTIMAL'
    activity_solved = solve_activity(**activity_args, solver=solver).unwrap()
    activity_schedule = activity_solved.solution.unwrap()
    assert [(item.task, item.start_ns, item.end_ns) for item in activity_schedule.placements] == [('a', 0, 2), ('b', 3, 5)]
    assert activity_schedule.cost == (2, 1) and activity_schedule.cancelled == ()
    optional = solve_activity(horizon_ns=(0, 2), resources=(), activities=(
        Activity(id='empty-column', modes=(Mode(id='selected', duration_ns=0, starts_ns=(0,),
            resources=(), cost=Rational.create(numerator=-1).unwrap()),), cancellation_cost=bpp_zero),
        Activity(id='cancelled', modes=(), cancellation_cost=bpp_one),
    ), dependencies=(), cost_unit=weight_unit, max_work=1000, solver=solver).unwrap()
    optional_schedule = optional.solution.unwrap()
    assert [item.task for item in optional_schedule.placements] == ['empty-column']
    assert optional_schedule.cancelled == ('cancelled',) and optional_schedule.cost == (0, 1)
    forced_cancel = solve_activity(horizon_ns=(0, 2), resources=(), activities=(
        Activity(id='optional', modes=(Mode(id='selected', duration_ns=1, starts_ns=(0,),
            resources=(), cost=bpp_zero),), cancellation_cost=bpp_one),
    ), dependencies=(), rows=(Row(id='cancel', unit=weight_unit, coefficients=(),
        cancellation_coefficients=(('optional', bpp_one),), lower=bpp_one),),
        cost_unit=weight_unit, max_work=1000, solver=solver).unwrap().solution.unwrap()
    assert forced_cancel.placements == () and forced_cancel.cancelled == ('optional',)
    assert forced_cancel.cost == (1, 1)
    impossible_args = {**activity_args, 'rows': (Row(id='require-b0', unit=weight_unit,
        coefficients=(('b', 'm', 0, bpp_one),), lower=bpp_one),)}
    impossible_activity = solve_activity(**impossible_args, solver=solver).unwrap()
    assert impossible_activity.report.problem_status == 'INFEASIBLE'
    assert impossible_activity.solution.is_failed()
    solved = projection.solve_master_lp(solver=solver).unwrap()
    assert solved.pricing.is_ok() and abs(solved.report.objective) < 1e-8
    pricing = projection.pricing_request(block='a').unwrap()
    assert abs(projection.reduced_cost(request=pricing, values={'x': 1}).unwrap() + 1) < 1e-8
    priced = projection.solve_pricing(request=pricing, solver=solver).unwrap()
    candidate = priced.candidate.unwrap()
    assert abs(candidate.values['x'] - 2) < 1e-8 and abs(candidate.reduced_cost + 2) < 1e-8
    bound = priced.bound.unwrap()
    bound_info = projection.pricing_bound_info(bound=bound).unwrap()
    assert bound_info.block == 'a' and abs(bound_info.reported_cx_lower + 2) < 1e-8
    assert abs(bound_info.convexity_price) < 1e-8 and not bound_info.reported_nonnegative
    assert projection.solve_master_lp(solver='unknown').is_failed()
    assert projection.pricing_info(request=pricing).is_failed()
    assert projection.pricing_bound_info(bound=bound).is_failed()
    assert projection.solve_master_lp(solver=solver).unwrap().pricing.is_ok()
    pricing = projection.pricing_request(block='a').unwrap()
    candidate = projection.solve_pricing(request=pricing, solver=solver).unwrap().candidate.unwrap()
    assert projection.add_priced_batch([(pricing, [ColumnSpec(id='priced', block='a', values=candidate.values)])]).is_ok()
    projection.build_master(integer=True).unwrap()
    final = projection.solve_master_integer(solver=solver).unwrap()
    assert abs(final.report.objective + 2) < 1e-8
    assert abs(projection.solution_value(solution=final.solution.unwrap(), handle=x).unwrap() - 2) < 1e-8
    assert projection.remove_columns(['priced']).is_ok()
    projection.build_master().unwrap()
assert projection.close().unwrap() is None
phase = model.create_projection(
    decisions=[ColumnDecisionSpec(id='x', block='a', variable=x)], blocks=['a']
).unwrap()
assert phase.build_master(phase_one=True).unwrap().phase_one
assert phase.build_master(integer=True, phase_one=True).is_failed()
assert phase.master_info().unwrap().phase_one and phase.columns().unwrap() == []
for solver in sys.argv[1:]:
    assert phase.build_master(phase_one=True).unwrap().phase_one
    first = phase.solve_master_lp(solver=solver).unwrap()
    assert first.pricing.is_ok() and abs(first.report.objective - 1) < 1e-8
    request = phase.pricing_request(block='a').unwrap()
    candidate = phase.solve_pricing(request=request, solver=solver).unwrap().candidate.unwrap()
    assert abs(candidate.reduced_cost + 1) < 1e-8
    assert phase.add_priced_batch([(request, [ColumnSpec(id='phase-seed', block='a', values=candidate.values)])]).is_ok()
    assert phase.pricing_info(request=request).is_failed()
    phase.build_master(phase_one=True).unwrap()
    feasible = phase.solve_master_lp(solver=solver).unwrap()
    assert feasible.pricing.is_ok() and abs(feasible.report.objective) < 1e-8
    request = phase.pricing_request(block='a').unwrap()
    assert not phase.build_master().unwrap().phase_one
    assert phase.pricing_info(request=request).is_failed()
    assert phase.remove_columns(['phase-seed']).is_ok()
assert phase.close().unwrap() is None
invalid_control = SolveHandle()
invalid_limit = model.solve(solver='unknown', time_limit=1e-20, cancellation=invalid_control)
assert invalid_limit.is_failed() and invalid_limit.error.code is ErrorCode.ILLEGAL_ARGUMENT
assert invalid_control.phase == 'READY'
for solver in sys.argv[1:]:
    bpp_lp = bpp_pool.solve_lp(solver=solver).unwrap()
    assert bpp_lp.report.model_generation == 1 and bpp_lp.solution.unwrap().model_objective == (1, 1)
    bpp_final = bpp_final_pool.solve_final_milp(solver=solver, expansion_limit=3).unwrap()
    assert bpp_final.report.model_generation == 0
    assert bpp_final.report.model_identity != bpp_final_pool.snapshot().unwrap().model_identity
    assert bpp_final.solution.unwrap().model_objective == (2, 1)
    assert bpp_final.solution.unwrap().indicators == {'flag': '1'}
    assert bpp_final_stages[-1] == 'final_milp'
    bpp_control = SolveHandle()
    bpp_solved = bpp.solve(
        solver=solver, max_patterns=100, max_nodes=1000, expansion_limit=3,
        cancellation=bpp_control,
    ).unwrap()
    assert bpp_solved.candidate_complete and bpp_control.phase == 'FINISHED'
    assert len(bpp_solved.columns) == 7 and bpp_solved.report.objective == 1
    assert bpp_solved.solution.unwrap().packed[5] == (1, 1)
    assert bpp_solved.solution.unwrap().model_objective == (1, 1)
    assert bpp_solved.solution.unwrap().indicators == {}
    assert bpp_solved.solution.unwrap().usages == [('bin', {'a': 1, 'b': 1, 'c': 1}, 1)]
    bpp_filtered = bpp.solve(
        solver=solver, max_patterns=100, max_nodes=1000, expansion_limit=3,
        policy=lambda pattern: len(pattern[1]) == 1,
    ).unwrap()
    assert bpp_filtered.candidate_complete and len(bpp_filtered.columns) == 3
    assert bpp_filtered.solution.unwrap().packed[5] == (3, 1)
    assert bpp_filtered.solution.unwrap().model_objective == (3, 1)
    bpp_extended = bpp.solve(
        solver=solver, max_patterns=100, max_nodes=1000, expansion_limit=3,
        extension=PatternExtension(register=bpp_register, extract_solution=bpp_extract),
    ).unwrap()
    assert len(bpp_extended.compiled_columns) == len(bpp_extended.report.values) == 8
    assert len(bpp_extended.columns) == 7
    assert bpp_extended.solution.unwrap().packed[5] == (1, 1)
    assert bpp_extended.solution.unwrap().model_objective == (3, 1)
    assert bpp_extended.solution.unwrap().indicators == {'enabled': '1'}
    if solver == 'scip':
        bpp_unused = SolveHandle()
        assert bpp.solve(solver=solver, max_patterns=100, max_nodes=1000,
                         expansion_limit=3, time_limit=10, cancellation=bpp_unused).is_failed()
        assert bpp_unused.phase == 'READY'
    control = SolveHandle()
    events = []
    def installed_progress(event):
        events.append(event)
        return mutable.set(indices=(0, 0), value=0)
    report = model.solve(
        solver=solver, time_limit=10.25, cancellation=control, on_progress=installed_progress
    ).unwrap()
    generation = model.generation().unwrap()
    assert report.model_identity == model.model_identity and report.model_generation == generation
    assert report.problem_status == 'FEASIBLE'
    assert abs(report.objective - 2) < 1e-8
    provenance = json.loads(report.raw_json)['provenance']
    assert provenance['requestedConfiguration']['time_limit'] == 'Some(10.25)'
    assert provenance['effectiveConfiguration']['time_limit'] == 'Some(10.25)'
    assert control.phase == 'FINISHED'
    assert control.completed_at_epoch_ms is not None
    assert events and events[-1].terminal
    assert all(event.model_identity == model.model_identity for event in events)
    assert model.solve(solver=solver, cancellation=control).is_failed()
    assert model.set_bounds(handle=x, lower=0, upper=1).is_ok()
    limited = model.solve(solver=solver).unwrap()
    assert limited.model_generation == generation + 1 and report.model_generation == generation
    assert abs(limited.objective - 1) < 1e-8
    assert abs(report.objective - 2) < 1e-8
    assert model.set_bounds(handle=x, lower=0, upper=2).is_ok()
    assert model.generation().unwrap() == generation + 2
    cancelled = SolveHandle()
    assert cancelled.cancel(reason='installed-smoke').unwrap()
    report = model.solve(solver=solver, cancellation=cancelled).unwrap()
    assert report.termination_reason == 'CANCELLED'
    assert cancelled.cancellation_preceded_completion
    result = model.solve(solver=solver, on_progress=lambda _: 123)
    assert result.is_failed() and result.error.value.error_class == 'CALLBACK'
    assert model.set_bounds(handle=x, lower=0, upper=None).is_ok()
    compiled = model.solve_compiled(solver=solver).unwrap()
    certificate = compiled.certificate.unwrap()
    assert compiled.report.objective is not None and abs(compiled.report.objective + 3) < 1e-8
    assert abs(model.source_price(certificate=certificate, handle=source_handle).unwrap() - 1) < 1e-8
    assert model.source_price(certificate=compiled.report, handle=source_handle).is_failed()
    if solver == 'scip':
        unused = SolveHandle()
        assert model.solve_compiled(solver=solver, time_limit=10, cancellation=unused).is_failed()
        assert unused.phase == 'READY'
    assert model.set_bounds(handle=x, lower=0, upper=2).is_ok()
    assert model.source_price(certificate=certificate, handle=source_handle).is_failed()
assert model.close().unwrap() is None
for solver in sys.argv[1:]:
    third = MetaModelFloat64.create('unrepresentable-third').unwrap()
    value = third.add_variables([VariableSpec(name='x', lower=0, upper=1)]).unwrap()[0]
    third.add_constraints([ConstraintSpec(name='third', terms=[(value, 3)], relation='==', rhs=1)]).unwrap()
    third.set_objective(terms=[(value, 1)], sense='minimize').unwrap()
    compiled = third.solve_compiled(solver=solver).unwrap()
    assert compiled.report.termination_reason == 'COMPLETED' and compiled.certificate.is_failed()
    projected = third.create_projection(decisions=[], blocks=['a']).unwrap()
    projected.add_columns([ColumnSpec(id='empty', block='a', values={})]).unwrap()
    projected.build_master().unwrap()
    attempt = projected.solve_master_lp(solver=solver).unwrap()
    assert attempt.report.termination_reason == 'COMPLETED' and attempt.pricing.is_failed()
    assert projected.pricing_request(block='a').is_failed()
    assert projected.close().is_ok() and third.close().is_ok()
assert bpp_pool.close().is_ok() and bpp_pool.snapshot().is_failed()
assert bpp_final_pool.close().is_ok() and bpp_final_pool.snapshot().is_failed()
for solver in sys.argv[1:]:
    for public_type in (PublicArray, PublicMutableArray):
        for order in StorageOrder:
            shared = np.empty(2, dtype=object)
            shared[0], shared[1] = Quantity(Fraction(1, 2), METER), Quantity(Fraction(99), METER)
            public = public_type(Shape2(1, 2, order), shared)
            def double_length(value):
                shared[1] = Quantity(Fraction(3, 2), METER)
                return (value * 2).unwrap()
            configs = public.map(double_length).unwrap().flat_map(lambda value: iter((value, (value*2).unwrap()))).unwrap()
            configured = public_type(Shape2(2, 2, order), configs._data)
            flattened = configured.flatten().unwrap()
            reshaped = public_type(configured.shape, flattened._data).reshape(DynShape((2, 2), order)).unwrap()
            coordinate_source = public_type(reshaped.shape, reshaped._data).transpose().unwrap()
            materialized = PublicView(coordinate_source).map(lambda value: value).materialize().unwrap()
            for row in range(2):
                for column in range(2):
                    assert materialized.get(row, column) == coordinate_source.get(row, column)
            leaves = materialized._data.tolist()
            assert [leaf.value for leaf in leaves] == [1, 2, 3, 6]
            assert all(leaf.unit is METER for leaf in leaves)
            lengths = [Rational.from_value(leaf.value).unwrap().to_float().unwrap() for leaf in leaves]
            profits = [Rational.from_value(leaf.value*Fraction(3, 2)).unwrap().to_float().unwrap() for leaf in leaves]
            installed_model = MetaModelFloat64.create('installed-public-mapping').unwrap()
            try:
                variables = installed_model.add_variables([VariableSpec(name=f'config-{index}', kind='binary') for index in range(4)]).unwrap()
                assert installed_model.add_constraints([
                    ConstraintSpec(name='length', terms=list(zip(variables, lengths)), relation='<=', rhs=3.5),
                    ConstraintSpec(name='one', terms=[(variable, 1) for variable in variables], relation='<=', rhs=1),
                ]).is_ok()
                assert installed_model.set_objective(terms=list(zip(variables, profits)), sense='maximize').is_ok()
                report = installed_model.solve(solver=solver).unwrap()
                assert report.solution_presence == 'OPTIMAL'
                assert all(abs(a-b)<1e-8 for a,b in zip(report.values, (0, 0, 1, 0)))
                assert abs(report.objective-4.5)<1e-8
            finally:
                assert installed_model.close().is_ok()
for sdk in ('gurobipy', 'pyscipopt', 'coptpy', 'mindoptpy'):
    assert importlib.util.find_spec(sdk) is None, sdk
print(json.dumps({'native_file': _native.__file__, 'build_info': _native.build_info(), 'logistic_candidate': 'tested'}))
"""
    script = workspace / "smoke.py"
    script.write_text(code, encoding="utf-8")
    subprocess.run(
        [str(python), "-I", str(script), *native_solvers],
        cwd=workspace,
        env=environment,
        check=True,
    )


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True, type=Path)
    parser.add_argument("--sdist", type=Path)
    parser.add_argument(
        "--native-solver",
        action="append",
        choices=["scip", "gurobi10", "gurobi11", "gurobi12"],
        default=[],
        help="Expected compiled backend; also enabled when rebuilding the sdist",
    )
    arguments = parser.parse_args()
    wheel = arguments.wheel.resolve()
    source = arguments.sdist.resolve() if arguments.sdist else None
    try:
        issues = _inspect_wheel(wheel)
        if source:
            issues.extend(_inspect_sdist(source))
        if issues:
            print("\n".join(issues), file=sys.stderr)
            return 1
        with tempfile.TemporaryDirectory(prefix="ospf-distribution-") as temporary:
            workspace = Path(temporary).resolve()
            root = Path(__file__).resolve().parents[1]
            if not workspace.is_relative_to(
                Path(tempfile.gettempdir()).resolve()
            ) or workspace.is_relative_to(root):
                print(
                    "Expected a temporary verification directory outside the checkout",
                    file=sys.stderr,
                )
                return 1
            environment = os.environ.copy()
            for variable in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
                environment.pop(variable, None)
            subprocess.run(
                [sys.executable, "-m", "venv", str(workspace / "env")],
                env=environment,
                check=True,
            )
            python = (
                workspace
                / "env"
                / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            )
            environment["PYO3_PYTHON"] = str(python)
            environment["CARGO_TARGET_DIR"] = str(workspace / "cargo-target")
            subprocess.run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    str(wheel),
                ],
                cwd=workspace,
                env=environment,
                check=True,
            )
            _smoke(
                python=python,
                workspace=workspace,
                environment=environment,
                native_solvers=arguments.native_solver,
            )
            if source:
                build_args = _sdist_build_args(
                    arguments.native_solver,
                    sys.platform,
                )
                destination = workspace / "rebuilt"
                subprocess.run(
                    [
                        str(python),
                        "-m",
                        "pip",
                        "wheel",
                        "--disable-pip-version-check",
                        "--no-cache-dir",
                        "--no-deps",
                        "--config-settings=build-args=" + build_args,
                        "--wheel-dir",
                        str(destination),
                        str(source),
                    ],
                    cwd=workspace,
                    env=environment,
                    check=True,
                )
                rebuilt = list(destination.glob("*.whl"))
                if len(rebuilt) != 1 or _inspect_wheel(rebuilt[0]):
                    print("Invalid rebuilt wheel", file=sys.stderr)
                    return 1
                subprocess.run(
                    [
                        str(python),
                        "-m",
                        "pip",
                        "install",
                        "--disable-pip-version-check",
                        "--force-reinstall",
                        "--no-deps",
                        str(rebuilt[0]),
                    ],
                    cwd=workspace,
                    env=environment,
                    check=True,
                )
                _smoke(
                    python=python,
                    workspace=workspace,
                    environment=environment,
                    native_solvers=arguments.native_solver,
                )
    except (
        OSError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
        tarfile.TarError,
        UnicodeError,
    ) as error:
        print(f"Distribution verification failed: {error}", file=sys.stderr)
        return 1
    configuration = (
        "with native backends: " + ", ".join(arguments.native_solver)
        if arguments.native_solver
        else "without solver SDKs"
    )
    print(f"Distribution verification passed outside the checkout {configuration}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
