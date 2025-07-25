import os

from easybuild.framework.easyconfig import EASYCONFIGS_PKG_SUBDIR
from easybuild.framework.easyconfig.tools import get_paths_for
from easybuild.framework.easyblock import EXTRACT_STEP, EasyBlock
from easybuild.tools.config import WARN, IGNORE, ERROR

from .base import eb_option
from .. import types as ctyp
from ..click_wrapper import click

GROUP = "Basic Options"

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


EB_DRY_RUN_OPTION = eb_option(
    '--dry-run',
    is_flag=True,
    help='Print build overview incl. dependencies (full paths)',
    group=GROUP,
)

EB_DRY_RUN_SHORT_OPTION = eb_option(
    '--dry-run-short',
    is_flag=True,
    help='Print build overview incl. dependencies (short paths)',
    short='D',
    group=GROUP,
)

EB_EXTENDED_DRY_RUN_OPTION = eb_option(
    '--extended-dry-run',
    is_flag=True,
    short='x',
    help='Perform an extended dry run, show all steps that would be executed',
    group=GROUP,
)

EB_EXTENDED_DRY_RUN_IGNORE_ERRORS_OPTION = eb_option(
    '--extended-dry-run-ignore-errors',
    is_flag=True,
    help='Ignore errors that occur during extended dry run',
    group=GROUP,
)

EB_FORCE_OPTION = eb_option(
    '--force',
    is_flag=True,
    short='f',
    help='Force the build, even if it is already installed or if it is not needed',
    group=GROUP,
)

EB_IGNORE_LOCKS_OPTION = eb_option(
    '--ignore-locks',
    is_flag=True,
    help='Ignore locks that prevent two identical installations running in parallel',
    group=GROUP,
)

EB_JOB_OPTION = eb_option(
    '--job',
    is_flag=True,
    help='Submit the build as a job',
    group=GROUP,
)

EB_LOG_TO_STDOUT_OPTION = eb_option(
    '--logtostdout',
    is_eager=True,
    is_flag=True,
    help='Redirect main log to stdout',
    callback=None,  # Not implemented yet
    group=GROUP,
)

EB_LOCKS_DIR_OPTION = eb_option(
    '--locks-dir',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True),
    help=(
        'Directory to store lock files (should be on a shared filesystem); '
        'None implies .locks subdirectory of software installation directory'
    ),
    group=GROUP,
)

EB_MISSING_MODULES_OPTION = eb_option(
    '--missing-modules',
    is_flag=True,
    help='Print list of missing modules for dependencies of specified easyconfigs',
    group=GROUP,
)

EB_ONLY_BLOCKS_OPTION = eb_option(
    '--only-blocks',
    type=ctyp.DelimitedString(delimiter=','),
    help='Only build listed blocks',
    short='b',
    group=GROUP,
    metavar='BLOCKS',
)

EB_REBUILD_OPTION = eb_option(
    '--rebuild',
    is_flag=True,
    help='Rebuild software, even if module already exists (don\'t skip OS dependencies checks)',
    group=GROUP,
)

EB_ROBOT_OPTION = eb_option(
    '--robot',
    is_eager=True,
    is_flag=False,
    flag_value=[''],
    short='r',
    type=ctyp.DelimitedPathList(delimiter=',', resolve_full=False),
    help='Enable dependency resolution, optionally consider additional paths to search for easyconfigs',
    group=GROUP,
)

EB_ROBOT_PATHS_OPTION = eb_option(
    '--robot-paths',
    is_eager=True,
    type=ctyp.DelimitedPathList(delimiter=',', resolve_full=False),
    help='Additional paths to consider by robot for easyconfigs (--robot PATHs get priority)',
    callback=robot_paths_callback,
    group=GROUP,
)

EB_SEARCH_PATHS = eb_option(
    '--search-paths',
    is_eager=True,
    type=ctyp.DelimitedPathList(delimiter=',', resolve_full=False),
    help='dditional locations to consider in --search (next to --robot and --robot-paths PATHs)',
    group=GROUP,
)

EB_SKIP_OPTION = eb_option(
    '--skip',
    is_flag=True,
    help='Skip existing software (useful for installing additional packages)',
    short='k',
    group=GROUP,
)

EB_STOP_OPTION = eb_option(
    '--stop',
    is_flag=False,
    flag_value=EXTRACT_STEP,
    type=click.Choice(ALL_STOPS, case_sensitive=False),
    help='Stop the installation after certain step',
    short='s',
    group=GROUP,
)

EB_STRICT_OPTION = eb_option(
    '--strict',
    default=WARN,
    type=click.Choice(strictness_options, case_sensitive=False),
    help='Set strictness level',
    group=GROUP,
)

def EB_BASIC_OPTIONS(func):
    """Decorator to register basic options."""
    func = EB_DRY_RUN_OPTION(func)
    func = EB_DRY_RUN_SHORT_OPTION(func)
    func = EB_EXTENDED_DRY_RUN_OPTION(func)
    func = EB_EXTENDED_DRY_RUN_IGNORE_ERRORS_OPTION(func)

    func = EB_FORCE_OPTION(func)
    func = EB_IGNORE_LOCKS_OPTION(func)
    func = EB_JOB_OPTION(func)
    func = EB_LOG_TO_STDOUT_OPTION(func)
    func = EB_LOCKS_DIR_OPTION(func)
    func = EB_MISSING_MODULES_OPTION(func)
    func = EB_ONLY_BLOCKS_OPTION(func)
    func = EB_REBUILD_OPTION(func)

    func = EB_ROBOT_OPTION(func)
    func = EB_ROBOT_PATHS_OPTION(func)
    func = EB_SEARCH_PATHS(func)

    func = EB_SKIP_OPTION(func)
    func = EB_STOP_OPTION(func)
    func = EB_STRICT_OPTION(func)

    return func
