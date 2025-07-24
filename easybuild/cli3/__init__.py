import logging

from rich.table import Table
from rich.console import Console

from easybuild.main import main_with_hooks
from easybuild.tools.version import this_is_easybuild

from click.core import ParameterSource
from .click_wrapper import click, fancy_install_tracebacks, HAVE_RICH_CLICK
from . import types as ctyp
from .options.cli_opt import eb_option
from .options.configfiles import load_configurations


def version_callback(ctx, param, value):
    click.echo(this_is_easybuild())
    ctx.exit()

def configfile_callback(ctx, param, value):
    """Callback for the --configfiles option."""
    cfg_dict = load_configurations(value)
    ctx.default_map = cfg_dict

@click.group()
# @click.command()
@click.option(
    '--version',
    is_eager=True,
    is_flag=True,
    expose_value=False,
    callback=lambda ctx, param, value: version_callback(ctx, param, value) if value else None,
    help='Show EasyBuild version and exit.',
)
@eb_option(
    '--configfiles',
    # default=None,
    expose_value=False,
    is_eager=True,
    type=ctyp.DelimitedPathList(delimiter=',', resolve_full=False),
    # callback=lambda ctx, param, value: set_configuration(load_configurations(value)),
    callback=configfile_callback,
    help='Load EasyBuild configuration files.',
)
@eb_option(
    '--opt1',
    # default=1,
    is_flag=False,
    flag_value=3,
    is_eager=True,
    # callback=opt1_callback,
    help='An example option 1.',
)
@eb_option(
    '--opt2',
    default=1,
    is_flag=False,
    flag_value=3,
    is_eager=True,
    # callback=opt1_callback,
    help='An example option 1.',
)
@click.pass_context
def eb(ctx):
    """EasyBuild command line interface."""
    fancy_install_tracebacks()
    # click.echo(f"Context: {ctx.obj}")
    # for k,v in ctx.__dict__.items():
    #     if k == 'help_config':
    #         continue
    #     print(f"|    {k}: {v}")

@eb.command()
@click.pass_context
def show_config(ctx: click.Context):
    """Run an Easyconfig Build."""
    source_map = {
        ParameterSource.DEFAULT: 'D',
        ParameterSource.ENVIRONMENT: 'E',
        ParameterSource.DEFAULT_MAP: 'F',
        ParameterSource.COMMANDLINE: 'C',
    }


    params = {}

    ptr = ctx
    while ptr:
        for param, value in ptr.obj.get('hidden_params', {}).items():
            source = ptr._parameter_source.get(param)
            if not source:
                continue
            if source == ParameterSource.DEFAULT and value is None:
                continue
            params[param] = (source, value)
            # table.add_row(param, source_map.get(source), str(value))
        ptr = ptr.parent

    click.echo("#")
    click.echo("# Current EasyBuild configuration:")
    click.echo("# (C: command line argument, D: default value, E: environment variable, F: configuration file)")
    click.echo("#")
    if HAVE_RICH_CLICK:
        table = Table(title="EasyBuild Configuration")
        table.add_column("Parameter", style="cyan")
        table.add_column("Source", style="magenta")
        table.add_column("Value", style="green")

        for param in sorted(params.keys()):
            source, value = params[param]
            table.add_row(param, source_map.get(source, '?'), str(value))

        console = Console()
        console.print(table)
    else:
        for param in sorted(params.keys()):
            source, value = params[param]
            click.echo(f"{param:<30s} ({source_map.get(source, '?')}) = {value}")

# @eb.command()
# @click.argument('easyconfigs', nargs=-1, type=ctyp.EasyconfigParam(), required=False)
# def build():
#     """Run an Easyconfig Build."""
#     # Placeholder for build command logic
#     print("Building...")

# @eb.group()
# def github():
#     """GitHub related commands."""

# @github.command()
# def sync_pr_with_develop():
#     """Sync a pull request with the develop branch."""
#     # Placeholder for sync PR logic
#     print("Syncing PR with develop...")
