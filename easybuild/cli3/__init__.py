import logging
import os

from easybuild.main import main_with_hooks
from easybuild.tools.version import this_is_easybuild
from easybuild.framework.easyconfig import EASYCONFIGS_PKG_SUBDIR
from easybuild.framework.easyconfig.tools import get_paths_for

from .click_wrapper import click, fancy_install_tracebacks, disable_rich, HAVE_RICH_CLICK
from . import types as ctyp
from . import options as opt
from .options.base import OPT_GROUP


def version_callback(ctx, param, value):
    click.echo(this_is_easybuild())
    ctx.exit()

def robot_paths_callback(ctx, param, value):
    """Callback for the --robot-paths option."""
    if value is None:
        value = get_paths_for(subdir=EASYCONFIGS_PKG_SUBDIR, robot_path=None) or []
    flattened = sum((item.split(os.pathsep) for item in value), start=[])
    if flattened and flattened[0] == '':
        default = get_paths_for(subdir=EASYCONFIGS_PKG_SUBDIR, robot_path=None)
        value = default + flattened
    elif flattened and flattened[-1] == '':
        default = get_paths_for(subdir=EASYCONFIGS_PKG_SUBDIR, robot_path=None)
        value = flattened + default

    value = list(filter(None, value))  # Remove empty strings

    return value


def output_style_callback(ctx, param, value):
    """Callback for the --color option."""
    if value in ['basic']:
        disable_rich()
    return value


        # raise NotImplementedError(f"The option {param.name} is not implemented yet.")

@click.group()
@click.option(
    '--version',
    is_eager=True,
    is_flag=True,
    expose_value=False,
    callback=lambda ctx, param, value: version_callback(ctx, param, value) if value else None,
    help='Show EasyBuild version and exit.',
)
@opt.EB_CONFIGURATION_OPTIONS
@opt.EB_BASIC_OPTIONS
@opt.EB_CONFIGFILES_OPTIONS
@opt.EB_DEBUG_LOG_OPTIONS

@opt.eb_option(
    '--ignore-index',
    is_flag=True,
    help='Ignore EasyBuild index (not implemented yet).',
)
@opt.eb_option(
    '--terse',
    is_flag=True,
    help='Enable terse output (not implemented yet).',
)

@opt.eb_option(
    '--output-style',
    type=click.Choice(['basic', 'rich', 'auto'], case_sensitive=False),
    is_eager=True,
    callback=output_style_callback,
    help='Set color output mode (auto, basic, rich, no_rich).',
)

@opt.eb_option(
    '--rpath',
    default=True,
    is_flag=True,
    help='Enable RPATH in built software (default: enabled).',
)
@click.pass_context
def eb3(ctx):
    """EasyBuild command line interface."""
    fancy_install_tracebacks()
    # click.echo(f'OPT_GROUP: {OPT_GROUP}')
    # for k,v in ctx.obj['hidden_params'].items():
    #     # logging.warning(f"Registered hidden parameter: {k} with value: {v}")
    #     click.echo(f"Registering hidden parameter: {k} with value: {v}")
    # click.echo(f"Context: {ctx.obj}")
    # for k,v in ctx.__dict__.items():
    #     if k == 'help_config':
    #         continue
    #     print(f"|    {k}: {v}")


@eb3.command(add_help_option=False)
@click.pass_context
def help_all(ctx):
    """Show help for all commands."""
    root_ctx = ctx
    while root_ctx.parent:
        root_ctx = root_ctx.parent
    formatter = ctx.make_formatter()
    root_cmd = root_ctx.command

    def recursive_display(name, cmd, ctx=None):
        new_ctx = click.Context(cmd, parent=ctx)
        # new_ctx = cmd.make_context(name, args=name.split(' '), parent=ctx)
        if HAVE_RICH_CLICK:
            formatter.config.options_panel_title = f"{name} command"
            formatter.config.commands_panel_title = f"{name} subcommands"
        else:
            formatter.write("\n" + "-" * 80)
            formatter.write(f"\n{name} command:")
        cmd.format_options(new_ctx, formatter)

        if isinstance(cmd, click.Group):
            for sub_name, sub_cmd in cmd.commands.items():
                recursive_display(f"{name} {sub_name}", sub_cmd, ctx=new_ctx)

    root_cmd.format_usage(root_ctx, formatter)
    root_cmd.format_help_text(root_ctx, formatter)
    recursive_display(root_cmd.name, root_cmd)
    # cmd.format_epilog(root_ctx, formatter)

    click.echo_via_pager(formatter.getvalue())


from .commands import *
