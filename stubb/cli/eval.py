import typer


app = typer.Typer(
    name="eval",
    help="Run an evaluation.",
    no_args_is_help=True,
    rich_help_panel=False,
)

"""
1. Given a new prompt, how does it perform on existing gold data
2. What are the output diffs of new prompt vs old
3. How do changes to schema affect the output
"""
