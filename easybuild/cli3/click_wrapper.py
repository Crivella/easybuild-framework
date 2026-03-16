import click as _click

OPT_GROUP = {}
HAVE_RICH_CLICK = False
try:
    import rich_click as click
    # raise ImportError("Simulating ImportError for rich_click to test fallback")
except ImportError:
    import click
else:
    HAVE_RICH_CLICK = True
    # HAVE_RICH_CLICK = False
    OPT_GROUP = click.rich_click.OPTION_GROUPS
    OPT_GROUP.clear()  # Clear existing groups to avoid conflicts

    from rich.traceback import install
    # install(suppress=[click, _click])

def disable_rich():
    """Disable rich formatting in Click."""
    global HAVE_RICH_CLICK
    HAVE_RICH_CLICK = False

def get_have_rich_click():
    """Return whether rich Click is available."""
    return HAVE_RICH_CLICK


def fancy_install_tracebacks():
    """Install rich traceback handler for Click."""
    if HAVE_RICH_CLICK:
        install(suppress=[click, _click])


__all__ = [
    'click',
    'OPT_GROUP',
    'HAVE_RICH_CLICK',
]
