from .click_wrapper import click
from . import types as cli_types


from easybuild.main import main_with_hooks
from easybuild.tools.version import this_is_easybuild

def version_callback(ctx, param, value):
    click.echo(this_is_easybuild())
    ctx.exit()

def opt1_callback(ctx, param, value):
    """Callback for the --opt1 option."""
    click.echo(f"Option --opt1 was set to: {value}")
    for k,v in ctx.__dict__.items():
        if k == 'help_config':
            continue
        print(f"|    {k}: {v}")
    # ctx.exit()

def opt2_callback(ctx, param, value):
    """Callback for the --opt2 option."""
    click.echo(f"Option --opt2 was set to: {value}")
    for k,v in ctx.__dict__.items():
        if k == 'help_config':
            continue
        print(f"|   {k}: {v}")
    ctx.exit()

@click.group()
@click.option(
    '--opt1',
    default=1, flag_value=3,
    is_eager=True,
    callback=opt1_callback,
)
@click.option(
    '--opt2',
    default=2, flag_value=4,
    is_eager=True,
    callback=opt2_callback,
)
@click.option(
    '--version',
    is_eager=True,
    is_flag=True,
    expose_value=False,
    callback=version_callback,
    help='Show EasyBuild version and exit.',
)
def eb(opt1, opt2):
    """EasyBuild command line interface."""

@eb.command()
@click.argument('easyconfigs', nargs=-1, type=cli_types.EasyconfigParam(), required=False)
def build():
    """Run an Easyconfig Build."""
    # Placeholder for build command logic
    print("Building...")

@eb.group()
def github():
    """GitHub related commands."""

@github.command()
def sync_pr_with_develop():
    """Sync a pull request with the develop branch."""
    # Placeholder for sync PR logic
    print("Syncing PR with develop...")
