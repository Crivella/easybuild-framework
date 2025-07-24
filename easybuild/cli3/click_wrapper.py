import click as _click

OPT_GROUP = {}
HAVE_RICH_CLICK = False
try:
    import click as _click
    import rich_click as click
except ImportError:
    import click
else:
    HAVE_RICH_CLICK = True
    # HAVE_RICH_CLICK = False
    OPT_GROUP = click.rich_click.OPTION_GROUPS
    OPT_GROUP.clear()  # Clear existing groups to avoid conflicts

    from rich.traceback import install
    # install(suppress=[click, _click])


def fancy_install_tracebacks():
    """Install rich traceback handler for Click."""
    if HAVE_RICH_CLICK:
        install(suppress=[click, _click])


__all__ = [
    'click',
    'OPT_GROUP',
    'HAVE_RICH_CLICK',
]
