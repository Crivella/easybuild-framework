from ...click_wrapper import click, get_have_rich_click

def avail_list(name: str, items: list):
    """Display a list of available items."""
    if get_have_rich_click():
        from rich.table import Table
        from rich.console import Console

        table = Table(title=f"Available {name}", row_styles=["", ""])
        table.add_column("Item", style="cyan")
        for item in sorted(items):
            table.add_row(item)
        console = Console()
        console.print(table)
    else:
        msg = '\n\t'.join([''] + sorted(items))
        click.echo(f"List of supported {name}:{msg}")
