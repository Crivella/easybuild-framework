import os
from click.shell_completion import CompletionItem
from easybuild.tools.options import set_up_configuration
from easybuild.tools.robot import search_easyconfigs

from .click_wrapper import click


class EasyconfigParam(click.ParamType):
    """Custom Click parameter type for easyconfig parameters."""
    name = 'easyconfig'

    def shell_complete(self, ctx, param, incomplete):
        set_up_configuration(args=["--ignore-index"], silent=True, reconfigure=True)
        return [CompletionItem(ec) for ec in search_easyconfigs(fr'^{incomplete}.*\.eb$', filename_only=True)]

class DelimitedPathList(click.Path):
    """Custom Click parameter type for delimited lists."""
    def __init__(self, *args,delimiter=',', **kwargs):
        kwargs.setdefault('resolve_path', True)
        super().__init__(*args, **kwargs)
        self.delimiter = delimiter
        name = self.name
        self.name = f'[{name}[{self.delimiter}{name}]]'

    def convert(self, value, param, ctx):
        # logging.warning(f"{param=} convert called with `{value=}`, `{type(value)=}`")
        if isinstance(value, str):
            res = value.split(self.delimiter)
        elif isinstance(value, (list, tuple)):
            res = value
        else:
            raise click.BadParameter(f"Expected a comma-separated string, got {value}")
        if self.resolve_path:
            res = [os.path.abspath(v) for v in res]
        # logging.warning(f"{param=} convert returning `{res=}`")
        return res

    def shell_complete(self, ctx, param, incomplete):
        others, last = ([''] + incomplete.rsplit(self.delimiter, 1))[-2:]
        # logging.warning(f"Shell completion for delimited path list: others={others}, last={last}")
        dir_path, prefix = os.path.split(last)
        dir_path = dir_path or '.'
        # logging.warning(f"Shell completion for delimited path list: dir_path={dir_path}, prefix={prefix}")

        possibles = []
        for path in os.listdir(dir_path):
            if not path.startswith(prefix):
                continue
            full_path = os.path.join(dir_path, path)
            if os.path.isdir(full_path):
                if self.dir_okay:
                    possibles.append(full_path)
                    possibles.append(full_path + os.sep)
            elif os.path.isfile(full_path):
                if self.file_okay:
                    possibles.append(full_path)
        # possibles = super().shell_complete(ctx, param, last)
        # logging.warning(f"Shell completion for delimited path list: possibles={possibles}")

        start = f'{others}{self.delimiter}' if others else ''
        res = [CompletionItem(f"{start}{path}") for path in possibles]
        # logging.warning(f"Shell completion for delimited path list: res={possibles}")
        return res


class DelimitedString(click.ParamType):
    """Custom Click parameter type for delimited strings."""
    def __init__(self, *args, delimiter=',', **kwargs):
        super().__init__(*args, **kwargs)
        self.delimiter = delimiter
        self.name = f'[STR[{self.delimiter}STR]]'

    def convert(self, value, param, ctx):
        if isinstance(value, str):
            res = value.split(self.delimiter)
        elif isinstance(value, (list, tuple)):
            res = value
        else:
            raise click.BadParameter(f"Expected a string or a comma-separated string, got {value}")
        return res

    def shell_complete(self, ctx, param, incomplete):
        last = incomplete.rsplit(self.delimiter, 1)[-1]
        return super().shell_complete(ctx, param, last)
