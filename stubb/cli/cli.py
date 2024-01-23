import typer

from conformable.cli import eval

app = typer.Typer(
    name="conformable-cli",
    help="Generate and evaluate structured LLM outputs.",
    no_args_is_help=True,
    rich_help_panel=False,
)

app.add_typer(eval.app, name="eval")
