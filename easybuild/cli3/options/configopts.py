import os

from easybuild.tools.config import (
    DEFAULT_JOB_BACKEND, DEFAULT_LOGFILE_FORMAT, DEFAULT_MNS, MOD_SEARCH_PATH_HEADERS, DEFAULT_MOD_SEARCH_PATH_HEADERS,
    DEFAULT_MODULE_SYNTAX, DEFAULT_MODULECLASSES, DEFAULT_MODULES_TOOL, DEFAULT_PNS, DEFAULT_REPOSITORY,
    DEFAULT_PATH_SUBDIRS, GENERAL_CLASS, DEFAULT_ENVVAR_USERS_MODULES
)
from easybuild.tools.toolchain.toolchain import DEFAULT_SEARCH_PATH_CPP_HEADERS, DEFAULT_SEARCH_PATH_LINKER, SEARCH_PATH
from easybuild.tools.job.backend import avail_job_backends
from easybuild.tools.module_generator import avail_module_generators
from easybuild.tools.modules import avail_modules_tools
from easybuild.tools.package.utilities import avail_package_naming_schemes
from easybuild.tools.repository.repository import avail_repositories

from .base import OptionsGroup
from ..click_wrapper import click
from .. import types as ctyp


EB_CONFIGURATION_OPTIONS = OptionsGroup(
    "Configuration options",
    "Options related to EasyBuild configuration, such as paths and naming schemes.",
)

DEFAULT_PREFIX = os.path.join(os.path.expanduser('~'), ".local", "easybuild")
SELECTED_PREFIX = None


def prefix_callback(ctx, param, value):
    """Callback for the --prefix option."""
    global SELECTED_PREFIX
    value = value or DEFAULT_PREFIX
    SELECTED_PREFIX = value

    return value

def path_or_prefix_callback_factory(dir_name: str):
    """Factory to create a callback for path options."""
    def path_callback(ctx, param, value):
        """Callback for the specified path option."""
        value = value or os.path.join(SELECTED_PREFIX, dir_name)
        return value
    return path_callback


def EB_PREFIX_PATH_OPTION(long:str, dirname: str, **kwargs):
    """Decorator to create an EasyBuild CLI option for prefix paths."""

    return EB_CONFIGURATION_OPTIONS.eb_option(
        long,
        type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
        callback=path_or_prefix_callback_factory(dirname),
        help=f'Set EasyBuild {dirname} path (default: <prefix>/{dirname}).',
        *kwargs
    )


EB_BUILDPATH_OPTION = EB_PREFIX_PATH_OPTION('--buildpath', 'build')

EB_CONTAINERPATH_OPTION = EB_PREFIX_PATH_OPTION('--containerpath', 'containers')

            # 'envvars-user-modules': ("List of environment variables that hold the base paths for which user-specific "
            #                          "modules will be installed relative to", 'strlist', 'store',
            #                          [DEFAULT_ENVVAR_USERS_MODULES]),

EB_ENVVARS_USER_MODULES_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--envvars-user-modules',
    type=ctyp.DelimitedString(delimiter=','),
    help=(
        'List of environment variables that hold the base paths for which user-specific '
        'modules will be installed relative to.'
    ),
    default=[DEFAULT_ENVVAR_USERS_MODULES],
)

            # 'external-modules-metadata': ("List of (glob patterns for) paths to files specifying metadata "
            #                               "for external modules (INI format)", 'strlist', 'store', None),

EB_EXTERNAL_MODULES_METADATA_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--external-modules-metadata',
    type=ctyp.DelimitedString(delimiter=','),
    help='List of (glob patterns for) paths to files specifying metadata  for external modules (INI format).',
)


EB_FAILED_INSTALL_BUILD_DIR_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--failed-install-build-dirs-path',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help=(
        'Location where build directories are copied if installation fails; '
        'an empty value disables copying of build directories.'
    ),
)

EB_FAILED_INSTALL_LOGS_PATH_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--failed-install-logs-path',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help='Location where log files are copied if installation fails;  an empty value disables copying of log files.',
)

EB_HOOKS_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--hooks',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    help='Location of Python module with hook implementations.',
)

EB_IGNORE_DIRS_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--ignore-dirs',
    type=ctyp.DelimitedString(delimiter=','),
    help='Directory names to ignore when searching for files/dirs.',
    default=['.git', '.svn'],
)

EB_INCLUDE_EASYBLOCKS_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--include-easyblocks',
    type=ctyp.DelimitedPathList(delimiter=',', dir_okay=False),
    help='Location(s) of extra or customized easyblocks.',
)

EB_INCLUDE_MODULE_NAMING_SCHEMES_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--include-module-naming-schemes',
    type=ctyp.DelimitedPathList(delimiter=',', dir_okay=False),
    help='Location(s) of extra or customized module naming schemes.',
)

EB_INCLUDE_TOOLCHAINS_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--include-toolchains',
    type=ctyp.DelimitedPathList(delimiter=',', dir_okay=False),
    help='Location(s) of extra or customized toolchains or toolchain components.',
)

EB_INSTALLPATH_OPTION = EB_PREFIX_PATH_OPTION('--installpath', 'install')

EB_INSTALLPATH_DATA_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--installpath-data',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    help='Install path for data (if None, combine --installpath and --subdir-data)',
)

EB_INSTALLPATH_MODULES_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--installpath-modules',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    help='Install path for modules (if None, combine --installpath and --subdir-modules)',
)

EB_INSTALLPATH_SOFTWARE_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--installpath-software',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    help='Install path for software (if None, combine --installpath and --subdir-software)',
)

EB_JOB_BACKEND_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--job-backend',
    type=click.Choice(sorted(avail_job_backends().keys()), case_sensitive=False),
    help='Backend to use for submitting jobs',
    default=DEFAULT_JOB_BACKEND,
)

EB_LOGFILE_FORMAT_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--logfile-format',
    type=ctyp.DelimitedString(delimiter=','),
    help='Directory name and format of the log file (e.g., "logs,txt")',
    default=DEFAULT_LOGFILE_FORMAT[:],
    metavar='DIR,FORMAT',
)

EB_MODULE_DEPENDS_ON_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--module-depends-on',
    is_flag=True,
    default=True,
    help=(
        'Use depends_on (Lmod 7.6.1+) for dependencies in all generated modules '
        '(implies recursive unloading of modules).'
    ),
)

EB_MODULE_EXTENSIONS_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--module-extensions',
    is_flag=True,
    default=True,
    help='Include "extensions" statement in generated module file (Lua syntax only)',
)

EB_MODULE_NAMING_SCHEME_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--module-naming-scheme',
    default=DEFAULT_MNS,
    help='Module naming scheme to use',
)

EB_MODULE_SEARCH_PATH_HEADERS_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--module-search-path-headers',
    type=click.Choice(sorted(MOD_SEARCH_PATH_HEADERS.keys()), case_sensitive=False),
    default=DEFAULT_MOD_SEARCH_PATH_HEADERS,
    help='Environment variable set by modules on load with search paths to header files',
)

EB_MODULE_SYNTAX_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--module-syntax',
    type=click.Choice(sorted(avail_module_generators().keys()), case_sensitive=False),
    default=DEFAULT_MODULE_SYNTAX,
    help='Syntax to be used for module files',
)

EB_MODULECLASSES_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--moduleclasses',
    type=ctyp.DelimitedString(delimiter=','),
    help=(
        'Extend supported module classes '
        '(For more info on the default classes, use --show-default-moduleclasses)'
    ),
    default=[x[0] for x in DEFAULT_MODULECLASSES],
)

EB_MODULES_FOOTER_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--modules-footer',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    help='Path to file containing footer to be added to all generated module files',
)

EB_MODULES_HEADER_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--modules-header',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    help='Path to file containing header to be added to all generated module files',
)

EB_MODULES_TOOL_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--modules-tool',
    type=click.Choice(sorted(avail_modules_tools().keys()), case_sensitive=False),
    default=DEFAULT_MODULES_TOOL,
    help='Modules tool to use',
)

EB_PACKAGE_NAMING_SCHEME_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--package-naming-scheme',
    type=click.Choice(sorted(avail_package_naming_schemes().keys()), case_sensitive=False),
    default=DEFAULT_PNS,
    help='Packaging naming scheme choice',
)

EB_PREFIX_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--prefix',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    is_eager=True,
    callback=prefix_callback,
    help=f'Set EasyBuild prefix directory (default: {DEFAULT_PREFIX}).',
)

EB_RECURSIVE_MODULE_UNLOAD_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--recursive-module-unload',
    is_flag=True,
    default=False,
    help='Enable generating of modules that unload recursively.',
)

EB_REPOSITORY_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--repository',
    type=click.Choice(sorted(avail_repositories().keys()), case_sensitive=False),
    default=DEFAULT_REPOSITORY,
    help='Repository type, using repositorypath',
)

EB_REPOSITORYPATH_OPTION = EB_PREFIX_PATH_OPTION('--repositorypath', 'ebfiles_repo')

EB_SEARCH_PATH_CPP_HEADERS_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--search-path-cpp-headers',
    type=click.Choice([*SEARCH_PATH["cpp_headers"]], case_sensitive=False),
    default=DEFAULT_SEARCH_PATH_CPP_HEADERS,
    help='Search path used at build time for include directories',
)

EB_SEARCH_PATH_LINKER_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--search-path-linker',
    type=click.Choice([*SEARCH_PATH["linker"]], case_sensitive=False),
    default=DEFAULT_SEARCH_PATH_LINKER,
    help='Search path used at build time by the linker for libraries',
)

EB_SOURCEPATH_OPTION = EB_PREFIX_PATH_OPTION('--sourcepath', 'sources')

EB_SOURCEPATH_DATA_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--sourcepath-data',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    help='Path(s) to where data sources should be downloaded (same as sourcepath if not specified)',
)

EB_SUBDIR_DATA_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--subdir-data',
    type=str,
    help='Installpath subdir for data',
    default=DEFAULT_PATH_SUBDIRS['subdir_data'],
)

EB_SUBDIR_MODULES_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--subdir-modules',
    type=str,
    help='Installpath subdir for modules',
    default=DEFAULT_PATH_SUBDIRS['subdir_modules'],
)

EB_SUBDIR_SOFTWARE_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--subdir-software',
    type=str,
    help='Installpath subdir for software',
    default=DEFAULT_PATH_SUBDIRS['subdir_software'],
)

EB_SUBDIR_USER_MODULES_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--subdir-user-modules',
    type=str,
    help='Base path of user-specific modules relative to --envvars-user-modules',
)

EB_SUFFIX_MODULES_PATH_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--suffix-modules-path',
    type=str,
    help='Suffix for module files install path',
    default=GENERAL_CLASS,
)

EB_TESTOUTPUT_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--testoutput',
    type=click.Path(file_okay=False, dir_okay=False, resolve_path=True),
    help='Path to where a job should place the output (to be set within jobscript)',
)

EB_TMPDIR_OPTION = EB_CONFIGURATION_OPTIONS.eb_option(
    '--tmpdir',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    help='Directory to use for temporary storage',
)
