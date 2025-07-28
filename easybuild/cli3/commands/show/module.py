from easybuild.tools.module_naming_scheme.utilities import avail_module_naming_schemes
from easybuild.tools.modules import avail_modules_tools
from easybuild.tools.config import mk_full_default_path
from easybuild.tools.repository.repository import avail_repositories as _avail_repositories

from . import show
from .utils import avail_list
from ...click_wrapper import click, get_have_rich_click


@show.command()
def module_naming_schemes():
    """Show all supported module naming schemes."""
    schemes = avail_module_naming_schemes()
    avail_list("module naming schemes", schemes)


@show.command()
def module_tools():
    """Show all supported modules tools."""
    avail_list("module tools", avail_modules_tools())


@show.command()
def avail_repositories():
    """Show list of known repository types."""
    repopath_defaults = [mk_full_default_path('repositorypath')]
    all_repos = _avail_repositories(check_useable=False)
    usable_repos = _avail_repositories(check_useable=True).keys()

    indent = ' ' * 2
    txt = ['All avaliable repository types']
    repos = sorted(all_repos.keys())
    if get_have_rich_click():
        from rich.table import Table
        from rich.console import Console

        table = Table(title="Available Repository Types")
        table.add_column("Repository Type", style="cyan")
        table.add_column("Description", style="magenta")
        table.add_column("Default Arguments", style="green")
        table.add_column("Usable", style="yellow")
        console = Console()
        for repo in repos:
            if repo in usable_repos:
                usable = 'Yes'
            else:
                usable = 'No - something is missing (e.g. a required Python module)'

            if repo in repopath_defaults:
                default_args = ', '.join(repopath_defaults[repo])
            else:
                default_args = 'None'

            table.add_row(repo, all_repos[repo].DESCRIPTION, default_args, usable)
        console.print(table)
    else:
        for repo in repos:
            if repo in usable_repos:
                missing = ''
            else:
                missing = ' (*not usable*, something is missing (e.g. a required Python module))'
            if repo in repopath_defaults:
                default = ' (default arguments: %s)' % ', '.join(repopath_defaults[repo])
            else:
                default = ' (no default arguments)'

            txt.append("%s* %s%s%s" % (indent, repo, default, missing))
            txt.append("%s%s" % (indent * 3, all_repos[repo].DESCRIPTION))

        click.echo("\n".join(txt))


__all__ = [
    'module_naming_schemes',
    'module_tools',
    'avail_repositories',
]
