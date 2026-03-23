from functools import wraps

from easybuild.tools.config import BuildOptions
from easybuild.base import fancylogger

from ..click_wrapper import click, OPT_GROUP

CONFIG_ENV_VAR_PREFIX = 'EASYBUILD'

build_options = BuildOptions()

_log = fancylogger.getLogger('options')
if fancylogger._env_to_boolean('DEBUG_EASYBUILD_OPTIONS', default=False):
    fancylogger.logToScreen(enable=True)
    # fancylogger.setLogLevel('DEBUG')
    _log.setLevel('DEBUG')

def notimpl_callback(ctx: click.Context, param: click.Parameter, value):
    """Callback for options that are not implemented yet."""
    if value:
        click.echo(f"Option {param.name} is not implemented yet.", err=True)
        ctx.exit(1)

def register_hidden_param(ctx: click.Context, param: click.Parameter, value):
    """Register a hidden parameter in the context."""
    ctx.ensure_object(dict)

    ctx.obj[param.name] = value
    build_options._FrozenDict__dict[param.name] = value

    _log.debug(f"Registered parameter: {param.name} with value: {value}")

def single_callback(func):
    """Decorator to register a single callback function."""
    return list_callback([func])

def list_callback(func_lst):
    """Decorator to register a callback function for lists."""
    def wrapped(ctx: click.Context, param: click.Parameter, value):
        for func in func_lst:
            value = func(ctx, param, value)
        register_hidden_param(ctx, param, value)
    return wrapped

class OptionsGroup:
    """Class to represent a group of options."""
    def __init__(self, name=None, desc=None):
        self.name = name
        self.desc = desc
        self.options = []
        self.decorators = []

    def __call__(self, func):
        """Apply all decorators to a function."""
        return self.apply(func)

    def eb_option(
            self,
            long: str, *,
            expose_value=False,
            short: str = None,
            # group: str = None,
            # build_option: str = None,
            name: str = None,
            show_default: bool = True,
            **kwargs
        ):
        """Decorator factory to create an EasyBuild CLI option."""
        long = long.lstrip('-')
        default = kwargs.get('default', None)
        if short:
            short = short.lstrip('-')
        callback = kwargs.pop('callback', 'default')
        if callback is None:
            # TODO: this is only for debugging, some options might actually just be used to set a build_option
            callback = notimpl_callback
        elif callback == 'default':
            callback = register_hidden_param
        elif isinstance(callback, (list, tuple)):
            callback = list_callback(callback)
        elif callable(callback):
            callback = single_callback(callback)
        else:
            raise ValueError(f"Invalid callback type: {type(callback)} for option {long}")
        kwargs['callback'] = callback
        kwargs['expose_value'] = expose_value
        kwargs['show_default'] = show_default

        is_flag = kwargs.get('is_flag', False)

        env_var_name = f"{CONFIG_ENV_VAR_PREFIX}_{long.replace('-', '_').upper()}"
        kwargs['envvar'] = env_var_name

        decls = []
        if is_flag:
            # decls.append(f'--{long}/--disable-{long}')
            default = kwargs.get('default', False)
            if default:
                decls.append(f'--{long}/--disable-{long}')
            else:
                decls.append(f'--{long}')
        else:
            decls.append(f'--{long}')
        if short:
            decls.append(f'-{short}')

        if name:
            decls.append(f'{name}')

        wrapper = click.option(*decls, **kwargs)
        def decorator(func):
            """Decorator to apply the option to a function."""
            command_name = func.__name__.replace('_', '-')
            if command_name != 'eb3':
                command_name = f'* {command_name}'
            func = wrapper(func)

            if self.name:
                cmd = OPT_GROUP.setdefault(command_name,  [])
                for grp in cmd:
                    if grp['name'] == self.name:
                        ptr = grp
                        break
                else:
                    # If the group is not found, create a new one
                    ptr = {'name': self.name}
                    cmd.append(ptr)
                opts = ptr.setdefault('options', [])
                opts.append(f'--{long}')

            @wraps(func)
            def wrapped(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Skip the traceback of the decorator to avoid polluting the traceback with the nested decorators
                    # for every option
                    tb = e.__traceback__.tb_next
                    while tb and tb.tb_frame.f_code.co_name == 'wrapped':
                        tb = tb.tb_next
                    raise e.with_traceback(tb)

            return wrapped

        self.options.append(long)
        self.decorators.append(decorator)

        return decorator

    def apply(self, func):
        """Apply all decorators to a function."""
        for dec in self.decorators:
            func = dec(func)
        return func
