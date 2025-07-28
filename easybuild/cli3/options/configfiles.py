import os
import configparser
import yaml
import json

from easybuild.tools.build_log import EasyBuildError

from .base import eb_option as _eb_option, notimpl_callback
from .. import types as ctyp

GROUP = "Configfiles Options"
_OPTIONS = []
def eb_option(*args, **kwargs):
    """Decorator to create an EasyBuild configuration option."""
    res = _eb_option(*args, group=GROUP, **kwargs)
    _OPTIONS.append(res)
    return res

def parse_config_file(file_path):
    """Parse a configuration file and return a dictionary of options."""
    config = configparser.ConfigParser()
    config.read(file_path)

    options = {}
    for section in config.sections():
        ptr = options.setdefault(section, {})
        for key, value in config.items(section):
            ptr[key] = value

    return options

def parse_yaml_file(file_path):
    """Parse a YAML configuration file and return a dictionary of options."""
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def parse_json_file(file_path):
    """Parse a JSON configuration file and return a dictionary of options."""
    with open(file_path, 'r') as file:
        return json.load(file)

def parse_config_file_by_extension(file_path):
    """Parse a configuration file based on its extension."""
    if file_path.endswith('.ini') or file_path.endswith('.cfg'):
        return parse_config_file(file_path)
    elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
        return parse_yaml_file(file_path)
    elif file_path.endswith('.json'):
        return parse_json_file(file_path)
    else:
        raise EasyBuildError(f"Unsupported configuration file format: {file_path}")

def get_config_files(cfg_paths: list[str] = None):
    """Get a list of configuration files to be used by EasyBuild."""
    if cfg_paths is None:
        cfg_paths = []
        cfg_home = os.getenv('XDG_CONFIG_HOME', os.path.join(os.path.expanduser('~'), '.config'))
        cfg_dirs = os.getenv('XDG_CONFIG_DIRS', '/etc/xdg').split(os.pathsep)

        to_check_dirs = []
        for dirpath in cfg_dirs:
            if os.path.exists(os.path.join(dirpath, 'easybuild.d')):
                to_check_dirs.append(os.path.join(dirpath, 'easybuild.d'))
        if os.path.exists(os.path.join(cfg_home, 'easybuild')):
            to_check_dirs.append(os.path.join(cfg_home, 'easybuild'))
        for root in to_check_dirs:
            for file in os.listdir(root):
                if file.endswith(('.ini', '.cfg', '.yaml', '.yml', '.json')):
                    cfg_paths.append(os.path.join(root, 'easybuild', file))

    return cfg_paths

def load_configurations(cfg_paths: list[str] = None):
    """Load configurations from the specified paths."""
    cfg_paths = get_config_files(cfg_paths)

    final_config = {}
    for path in cfg_paths:
        config = parse_config_file_by_extension(path)
        for section, options in config.items():
            # ptr = final_config.setdefault(section, {})
            # ptr.update(options)
            final_config.update(options)

    return final_config

def configfile_callback(ctx, param, value):
    """Callback for the --configfiles option."""
    cfg_dict = load_configurations(value)
    ctx.default_map = cfg_dict
    return value



EB_CONFIGFILES_OPTION = eb_option(
    '--configfiles',
    is_eager=True,
    type=ctyp.DelimitedPathList(delimiter=','),
    callback=configfile_callback,
    help='Load EasyBuild configuration files.',
)

EB_IGNORE_CONFIGFILES_OPTION = eb_option(
    '--ignoreconfigfiles',
    is_eager=True,
    type=ctyp.DelimitedPathList(delimiter=','),
    callback=notimpl_callback,
    help='Ignore EasyBuild configuration files.',
)

def EB_CONFIGFILES_OPTIONS(func):
    """Decorator to add EasyBuild configuration file options."""
    for opt in _OPTIONS:
        func = opt(func)

    return func
