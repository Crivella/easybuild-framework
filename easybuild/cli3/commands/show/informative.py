from easybuild.tools.docs import avail_cfgfile_constants, avail_easyconfig_constants, avail_easyconfig_licenses

from . import show
from ...click_wrapper import click, get_have_rich_click


def no_help_command(*args, **kwargs):
    """Decorator to create a command that is hidden from help output."""
    kwargs.setdefault('add_help_option', False)
    return show.command(*args, **kwargs)


@no_help_command()
def avail_cfgfile_constants():
    """Show all constants that can be used in configuration files."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def avail_easyconfig_constants():
    """Show all constants that can be used in easyconfigs."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def avail_easyconfig_licenses():
    """Show all license constants that can be used in easyconfigs."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def avail_easyconfig_params():
    """Show all easyconfig parameters (include easyblock-specific ones by using -e)."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def avail_easyconfig_templates():
    """Show all template names and template constants that can be used in easyconfigs."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def avail_hooks():
    """Show list of known hooks."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def avail_toolchain_opts():
    """Show options for toolchain."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def check_conflicts():
    """Check for version conflicts in dependency graphs."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def check_eb_deps():
    """Check presence and version of (required and optional) EasyBuild dependencies."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def dep_graph():
    """Create dependency graph. Output format depends on <ext>, e.g. 'dot', 'png', 'pdf', 'gv'."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def dump_env_script():
    """Dump source script to set up build environment based on toolchain/dependencies."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def last_log():
    """Print location to EasyBuild log file of last (failed) session."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
# @click.option('-v', '--verbose', is_flag=True, help='Show detailed information about easyblocks')
def list_easyblocks(verbose):
    """Show list of available easyblocks."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
# @click.option('-v', '--verbose', is_flag=True, help='Show detailed information about easyblocks')
def list_installed_software(verbose):
    """Show list of installed software."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
# @click.option('-v', '--verbose', is_flag=True, help='Show detailed information about software')
def list_software(verbose):
    """Show list of supported software."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
def list_toolchains():
    """Show list of known toolchains."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
@click.argument('regex', required=False, default='', type=str)
def search(regex):
    """Search for easyconfig files in the robot search path, print full paths."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
@click.argument('regex', required=False, default='', type=str)
def search_filename(regex):
    """Search for easyconfig files in the robot search path, print only filenames."""
    raise NotImplementedError("This command is not implemented yet.")

@no_help_command()
@click.argument('regex', required=False, default='', type=str)
def search_short(regex):
    """Search for easyconfig files in the robot search path, print short paths."""
    raise NotImplementedError("This command is not implemented yet.")


__all__ = [
    'avail_cfgfile_constants',
    'avail_easyconfig_constants',
    'avail_easyconfig_licenses',
]
