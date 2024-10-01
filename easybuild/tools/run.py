# #
# Copyright 2009-2024 Ghent University
#
# This file is part of EasyBuild,
# originally created by the HPC team of Ghent University (http://ugent.be/hpc/en),
# with support of Ghent University (http://ugent.be/hpc),
# the Flemish Supercomputer Centre (VSC) (https://www.vscentrum.be),
# Flemish Research Foundation (FWO) (http://www.fwo.be/en)
# and the Department of Economy, Science and Innovation (EWI) (http://www.ewi-vlaanderen.be/en).
#
# https://github.com/easybuilders/easybuild
#
# EasyBuild is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation v2.
#
# EasyBuild is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EasyBuild.  If not, see <http://www.gnu.org/licenses/>.
# #
"""
Tools to run commands.

Authors:

* Stijn De Weirdt (Ghent University)
* Dries Verdegem (Ghent University)
* Kenneth Hoste (Ghent University)
* Pieter De Baets (Ghent University)
* Jens Timmerman (Ghent University)
* Toon Willems (Ghent University)
* Ward Poelmans (Ghent University)
"""
import contextlib
import fcntl
import functools
import inspect
import locale
import os
import re
import signal
import shutil
import string
import subprocess
import sys
import tempfile
import time
import threading
from collections import namedtuple
from datetime import datetime

try:
    # get_native_id is only available in Python >= 3.8
    from threading import get_native_id as get_thread_id
except ImportError:
    # get_ident is available in Python >= 3.3
    from threading import get_ident as get_thread_id

import easybuild.tools.asyncprocess as asyncprocess
from easybuild.base import fancylogger
from easybuild.tools.build_log import EasyBuildError, dry_run_msg, print_msg, time_str_since
from easybuild.tools.config import ERROR, IGNORE, WARN, build_option
from easybuild.tools.hooks import RUN_SHELL_CMD, load_hooks, run_hook
from easybuild.tools.utilities import nub, trace_msg


_log = fancylogger.getLogger('run', fname=False)


errors_found_in_log = 0

# default strictness level
strictness = WARN


CACHED_COMMANDS = [
    "sysctl -n hw.cpufrequency_max",  # used in get_cpu_speed (OS X)
    "sysctl -n hw.memsize",  # used in get_total_memory (OS X)
    "sysctl -n hw.ncpu",  # used in get_avail_core_count (OS X)
    "sysctl -n machdep.cpu.brand_string",  # used in get_cpu_model (OS X)
    "sysctl -n machdep.cpu.vendor",  # used in get_cpu_vendor (OS X)
    "type module",  # used in ModulesTool.check_module_function
    "type _module_raw",  # used in EnvironmentModules.check_module_function
    "ulimit -u",  # used in det_parallelism
]


RunShellCmdResult = namedtuple('RunShellCmdResult', ('cmd', 'exit_code', 'output', 'stderr', 'work_dir',
                                                     'out_file', 'err_file', 'thread_id', 'task_id'))


class RunShellCmdError(BaseException):

    def __init__(self, cmd_result, caller_info, *args, **kwargs):
        """Constructor for RunShellCmdError."""
        self.cmd = cmd_result.cmd
        self.cmd_name = os.path.basename(self.cmd.split(' ')[0])
        self.exit_code = cmd_result.exit_code
        self.work_dir = cmd_result.work_dir
        self.output = cmd_result.output
        self.out_file = cmd_result.out_file
        self.stderr = cmd_result.stderr
        self.err_file = cmd_result.err_file

        self.caller_info = caller_info

        msg = f"Shell command '{self.cmd_name}' failed!"
        super(RunShellCmdError, self).__init__(msg, *args, **kwargs)

    def print(self):
        """
        Report failed shell command for this RunShellCmdError instance
        """

        def pad_4_spaces(msg):
            return ' ' * 4 + msg

        error_info = [
            '',
            "ERROR: Shell command failed!",
            pad_4_spaces(f"full command              ->  {self.cmd}"),
            pad_4_spaces(f"exit code                 ->  {self.exit_code}"),
            pad_4_spaces(f"working directory         ->  {self.work_dir}"),
        ]

        if self.out_file is not None:
            # if there's no separate file for error/warnings, then out_file includes both stdout + stderr
            out_info_msg = "output (stdout + stderr)" if self.err_file is None else "output (stdout)         "
            error_info.append(pad_4_spaces(f"{out_info_msg}  ->  {self.out_file}"))

        if self.err_file is not None:
            error_info.append(pad_4_spaces(f"error/warnings (stderr)   ->  {self.err_file}"))

        caller_file_name, caller_line_nr, caller_function_name = self.caller_info
        called_from_info = f"'{caller_function_name}' function in {caller_file_name} (line {caller_line_nr})"
        error_info.extend([
            pad_4_spaces(f"called from               ->  {called_from_info}"),
            '',
        ])

        sys.stderr.write('\n'.join(error_info) + '\n')


def raise_run_shell_cmd_error(cmd_res):
    """
    Raise RunShellCmdError for failed shell command, after collecting additional caller info
    """

    # figure out where failing command was run
    # need to go 3 levels down:
    # 1) this function
    # 2) run_shell_cmd function
    # 3) run_cmd_cache decorator
    # 4) actual caller site
    frameinfo = inspect.getouterframes(inspect.currentframe())[3]
    caller_info = (frameinfo.filename, frameinfo.lineno, frameinfo.function)

    raise RunShellCmdError(cmd_res, caller_info)


def run_cmd_cache(func):
    """Function decorator to cache (and retrieve cached) results of running commands."""
    cache = {}

    @functools.wraps(func)
    def cache_aware_func(cmd, *args, **kwargs):
        """Retrieve cached result of selected commands, or run specified and collect & cache result."""
        # cache key is combination of command and input provided via stdin ('stdin' for run, 'inp' for run_cmd)
        key = (cmd, kwargs.get('stdin', None) or kwargs.get('inp', None))
        # fetch from cache if available, cache it if it's not, but only on cmd strings
        if isinstance(cmd, str) and key in cache:
            _log.debug("Using cached value for command '%s': %s", cmd, cache[key])
            return cache[key]
        else:
            res = func(cmd, *args, **kwargs)
            if cmd in CACHED_COMMANDS:
                cache[key] = res
            return res

    # expose clear/update methods of cache to wrapped function
    cache_aware_func.clear_cache = cache.clear
    cache_aware_func.update_cache = cache.update

    return cache_aware_func


run_shell_cmd_cache = run_cmd_cache


def fileprefix_from_cmd(cmd, allowed_chars=False):
    """
    Simplify the cmd to only the allowed_chars we want in a filename

    :param cmd: the cmd (string)
    :param allowed_chars: characters allowed in filename (defaults to string.ascii_letters + string.digits + "_-")
    """
    if not allowed_chars:
        allowed_chars = f"{string.ascii_letters}{string.digits}_-"

    return ''.join([c for c in cmd if c in allowed_chars])


def _answer_question(stdout, proc, qa_patterns, qa_wait_patterns):
    """
    Private helper function to try and answer questions raised in interactive shell commands.
    """
    match_found = False

    stdout_end = stdout.decode(errors='ignore')[-1000:]
    for question, answers in qa_patterns:
        # allow extra whitespace at the end
        question += r'[\s\n]*$'
        regex = re.compile(question.encode())
        res = regex.search(stdout)
        if res:
            _log.debug(f"Found match for question pattern '{question}' at end of stdout: {stdout_end}")
            # if answer is specified as a list, we take the first item as current answer,
            # and add it to the back of the list (so we cycle through answers)
            if isinstance(answers, list):
                answer = answers.pop(0)
                answers.append(answer)
            elif isinstance(answers, str):
                answer = answers
            else:
                raise EasyBuildError(f"Unknown type of answers encountered for question ({question}): {answers}")

            # answer may need to be completed via pattern extracted from question
            _log.debug(f"Raw answer for question pattern '{question}': {answer}")
            answer = answer % {k: v.decode() for (k, v) in res.groupdict().items()}
            answer += '\n'
            _log.info(f"Found match for question pattern '{question}', replying with: {answer}")

            try:
                os.write(proc.stdin.fileno(), answer.encode())
            except OSError as err:
                raise EasyBuildError("Failed to answer question raised by interactive command: %s", err)

            match_found = True
            break
    else:
        _log.info("No match found for question patterns, considering question wait patterns")
        # if no match was found among question patterns,
        # take into account patterns for non-questions (qa_wait_patterns)
        for pattern in qa_wait_patterns:
            # allow extra whitespace at the end
            pattern += r'[\s\n]*$'
            regex = re.compile(pattern.encode())
            if regex.search(stdout):
                _log.info(f"Found match for wait pattern '{pattern}'")
                _log.debug(f"Found match for wait pattern '{pattern}' at end of stdout: {stdout_end}")
                match_found = True
                break
        else:
            _log.info("No match found for question wait patterns")
            _log.debug(f"No match found in question/wait patterns at end of stdout: {stdout_end}")

    return match_found

def _read_pipe(pipe, size, output):
    """Helper function to read from a pipe and store output in a list.
    :param pipe: pipe to read from
    :param size: number of bytes to read
    :param output: list to store output in
    """
    data = pipe.read(size)
    output.append(data)

def read_pipe(pipe, size, timeout=None):
    """Read from a pipe using a separate thread to avoid blocking and implement a timeout.
    :param pipe: pipe to read from
    :param size: number of bytes to read
    :param timeout: timeout in seconds (default: None = no timeout)

    :return: data read from pipe

    :raises TimeoutError: when reading from pipe takes longer than specified timeout
    """

    output = []
    t = threading.Thread(target=_read_pipe, args=(pipe, size, output))
    t.start()
    t.join(timeout)
    if t.is_alive():
        raise TimeoutError()
    return output[0]

def terminate_process(proc, timeout=20):
    """
    Terminate specified process (subprocess.Popen instance).
    Attempt to terminate the process using proc.terminate(), and if that fails, use proc.kill().

    :param proc: process to terminate
    :param timeout: timeout in seconds to wait for process to terminate
    """
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _log.warning(f"Process did not terminate after {timeout} seconds, sending SIGKILL")
    proc.kill()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        raise EasyBuildError(f"Process `{proc.args}` did not terminate after {timeout} seconds, giving up")


@run_shell_cmd_cache
def run_shell_cmd(cmd, fail_on_error=True, split_stderr=False, stdin=None, env=None,
                  hidden=False, in_dry_run=False, verbose_dry_run=False, work_dir=None, use_bash=True,
                  output_file=True, stream_output=None, asynchronous=False, task_id=None, with_hooks=True,
                  timeout=None, qa_patterns=None, qa_wait_patterns=None, qa_timeout=100):
    """
    Run specified (interactive) shell command, and capture output + exit code.

    :param fail_on_error: fail on non-zero exit code (enabled by default)
    :param split_stderr: split of stderr from stdout output
    :param stdin: input to be sent to stdin (nothing if set to None)
    :param env: environment to use to run command (if None, inherit current process environment)
    :param hidden: do not show command in terminal output (when using --trace, or with --extended-dry-run / -x)
    :param in_dry_run: also run command in dry run mode
    :param verbose_dry_run: show that command is run in dry run mode (overrules 'hidden')
    :param work_dir: working directory to run command in (current working directory if None)
    :param use_bash: execute command through bash shell (enabled by default)
    :param output_file: collect command output in temporary output file
    :param stream_output: stream command output to stdout (auto-enabled with --logtostdout if None)
    :param asynchronous: indicate that command is being run asynchronously
    :param task_id: task ID for specified shell command (included in return value)
    :param with_hooks: trigger pre/post run_shell_cmd hooks (if defined)
    :param timeout: timeout in seconds for command execution
    :param qa_patterns: list of 2-tuples with patterns for questions + corresponding answers
    :param qa_wait_patterns: list of strings with patterns for non-questions
    :param qa_timeout: amount of seconds to wait until more output is produced when there is no matching question

    :return: Named tuple with:
    - output: command output, stdout+stderr combined if split_stderr is disabled, only stdout otherwise
    - exit_code: exit code of command (integer)
    - stderr: stderr output if split_stderr is enabled, None otherwise
    """
    def to_cmd_str(cmd):
        """
        Helper function to create string representation of specified command.
        """
        if isinstance(cmd, str):
            cmd_str = cmd.strip()
        elif isinstance(cmd, list):
            cmd_str = ' '.join(cmd)
        else:
            raise EasyBuildError(f"Unknown command type ('{type(cmd)}'): {cmd}")

        return cmd_str

    # make sure that qa_patterns is a list of 2-tuples (not a dict, or something else)
    if qa_patterns:
        if not isinstance(qa_patterns, list) or any(not isinstance(x, tuple) or len(x) != 2 for x in qa_patterns):
            raise EasyBuildError("qa_patterns passed to run_shell_cmd should be a list of 2-tuples!")

    if qa_wait_patterns is None:
        qa_wait_patterns = []

    if work_dir is None:
        work_dir = os.getcwd()

    cmd_str = to_cmd_str(cmd)

    thread_id = None
    if asynchronous:
        thread_id = get_thread_id()
        _log.info(f"Initiating running of shell command '{cmd_str}' via thread with ID {thread_id}")

    # auto-enable streaming of command output under --logtostdout/-l, unless it was disabled explicitely
    if stream_output is None and build_option('logtostdout'):
        _log.info(f"Auto-enabling streaming output of '{cmd_str}' command because logging to stdout is enabled")
        stream_output = True

    # temporary output file(s) for command output
    if output_file:
        toptmpdir = os.path.join(tempfile.gettempdir(), 'run-shell-cmd-output')
        os.makedirs(toptmpdir, exist_ok=True)
        cmd_name = fileprefix_from_cmd(os.path.basename(cmd_str.split(' ')[0]))
        tmpdir = tempfile.mkdtemp(dir=toptmpdir, prefix=f'{cmd_name}-')
        cmd_out_fp = os.path.join(tmpdir, 'out.txt')
        _log.info(f'run_cmd: Output of "{cmd_str}" will be logged to {cmd_out_fp}')
        if split_stderr:
            cmd_err_fp = os.path.join(tmpdir, 'err.txt')
            _log.info(f'run_cmd: Errors and warnings of "{cmd_str}" will be logged to {cmd_err_fp}')
        else:
            cmd_err_fp = None
    else:
        cmd_out_fp, cmd_err_fp = None, None

    interactive = bool(qa_patterns)
    interactive_msg = 'interactive ' if interactive else ''

    # early exit in 'dry run' mode, after printing the command that would be run (unless 'hidden' is enabled)
    if not in_dry_run and build_option('extended_dry_run'):
        if not hidden or verbose_dry_run:
            silent = build_option('silent')
            msg = f"  running {interactive_msg}shell command \"{cmd_str}\"\n"
            msg += f"  (in {work_dir})"
            dry_run_msg(msg, silent=silent)

        return RunShellCmdResult(cmd=cmd_str, exit_code=0, output='', stderr=None, work_dir=work_dir,
                                 out_file=cmd_out_fp, err_file=cmd_err_fp, thread_id=thread_id, task_id=task_id)

    start_time = datetime.now()
    if not hidden:
        _cmd_trace_msg(cmd_str, start_time, work_dir, stdin, cmd_out_fp, cmd_err_fp, thread_id, interactive=interactive)

    if stream_output:
        print_msg(f"(streaming) output for command '{cmd_str}':")

    # use bash as shell instead of the default /bin/sh used by subprocess.run
    # (which could be dash instead of bash, like on Ubuntu, see https://wiki.ubuntu.com/DashAsBinSh)
    # stick to None (default value) when not running command via a shell
    if use_bash:
        bash = shutil.which('bash')
        _log.info(f"Path to bash that will be used to run shell commands: {bash}")
        executable, shell = bash, True
    else:
        executable, shell = None, False

    if with_hooks:
        hooks = load_hooks(build_option('hooks'))
        kwargs = {
            'interactive': interactive,
            'work_dir': work_dir,
        }
        hook_res = run_hook(RUN_SHELL_CMD, hooks, pre_step_hook=True, args=[cmd], kwargs=kwargs)
        if hook_res:
            cmd, old_cmd = hook_res, cmd
            cmd_str = to_cmd_str(cmd)
            _log.info("Command to run was changed by pre-%s hook: '%s' (was: '%s')", RUN_SHELL_CMD, cmd, old_cmd)

    stderr = subprocess.PIPE if split_stderr else subprocess.STDOUT

    log_msg = f"Running {interactive_msg}shell command '{cmd_str}' in {work_dir}"
    if thread_id:
        log_msg += f" (via thread with ID {thread_id})"
    _log.info(log_msg)

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=stderr, stdin=subprocess.PIPE,
                            cwd=work_dir, env=env, shell=shell, executable=executable)

    # 'input' value fed to subprocess.run must be a byte sequence
    if stdin:
        stdin = stdin.encode()

    if stream_output or qa_patterns:

        if qa_patterns:
            # make stdout, stderr, stdin non-blocking files
            channels = [proc.stdout, proc.stdin]
            if split_stderr:
                channels += proc.stderr
            for channel in channels:
                fd = channel.fileno()
                flags = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

        if stdin:
            proc.stdin.write(stdin)

        exit_code = None
        stdout, stderr = b'', b''
        check_interval_secs = 0.1
        time_no_match = 0

        # collect output piece-wise, while checking for questions to answer (if qa_patterns is provided)
        start = time.time()
        while exit_code is None:
            if timeout and time.time() - start > timeout:
                error_msg = f"Timeout during `{cmd}` after {timeout} seconds!"
                _log.warning(error_msg)
                terminate_process(proc)
                raise EasyBuildError(error_msg)
            # use small read size (128 bytes) when streaming output, to make it stream more fluently
            # -1 means reading until EOF
            read_size = 128 if exit_code is None else -1

            # get output as long as output is available;
            # note: can't use proc.stdout.read without read_size argument,
            # since that will always wait until EOF
            more_stdout = True
            while more_stdout:
                try:
                    t = timeout - (time.time() - start) if timeout else None
                    more_stdout = read_pipe(proc.stdout, read_size, timeout=t) or b''
                except TimeoutError:
                    break
                _log.debug(f"Obtained more stdout: {more_stdout}")
                stdout += more_stdout

            # note: we assume that there won't be any questions in stderr output
            if split_stderr:
                more_stderr = True
                while more_stderr:
                    try:
                        t = timeout - (time.time() - start) if timeout else None
                        more_stderr = read_pipe(proc.stderr, read_size, timeout=t) or b''
                    except TimeoutError:
                        break
                    stderr += more_stderr

            if qa_patterns:
                if _answer_question(stdout, proc, qa_patterns, qa_wait_patterns):
                    time_no_match = 0
                else:
                    # this will only run if the for loop above was *not* stopped by the break statement
                    time_no_match += check_interval_secs
                    if time_no_match > qa_timeout:
                        error_msg = "No matching questions found for current command output, "
                        error_msg += f"giving up after {qa_timeout} seconds!"
                        raise EasyBuildError(error_msg)
                    else:
                        _log.debug(f"{time_no_match:0.1f} seconds without match in output of interactive shell command")

            time.sleep(check_interval_secs)

            exit_code = proc.poll()

        # collect last bit of output once processed has exited
        stdout += proc.stdout.read()
        if split_stderr:
            stderr += proc.stderr.read()
    else:
        try:
            (stdout, stderr) = proc.communicate(input=stdin, timeout=timeout)
        except subprocess.TimeoutExpired as err:
            error_msg = f"Timeout during `{cmd}` after {timeout} seconds"
            _log.warning(error_msg)
            terminate_process(proc)
            raise EasyBuildError(error_msg)

    # return output as a regular string rather than a byte sequence (and non-UTF-8 characters get stripped out)
    # getpreferredencoding normally gives 'utf-8' but can be ASCII (ANSI_X3.4-1968)
    # for Python 3.6 and older with LC_ALL=C
    encoding = locale.getpreferredencoding(False)
    output = stdout.decode(encoding, 'ignore')
    stderr = stderr.decode(encoding, 'ignore') if split_stderr else None

    # store command output to temporary file(s)
    if output_file:
        try:
            with open(cmd_out_fp, 'w') as fp:
                fp.write(output)
            if split_stderr:
                with open(cmd_err_fp, 'w') as fp:
                    fp.write(stderr)
        except IOError as err:
            raise EasyBuildError(f"Failed to dump command output to temporary file: {err}")

    res = RunShellCmdResult(cmd=cmd_str, exit_code=proc.returncode, output=output, stderr=stderr, work_dir=work_dir,
                            out_file=cmd_out_fp, err_file=cmd_err_fp, thread_id=thread_id, task_id=task_id)

    # always log command output
    cmd_name = cmd_str.split(' ')[0]
    if split_stderr:
        _log.info(f"Output of '{cmd_name} ...' shell command (stdout only):\n{res.output}")
        _log.info(f"Warnings and errors of '{cmd_name} ...' shell command (stderr only):\n{res.stderr}")
    else:
        _log.info(f"Output of '{cmd_name} ...' shell command (stdout + stderr):\n{res.output}")

    if res.exit_code == 0:
        _log.info(f"Shell command completed successfully (see output above): {cmd_str}")
    else:
        _log.warning(f"Shell command FAILED (exit code {res.exit_code}, see output above): {cmd_str}")
        if fail_on_error:
            raise_run_shell_cmd_error(res)

    if with_hooks:
        run_hook_kwargs = {
            'exit_code': res.exit_code,
            'interactive': interactive,
            'output': res.output,
            'stderr': res.stderr,
            'work_dir': res.work_dir,
        }
        run_hook(RUN_SHELL_CMD, hooks, post_step_hook=True, args=[cmd], kwargs=run_hook_kwargs)

    if not hidden:
        time_since_start = time_str_since(start_time)
        trace_msg(f"command completed: exit {res.exit_code}, ran in {time_since_start}")

    return res


def _cmd_trace_msg(cmd, start_time, work_dir, stdin, cmd_out_fp, cmd_err_fp, thread_id, interactive=False):
    """
    Helper function to construct and print trace message for command being run

    :param cmd: command being run
    :param start_time: datetime object indicating when command was started
    :param work_dir: path of working directory in which command is run
    :param stdin: stdin input value for command
    :param cmd_out_fp: path to output file for command
    :param cmd_err_fp: path to errors/warnings output file for command
    :param thread_id: thread ID (None when not running shell command asynchronously)
    :param interactive: boolean indicating whether it is an interactive command, or not
    """
    start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')

    interactive = 'interactive ' if interactive else ''
    if thread_id:
        run_cmd_msg = f"running {interactive}shell command (asynchronously, thread ID: {thread_id}):"
    else:
        run_cmd_msg = f"running {interactive}shell command:"

    lines = [
        run_cmd_msg,
        f"\t{cmd}",
        f"\t[started at: {start_time}]",
        f"\t[working dir: {work_dir}]",
    ]
    if stdin:
        lines.append(f"\t[input: {stdin}]")
    if cmd_out_fp:
        lines.append(f"\t[output saved to {cmd_out_fp}]")
    if cmd_err_fp:
        lines.append(f"\t[errors/warnings saved to {cmd_err_fp}]")

    trace_msg('\n'.join(lines))


def get_output_from_process(proc, read_size=None, asynchronous=False):
    """
    Get output from running process (that was opened with subprocess.Popen).

    :param proc: process to get output from
    :param read_size: number of bytes of output to read (if None: read all output)
    :param asynchronous: get output asynchronously
    """

    if asynchronous:
        # e=False is set to avoid raising an exception when command has completed;
        # that's needed to ensure we get all output,
        # see https://github.com/easybuilders/easybuild-framework/issues/3593
        output = asyncprocess.recv_some(proc, e=False)
    elif read_size:
        output = proc.stdout.read(read_size)
    else:
        output = proc.stdout.read()

    # need to be careful w.r.t. encoding since we want to obtain a string value,
    # and the output may include non UTF-8 characters
    # * in Python 2, .decode() returns a value of type 'unicode',
    #   but we really want a regular 'str' value (which is also why we use 'ignore' for encoding errors)
    # * in Python 3, .decode() returns a 'str' value when called on the 'bytes' value obtained from .read()
    output = str(output.decode('ascii', 'ignore'))

    return output


@run_cmd_cache
def run_cmd(cmd, log_ok=True, log_all=False, simple=False, inp=None, regexp=True, log_output=False, path=None,
            force_in_dry_run=False, verbose=True, shell=None, trace=True, stream_output=None, asynchronous=False,
            with_hooks=True):
    """
    Run specified command (in a subshell)
    :param cmd: command to run
    :param log_ok: only run output/exit code for failing commands (exit code non-zero)
    :param log_all: always log command output and exit code
    :param simple: if True, just return True/False to indicate success, else return a tuple: (output, exit_code)
    :param inp: the input given to the command via stdin
    :param regexp: regex used to check the output for errors;  if True it will use the default (see parse_log_for_error)
    :param log_output: indicate whether all output of command should be logged to a separate temporary logfile
    :param path: path to execute the command in; current working directory is used if unspecified
    :param force_in_dry_run: force running the command during dry run
    :param verbose: include message on running the command in dry run output
    :param shell: allow commands to not run in a shell (especially useful for cmd lists), defaults to True
    :param trace: print command being executed as part of trace output
    :param stream_output: enable streaming command output to stdout
    :param asynchronous: run command asynchronously (returns subprocess.Popen instance if set to True)
    :param with_hooks: trigger pre/post run_shell_cmd hooks (if defined)
    """
    cwd = os.getcwd()

    if isinstance(cmd, str):
        cmd_msg = cmd.strip()
    elif isinstance(cmd, list):
        cmd_msg = ' '.join(cmd)
    else:
        raise EasyBuildError("Unknown command type ('%s'): %s", type(cmd), cmd)

    if shell is None:
        shell = True
        if isinstance(cmd, list):
            raise EasyBuildError("When passing cmd as a list then `shell` must be set explictely! "
                                 "Note that all elements of the list but the first are treated as arguments "
                                 "to the shell and NOT to the command to be executed!")

    if log_output or (trace and build_option('trace')):
        # collect output of running command in temporary log file, if desired
        fd, cmd_log_fn = tempfile.mkstemp(suffix='.log', prefix='easybuild-run_cmd-')
        os.close(fd)
        try:
            cmd_log = open(cmd_log_fn, 'w')
        except IOError as err:
            raise EasyBuildError("Failed to open temporary log file for output of command: %s", err)
        _log.debug('run_cmd: Output of "%s" will be logged to %s' % (cmd, cmd_log_fn))
    else:
        cmd_log_fn, cmd_log = None, None

    # auto-enable streaming of command output under --logtostdout/-l, unless it was disabled explicitely
    if stream_output is None and build_option('logtostdout'):
        _log.info("Auto-enabling streaming output of '%s' command because logging to stdout is enabled", cmd_msg)
        stream_output = True

    if stream_output:
        print_msg("(streaming) output for command '%s':" % cmd_msg)

    start_time = datetime.now()
    if trace:
        trace_txt = "running command:\n"
        trace_txt += "\t[started at: %s]\n" % start_time.strftime('%Y-%m-%d %H:%M:%S')
        trace_txt += "\t[working dir: %s]\n" % (path or os.getcwd())
        if inp:
            trace_txt += "\t[input: %s]\n" % inp
        trace_txt += "\t[output logged in %s]\n" % cmd_log_fn
        trace_msg(trace_txt + '\t' + cmd_msg)

    # early exit in 'dry run' mode, after printing the command that would be run (unless running the command is forced)
    if not force_in_dry_run and build_option('extended_dry_run'):
        if path is None:
            path = cwd
        if verbose:
            dry_run_msg("  running command \"%s\"" % cmd_msg, silent=build_option('silent'))
            dry_run_msg("  (in %s)" % path, silent=build_option('silent'))

        # make sure we get the type of the return value right
        if simple:
            return True
        else:
            # output, exit code
            return ('', 0)

    try:
        if path:
            os.chdir(path)

        _log.debug("run_cmd: running cmd %s (in %s)" % (cmd, os.getcwd()))
    except OSError as err:
        _log.warning("Failed to change to %s: %s" % (path, err))
        _log.info("running cmd %s in non-existing directory, might fail!", cmd)

    if cmd_log:
        cmd_log.write("# output for command: %s\n\n" % cmd_msg)

    exec_cmd = "/bin/bash"

    if not shell:
        if isinstance(cmd, list):
            exec_cmd = None
            cmd.insert(0, '/usr/bin/env')
        elif isinstance(cmd, str):
            cmd = '/usr/bin/env %s' % cmd
        else:
            raise EasyBuildError("Don't know how to prefix with /usr/bin/env for commands of type %s", type(cmd))

    if with_hooks:
        hooks = load_hooks(build_option('hooks'))
        hook_res = run_hook(RUN_SHELL_CMD, hooks, pre_step_hook=True, args=[cmd], kwargs={'work_dir': os.getcwd()})
        if isinstance(hook_res, str):
            cmd, old_cmd = hook_res, cmd
            _log.info("Command to run was changed by pre-%s hook: '%s' (was: '%s')", RUN_SHELL_CMD, cmd, old_cmd)

    _log.info('running cmd: %s ' % cmd)
    try:
        proc = subprocess.Popen(cmd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.PIPE, close_fds=True, executable=exec_cmd)
    except OSError as err:
        raise EasyBuildError("run_cmd init cmd %s failed:%s", cmd, err)

    if inp:
        proc.stdin.write(inp.encode())
    proc.stdin.close()

    if asynchronous:
        return (proc, cmd, cwd, start_time, cmd_log)
    else:
        return complete_cmd(proc, cmd, cwd, start_time, cmd_log, log_ok=log_ok, log_all=log_all, simple=simple,
                            regexp=regexp, stream_output=stream_output, trace=trace, with_hook=with_hooks)


def check_async_cmd(proc, cmd, owd, start_time, cmd_log, fail_on_error=True, output_read_size=1024, output=''):
    """
    Check status of command that was started asynchronously.

    :param proc: subprocess.Popen instance representing asynchronous command
    :param cmd: command being run
    :param owd: original working directory
    :param start_time: start time of command (datetime instance)
    :param cmd_log: log file to print command output to
    :param fail_on_error: raise EasyBuildError when command exited with an error
    :param output_read_size: number of bytes to read from output
    :param output: already collected output for this command

    :result: dict value with result of the check (boolean 'done', 'exit_code', 'output')
    """
    # use small read size, to avoid waiting for a long time until sufficient output is produced
    if output_read_size:
        if not isinstance(output_read_size, int) or output_read_size < 0:
            raise EasyBuildError("Number of output bytes to read should be a positive integer value (or zero)")
        add_out = get_output_from_process(proc, read_size=output_read_size)
        _log.debug("Additional output from asynchronous command '%s': %s" % (cmd, add_out))
        output += add_out

    exit_code = proc.poll()
    if exit_code is None:
        _log.debug("Asynchronous command '%s' still running..." % cmd)
        done = False
    else:
        _log.debug("Asynchronous command '%s' completed!", cmd)
        output, _ = complete_cmd(proc, cmd, owd, start_time, cmd_log, output=output,
                                 simple=False, trace=False, log_ok=fail_on_error)
        done = True

    res = {
        'done': done,
        'exit_code': exit_code,
        'output': output,
    }
    return res


def complete_cmd(proc, cmd, owd, start_time, cmd_log, log_ok=True, log_all=False, simple=False,
                 regexp=True, stream_output=None, trace=True, output='', with_hook=True):
    """
    Complete running of command represented by passed subprocess.Popen instance.

    :param proc: subprocess.Popen instance representing running command
    :param cmd: command being run
    :param owd: original working directory
    :param start_time: start time of command (datetime instance)
    :param cmd_log: log file to print command output to
    :param log_ok: only run output/exit code for failing commands (exit code non-zero)
    :param log_all: always log command output and exit code
    :param simple: if True, just return True/False to indicate success, else return a tuple: (output, exit_code)
    :param regexp: regex used to check the output for errors;  if True it will use the default (see parse_log_for_error)
    :param stream_output: enable streaming command output to stdout
    :param trace: print command being executed as part of trace output
    :param with_hook: trigger post run_shell_cmd hooks (if defined)
    """
    # use small read size when streaming output, to make it stream more fluently
    # read size should not be too small though, to avoid too much overhead
    if stream_output:
        read_size = 128
    else:
        read_size = 1024 * 8

    stdouterr = output

    try:
        ec = proc.poll()
        while ec is None:
            # need to read from time to time.
            # - otherwise the stdout/stderr buffer gets filled and it all stops working
            output = get_output_from_process(proc, read_size=read_size)
            if cmd_log:
                cmd_log.write(output)
            if stream_output:
                sys.stdout.write(output)
            stdouterr += output
            ec = proc.poll()

        # read remaining data (all of it)
        output = get_output_from_process(proc)
    finally:
        proc.stdout.close()

    if cmd_log:
        cmd_log.write(output)
        cmd_log.close()
    if stream_output:
        sys.stdout.write(output)
    stdouterr += output

    if with_hook:
        hooks = load_hooks(build_option('hooks'))
        run_hook_kwargs = {
            'exit_code': ec,
            'output': stdouterr,
            'work_dir': os.getcwd(),
        }
        run_hook(RUN_SHELL_CMD, hooks, post_step_hook=True, args=[cmd], kwargs=run_hook_kwargs)

    if trace:
        trace_msg("command completed: exit %s, ran in %s" % (ec, time_str_since(start_time)))

    try:
        os.chdir(owd)
    except OSError as err:
        raise EasyBuildError("Failed to return to %s after executing command: %s", owd, err)

    return parse_cmd_output(cmd, stdouterr, ec, simple, log_all, log_ok, regexp)


def run_cmd_qa(cmd, qa, no_qa=None, log_ok=True, log_all=False, simple=False, regexp=True, std_qa=None, path=None,
               maxhits=50, trace=True):
    """
    Run specified interactive command (in a subshell)
    :param cmd: command to run
    :param qa: dictionary which maps question to answers
    :param no_qa: list of patters that are not questions
    :param log_ok: only run output/exit code for failing commands (exit code non-zero)
    :param log_all: always log command output and exit code
    :param simple: if True, just return True/False to indicate success, else return a tuple: (output, exit_code)
    :param regexp: regex used to check the output for errors; if True it will use the default (see parse_log_for_error)
    :param std_qa: dictionary which maps question regex patterns to answers
    :param path: path to execute the command is; current working directory is used if unspecified
    :param maxhits: maximum number of cycles (seconds) without being able to find a known question
    :param trace: print command being executed as part of trace output
    """
    cwd = os.getcwd()

    if not isinstance(cmd, str) and len(cmd) > 1:
        # We use shell=True and hence we should really pass the command as a string
        # When using a list then every element past the first is passed to the shell itself, not the command!
        raise EasyBuildError("The command passed must be a string!")

    if log_all or (trace and build_option('trace')):
        # collect output of running command in temporary log file, if desired
        fd, cmd_log_fn = tempfile.mkstemp(suffix='.log', prefix='easybuild-run_cmd_qa-')
        os.close(fd)
        try:
            cmd_log = open(cmd_log_fn, 'w')
        except IOError as err:
            raise EasyBuildError("Failed to open temporary log file for output of interactive command: %s", err)
        _log.debug('run_cmd_qa: Output of "%s" will be logged to %s' % (cmd, cmd_log_fn))
    else:
        cmd_log_fn, cmd_log = None, None

    start_time = datetime.now()
    if trace:
        trace_txt = "running interactive command:\n"
        trace_txt += "\t[started at: %s]\n" % start_time.strftime('%Y-%m-%d %H:%M:%S')
        trace_txt += "\t[working dir: %s]\n" % (path or os.getcwd())
        trace_txt += "\t[output logged in %s]\n" % cmd_log_fn
        trace_msg(trace_txt + '\t' + cmd.strip())

    # early exit in 'dry run' mode, after printing the command that would be run
    if build_option('extended_dry_run'):
        if path is None:
            path = cwd
        dry_run_msg("  running interactive command \"%s\"" % cmd, silent=build_option('silent'))
        dry_run_msg("  (in %s)" % path, silent=build_option('silent'))
        if cmd_log:
            cmd_log.close()
        if simple:
            return True
        else:
            # output, exit code
            return ('', 0)

    try:
        if path:
            os.chdir(path)

        _log.debug("run_cmd_qa: running cmd %s (in %s)" % (cmd, os.getcwd()))
    except OSError as err:
        _log.warning("Failed to change to %s: %s" % (path, err))
        _log.info("running cmd %s in non-existing directory, might fail!" % cmd)

    # Part 1: process the QandA dictionary
    # given initial set of Q and A (in dict), return dict of reg. exp. and A
    #
    # make regular expression that matches the string with
    # - replace whitespace
    # - replace newline

    def escape_special(string):
        return re.sub(r"([\+\?\(\)\[\]\*\.\\\$])", r"\\\1", string)

    split = r'[\s\n]+'
    regSplit = re.compile(r"" + split)

    def process_QA(q, a_s):
        splitq = [escape_special(x) for x in regSplit.split(q)]
        regQtxt = split.join(splitq) + split.rstrip('+') + "*$"
        # add optional split at the end
        for i in [idx for idx, a in enumerate(a_s) if not a.endswith('\n')]:
            a_s[i] += '\n'
        regQ = re.compile(r"" + regQtxt)
        if regQ.search(q):
            return (a_s, regQ)
        else:
            raise EasyBuildError("runqanda: Question %s converted in %s does not match itself", q, regQtxt)

    def check_answers_list(answers):
        """Make sure we have a list of answers (as strings)."""
        if isinstance(answers, str):
            answers = [answers]
        elif not isinstance(answers, list):
            if cmd_log:
                cmd_log.close()
            raise EasyBuildError("Invalid type for answer on %s, no string or list: %s (%s)",
                                 question, type(answers), answers)
        # list is manipulated when answering matching question, so return a copy
        return answers[:]

    new_qa = {}
    _log.debug("new_qa: ")
    for question, answers in qa.items():
        answers = check_answers_list(answers)
        (answers, regQ) = process_QA(question, answers)
        new_qa[regQ] = answers
        _log.debug("new_qa[%s]: %s" % (regQ.pattern, new_qa[regQ]))

    new_std_qa = {}
    if std_qa:
        for question, answers in std_qa.items():
            regQ = re.compile(r"" + question + r"[\s\n]*$")
            answers = check_answers_list(answers)
            for i in [idx for idx, a in enumerate(answers) if not a.endswith('\n')]:
                answers[i] += '\n'
            new_std_qa[regQ] = answers
            _log.debug("new_std_qa[%s]: %s" % (regQ.pattern, new_std_qa[regQ]))

    new_no_qa = []
    if no_qa:
        # simple statements, can contain wildcards
        new_no_qa = [re.compile(r"" + x + r"[\s\n]*$") for x in no_qa]

    _log.debug("New noQandA list is: %s" % [x.pattern for x in new_no_qa])

    # Part 2: Run the command and answer questions
    # - this needs asynchronous stdout

    hooks = load_hooks(build_option('hooks'))
    run_hook_kwargs = {
        'interactive': True,
        'work_dir': os.getcwd(),
    }
    hook_res = run_hook(RUN_SHELL_CMD, hooks, pre_step_hook=True, args=[cmd], kwargs=run_hook_kwargs)
    if isinstance(hook_res, str):
        cmd, old_cmd = hook_res, cmd
        _log.info("Interactive command to run was changed by pre-%s hook: '%s' (was: '%s')",
                  RUN_SHELL_CMD, cmd, old_cmd)

    # # Log command output
    if cmd_log:
        cmd_log.write("# output for interactive command: %s\n\n" % cmd)

    # Make sure we close the proc handles and the cmd_log file
    @contextlib.contextmanager
    def get_proc():
        try:
            proc = asyncprocess.Popen(cmd, shell=True, stdout=asyncprocess.PIPE, stderr=asyncprocess.STDOUT,
                                      stdin=asyncprocess.PIPE, close_fds=True, executable='/bin/bash')
        except OSError as err:
            if cmd_log:
                cmd_log.close()
            raise EasyBuildError("run_cmd_qa init cmd %s failed:%s", cmd, err)
        try:
            yield proc
        finally:
            if proc.stdout:
                proc.stdout.close()
            if proc.stdin:
                proc.stdin.close()
            if cmd_log:
                cmd_log.close()

    with get_proc() as proc:
        ec = proc.poll()
        stdout_err = ''
        old_len_out = -1
        hit_count = 0

        while ec is None:
            # need to read from time to time.
            # - otherwise the stdout/stderr buffer gets filled and it all stops working
            try:
                out = get_output_from_process(proc, asynchronous=True)

                if cmd_log:
                    cmd_log.write(out)
                stdout_err += out
            # recv_some used by get_output_from_process for getting asynchronous output may throw exception
            except (IOError, Exception) as err:
                _log.debug("run_cmd_qa cmd %s: read failed: %s", cmd, err)
                out = None

            hit = False
            for question, answers in new_qa.items():
                res = question.search(stdout_err)
                if out and res:
                    fa = answers[0] % res.groupdict()
                    # cycle through list of answers
                    last_answer = answers.pop(0)
                    answers.append(last_answer)
                    _log.debug("List of answers for question %s after cycling: %s", question.pattern, answers)

                    _log.debug("run_cmd_qa answer %s question %s out %s", fa, question.pattern, stdout_err[-50:])
                    asyncprocess.send_all(proc, fa)
                    hit = True
                    break
            if not hit:
                for question, answers in new_std_qa.items():
                    res = question.search(stdout_err)
                    if out and res:
                        fa = answers[0] % res.groupdict()
                        # cycle through list of answers
                        last_answer = answers.pop(0)
                        answers.append(last_answer)
                        _log.debug("List of answers for question %s after cycling: %s", question.pattern, answers)

                        _log.debug("run_cmd_qa answer %s std question %s out %s",
                                   fa, question.pattern, stdout_err[-50:])
                        asyncprocess.send_all(proc, fa)
                        hit = True
                        break
                if not hit:
                    if len(stdout_err) > old_len_out:
                        old_len_out = len(stdout_err)
                    else:
                        noqa = False
                        for r in new_no_qa:
                            if r.search(stdout_err):
                                _log.debug("runqanda: noQandA found for out %s", stdout_err[-50:])
                                noqa = True
                        if not noqa:
                            hit_count += 1
                else:
                    hit_count = 0
            else:
                hit_count = 0

            if hit_count > maxhits:
                # explicitly kill the child process before exiting
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                    os.kill(proc.pid, signal.SIGKILL)
                except OSError as err:
                    _log.debug("run_cmd_qa exception caught when killing child process: %s", err)
                _log.debug("run_cmd_qa: full stdouterr: %s", stdout_err)
                raise EasyBuildError("run_cmd_qa: cmd %s : Max nohits %s reached: end of output %s",
                                     cmd, maxhits, stdout_err[-500:])

            # the sleep below is required to avoid exiting on unknown 'questions' too early (see above)
            time.sleep(1)
            ec = proc.poll()

        # Process stopped. Read all remaining data
        try:
            if proc.stdout:
                out = get_output_from_process(proc)
                stdout_err += out
                if cmd_log:
                    cmd_log.write(out)
        except IOError as err:
            _log.debug("runqanda cmd %s: remaining data read failed: %s", cmd, err)

    run_hook_kwargs.update({
        'interactive': True,
        'exit_code': ec,
        'output': stdout_err,
    })
    run_hook(RUN_SHELL_CMD, hooks, post_step_hook=True, args=[cmd], kwargs=run_hook_kwargs)

    if trace:
        trace_msg("interactive command completed: exit %s, ran in %s" % (ec, time_str_since(start_time)))

    try:
        os.chdir(cwd)
    except OSError as err:
        raise EasyBuildError("Failed to return to %s after executing command: %s", cwd, err)

    return parse_cmd_output(cmd, stdout_err, ec, simple, log_all, log_ok, regexp)


def parse_cmd_output(cmd, stdouterr, ec, simple, log_all, log_ok, regexp):
    """
    Parse command output and construct return value.
    :param cmd: executed command
    :param stdouterr: combined stdout/stderr of executed command
    :param ec: exit code of executed command
    :param simple: if True, just return True/False to indicate success, else return a tuple: (output, exit_code)
    :param log_all: always log command output and exit code
    :param log_ok: only run output/exit code for failing commands (exit code non-zero)
    :param regexp: regex used to check the output for errors; if True it will use the default (see parse_log_for_error)
    """
    if strictness == IGNORE:
        check_ec = False
        fail_on_error_match = False
    elif strictness == WARN:
        check_ec = True
        fail_on_error_match = False
    elif strictness == ERROR:
        check_ec = True
        fail_on_error_match = True
    else:
        raise EasyBuildError("invalid strictness setting: %s", strictness)

    # allow for overriding the regexp setting
    if not regexp:
        fail_on_error_match = False

    if ec and (log_all or log_ok):
        # We don't want to error if the user doesn't care
        if check_ec:
            raise EasyBuildError('cmd "%s" exited with exit code %s and output:\n%s', cmd, ec, stdouterr)
        else:
            _log.warning('cmd "%s" exited with exit code %s and output:\n%s' % (cmd, ec, stdouterr))
    elif not ec:
        if log_all:
            _log.info('cmd "%s" exited with exit code %s and output:\n%s' % (cmd, ec, stdouterr))
        else:
            _log.debug('cmd "%s" exited with exit code %s and output:\n%s' % (cmd, ec, stdouterr))

    # parse the stdout/stderr for errors when strictness dictates this or when regexp is passed in
    if fail_on_error_match or regexp:
        res = parse_log_for_error(stdouterr, regexp, stdout=False)
        if res:
            errors = "\n\t" + "\n\t".join([r[0] for r in res])
            error_str = "error" if len(res) == 1 else "errors"
            if fail_on_error_match:
                raise EasyBuildError("Found %s %s in output of %s:%s", len(res), error_str, cmd, errors)
            else:
                _log.warning("Found %s potential %s (some may be harmless) in output of %s:%s",
                             len(res), error_str, cmd, errors)

    if simple:
        if ec:
            # If the user does not care -> will return true
            return not check_ec
        else:
            return True
    else:
        # Because we are not running in simple mode, we return the output and ec to the user
        return (stdouterr, ec)


def parse_log_for_error(txt, regExp=None, stdout=True, msg=None):
    """
    txt is multiline string.
    - in memory
    regExp is a one-line regular expression
    - default
    """
    global errors_found_in_log

    if regExp and isinstance(regExp, bool):
        regExp = r"(?<![(,-]|\w)(?:error|segmentation fault|failed)(?![(,-]|\.?\w)"
        _log.debug('Using default regular expression: %s' % regExp)
    elif isinstance(regExp, str):
        pass
    else:
        raise EasyBuildError("parse_log_for_error no valid regExp used: %s", regExp)

    reg = re.compile(regExp, re.I)

    res = []
    for line in txt.split('\n'):
        r = reg.search(line)
        if r:
            res.append([line, r.groups()])
            errors_found_in_log += 1

    if stdout and res:
        if msg:
            _log.info("parse_log_for_error msg: %s" % msg)
        _log.info("parse_log_for_error (some may be harmless) regExp %s found:\n%s" %
                  (regExp, '\n'.join([x[0] for x in res])))

    return res


def extract_errors_from_log(log_txt, reg_exps):
    """
    Check provided string (command output) for messages matching specified regular expressions,
    and return 2-tuple with list of warnings and errors.
    :param log_txt: String containing the log, will be split into individual lines
    :param reg_exps: List of: regular expressions (as strings) to error on,
                    or tuple of regular expression and action (any of [IGNORE, WARN, ERROR])
    :return: (warnings, errors) as lists of lines containing a match
    """
    actions = (IGNORE, WARN, ERROR)

    # promote single string value to list, since code below expects a list
    if isinstance(reg_exps, str):
        reg_exps = [reg_exps]

    re_tuples = []
    for cur in reg_exps:
        try:
            if isinstance(cur, str):
                # use ERROR as default action if only regexp pattern is specified
                reg_exp, action = cur, ERROR
            elif isinstance(cur, tuple) and len(cur) == 2:
                reg_exp, action = cur
            else:
                raise TypeError("Incorrect type of value, expected string or 2-tuple")

            if not isinstance(reg_exp, str):
                raise TypeError("Regular expressions must be passed as string, got %s" % type(reg_exp))
            if action not in actions:
                raise TypeError("action must be one of %s, got %s" % (actions, action))

            re_tuples.append((re.compile(reg_exp), action))
        except Exception as err:
            raise EasyBuildError("Invalid input: No regexp or tuple of regexp and action '%s': %s", str(cur), err)

    warnings = []
    errors = []
    for line in log_txt.split('\n'):
        for reg_exp, action in re_tuples:
            if reg_exp.search(line):
                if action == ERROR:
                    errors.append(line)
                elif action == WARN:
                    warnings.append(line)
                break
    return nub(warnings), nub(errors)


def check_log_for_errors(log_txt, reg_exps):
    """
    Check log_txt for messages matching regExps in order and do appropriate action
    :param log_txt: String containing the log, will be split into individual lines
    :param reg_exps: List of: regular expressions (as strings) to error on,
                    or tuple of regular expression and action (any of [IGNORE, WARN, ERROR])
    """
    global errors_found_in_log
    warnings, errors = extract_errors_from_log(log_txt, reg_exps)

    errors_found_in_log += len(warnings) + len(errors)
    if warnings:
        _log.warning("Found %s potential error(s) in command output:\n\t%s",
                     len(warnings), "\n\t".join(warnings))
    if errors:
        raise EasyBuildError("Found %s error(s) in command output:\n\t%s",
                             len(errors), "\n\t".join(errors))


def subprocess_popen_text(cmd, **kwargs):
    """Call subprocess.Popen in text mode with specified named arguments."""
    # open stdout/stderr in text mode in Popen when using Python 3
    kwargs.setdefault('stderr', subprocess.PIPE)
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True, **kwargs)


def subprocess_terminate(proc, timeout):
    """Terminate the subprocess if it hasn't finished after the given timeout"""
    try:
        proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        for pipe in (proc.stdout, proc.stderr, proc.stdin):
            if pipe:
                pipe.close()
        proc.terminate()
