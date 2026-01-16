import sys
from ast import literal_eval
from functools import lru_cache
from typing import Any, Callable, Iterator, Optional

from . import __name__ as prog
from .util import _signature, get_kwdefaults, get_local_interfaces


def init_formatters():
    from inspect import Parameter
    from types import FunctionType, ModuleType

    def inner(module: ModuleType) -> Iterator[tuple[str, FunctionType]]:
        for name in getattr(module, '__all__', []):
            x = getattr(module, name)
            if isinstance(x, ModuleType):
                yield from inner(x)
            elif isinstance(x, FunctionType):
                try:
                    sig = _signature(x)
                except Exception:
                    continue

                # signature must accept these as non-varkw kwargs
                varnames = 'lhost', 'lport'

                # validation loop
                for varname in varnames:
                    for p in sig.parameters.values():
                        if p.name == varname and p.kind in {
                            Parameter.POSITIONAL_OR_KEYWORD,
                            Parameter.KEYWORD_ONLY,
                        }:
                            # varname is valid
                            # break inner parameter loop
                            break
                    else:
                        # varname not found or is wrong kind
                        # break outer validation loop
                        break
                else:
                    # signature is valid
                    ident = x.__module__.removeprefix(prog).strip('.')
                    ident = '/'.join(ident.split('.') + [x.__name__])
                    yield (ident, x)

    return dict(inner(sys.modules[prog]))


_REVSHELL_FORMATTERS: dict[str, Callable[..., str]] = init_formatters()


@lru_cache(maxsize=1)
def kv_pair_re():
    def define_groups(**patterns: str):
        res = "(?(DEFINE)%s)" % ''.join(named_groups(**patterns).values())
        return res.format_map({k: subroutine(k) for k in patterns})

    def named_groups(**patterns: str):
        return {k: f"(?P<{k}>{v})" for k, v in patterns.items()}

    def subroutine(__s: str):
        return f"(?&{__s})"

    def any_of(*choices: str):
        return '|'.join(choices)

    def group(*choices: str):
        return f"(?:{any_of(*choices)})"

    def stringprefix():
        from collections import defaultdict
        from itertools import permutations

        d = defaultdict[int, set[str]](set)
        for prefix in ['br', 'b', 'r', 'u']:
            for t in permutations(prefix):
                d[len(prefix)].add(''.join(t))
        return '|'.join(
            ''.join(f"[{c.upper()}{c}]" for c in x)
            for i, xs in sorted(d.items(), key=lambda x: x[0], reverse=True)
            for x in (sorted(xs) if i > 1 else [[''.join(sorted(xs))]])
        )

    pattern = define_groups(
        sign='[+-]',
        digit=r'\d',
        integer=any_of(
            "[1-9](?:_?{digit})*",
            '0'
            + group(
                "(?:_?0)*",
                *(
                    f"[{c.upper()}{c}](?:_?{x})+"
                    for c, x in zip('box', ['[0-1]', '[0-7]', r'\p{{AHex}}'])
                ),
            ),
        ),
        pointfloat=any_of("{digitpart}?{fraction}", r"{digitpart}\."),
        exponentfloat=group("{digitpart}", "{pointfloat}") + "{exponent}",
        digitpart="{digit}(?:_?{digit})*",
        fraction=r'\.{digitpart}',
        exponent="[Ee]{sign}?{digitpart}",
        floatnumber=any_of("{pointfloat}", "{exponentfloat}"),
        imagnumber=group("{floatnumber}", "{digitpart}") + "[Jj]",
        number="{sign}?" + group("{imagnumber}", "{floatnumber}", "{integer}"),
        stringliteral="{stringprefix}?{stringitems}",
        stringprefix=stringprefix(),
        stringescape=r"\\.",
        stringitems=any_of(
            *(f"{q}{group(rf"[^\n{q}\\]", "{stringescape}")}*{q}" for q in "\"\'")
        ),
    )

    from operator import itemgetter

    [ident, literal, string] = itemgetter("key", "literal", "str")(
        named_groups(
            key=r'[A-Z_a-z]\w*',
            literal=any_of(
                *map(repr, [True, False, None]),
                *map(subroutine, ['number', 'stringliteral']),
            ),
            str='.*',
        )
    )
    value = group(literal, string)
    pattern += f"^{ident}={value}$"

    import regex as re

    return re.compile(pattern, re.UNICODE)


def kv_pair(__s: str) -> tuple[str, Optional[Any]]:
    if m := kv_pair_re().match(__s):
        if m["literal"] is not None:
            value = literal_eval(m["literal"])
        elif m["str"]:
            value = m["str"]
        else:
            value = None
        return m["key"], value
    raise ValueError


def localhost(__s: str) -> str:
    return get_local_interfaces().get(__s, __s)


def portnumber(__x: str) -> int:
    n = int(__x, 10)
    if not 0 <= n <= 0x10000:
        raise ValueError
    return n


def print_payload_list():
    if sys.stdout.isatty():
        fmt_s = '{: <%d}{}'
        fmt_s %= max(map(len, _REVSHELL_FORMATTERS)) + 10
    else:
        fmt_s = '{}\t{}'

    from string import whitespace

    norm_space = str.maketrans(dict.fromkeys(whitespace, 0x20))
    return print(
        *(
            (
                fmt_s.format(
                    k, fn.__doc__.splitlines()[0].translate(norm_space).strip()
                )
                if (fn.__doc__ or '').strip()
                else k
            )
            for k, fn in sorted(_REVSHELL_FORMATTERS.items(), key=lambda x: x[0])
        ),
        sep='\n',
    )


def get_extra_options(__f: Callable) -> dict[str, Any]:
    return get_kwdefaults(__f) or {}


def print_extra_options(ident: str):
    from shlex import quote

    sep = '=' if sys.stdout.isatty() else '\t'
    out = []
    for k, v in get_extra_options(_REVSHELL_FORMATTERS[ident]).items():
        if v in {"True", "False", "None", "..."}:
            v = '"%s"' % v
        elif not isinstance(v, str):
            v = repr(v)
        out.append(f"{k.upper()}{sep}{quote(v)}")
    return print(*out, sep='\n')


def main():
    import argparse
    from textwrap import dedent

    payload_options = sorted(_REVSHELL_FORMATTERS, key=lambda s: s.split('/'))

    def payload_opt(__s: str):
        if __s.isdigit():
            i = int(__s)
            if i < len(payload_options):
                return payload_options[i]
        return __s

    top = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    fmt_help = top.add_argument_group('payload help')
    fmt_help.add_argument(
        "-l",
        "--list",
        dest="list_payloads",
        action="store_true",
        help="list all currently available payloads and exit",
    )
    fmt_help.add_argument(
        "--show-options",
        dest="show_options",
        choices=payload_options,
        type=payload_opt,
        metavar="PAYLOAD",
        help="show keyword defaults for a specific payload and exit",
    )

    top_ns, rest = top.parse_known_args()
    if getattr(top_ns, 'list_payloads', False):
        return print_payload_list()
    if hasattr(top_ns, 'show_options'):
        return print_extra_options(top_ns.show_options)

    parser = argparse.ArgumentParser(
        parents=[top],
        description="generate a reverse shell payload",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        dest="formatter",
        choices=payload_options,
        type=payload_opt,
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
        help=dedent("""\
            assigns value VAL to variable VAR,
            for kwargs to the payload function.
            show var defaults with '--show-options'
            """),
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
