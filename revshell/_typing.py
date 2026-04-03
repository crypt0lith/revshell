from typing import Any, Hashable, Protocol


class RevshellCallable(Protocol, Hashable):
    __name__: str
    def __call__(self, lhost: str, lport: int, **kwargs: Any) -> str: ...
