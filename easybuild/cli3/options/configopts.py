import os

from easybuild.tools.config import (
    DEFAULT_JOB_BACKEND, DEFAULT_LOGFILE_FORMAT, DEFAULT_MNS, MOD_SEARCH_PATH_HEADERS, DEFAULT_MOD_SEARCH_PATH_HEADERS,
    DEFAULT_MODULE_SYNTAX,
)
from easybuild.tools.job.backend import avail_job_backends
from easybuild.tools.module_generator import avail_module_generators

from .base import eb_option, notimpl_callback
from ..click_wrapper import click
from .. import types as ctyp

GROUP = "Configuration Options"

DEFAULT_PREFIX = os.path.join(os.path.expanduser('~'), ".local", "easybuild")
SELECTED_PREFIX = None

# def config_options(self):
#     # config options
#     descr = ("Configuration options", "Configure EasyBuild behavior.")

#     opts = OrderedDict({
#         'avail-module-naming-schemes': ("Show all supported module naming schemes",
#                                         None, 'store_true', False,),
#         'avail-modules-tools': ("Show all supported module tools",
#                                 None, "store_true", False,),
#         'avail-repositories': ("Show all repository types (incl. non-usable)",
#                                 None, "store_true", False,),
#         'buildpath': ("Temporary build path", None, 'store', mk_full_default_path('buildpath')),
#         'containerpath': ("Location where container recipe & image will be stored", None, 'store',
#                             mk_full_default_path('containerpath')),
#         'envvars-user-modules': ("List of environment variables that hold the base paths for which user-specific "
#                                     "modules will be installed relative to", 'strlist', 'store',
#                                     [DEFAULT_ENVVAR_USERS_MODULES]),
#         'external-modules-metadata': ("List of (glob patterns for) paths to files specifying metadata "
#                                         "for external modules (INI format)", 'strlist', 'store', None),
#         'failed-install-build-dirs-path': ("Location where build directories are copied if installation fails; "
#                                             "an empty value disables copying of build directories",
#                                             None, 'store', None, {'metavar': "PATH"}),
#         'failed-install-logs-path': ("Location where log files are copied if installation fails; "
#                                         "an empty value disables copying of log files",
#                                         None, 'store', None, {'metavar': "PATH"}),
#         'hooks': ("Location of Python module with hook implementations", 'str', 'store', None),
#         'ignore-dirs': ("Directory names to ignore when searching for files/dirs",
#                         'strlist', 'store', ['.git', '.svn']),
#         'include-easyblocks': ("Location(s) of extra or customized easyblocks", 'strlist', 'store', []),
#         'include-module-naming-schemes': ("Location(s) of extra or customized module naming schemes",
#                                             'strlist', 'store', []),
#         'include-toolchains': ("Location(s) of extra or customized toolchains or toolchain components",
#                                 'strlist', 'store', []),
#         'installpath': ("Install path for software and modules",
#                         None, 'store', mk_full_default_path('installpath')),
#         'installpath-data': ("Install path for data (if None, combine --installpath and --subdir-data)",
#                                 None, 'store', None),
#         'installpath-modules': ("Install path for modules (if None, combine --installpath and --subdir-modules)",
#                                 None, 'store', None),
#         'installpath-software': ("Install path for software (if None, combine --installpath and --subdir-software)",
#                                     None, 'store', None),
#         'job-backend': ("Backend to use for submitting jobs", 'choice', 'store',
#                         DEFAULT_JOB_BACKEND, sorted(avail_job_backends().keys())),
#         # purposely take a copy for the default logfile format
#         'logfile-format': ("Directory name and format of the log file",
#                             'strtuple', 'store', DEFAULT_LOGFILE_FORMAT[:], {'metavar': 'DIR,FORMAT'}),
#         'module-depends-on': ("Use depends_on (Lmod 7.6.1+) for dependencies in all generated modules "
#                                 "(implies recursive unloading of modules).",
#                                 None, 'store_true', True),
#         'module-extensions': ("Include 'extensions' statement in generated module file (Lua syntax only)",
#                                 None, 'store_true', True),
#         'module-naming-scheme': ("Module naming scheme to use", None, 'store', DEFAULT_MNS),
#         'module-search-path-headers': ("Environment variable set by modules on load with search paths "
#                                         "to header files", 'choice', 'store', DEFAULT_MOD_SEARCH_PATH_HEADERS,
#                                         sorted(MOD_SEARCH_PATH_HEADERS.keys())),
#         'module-syntax': ("Syntax to be used for module files", 'choice', 'store', DEFAULT_MODULE_SYNTAX,
#                             sorted(avail_module_generators().keys())),
#         'moduleclasses': (("Extend supported module classes "
#                             "(For more info on the default classes, use --show-default-moduleclasses)"),
#                             'strlist', 'extend', [x[0] for x in DEFAULT_MODULECLASSES]),
#         'modules-footer': ("Path to file containing footer to be added to all generated module files",
#                             None, 'store_or_None', None, {'metavar': "PATH"}),
#         'modules-header': ("Path to file containing header to be added to all generated module files",
#                             None, 'store_or_None', None, {'metavar': "PATH"}),
#         'modules-tool': ("Modules tool to use",
#                             'choice', 'store', DEFAULT_MODULES_TOOL, sorted(avail_modules_tools().keys())),
#         'packagepath': ("The destination path for the packages built by package-tool",
#                         None, 'store', mk_full_default_path('packagepath')),
#         'package-naming-scheme': ("Packaging naming scheme choice",
#                                     'choice', 'store', DEFAULT_PNS, sorted(avail_package_naming_schemes().keys())),
#         'prefix': (("Change prefix for buildpath, installpath, sourcepath, sourcepath-data, and repositorypath "
#                     "(used prefix for defaults %s)" % DEFAULT_PREFIX),
#                     None, 'store', None),
#         'recursive-module-unload': ("Enable generating of modules that unload recursively.",
#                                     None, 'store_true', False),
#         'repository': ("Repository type, using repositorypath",
#                         'choice', 'store', DEFAULT_REPOSITORY, sorted(avail_repositories().keys())),
#         'repositorypath': (("Repository path, used by repository "
#                             "(is passed as list of arguments to create the repository instance). "
#                             "For more info, use --avail-repositories."),
#                             'strlist', 'store', self.default_repositorypath),
#         'search-path-cpp-headers': ("Search path used at build time for include directories", 'choice',
#                                     'store', DEFAULT_SEARCH_PATH_CPP_HEADERS, [*SEARCH_PATH["cpp_headers"]]),
#         'search-path-linker': ("Search path used at build time by the linker for libraries", 'choice',
#                                 'store', DEFAULT_SEARCH_PATH_LINKER, [*SEARCH_PATH["linker"]]),
#         'sourcepath': ("Path(s) to where software sources should be downloaded (string, colon-separated)",
#                         None, 'store', mk_full_default_path('sourcepath')),
#         'sourcepath-data': ("Path(s) to where data sources should be downloaded (string, colon-separated) "
#                             "(same as sourcepath if not specified)", None, 'store', None),
#         'subdir-data': ("Installpath subdir for data",
#                         None, 'store', DEFAULT_PATH_SUBDIRS['subdir_data']),
#         'subdir-modules': ("Installpath subdir for modules", None, 'store', DEFAULT_PATH_SUBDIRS['subdir_modules']),
#         'subdir-software': ("Installpath subdir for software",
#                             None, 'store', DEFAULT_PATH_SUBDIRS['subdir_software']),
#         'subdir-user-modules': ("Base path of user-specific modules relative to --envvars-user-modules",
#                                 None, 'store', None),
#         'suffix-modules-path': ("Suffix for module files install path", None, 'store', GENERAL_CLASS),
#         # this one is sort of an exception, it's something jobscripts can set,
#         # has no real meaning for regular eb usage
#         'testoutput': ("Path to where a job should place the output (to be set within jobscript)",
#                         None, 'store', None),
#         'tmp-logdir': ("Log directory where temporary log files are stored", None, 'store', None),
#         'tmpdir': ('Directory to use for temporary storage', None, 'store', None),
#     })

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

    return eb_option(
        long,
        type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
        callback=path_or_prefix_callback_factory(dirname),
        help=f'Set EasyBuild {dirname} path (default: <prefix>/{dirname}).',
        group=GROUP,
        *kwargs
    )

EB_FAILED_INSTALL_BUILD_DIR_OPTION = eb_option(
    '--failed-install-build-dirs-path',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help=(
        'Location where build directories are copied if installation fails; '
        'an empty value disables copying of build directories.'
    ),
    group=GROUP,
)

EB_FAILED_INSTALL_LOGS_PATH_OPTION = eb_option(
    '--failed-install-logs-path',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help=(
        'Location where log files are copied if installation fails; '
        'an empty value disables copying of log files.'
    ),
    group=GROUP,
)

EB_HOOKS_OPTION = eb_option(
    '--hooks',
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    help='Location of Python module with hook implementations.',
    group=GROUP,
)

EB_IGNORE_DIRS_OPTION = eb_option(
    '--ignore-dirs',
    type=ctyp.DelimitedString(delimiter=','),
    help='Directory names to ignore when searching for files/dirs.',
    group=GROUP,
    default=['.git', '.svn'],
)

EB_INCLUDE_EASYBLOCKS_OPTION = eb_option(
    '--include-easyblocks',
    type=ctyp.DelimitedPathList(delimiter=',', resolve_full=False, file_okay=True, dir_okay=False),
    help='Location(s) of extra or customized easyblocks.',
    group=GROUP,
)

EB_INCLUDE_MODULE_NAMING_SCHEMES_OPTION = eb_option(
    '--include-module-naming-schemes',
    type=ctyp.DelimitedPathList(delimiter=',', resolve_full=False, file_okay=True, dir_okay=False),
    help='Location(s) of extra or customized module naming schemes.',
    group=GROUP,
)

EB_INCLUDE_TOOLCHAINS_OPTION = eb_option(
    '--include-toolchains',
    type=ctyp.DelimitedPathList(delimiter=',', resolve_full=False, file_okay=True, dir_okay=False),
    help='Location(s) of extra or customized toolchains or toolchain components.',
    group=GROUP,
)

EB_INSTALLPATH_DATA_OPTION = eb_option(
    '--installpath-data',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    help='Install path for data (if None, combine --installpath and --subdir-data)',
    group=GROUP,
    default=None,
    callback=notimpl_callback
)

EB_INSTALLPATH_MODULES_OPTION = eb_option(
    '--installpath-modules',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    help='Install path for modules (if None, combine --installpath and --subdir-modules)',
    group=GROUP,
    default=None,
    callback=notimpl_callback
)

EB_INSTALLPATH_SOFTWARE_OPTION = eb_option(
    '--installpath-software',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    help='Install path for software (if None, combine --installpath and --subdir-software)',
    group=GROUP,
    default=None,
    callback=notimpl_callback
)

EB_JOB_BACKEND_OPTION = eb_option(
    '--job-backend',
    type=click.Choice(sorted(avail_job_backends().keys()), case_sensitive=False),
    help='Backend to use for submitting jobs',
    group=GROUP,
    default=DEFAULT_JOB_BACKEND,
)

EB_LOGFILE_FORMAT_OPTION = eb_option(
    '--logfile-format',
    type=ctyp.DelimitedString(delimiter=','),
    help='Directory name and format of the log file (e.g., "logs,txt")',
    group=GROUP,
    default=DEFAULT_LOGFILE_FORMAT[:],
    metavar='DIR,FORMAT',
)

EB_MODULE_DEPENDS_ON_OPTION = eb_option(
    '--module-depends-on',
    is_flag=True,
    default=True,
    help=(
        'Use depends_on (Lmod 7.6.1+) for dependencies in all generated modules '
        '(implies recursive unloading of modules).'
    ),
    group=GROUP,
)

EB_MODULE_EXTENSIONS_OPTION = eb_option(
    '--module-extensions',
    is_flag=True,
    default=True,
    help='Include "extensions" statement in generated module file (Lua syntax only)',
    group=GROUP,
)

EB_MODULE_NAMING_SCHEME_OPTION = eb_option(
    '--module-naming-scheme',
    default=DEFAULT_MNS,
    help='Module naming scheme to use',
    group=GROUP,
)

EB_MODULE_SEARCH_PATH_HEADERS_OPTION = eb_option(
    '--module-search-path-headers',
    type=click.Choice(sorted(MOD_SEARCH_PATH_HEADERS.keys()), case_sensitive=False),
    default=DEFAULT_MOD_SEARCH_PATH_HEADERS,
    help='Environment variable set by modules on load with search paths to header files',
    group=GROUP,
)

EB_MODULE_SYNTAX_OPTION = eb_option(
    '--module-syntax',
    type=click.Choice(sorted(avail_module_generators().keys()), case_sensitive=False),
    default=DEFAULT_MODULE_SYNTAX,
    help='Syntax to be used for module files',
    group=GROUP,
)

EB_PREFIX_OPTION = eb_option(
    '--prefix',
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    is_eager=True,
    callback=prefix_callback,
    help=f'Set EasyBuild prefix directory (default: {DEFAULT_PREFIX}).',
)


def EB_CONFIGURATION_OPTIONS(func):
    """Decorator to apply the EB_PREFIX_OPTION to a function."""
    func = EB_FAILED_INSTALL_BUILD_DIR_OPTION(func)
    func = EB_FAILED_INSTALL_LOGS_PATH_OPTION(func)
    func = EB_HOOKS_OPTION(func)
    func = EB_IGNORE_DIRS_OPTION(func)
    func = EB_INCLUDE_EASYBLOCKS_OPTION(func)
    func = EB_INCLUDE_MODULE_NAMING_SCHEMES_OPTION(func)
    func = EB_INCLUDE_TOOLCHAINS_OPTION(func)
    func = EB_INSTALLPATH_DATA_OPTION(func)
    func = EB_INSTALLPATH_MODULES_OPTION(func)
    func = EB_INSTALLPATH_SOFTWARE_OPTION(func)
    func = EB_JOB_BACKEND_OPTION(func)
    func = EB_LOGFILE_FORMAT_OPTION(func)

    func = EB_PREFIX_OPTION(func)

    func = EB_PREFIX_PATH_OPTION('--buildpath', 'build')(func)
    func = EB_PREFIX_PATH_OPTION('--installpath', 'install')(func)
    func = EB_PREFIX_PATH_OPTION('--containerpath', 'containers')(func)
    func = EB_PREFIX_PATH_OPTION('--repositorypath', 'ebfiles_repo')(func)
    func = EB_PREFIX_PATH_OPTION('--sourcepath', 'sources')(func)

    return func
