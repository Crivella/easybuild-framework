from .. import eb3

@eb3.group()
def show():
    """Show EasyBuild configuration options."""

from .config import config
from .easyconfigs import ec
from .system_info import system_info

__all__ = [
    'show',
    'config',
    'ec',
    'system_info',
]
