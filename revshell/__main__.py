import inspect
import sys
from ast import literal_eval
from functools import lru_cache
from types import FunctionType, ModuleType
from typing import Any, Callable, Iterator, Optional

import regex as re

from . import __name__ as prog
from .util import get_kwdefaults, get_local_interfaces


def init_formatters():
    def inner(module: ModuleType) -> Iterator[tuple[str, FunctionType]]:
        for name in getattr(module, '__all__', []):
            x = getattr(module, name)
            if isinstance(x, ModuleType):
                yield from inner(x)
            elif isinstance(x, FunctionType):
                try:
                    sig = inspect.signature(x)
                except Exception:
                    continue
                for varname in {'lhost', 'lport'}:
                    for p in sig.parameters.values():
                        if p.name == varname and p.kind in {
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            inspect.Parameter.KEYWORD_ONLY,
                        }:
                            break
                    else:
                        break
                else:
                    ident = x.__module__.removeprefix(prog).strip('.')
                    ident = '/'.join(ident.split('.') + [x.__name__])
                    yield (ident, x)

    return {k: v for k, v in inner(sys.modules[prog])}


_REVSHELL_FORMATTERS = init_formatters()


@lru_cache(maxsize=1)
def kv_pair_re():
    def group(__s: str):
        return f"(?:{__s})"

    def named_groups(**patterns: str):
        return [f"(?P<{name}>{pat})" for name, pat in patterns.items()]

    def one_or_more(__s: str):
        return f"{group(__s)}+"

    def any_of(*choices: str):
        return group('|'.join(choices))

    pattern = "(?(DEFINE)%s)"
    pattern %= r"(?P<digit>\d(?:_?\d)*)"
    hex_radix = '[xX]' + one_or_more(r'_?\p{AHex}')
    oct_radix = '[oO]' + one_or_more(r'_?[0-7]')
    bin_radix = '[bB]' + one_or_more(r'_?[0-1]')
    radix = '0' + any_of(hex_radix, oct_radix, bin_radix)
    digit = '(?&digit)'
    float_or_complex = rf"{digit}?\.{digit}?"
    float_or_complex += f"{group('[eE]' + digit)}?[jJ]?"
    float_or_complex = any_of(float_or_complex, digit)
    number = group(f"-?{any_of(radix, float_or_complex)}")
    key, *value = named_groups(
        key=r"[_a-zA-Z][_a-zA-Z\d]*", literal=f"{None}|{number}", str='.*'
    )
    pattern += f"^{key}={any_of(*value)}$"
    return re.compile(pattern)


def kv_pair(__s: str) -> tuple[str, Optional[str | int | float | complex]]:
    if m := kv_pair_re().match(__s):
        k = m["key"]
        v = literal_eval(m["literal"]) if m["literal"] else (m["str"] or None)
        return k, v
    raise ValueError


def localhost(__s: str) -> str:
    return get_local_interfaces().get(__s, __s)


def portnumber(__x: str) -> int:
    n = int(__x, 10)
    if not 0 <= n <= 0x10000:
        raise ValueError
    return n


def print_payload_list():
    return print(
        *(
            f"{k: <40}{fn.__doc__.splitlines()[0]}" if (fn.__doc__ or '').strip() else k
            for k, fn in sorted(_REVSHELL_FORMATTERS.items(), key=lambda x: x[0])
        ),
        sep='\n',
    )


def get_extra_options(__f: Callable) -> dict[str, Any]:
    return get_kwdefaults(__f) or {}


def main():
    import argparse
    from textwrap import dedent

    payload_options = sorted(_REVSHELL_FORMATTERS)

    top = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    fmt_help = top.add_argument_group('payload help')
    fmt_help.add_argument(
        "--list-payloads",
        dest="list_payloads",
        action="store_true",
        help="list all currently available payloads and exit",
    )
    fmt_help.add_argument(
        "--show-options",
        dest="show_options",
        choices=payload_options,
        metavar="PAYLOAD",
        help="show keyword defaults for a specific payload and exit",
    )

    top_ns, rest = top.parse_known_args()
    if getattr(top_ns, 'list_payloads', False):
        return print_payload_list()
    if hasattr(top_ns, 'show_options'):
        formatter = _REVSHELL_FORMATTERS[top_ns.show_options]
        return print(
            *(f"{k.upper()}={v!r}" for k, v in get_extra_options(formatter).items()),
            sep='\n',
        )

    parser = argparse.ArgumentParser(
        parents=[top],
        description="generate a reverse shell payload",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        dest="formatter",
        choices=payload_options,
        metavar="PAYLOAD",
        help="which payload generator to use",
    )
    parser.add_argument(
        dest="lhost",
        type=localhost,
        metavar="LHOST",
        help="ipv4 address or name of local network interface",
    )
    parser.add_argument(
        dest="lport",
        type=portnumber,
        metavar="LPORT",
        nargs="?",
        default=4444,
        help="listener port",
    )
    parser.add_argument(
        "-v",
        "--assign",
        dest="extra_options",
        action="append",
        type=kv_pair,
        metavar="VAR=VAL",
        help=dedent(
            """\
            assigns value VAL to variable VAR,
            for kwargs to the payload function.
            show var defaults with '--show-options'
            """
        ),
        default=argparse.SUPPRESS,
    )
    parsed_args = {
        k: v for k, v in vars(parser.parse_args(rest)).items() if k not in top_ns
    }
    ident = parsed_args.pop("formatter")
    formatter = _REVSHELL_FORMATTERS[ident]
    if "extra_options" in parsed_args:
        extra_options = dict(parsed_args.pop("extra_options"))
        expected = get_extra_options(formatter)
        diff = []
        for k, v in list(extra_options.items()):
            try:
                kx = next(x for x in expected if x.casefold() == k.casefold())
            except StopIteration:
                diff.append(k)
            else:
                if kx not in extra_options:
                    extra_options[kx] = extra_options.pop(k)
        if diff:
            return parser.error(
                'unexpected keywords for {!r}: {}'.format(
                    ident, sorted(set(diff), key=diff.index)
                )
            )
        parsed_args |= extra_options
    return print(formatter(**parsed_args))


if __name__ == "__main__":
    sys.exit(main())
