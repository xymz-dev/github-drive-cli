import typer
import base64
from rich.table import Table
from utils import console, human_size, log_history
from auth import check_auth
from config import get_config
from github_api import get_repo_contents, upload_file_api, delete_file_api
from uploader import handle_upload_target, download_remote_file

file_app = typer.Typer(help="File operations and upload/download")

@file_app.command("upload")
def upload_cmd(
    target: str = typer.Argument(..., help="File, folder, or glob pattern to upload"),
    folder: str = typer.Option("", "--folder", "-f", help="Target remote folder"),
    zip_compress: bool = typer.Option(False, "--zip", "-z", help="Compress folder to ZIP before upload"),
    flat: bool = typer.Option(False, "--flat", help="Flatten folder structure (upload all files directly without subfolders)"),
    branch: str = typer.Option(None, "--branch", "-b", help="Target branch")
):
    """Upload file(s) or folder(s) to GitHub repository"""
    token = check_auth()
    if not token:
        return

    active_repo = get_config("active_repo")
    if not active_repo:
        console.print("[error]No active repository set. Use 'ghup repo use <owner/repo>' first.[/error]")
        return

    owner, repo = active_repo.split("/")
    target_branch = branch if branch else get_config("default_branch", "main")
    target_folder = folder if folder else get_config("default_folder", "")

    handle_upload_target(token, owner, repo, target, target_folder, zip_compress, flat, target_branch)

@file_app.command("download")
def download_cmd(
    remote_path: str = typer.Argument(..., help="Path of remote file on GitHub"),
    output: str = typer.Option(None, "--output", "-o", help="Local output filename/path"),
    branch: str = typer.Option(None, "--branch", "-b", help="Branch name")
):
    """Download a file from GitHub repository"""
    token = check_auth()
    if not token:
        return

    active_repo = get_config("active_repo")
    if not active_repo:
        console.print("[error]No active repository set.[/error]")
        return

    owner, repo = active_repo.split("/")
    target_branch = branch if branch else get_config("default_branch", "main")
    download_remote_file(token, owner, repo, remote_path, output, target_branch)

@file_app.command("ls")
def list_files_cmd(
    path: str = typer.Argument("", help="Remote directory path (optional)"),
    branch: str = typer.Option(None, "--branch", "-b", help="Branch name")
):
    """List files and folders in repository or specific path"""
    token = check_auth()
    if not token:
        return

    active_repo = get_config("active_repo")
    if not active_repo:
        console.print("[error]No active repository set.[/error]")
        return

    owner, repo = active_repo.split("/")
    target_branch = branch if branch else get_config("default_branch", "main")

    data = get_repo_contents(token, owner, repo, path, target_branch)
    if data is None:
        console.print(f"[warning]Path not found or empty: {path}[/warning]")
        return

    if isinstance(data, dict):
        console.print(f"[info]File:[/info] {data.get('name')} ({human_size(data.get('size', 0))})")
        return

    table = Table(title=f"Contents of {active_repo}:{path or '/'}")
    table.add_column("Type", style="cyan", width=10)
    table.add_column("Name", style="bold green")
    table.add_column("Size", justify="right", style="magenta")

    for item in data:
        itype = item.get("type")
        name = item.get("name")
        size = human_size(item.get("size", 0)) if itype == "file" else "-"
        type_str = "📁 DIR" if itype == "dir" else "📄 FILE"
        table.add_row(type_str, name, size)

    console.print(table)

@file_app.command("delete")
def delete_file_cmd(
    remote_path: str = typer.Argument(..., help="Remote file path to delete"),
    branch: str = typer.Option(None, "--branch", "-b", help="Branch name")
):
    """Delete a file from the repository"""
    token = check_auth()
    if not token:
        return

    active_repo = get_config("active_repo")
    if not active_repo:
        console.print("[error]No active repository set.[/error]")
        return

    owner, repo = active_repo.split("/")
    target_branch = branch if branch else get_config("default_branch", "main")

    commit_msg = f"Delete {remote_path} via GHUP Termux"
    success, res = delete_file_api(token, owner, repo, remote_path, commit_msg, target_branch)
    if success:
        console.print(f"[success]Successfully deleted {remote_path}[/success]")
        log_history("DELETE", f"{active_repo}:{remote_path}")
    else:
        console.print(f"[error]Failed to delete file: {res.get('message', 'Unknown error')}[/error]")

@file_app.command("rename")
def rename_cmd(
    old_path: str = typer.Argument(..., help="Current remote file path"),
    new_path: str = typer.Argument(..., help="New remote file path"),
    branch: str = typer.Option(None, "--branch", "-b", help="Branch name")
):
    """Rename a remote file"""
    token = check_auth()
    if not token:
        return

    active_repo = get_config("active_repo")
    if not active_repo:
        console.print("[error]No active repository set.[/error]")
        return

    owner, repo = active_repo.split("/")
    target_branch = branch if branch else get_config("default_branch", "main")

    data = get_repo_contents(token, owner, repo, old_path, target_branch)
    if not data or isinstance(data, list):
        console.print(f"[error]Source file not found or is a directory: {old_path}[/error]")
        return

    content_b64 = data.get("content")
    if not content_b64:
        res = requests.get(data.get("download_url"), timeout=30)
        content_bytes = res.content
    else:
        content_bytes = base64.b64decode(content_b64)

    success, res = upload_file_api(token, owner, repo, new_path, content_bytes, f"Rename {old_path} to {new_path} via GHUP", target_branch)
    if not success:
        console.print(f"[error]Failed to create new file: {res.get('message')}[/error]")
        return

    delete_file_api(token, owner, repo, old_path, f"Remove old file after rename to {new_path}", target_branch)
    console.print(f"[success]Successfully renamed {old_path} -> {new_path}[/success]")
    log_history("RENAME", f"{old_path} -> {new_path}")

@file_app.command("move")
def move_cmd(
    src_path: str = typer.Argument(..., help="Source remote file path"),
    dest_path: str = typer.Argument(..., help="Destination remote file path"),
    branch: str = typer.Option(None, "--branch", "-b", help="Branch name")
):
    """Move a remote file to another path"""
    rename_cmd(src_path, dest_path, branch)

@file_app.command("copy")
def copy_cmd(
    src_path: str = typer.Argument(..., help="Source remote file path"),
    dest_path: str = typer.Argument(..., help="Destination remote file path"),
    branch: str = typer.Option(None, "--branch", "-b", help="Branch name")
):
    """Copy a remote file to another path"""
    token = check_auth()
    if not token:
        return

    active_repo = get_config("active_repo")
    if not active_repo:
        console.print("[error]No active repository set.[/error]")
        return

    owner, repo = active_repo.split("/")
    target_branch = branch if branch else get_config("default_branch", "main")

    data = get_repo_contents(token, owner, repo, src_path, target_branch)
    if not data or isinstance(data, list):
        console.print(f"[error]Source file not found: {src_path}[/error]")
        return

    content_b64 = data.get("content")
    if content_b64:
        content_bytes = base64.b64decode(content_b64)
    else:
        import requests
        res = requests.get(data.get("download_url"), timeout=30)
        content_bytes = res.content

    success, res = upload_file_api(token, owner, repo, dest_path, content_bytes, f"Copy {src_path} to {dest_path} via GHUP", target_branch)
    if success:
        console.print(f"[success]Successfully copied {src_path} -> {dest_path}[/success]")
        log_history("COPY", f"{src_path} -> {dest_path}")
    else:
        console.print(f"[error]Failed to parse copy file: {res.get('message')}[/error]")

@file_app.command("mkdir")
def mkdir_cmd(
    folder_path: str = typer.Argument(..., help="Folder path to create (GitHub requires a placeholder file like .gitkeep)"),
    branch: str = typer.Option(None, "--branch", "-b", help="Branch name")
):
    """Create a folder on GitHub repository (by adding a .gitkeep file)"""
    token = the_token = check_auth()
    if not the_token:
        return

    active_repo = get_config("active_repo")
    if not active_repo:
        console.print("[error]No active repository set.[/error]")
        return

    owner, repo = active_repo.split("/")
    target_branch = branch if branch else get_config("default_branch", "main")

    gitkeep_path = f"{folder_path.strip('/')}/.gitkeep"
    content_bytes = b"# GHUP placeholder for directory\n"
    success, res = upload_file_api(token, owner, repo, gitkeep_path, content_bytes, f"Create directory {folder_path} via GHUP", target_branch)
    if success:
        console.print(f"[success]Successfully created directory: {folder_path}[/success]")
        log_history("MKDIR", folder_path)
    else:
        console.print(f"[error]Failed to create directory: {res.get('message')}[/error]")
