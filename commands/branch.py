import typer
from rich.table import Table
from utils import console
from auth import check_auth
from config import get_config, set_config
from github_api import get_branches

branch_app = typer.Typer(help="Manage repository branches")

@branch_app.command("list")
def branch_list():
    """List branches of the active repository"""
    token = check_auth()
    if not token:
        return

    active_repo = get_config("active_repo")
    if not active_repo:
        console.print("[error]No active repository set. Use 'ghup repo use <owner/repo>' first.[/error]")
        return

    owner, repo = active_repo.split("/")
    branches = get_branches(token, owner, repo)
    if not branches:
        console.print("[warning]No branches found or failed to fetch.[/warning]")
        return

    current_branch = get_config("default_branch", "main")
    table = Table(title=f"Branches for {active_repo}")
    table.add_column("Branch Name", style="bold green")
    table.add_column("Status", style="cyan")

    for b in branches:
        name = b.get("name")
        status = "Active (Default)" if name == current_branch else ""
        table.add_row(name, status)

    console.print(table)

@branch_app.command("use")
def branch_use(branch_name: str = typer.Argument(..., help="Branch name to use")):
    """Set the active default branch"""
    set_config("default_branch", branch_name)
    console.print(f"[success]Default branch set to: [bold]{branch_name}[/bold][/success]")
