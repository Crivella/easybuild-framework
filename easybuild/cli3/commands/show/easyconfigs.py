from easybuild.tools.filetools import locate_files, read_file
from easybuild.tools.config import build_option

from . import show
from ... import types as ctyp
from ...click_wrapper import click

@show.command()
@click.argument('easyconfigs', nargs=-1, type=ctyp.EasyconfigParam(), required=True)
def ec(easyconfigs):
    """Show Easyconfig file information."""
    robot_paths = build_option('robot_path')
    determined_paths = locate_files(list(easyconfigs), robot_paths)
    for path in determined_paths:
        click.echo(f"Contents of {path}:")
        click.echo(read_file(path))

__all__ = [
    'ec',
]
