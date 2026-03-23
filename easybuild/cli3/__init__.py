import sys

from easybuild.tools.version import this_is_easybuild
from easybuild.base import fancylogger
from easybuild.tools.build_log import EasyBuildError, stop_logging, print_error
from easybuild.tools.filetools import cleanup
from easybuild.tools import options as eb_opts
from easybuild.tools.config import build_option
from easybuild.tools.hooks import load_hooks, run_hook
from easybuild.tools.hooks import BUILD_AND_INSTALL_LOOP, PRE_PREF, POST_PREF, START, END, CANCEL, CRASH, FAIL

from .click_wrapper import click, fancy_install_tracebacks, disable_rich, HAVE_RICH_CLICK
from . import options as opt


def version_callback(ctx, param, value):
    click.echo(this_is_easybuild())
    ctx.exit()


def output_style_callback(ctx, param, value):
    """Callback for the --color option."""
    if value in ['basic']:
        disable_rich()
    return value

EB_OPTIONS = opt.OptionsGroup()


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
@opt.EB_LOG_OPTIONS

@EB_OPTIONS.eb_option(
    '--ignore-index',
    is_flag=True,
    help='Ignore EasyBuild index (not implemented yet).',
)
@EB_OPTIONS.eb_option(
    '--terse',
    is_flag=True,
    help='Enable terse output (not implemented yet).',
)

@EB_OPTIONS.eb_option(
    '--output-style',
    type=click.Choice(['basic', 'rich', 'auto'], case_sensitive=False),
    is_eager=True,
    callback=output_style_callback,
    help='Set color output mode (auto, basic, rich, no_rich).',
)

@EB_OPTIONS.eb_option(
    '--rpath',
    default=True,
    is_flag=True,
    help='Enable RPATH in built software (default: enabled).',
)
@click.pass_context
def eb3(ctx):
    """EasyBuild command line interface."""
    ctx.ensure_object(dict)
    ctx.obj['success'] = True

    hooks = load_hooks(build_option('hooks'))

    def _cleanup(ctx):
        """Cleanup function to stop logging."""
        run_hook(END, hooks)

        logtostdout = build_option('logtostdout')
        logfile = ctx.obj.get('logfile')
        eb_tmpdir = build_option('tmpdir')
        print(f"Logfile: {logfile}, logtostdout: {logtostdout}, eb_tmpdir: {eb_tmpdir}")
        silent = build_option('terse')
        # testing = build_option('testing')
        testing = False

        stop_logging(logfile=logfile, logtostdout=logtostdout)

        if ctx.obj['success']:
            cleanup(logfile, eb_tmpdir, testing, silent)

        click.echo("Exiting EasyBuild CLI...")

    ctx.call_on_close(lambda: _cleanup(ctx))

    run_hook(START, hooks)
    try:
        # click.echo("Starting EasyBuild CLI...")
        fancy_install_tracebacks()
        eb_opts.check_root_usage(build_option('allow_use_as_root'))
        eb_opts.check_python_version()
    except EasyBuildError as err:
        run_hook(FAIL, hooks, args=[err])
        print_error(err.msg, exit_on_error=True, exit_code=err.exit_code)
        ctx.obj['success'] = False
    except KeyboardInterrupt as err:
        run_hook(CANCEL, hooks, args=[err])
        print_error("Cancelled by user: %s" % err)
        ctx.obj['success'] = False
    except Exception as err:
        run_hook(CRASH, hooks, args=[err])
        sys.stderr.write("EasyBuild crashed! Please consider reporting a bug, this should not happen...\n\n")
        ctx.obj['success'] = False
        raise



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
    root_cmd.format_epilog(root_ctx, formatter)

    click.echo_via_pager(formatter.getvalue())


from .commands import *
