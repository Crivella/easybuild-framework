from ..click_wrapper import click

CONFIG_ENV_VAR_PREFIX = 'EASYBUILD'


import logging


def register_hidden_param(ctx: click.Context, param: click.Parameter, value):
    """Register a hidden parameter in the context."""
    ctx.ensure_object(dict)
    ctx.obj.setdefault('hidden_params', {})
    # ctx.obj.setdefault('sources', {})
    param.value_from_envvar
    # if value is None:
    #     value = CONFIGURATION.get(param.name, None)
    #     if value is not None:
    #         ctx.obj['sources'][param.name] = 'F'
    # elif value == param.value_from_envvar(ctx):
    #     ctx.obj['sources'][param.name] = 'E'

    ctx.obj['hidden_params'][param.name] = value
    # logging.warning(f"Registered hidden parameter: {param.name} with value: {value}  {param.value_from_envvar(ctx)}")

def single_callback(func, *args, **kwargs):
    """Decorator to register a single callback function."""
    return list_callback([func], *args, **kwargs)

def list_callback(func_lst, *args, **kwargs):
    """Decorator to register a callback function for lists."""
    def wrapped(*args, **kwargs):
        register_hidden_param(*args, **kwargs)
        for func in func_lst:
            func(*args, **kwargs)
    return wrapped


def eb_option(
        long: str, *,
        # callback=register_hidden_param,
        expose_value=False,
        short: str = None,
        # default = None,
        show_default: bool = True,
        **kwargs
    ):
    if long.startswith('--'):
        long = long[2:]
    """Decorator to create an EasyBuild CLI option."""
    # if 'default' in kwargs:
    #     raise ValueError("Use `default` parameter directly, not in kwargs.")
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
    # kwargs['default'] = None
    kwargs['show_default'] = show_default

    is_flag = kwargs.get('is_flag', False)

    env_var_name = f"{CONFIG_ENV_VAR_PREFIX}_{long.replace('-', '_').upper()}"
    kwargs['envvar'] = env_var_name

    decls = []
    if is_flag:
        decls.append(f'--{long}/--disable-{long}')
    else:
        decls.append(f'--{long}')
    if short:
        decls.append(f'-{short}')

    # logging.warning(f"Creating option: {decls} with envvar: {env_var_name} and default: {default}")

    return click.option(*decls, **kwargs)
