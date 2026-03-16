import os

from easybuild.framework.easyconfig import EASYCONFIGS_PKG_SUBDIR
from easybuild.framework.easyconfig.tools import get_paths_for
from easybuild.framework.easyblock import EXTRACT_STEP, EasyBlock
from easybuild.tools.config import WARN, IGNORE, ERROR

from .base import eb_option as _eb_option
from .. import types as ctyp
from ..click_wrapper import click

_OPTIONS = []

GROUP = "Basic Options"
def eb_option(*args, **kwargs):
    """Decorator to create an EasyBuild configuration option."""
    res = _eb_option(*args, group=GROUP, **kwargs)
    _OPTIONS.append(res)
    return res

ALL_STOPS = [x[0] for x in EasyBlock.get_steps()]
strictness_options = [IGNORE, WARN, ERROR]

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


EB_CONSIDER_ARCHIVED_EASYVONFIGS_OPTION = eb_option(
    '--consider-archived-easyconfigs',
    is_flag=True,
    help='Consider archived easyconfigs when resolving dependencies',
)

EB_DRY_RUN_OPTION = eb_option(
    '--dry-run',
    is_flag=True,
    help='Print build overview incl. dependencies (full paths)',
)

EB_DRY_RUN_SHORT_OPTION = eb_option(
    '--dry-run-short',
    is_flag=True,
    help='Print build overview incl. dependencies (short paths)',
    short='D',
)

EB_EXTENDED_DRY_RUN_OPTION = eb_option(
    '--extended-dry-run',
    is_flag=True,
    short='x',
    help='Perform an extended dry run, show all steps that would be executed',
)

EB_EXTENDED_DRY_RUN_IGNORE_ERRORS_OPTION = eb_option(
    '--extended-dry-run-ignore-errors',
    is_flag=True,
    help='Ignore errors that occur during extended dry run',
)

EB_FORCE_OPTION = eb_option(
    '--force',
    is_flag=True,
    short='f',
    help='Force the build, even if it is already installed or if it is not needed',
)

EB_IGNORE_LOCKS_OPTION = eb_option(
    '--ignore-locks',
    is_flag=True,
    help='Ignore locks that prevent two identical installations running in parallel',
)

EB_JOB_OPTION = eb_option(
    '--job',
    is_flag=True,
    help='Submit the build as a job',
)

EB_LOG_TO_STDOUT_OPTION = eb_option(
    '--logtostdout',
    is_eager=True,
    is_flag=True,
    help='Redirect main log to stdout',
    callback=None,  # Not implemented yet
)

EB_LOCKS_DIR_OPTION = eb_option(
    '--locks-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help=(
        'Directory to store lock files (should be on a shared filesystem); '
        'None implies .locks subdirectory of software installation directory'
    ),
)

EB_MISSING_MODULES_OPTION = eb_option(
    '--missing-modules',
    is_flag=True,
    short='M',
    help='Print list of missing modules for dependencies of specified easyconfigs',
)

EB_ONLY_BLOCKS_OPTION = eb_option(
    '--only-blocks',
    type=ctyp.DelimitedString(delimiter=','),
    help='Only build listed blocks',
    short='b',
    metavar='BLOCKS',
)

EB_REBUILD_OPTION = eb_option(
    '--rebuild',
    is_flag=True,
    help='Rebuild software, even if module already exists (don\'t skip OS dependencies checks)',
)

EB_ROBOT_OPTION = eb_option(
    '--robot',
    is_eager=True,
    is_flag=True,
    # flag_value=[''],
    short='r',
    # type=ctyp.DelimitedPathList(delimiter=',', file_okay=False, resolve_path=False),
    help='Enable dependency resolution, optionally consider additional paths to search for easyconfigs',
    # callback=robot_paths_callback,
)

EB_ROBOT_PATHS_OPTION = eb_option(
    '--robot-path',
    is_eager=True,
    type=ctyp.DelimitedPathList(delimiter=':', file_okay=False, resolve_path=False),
    help='Additional paths to consider by robot for easyconfigs (--robot PATHs get priority)',
    callback=robot_paths_callback,
)

EB_SEARCH_PATHS = eb_option(
    '--search-paths',
    is_eager=True,
    type=ctyp.DelimitedPathList(delimiter=',', file_okay=False),
    help='dditional locations to consider in --search (next to --robot and --robot-paths PATHs)',
)

EB_SKIP_OPTION = eb_option(
    '--skip',
    is_flag=True,
    help='Skip existing software (useful for installing additional packages)',
    short='k',
)

EB_STOP_OPTION = eb_option(
    '--stop',
    is_flag=False,
    flag_value=EXTRACT_STEP,
    type=click.Choice(ALL_STOPS, case_sensitive=False),
    help='Stop the installation after certain step',
    short='s',
)

EB_STRICT_OPTION = eb_option(
    '--strict',
    default=WARN,
    type=click.Choice(strictness_options, case_sensitive=False),
    help='Set strictness level',
)

def EB_BASIC_OPTIONS(func):
    """Decorator to apply all basic options to a function."""
    for opt in _OPTIONS:
        func = opt(func)

    return func
