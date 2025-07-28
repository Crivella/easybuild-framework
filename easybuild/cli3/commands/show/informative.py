from easybuild.tools.docs import avail_cfgfile_constants, avail_easyconfig_constants, avail_easyconfig_licenses

from . import show
from ...click_wrapper import click, get_have_rich_click

        # opts = OrderedDict({
        #     'avail-cfgfile-constants': ("Show all constants that can be used in configuration files",
        #                                 None, 'store_true', False),
        #     'avail-easyconfig-constants': ("Show all constants that can be used in easyconfigs",
        #                                    None, 'store_true', False),
        #     'avail-easyconfig-licenses': ("Show all license constants that can be used in easyconfigs",
        #                                   None, 'store_true', False),
        #     'avail-easyconfig-params': (("Show all easyconfig parameters (include "
        #                                  "easyblock-specific ones by using -e)"),
        #                                 None, 'store_true', False, 'a'),
        #     'avail-easyconfig-templates': (("Show all template names and template constants "
        #                                     "that can be used in easyconfigs."),
        #                                    None, 'store_true', False),
        #     'avail-hooks': ("Show list of known hooks", None, 'store_true', False),
        #     'avail-toolchain-opts': ("Show options for toolchain", 'str', 'store', None),
        #     'check-conflicts': ("Check for version conflicts in dependency graphs", None, 'store_true', False),
        #     'check-eb-deps': ("Check presence and version of (required and optional) EasyBuild dependencies",
        #                       None, 'store_true', False),
        #     'dep-graph': ("Create dependency graph. Output format depends on <ext>, e.g. 'dot', 'png', 'pdf', 'gv'.",
        #                   None, 'store', None, {'metavar': 'depgraph.<ext>'}),
        #     'dump-env-script': ("Dump source script to set up build environment based on toolchain/dependencies",
        #                         None, 'store_true', False),
        #     'last-log': ("Print location to EasyBuild log file of last (failed) session", None, 'store_true', False),
        #     'list-easyblocks': ("Show list of available easyblocks",
        #                         'choice', 'store_or_None', 'simple', ['simple', 'detailed']),
        #     'list-installed-software': ("Show list of installed software", 'choice', 'store_or_None', 'simple',
        #                                 ['simple', 'detailed']),
        #     'list-software': ("Show list of supported software", 'choice', 'store_or_None', 'simple',
        #                       ['simple', 'detailed']),
        #     'list-toolchains': ("Show list of known toolchains",
        #                         None, 'store_true', False),
        #     'search': ("Search for easyconfig files in the robot search path, print full paths",
        #                None, 'store', None, {'metavar': 'REGEX'}),
        #     'search-filename': ("Search for easyconfig files in the robot search path, print only filenames",
        #                         None, 'store', None, {'metavar': 'REGEX'}),
        #     'search-short': ("Search for easyconfig files in the robot search path, print short paths",
        #                      None, 'store', None, 'S', {'metavar': 'REGEX'}),
        #     'show-config': ("Show current EasyBuild configuration (only non-default + selected settings)",
        #                     None, 'store_true', False),
        #     'show-default-configfiles': ("Show list of default config files", None, 'store_true', False),
        #     'show-default-moduleclasses': ("Show default module classes with description",
        #                                    None, 'store_true', False),
        #     'show-ec': ("Show contents of specified easyconfig(s)", None, 'store_true', False),
        #     'show-full-config': ("Show current EasyBuild configuration (all settings)", None, 'store_true', False),
        #     'show-system-info': ("Show system information relevant to EasyBuild", None, 'store_true', False),
        #     'terse': ("Terse output (machine-readable)", None, 'store_true', False),
        #     'easystack': ("Path to easystack file in YAML format, specifying details of a software stack",
        #                   None, 'store', None),
        # })


@show.command()
def avail_cfgfile_constants():
    """Show all constants that can be used in configuration files."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def avail_easyconfig_constants():
    """Show all constants that can be used in easyconfigs."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def avail_easyconfig_licenses():
    """Show all license constants that can be used in easyconfigs."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def avail_easyconfig_params():
    """Show all easyconfig parameters (include easyblock-specific ones by using -e)."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def avail_easyconfig_templates():
    """Show all template names and template constants that can be used in easyconfigs."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def avail_hooks():
    """Show list of known hooks."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def avail_toolchain_opts():
    """Show options for toolchain."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def check_conflicts():
    """Check for version conflicts in dependency graphs."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def check_eb_deps():
    """Check presence and version of (required and optional) EasyBuild dependencies."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def dep_graph():
    """Create dependency graph. Output format depends on <ext>, e.g. 'dot', 'png', 'pdf', 'gv'."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def dump_env_script():
    """Dump source script to set up build environment based on toolchain/dependencies."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def last_log():
    """Print location to EasyBuild log file of last (failed) session."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
@click.option('-v', '--verbose', is_flag=True, help='Show detailed information about easyblocks')
def list_easyblocks(verbose):
    """Show list of available easyblocks."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
@click.option('-v', '--verbose', is_flag=True, help='Show detailed information about easyblocks')
def list_installed_software(verbose):
    """Show list of installed software."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
@click.option('-v', '--verbose', is_flag=True, help='Show detailed information about software')
def list_software(verbose):
    """Show list of supported software."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
def list_toolchains():
    """Show list of known toolchains."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
@click.argument('regex', required=False, default='', type=str)
def search(regex):
    """Search for easyconfig files in the robot search path, print full paths."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
@click.argument('regex', required=False, default='', type=str)
def search_filename(regex):
    """Search for easyconfig files in the robot search path, print only filenames."""
    raise NotImplementedError("This command is not implemented yet.")

@show.command()
@click.argument('regex', required=False, default='', type=str)
def search_short(regex):
    """Search for easyconfig files in the robot search path, print short paths."""
    raise NotImplementedError("This command is not implemented yet.")


__all__ = [
    'avail_cfgfile_constants',
    'avail_easyconfig_constants',
    'avail_easyconfig_licenses',
]
