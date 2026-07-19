import typer
from utils import display_banner, console
from commands.repo import repo_app
from commands.branch import branch_app
from commands.upload import file_app
from commands.system import system_app

app = typer.Typer(
    help="GHUP (GitHub Uploader) - CLI tool for Termux to upload and manage files on GitHub repositories.",
    no_args_is_help=True
)

# Register command sub-apps
app.add_typer(repo_app, name="repo")
app.add_typer(branch_app, name="branch")
app.add_typer(file_app, name="")  # Allows top-level commands like upload, download, ls, delete, etc.
app.add_typer(system_app, name="")  # Allows login, info, history, config, doctor, version, self-update

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context, show_banner: bool = typer.Option(True, "--banner/--no-banner", help="Show/Hide banner")):
    if show_banner and ctx.invoked_subcommand is not None:
        # Show banner for relevant subcommands
        display_banner()

if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        console.print(f"[error]Unexpected error: {e}[/error]")
        raise
