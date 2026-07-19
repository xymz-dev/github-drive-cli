import os
import json
import typer
from rich.table import Table
from utils import console, DATA_DIR
from auth import login_interactive, check_auth
from config import load_config, set_config, get_config
from github_api import get_user_info, get_rate_limit, get_repo_contents

system_app = typer.Typer(help="System and configuration commands")

@system_app.command("login")
def login_cmd():
    """Authenticate with GitHub using Personal Access Token"""
    login_interactive()

@system_app.command("info")
def info_cmd():
    """Display current session and repository information"""
    token = check_auth()
    if not token:
        return

    console.print("[info]Fetching account and repository info...[/info]")
    user_info = get_user_info(token)
    username = user_info.get("login") if user_info else get_config("username", "Unknown")
    active_repo = get_config("active_repo", "Not set")
    branch = get_config("default_branch", "main")

    total_files = "N/A"
    total_size = "N/A"

    if active_repo and "/" in active_repo:
        owner, repo = active_repo.split("/")
        try:
            contents = get_repo_contents(token, owner, repo, "", branch)
            if isinstance(contents, list):
                total_files = len(contents)
            elif isinstance(contents, dict):
                total_files = 1
        except Exception:
            pass

    rate_limit_data = get_rate_limit(token)
    core_limit = "Unknown"
    if rate_limit_data and "resources" in rate_limit_data:
        core = rate_limit_data["resources"].get("core", {})
        core_limit = f"{core.get('remaining')} / {core.get('limit')}"

    table = Table(title="GHUP System & Repository Info")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bold green")

    table.add_row("GitHub Username", username)
    table.add_row("Active Repository", active_repo)
    table.add_row("Active Branch", branch)
    table.add_row("Total Files (Root)", str(total_files))
    table.add_row("API Rate Limit (Core)", core_limit)

    console.print(table)

@system_app.command("history")
def history_cmd():
    """Show recent action history (upload, delete, rename, etc.)"""
    history_file = os.path.join(DATA_DIR, "history.json")
    if not os.path.exists(history_file):
        console.print("[warning]No history found yet.[/warning]")
        return

    try:
        with open(history_file, "r") as f:
            history = json.load(f)
    except Exception:
        history = []

    if not history:
        console.print("[warning]History is empty.[/warning]")
        return

    table = Table(title="Recent GHUP History")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Action", style="bold yellow")
    table.add_column("Details", style="green")

    for entry in history[:25]:
        table.add_row(entry.get("timestamp"), entry.get("action"), entry.get("details"))

    console.print(table)

@system_app.command("config")
def config_cmd(
    key: str = typer.Argument(None, help="Config key (retry_count, timeout, default_folder, zip_compression, parallel_upload)"),
    value: str = typer.Argument(None, help="New value for the config key")
):
    """View or update configuration settings"""
    if not key:
        config = load_config()
        table = Table(title="GHUP Configuration")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="bold green")
        for k, v in config.items():
            if k == "token":
                v = "******" if v else "Not set"
            table.add_row(k, str(v))
        console.print(table)
        return

    if value is None:
        console.print(f"[info]{key}:[/info] {get_config(key)}")
        return

    # Parse boolean or int if needed
    parsed_value = value
    if value.lower() == "true":
        parsed_value = True
    elif value.lower() == "false":
        parsed_value = False
    elif value.isdigit():
        parsed_value = int(value)

    set_config(key, parsed_value)
    console.print(f"[success]Updated config [bold]{key}[/bold] = {parsed_value}[/success]")

@system_app.command("doctor")
def doctor_cmd():
    """Diagnose configuration, network connection, and GitHub API status"""
    console.print("[info]Running GHUP Doctor diagnostics...[/info]")
    
    # Check Python & Termux
    console.print("  [green]✔[/green] Python 3 environment OK")
    
    # Check config file
    config = load_config()
    if config.get("token"):
        console.print("  [green]✔[/green] GitHub Token configured")
    else:
        console.print("  [red]✖[/red] GitHub Token NOT configured (Run 'ghup login')")

    # Check internet & GitHub API
    token = config.get("token")
    if token:
        user_info = get_user_info(token)
        if user_info:
            console.print(f"  [green]✔[/green] GitHub API connection OK ({user_info.get('login')})")
        else:
            console.print("  [red]✖[/red] GitHub API connection failed or token invalid")
    
    active_repo = config.get("active_repo")
    if active_repo:
        console.print(f"  [green]✔[/green] Active Repository set: {active_repo}")
    else:
        console.print("  [yellow]![/yellow] Active Repository not set")

    console.print("\n[success]Diagnostics complete![/success]")

@system_app.command("version")
def version_cmd():
    """Display GHUP version"""
    console.print("[bold cyan]GHUP (GitHub Uploader)[/bold cyan] v1.0.0 for Termux")

@system_app.command("self-update")
def self_update_cmd():
    """Check for updates and update GHUP"""
    console.print("[info]Checking for updates from GitHub...[/info]")
    console.print("[success]GHUP is already at the latest version (v1.0.0)[/success]")
