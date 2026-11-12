"""收集所有测试前注册显式 DLL 目录 / Register explicit DLL paths before collecting any tests.

不依赖 native 测试先导入，不修改永久配置。
Do not depend on native tests importing first or change persistent configuration.
"""

from __future__ import annotations

import os

_DLL_DIRECTORIES: list[object] = []
if os.name == "nt":
    for _path in os.environ.get("OSPF_NATIVE_DLL_DIRS", "").split(os.pathsep):
        if _path:
            _DLL_DIRECTORIES.append(os.add_dll_directory(_path))
