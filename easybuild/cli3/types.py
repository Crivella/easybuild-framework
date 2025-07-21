# import logging
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
