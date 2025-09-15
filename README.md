# revshell

`revshell` is a reverse shell payload generator CLI.

## Description

Generates reverse shell commands for different platforms.

Resolves network interface names to IPv4 addresses for `LHOST`.

### Simple usage

```bash
revshell cmd/unix/reverse_bash tun0 1337 -v bash_path=/usr/bin/bash -v shell_path=/bin/sh | xclip -sel clip

# View help
revshell --list-payloads
revshell --show-options cmd/unix/reverse_bash
```

## Installation

```bash
git clone https://github.com/crypt0lith/revshell.git
cd revshell
pip install .
```

## Shell completions

```bash
revshell-completions        # bash by default
revshell-completions zsh    # zsh completions
```

## License

MIT
