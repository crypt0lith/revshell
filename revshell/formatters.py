import importlib
import inspect
import pkgutil
from collections import defaultdict

import revshell

from ._typing import RevshellCallable
from .util import _signature

FORMATTERS = dict[str, RevshellCallable]()
_M_CACHE = defaultdict(dict)
_PREFIX = f"{revshell.__name__}."


def register[_F: RevshellCallable](__f: _F, /) -> _F:
    caller_frame = inspect.stack()[1].frame
    module_name = caller_frame.f_globals["__name__"]
    module_name = module_name.removeprefix(_PREFIX)
    pos_arg_names = "lhost", "lport"
    for i, p in enumerate(_signature(__f).parameters.values()):
        if i < len(pos_arg_names):
            if (
                p.name != pos_arg_names[i]
                or p.kind > inspect.Parameter.POSITIONAL_OR_KEYWORD
            ):
                raise ValueError
        elif p.kind < inspect.Parameter.KEYWORD_ONLY:
            raise ValueError
    _M_CACHE[module_name][__f.__name__] = __f
    return __f


def init_formatters():
    for module_info in pkgutil.walk_packages(revshell.__path__, prefix=_PREFIX):
        importlib.import_module(module_info.name)
        submodule_name = module_info.name.removeprefix(_PREFIX)
        if submodule_name not in _M_CACHE:
            continue
        parts = submodule_name.split(".")
        for name, f in _M_CACHE[submodule_name].items():
            key = "/".join([*parts, name])
            FORMATTERS[key] = f
