from typing import Any, Protocol


class RevshellCallable(Protocol):
    def __call__(self, lhost: str, lport: int, **kwargs: Any) -> str:
        ...
