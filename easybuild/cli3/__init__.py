import logging
import os

from rich.table import Table
from rich.console import Console

from easybuild.main import main_with_hooks
from easybuild.tools.version import this_is_easybuild

from click.core import ParameterSource
from .click_wrapper import click, fancy_install_tracebacks, get_have_rich_click, disable_rich
from . import types as ctyp
from .options.cli_opt import eb_option
from .options.configfiles import load_configurations

DEFAULT_PREFIX = os.path.join(os.path.expanduser('~'), ".local", "easybuild")
SELECTED_PREFIX = None

def version_callback(ctx, param, value):
    click.echo(this_is_easybuild())
    ctx.exit()

def configfile_callback(ctx, param, value):
    """Callback for the --configfiles option."""
    cfg_dict = load_configurations(value)
    ctx.default_map = cfg_dict
    return value

def output_style_callback(ctx, param, value):
    """Callback for the --color option."""
    if value in ['basic']:
        disable_rich()
    return value

def prefix_callback(ctx, param, value):
    """Callback for the --prefix option."""
    global SELECTED_PREFIX
    value = value or DEFAULT_PREFIX
    SELECTED_PREFIX = value

    return value
    # ctx.obj['prefix'] = SELECTED_PREFIX

def path_or_prefix_callback_factory(dir_name: str):
    """Factory to create a callback for path options."""
    def path_callback(ctx, param, value):
        """Callback for the specified path option."""
        value = value or os.path.join(SELECTED_PREFIX, dir_name)
        return value
    return path_callback

def notimpl_callback(ctx, param, value):
    """Callback for options that are not implemented yet."""
    if value:
        raise NotImplementedError(f"The option {param.name} is not implemented yet.")

# def buildpath_callback(ctx, param, value):
#     """Callback for the --buildpath option."""
#     value = value or os.path.join(DEFAULT_PREFIX, 'build')
#     return value

# def install

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
    is_eager=True,
    type=ctyp.DelimitedPathList(delimiter=',', resolve_full=False),
    # callback=lambda ctx, param, value: set_configuration(load_configurations(value)),
    callback=configfile_callback,
    help='Load EasyBuild configuration files.',
)
@eb_option(
    '--ignoreconfigfiles',
    is_eager=True,
    type=ctyp.DelimitedPathList(delimiter=',', resolve_full=False),
    callback=notimpl_callback,
    help='Ignore EasyBuild configuration files.',
)
# @eb_option(
#     '--opt1',
#     # default=1,
#     is_flag=False,
#     flag_value=3,
#     is_eager=True,
#     # callback=opt1_callback,
#     help='An example option 1.',
# )
# @eb_option(
#     '--opt2',
#     default=1,
#     is_flag=False,
#     flag_value=3,
#     is_eager=True,
#     # callback=opt1_callback,
#     help='An example option 1.',
# )
@eb_option(
    '--output-style',
    type=click.Choice(['basic', 'rich', 'auto'], case_sensitive=False),
    is_eager=True,
    callback=output_style_callback,
    help='Set color output mode (auto, basic, rich, no_rich).',
)
@eb_option(
    '--prefix',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    is_eager=True,
    callback=prefix_callback,
    help=f'Set EasyBuild prefix directory (default: {DEFAULT_PREFIX}).',
)
@eb_option(
    '--buildpath',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    callback=path_or_prefix_callback_factory('build'),
    help='Set EasyBuild build path (default: <prefix>/build).',
)
@eb_option(
    '--installpath',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    callback=path_or_prefix_callback_factory(''),
    help='Set EasyBuild install path (default: <prefix>/install).',
)
@eb_option(
    '--containerpath',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    callback=path_or_prefix_callback_factory('containers'),
    help='Set EasyBuild container path (default: <prefix>/containers).',
)
@eb_option(
    '--repositorypath',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    callback=path_or_prefix_callback_factory('ebfiles_repo'),
    help='Set EasyBuild repository path (default: <prefix>/ebfiles_repo).',
)
@eb_option(
    '--sourcepath',
    default=None,
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    callback=path_or_prefix_callback_factory('sources'),
    help='Set EasyBuild source path (default: <prefix>/sources).',
)
@eb_option(
    '--rpath',
    default=True,
    is_flag=True,
    help='Enable RPATH in built software (default: enabled).',
)
@eb_option(
    '--debug',
    default=None,
    is_flag=True,
    short='-d',
    help='Enable debug logmode (default: disabled).',
)
@eb_option(
    '--info',
    default=None,
    is_flag=True,
    help='Enable info log mode (default: disabled).',
)
@eb_option(
    '--quiet',
    default=None,
    is_flag=True,
    help='Enable quiet/warning log mode (default: disabled).',
)
@click.pass_context
def eb(ctx):
    """EasyBuild command line interface."""
    fancy_install_tracebacks()
    # for k,v in ctx.obj['hidden_params'].items():
    #     # logging.warning(f"Registered hidden parameter: {k} with value: {v}")
    #     click.echo(f"Registering hidden parameter: {k} with value: {v}")
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
    if get_have_rich_click():
        table = Table(title="EasyBuild Configuration")
        table.add_column("Parameter", style="cyan")
        table.add_column("Source", style="magenta")
        table.add_column("Value", style="green")

        for param in sorted(params.keys()):
            source, value = params[param]
            table.add_row(param, source_map.get(source), str(value))

        console = Console()
        console.print(table)
    else:
        for param in sorted(params.keys()):
            source, value = params[param]
            click.echo(f"{param:<30s} ({source_map.get(source)}) = {value}")

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
