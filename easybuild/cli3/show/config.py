from rich.console import Console
from rich.table import Table

from ..click_wrapper import click, get_have_rich_click
from . import show
from click.core import ParameterSource

ROW_COLOR1 = "#333333"
ROW_COLOR2 = "#000000"

@show.command()
@click.pass_context
def config(ctx: click.Context):
    """Run an Easyconfig Build."""
    source_map = {
        ParameterSource.DEFAULT: 'D',
        ParameterSource.ENVIRONMENT: 'E',
        ParameterSource.DEFAULT_MAP: 'F',
        ParameterSource.COMMANDLINE: 'C',
    }
    # color_map = {
    #     ParameterSource.DEFAULT: '#D3D3D3', # Pale gray
    #     ParameterSource.ENVIRONMENT: '#FF6347',  # Tomato
    #     ParameterSource.DEFAULT_MAP: '#4682B4',  # SteelBlue
    #     ParameterSource.COMMANDLINE: '#32CD32',  # LimeGreen
    # }

    params = {}

    ptr = ctx
    while ptr:
        for param, value in ptr.obj.items():
            source = ptr._parameter_source.get(param)
            if not source:
                continue
            if source == ParameterSource.DEFAULT and value is None:
                continue
            params[param] = (source, value)
            # table.add_row(param, source_map.get(source), str(value))
        ptr = ptr.parent

    click.echo("#")
    click.echo("# Current EasyBuild configuration:")
    click.echo("# (C: command line argument, D: default value, E: environment variable, F: configuration file)")
    click.echo("#")
    if get_have_rich_click():
        # table = Table(title="EasyBuild Configuration", row_styles=[f"on {ROW_COLOR1}", f"on {ROW_COLOR2}"])
        table = Table(title="EasyBuild Configuration", row_styles=[f"bold", ""])
        table.add_column("Parameter", style="cyan")
        table.add_column("Source", style="red")
        table.add_column("Value", style="green")

        for param in sorted(params.keys()):
            source, value = params[param]
            table.add_row(param, source_map.get(source), str(value))

        console = Console()
        console.print(table)
    else:
        for param in sorted(params.keys()):
            source, value = params[param]
            click.echo(f"{param:<30s} ({source_map.get(source)}) = {value}")
