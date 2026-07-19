import typer
from rich.table import Table
from utils import console
from auth import check_auth
from config import get_config, set_config
from github_api import list_repos

repo_app = typer.Typer(help="Manage GitHub repositories")

@repo_app.command("list")
def repo_list():
    """List all accessible GitHub repositories"""
    token = check_auth()
    if not token:
        return

    console.print("[info]Fetching repositories...[/info]")
    repos = list_repos(token)
    if not repos:
        console.print("[warning]No repositories found or failed to fetch.[/warning]")
        return

    table = Table(title="GitHub Repositories")
    table.add_column("No.", justify="right", style="cyan")
    table.add_column("Repository Name", style="bold green")
    table.add_column("Visibility", style="yellow")
    table.add_column("Default Branch", style="magenta")
    table.add_column("Description", style="dim")

    for idx, repo in enumerate(repos, 1):
        name = repo.get("full_name")
        private = "Private" if repo.get("private") else "Public"
        default_branch = repo.get("default_branch", "main")
        desc = (repo.get("description") or "")[:50]
        table.add_row(str(idx), name, private, default_branch, desc)

    console.print(table)

@repo_app.command("use")
def repo_use(repo_name: str = typer.Argument(..., help="Repository full name (e.g., username/repo)")):
    """Set the active repository"""
    token = check_auth()
    if not token:
        return

    set_config("active_repo", repo_name)
    console.print(f"[success]Active repository set to: [bold]{repo_name}[/bold][/success]")

@repo_app.command("current")
def repo_current():
    """Show the currently active repository"""
    active = get_config("active_repo")
    if active:
        console.print(f"[info]Active Repository:[/info] [bold green]{active}[/bold green]")
    else:
        console.print("[warning]No active repository set. Use 'ghup repo use <owner/repo>' or 'ghup repo list'.[/warning]")
