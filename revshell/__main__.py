import sys
from ast import literal_eval
from functools import lru_cache
from shlex import quote
from typing import Any, Callable, Iterator, Optional

import regex as re

from . import __name__ as prog
from . import __version__
from .formatters import FORMATTERS, init_formatters
from .util import _signature, get_kwdefaults, get_local_interfaces


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


@lru_cache(maxsize=1)
def py_literal_re_define():
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
    return pattern


@lru_cache(maxsize=1)
def _py_literal_re_pattern():
    pattern = any_of(
        *map(repr, [True, False, None]),
        *map(subroutine, ['number', 'stringliteral']),
    )
    return pattern


@lru_cache(maxsize=1)
def kv_pair_re():
    d = named_groups(key=r'[A-Z_a-z]\w*', literal=_py_literal_re_pattern(), str='.*')
    ident, literal, string = (d[k] for k in ["key", "literal", "str"])
    value = group(literal, string)
    pattern = py_literal_re_define() + f"^{ident}={value}$"
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
        fmt_s %= max(map(len, FORMATTERS)) + 8
    else:
        fmt_s = '{}\t{}'

    from string import whitespace

    norm_space = str.maketrans(dict.fromkeys(whitespace, 0x20))
    out = []
    for k, fn in sorted(FORMATTERS.items(), key=lambda x: x[0]):
        if (fn.__doc__ or "").strip():
            desc = fn.__doc__.splitlines()[0].translate(norm_space).strip()
            out.append(fmt_s.format(k, desc))
        else:
            out.append(k)
    return print(*out, sep='\n')


@lru_cache(maxsize=1)
def get_extra_options(__f: Callable) -> dict[str, Any]:
    return get_kwdefaults(__f) or {}


def print_extra_options(__f: Callable, /, **kwargs):
    kwd_opts = get_extra_options(__f)
    if kwargs.keys() - kwd_opts.keys():
        raise ValueError
    kwd_opts |= kwargs
    sep = "=" if sys.stdout.isatty() else "\t"
    literal_re = re.compile(
        py_literal_re_define() + _py_literal_re_pattern(),
        re.UNICODE,
    )
    out = []
    for k, v in kwd_opts.items():
        k = k.upper()
        if isinstance(v, str):
            if literal_re.fullmatch(v):
                v = '"%s"' % v
        else:
            v = repr(v)
        out.append(f"{k}{sep}{quote(v)}")
    return print(*out, sep='\n')


def main():
    import argparse

    init_formatters()
    payload_options = sorted(FORMATTERS, key=lambda s: s.split('/'))

    def payload_opt(__s: str):
        if __s.isdigit():
            i = int(__s)
            if i < len(payload_options):
                return payload_options[i]
            raise ValueError
        return __s

    from os.path import isfile, samefile

    prog_kwd = (
        {"prog": prog}
        if (isfile(sys.argv[0]) and samefile(sys.argv[0], __file__))
        else {}
    )
    top = argparse.ArgumentParser(
        add_help=False,
        allow_abbrev=False,
        argument_default=argparse.SUPPRESS,
        **prog_kwd,
    )
    top.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    fmt_help = top.add_argument_group('payload help')
    fmt_help.add_argument(
        "-l",
        "--list",
        dest="list_payloads",
        action="store_true",
        help="list all currently available payloads and exit",
    )
    payload_metavar = "PAYLOAD"
    fmt_help.add_argument(
        "--list-options",
        dest="show_options",
        action="store_true",
        help=f"show optional keyword vars and assigned values for {payload_metavar} and exit",
    )
    fmt_parser = argparse.ArgumentParser(
        parents=[top],
        add_help=False,
        allow_abbrev=False,
        argument_default=argparse.SUPPRESS,
        exit_on_error=False,
    )
    fmt_parser.add_argument(
        dest="formatter",
        choices=payload_options,
        type=payload_opt,
        metavar=payload_metavar,
        help="which payload generator to use",
    )
    payload_opts_group = fmt_parser.add_argument_group("payload options")
    var_assign_action = payload_opts_group.add_argument(
        "-v",
        "--assign",
        dest="extra_options",
        action="append",
        type=kv_pair,
        metavar="VAR=VAL",
        help=" ".join(
            [
                "assigns value VAL to variable VAR,",
                "for kwargs to the payload function.",
                "see '--list-options'",
            ]
        ),
        default=argparse.SUPPRESS,
    )
    fmt_args_parser = argparse.ArgumentParser(
        add_help=False,
        allow_abbrev=False,
        argument_default=argparse.SUPPRESS,
        exit_on_error=False,
    )
    fmt_args_parser.add_argument(
        dest="lhost",
        type=localhost,
        metavar="LHOST",
        help="ipv4 address or name of local network interface",
    )
    fmt_args_parser.add_argument(
        dest="lport",
        type=portnumber,
        metavar="LPORT",
        nargs="?",
        default=4444,
        help="listener port",
    )

    fake_parser = argparse.ArgumentParser(
        parents=[fmt_parser, fmt_args_parser],
        description="generate a reverse shell payload",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        allow_abbrev=False,
        **prog_kwd,
    )

    opt_indices = slice(
        1, next((i + 1 for i, x in enumerate(sys.argv[1:]) if x == "--"), None)
    )
    if set(sys.argv[opt_indices]) & {"-h", "--help"}:
        return fake_parser.print_help()
    try:
        ns, rest = top.parse_known_args()
        if getattr(ns, 'list_payloads', False):
            return print_payload_list()
        ns, rest = fmt_parser.parse_known_args(rest, ns)
        formatter = FORMATTERS[ns.formatter]
        kwargs = {}
        if hasattr(ns, "extra_options"):
            kwd_opts = get_extra_options(formatter)
            for k, v in ns.extra_options:
                for x in kwd_opts:
                    if x.casefold() == k.casefold():
                        kwargs[x] = v
                        break
                else:
                    raise argparse.ArgumentError(
                        var_assign_action,
                        f"invalid keyword for {ns.formatter!r}: {k!r}",
                    )
        if getattr(ns, "show_options", False):
            return print_extra_options(formatter, **kwargs)
        ns = fmt_args_parser.parse_args(rest, ns)
    except argparse.ArgumentError as e:
        return fake_parser.error(e)
    else:
        return print(formatter(ns.lhost, ns.lport, **kwargs))


if __name__ == "__main__":
    sys.exit(main())
