from ... import eb3
from ...click_wrapper import click
from ... import types as ctyp

@eb3.command()
@click.argument('easyconfigs', nargs=-1, type=ctyp.EasyconfigParam(), required=True)
def build(easyconfigs):
    """Run an Easyconfig Build."""
    # Placeholder for build command logic
    click.echo(f"TODO: Building... {easyconfigs}")

__all__ = [
    'build',
]
