# revshell

`revshell` is a reverse shell payload generator CLI.

## Description

Generates reverse shell commands for different platforms.

Resolves network interface names to IPv4 addresses for `LHOST`.

### Simple usage

```bash
revshell cmd/unix/reverse_bash tun0 4444 -v bash_path='/usr/bin/env bash' -v shell_path=/bin/sh | xclip -sel c

# available payloads
revshell --list

# options for a specific payload
revshell --list-options windows/powershell/reverse_tcp
```

## Installation

Install using `pipx` (recommended):
```bash
pipx install git+https://github.com/crypt0lith/revshell.git
```
