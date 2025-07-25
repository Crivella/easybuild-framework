from .base import eb_option

GROUP="Debug and logging options"

DEBUG_OPTION = eb_option(
    '--debug',
    default=None,
    is_flag=True,
    short='-d',
    help='Enable debug logmode (default: disabled).',
)
INFO_OPTION = eb_option(
    '--info',
    default=None,
    is_flag=True,
    help='Enable info log mode (default: disabled).',
)
QUITE_OPTION = eb_option(
    '--quiet',
    default=None,
    is_flag=True,
    help='Enable quiet/warning log mode (default: disabled).',
)

def EB_DEBUG_LOG_OPTIONS(func):
    """Decorator to register debug log options."""
    func = DEBUG_OPTION(func)
    func = INFO_OPTION(func)
    func = QUITE_OPTION(func)
    return func
