import inspect
import socket
import struct
from array import array
from functools import lru_cache, wraps
from itertools import chain
from typing import Callable

try:
    import fcntl

    @lru_cache(maxsize=1)
    def get_local_interfaces() -> dict[str, str]:
        MAX_BYTES = 4096
        SIOCGIFCONF = 0x8912

        buf = array("B", b"\0" * MAX_BYTES)
        ptr, _ = buf.buffer_info()
        packed = struct.pack("iP", MAX_BYTES, ptr)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            res = fcntl.ioctl(sock.fileno(), SIOCGIFCONF, packed)
        nbytes, _ = struct.unpack("iP", res)
        data = buf.tobytes()[:nbytes]
        return {
            data[i : i + 16]
            .partition(b"\0")[0]
            .decode(): socket.inet_ntoa(data[i + 20 : i + 24])
            for i in range(0, nbytes, 40)
        }

except ImportError:
    fcntl = None
    get_local_interfaces = lambda: {}


def get_kwdefaults(__f: Callable):
    if not callable(__f):
        raise TypeError
    try:
        return {
            v.name: v.default
            for v in inspect.signature(__f).parameters.values()
            if v.kind is v.KEYWORD_ONLY and v.default is not v.empty
        } or None
    except Exception:
        return


def kwdefaults_from(*callables: Callable) -> Callable:
    src_kwdefaults = {
        k: v for d in map(get_kwdefaults, callables) for k, v in dict.items(d or {})
    }

    def decorator[**P, R](func: Callable[P, R]) -> Callable[P, R]:
        sig = inspect.signature(func)
        new_sig = inspect.Signature(
            [
                x
                for _, x in sorted(
                    (
                        ((x.kind, i), x)
                        for i, x in enumerate(
                            chain(
                                (
                                    p
                                    for p in sig.parameters.values()
                                    if p.kind is not inspect.Parameter.KEYWORD_ONLY
                                ),
                                (
                                    inspect.Parameter(
                                        k, inspect.Parameter.KEYWORD_ONLY, default=v
                                    )
                                    for k, v in src_kwdefaults.items()
                                ),
                            )
                        )
                    ),
                    key=lambda x: x[0],
                )
            ],
            return_annotation=sig.return_annotation,
        )

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs):
            for k, v in src_kwdefaults.items():
                kwargs.setdefault(k, v)
            return func(*args, **kwargs)

        wrapper.__signature__ = new_sig
        wrapper.__kwdefaults__ = src_kwdefaults.copy() or None
        return wrapper

    return decorator
