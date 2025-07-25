from functools import wraps

from easybuild.tools.config import BuildOptions

from ..click_wrapper import click, OPT_GROUP

CONFIG_ENV_VAR_PREFIX = 'EASYBUILD'
import logging

build_options = BuildOptions()

def notimpl_callback(ctx: click.Context, param: click.Parameter, value):
    """Callback for options that are not implemented yet."""
    if value:
        click.echo(f"Option {param.name} is not implemented yet.", err=True)
        ctx.exit(1)

def register_hidden_param(ctx: click.Context, param: click.Parameter, value):
    """Register a hidden parameter in the context."""
    ctx.ensure_object(dict)
    param.value_from_envvar

    ctx.obj[param.name] = value
    build_options._FrozenDict__dict[param.name] = value

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


def eb_option(
        long: str, *,
        expose_value=False,
        short: str = None,
        group: str = None,
        show_default: bool = True,
        **kwargs
    ):
    """Decorator factory to create an EasyBuild CLI option."""
    long = long.lstrip('-')
    if short:
        short = short.lstrip('-')
    callback = kwargs.pop('callback', None)
    if callback is None:
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
        default = kwargs.pop('default', None)
        if default:
            decls.append(f'--{long}/--disable-{long}')
        else:
            decls.append(f'--{long}')
    else:
        decls.append(f'--{long}')
    if short:
        decls.append(f'-{short}')

    wrapper = click.option(*decls, **kwargs)
    def decorator(func):
        """Decorator to apply the option to a function."""
        command_name = func.__name__.replace('_', '-')
        if command_name != 'eb3':
            command_name = f'* {command_name}'
        func = wrapper(func)

        if group:
            cmd = OPT_GROUP.setdefault(command_name,  [])
            for grp in cmd:
                if grp['name'] == group:
                    ptr = grp
                    break
            else:
                # If the group is not found, create a new one
                ptr = {'name': group}
                cmd.append(ptr)
            opts = ptr.setdefault('options', [])
            opts.append(f'--{long}')

        @wraps(func)
        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapped

    return decorator
