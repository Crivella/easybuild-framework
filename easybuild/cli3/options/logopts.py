from easybuild.base import fancylogger
from easybuild.tools.build_log import init_logging

from .base import OptionsGroup
from ..click_wrapper import click


EB_LOG_OPTIONS = OptionsGroup(
    "Debug and logging options",
    "Options related to logging and debugging."
)

DEVEL_OPTION = EB_LOG_OPTIONS.eb_option(
    '--devel',
    is_eager=True,
    default=None,
    is_flag=True,
    help='Enable development log mode (default: disabled).',
    callback=lambda ctx, param, value: fancylogger.setLogLevel('DEVEL') if value else None,
)

DEBUG_OPTION = EB_LOG_OPTIONS.eb_option(
    '--debug',
    is_eager=True,
    default=None,
    is_flag=True,
    short='-d',
    help='Enable debug logmode (default: disabled).',
    callback=lambda ctx, param, value: fancylogger.setLogLevel('DEBUG') if value else None,
)
INFO_OPTION = EB_LOG_OPTIONS.eb_option(
    '--info',
    is_eager=True,
    default=None,
    is_flag=True,
    help='Enable info log mode (default: disabled).',
    callback=lambda ctx, param, value: fancylogger.setLogLevel('INFO') if value else None,
)
QUITE_OPTION = EB_LOG_OPTIONS.eb_option(
    '--quiet',
    is_eager=True,
    default=None,
    is_flag=True,
    help='Enable quiet/warning log mode (default: disabled).',
    callback=lambda ctx, param, value: fancylogger.setLogLevel('WARNING') if value else None,
)

EB_LOG_TO_STDOUT_OPTION = EB_LOG_OPTIONS.eb_option(
    '--logtostdout',
    is_eager=True,
    is_flag=True,
    help='Redirect main log to stdout',
    callback=lambda ctx, param, value: init_logging(logfile=None, logtostdout=value)[0] if value else None,
)

def tmp_logdir_callback(ctx, param, value):
    _, logfile = init_logging(logfile=None, tmp_logdir=value)
    ctx.obj['logfile'] = logfile
    return value

EB_TMP_LOGDIR_OPTION = EB_LOG_OPTIONS.eb_option(
    '--tmp-logdir',
    is_eager=True,
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True),
    help='Log directory where temporary log files are stored',
    callback=tmp_logdir_callback,
)
