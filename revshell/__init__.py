__all__ = ['cmd', 'php', 'windows']

try:
    from ._version import __version__
except ImportError:
    __version__ = "0.0.0"
from . import cmd, php, windows
