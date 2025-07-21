from ..click_wrapper import click

CONFIG_ENV_VAR_PREFIX = 'EASYBUILD'

def register_hidden_param(ctx: click.Context, param: click.Parameter, value):
    """Register a hidden parameter in the context."""
    ctx.ensure_object(dict)
    ctx.obj.setdefault('hidden_params', {})
    ctx.obj.hidden_params[param.name] = value

def eb_option(
        long: str, *,
        callback=register_hidden_param,
        expose_value=False,
        short: str = None,
        default = None,
        show_default: bool = True,
        **kwargs
    ):
    """Decorator to create an EasyBuild CLI option."""
    def decorator(func):
        kwargs['callback'] = callback
        kwargs['expose_value'] = expose_value
        kwargs['default'] = default
        kwargs['show_default'] = show_default

        env_var_name = f"{CONFIG_ENV_VAR_PREFIX}_{long.replace('-', '_').upper()}"
        kwargs['envvar'] = env_var_name

        decls = []
        if isinstance(default, bool):
            decls.append(f'--{long}/--disable-{long}')
        else:
            decls.append(f'--{long}')
        if short:
            decls.append(f'-{short}')
        return click.option(**kwargs)(func)
    return decorator
